# myThreads

Tisu's personal thread of daily inputs. He builds products and works in AI / data science.
Everything here is data-first: a run writes JSON, and generated artifacts are rendered from it.

---

# Morning Spark

Three idea-collisions to start the day, delivered every morning at 08:00 (GMT+7) by a
scheduled task. This repo is the sink: the JSON in `morning-spark/data/` is the memory
that keeps the task from repeating itself, and every spark carries an out-link so the
whole story is one click away.

## Layout

```
morning-spark/
  spark.py            build tool (stdlib only)
  template.html       fixed layout, tokens are [[LIKE_THIS]] -- do not edit the CSS or structure
  data/YYYY-MM-DD.json   the edition, hand-authored -- the only file you write by hand
  editions/YYYY-MM-DD.html  generated
  editions/YYYY-MM-DD.txt   generated -- this is the message you send
  index.json          generated rollup of every spark ever sent
```

## What a spark is

A collision of two thinkers' ideas producing a fresh third thought (1 + 1 = 3), plus a
one-line "tick": a provocative question to carry all day. Three per day, three different
pairings, each tied to a builder / AI / data lens.

Tone: minimalist, Braun / Teenage-Engineering. No emoji anywhere (`spark.py` enforces this).
Every claim grounded in a real piece you actually read -- no bluffing.

## Sources (rotate; they post infrequently, so "most recent strong piece" is fine)

| | | |
|---|---|---|
| Lenny Rachitsky | https://www.lennysnewsletter.com/ | |
| Ben Thompson | https://stratechery.com/ | aggregation theory, agents |
| Teresa Torres | https://www.producttalk.org/ | continuous discovery |
| April Dunford | https://www.aprildunford.com/blog | positioning |
| John Cutler | https://cutlefish.substack.com/ | |
| Jason Cohen | https://longform.asmartbear.com/ | |
| Marty Cagan | https://www.svpg.com/articles/ | empowered teams |
| Gibson Biddle | https://gibsonbiddle.com/ | DHM, proxy metrics |
| Brian Balfour | https://brianbalfour.com/essays | growth loops |
| Andrew Chen | https://andrewchen.com/ | network effects, cold start |
| Paul Graham | https://paulgraham.com/articles.html | make something people want |
| Melissa Perri | https://melissaperri.com/ | |

The second half of a collision may be another fetched piece or one of the signature
frameworks above -- represent it faithfully. Vary pairings daily, don't let one source
dominate, and anchor at least one spark on something recently published.

## The run

1. `python3 morning-spark/spark.py ledger` -- gives today's date, the next edition number,
   and everything already sent. Do not reuse a piece or a pairing from it.
2. Search and fetch. Read at least one of the two pieces behind each spark so the idea is
   accurate, and keep the exact URL you read.
3. Write `morning-spark/data/<today>.json` (schema below).
4. `python3 morning-spark/spark.py build` -- validates, renders both editions, updates
   `index.json`. It fails loudly on emoji, missing fields, or a source URL already used;
   fix the JSON and run it again.
5. `SendUserFile` on `morning-spark/editions/<today>.html`, status `proactive`,
   display `render`, one-line caption.
6. Commit and push: `git add -A && git commit && git push -u origin main`.
7. Your final message is the contents of `morning-spark/editions/<today>.txt`, verbatim --
   it becomes the push notification and email. Nothing else: no preamble, no status update,
   no sign-off, no Markdown. If the run genuinely failed, the whole final message is instead
   one plain line saying what broke and whether an edition was produced.

## Data schema

```json
{
  "date": "2026-07-27",
  "edition": 1,
  "framing": "One short framing line, max 12 words.",
  "note": "One line on themes used, so tomorrow can avoid them.",
  "sparks": [
    {
      "title": "TWO OR THREE WORD KICKER",
      "headline": "Short punchy headline",
      "a": {"who": "Ben Thompson", "what": "What his piece or framework actually argues."},
      "b": {"who": "April Dunford", "what": "What hers argues."},
      "result": "The fresh third thought, one or two lines, ending on the punchiest tail.",
      "result_underline": "the punchiest tail",
      "tick": "The question he carries all day.",
      "tick_bold": ["the key words"],
      "provocation": "One or two plain sentences for the text edition.",
      "source": {
        "site": "Stratechery",
        "title": "Title of the piece you read",
        "url": "https://stratechery.com/...",
        "published": "2026-07-21"
      }
    }
  ]
}
```

`result_underline` must be a substring of `result`; each `tick_bold` entry must be a
substring of `tick`. The script escapes everything and applies the markup, so never put
HTML in the JSON. Three sparks exactly.

## Pushing

The scheduled run commits its edition straight to `main` -- that is intended, and is the
standing permission for it. The ledger only works if every edition lands on the default
branch.
