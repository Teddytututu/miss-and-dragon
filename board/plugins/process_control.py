"""Explicit, identity-bound process termination; observation never calls this."""
import argparse
import json
import math
import os
from pathlib import Path
import psutil


def stop_registered(record, *, allowed_pids, apply=True):
    pid=record.get('pid');created=record.get('create_time');executable=record.get('executable')
    if type(pid) is not int or pid<=0 or pid==os.getpid() or pid not in allowed_pids:
        return dict(status='outside_scope')
    if type(created) not in (int,float) or not math.isfinite(created) or not isinstance(executable,str) or not executable:
        return dict(status='identity_required')
    try:
        process=psutil.Process(pid)
        if abs(process.create_time()-created)>0.001 or os.path.normcase(process.exe())!=os.path.normcase(executable):
            return dict(status='identity_changed')
        if not apply:return dict(status='ready',pid=pid)
        process.terminate()
        try:process.wait(timeout=5)
        except psutil.TimeoutExpired:return dict(status='termination_requested',pid=pid)
        return dict(status='stopped',pid=pid)
    except psutil.NoSuchProcess:return dict(status='exited',pid=pid)
    except psutil.AccessDenied:return dict(status='access_required',pid=pid)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--record',type=Path,required=True)
    parser.add_argument('--pid',type=int,required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    print(json.dumps(stop_registered(json.loads(args.record.read_text('utf-8')),allowed_pids={args.pid},apply=args.apply)))


if __name__=='__main__':main()
