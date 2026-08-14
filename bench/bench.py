#!/usr/bin/env python3
"""Bench build tool.

  bench.py status                  where you are: day, streak, drift, and what is gated
  bench.py ledger [--limit N]      history digest + the next day to author (read before curating)
  bench.py build [--day N]         validate data/NNN.json -> editions/NNN.{html,txt} + index + progress
  bench.py log [--day N] ...       close a day: writes logs/NNN.json, then rebuilds progress
  bench.py plan [--day N]          print the curriculum spine for a day (phase, week, milestone)

No dependencies. Data is the source of truth; HTML and text are generated.

The gate: day N cannot be authored until day N-1 has a log. The curriculum waits for
you -- it never hands out homework debt. Drift is reported honestly and left at that.
"""

import argparse
import datetime as dt
import html
import json
import pathlib
import re
import sys
import urllib.parse
import zoneinfo

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import glyphs  # noqa: E402  (needs the path above)

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"
LOGS = ROOT / "logs"
EDITIONS = ROOT / "editions"
TEMPLATE = ROOT / "template.html"
PROGRESS_TEMPLATE = ROOT / "progress.template.html"
PROGRESS = ROOT / "progress.html"
CURRICULUM = ROOT / "curriculum.json"
INDEX = ROOT / "index.json"
SITE = ROOT.parent
TZ = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
SEP = "─" * 17

TOTAL_DAYS = 168
WEEK_LEN = 7
BUDGET_MINUTES = 65  # one hour, with five minutes of slack. Filler has nowhere to hide.

# Same rule as Morning Spark: authored data carries no emoji or decorative symbols.
# The arrows and rules in the generated chrome are added by this script, never by JSON.
EMOJI = re.compile(
    "["
    "\U0001F000-\U0001FAFF"  # emoji and pictograph blocks
    "←-⇿"          # arrows
    "⌀-⏿"          # misc technical
    "☀-➿"          # misc symbols, dingbats
    "⬀-⯿"          # misc symbols and arrows
    "️‍"           # variation selector, zero-width joiner
    "]"
)


class Bad(Exception):
    pass


def today():
    return dt.datetime.now(TZ).date()


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Bad(f"missing {path}")
    except json.JSONDecodeError as e:
        raise Bad(f"{path.name} is not valid JSON: {e}")


def stem(day):
    return f"{day:03d}"


# ------------------------------------------------------------------ curriculum

def curriculum():
    return load(CURRICULUM)


def week_of(day):
    return (day - 1) // WEEK_LEN + 1


def is_bench_test(day):
    return day % WEEK_LEN == 0


def spine(day):
    """The fixed scaffolding for a day: which phase, which week, which milestone."""
    c = curriculum()
    wk = week_of(day)
    phase = next((p for p in c["phases"] if p["weeks"][0] <= wk <= p["weeks"][1]), None)
    if phase is None:
        raise Bad(f"day {day} falls outside the curriculum")
    week = next((w for w in c["weeks"] if w["week"] == wk), None)
    if week is None:
        raise Bad(f"week {wk} is missing from curriculum.json")
    return phase, week


def deadline_day(week):
    """Every week's project is due on its Bench Test, the seventh day."""
    return week["week"] * WEEK_LEN


def needed_by(kit_id, from_week):
    """The first week that actually puts this part to work. That is the real deadline."""
    for w in curriculum()["weeks"]:
        if w["week"] >= from_week and kit_id in w.get("kit", []):
            return w["week"]
    return None


def prep_for_week(wk):
    """What has to be ordered this week so it is on the bench when it is needed.

    This is the school supply list. Lead times to Ho Chi Minh City are short for the
    local shops and long for anything that crosses a border, so the curriculum places
    each order weeks ahead of the day it matters.
    """
    c = curriculum()
    week = next((w for w in c["weeks"] if w["week"] == wk), None)
    if not week:
        return []
    out = []
    for kid in week.get("order_now", []):
        item = c["kit"].get(kid)
        if not item:
            raise Bad(f"week {wk} orders unknown kit item {kid!r}")
        due = needed_by(kid, wk)
        shops = [c["shops"][s] for s in item["where"] if s in c["shops"]]
        out.append(
            {
                "id": kid,
                "name": item["name"],
                "why": item["why"],
                "vnd": item.get("vnd", ""),
                "lead": item.get("lead", ""),
                "where": item["where"],
                "shops": shops,
                "needed_week": due,
                "needed_day": due * WEEK_LEN if due else None,
            }
        )
    return out


# ----------------------------------------------------------------------- state

def days_on_disk():
    """Every authored day. A week can be written ahead, so this runs ahead of delivery."""
    out = []
    for p in sorted(DATA.glob("[0-9][0-9][0-9].json")):
        out.append((int(p.stem), load(p)))
    return out


def delivered_days():
    """Only the days whose card has actually been rendered and sent.

    Authoring a week in advance is normal, so the data directory runs ahead of what
    has been delivered. The index, the build log and the front door must follow
    delivery, or they link to editions that do not exist yet.
    """
    return [(d, doc) for d, doc in days_on_disk() if (EDITIONS / f"{stem(d)}.html").exists()]


def logs_on_disk():
    out = {}
    for p in sorted(LOGS.glob("[0-9][0-9][0-9].json")):
        out[int(p.stem)] = load(p)
    return out


def log_dates(logs):
    seen = set()
    for entry in logs.values():
        try:
            seen.add(dt.date.fromisoformat(entry["date"]))
        except (KeyError, ValueError):
            continue
    return sorted(seen)


def streak(logs, ref=None):
    """Consecutive calendar days ending today or yesterday that carry a log.

    Ending yesterday still counts: at 19:00 today's card has only just landed, so a
    streak should not read as broken before the day has had its chance.
    """
    dates = set(log_dates(logs))
    if not dates:
        return 0
    ref = ref or today()
    cursor = ref if ref in dates else ref - dt.timedelta(days=1)
    if cursor not in dates:
        return 0
    n = 0
    while cursor in dates:
        n += 1
        cursor -= dt.timedelta(days=1)
    return n


def state(ref=None):
    """Everything a run needs to decide what to hand out, in one dict."""
    ref = ref or today()
    logs = logs_on_disk()
    authored = {d for d, _ in delivered_days()}
    # Showing up and finishing are different things. A partial log keeps the streak
    # alive -- you sat down -- but it does not advance the day, so tomorrow hands you
    # the same card again to finish. Being slow costs drift, never a broken streak.
    done = sorted(d for d, e in logs.items() if not e.get("partial"))
    partial = sorted(d for d, e in logs.items() if e.get("partial"))
    dates = log_dates(logs)

    current = (max(done) + 1) if done else 1
    gated = current > 1 and (current - 1) not in done  # cannot happen, kept as a guard
    last = dates[-1] if dates else None
    silent = (ref - last).days if last else 0
    # Two consecutive missed calendar days: the way back in gets shorter, not longer.
    re_entry = bool(last) and silent >= 3
    elapsed = (ref - dates[0]).days + 1 if dates else 0
    drift = max(0, elapsed - len(done))

    return {
        "today": ref.isoformat(),
        "current_day": min(current, TOTAL_DAYS),
        "total_days": TOTAL_DAYS,
        "completed": len(done),
        "in_progress": partial,
        "authored": sorted(authored),
        "unlogged": sorted(authored - set(done)),
        "streak": streak(logs, ref),
        "drift": drift,
        "elapsed": elapsed,
        "silent_days": silent,
        "re_entry": re_entry,
        "gated": gated,
        "started": dates[0].isoformat() if dates else None,
        "last_log": last.isoformat() if last else None,
        "finished": len(done) >= TOTAL_DAYS,
    }


# ------------------------------------------------------------------ validation

def check_text(where, value, limit=None):
    if not isinstance(value, str) or not value.strip():
        raise Bad(f"{where}: must be a non-empty string")
    hit = EMOJI.search(value)
    if hit:
        raise Bad(f"{where}: emoji or symbol {hit.group()!r} is not allowed")
    v = value.strip()
    if limit and len(v.split()) > limit:
        raise Bad(f"{where}: {len(v.split())} words, max {limit}")
    return v


def check_source(where, src, prior_urls):
    for f in ("site", "title", "url"):
        check_text(f"{where}.{f}", src.get(f, ""))
    url = src["url"]
    if not url.startswith("http"):
        raise Bad(f"{where}.url must be an absolute URL")
    if url in prior_urls and not src.get("revisit"):
        raise Bad(
            f"{where}: {url} was already used on day {prior_urls[url]:03d} "
            '(set "revisit": true if the second pass is deliberate)'
        )
    return url


def validate(day, doc, prior_urls):
    if doc.get("day") != day:
        raise Bad(f"day field {doc.get('day')!r} does not match filename {stem(day)}")
    if not 1 <= day <= TOTAL_DAYS:
        raise Bad(f"day must be between 1 and {TOTAL_DAYS}")

    kind = doc.get("kind", "build")
    if kind not in ("build", "bench_test"):
        raise Bad("kind must be 'build' or 'bench_test'")
    if is_bench_test(day) and kind != "bench_test":
        raise Bad(f"day {day} closes a week, so kind must be 'bench_test'")
    if not is_bench_test(day) and kind != "build":
        raise Bad(f"day {day} is not a week close, so kind must be 'build'")

    check_text("framing", doc.get("framing", ""), limit=12)
    check_text("done_when", doc.get("done_when", ""))
    check_text("question", doc.get("question", ""))

    blocks = doc.get("blocks")
    if not isinstance(blocks, list) or len(blocks) != 3:
        raise Bad("blocks must be a list of exactly 3 entries")
    total = 0
    for i, b in enumerate(blocks, 1):
        check_text(f"block {i}.label", b.get("label", ""), limit=2)
        check_text(f"block {i}.body", b.get("body", ""))
        if not isinstance(b.get("minutes"), int) or b["minutes"] <= 0:
            raise Bad(f"block {i}.minutes must be a positive integer")
        total += b["minutes"]
        for j, d in enumerate(b.get("detail", []), 1):
            check_text(f"block {i}.detail[{j}]", d)
        # The renderer marks these up by substring replacement, so a phrase that is not
        # actually in the body would silently do nothing.
        for phrase in b.get("bold", []):
            if phrase not in b["body"]:
                raise Bad(f"block {i}: bold {phrase!r} not found in body")
    if total > BUDGET_MINUTES:
        raise Bad(f"blocks total {total} minutes, budget is {BUDGET_MINUTES}")
    if kind == "build" and total < 45:
        raise Bad(f"blocks total only {total} minutes -- a build day should fill the hour")

    src = doc.get("source")
    if kind == "build" and not src:
        raise Bad("a build day needs a source: the piece you actually read or watched")
    if src:
        check_source("source", src, prior_urls)
        # A 39-minute talk does not fit in a 25-minute block. If only part of a long
        # piece is wanted, say so in `length` ("28 min (stop at the SDK section)") so
        # the number on the card is the time it actually takes.
        hit = re.match(r"\s*(\d+)", src.get("length", ""))
        if hit and int(hit.group(1)) > blocks[0]["minutes"]:
            raise Bad(
                f"source is {hit.group(1)} min but the intake block is only "
                f"{blocks[0]['minutes']} min -- widen the block, or scope the excerpt "
                "in source.length"
            )

    obj = doc.get("object", {})
    check_text("object.name", obj.get("name", ""))
    check_text("object.why", obj.get("why", ""))
    if obj.get("url") and not obj["url"].startswith("http"):
        raise Bad("object.url must be an absolute URL")

    return blocks, total


# ------------------------------------------------------------------- rendering

def esc(s):
    return html.escape(s, quote=True)


def nav(current, up, latest=None, here=""):
    """Breadcrumb plus sibling links, on one line that never wraps.

    Class is `crumb`, not `nav`: the kit page's slider already owns `.nav` for its
    42px transport buttons, and the collision collapsed this to 42px wide on a phone.

    `up` is the prefix back to the bench/ directory, so a day card passes "../" and
    the hub pages pass "".
    """
    sibs = [
        ("build log", f"{up}progress.html", "progress"),
        ("kit", f"{up}kit.html", "kit"),
    ]
    if latest is not None and current != "day":
        sibs.insert(0, ("today", f"{up}editions/{stem(latest)}.html", "day"))
    rest = "".join(
        f'<a href="{esc(href)}">{label}</a>' for label, href, key in sibs if key != current
    )
    return (
        '<nav class="crumb" aria-label="Breadcrumb">'
        f'<a href="{esc(up)}../index.html">myThreads</a>'
        '<span class="sep">&rsaquo;</span>'
        f'<a href="{esc(up)}progress.html">Bench</a>'
        '<span class="sep">&rsaquo;</span>'
        f'<span class="here">{esc(here)}</span>'
        f'<span class="sib">{rest}</span>'
        "</nav>"
    )


def wrap_all(text, phrases, tag):
    out = esc(text)
    for p in phrases:
        out = out.replace(esc(p), f"<{tag}>{esc(p)}</{tag}>", 1)
    return out


def daynav(day):
    """Previous and next day, so a card is not a dead end.

    Only links days that were actually delivered; a stub pointing at an unwritten
    day would 404 on Pages.
    """
    have = {d for d, _ in delivered_days()} | {day}
    prev = max((d for d in have if d < day), default=None)
    nxt = min((d for d in have if d > day), default=None)
    left = (
        f'<a class="pn" href="{stem(prev)}.html">&larr; {stem(prev)}</a>'
        if prev else '<span class="pn off">&larr;</span>'
    )
    right = (
        f'<a class="pn" href="{stem(nxt)}.html">{stem(nxt)} &rarr;</a>'
        if nxt else '<span class="pn off">&rarr;</span>'
    )
    return (
        f'<div class="daynav">{left}'
        '<a class="all" href="../progress.html">all days</a>'
        f"{right}</div>"
    )


def render_html(day, doc, blocks, total, st):
    phase, week = spine(day)
    day_in_week = (day - 1) % WEEK_LEN + 1

    rows = []
    for i, b in enumerate(blocks, 1):
        detail = "".join(f"<li>{esc(d)}</li>" for d in b.get("detail", []))
        detail = f'<ul class="detail">{detail}</ul>' if detail else ""
        src = ""
        if i == 1 and doc.get("source"):
            s = doc["source"]
            meta = " / ".join(x for x in (s.get("kind", ""), s.get("length", "")) if x)
            src = (
                f'<a class="src" href="{esc(s["url"])}" target="_blank" rel="noopener">'
                f'<span class="site">{esc(s["site"])}</span>'
                f'<span class="ttl">{esc(s["title"])}</span>'
                + (f'<span class="kind">{esc(meta)}</span>' if meta else "")
                + "</a>"
            )
        rows.append(
            f'<section class="blk"><div class="blkhead">'
            f'<span class="n">{i:02d}</span>'
            f'<span class="lbl">{esc(b["label"].upper())}</span>'
            f'<span class="min">{b["minutes"]} min</span></div>'
            f'<p class="body">{wrap_all(b["body"], b.get("bold", []), "b")}</p>'
            f"{src}{detail}</section>"
        )

    # The rail: one tick per day of the current phase, so progress is visible but the
    # remaining 140 days never loom.
    lo = (phase["weeks"][0] - 1) * WEEK_LEN + 1
    hi = phase["weeks"][1] * WEEK_LEN
    ticks = []
    for d in range(lo, hi + 1):
        cls = "t done" if d < day else ("t now" if d == day else "t")
        if is_bench_test(d):
            cls += " bt"
        ticks.append(f'<i class="{cls}"></i>')

    obj = doc["object"]
    obj_body = esc(obj["why"])
    if obj.get("url"):
        obj_body += (
            f' <a href="{esc(obj["url"])}" target="_blank" rel="noopener">look &rarr;</a>'
        )

    stats = [
        ("streak", f"{st['streak']}d"),
        ("done", f"{st['completed']}/{TOTAL_DAYS}"),
        ("drift", f"{st['drift']}d" if st["drift"] else "none"),
    ]
    statline = "".join(
        f'<div class="stat"><span class="k">{k}</span><span class="v">{v}</span></div>'
        for k, v in stats
    )

    # The project strip. A day is never just a day -- it is a slice of something due
    # on this week's Bench Test, and the card says how many days are left.
    proj = week["project"]
    due = deadline_day(week)
    left = due - day
    if left > 1:
        countdown = f"{left} days left"
    elif left == 1:
        countdown = "due tomorrow"
    else:
        countdown = "due today"
    project = (
        f'<section class="proj"><div class="projhead">'
        f'<span class="lbl">Week {week["week"]} project</span>'
        f'<span class="due">Day {stem(due)} &middot; {esc(countdown)}</span></div>'
        f'<h2>{esc(proj["name"])}</h2>'
        f'<p class="spec">{esc(proj["spec"])}</p>'
        f'<dl><dt>Deliverable</dt><dd>{esc(proj["deliverable"])}</dd>'
        + (f'<dt>Stretch</dt><dd>{esc(proj["stretch"])}</dd>' if proj.get("stretch") else "")
        + "</dl></section>"
    )

    # The supply list. Only shown on the first day of a week that has orders to place,
    # so it lands once, with time to act, and never nags.
    prep = ""
    orders = prep_for_week(week["week"]) if day_in_week == 1 else []
    if orders:
        items = []
        for o in orders:
            shops = " &middot; ".join(
                f'<a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(n)}</a>'
                if s.get("url")
                else esc(n)
                for n, s in zip(o["where"], o["shops"])
            )
            when = (
                f'needed week {o["needed_week"]} (day {stem(o["needed_day"])})'
                if o["needed_week"]
                else "keep on hand"
            )
            items.append(
                f'<li><span class="it">{esc(o["name"])}</span>'
                f'<span class="mt">{esc(o["vnd"])} &middot; {esc(o["lead"])} &middot; {when}</span>'
                f'<span class="sh">{shops}</span></li>'
            )
        prep = (
            '<section class="prep"><div class="prephead">'
            "<span class=\"lbl\">Order this week</span>"
            '<span class="due">so it is on the bench in time</span></div>'
            f'<ul>{"".join(items)}</ul>'
            '<p class="note">Local shops deliver in HCMC within one to three days. '
            "Anything crossing a border needs weeks. Order today, not on the day you need it.</p>"
            "</section>"
        )

    tokens = {
        "DAY": stem(day),
        "TOTAL": str(TOTAL_DAYS),
        "KIND": "BENCH TEST" if doc.get("kind") == "bench_test" else "BUILD DAY",
        "PHASE_N": f"{phase['phase']:02d}",
        "PHASE": esc(phase["title"]),
        "WEEK": str(week["week"]),
        "WEEK_TITLE": esc(week["title"]),
        "DAY_IN_WEEK": f"{day_in_week}",
        "FRAMING": esc(doc["framing"]),
        "BLOCKS": "".join(rows),
        "DONE_WHEN": esc(doc["done_when"]),
        "QUESTION": esc(doc["question"]),
        "OBJ_NAME": esc(obj["name"]),
        "OBJ_WHY": obj_body,
        "RAIL": "".join(ticks),
        "TOTAL_MIN": str(total),
        "STATS": statline,
        "MILESTONE": esc(phase["milestone"]),
        "PROJECT": project,
        "PREP": prep,
        "NAV": nav("day", "../", here=f"Day {stem(day)}"),
        "DAYNAV": daynav(day),
        "BANNER": (
            '<div class="banner">Two days quiet. This one is deliberately short. '
            "Just get back on the bench.</div>"
            if st["re_entry"]
            else ""
        ),
    }

    out = TEMPLATE.read_text(encoding="utf-8")
    for k, v in tokens.items():
        out = out.replace(f"[[{k}]]", v)
    left = re.findall(r"\[\[[A-Z0-9_]+\]\]", out)
    if left:
        raise Bad(f"template tokens left unfilled: {sorted(set(left))}")
    return out


def render_text(day, doc, blocks, total, st):
    phase, week = spine(day)
    day_in_week = (day - 1) % WEEK_LEN + 1
    kind = "Bench Test" if doc.get("kind") == "bench_test" else "Day"
    head = (
        f"Bench · {kind} {stem(day)}/{TOTAL_DAYS} · "
        f"P{phase['phase']:02d} {phase['title']} · W{week['week']} {week['title']}\n"
        f"{doc['framing']}"
    )
    out = [head]

    proj = week["project"]
    due = deadline_day(week)
    left = due - day
    when = f"{left} days left" if left > 1 else ("due tomorrow" if left == 1 else "due today")
    out.append(
        f"{SEP}\nWEEK {week['week']} PROJECT — {proj['name']}\n"
        f"Due day {stem(due)}, {when}.\n{proj['spec']}\n"
        f"Deliverable: {proj['deliverable']}"
    )

    orders = prep_for_week(week["week"]) if day_in_week == 1 else []
    if orders:
        lines = [f"{SEP}\nORDER THIS WEEK"]
        for o in orders:
            need = f"needed week {o['needed_week']}" if o["needed_week"] else "keep on hand"
            lines.append(
                f"  - {o['name']}\n    {o['vnd']} · {o['lead']} · {need}"
                f"\n    {', '.join(o['where'])}"
            )
        out.append("\n".join(lines))

    for i, b in enumerate(blocks, 1):
        body = [f"{SEP}\n{b['label'].upper()}  {b['minutes']} min\n{b['body']}"]
        if i == 1 and doc.get("source"):
            s = doc["source"]
            body.append(f"{s['site']} — {s['title']}\n→ {s['url']}")
        for d in b.get("detail", []):
            body.append(f"  - {d}")
        out.append("\n".join(body))
    out.append(f"{SEP}\nDONE WHEN\n{doc['done_when']}")
    out.append(f"LOG\n{doc['question']}\nbench.py log --day {day} --did \"...\" --made \"...\"")
    out.append(f"THE OBJECT\n{doc['object']['name']} — {doc['object']['why']}")
    if doc["object"].get("url"):
        out.append(f"→ {doc['object']['url']}")
    tail = f"{total} min · streak {st['streak']}d · {st['completed']}/{TOTAL_DAYS} done"
    if st["drift"]:
        tail += f" · drift {st['drift']}d"
    out.append(tail)
    return "\n\n".join(out) + "\n"


# -------------------------------------------------------------------- rollups

def rebuild_index(all_days, logs):
    entries = []
    for day, doc in all_days:
        phase, week = spine(day)
        lg = logs.get(day, {})
        entries.append(
            {
                "day": day,
                "kind": doc.get("kind", "build"),
                "phase": phase["phase"],
                "week": week["week"],
                "framing": doc.get("framing", ""),
                "source": (
                    f"{doc['source']['site']} — {doc['source']['title']}"
                    if doc.get("source")
                    else ""
                ),
                "url": doc.get("source", {}).get("url", ""),
                "object": doc.get("object", {}).get("name", ""),
                "note": doc.get("note", ""),
                "logged": bool(lg) and not lg.get("partial"),
                "partial": bool(lg.get("partial")),
                "log_date": lg.get("date", ""),
                "made": lg.get("made", ""),
                "stuck": lg.get("stuck", ""),
                "link": lg.get("link", ""),
            }
        )
    entries.sort(key=lambda e: e["day"], reverse=True)
    st = state()
    INDEX.write_text(
        json.dumps({"thread": "bench", "state": st, "days": entries}, indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    return entries, st


def rebuild_progress(entries, st):
    """The build log: 168 cells and every line of evidence. This page is the point.

    It is the one artefact that gets visibly better every single day, which is the
    only motivation mechanism here that does not depend on willpower.
    """
    c = curriculum()
    by_day = {e["day"]: e for e in entries}
    logs = logs_on_disk()

    sections = []
    for p in c["phases"]:
        lo = (p["weeks"][0] - 1) * WEEK_LEN + 1
        hi = p["weeks"][1] * WEEK_LEN
        done = sum(1 for d in range(lo, hi + 1) if d in logs and not logs[d].get("partial"))
        cells = []
        for d in range(lo, hi + 1):
            e = by_day.get(d)
            if d in logs and logs[d].get("partial"):
                cls = "c part"
                tip = f"Day {d:03d} — in progress: {logs[d].get('made', '')}"
            elif d in logs:
                cls = "c done"
                tip = f"Day {d:03d} — {logs[d].get('made') or logs[d].get('did', 'logged')}"
            elif d == st["current_day"]:
                cls = "c now"
                tip = f"Day {d:03d} — up next"
            elif e:
                cls = "c open"
                tip = f"Day {d:03d} — delivered, not logged"
            else:
                cls = "c"
                tip = f"Day {d:03d}"
            if is_bench_test(d):
                cls += " bt"
            inner = f'<span title="{esc(tip)}"></span>'
            cells.append(
                f'<a class="{cls}" href="editions/{stem(d)}.html">{inner}</a>'
                if e
                else f'<i class="{cls}" title="{esc(tip)}"></i>'
            )
        sections.append(
            f'<section class="ph"><div class="phhead">'
            f'<span class="n">{p["phase"]:02d}</span>'
            f'<span class="t">{esc(p["title"])}</span>'
            f'<span class="c2">{done}/28</span></div>'
            f'<div class="qq">{esc(p["question"])}</div>'
            f'<div class="grid">{"".join(cells)}</div>'
            f'<div class="ms">{esc(p["milestone"])}</div></section>'
        )

    rows = []
    for e in entries:
        if not e["logged"]:
            continue
        made = e["made"] or "logged"
        link = (
            f' <a href="{esc(e["link"])}" target="_blank" rel="noopener">evidence &rarr;</a>'
            if e["link"]
            else ""
        )
        stuck = f'<span class="stuck">stuck: {esc(e["stuck"])}</span>' if e["stuck"] else ""
        rows.append(
            f'<li><a class="d" href="editions/{stem(e["day"])}.html">{stem(e["day"])}</a>'
            f'<span class="dt">{esc(e["log_date"])}</span>'
            f'<span class="made">{esc(made)}{link}</span>{stuck}</li>'
        )
    if not rows:
        rows.append('<li class="empty">Nothing logged yet. Day 001 is waiting.</li>')

    pct = round(st["completed"] / TOTAL_DAYS * 100)
    tokens = {
        "NAV": nav("progress", "", latest=max((e["day"] for e in entries), default=None), here="Build log"),
        "DONE": str(st["completed"]),
        "TOTAL": str(TOTAL_DAYS),
        "PCT": str(pct),
        "STREAK": str(st["streak"]),
        "DRIFT": f"{st['drift']}" if st["drift"] else "0",
        "CURRENT": stem(st["current_day"]),
        "SECTIONS": "".join(sections),
        "ROWS": "".join(rows),
        "STARTED": esc(st["started"] or "not yet"),
    }
    out = PROGRESS_TEMPLATE.read_text(encoding="utf-8")
    for k, v in tokens.items():
        out = out.replace(f"[[{k}]]", v)
    left = re.findall(r"\[\[[A-Z0-9_]+\]\]", out)
    if left:
        raise Bad(f"progress template tokens left unfilled: {sorted(set(left))}")
    PROGRESS.write_text(out, encoding="utf-8")
    return PROGRESS


def buy_links(c, item_id, where):
    """Per shop, one link for each distinct product the item bundles.

    Never a product URL. Shopee listings are seller-specific and go dead constantly,
    and a dead link is worse than a live search. But one search per bundle does not
    work either: a query naming six things at once matches none of them well, so a
    craft-kit search comes back full of notebooks. One short query per real product.
    Nhat Tao is a physical market, so its link is a map.
    """
    kit = c["kit"][item_id]
    searches = kit.get("search") or []
    if isinstance(searches, str):
        searches = [{"q": searches, "icon": ""}]
    out = []
    for name in where:
        shop = c["shops"].get(name)
        if not shop:
            continue
        tpl = shop.get("search_url")
        if tpl and "{q}" in tpl and searches:
            chips = [
                (s["q"], tpl.replace("{q}", urllib.parse.quote_plus(s["q"])),
                 s.get("icon", ""))
                for s in searches
            ]
        elif tpl:
            # A market, or a shop with no search: one link, labelled for what it is.
            chips = [("open map" if "google.com/maps" in tpl else "visit", tpl, "")]
        elif shop.get("url"):
            chips = [("visit", shop["url"], "")]
        else:
            continue
        out.append((name, shop.get("where", ""), chips))
    return out


def rebuild_kit(st):
    """The supply list as a swipeable deck, one part per card.

    Filed under the week the order has to be placed. Ticks persist in localStorage,
    so this doubles as the thing you actually shop from on a phone. Nothing here is
    a server; it is a static page that remembers.
    """
    c = curriculum()
    cur_week = week_of(st["current_day"])

    items = []
    for w in c["weeks"]:
        for o in prep_for_week(w["week"]):
            items.append((w, o))

    cards, steps = [], []
    for i, (w, o) in enumerate(items, 1):
        links = "".join(
            f'<div class="shopgrp"><div class="sh"><span class="nm">{esc(name)}</span>'
            + (f'<span class="ad">{esc(addr)}</span>' if addr else "")
            + "</div><div class=\"chips\">"
            + "".join(
                f'<a class="chip" href="{esc(url)}" target="_blank" rel="noopener"'
                + (f' data-icon="{esc(icon)}"' if icon else "")
                + ">"
                + (glyphs.svg(icon) if icon else "")
                + f"<span>{esc(term)}</span></a>"
                for term, url, icon in chips
            )
            + "</div></div>"
            for name, addr, chips in buy_links(c, o["id"], o["where"])
        )
        need = (
            f'week {o["needed_week"]} &middot; day {stem(o["needed_day"])}'
            if o["needed_week"]
            else "keep on hand"
        )
        state_cls = "past" if w["week"] < cur_week else ("now" if w["week"] == cur_week else "")
        cards.append(
            f'<article class="card {state_cls}" id="i{i}">'
            f'<div class="chead"><span class="idx">{i:02d}<span class="of">/{len(items):02d}</span></span>'
            f'<span class="wk">Order week {w["week"]}</span></div>'
            f'<h2>{esc(o["name"])}</h2>'
            f'<p class="why">{esc(o["why"])}</p>'
            f'<dl class="spec">'
            f'<div><dt>Price</dt><dd class="hi">{esc(o["vnd"])}</dd></div>'
            f'<div><dt>Lead time</dt><dd>{esc(o["lead"])}</dd></div>'
            f'<div><dt>Needed by</dt><dd>{need}</dd></div>'
            f"</dl>"
            f'<div class="buys">{links}</div>'
            f'<label class="own"><input type="checkbox" data-k="{esc(o["id"])}">'
            f"<span>In hand</span></label>"
            "</article>"
        )
        steps.append(
            f'<button type="button" class="step" data-i="{i}" '
            f'data-k="{esc(o["id"])}" title="{esc(o["name"])}">{i:02d}</button>'
        )

    shops = "".join(
        f'<li><span class="nm">'
        + (
            f'<a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(name)}</a>'
            if s.get("url")
            else esc(name)
        )
        + f'</span><span class="ad">{esc(s.get("where", ""))}</span>'
        f'<span class="nt">{esc(s.get("note", ""))}</span></li>'
        for name, s in c["shops"].items()
    )

    tokens = {
        "NAV": nav("kit", "", latest=max((d for d, _ in delivered_days()), default=None), here="Kit"),
        "CARDS": "".join(cards),
        "STEPS": "".join(steps),
        "COUNT": f"{len(items):02d}",
        "SHOPS": shops,
        "WEEK": str(cur_week),
    }
    out = (ROOT / "kit.template.html").read_text(encoding="utf-8")
    for k, v in tokens.items():
        out = out.replace(f"[[{k}]]", v)
    left = re.findall(r"\[\[[A-Z0-9_]+\]\]", out)
    if left:
        raise Bad(f"kit template tokens left unfilled: {sorted(set(left))}")
    path = ROOT / "kit.html"
    path.write_text(out, encoding="utf-8")
    return path


def rebuild_all():
    logs = logs_on_disk()
    entries, st = rebuild_index(delivered_days(), logs)
    rebuild_progress(entries, st)
    rebuild_kit(st)
    sys.path.insert(0, str(SITE))
    import site_index

    site_index.rebuild()
    return entries, st


# ------------------------------------------------------------------- commands

def cmd_status(args):
    st = state()
    phase, week = spine(st["current_day"])
    print(f"today {st['today']}   day {stem(st['current_day'])}/{TOTAL_DAYS}   "
          f"P{phase['phase']:02d} {phase['title']}   W{week['week']} {week['title']}")
    print(f"done {st['completed']}   streak {st['streak']}d   drift {st['drift']}d   "
          f"elapsed {st['elapsed']}d   started {st['started'] or 'not yet'}")
    due = deadline_day(week)
    print(f"project: {week['project']['name']} — due day {stem(due)}, "
          f"{due - st['current_day']} days out")
    if st["unlogged"]:
        print(f"delivered but not logged: {', '.join(stem(d) for d in st['unlogged'])}")
    orders = prep_for_week(week["week"])
    if orders:
        print(f"order this week: {'; '.join(o['name'].split(':')[0] for o in orders)}")
    if st["re_entry"]:
        print(f"RE-ENTRY: {st['silent_days']} days quiet -- author a short day, 25 min ceiling")
    if st["finished"]:
        print("the curriculum is complete")
    return 0


def cmd_plan(args):
    day = args.day or state()["current_day"]
    phase, week = spine(day)
    kind = "BENCH TEST" if is_bench_test(day) else "BUILD DAY"
    due = deadline_day(week)
    print(f"day {stem(day)}  {kind}  day {(day - 1) % WEEK_LEN + 1} of week {week['week']}")
    print(f"phase {phase['phase']:02d}  {phase['title']}")
    print(f"  question:  {phase['question']}")
    print(f"  milestone: {phase['milestone']}")
    print(f"week {week['week']}  {week['title']}")
    print(f"  arc:    {week['arc']}")
    print(f"  covers: {', '.join(week['covers'])}")
    p = week["project"]
    print(f"\nproject: {p['name']}   due day {stem(due)} ({due - day} days out)")
    print(f"  spec:        {p['spec']}")
    print(f"  deliverable: {p['deliverable']}")
    if p.get("stretch"):
        print(f"  stretch:     {p['stretch']}")
    if week.get("kit"):
        print(f"\nkit in use this week: {', '.join(week['kit'])}")
    orders = prep_for_week(week["week"])
    if orders:
        print("\nORDER THIS WEEK:")
        for o in orders:
            need = f"needed week {o['needed_week']}" if o["needed_week"] else "keep on hand"
            print(f"  - {o['name']}")
            print(f"      {o['vnd']} · {o['lead']} · {need} · {', '.join(o['where'])}")
    if week.get("sources"):
        print(f"\nsuggested sources: {', '.join(week['sources'])}")

    obj = curriculum().get("objects")
    if obj:
        # Rotated by day number rather than chosen at random, so a run is reproducible
        # and consecutive nights never draw the same well twice.
        pool = [s for s in obj["sources"] if phase["phase"] in s.get("phases", [])]
        pool = pool or obj["sources"]
        pick = [pool[(day * 3 + i) % len(pool)] for i in range(3)]
        seen, uniq = set(), []
        for s in pick:
            if s["name"] not in seen:
                seen.add(s["name"])
                uniq.append(s)
        print("\nTHE OBJECT -- hunt here tonight (never repeat one, check the ledger):")
        for s in uniq:
            print(f"  {s['name']}  {s['url']}")
            print(f"      {s['lens']}")
        veins = obj.get("veins", [])
        if veins:
            print(f"  off-web: {veins[day % len(veins)]}")
    return 0


def cmd_kit(args):
    c = curriculum()
    st = state()
    wk = args.week or week_of(st["current_day"])
    weeks = c["weeks"] if args.all else [w for w in c["weeks"] if w["week"] == wk]
    any_order = False
    for w in weeks:
        orders = prep_for_week(w["week"])
        if not orders:
            continue
        any_order = True
        print(f"\nweek {w['week']} — {w['title']}  (order now)")
        for o in orders:
            need = (
                f"needed week {o['needed_week']}, day {stem(o['needed_day'])}"
                if o["needed_week"]
                else "keep on hand"
            )
            print(f"  [ ] {o['name']}")
            print(f"      {o['why']}")
            print(f"      {o['vnd']} · lead {o['lead']} · {need}")
            for name in o["where"]:
                s = c["shops"].get(name, {})
                print(f"      {name}: {s.get('where', '')} {s.get('url', '')}".rstrip())
    if not any_order:
        print(f"week {wk}: nothing to order. Everything you need should already be on the bench.")
    if args.all:
        print("\nshops:")
        for name, s in c["shops"].items():
            print(f"  {name}: {s.get('where', '')} {s.get('url', '')}".rstrip())
            print(f"      {s.get('note', '')}")
    return 0


def cmd_ledger(args):
    st = state()
    all_days = days_on_disk()
    logs = logs_on_disk()
    sent = {d for d, _ in delivered_days()}
    ahead = sorted(d for d, _ in all_days if d not in sent)
    print(f"today: {st['today']}   next day to author: {stem(st['current_day'])}   "
          f"authored: {len(all_days)}   delivered: {len(sent)}   logged: {st['completed']}")
    if ahead:
        print(f"already written, not yet delivered: {', '.join(stem(d) for d in ahead)}"
              " -- build these rather than writing them again")
    print(f"streak: {st['streak']}d   drift: {st['drift']}d"
          + ("   RE-ENTRY (keep it short)" if st["re_entry"] else ""))
    if st["unlogged"]:
        print(f"\nnot logged yet: {', '.join(stem(d) for d in st['unlogged'])}")
        print("the gate: do not author past an unlogged day -- open the card by asking about it")
    if not all_days:
        print("\nno history yet")
        return 0
    print("\nalready used (never repeat a source or an object):")
    for day, doc in sorted(all_days, reverse=True)[: args.limit]:
        src = doc.get("source", {})
        mark = "x" if day in logs else ("-" if day in sent else " ")
        print(f"\n[{mark}] {stem(day)}  {doc.get('framing', '')}")
        if src:
            print(f"      {src.get('site')} — {src.get('title')} | {src.get('url')}")
        print(f"      object: {doc.get('object', {}).get('name', '')}")
        if doc.get("note"):
            print(f"      note: {doc['note']}")
        if day in logs:
            lg = logs[day]
            print(f"      made: {lg.get('made', '')}"
                  + (f" | stuck: {lg['stuck']}" if lg.get("stuck") else ""))
    return 0


def cmd_build(args):
    day = args.day or state()["current_day"]
    all_days = days_on_disk()
    logs = logs_on_disk()

    prev_done = (day - 1) in logs and not logs[day - 1].get("partial")
    if not args.force and day > 1 and not prev_done:
        why = (
            "is only part-logged" if (day - 1) in logs else "has no log"
        )
        raise Bad(
            f"day {stem(day - 1)} {why}, so day {stem(day)} is gated. "
            "The curriculum waits. Finish and log the previous day first, or pass --force."
        )

    prior_urls = {}
    for d, doc in all_days:
        if d == day:
            continue
        u = doc.get("source", {}).get("url")
        if u:
            prior_urls.setdefault(u, d)
    if args.allow_repeat:
        prior_urls = {}

    doc = load(DATA / f"{stem(day)}.json")
    blocks, total = validate(day, doc, prior_urls)
    st = state()

    EDITIONS.mkdir(parents=True, exist_ok=True)
    html_path = EDITIONS / f"{stem(day)}.html"
    txt_path = EDITIONS / f"{stem(day)}.txt"
    html_path.write_text(render_html(day, doc, blocks, total, st), encoding="utf-8")
    txt_path.write_text(render_text(day, doc, blocks, total, st), encoding="utf-8")

    rebuild_all()
    for p in (html_path, txt_path, INDEX, PROGRESS, ROOT / "kit.html", SITE / "index.html"):
        print(f"ok  {p}")
    print(f"    {total} min budgeted")
    return 0


def cmd_log(args):
    st = state()
    day = args.day or (st["unlogged"][0] if st["unlogged"] else st["current_day"])
    if not (DATA / f"{stem(day)}.json").exists():
        raise Bad(f"day {stem(day)} was never delivered, so there is nothing to log")

    LOGS.mkdir(parents=True, exist_ok=True)
    entry = {
        "day": day,
        "date": args.date or today().isoformat(),
        "did": check_text("did", args.did),
        "made": check_text("made", args.made),
    }
    if args.partial:
        entry["partial"] = True
    if args.stuck:
        entry["stuck"] = check_text("stuck", args.stuck)
    if args.link:
        if not args.link.startswith("http"):
            raise Bad("link must be an absolute URL")
        entry["link"] = args.link
    if args.minutes:
        entry["minutes"] = args.minutes

    path = LOGS / f"{stem(day)}.json"
    path.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _, new = rebuild_all()
    print(f"ok  {path}")
    if args.partial:
        print(f"    day {stem(day)} part-logged. streak {new['streak']}d holds -- you sat down.")
        print(f"    tomorrow hands you day {stem(day)} again to finish, not day {stem(day + 1)}.")
    else:
        print(f"    day {stem(day)} logged. streak {new['streak']}d, "
              f"{new['completed']}/{TOTAL_DAYS} done. next up: {stem(new['current_day'])}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("status", help="day, streak, drift, what is gated")
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("plan", help="the curriculum spine, project and deadline for a day")
    p.add_argument("--day", type=int)
    p.set_defaults(fn=cmd_plan)

    p = sub.add_parser("kit", help="what to buy, where in HCMC, and by when")
    p.add_argument("--week", type=int)
    p.add_argument("--all", action="store_true", help="the whole course supply list")
    p.set_defaults(fn=cmd_kit)

    p = sub.add_parser("ledger", help="history digest and the next day to author")
    p.add_argument("--limit", type=int, default=14)
    p.set_defaults(fn=cmd_ledger)

    p = sub.add_parser("build", help="validate and render one day")
    p.add_argument("--day", type=int)
    p.add_argument("--allow-repeat", action="store_true", help="skip the reused-source check")
    p.add_argument("--force", action="store_true", help="author past an unlogged day")
    p.set_defaults(fn=cmd_build)

    p = sub.add_parser("log", help="close a day with evidence")
    p.add_argument("--day", type=int)
    p.add_argument("--date", help="YYYY-MM-DD, defaults to today in Asia/Ho_Chi_Minh")
    p.add_argument("--did", required=True, help="what actually happened, one line")
    p.add_argument("--made", required=True, help="what exists now that did not before")
    p.add_argument("--stuck", help="where it snagged")
    p.add_argument("--link", help="photo, gist, commit -- the evidence")
    p.add_argument("--minutes", type=int, help="how long it really took")
    p.add_argument("--partial", action="store_true",
                   help="ran out of time: keeps the streak, does not advance the day")
    p.set_defaults(fn=cmd_log)

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except Bad as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
