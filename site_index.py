#!/usr/bin/env python3
"""The GitHub Pages front door, rebuilt from every thread's index.json.

Deliberately small. It is not a design surface -- the design lives in the dated
cards -- but it is the one page that has to answer "where do I go" in a second,
so it shows each thread's current state and its most recent entries rather than an
undifferentiated list that grows to five hundred links.

Both build tools call rebuild() at the end of a run, so whichever thread published
last, the front door is correct for all of them.
"""

import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
HOME = ROOT / "index.html"
NOJEKYLL = ROOT / ".nojekyll"
RECENT = 8  # entries shown per thread before the rest is folded away

CSS = """
:root{--ground:#121214;--ink:#EDEBE5;--dim:#9A968C;--hair:#2A2A2E;--card:#1A1A1D;--accent:#FF4A00}
*{box-sizing:border-box;margin:0;padding:0}html{-webkit-text-size-adjust:100%}
body{background:var(--ground);color:var(--ink);font-family:"Helvetica Neue",Helvetica,Arial,
 -apple-system,system-ui,sans-serif;line-height:1.5;-webkit-font-smoothing:antialiased;padding:0 0 70px}
.wrap{max-width:680px;margin:0 auto;padding:0 24px}
.mono{font-family:ui-monospace,"SF Mono",Menlo,monospace}
header{padding:36px 0 0}
h1{font-size:clamp(24px,6vw,32px);letter-spacing:-.02em;font-weight:800;line-height:1.15}
.sub{color:var(--dim);font-size:15px;margin-top:8px}
.th{margin-top:30px;padding-top:24px;border-top:3px solid var(--ink)}
.thead{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
.thead h2{font-size:19px;font-weight:800;letter-spacing:-.01em}
.thead .when{font-family:ui-monospace,Menlo,monospace;font-size:11px;letter-spacing:.14em;
 text-transform:uppercase;color:var(--dim)}
.blurb{color:var(--dim);font-size:14px;margin-top:6px;line-height:1.55}
.stat{display:flex;gap:24px;flex-wrap:wrap;margin-top:14px}
.stat div span{display:block}
.stat .v span{display:inline}
.stat .k{font-family:ui-monospace,Menlo,monospace;font-size:10px;letter-spacing:.16em;
 text-transform:uppercase;color:var(--dim)}
.stat .v{font-family:ui-monospace,Menlo,monospace;font-size:22px;font-weight:700;margin-top:2px}
.stat .v.a{color:var(--accent)}
.go{display:flex;gap:2px;margin-top:16px;flex-wrap:wrap}
.go a{font-family:ui-monospace,Menlo,monospace;font-size:11px;letter-spacing:.12em;
 text-transform:uppercase;color:var(--dim);text-decoration:none;padding:9px 13px;
 border:1px solid var(--hair);line-height:1}
.go a:hover{color:var(--accent);border-color:var(--accent)}
.go a.pri{border-color:var(--accent);color:var(--accent);font-weight:700}
.go a.pri:hover{background:var(--accent);color:var(--ground)}
ul{list-style:none;margin-top:18px}
li{padding:9px 0;border-top:1px solid var(--hair);display:flex;gap:12px;align-items:baseline}
li:first-child{border-top:none}
li .n{font-family:ui-monospace,Menlo,monospace;font-size:11px;color:var(--dim);flex:0 0 78px}
li a{color:var(--ink);text-decoration:none;font-size:15px;line-height:1.4}
li a:hover{color:var(--accent)}
details{margin-top:10px}
summary{font-family:ui-monospace,Menlo,monospace;font-size:11px;letter-spacing:.12em;
 text-transform:uppercase;color:var(--dim);cursor:pointer;padding:8px 0}
summary:hover{color:var(--accent)}
footer{margin-top:34px;padding-top:18px;border-top:1px solid var(--hair);
 font-family:ui-monospace,Menlo,monospace;font-size:11px;color:var(--dim);line-height:1.8}
"""


def esc(s):
    return html.escape(str(s), quote=True)


def read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def rows(items):
    """A list, with everything past RECENT folded into a details element."""
    head = "".join(items[:RECENT])
    if len(items) <= RECENT:
        return f"<ul>{head}</ul>"
    rest = "".join(items[RECENT:])
    return (
        f"<ul>{head}</ul><details><summary>all {len(items)} &darr;</summary>"
        f"<ul>{rest}</ul></details>"
    )


def bench():
    doc = read(ROOT / "bench" / "index.json")
    if not doc:
        return None
    st = doc.get("state", {})
    days = doc.get("days", [])
    latest = days[0] if days else None
    items = [
        f'<li><span class="n">{d["day"]:03d}'
        + ("" if d.get("logged") else " &middot;")
        + f'</span><a href="bench/editions/{d["day"]:03d}.html">{esc(d.get("framing", ""))}</a></li>'
        for d in days
    ]
    go = []
    if latest:
        go.append(
            f'<a class="pri" href="bench/editions/{latest["day"]:03d}.html">'
            f'Day {latest["day"]:03d} &rarr;</a>'
        )
    go += ['<a href="bench/progress.html">Build log</a>', '<a href="bench/kit.html">Kit list</a>']
    return f"""<section class="th">
<div class="thead"><h2>Bench</h2><div class="when">19:00 &middot; every evening</div></div>
<p class="blurb">168 days from software engineer to hardware interaction designer,
one hour at a time. Six phases, twenty-four projects, one finished object.</p>
<div class="stat">
<div><span class="k">days done</span><span class="v">{st.get('completed', 0)}<span
 style="font-size:14px;color:var(--dim)">/{st.get('total_days', 168)}</span></span></div>
<div><span class="k">streak</span><span class="v a">{st.get('streak', 0)}d</span></div>
<div><span class="k">up next</span><span class="v">{st.get('current_day', 1):03d}</span></div>
</div>
<div class="go">{''.join(go)}</div>
{rows(items) if items else ''}
</section>"""


def morning_spark():
    doc = read(ROOT / "morning-spark" / "index.json")
    if not doc or not doc.get("editions"):
        return None
    eds = doc["editions"]
    items = [
        f'<li><span class="n">{esc(e["date"])}</span>'
        f'<a href="morning-spark/editions/{esc(e["date"])}.html">Ed. {e["edition"]:02d}</a></li>'
        for e in eds
    ]
    latest = eds[0]
    return f"""<section class="th">
<div class="thead"><h2>Morning Spark</h2><div class="when">08:00 &middot; every morning</div></div>
<p class="blurb">Three idea-collisions to think with, bilingual, each grounded in a
piece actually read that week.</p>
<div class="stat">
<div><span class="k">editions</span><span class="v">{len(eds)}</span></div>
<div><span class="k">latest</span><span class="v a">{latest['edition']:02d}</span></div>
</div>
<div class="go"><a class="pri" href="morning-spark/editions/{esc(latest['date'])}.html">
Ed. {latest['edition']:02d} &rarr;</a></div>
{rows(items)}
</section>"""


def rebuild():
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>myThreads</title>",
        f"<style>{CSS}</style></head><body><div class='wrap'>",
        "<header><h1>myThreads</h1>",
        '<p class="sub">Two threads, two moments of the day. '
        "Each one writes JSON; everything else is generated.</p></header>",
    ]
    for section in (bench(), morning_spark()):
        if section:
            parts.append(section)
    parts += [
        "<footer>Generated by site_index.py from each thread's index.json. "
        "Never hand-edited.</footer>",
        "</div></body></html>",
    ]
    HOME.write_text("\n".join(parts) + "\n", encoding="utf-8")
    NOJEKYLL.touch()
    return HOME


if __name__ == "__main__":
    print(f"ok  {rebuild()}")
