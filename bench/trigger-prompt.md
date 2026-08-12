# Scheduled task prompt

The prompt body for the nightly Bench routine (cron `0 12 * * *` UTC = 19:00 GMT+7,
fresh session per firing, push and email notifications on). Everything substantive lives
in `CLAUDE.md`; the prompt only points at it and states the few things a fresh session
cannot infer.

This file is a copy for reference. Editing it does not change the routine -- edit the
scheduled task itself.

---

Run Bench for tonight.

The runbook is CLAUDE.md in the myThreads repo, section "Bench". Read it and follow "The
Bench run" -- it holds the gate, the schema, the build commands and the tone. The repo is
the memory: `bench/curriculum.json` is the fixed spine, `bench/data/` is what has been
written, `bench/logs/` is what he actually did.

Five things the runbook cannot tell you:

1. Work on `main`, which is the default branch. Committing tonight's day straight to it is
   expected and authorised, and no pull request is wanted. Pushing is also what deploys to
   GitHub Pages, so there is nothing else to publish.

2. Start with `python3 bench/bench.py status`. It tells you the day, the streak, the drift,
   and whether the previous day was logged. If the previous day has no log, the next day is
   gated and `build` will refuse. That refusal is the feature. Do not pass `--force` to get
   around it -- instead deliver nothing new, and make the entire message a short, unbothered
   nudge naming the unlogged day and the one-line command that closes it.

3. Week 1 is already written. `bench/data/001.json` through `007.json` exist. For those days
   the job is only to `build` and send, not to write. From day 008 you author the day
   yourself against `bench.py plan`, which gives you the week's project, deadline and kit.

4. If `WebFetch` returns 403 on hosts that are plainly reachable, the network is not down --
   fetch with `curl` instead. Never cite a source you did not open, and never invent a URL:
   check it resolves before it goes in the JSON.

5. Your final message is the contents of `bench/editions/<NNN>.txt`, verbatim and nothing
   else -- no preamble, no status update, no sign-off, no Markdown. It is sent as a push
   notification and an email. If the run genuinely failed, the entire final message is
   instead one plain line saying what broke and whether a day was delivered.
