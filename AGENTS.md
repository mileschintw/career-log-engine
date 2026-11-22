# AGENTS.md

This repo is a personal career log (a Log, with its Engine; see [GLOSSARY.md](GLOSSARY.md)), managed through the `career-log` skill in `skills/career-log/`. Read `skills/career-log/SKILL.md`, the skill entry point (the modes are in `skills/career-log/modes/`), before creating or editing anything here; its rules (provenance, attribution, gaps) apply to every file.

<!-- source-only -->
Here, in the Engine repo (`career-log-engine`, the Template's source), there is no Log: no entries, profile, direction or applications to read, and nothing to log, consolidate or save. Here the skill's Engine-change rules apply; its modes, setup and `docs/guide.md`'s *For agents* are for a Log, so do not run them here. There are three repos ([ADR 0015](docs/adr/0015-the-engine-is-developed-in-its-own-public-repo.md)): this one, public, holds the Engine's source and the maintainer's files; the Template, `career-log-template`, public, is this repo's export and is never edited by hand, and its issue forms and front page send its users' issues and pull requests here; the maintainer's Log, `career-log`, is private, and an Engine change found while using it is made here. [docs/maintaining.md](docs/maintaining.md) says more.
<!-- /source-only -->

Asked what this repo is or can do, where to start or what to do next ("introduce this repo and set me up"): read [docs/guide.md](docs/guide.md) and follow its *For agents*.

<!-- source-only -->
Here, in the Template's source, also read `docs/maintaining.md` at session start, and `docs/maintaining-tests.md` before testing an Engine change.

Multi-session work: records in the worktree on branch coord (find it with git worktree list; never merged); the coordinator runs /relay:coordinate, workers follow relay:work.
<!-- /source-only -->

Tool names in the skill (subagents, `Explore`, the PowerShell tool) are Claude Code's; use your agent's equivalent, or do the work inline.

<!-- source-only -->
When the user is migrating (moving to a new machine, account or checkout path, or just moved), follow `docs/migrating.md`.
<!-- /source-only -->

## Changes

Log data (entries, profile, direction, applications, outputs, sources) is committed as [SKILL.md › Commits](skills/career-log/SKILL.md) says. Engine changes change how the agent behaves: every path in the `ALLOW` list of `tools/export-template.sh` (the skill, `tools/` and the Template skeleton in `tools/template/`, `SETUP.md`, this file and `CLAUDE.md`, `GLOSSARY.md`, `docs/guide.md`, `docs/adr/`, `docs/upgrades/`, the two `.svg` files of `docs/social-preview/`, `.gitignore`, `.gitattributes`, `entries/_template.md`). `tools/checks_for.py` ([SETUP.md](SETUP.md) step 7) prints `engine: <path>` for each Engine path a change touches.

<!-- source-only -->
Here, this repo's CI in `.github/`, the maintainer docs the export leaves out (`docs/maintaining.md`, `docs/maintaining-tests.md`, `docs/migrating.md`, `docs/publishing.md`) and the maintainer's own tools in `maintainer/`, the project settings in `.claude/settings.json` (the relay plugin), `docs/agents/` and the root `LICENSE` (all left out the same way) are Engine too, and go through a pull request like the rest. The coordinating session's plan, briefs and reports are not in the default branch at all: they live on the `coord` branch, which relay's coordinator commits and pushes and which is never merged. A pull request here runs CI: read its result on the pull request before you ask the user to merge.
<!-- /source-only -->

An Engine change never goes straight to the default branch: first a branch, then an issue, then a pull request. Before its first edit, read [skills/career-log/engine-changes.md](skills/career-log/engine-changes.md): the steps, their exceptions, the checks to run, and keeping Engine files free of personal content.

<!-- source-only -->
Here, in the Template's source, read [docs/publishing.md](docs/publishing.md) before you publish a release, take an issue or pull request from a Template user, edit the Template's front page (`tools/template/README*.md`), or write Engine text only this repo's maintainer needs (a source-only block), and when the export fails (its scan, here against `tools/template/.export-deny`) or a CI run fails.
<!-- /source-only -->

<!-- source-only -->
## Agent skills

### Issue tracker

GitHub Issues on this repo, with relay's blocking and frontier rules. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
<!-- /source-only -->
