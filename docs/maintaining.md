# Maintaining this repo

Write a new maintainer rule here, or in the repo file it belongs to (the export, CI and release steps: [publishing.md](publishing.md)); Claude Code's auto-memory holds only reminders the repo does not carry, such as a deadline.

## The three repos

This is the **Engine repo**, `career-log-engine`: public, the Engine's source and everything only its maintainer needs (these docs, `maintainer/`, CI in `.github/`, `docs/agents/`, `docs/research/`, the project settings in `.claude/settings.json`). It holds **no Log**: no entries, profile, direction, applications, outputs or sources, and no `.export-deny`, `.export-cleared` or `.export-allow`. The other two ([ADR 0015](adr/0015-the-engine-is-developed-in-its-own-public-repo.md)):

- **The Template**, `career-log-template`, public: the export of this repo ([publishing.md](publishing.md)), what a user starts a Log from. Never edited by hand.
- **The maintainer's Log**, `career-log`, private: one person's Log, with the history, issues, pull requests and coordination records from before this repo existed. An Engine fault found while using it is fixed here, never in that Log.

The export here runs no name-coverage check and masks nothing: with no Log beside the source, its scan reads `tools/template/.export-deny`, the list every Log starts with. Every push here is a publication: keeping a name from the maintainer's Log out of a commit, its message included, is the maintainer's job before each push, and the pre-push check below refuses a push that carries one. Until the maintainer's Log is converted to a release made here, the coordination records stay on its private `coord` branch; this repo's `coord` branch starts empty.

## The pre-push check

A push from the maintainer's checkout of this repo runs `maintainer/hooks/pre-push`, which runs `maintainer/prepush.py hook`: it scans the commits the push sends (each commit message, and the name and contents of each file a commit adds or changes) against the `.export-deny` of the maintainer's own Log, as the export scans (whole words, case-insensitive), and refuses the push on a hit, naming the commit and the line, never the list. It fails closed: with no path configured, no file there, an empty list or no Python 3.11+, the push is refused. The path lives in this checkout's git config, never in a tracked file, and the list never enters this repo. It is the maintainer's guard only: an outside contributor has no such list and does not install the hook.

Set it up once per checkout of this repo (worktrees share the checkout's config, so its worktrees are covered too):

1. Point git at the repo's hooks. macOS and Windows PowerShell, in the checkout:

   ```sh
   git config core.hooksPath maintainer/hooks
   ```

   Check: `git config --get core.hooksPath` prints `maintainer/hooks`. On macOS, also `ls -l maintainer/hooks/pre-push` shows it executable (`x`); git checks it out so.
2. Name the deny list: the `.export-deny` at the root of the maintainer's Log checkout. macOS and Windows PowerShell: `git config careerlog.denylist <Log checkout>/.export-deny`, with the Log checkout's full path (forward slashes work on Windows; a leading `~` is expanded).
   Check: `git config --get careerlog.denylist` prints that path.
3. Confirm the hook is active. macOS: `python3 -I maintainer/prepush.py check`; Windows PowerShell: `py -3 -I maintainer/prepush.py check`.
   Check: it prints `OK: the pre-push hook is active; it scans against <n> patterns in <path>`, and `git push --dry-run origin HEAD` prints `OK: no name from the deny list in the commits this push sends` (the hook runs on a dry run too; with nothing to send it prints the same line).

On a `FAIL:` from the hook, take the name out of the commits it lists (amend the last commit, or rewrite the branch's unpushed commits) and push again; a name already pushed is published, so tell the user. To scan a range by hand: `python3 -I maintainer/prepush.py scan --deny <path> origin/master..HEAD` (Windows: `py -3 -I ...`). Never skip it with `git push --no-verify`.

## Rules

- **Conversation language.** Talk to the human user in Traditional Chinese (zh-TW) in every session, Engine work included: questions, answers, reports, wrap-ups, pull request summaries given in chat. Repo files stay in English (issues and pull request bodies too); file paths, technical names and quoted source text stay in their own language. A subagent reports to its parent in the language its prompt asks for.
- **Agent-first docs.** Write setup and instruction docs (`SETUP.md`, checklists, this file) for an agent to run, readable by a human too: numbered steps, the exact command for macOS and for Windows PowerShell (the reference shell there), and a check per step that says when it is done.
- **Coordinator plan.** When Engine work spans several sessions or pull requests, coordinate it with the relay plugin, installed at project scope by `.claude/settings.json`: a coordinator session runs `/relay:coordinate`, each worker follows `relay:work`. The plan, its history, the briefs, status files, reports and PR body drafts live on the orphan branch `coord`, checked out beside the main checkout as `career-log-coord` (`git worktree list` shows it), never merged into the default branch. Its `project.md` holds this repo's settings for relay: checks, test bar, off-limits paths, deny list. How issues are tracked and blocked: [`docs/agents/issue-tracker.md`](agents/issue-tracker.md). The records from before relay (the old `docs/coordination/` plan, orchestrator prompt and session brief) are kept in full in `coord`'s `plan-history.md`.
- **Log format changes.** A change to the Log's data format (an entry's front matter or sections, a `config.toml` field with no default, a `direction.md` section, the `outputs/applications/` layout, a `stories.md` mark) breaks the Logs made from an earlier release, so its pull request also writes the upgrade for them into the guide of the release not yet made ([ADR 0011](adr/0011-template-versions-and-upgrades.md)): a line under `## Changes` in `docs/upgrades/upgrade-next.md` naming the change and the step that migrates it, replacing the line `No Log format change yet.`; its step there, with what the user's agent must ask them; and, for what is mechanical, a check in `docs/upgrades/upgrade-next.py`'s `CHECKS`. Its Done when includes `docs/upgrades/test-next.sh`, which builds a scratch Log in the earlier format, upgraded by the guide through the upgrade mode. A **new setting** is not a Log format change: a Config field with a default in `tools/config.default.toml`, or a Direction item, breaks no Log, since `tools/config.py` reads the default (empty, for a Direction item) when the Log leaves it out. Its pull request writes it under `## 3. New settings` in `upgrade-next.md`, replacing the line `This release adds none.`, with what the user's agent asks them; it needs no `## Changes` line and no `test-next.sh`. A `## 3` entry still makes the release ship the guide, a patch release while `## Changes` says `No Log format change yet.` ([publishing.md](publishing.md)). `upgrade-next.*` start as copies of `upgrade-skeleton.*`, the guide's empty form: a change to that form goes into both while `upgrade-next.*` is still empty. An Engine-only change needs none.
