#!/usr/bin/env python3
"""Morning Spark build tool.

  spark.py ledger [--limit N]        compact history + next edition number (read this before curating)
  spark.py build [--date YYYY-MM-DD] validate data/<date>.json -> editions/<date>.{html,txt} + index.json

No dependencies. Data is the source of truth; HTML and text are generated.
"""

import argparse
import datetime as dt
import html
import json
import pathlib
import re
import sys
import zoneinfo

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data"
EDITIONS = ROOT / "editions"
TEMPLATE = ROOT / "template.html"
INDEX = ROOT / "index.json"
SITE = ROOT.parent
HOME = SITE / "index.html"
NOJEKYLL = SITE / ".nojekyll"
TZ = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
SEP = "─" * 17

# Emoji and decorative symbols are rejected in authored data. The arrows and rules
# the generated chrome uses are added by this script, never by the data file.
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

SPARK_FIELDS = ["title", "headline", "result", "tick", "provocation", "a", "b"]
SIDE_FIELDS = ["who", "what"]

# Every authored string exists twice: English, and a `_vi` twin. Names, URLs and dates
# are not translated. The Vietnamese is written, not machine-translated -- keep the
# English loanwords Vietnamese product people actually say (output, outcome, retention,
# agent, proxy metric) rather than forcing Sino-Vietnamese equivalents nobody uses.
BILINGUAL = ["title", "headline", "result", "tick", "provocation"]


class Bad(Exception):
    pass


def today():
    return dt.datetime.now(TZ).date().isoformat()


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Bad(f"missing {path}")
    except json.JSONDecodeError as e:
        raise Bad(f"{path.name} is not valid JSON: {e}")


def editions_on_disk():
    out = []
    for p in sorted(DATA.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].json")):
        out.append((p.stem, load(p)))
    return out


# ---------------------------------------------------------------- validation

def check_text(where, value):
    if not isinstance(value, str) or not value.strip():
        raise Bad(f"{where}: must be a non-empty string")
    hit = EMOJI.search(value)
    if hit:
        raise Bad(f"{where}: emoji or symbol {hit.group()!r} is not allowed")
    return value.strip()


def validate(date, doc, prior_urls):
    if doc.get("date") != date:
        raise Bad(f"date field {doc.get('date')!r} does not match filename {date}")
    if not isinstance(doc.get("edition"), int):
        raise Bad("edition must be an integer")
    check_text("framing", doc.get("framing", ""))
    check_text("framing_vi", doc.get("framing_vi", ""))
    sparks = doc.get("sparks")
    if not isinstance(sparks, list) or len(sparks) != 3:
        raise Bad("sparks must be a list of exactly 3 entries")

    seen_here = set()
    for i, s in enumerate(sparks, 1):
        for f in SPARK_FIELDS:
            if f not in s:
                raise Bad(f"spark {i}: missing field {f!r}")
        for f in BILINGUAL:
            check_text(f"spark {i}.{f}", s[f])
            check_text(f"spark {i}.{f}_vi", s.get(f + "_vi", ""))
        for side in ("a", "b"):
            for f in SIDE_FIELDS:
                check_text(f"spark {i}.{side}.{f}", s[side].get(f, ""))
            check_text(f"spark {i}.{side}.what_vi", s[side].get("what_vi", ""))

        for suffix in ("", "_vi"):
            under = s.get("result_underline" + suffix, "")
            if under and under not in s["result" + suffix]:
                raise Bad(
                    f"spark {i}: result_underline{suffix} {under!r} not found in result{suffix}"
                )
            for b in s.get("tick_bold" + suffix, []):
                if b not in s["tick" + suffix]:
                    raise Bad(f"spark {i}: tick_bold{suffix} {b!r} not found in tick{suffix}")

        src = s.get("source", {})
        for f in ("title", "site", "url"):
            check_text(f"spark {i}.source.{f}", src.get(f, ""))
        url = src["url"]
        if not url.startswith("http"):
            raise Bad(f"spark {i}: source.url must be an absolute URL")
        if url in seen_here:
            raise Bad(f"spark {i}: source.url repeated inside this edition")
        seen_here.add(url)
        if url in prior_urls:
            raise Bad(
                f"spark {i}: {url} was already used on {prior_urls[url]} "
                "(pass --allow-repeat to override)"
            )
    return sparks


# ------------------------------------------------------------------ rendering

def esc(s):
    return html.escape(s, quote=True)


def wrap(text, phrase, tag):
    """Escape text, then wrap the escaped form of `phrase` in `tag`."""
    out = esc(text)
    if phrase:
        out = out.replace(esc(phrase), f"<{tag}>{esc(phrase)}</{tag}>", 1)
    return out


def wrap_all(text, phrases, tag):
    out = esc(text)
    for p in phrases:
        out = out.replace(esc(p), f"<{tag}>{esc(p)}</{tag}>", 1)
    return out


def ednav(date, all_dates):
    """Previous and next edition, plus the way back to the front door.

    Sits at the foot of the card rather than the head: a spark is read once, top to
    bottom, and nobody wants navigation competing with the first collision. Only
    dates that exist are linked, so nothing here can 404.
    """
    older = max((d for d in all_dates if d < date), default=None)
    newer = min((d for d in all_dates if d > date), default=None)

    def side(d, arrow, label_en, label_vi, cls):
        if not d:
            return f'<span class="pn off">{arrow}</span>'
        return (
            f'<a class="pn {cls}" href="{esc(d)}.html">'
            f'<span class="ar">{arrow}</span>'
            f'<span class="dt"><span data-l="en">{label_en}</span>'
            f'<span data-l="vi">{label_vi}</span><br>{esc(d)}</span></a>'
        )

    return (
        '<nav class="ednav">'
        + side(older, "&larr;", "Previous", "Hôm trước", "prev")
        + '<a class="all" href="../../index.html">'
        '<span data-l="en">All threads</span><span data-l="vi">Tất cả</span></a>'
        + side(newer, "&rarr;", "Next", "Hôm sau", "next")
        + "</nav>"
    )


def render_html(date, doc, sparks):
    d = dt.date.fromisoformat(date)
    tokens = {
        "DATE_SHORT": d.strftime("%b %-d"),
        "DATE_LONG": d.strftime("%A, %B %-d, %Y"),
        "ED": f"{doc['edition']:02d}",
    }
    people = []
    for i, s in enumerate(sparks, 1):
        p = f"S{i}_"
        tokens[p + "WHO_A"] = esc(s["a"]["who"])
        tokens[p + "WHO_B"] = esc(s["b"]["who"])
        tokens[p + "URL"] = esc(s["source"]["url"])
        tokens[p + "SRC"] = esc(f"{s['source']['site']} — {s['source']['title']}")
        for suffix, key in (("", ""), ("_VI", "_vi")):
            tokens[p + "TITLE" + suffix] = esc(s["title" + key].upper())
            tokens[p + "WHAT_A" + suffix] = esc(s["a"]["what" + key])
            tokens[p + "WHAT_B" + suffix] = esc(s["b"]["what" + key])
            tokens[p + "RESULT" + suffix] = wrap(
                s["result" + key], s.get("result_underline" + key, ""), "u"
            )
            tokens[p + "TICK" + suffix] = wrap_all(
                s["tick" + key], s.get("tick_bold" + key, []), "b"
            )
        for who in (s["a"]["who"], s["b"]["who"]):
            if who not in people:
                people.append(who)
    tokens["SOURCES_NAMES"] = esc(" / ".join(people))
    tokens["EDNAV"] = ednav(date, [d for d, _ in editions_on_disk()])

    out = TEMPLATE.read_text(encoding="utf-8")
    for k, v in tokens.items():
        out = out.replace(f"[[{k}]]", v)
    left = re.findall(r"\[\[[A-Z0-9_]+\]\]", out)
    if left:
        raise Bad(f"template tokens left unfilled: {sorted(set(left))}")
    return out


def render_text(date, doc, sparks):
    d = dt.date.fromisoformat(date)
    blocks = [
        f"Morning Spark · {d.strftime('%A, %B %-d')} · Ed. {doc['edition']:02d}\n"
        f"{doc['framing']}"
    ]
    for i, s in enumerate(sparks, 1):
        blocks.append(
            f"{SEP}\n"
            f"{i:02d} · {s['headline']}\n"
            f"{s['a']['who']} × {s['b']['who']}\n"
            f"{s['provocation']}\n"
            f"→ {s['source']['url']}"
        )
    blocks.append(doc.get("footer", "Full styled card → open the session."))
    return "\n\n".join(blocks) + "\n"


def rebuild_index(all_editions):
    entries = []
    for date, doc in all_editions:
        entries.append(
            {
                "date": date,
                "edition": doc["edition"],
                "note": doc.get("note", ""),
                "sparks": [
                    {
                        "pair": f"{s['a']['who']} x {s['b']['who']}",
                        "headline": s["headline"],
                        "source": f"{s['source']['site']} — {s['source']['title']}",
                        "url": s["source"]["url"],
                    }
                    for s in doc["sparks"]
                ],
            }
        )
    entries.sort(key=lambda e: e["date"], reverse=True)
    INDEX.write_text(
        json.dumps({"editions": entries}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return entries


def rebuild_home(entries):
    """The GitHub Pages front door: a plain list of links, deliberately unstyled.

    The repo now carries more than one thread, so the front door is built from every
    thread's index.json rather than from this one alone. `entries` is written to
    index.json before this runs, so site_index picks the new edition up from there.
    """
    sys.path.insert(0, str(SITE))
    import site_index

    return site_index.rebuild()


# ------------------------------------------------------------------- commands

def cmd_ledger(args):
    all_editions = editions_on_disk()
    next_ed = max((d.get("edition", 0) for _, d in all_editions), default=0) + 1
    print(f"today: {today()}   next edition: {next_ed}   editions on file: {len(all_editions)}")
    if not all_editions:
        print("no history yet")
        return 0
    print("\nalready used (do not repeat a piece or a pairing):")
    for date, doc in sorted(all_editions, reverse=True)[: args.limit]:
        print(f"\n{date}  Ed. {doc.get('edition')}")
        for s in doc["sparks"]:
            print(f"  {s['a']['who']} x {s['b']['who']} | {s['source']['title']} | {s['source']['url']}")
        if doc.get("note"):
            print(f"  note: {doc['note']}")
    return 0


def cmd_build(args):
    date = args.date or today()
    all_editions = editions_on_disk()
    prior_urls = {}
    for d, doc in all_editions:
        if d == date:
            continue
        for s in doc.get("sparks", []):
            prior_urls.setdefault(s.get("source", {}).get("url", ""), d)
    if args.allow_repeat:
        prior_urls = {}

    doc = load(DATA / f"{date}.json")
    sparks = validate(date, doc, prior_urls)

    EDITIONS.mkdir(parents=True, exist_ok=True)
    html_path = EDITIONS / f"{date}.html"
    txt_path = EDITIONS / f"{date}.txt"
    html_path.write_text(render_html(date, doc, sparks), encoding="utf-8")
    txt_path.write_text(render_text(date, doc, sparks), encoding="utf-8")

    if not any(d == date for d, _ in all_editions):
        all_editions.append((date, doc))
    rebuild_home(rebuild_index(all_editions))

    print(f"ok  {html_path}")
    print(f"ok  {txt_path}")
    print(f"ok  {INDEX}")
    print(f"ok  {HOME}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ledger", help="print history digest and next edition number")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(fn=cmd_ledger)

    p = sub.add_parser("build", help="validate and render one edition")
    p.add_argument("--date", help="YYYY-MM-DD, defaults to today in Asia/Ho_Chi_Minh")
    p.add_argument("--allow-repeat", action="store_true", help="skip the reused-source check")
    p.set_defaults(fn=cmd_build)

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except Bad as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
