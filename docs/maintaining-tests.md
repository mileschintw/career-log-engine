# Testing Engine changes

Test an Engine change to the `career-log` skill with this file: the bar each check must reach, the clean-agent runs that reach it, how to grade them, when to stop fixing by wording, and how to report. The branch, issue, pull request and merge flow is [engine-changes.md](../skills/career-log/engine-changes.md).

A test is a **clean-agent run**: a fresh agent with the skill installed and none of this session's context, given one user message on a scratch copy of the Log. A **check** is one behaviour you grade (fetching the posting, the requirement map, a save). The **expected sheet** is your notes on what a pass looks like for each check and test case. A **round** is one batch of runs on one head; a pull request's rounds are numbered from 1 and keep counting across heads.

The order of work:
1. Before you edit.
2. Pick the bar for each check, and plan any run that needs the maintainer's accounts, an outside site or the maintainer present (*Accounts, outside sites and the maintainer*).
3. Run rounds: harness (every agent case under *The real profile*), grading, reporting; the stop rule whenever a round fails.
4. The checks [SETUP.md](../SETUP.md) step 7 prints, once, on the head the final round runs on; a fix after them reruns what it touched.
5. Final review.
6. Records.

## Before you edit

1. Read the `writing-for-agents` skill before editing any file under `skills/`, and again before proposing a fix for a failed round.
2. Keep the pull request to its one issue: a problem the tests find outside it gets its own issue and its own pull request.

Done when: the round report names the `writing-for-agents` read, and every hunk of the diff serves the branch's issue.

## Test bar

The bar depends on the phase the Engine is in ([ADR 0006](adr/0006-engine-testing-works-in-phases.md)):
- **Feature phase**, and the refactor phase after it: run each test case once, on the model your session runs on. A case passes when the feature works and the user can use it; that one run is the whole bar, the final head included (the maintainer, 2026-10-21 and 2026-10-22).
- **Model compatibility phase**, which replaces the tuning phase (the maintainer, 2026-10-23): Haiku is no longer a target. Sonnet in Claude Code is the lowest model tested; #72 runs each mode's representative case on it once, and the Template's README lists only the models tested (Opus, Sonnet). Haiku runs only as a reference round, recorded and never fixed (the maintainer, 2026-10-26; results in [ADR 0008](adr/0008-sonnet-is-the-lowest-supported-model.md)). A change that fixes a Sonnet failure in the skill text takes the check kinds and the bar below, and *Stop rule*.

Classify each check by what you grade:
- **Mechanical**: an action or artefact the transcript shows or not (a call and its parameters, a file path, a printed line, a stop).
- **Judgement**: a choice between readings of the Log or the posting (a category, a cap, which entry backs a claim).

A change of wording takes the kind of the behaviour its step governs. In the model compatibility phase every check takes the same bar: each test case run once, on Sonnet medium (the maintainer, 2026-10-24); its kind decides where it is graded (*Collect a run* step 3 for mechanical checks, *Grading*) and goes in the round report. Haiku runs are reference only: report them; they do not count towards the bar.

A check passes when the run of each test case that reaches the step under test passes on the branch's current text of the files and steps that check reads. A later commit touching those files or steps voids the earlier runs. To keep a run, show in the report that `git diff <run head> HEAD` leaves its step untouched.

An in-person run (one that needs the maintainer present: a first sign-in, an `always read` interview read, a clean-machine install) is not rerun when a later commit leaves its path untouched (the maintainer, 2026-10-21). The path is every file and step the run read or ran, the install and sign-in steps included. The run keeps its head; the report names that head and shows `git diff <run head> HEAD -- <the path's files>` printing nothing, or, when a file of the path changed, that the hunks miss the run's steps.

A model is a test setting. Fix a model's weakness in the skill text (a check, a clearer stop, a required read), and write any model choice in the skill as a default the user can override.

## Accounts, outside sites and the maintainer

This section covers a run, or a step you run yourself, that does any of these:
- signs in to one of the maintainer's accounts, or reads through one (the setup browser profile, a site's session);
- requests an outside site's pages beyond the public pages a test case names;
- installs into a clean environment, or anywhere outside a scratch HOME;
- needs the maintainer at the machine: a sign-in, an administrator password, a system permission, a choice only they can make.

A public page read with no sign-in (a fetch, or a browser session without a profile) is outside it: read only the pages the test case names, under *Load on a site*'s pace and challenge rules.

### Prefer a stand-in

Test what you can without the real account first: a fake of the site's API or pages served locally (#309 tested its capture scripts end to end against a fake API), a public page, a scratch HOME. Use the real account only for what the stand-in cannot show, and keep that run read-only (counts and shapes, no files written, no content captured) unless the capture itself is the case.

Done when: the plan names, for each real-account run, what the stand-in could not show.

### The plan and its one approval

Before the first such run, write the test plan and get the maintainer's yes on it once (AskUserQuestion, with the exact scope). It lists:
1. Each site, with its volume cap: pages, threads or requests per run and per pull request.
2. Each person whose page a signed-in run reads, by URL, and what the run does there (read and scroll). A signed-in visit can show that person who visited: a LinkedIn profile does.
3. Each step that needs the maintainer: what they do, in which window, and for about how long.
4. Each environment: what installs where, and which profile, account or credentials the run uses. A browser's sign-ins stay in the profile they were made in (the setup profile on the host, or the one the test makes inside a clean environment); never copy that profile's login data. The agent's own login, copied into a test environment so a run can start there, is listed with when it is deleted.
5. What the runs write, where, and what is deleted at the end.

A run that would go past the plan (another site, a bigger range, another person) stops and asks again; in phase 1 (*Two phases*), with no one to ask, it takes the cautious answer of phase 1 step 1. When the maintainer is away and no plan is approved yet, write the plan into the report, set your status to blocked, and end the turn.

Done when: the maintainer's answer, in their words, is in the round notes, and every site, person, maintainer step and environment the runs use is in the plan they approved.

### Load on a site

- A heavy capture (a whole account) runs once per pull request. Reruns use the small range the plan names (the newest page, a few threads).
- One request at a time per site, with a pause between them; never two runs on the same site at once.
- A CAPTCHA, another challenge, a rate limit or an unexpected sign-in page stops every case on that site: no retry, no way around it. Cases on other sites go on, and the report names the step and the site.
- Signed in, a run reads and scrolls only: no posts, likes, messages, follows, settings changes or purchases.

### The clean-agent prompt's sign-in rule

*Harness › Start a clean agent* gives every run "Never sign in, submit a form or accept terms". That line is for runs that reach a sign-in by accident, and it stays in every prompt the approved plan does not cover. A run the plan lists as signed-in has this line in its place:

```
- Read the sites the test plan lists, signed in through <profile>, within its caps (<site: cap>; …). Only read: never post, submit a form or accept terms. A sign-in page, CAPTCHA or other challenge stops that site: report it.
```

### Clean environments

**macOS:** a throwaway Tart VM, always (the maintainer, 2026-10-22): nothing installed on or removed from the host, and no extra user account. The image is `ghcr.io/cirruslabs/macos-tahoe-base:latest`; on the maintainer's Mac, Tart 2.41.1 is the whole `tart.app` in `~/Applications/tart.app`, and `~/bin-test/tart` links to its executable. Start with `tart clone <image> <vm>` and `tart run <vm>`, and end with `tart delete <vm>`. To keep a VM for a rerun instead, run `tart exec <vm> sync` before `tart stop`: a quick `tart stop` once lost the home folder's changes. Prepare the VM in this order:
1. Move tart-guest-agent out of Homebrew: copy it to `/Library/Application Support/tart/` and point its launchd plist there, so `tart exec` survives step 2.
2. Delete `/opt/homebrew` whole, `/etc/paths.d/homebrew`, `~/.zprofile` whole (besides its Homebrew, Node and pnpm lines, the image adds an rbenv line; a new Mac has no `~/.zprofile`), and `~/Library/Caches/Homebrew` (the image ships bottles there that a new Mac has not). Also delete the `~/.profile` link to `~/.zprofile` (a new Mac has no `~/.profile`; with the link, uv's line lands in `.zprofile`, and a setup measurement is not a new Mac's), and `~/.homebrew`, `~/.rbenv`, `~/.npm`, `~/.cache` and `~/.local`.
3. A private repo: clone it on the host, then stream it in, `tar -cf - -C <host clone> . | tart exec -i <vm> sh -c 'mkdir -p <dest> && tar -xf - -C <dest>'`.
4. Last, delete `/etc/sudoers.d/admin-nopasswd`, so `sudo` asks for a password as on a real Mac.

To restart the VM, run `sudo /sbin/shutdown -r now` in its Terminal, with the full path (the Mac retest, 2026-10-26); after step 4, `sudo` there asks for the password.

Done when: in the VM, `brew`, `node`, `pdflatex` and `pdftotext` are not found, `ls -a ~` lists no `.zprofile`, `.profile`, `.homebrew`, `.rbenv`, `.npm`, `.cache` or `.local`, `sudo -n true` fails, and `tart exec <vm> true` exits 0.

A session not on the Mac writes the Mac test as a prompt, with these steps, for the maintainer to run there. A release's Mac test also follows the test step of [publishing.md](publishing.md) › Publishing a release, for the commit it checks out and the setup lines it expects.

**Windows and Linux:** a scratch HOME, or on Linux a container when the case needs a machine with nothing installed. On Windows, point `USERPROFILE`, `HOME`, `HOMEDRIVE` and `HOMEPATH`, `APPDATA` and `LOCALAPPDATA` into the scratch folder, in the process that runs setup, so its children inherit them. Leaving `APPDATA` at the real profile once let setup run `tlmgr update --self` against the maintainer's real TinyTeX. An install step that would still write the real profile (reusing an installed tool to skip a download) is a stop: ask first. Reading through the setup browser profile the approved plan names is not an install.

Done when: before the first install command, that process prints each variable, and each is inside the scratch folder.

### Two phases: the maintainer present, then unattended

When a long test needs the maintainer for a few of its steps, do all of those steps in phase 0 and run the rest unattended.

Phase 0, with the maintainer (aim for 15 minutes; tell them, each time you need them, what to do, in which window, and for about how long):
1. Check what needs no one: `gh auth status`, the head under test, the tools' versions, and that this session runs without permission prompts.
2. Keep the machine awake (on a Mac, `caffeinate -dimsu` in the background, its PID noted), on mains power, the lid open.
3. Build the clean environments; the maintainer types any administrator password now, and every large download has started.
4. Grant the system permissions the runs need (for computer use, Accessibility and Screen Recording) and take one screenshot to confirm.
5. The maintainer signs in to each site of the plan, in the profile the runs use; read one signed-in page on each, with no window, to confirm.
6. Ask in one go every choice phase 1 needs (whose page, which sources, the caps), and write the answers into the answer script for phase 1.
7. Get the plan's one approval (*The plan and its one approval*), showing also how each case runs and what it should give, how long it takes, and what the maintainer may have to do afterwards.
8. A trial run: the shortest case end to end (start the run, answer from the script, grade it, save the result). Fix a failure now.

Done when: the maintainer has seen this checklist and confirmed it: the machine kept awake, environments ready, sign-ins confirmed, script and plan approved, trial run passed, and the report's path agreed. Then start phase 1.

Phase 1, unattended:
1. Answer a run's questions from the script, each answer starting `User:`. A question the script does not cover gets the most cautious answer (install nothing, read nothing, skip), and goes in the report.
2. A case that needs the maintainer is marked as waiting for them and skipped; the others go on.
3. A challenge stops that site only (*Load on a site*).
4. Keep to the time caps the plan names, per case and for the phase (#120's were 45 minutes and 8 hours); past one, stop and write the report.
5. Add each case's result to the report as the case ends, so a crash keeps the finished ones.
6. At the end, delete the agent login copied into each test environment, any captured personal data, and the sign-ins of any browser profile the test made inside an environment; close every browser session and the keep-awake process; and keep the environments for a rerun (a rerun copies the agent login in again, as the plan lists). At the top of the report, write the passes and fails, the cases waiting for the maintainer (what to do, how long), and the decisions needed.

Done when: every case has a result, a waiting mark, or the reason it did not run, and the report says what step 6 deleted and closed.

### Report

For each run this section covers, the report gives the maintainer's approval in their words, each site with the volume actually used, the people whose pages were read, what was installed and removed and where, and the copied agent logins deleted.

## The real profile

Every agent case (a clean-agent run in a round, or any case a session hands to a fresh agent) keeps off the maintainer's real profile (the maintainer, 2026-10-24). A case once ran setup against it: its scratch Log had no `config.toml`, the agent read the *Trigger check* as "run setup", rewrote the real `~/.career-log/machine.toml` and ran `tlmgr` on the real TinyTeX.

`maintainer/harness.py` (*Harness*) applies these rules: its copies give the agent a scratch `config.toml` and home, its `prompt` keeps the agent's commands in that home, and its `start` and `collect` hash the real `~/.career-log/machine.toml` (`harness.py --help` says how). Start every agent case through it, a case outside a round too (`start --round 0`, with its own `<runs>` file): build its copy (*Build one scratch copy per concurrent run*), run `start`, and give the agent what `prompt` prints. A prompt of your own holds, word for word, the three lines of `prompt`'s output that begin `- Never run setup`, `- Start every shell command` and `- Copy the two lines above`, in that order and next to each other.

In that home the agent finds no machine setup and no `gh` login: copy the real `~/.career-log/machine.toml` into `<t>/home/.career-log/` when the case needs this machine's tools (a write then lands on the copy), and expect a `gh` read to fail when the case gives no token.

A signed-in case (one the approved plan lists as signed-in) reads through the setup browser profile, which the agent looks for at `$HOME/.career-log/browser-profile`, so link it into that home; never copy it, since its login data stays in the profile it was made in. Run `harness.py signed-in-home <t>` after `copy` or `template-copy` and again after each `reset`: it links the profile (a junction on Windows), replacing the link a `reset` leaves (a second plain `ln -s` would land inside the profile), and copies the real `machine.toml` in, fresh each time, which a signed-in case needs too. `harness.py remove` deletes the link, never the profile. Playwright's browsers are in the real home too (macOS `~/Library/Caches/ms-playwright`, Linux `~/.cache/ms-playwright`, Windows `%LOCALAPPDATA%\ms-playwright`), so when this checkout's `.playwright/cli.config.json` picks Chromium (the machine has no Chrome), start the run with `PLAYWRIGHT_BROWSERS_PATH` set to that folder, expanded from the real home before harness changes it: macOS `PLAYWRIGHT_BROWSERS_PATH="$HOME/Library/Caches/ms-playwright" python3 -I maintainer/harness.py process …`, Windows PowerShell `$env:PLAYWRIGHT_BROWSERS_PATH="$env:LOCALAPPDATA\ms-playwright"; py -3 -I maintainer/harness.py process …` (*A run as its own process*). Tried on macOS only (2026-10-25).

The exception: a case that tests the missing-config path (the *Trigger check*'s stop for a missing `config.toml`) builds its copy with `template-copy --no-config`; the home, the prompt and the hash still hold. Its prompt still tells the agent to skip that stop, so the case passes when the check printed its `stop:` line, the run ran no setup, and `collect` printed `PASS machine-toml`. A case that tests setup's install path (`setup.sh`, `setup.ps1`, or the tool installs the setup mode starts) has to run it, so it is no agent case on a scratch Log: it runs in a clean environment, under *Accounts, outside sites and the maintainer*. A setup *Changes* case for a Config or Direction field stays an agent case: the setup mode's `tools/config.py` edits are not `setup.sh`.

Done when: before each agent starts, `start` printed no FAIL line and the prompt holds the three lines; after it ends, `collect` printed `PASS machine-toml` (a FAIL fails the case, and the report says what changed).

## Harness

`maintainer/harness.py` builds, resets and removes the scratch copies, prints a run's prompt, records each run's row and grades it; `harness.py --help` gives each subcommand's checks. Run it from the branch's worktree with `python3 -I maintainer/harness.py` (`py -3 -I` on Windows), and follow what it prints. `<t>` is a copy's folder, `<scratchpad>/t`, `<scratchpad>/t2`, …; `<runs>` is the file of the pull request's run rows, `<scratchpad>/runs.jsonl`, outside every `<t>`.

### Build one scratch copy per concurrent run

This repo holds no Log ([ADR 0015](adr/0015-the-engine-is-developed-in-its-own-public-repo.md)), so a case that reads entries, profile or direction runs on a Template copy (*A Template copy*) with fixtures: the files the expected sheet lists for the case, written for it and made up (names, employers, dates and numbers), in the formats of the head under test (`entries/_template.md`, the skeleton's `profile.md` and `direction.md`). No fixture comes from a real Log, the maintainer's included, and none is kept in this repo: each case writes its own, so a format change never leaves a stale set behind.

A case that runs in this repo itself (an Engine change made by the agent under [engine-changes.md](../skills/career-log/engine-changes.md), or the no-Log rule of `AGENTS.md`) takes `harness.py copy <t>` instead: this repo as the branch has it, the Engine and the maintainer's files, with no Log data (`copy` refuses a branch that holds any).

Saves commit, so each concurrent run gets its own copy. Either kind has the head under test on its default branch, with no Engine branch: the skill commits every data save to its default branch ([SKILL.md › Commits](../skills/career-log/SKILL.md)), a bulk one after the user's yes (*Collect a run* step 2), so the save starts from the text under test and lands where *Collect a run* grades it.

Commit the branch, then run `harness.py template-copy <t>` (*A Template copy*) or `harness.py copy <t>`.

Done when: it printed no FAIL line, and a Template copy's `<t>/log` holds every fixture the expected sheet lists for its case.

### A Template copy

`harness.py template-copy <t>` makes a copy from the export of the committed branch: a new Log with no history. When the expected sheet lists fixtures or edits for the test case, add `--no-seed`, write them in `<t>/log`, then run `harness.py seed <t>`. Add `--no-config` only for a case that must start with no `config.toml` (*The real profile*'s exception); a setup *Changes* case for a Config or Direction field needs it.

Done when: it printed no FAIL line. To reset it, run `harness.py remove <t>` and build it again.

### Reset a copy before each run

A copy keeps the commits, branches and drafts of the run before it. Before every run after a copy's first, commit the branch (a fix commit included), then run `harness.py reset <t>`. A Template copy is not reset: remove it and build it again (*A Template copy*).

Done when: it printed no FAIL line.

### Write the expected sheet

Before the round's first run:
1. Read the steps under test and the Log files your test cases touch.
2. Pick test cases (a user message, plus any posting it needs, from live postings) that exercise each branch the change touches. For `write`: at least one posting that needs the browser, one with sponsorship language, and one that stops at an apply flow.
3. Write a pass line for each check, and for each test case the value the run must reach (which entry is course work, which part an agent wrote, whether the posting has a sponsorship line).
4. For each test case that reads the Log, list its fixtures: each file and its made-up content (*Build one scratch copy per concurrent run*).

Done when: every branch the change touches has a test case, every check has a pass line, every test case has an expected value, and every test case that reads the Log has its fixtures listed.

### Start a clean agent

Start each run as a background `general-purpose` subagent (it writes files), with `model` and `effort` set in the Agent call to the bar's, unless its check depends on the run's project or config folder (*A run as its own process* below):
1. Write the user's message, verbatim, to a file in your scratchpad.
2. Run `harness.py start <t> --runs <runs> --round <round> --model <h|s|o> --case "<test case>"` (`h` for Haiku, `s` for Sonnet, `o` for Opus). It names the run `v<round><model letter>-<n>` (`v3s-2`: round 3, Sonnet, second run) and records its row; the report's Run column takes that name.
3. Give the agent, as its whole prompt, what `harness.py prompt <t> --run <run name> --message <file>` prints. Add `--browser playwright` only for a case that needs a page a plain fetch cannot read (an Ashby or Workday posting, an application form behind a tab), and run those agents one at a time: two installs at once fail. A run the approved plan lists as signed-in adds `--signed-in <file>`, the file holding the line *The clean-agent prompt's sign-in rule* gives, filled in.

Done when: every run of the round is started, each after a `start` that printed no FAIL line.

#### A run as its own process

A subagent's project folder is your worktree, and its config folder is yours: it never sees what the copy's `.claude/` holds (project skills, settings), the copy's `CLAUDE.md` as a project file, or a user-level skill other than yours. It does carry your own memory and settings: your auto-memory is in its context, so it can follow a rule of yours the Engine never gave it (in 0.3.0's consolidate case, a run wrote the change list to a file, citing "your saved rule", the tester's memory about pasted diffs). `harness.py prompt` tells a subagent run to set those aside, and *Grading* notes a run that still cites one. So when a check depends on what the run's project or config folder holds (a skill the copy installs into `.claude/skills/`, a project setting, `CLAUDE.md`), start the run as its own `claude -p` process instead, in the copy's Log root with a scratch config folder that holds only the copy's `career-log` skill. Prefer a process run, too, for a check that judges how the run presents its output (a change list, a diff or a draft shown or written to a file).

Steps 1 and 2 as above, then:
3. Put in place what the case needs in the project folder (a skill into `<t>/log/.claude/skills/`) after `start`, since `start` checks the copy is clean, and add each such path to `<t>/log/.git/info/exclude` so `git-status` grades the run's own files only.
4. Write what `harness.py prompt <t> --run <run name> --message <file> --relay turn` prints to a file, with the `--browser` and `--signed-in` options the subagent step 3 gives.
5. Get a token: with no token file `<scratchpad>/token` yet, create it empty and restrict it to you (mode 600, or in Windows PowerShell `icacls <token file> /inheritance:r /grant:r "${env:USERNAME}:(R,W,D)"`), then ask the maintainer to run `claude setup-token` (they authorize it in a browser) and save the token it prints into that file themselves (give them its full path), never pasting it into the chat. Then, in the background, run `harness.py process <run name> --runs <runs> --effort <the bar's effort>` with `CLAUDE_CODE_OAUTH_TOKEN` read from that file in the command's environment: in a POSIX shell (macOS, Linux, Git Bash) `CLAUDE_CODE_OAUTH_TOKEN="$(cat <token file>)" python3 -I maintainer/harness.py process …` (`py -3` in Git Bash), in Windows PowerShell `$env:CLAUDE_CODE_OAUTH_TOKEN = (Get-Content -Raw <token file>).Trim(); py -3 -I maintainer/harness.py process …` (in an interactive shell it stays set: `Remove-Item Env:CLAUDE_CODE_OAUTH_TOKEN` after the round). `harness.py --help` gives the config folder and the environment. `process` copies no login file and refuses without the token (or `ANTHROPIC_API_KEY`). As root (a Linux container), also set `IS_SANDBOX=1` there (`IS_SANDBOX=1 python3 -I maintainer/harness.py process …`, or `docker exec -e IS_SANDBOX=1 …`): Claude Code refuses `bypassPermissions` as root, so the process ends at once, and `process` prints its error. Why a token: on Windows and Linux `process` used to copy `<config>/.credentials.json`, and once (2026-10-26, on Windows, #538's rounds) a run rewrote the real file and signed the maintainer's own CLI out (`OAuth session expired and could not be refreshed`) until they logged in again. The token worked with Claude Code 2.1.292 and 2.1.310 on macOS (2026-10-25) and 2.1.311 on Windows (2026-10-26: two turns, no credentials file written in the config, the real `.credentials.json` unchanged); untried on Linux.
6. In the background, run `harness.py say <run name> --runs <runs> --message <the prompt file>`: it sends the turn and exits when the run's turn ends, printing its last message. A turn that leaves a background subagent running (a background review) ends only after that subagent's result has come back as a new turn and the run has answered it; `say` then prints each of the turn's messages, `---` between them.

Done when: the run's first `say` exited 0, or it printed `turn 1: error` with `Failed to authenticate` (the token is wrong or has expired), you stopped the process (`say --end`), and you asked the maintainer for a new `claude setup-token` before the next run.

### Collect a run

1. Wait for the run's completion notification: that notification is what ends a run, since an advisor call can leave a transcript idle for minutes.
2. When the run asks the user something (an approval before a save), answer once as the user would, with `SendMessage` to the run's agent id, the message starting `User: ` as the prompt's rule says. This answer is part of the test, not an intervention. A run that still refuses the answer as not the user's has not reached the steps after it: give no second answer, and note the refusal under the run's name in your round notes, for the round report (*Grading*).
3. Grade the mechanical checks: in your own session, the one that started the run, run `harness.py collect <run name> --runs <runs> --agent <agent id>`, the id from the Agent tool's result, and follow its output (`tools/check_run.py --help` gives each check's rule and the exit codes). Grade its output as *Grading* says. Read the transcript its `transcript:` line names, and beside it the `agent-<id>.jsonl` of each agent id the run's Agent results give, for every other check; the task output files stay empty.
4. Delete each file the `outside-root` line names, and any file a shell command of the run wrote outside the Log root.

A process run (*A run as its own process*) differs in three steps:
- Step 1: its turn ends when its `say` exits.
- Step 2: answer with `harness.py say <run name> --runs <runs> --message <file>`, the file holding the `User: ` answer. Once a turn's last message asks the user nothing, stop the run with `say <run name> --runs <runs> --end` and wait for `process` to exit; first check `<t>/process/events.log` for `TURN <n> LATE`, a message the run sent after that `say` exited, and if it is there, read `out/<n>.txt` again. A turn that never ends (`<t>/process/events.log` stays on `TURN <n> WAITING <subagents>` for 30 minutes, whether or not `stream.jsonl` still grows, for example): `say <run name> --runs <runs> --end` (the waiting `say` then exits 1, `the process ended first`), or, if `process` does not exit, stop it; `collect` then deletes a credentials file it left in `<t>/config/`.
- Step 3: run `collect` without `--agent`. It finds the transcript itself (its `transcript:` line; the run's subagents are in the `<session>/subagents/` folder beside it) and keeps a copy for the records. A `FAIL credentials` line means a credentials file the run wrote into `<t>/config/` is still on disk: delete that file now.

Done when: you have the run's final message and every subagent call it made, `collect` printed its `machine-toml` line (and, for a process run, a `credentials` line that is no FAIL), and no file the run wrote outside the Log root is left.

### Remove the copies

After the pull request's last check passes, run `harness.py remove` with every `<t>`, and delete the token file. Delete a copy it prints on a `locked:` line after the session ends.

Done when: no scratch copy of this pull request is left in the scratchpad.

## Grading

Grade each run against the expected sheet, `tools/check_run.py`'s output and the table below. A **fail** does not count towards the bar; a **note** counts and goes in the report. `tools/check_run.py --help` gives the grade of every check the script runs; the table holds only what it does not grade, and the exceptions under it say where the script's grade is read by hand. A behaviour none of them covers is a **new kind of failure** (*Stop rule*).

| Behaviour | Grade |
|---|---|
| Any step's outcome differs from the expected sheet | fail |
| A save leaves provenance that can go stale (a pointer to a file that is overwritten in place) or loses a citation | fail |
| A save adds a `## Past phrasings` line whose meaning matches a line already there for that angle | fail |
| A prompt copied to a subagent drifts in wording with the same effect | note |
| A save rewords a line harmlessly | note |
| A shell command writes a file outside the Log root (`outside-root` lists the files a Write or Edit call wrote) | note |
| The run refuses a relayed `User:` answer as not the user's (*Collect a run* step 2) | the run does not count; list it in the round report under its name, and start another run on the same test case |
| The tester intervened (stopped the run, resumed it by hand, relayed a subagent's result) | the run does not count, as neither pass nor fail |
| The run cites or follows a rule from outside the copy (the tester's memory or settings, *A run as its own process*) | note, a run artefact: the step that rule changed is neither pass nor fail; grade the rest of the run as usual |
| The run (or a subagent it started) read (the Skill tool, Read or `cat`) the whole skill a mode's step names before its first command that needs it | pass |
| The run reached a result, correct or not, with no read of the skill a mode's step names | fail |
| The run read only part of that skill (the first lines of a longer file) | note; say in the report which part |

Grade a save by its effect on the Log.

Take `tools/check_run.py`'s grade for the checks it covers (*Collect a run* step 3), except:
1. **A `reviewer-prompt` FAIL:** read the line it quotes. A wording change with the same effect is a note (*a prompt copied to a subagent drifts*); any other change is a fail.
2. **A `humanizer-after-review` line:** on a FAIL, if that review changed no text, or the humanizer skill was not available in the run (its skill list or its own message says so; a process run's config folder never holds it), it is a pass. On a PASS, check that the humanizer call started after the review returned (one started before a background review returned does not count) and that its text holds the sentences the review changed (for a write save, `printed-lines` checks the lines the run lists).
3. **A `reviewer-prompt` note for the root** (a NOTE, or a root note inside a FAIL line): the script has already set aside the spellings its `--help` names, so compare the two paths. Another spelling of the run's Log root is a pass; another Log is a fail.
4. **A `past-phrasings` line with any added or removed line** (a count above 0 in its `+n -n` evidence), or a NOTE that the write save added none: these rules are write step 10's, and the script grades only write saves. The script only finds the lines; diff the entry's `## Past phrasings` against the base and grade each line by meaning, for its angle:
   - an added line that means the same as a line already there for that angle is a fail; one that means something else is a pass;
   - a bullet of the approved resume or bullets report (bullets copied unchanged included) whose meaning differs from each line for its angle, but that the save did not add, is a fail;
   - an added line whose wording is not a bullet of the approved resume or bullets report (`Kind: resume bullets`) (a form answer, a cover letter, a bio, a pitch, a resume's summary or Skills line) is a fail; such a wording left out is a pass;
   - a removed line is a pass only when its claim had one wording more for the angle than the cap (`tools/check_save.py` `PHRASING_CAP`) after the save's addition and it is the line [consolidate](../skills/career-log/modes/consolidate.md) step 2 ranks last;
   - a removed line replaced by one with the same meaning and its citation is a note (*a save rewords a line harmlessly*); any other removed line is a fail (a drop below the cap, a rewrite that changes the meaning or loses the citation).
   At the Archived level ([write › Save levels](../skills/career-log/modes/write.md#save-levels)) these rules change: an Archived save adds no line, so a wording it leaves out is a pass, and in a demote each removed line that cites the demoted folder or bullets report is a pass (the script sets those lines aside, and passes a range whose every write commit adds an `archived.md` or a report's Archived line).
5. **A `provenance` line:** on a FAIL, read the quoted cell: a source citation that only looks like an output (a file name with `reports/` in it) is a pass. On a PASS or NOTE, the script has read the entry sections that name a file with an extension, or an entry by its name, and found each section after ` › ` among that file's headings. Check that every other row's entry section names a section of an entry, `profile.md` or `direction.md` (write step 10), and that the table covers every claim in the output.
6. **A `call-lines` FAIL for a line that does not parse:** read the line, and grade it by the model it names; a mention of the label that is not a call line is a missing line (a note).
7. **A call the script sorted wrongly** (a reviewer it lists as `other`, a lookup it lists as the reviewer, from the description in its evidence): grade every transcript check for that call by hand.
8. **A `map-count` line:** the counts are `tools/fit.py map`'s, from the map file, so the rows are not counted by hand. With several postings, check that every posting has its own `Map (<company>, <role>):` line: the script grades only the labels fit.py printed. A map file can still be wrong in what the tool cannot judge (a requirement left out of `requirements`, a category the entry does not support): grade that against the posting and the entries by hand.
9. **A `printed-lines` line:** `Humanizer after review: none` is the run's own claim: a fail when the review's applied edits changed text. A NOTE for a line found only with other case or quotes, or cut: compare it with the humanizer call's prompt and reply; the same sentence is a pass. A FAIL cut at a `write(` commit that failed in a way the script does not read as a failure (its `--help` says which it reads) is graded at the commit that succeeded.
10. **A SKIP on a check the expected sheet says the run reaches:** the script did not find the call or the save, so find it in the transcript or the copy and grade it by hand.

A change to a grade `tools/check_run.py` gives is made in the script and its `--help`; a change to any other grade is made in this table or its exceptions. Either way, during a pull request, add a dated line naming the pull request to *Changes* below before the round that uses it, so a later session grades by the same rule.

Changes:
- 2026-10-19 (#86): missing call line → note; lookup without model → note, reviewer without model → fail; prompt drift with the same effect → note; saves graded by effect on the Log.
- 2026-10-20 (#93): rows for `tools/check_run.py`'s grades: humanizer without model → fail; call line naming another model → fail; no humanizer after a review that changed text → fail; a Past phrasings line with the same meaning as one already there → fail; subagent type not read-only → note; call line only inside a tool call → note; reviewer pointed at another Log root → fail; subagent on another model than the run's, unasked → note; a wording in the approved text whose meaning is new for its angle but that the save did not add → fail; the hand checks in the exceptions under the table.
- 2026-10-20 (#119): a run that refuses a relayed `User:` answer → does not count; start another run.
- 2026-10-20 (#122): save levels: an Archived save adding no Past phrasings line → pass; a demote's removal of the lines citing its folder → pass.
- 2026-10-21 (#88, #129): a provenance row whose entry section is in `direction.md` → pass (exception 5); a requirement map's "written by" cell that holds `none` or `n/a` on a `gap` or `claimed, unbacked` row → note.
- 2026-10-22 (#108): `tools/check_run.py` reads a line's own `**<angle>:**` prefix as its angle only before a quoted wording, and that prefix wins over a label line; grades unchanged.
- 2026-10-22 (#137): write step 10's printed check lines in another form, or not ending on `none` → fail, one `Provenance check (<file>):` line per provenance file; missing or printed after the save's commit → note until #239 (the user, 2026-10-22: 「先判 NOTE (Recommended)」); a requirement map shown without its `Map:` count line, or whose last one names a missing row or counts too few rows → fail; a printed check line only inside a tool call → note; `tools/check_run.py` grades them as `printed-lines` and `map-count`, exception 9 compares the map's rows with the count by hand, and exception 10 passes lines printed between a failed commit attempt and the commit that succeeded.
- 2026-10-22 (#210): exception 4's missed-wording fail names lines copied unchanged too (bullets from the resume step 6 copied, answers reused as they were), as write step 10 now says; grades unchanged.
- 2026-10-22 (#239): write step 10's check lines come from `tools/check_save.py`'s output: missing, printed only after the save's commit, or written by the run itself → fail (was a note until this tool, #137); a last line whose row count differs from the file at the save's commit, or that comes before the run's last edit of the file, or a last tool run that did not exit 0 → fail; a check line only inside a tool call is no longer its own row (only the tool's output counts); exception 10 now checks the tool's `Humanizer after review:` lines against the humanizer call's prompt or reply (reply added after #239's round 2, whose lines were checked both ways), and the script skips a failed `write(` commit itself; `provenance` also fails an entry section naming a file other than an entry, `profile.md` or `direction.md`.
- 2026-10-22 (#261): a subagent whose type its mode names (scan's Screen batches, fits and drafts, which write files) is not a type note; `tools/check_run.py` knows them by the mode's own prompt first lines.
- 2026-10-22 (#247): exception 4: only the approved resume's bullets feed `## Past phrasings` (the user, 2026-10-22: "None (Recommended)"); an added line whose wording is not a resume bullet (a form answer, cover letter, bio, pitch, summary or Skills line) → fail, such a wording left out → pass.
- 2026-10-24 (#304): exception 4 counts a `Kind: resume bullets` report's bullets with the resume's, and its Archived line with `archived.md` (D8 of #171: the user, 2026-10-23: 「D8 選「要餵」」); exception 5's section check is the script's now (a section that is no heading in its file → fail); grades unchanged otherwise.
- 2026-10-24 (#303): the requirement map's `Map:` and `Course work:` lines are `tools/fit.py map`'s output: `map-count` reads them from that tool's results, a `Map:` line the run wrote with no fit.py map output → fail (was graded as the run's own count), a map shown whose `Map:` or `Course work:` line differs from fit.py's last → fail, a run that built a map without showing it (interview, several postings) → graded by fit.py's lines (was a SKIP); exception 9 no longer counts the rows by hand.
- 2026-10-24 (#310): `tools/check_run.py --help` is the spec for the grades the script gives, and the table keeps only the rows it does not grade (#171 D11: the user, 2026-10-23: 「D11 照建議：check_run 已評的列以 check_run.py --help 為規格，maintaining-tests.md 評分表只留工具不評的列和例外，:186 一起改。」). New script grades: `save-branch` (the save on the default branch, pushed, one worktree → else fail; before this change *Collect a run* step 4.1), `outside-root` (a file a Write or Edit call wrote outside the Log root → note), `commit-subject` (a subject no mode gives and no tool printed, or a `consolidate(<slugs>)` or `log(<slug>)` slug that is not the entries the commit changes or an entry → fail); `subagent-model` passes another model family the user named (before this change exception 7); `reviewer-prompt` sets aside a root spelling realpath resolves (exception 3 kept for the rest); `printed-lines` fails a `Humanizer after review:` line whose text no humanizer call after the review holds, and notes a near match (before this change part of exception 10); a Log file that is not UTF-8 fails the check that reads it. Exceptions 8 to 11 are now 7 to 10; the lines above keep the old numbers.
- 2026-10-25 (#139): skill use: the skill a mode's step names read whole before the first command that needs it → pass; a result without the read → fail; a partial read → note. Exception 2: a process run (*A run as its own process*) has no humanizer skill.
- 2026-11-03 (#604): a run that cites or follows a rule from outside the copy (the tester's memory or settings) → note, a run artefact; the step it changed is neither pass nor fail.

## Stop rule

Keep a count, in the round notes, of the fixes aimed at each failure class.

1. A new kind of failure stops the round: grade the runs in flight on the current text, start no new run, and send the round report.
2. A failure class that a fix has already targeted twice, and that fails again, ends fixing by wording. The third fix is, in this order, the first that fits:
   1. a check the run can fail before it commits (a completion criterion it prints);
   2. a sentence that replaces an existing one;
   3. a deletion;
   4. moving the item out of this pull request to its own issue.

Between fixes of the same kind, choose by the next round's outcomes alone.

Done when: each failure in the round is fixed by the rule above or moved to an issue, and the fix is committed before the next round.

## Reporting

Report once per round, in this format. `harness.py report <round> --runs <runs>` prints its first line, a `mechanical` row per run with `check_run.py`'s grade, and the mechanical checks' raw `Bar:` counts; fill in `<effort>`, take out of the counts the runs that do not count and the grades *Grading*'s exceptions change, and add the judgement checks' rows and counts, the results and the rest:

```
Round <round> on <short sha> (<model> <effort>)

| Run | Check | Test case | Result | Evidence |
|---|---|---|---|---|
| v<round>s-1 | mechanical | <case> | PASS / FAIL / PASS with notes | <transcript line or file> |

Bar: <check>: <passes>/<test cases that reach it> on this head; …
Fixes: <commit>: <check, replace, delete or move>; a net-new sentence gives its reason.
Decisions needed:
1. <question> — recommended: <option>, because <reason>.
```

Collect every decision the round raises into that one list, so the user answers once per round; write `Decisions needed: none` when there are none. Apply the answers in one commit, then reset the copies (*Reset a copy before each run*).

Done when: the report is sent and, after the user's answers, `git log -1` shows the commit applying them.

## Sessions

When a pull request needs more rounds than one session's context holds, split it by stage, skipping a stage the bar does not need:
1. Design and fixes.
2. Rounds.
3. Final review and the wrap-up.

Each session starts from this file and the pull request's handover notes.

Done when: the handover notes name the state, the head, the run table so far, the expected sheet and the open decisions.

## Final review

Before you ask for the merge, start a clean reviewer subagent with the `writing-for-agents` skill on the pull request's diff, and apply the fixes you accept.

Done when: the pull request body has a *writing-for-agents review* section listing each finding and what was done with it.

## Records

Run notes live outside the repo, in the folder `career-log-experiments/` beside the main checkout (the first path `git worktree list` prints), where no commit, export or worktree removal reaches them.

1. Keep the round notes, expected sheets and handover notes in your session's scratchpad while you work.
2. Before the session is archived, run `python3 -I maintainer/harness.py records scratchpad <scratchpad> --session <session id>` from the session's worktree: it copies the files to `snapshot-<date>/scratchpads/<project folder>/<session id>/` in the records folder, `<project folder>` being the name `harness.py records project-folder` prints.
3. Claude Code deletes session transcripts (`~/.claude/projects/<project folder>/*.jsonl` and their folders) after `cleanupPeriodDays`, 30 by default; copy them (`harness.py records snapshot`), or extract the numbers you need, before then.

Done when: the folder `records scratchpad` printed lists this session's round notes, expected sheets and handover notes.
