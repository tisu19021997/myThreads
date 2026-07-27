# Scheduled task prompt

The prompt body for the daily Morning Spark routine (cron `0 1 * * *` UTC = 08:00 GMT+7,
fresh session per firing, push and email notifications on). Everything substantive lives
in `CLAUDE.md`; the prompt only points at it and states the two things a fresh session
cannot infer.

---

Run Morning Spark for today.

The runbook is CLAUDE.md in the myThreads repo. Read it and follow the "The run" section
-- it holds the sources, the data schema, the build commands and the tone. The repo is the
memory; nothing lives in Google Drive any more, so do not search Drive.

Two things the runbook cannot tell you:

1. Work on `main`. Committing today's edition straight to `main` is expected and
   authorised -- the ledger only dedupes correctly if every edition lands on the default
   branch.

2. Your final message is the contents of `morning-spark/editions/<today>.txt`, verbatim
   and nothing else -- no preamble, no status update, no sign-off, no Markdown. It is
   sent as a push notification and an email. If the run genuinely failed, the entire
   final message is instead one plain line saying what broke and whether an edition was
   produced.
