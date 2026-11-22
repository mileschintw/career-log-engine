# Supporting Codex, Cursor and Antigravity alongside Claude Code

Checked 2026-10-15 against the vendors' live docs (Claude Code docs with v2.1.277+ behaviour, Codex docs now served from learn.chatgpt.com, Cursor docs, Antigravity docs). Items I could not confirm from a primary source are marked **unverified**.

## Summary

- **One AGENTS.md is enough for the instructions, not for the skill.** All four tools can read AGENTS.md. Skill discovery is a separate mechanism with different directories per tool.
- **Fastest path (about 5 minutes):** make `AGENTS.md` the real file (move CLAUDE.md's content into it), and reduce `CLAUDE.md` to a line `@AGENTS.md`. Because CLAUDE.md already exists, Claude Code reads CLAUDE.md only and ignores a bare AGENTS.md, so the import is required, not optional.
- Inside this repo, Codex, Cursor and Antigravity then work with no skill install: AGENTS.md tells them to read `skills/career-log/SKILL.md`, which is plain Markdown with relative links to `modes/*.md`.
- The skill format already conforms to the Agent Skills spec (`name` equals the folder name, `description` is under 1024 characters, no Claude-only frontmatter). Auto-triggering from other projects needs a per-machine link, the same kind of step as SETUP.md step 4.
- Do not use a committed symlink (CLAUDE.md -> AGENTS.md) because the repo is cloned on Windows. Use the `@AGENTS.md` import.
- Cursor already discovers the skill through the existing `~/.claude/skills/` link. Codex and Antigravity need one extra link each.
- `tools/export-template.sh` has an allowlist: AGENTS.md and any `.agents/` file must be added to `ALLOW` or they will not reach the Template.

## Comparison

| | Claude Code | Codex (CLI/IDE/cloud) | Cursor | Antigravity |
|---|---|---|---|---|
| Reads AGENTS.md natively | Yes since v2.1.277, but only when no CLAUDE.md/CLAUDE.local.md exists in cwd or above (default) | Yes; global, then root-to-cwd walk, one file per directory | Yes, root and subdirectories | Yes, any directory or inside `.agents/`; no frontmatter; version that added it **unverified** from primary source (third party says IDE 1.20.5) |
| Nested / precedence | Subdirectory AGENTS.md loads on demand when a file there is read | Concatenated root to cwd; closer files come later and win | Nested ones apply to that directory; more specific wins | Walks up from edited file to workspace root; more specific directory wins |
| Size limit | Aim under 200 lines per file (guidance) | `project_doc_max_bytes`, 32 KiB combined by default | Rules under 500 lines advised (guidance); no AGENTS.md limit documented | Rule files over 24 KB truncated; always-on rules share a 20,000-token budget |
| Reads CLAUDE.md | Yes (native) | Not by default; opt in with `project_doc_fallback_filenames` in `~/.codex/config.toml` | Not documented on the rules page (**unverified**) | Not documented (**unverified**) |
| `@file` import in instruction file | Yes, `@path`, max depth 4 | Not documented (**unverified**) | Not documented for AGENTS.md (**unverified**) | Not documented (**unverified**) |
| Skills format | Agent Skills open standard + extensions | Agent Skills (`name`, `description` required) | Agent Skills | Agent Skills |
| Project skill dirs | `.claude/skills/` | `.agents/skills/` (cwd up to repo root) | `.agents/skills/`, `.cursor/skills/`, plus `.claude/skills/`, `.codex/skills/` | `.agents/skills/`, legacy `.agent/skills/` |
| User skill dirs | `~/.claude/skills/` | `~/.agents/skills/`, `/etc/codex/skills` | `~/.agents/skills/`, `~/.cursor/skills/`, plus `~/.claude/skills/`, `~/.codex/skills/` | App/IDE: `~/.gemini/config/skills/`; CLI: `~/.gemini/antigravity-cli/skills/` |
| Follows symlinked skill folder | Yes | Yes (documented) | Not documented (**unverified**) | Not documented (**unverified**) |
| Tool-specific extras needed? | No | No | No (`.cursor/rules/*.mdc` optional) | No (`.agents/rules/*.md` optional) |

## Findings by tool

### Agent Skills spec (shared baseline)
- Required fields: `name` (max 64 chars, lowercase letters, digits, hyphens, must match parent directory name) and `description` (max 1024 chars). Optional: `license`, `compatibility`, `metadata`, experimental `allowed-tools`. Files are referenced by relative path from the skill root. Source: https://agentskills.io/specification
- This repo's `skills/career-log/SKILL.md` has only `name: career-log` and a `description` of roughly 600 characters, and the folder is `career-log`. It conforms. Relative links to `modes/*.md`, `writing.md`, `latex.md` are the spec's recommended pattern. The spec asks to keep references one level deep from SKILL.md; the modes link onward to other files, which is a recommendation, not a requirement (and I did not test how each agent handles it).

### Claude Code
- Reads AGENTS.md since v2.1.277. Default setting `claude-md-or-agents-md`: it reads CLAUDE.md files, or AGENTS.md only when there is no CLAUDE.md or CLAUDE.local.md in the working directory or above. A CLAUDE.md that imports `@AGENTS.md` works; Claude Code does not load AGENTS.md twice. Setting `claude-md-and-agents-md` loads both. Source: https://code.claude.com/docs/en/memory (section AGENTS.md) and https://code.claude.com/docs/en/glossary
- `@path` imports: relative to the containing file, recursive up to four hops, skipped inside code spans and fenced blocks. Source: same memory page, "Import additional files".
- Official recommendation for sharing one file: CLAUDE.md containing `@AGENTS.md`, with Claude-specific notes below it. Symlink `ln -s AGENTS.md CLAUDE.md` also works, but the docs say the Edit/Write tools refuse to write through a symlink, and for Windows: "use the `@AGENTS.md` import instead", because creating symlinks needs Administrator or Developer Mode and Git checks a committed symlink out as a plain one-line text file unless `core.symlinks` is enabled. Source: same page, "Share one file with other coding tools".
- Skills: `.claude/skills/<name>/SKILL.md`, personal `~/.claude/skills/`; a skill folder may itself be a symlink. The `.agents/skills` directory is not mentioned on the skills page. Claude-specific frontmatter extensions (ignored or rejected elsewhere): `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `disallowed-tools`, `model`, `effort`, `context`, `agent`, `background`, `hooks`, `paths`, `shell`. Source: https://code.claude.com/docs/en/skills. The career-log skill uses none of them.

### Codex
- AGENTS.md: global `~/.codex/AGENTS.override.md` or `AGENTS.md` (first non-empty), then from the project root (usually the Git root) down to cwd, checking per directory `AGENTS.override.md`, `AGENTS.md`, then fallback names, at most one file per directory. Files are concatenated root-down with blank lines; later (closer) files override. Stops at `project_doc_max_bytes` (32 KiB default). Config `project_doc_fallback_filenames = [...]` and `project_doc_max_bytes` in `~/.codex/config.toml`. Source: https://learn.chatgpt.com/docs/agent-configuration/agents-md.
- CLAUDE.md is not read by default. It can be added as a fallback name via the setting above; the docs describe the mechanism for arbitrary names, but do not mention CLAUDE.md specifically. The fallback applies per machine in the user's config, so it cannot be shipped in the repo.
- Skills: a directory with `SKILL.md` (`name` and `description` required) and optional `scripts/`, `references/`, `assets/`, an agent config file named after that vendor in `agents/`. Discovery: `$CWD/.agents/skills`, `$CWD/../.agents/skills`, `$REPO_ROOT/.agents/skills`, `$HOME/.agents/skills`, `/etc/codex/skills`, bundled system skills. `.codex/skills` is not listed on this page. "Codex supports symlinked skill folders and follows the symlink target." Invocation: `$` or `/skills` in CLI/IDE, or implicit by description match. That optional file takes `policy.allow_implicit_invocation` (default true). Source: https://learn.chatgpt.com/docs/build-skills.
- Codex `@file` imports in AGENTS.md: not found in the pages above (**unverified**).
- Windows junction vs symlink for the Codex skill link: not documented (**unverified**). A Windows junction is a reparse point, and Codex says it follows symlinks; test it.

### Cursor
- AGENTS.md in project root and subdirectories; nested files apply to their directory, combine with parents, more specific wins. Described as a simple alternative to `.cursor/rules`. Project rules are `.mdc` files with `description`, `globs`, `alwaysApply`; a plain `.md` in `.cursor/rules` is ignored. The page does not mention CLAUDE.md or AGENTS.md size limits. Source: https://cursor.com/docs/context/rules
- Skills: project `.agents/skills/`, `.cursor/skills/`; user `~/.agents/skills/`, `~/.cursor/skills/`; "for compatibility" also `.claude/skills/`, `.codex/skills/`, `~/.claude/skills/`, `~/.codex/skills/`. Fields: `name` (must match folder), `description`, `paths`, `disable-model-invocation`, `icon`, `color`, `metadata`. Invoked with `/`. Cloud Agents do not get `~/.agents/skills/`; project skills in the repo do travel. Symlinks not documented (**unverified**). Source: https://cursor.com/docs/context/skills
- Consequence: Cursor on a machine that already did SETUP step 4 sees the career-log skill with no new link.
- The Cursor changelog page I fetched (entries Sep 2 to Oct 13, 2026) had nothing on AGENTS.md or skills. Source: https://cursor.com/changelog

### Antigravity (Google)
- Rules: `AGENTS.md` or `GEMINI.md` in any project directory or inside `.agents/`; `.agents/rules/*.md` (legacy `.agent/rules/`); walks from the edited file's folder up to the workspace root; AGENTS.md and GEMINI.md take no frontmatter and are always on. Global: `~/.gemini/AGENTS.md`, `~/.gemini/GEMINI.md`, `~/.gemini/config/AGENTS.md`, `~/.gemini/config/GEMINI.md`, `~/.gemini/config/rules/*.md`. Rule files need `trigger` frontmatter (`always_on`, `model_decision`, `glob`, `manual`) or are silently discarded. Limits: 24 KB per file, 20,000-token aggregate budget for global and always-on rules. Source: https://antigravity.google/docs/rules
- Skills: workspace `<root>/.agents/skills/<skill>/` (legacy `.agent/skills` still supported); global for App and IDE `~/.gemini/config/skills/` (legacy `~/.gemini/antigravity/skills/`); CLI `~/.gemini/antigravity-cli/skills/`. Describes itself as the Agent Skills open standard. `name` is optional there (folder name used), `description` required. Symlinks not documented (**unverified**). Source: https://antigravity.google/docs/skills
- No documentation found that Antigravity reads CLAUDE.md or `.claude/skills` (**unverified**). Workflows: the rules page only links to a separate workflows page, which I did not read.

## Gotchas for this repo

1. **CLAUDE.md must keep existing.** If AGENTS.md were added next to the current CLAUDE.md with different content, Claude Code reads CLAUDE.md only. Single source: AGENTS.md holds the text, CLAUDE.md holds `@AGENTS.md`.
2. **Claude-specific wording** (not in CLAUDE.md, but in the skill): `modes/review.md` line 7 says "Spawn one subagent (Agent tool ... `Explore`)"; `modes/rank.md` and `career-fair.md` mention parallel subagents; SKILL.md line 60 and SETUP.md line 5 mention "Claude Code's PowerShell tool". For other agents these degrade to "do it inline / use your own subagent feature". Whether each tool offers subagents is **unverified** here; a one-line note in AGENTS.md ("tool names in the skill are Claude Code's; use your equivalent or work inline") is the cheap fix.
3. **Skill base directory.** SKILL.md resolves the Log root with `start.py` in the skill base directory, which takes its own real path, a symlink or junction resolved; this works for any agent that exposes the skill's real or linked path. When an agent is opened inside the repo, it can use the repo root directly.
4. **Template export.** `tools/export-template.sh` line 17: `ALLOW="skills tools SETUP.md CLAUDE.md GLOSSARY.md docs/adr .gitattributes .gitignore entries/_template.md"`. AGENTS.md (and `.agents/` if added) must be added there, and AGENTS.md must stay free of names, employers, projects and dates (the deny scan in `.export-deny` will fail the export otherwise). `docs/research/` is not in the allowlist, so this file will not be exported. `tools/template/README.md` and README.md say "open Claude Code" and `~/.claude/skills/`; reword to be tool-neutral if the Template should advertise other agents.
5. **Windows.** Avoid committed symlinks (`core.symlinks` off by default for Git for Windows, per the Claude doc above). SETUP.md already uses a directory junction for the Claude skill link; the new links can follow the same pattern.
6. **Cursor rules / Antigravity rules are optional.** AGENTS.md covers both. Do not add `.cursor/rules/*.mdc` or `.agents/rules/*.md`: they duplicate content and Antigravity silently drops rule files with a bad `trigger` field.

## Recommendation (ranked by effort)

**Step 1, about 5 min, covers all four agents when opened in this repo.**
- Create `AGENTS.md` with the current CLAUDE.md text plus: "Read `skills/career-log/SKILL.md` first; it is the skill entry point, and modes are in `skills/career-log/modes/`. Tool names in the skill are Claude Code's; use your equivalent or work inline."
- Replace `CLAUDE.md` with `@AGENTS.md` (optionally followed by Claude-only notes).
- Add `AGENTS.md` to `ALLOW` in `tools/export-template.sh`. Commit before exporting.
- Verify: Claude Code `/context` shows CLAUDE.md under Memory files; Codex run shows AGENTS.md in its instruction list; Cursor and Antigravity respond to "which rules apply".

**Step 2, about 10 min per machine, makes the skill auto-trigger from other projects** (this is the repo's main use: "offer to log a milestone in any project"). Add to SETUP.md next to step 4, same pattern, each with a check:
- Cursor: nothing, it reads `~/.claude/skills/`.
- Codex: link `skills/career-log` to `~/.agents/skills/career-log` (junction on Windows). Cursor also reads this path.
- Antigravity: link to `~/.gemini/config/skills/career-log` (IDE/App) and/or `~/.gemini/antigravity-cli/skills/career-log` (CLI).
- Test each on Windows, since junction handling is unverified for all three.

**Step 3, optional.** Reword the subagent and PowerShell-tool sentences in the skill; make README and `tools/template/README.md` tool-neutral; mention the Codex `project_doc_fallback_filenames` setting is unnecessary since AGENTS.md exists.

**Not recommended:** committing `.agents/skills/career-log` as a symlink (breaks on Windows), duplicating the skill into `.cursor/` or `.codex/` (drift), `.cursor/rules` and `.agents/rules` copies.

## Sources
- https://agents.md (supported tools list, nesting, "closest AGENTS.md wins", symlink-for-backward-compat migration tip)
- https://agentskills.io/specification
- https://code.claude.com/docs/en/memory, /glossary, /skills
- https://learn.chatgpt.com/docs/agent-configuration/agents-md and https://learn.chatgpt.com/docs/build-skills (Codex)
- https://cursor.com/docs/context/rules, https://cursor.com/docs/context/skills, https://cursor.com/changelog
- https://antigravity.google/docs/rules, https://antigravity.google/docs/skills
- Third-party, not relied on: a blog claiming Antigravity IDE 1.20.5 added AGENTS.md (thepromptshelf.dev); not confirmed by Google docs.
