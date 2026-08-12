#!/usr/bin/env python3
"""The GitHub Pages front door, rebuilt from every thread's index.json.

Deliberately unstyled. The design lives in the dated cards and in each thread's own
generated pages; this file only has to be a working index of them, so it carries no
CSS and needs no upkeep.

Both build tools call rebuild() at the end of a run, so whichever thread published
last, the front door is correct for all of them.
"""

import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
HOME = ROOT / "index.html"
NOJEKYLL = ROOT / ".nojekyll"


def esc(s):
    return html.escape(str(s), quote=True)


def read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def morning_spark():
    doc = read(ROOT / "morning-spark" / "index.json")
    if not doc or not doc.get("editions"):
        return None
    eds = doc["editions"]
    lines = [
        "<h2>Morning Spark</h2>",
        "<p>Three idea-collisions every morning at 08:00. "
        f"{len(eds)} edition{'' if len(eds) == 1 else 's'}.</p>",
        "<ul>",
    ]
    for e in eds:
        d = esc(e["date"])
        lines.append(
            f'<li><a href="morning-spark/editions/{d}.html">{d} &mdash; '
            f'Ed. {e["edition"]:02d}</a> '
            f'(<a href="morning-spark/editions/{d}.txt">text</a>)</li>'
        )
    lines.append("</ul>")
    return "\n".join(lines)


def bench():
    doc = read(ROOT / "bench" / "index.json")
    if not doc:
        return None
    st = doc.get("state", {})
    days = doc.get("days", [])
    lines = [
        "<h2>Bench</h2>",
        "<p>168 days from software to hardware interaction design, one hour a night at 19:00. "
        f'{st.get("completed", 0)} of {st.get("total_days", 168)} days logged, '
        f'streak {st.get("streak", 0)}.</p>',
        '<p><a href="bench/progress.html"><b>Build log</b></a> &middot; '
        '<a href="bench/kit.html">Kit list</a></p>',
    ]
    if not days:
        return "\n".join(lines)
    lines.append("<ul>")
    for e in days:
        n = f"{e['day']:03d}"
        mark = "" if e.get("logged") else " &mdash; not logged"
        kind = "Bench Test" if e.get("kind") == "bench_test" else "Day"
        lines.append(
            f'<li><a href="bench/editions/{n}.html">{kind} {n} &mdash; '
            f'{esc(e.get("framing", ""))}</a> '
            f'(<a href="bench/editions/{n}.txt">text</a>){mark}</li>'
        )
    lines.append("</ul>")
    return "\n".join(lines)


def rebuild():
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>myThreads</title>",
        "<h1>myThreads</h1>",
        "<p>Tisu's daily threads. Each one writes JSON; everything else is generated.</p>",
    ]
    for section in (bench(), morning_spark()):
        if section:
            parts += ["<hr>", section]
    parts.append("</html>")
    HOME.write_text("\n".join(parts) + "\n", encoding="utf-8")
    NOJEKYLL.touch()
    return HOME


if __name__ == "__main__":
    print(f"ok  {rebuild()}")
