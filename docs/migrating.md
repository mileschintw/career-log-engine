# Migrating to a new machine, account or path

Claude Code's auto-memory, the records folder and session transcripts are outside git; plugins and the skill link are per machine. Step 1 runs on the old machine (or account, or path) before you leave it; steps 2–5 run on the new one before other work.

Steps 1, 3 and 4 run `maintainer/harness.py` from the checkout named, `python3 -I maintainer/harness.py records …` (`py -3 -I` on Windows); follow what it prints.

Placeholders:
- `<project folder>`: the name Claude Code gives a checkout's folder under `~/.claude/projects/`, which `harness.py records project-folder <checkout>` prints. `<old folder>` is the old main checkout's: run that on the old machine, or read it in `~/.claude/projects/` there (the same name when the path is unchanged).
- `<old home>`, `<old checkout's parent>`: the old machine's home folder and the folder holding its main checkout, as copied or mounted (on the same machine, the folders themselves). `<new checkout's parent>`: the folder holding the new main checkout.
- `<records>`: the records folder ([maintaining-tests.md › Records](maintaining-tests.md#records)), `career-log-experiments/` beside the main checkout. `<date>`: today, as `YYYY-MM-DD`.

1. **Old machine, before `cleanupPeriodDays` runs out**: from the old main checkout, run `harness.py records snapshot` (a checkout with no `maintainer/harness.py` yet: `git pull --ff-only` on the default branch first). It copies the Claude Code folders `~/.claude/projects/<old folder>*` into `<records>/snapshot-<date>/`.

   Done when: it printed no FAIL line, and `<records>/snapshot-<date>/` holds every transcript folder the coordinator plan names.
2. **Checkout, skill link and git identity.** Run [SETUP.md](../SETUP.md) steps 1–4.

   Done when: their checks pass.
3. **Records folder.** From the new main checkout, run `harness.py records move <old checkout's parent> <new checkout's parent>`. The coordinator plan is on the `coord` branch: from the new main checkout, `git fetch origin coord`, then `git worktree add ../career-log-coord coord`.

   Done when: it printed no FAIL line, and `git worktree list` shows `career-log-coord` on `[coord]`.
4. **Memory.** The memory (reminders the repo does not carry, such as a deadline) lives in `~/.claude/projects/<project folder>/memory/` of the main checkout; sessions in worktrees under `.claude/worktrees/` load it too. From the new main checkout, run `harness.py records memory <old home>/.claude/projects <old folder>`; when `<old home>` cannot be reached, give it the copy step 1 made, `harness.py records memory <records>/snapshot-<date> <old folder>`. It overwrites a memory file of the same name already in the new main checkout's project folder.

   Done when: it printed no FAIL line, and a new session in the checkout shows the `MEMORY.md` index in its context.
5. **Plugins.** The maintainer's skills come from two plugins:
   - `mattpocock-skills` (`writing-for-agents`, `code-review`, `pr`, …), from the `claude-plugins-official` marketplace: in an interactive `claude` terminal, `/plugin install mattpocock-skills@claude-plugins-official`.
   - `humanizer`, synced from the claude.ai account's plugin catalog: on a new account, add it there again.

   Done when: a new session's skill list shows `mattpocock-skills:writing-for-agents` and `humanizer:humanizer`.
