# Clean extraction acceptance

1. Build with `python scripts/release.py` and extract the ZIP into a fresh directory.
2. Create a project-local environment with `python -m venv .venv`. Install `requirements.txt` using that environment.
3. Run `python -B scripts/verify.py` and `node --test tests/*.test.cjs`.
4. Run `python -m board start "Fictional study" --question "Which workflow helps?" --deliverable "A small comparison" --port 8788`. Open the loopback page, verify the opening messages and return to the same state after restart.
5. Verify that the server socket listens on 127.0.0.1 and that Host, Origin and forwarded-header protections reject requests outside the direct local page.
6. Capture blue and pink at wide and narrow desktop widths. Review task grouping, quota controls, replies, Markdown, image dismissal and keyboard focus.
7. Keep verification logs and screenshots in a companion review directory; distribute the clean source ZIP.

## Current artwork candidate

The candidate includes the existing 33 character PNGs, a 225-item public emote source list, original SVG fallbacks and matching code/image license scopes. Runtime emote downloads belong to local data. The bundled Xiaolai subset retains its SIL OFL license. The notebook supports both themes and desktop/mobile layouts; the reaction dialog supports keyboard focus and Escape dismissal.

## 0.4 command acceptance

Exercise numbered questions and peer answers, execution choices and lead vetoes, exact event acknowledgment results, expired cards, dated schedules and assistant-owned efficiency observations. Concurrent answers close a question once. Missing GPU observations return a count of zero and an idle value of null. Verify custom project names and unrelated JSON fields survive updates.

## Rebuild the README diagrams

The generated SVGs ship with the source package and display directly in a browser. To edit and regenerate them, install the optional development tool in the project environment:

```sh
python -m pip install "fonttools>=4.61,<5"
python scripts/make_readme_diagrams.py
```

Pillow remains the application runtime dependency. The generator uses the bundled font files and licenses in `scripts/fonts/` and writes English and Simplified Chinese diagrams with accessible glyph outlines.
