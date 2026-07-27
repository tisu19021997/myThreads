# Scheduled task prompt

The prompt body for the daily Morning Spark routine (cron `0 1 * * *` UTC = 08:00 GMT+7,
fresh session per firing, push and email notifications on). Everything substantive lives
in `CLAUDE.md`; the prompt only points at it and states the few things a fresh session
cannot infer.

This file is a copy for reference. Editing it does not change the routine -- paste the
body below into the scheduled task itself.

---

Run Morning Spark for today.

The runbook is CLAUDE.md in the myThreads repo. Read it and follow the "The run" section
-- it holds the sources, the data schema, the build commands and the tone. The repo is the
memory; nothing lives in Google Drive any more, so do not search Drive.

Three things the runbook cannot tell you:

1. Work on `main`, which is the default branch. Committing today's edition straight to it
   is expected and authorised, and no pull request is wanted. Pushing is also what
   deploys the edition to GitHub Pages, so there is nothing else to publish.

2. If `WebFetch` returns 403 on hosts that are plainly reachable, the network is not down
   -- fetch with `curl` instead. Do not abandon a run over it, and never assemble sparks
   out of search snippets you have not read.

3. Your final message is the contents of `morning-spark/editions/<today>.txt`, verbatim
   and nothing else -- no preamble, no status update, no sign-off, no Markdown. It is
   sent as a push notification and an email. If the run genuinely failed, the entire
   final message is instead one plain line saying what broke and whether an edition was
   produced.
