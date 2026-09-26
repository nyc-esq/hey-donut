# Working context for Claude sessions — hey-donut

---

## Your scope, and everyone else's

**You are part of the Donut Matters session** (with `~/Claude/Projects/Donut`). This repo is the wake word
and its training pipeline; the live training data is on Donut at `/data/wakeword`.

**The boundary map is `~/Claude/Projects/Donut/SESSIONS.md`**: every session, what it owns, who decides on the shared ground, and **what to do when the problem you have found is not yours**. Read it once.

**One Ring pushes.** When One Ring sends push P<n>, run `~/Claude/Projects/onering/bin/ring apply P<n>` and show Chris its output as-is. Ask "Ring apply P<n>?" On his yes, ask him to type `confirm <code>` with the code it printed, then run `ring apply P<n> <code>`. It refuses a wrong code, a change edited since he saw it, another lane's file, or anything but a CLAUDE.md or SESSIONS.md. If it applies, commit with the push id and journal it. If it refuses, don't make the change by hand; tell Chris. (Chris, 2026-09-26, in this session.)
