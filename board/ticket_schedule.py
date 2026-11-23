"""Whole-job forecasts from explicit measured units. Standard library only.

Each input is one single-card job; a batch stays one job. ``measurement``
contains ``unit``, ``seconds`` and ``units`` and must match the job's ``unit``.
The caller supplies an ordered list, dependencies and the available card count.
This module projects files in memory; it never dispatches jobs or calls a model.
"""
from __future__ import annotations

import math
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _number(value, *, positive=False):
    if isinstance(value, bool):
        raise ValueError("Expected a finite number")
    try:
        value = float(value)
    except (TypeError, OverflowError) as exc:
        raise ValueError("Expected a finite number") from exc
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError("Expected a finite positive number" if positive else "Expected a finite nonnegative number")
    return value


def _duration(job):
    measurement = job.get("measurement")
    if measurement is None:
        return None
    if not isinstance(measurement, dict):
        raise ValueError("measurement must be an object")
    if not job.get("unit") or measurement.get("unit") != job["unit"]:
        return None
    if measurement.get("seconds") is None or measurement.get("units") is None:
        return None
    units = _number(job.get("units", 1), positive=True)
    rate = _number(measurement["seconds"], positive=True) / _number(measurement["units"], positive=True)
    return _number(units * rate + _number(job.get("load_seconds", 0)), positive=True)


def plan(jobs, *, cards=4, now=None):
    """Return stable forecasts; running jobs retain their physical card.

    ``state=done`` is an explicit completion fact. ``state=running`` uses
    ``card`` and ``elapsed_seconds`` (or explicit ``remaining_seconds``).
    Missing measurements and unresolved dependencies retain a waiting state.
    A running job with unknown remaining time holds its card for this forecast.
    """
    if isinstance(cards, bool) or _number(cards, positive=True) != cards or int(cards) != cards:
        raise ValueError("cards must be a positive integer")
    origin = datetime.now(timezone.utc) if now is None else datetime.fromisoformat(str(now).replace("Z", "+00:00"))
    if origin.tzinfo is None:
        raise ValueError("now must include a timezone")
    if not isinstance(jobs, list):
        raise ValueError("jobs must be a list")
    for job in jobs:
        if not isinstance(job, dict) or not isinstance(job.get("id"), str) or not job["id"].strip():
            raise ValueError("Each job requires a nonempty string id")
        if job.get("unit") is not None and not isinstance(job["unit"], str):
            raise ValueError("unit must be a string")
        deps = job.get("depends_on", [])
        if not isinstance(deps, list) or any(not isinstance(dep, str) or not dep.strip() for dep in deps):
            raise ValueError("depends_on must be a list of job IDs")
        if job.get("measurement") is not None and not isinstance(job["measurement"], dict):
            raise ValueError("measurement must be an object")
    ids = [job["id"] for job in jobs]
    if len(set(ids)) != len(ids):
        raise ValueError("Job IDs must be unique")
    available = [0.0] * int(cards)
    running_cards = set()
    endings, output, waiting = {}, {}, []
    known_hours = 0.0

    def stamp(seconds):
        try:
            return (origin + timedelta(seconds=seconds)).isoformat(timespec="seconds")
        except OverflowError as exc:
            raise ValueError("Forecast time exceeds the supported calendar") from exc

    for job, job_id in zip(jobs, ids):
        row = dict(id=job_id, task=job.get("task"), title=job.get("title", job_id),
                   unit=job.get("unit"), state="waiting_trial", card=None,
                   start=None, finish=None, card_hours=None, reason="Waiting for a matching unit measurement")
        output[job_id] = row
        if job.get("state") in ("done", "completed", "accepted"):
            row.update(state="done", card_hours=0, reason="Completed")
            endings[job_id] = 0.0
            continue
        duration = _duration(job)
        if duration is not None:
            row["reason"] = "Measured time per " + job["unit"]
        if job.get("state") == "running":
            card = job.get("card")
            if isinstance(card, bool) or not isinstance(card, int) or not 0 <= card < cards or card in running_cards:
                raise ValueError("Running jobs require distinct available card indices")
            running_cards.add(card)
            elapsed = _number(job.get("elapsed_seconds", 0))
            remaining = job.get("remaining_seconds")
            if remaining is not None:
                duration = _number(remaining)
            elif duration is not None:
                duration = max(0, duration - elapsed)
                if duration == 0:
                    duration = None
            row.update(state="running", card=card, start=stamp(-elapsed), run_elapsed_seconds=elapsed,
                       total_seconds=elapsed + duration if duration is not None else None)
            available[card] = duration if duration is not None else math.inf
            if duration is not None:
                row.update(finish=stamp(duration), card_hours=duration / 3600)
                endings[job_id] = duration
                known_hours += duration / 3600
        elif job.get("state") in ("paused", "waiting_review", "waiting_human"):
            row["state"] = job["state"]
        elif duration is not None:
            row["card_hours"] = duration / 3600
            known_hours += duration / 3600
            waiting.append((job, job_id, duration))

    while waiting:
        deferred, progressed = [], False
        for job, job_id, duration in waiting:
            row = output[job_id]
            deps = [str(dep) for dep in job.get("depends_on", [])]
            if any(dep not in endings for dep in deps):
                row["state"] = "waiting_dependency"
                row["reason"] = "Waiting for dependency completion"
                deferred.append((job, job_id, duration))
                continue
            earliest = max((endings[dep] for dep in deps), default=0.0)
            card = min(range(int(cards)), key=lambda index: (available[index], index))
            start = max(earliest, available[card])
            if math.isinf(start):
                row["state"] = "waiting_card"
                row["reason"] = "Waiting for a measured card release"
                continue
            end = start + duration
            row.update(state="scheduled", card=card, start=stamp(start), finish=stamp(end))
            available[card] = end
            endings[job_id] = end
            progressed = True
        if not progressed:
            break
        waiting = deferred
    rows = [output[job_id] for job_id in ids]
    finishes = [row["finish"] for row in rows if row["finish"]]
    complete = all(row["state"] in ("done", "scheduled") or row["state"] == "running" and row["finish"] for row in rows)
    return dict(now=origin.isoformat(), cards=int(cards), jobs=rows,
                remaining_card_hours=round(known_hours, 6), complete=complete,
                finish=max(finishes, key=datetime.fromisoformat) if finishes and complete else None)


def from_file(path, *, now=None, cards=None):
    """Read the optional resource-plan file and project it without changing it."""
    path = Path(path)
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict) or "jobs" not in value:
        raise ValueError("Resource plan requires an object containing jobs")
    return plan(value["jobs"], cards=value.get("cards", 4) if cards is None else cards, now=now)
