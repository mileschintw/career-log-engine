#!/usr/bin/env python3
"""The test harness of docs/maintaining-tests.md and the copy steps of docs/migrating.md: scratch
copies for clean-agent runs (a new Log from the export, or this repo's Engine), the run's prompt,
its row and grade, the round's table, and the records folder's snapshots. Run a subcommand, then
follow what it prints.

  python3 -I maintainer/harness.py copy <t> [--worktree <w>] [--branch <b>] [--default <d>]
  python3 -I maintainer/harness.py template-copy <t> [--worktree <w>] [--default <d>] [--from <dir>
                                   [--modes-from <clone> v<release>]] [--no-config] [--no-seed]
  python3 -I maintainer/harness.py seed <t>
  python3 -I maintainer/harness.py reset <t>
  python3 -I maintainer/harness.py verify <t>
  python3 -I maintainer/harness.py prompt <t> --run <run> --message <file>
                                   [--browser fetch|playwright] [--signed-in <file>] [--relay message|turn]
  python3 -I maintainer/harness.py start <t> --runs <file> --round <n> --model h|s|o --case <text>
  python3 -I maintainer/harness.py process <run> --runs <file> --effort <level> [--idle <minutes>]
  python3 -I maintainer/harness.py say <run> --runs <file> (--message <file> | --end)
  python3 -I maintainer/harness.py collect <run> --runs <file> [--agent <id>]
  python3 -I maintainer/harness.py report <round> --runs <file>
  python3 -I maintainer/harness.py signed-in-home <t>
  python3 -I maintainer/harness.py remove <t>...
  python3 -I maintainer/harness.py records project-folder [<path>]
  python3 -I maintainer/harness.py records snapshot [--folder <name>] [--projects <dir>]
  python3 -I maintainer/harness.py records scratchpad <dir> --session <id> [--folder <name>]
  python3 -I maintainer/harness.py records notes <dir>
  python3 -I maintainer/harness.py records move <old parent> <new parent>
  python3 -I maintainer/harness.py records memory <from> <old folder> [--new <checkout>]
                                   [--projects <dir>]
(Windows: py -3 -I ...). <t> is a copy's folder in the scratchpad (<scratchpad>/t, <scratchpad>/t2,
...); the copy is <t>/log. <w> defaults to the worktree this script is in, <b> to its current branch,
<d> to its default branch (origin/HEAD). The records subcommands also take --records <dir> (default:
career-log-experiments/ beside the main checkout, the first path `git worktree list` prints, of
--root, default the repository this script is in) and --date <YYYY-MM-DD> (default: today).

Every copy is made for *The real profile*'s rules: <t>/log has a config.toml with
update_check = "off" (left out with --no-config; a release before update_check: the
config.toml only), <t>/home/AppData/Roaming and
<t>/home/AppData/Local exist, and the copy's own tools run with HOME, USERPROFILE, APPDATA and
LOCALAPPDATA pointed there. <t>/harness.json records how the copy was made; reset, verify, start
and remove refuse a folder without it.

copy           builds a copy of <b> as it is committed in <w> (an uncommitted change in a tracked
               file is refused: the fetch takes commits only), with <b> as <t>/log's default
               branch <d>, its origin the bare repo <t>/remote.git, identity Test
               <test@example.invalid>. It carries no Log data: this repo holds no Log, so the copy
               is the Engine and the maintainer's files, for a case that runs in this repo itself;
               a case that reads entries, profile or direction takes template-copy and fixtures.
               A <b> that holds Log data (a Log file or folder of tools/logfiles.py's LOG_FILES and
               LOG_FOLDERS but entries/_template.md, the front pages and config.toml) is refused,
               by reset too. When update_check is not off, a commit `test: update_check off` on top
               of the head under test turns it off and is pushed; it changes no Engine file. Then
               runs verify. <t> must be empty or missing.
template-copy  builds a copy from `tools/export-template.sh` of <w>'s committed head: a new Log
               with no history, its seed commit with the head's executable bits, as "Use this
               template" gives them (a copy on Windows has no executable bit to stage). --from
               <dir> takes the files of <dir> in place of the export (a past release:
               `git -C <clone> archive v<release> | tar -x -C <dir>`); with --modes-from
               <clone> v<release>, its seed commit takes that ref's file modes, as the release has them (a folder on Windows has no executable bit to stage), and a ref
               whose files are not <dir>'s is refused. Writes
               config.toml from config.default.toml with update_check off (a release before
               update_check: with its defaults; --no-config leaves it out: only a case testing the
               Trigger check's stop for a missing config.toml), commits it all as `seed`, pushes it to <t>/remote.git and runs
               verify. --no-seed stops before the commit, for the expected sheet's edits: make
               them in <t>/log, then run seed.
seed           commits and pushes a --no-seed Template copy, then runs verify.
reset          puts a copy back on <b>'s current commit in <w> before a run after its first: the
               last run's worktrees, branches (in both repos), commits and files, ignored ones
               (.build/) too, are gone, and so are a process run's <t>/process and <t>/config, and
               <t>/log/.git/info/exclude is emptied; then update_check as copy does, then verify. A Template
               copy is not reset: remove it and build it again.
verify         prints one `PASS|FAIL <check>: <evidence>` line per Done-when check of the copy:
               head (the head under test, or the update_check commit on top of it; a Template
               copy: its seed commit), config, branch, origin-head, origin, branches, worktrees,
               clean (`git status --porcelain --ignored` prints nothing), home; then
               `start: <short sha>`, the copy's HEAD.
prompt         prints the clean-agent prompt for <t> and the run named <run> (start's `run:`
               line), its paths with forward slashes, with the user message from <file> verbatim. --browser playwright gives the playwright-cli
               line (default fetch). --signed-in <file> replaces the `Never sign in` line with the
               file's line (*The clean-agent prompt's sign-in rule*). --relay turn (a process
               run) says the user's replies come as the next user message, not by SendMessage,
               and leaves out the line that asks for foreground subagents (a subagent run keeps it:
               a background subagent's result is lost once that run's turn ends) and the line that
               sets aside memory and rules from outside the copy (a subagent run keeps it: it runs
               in the tester's session, with the tester's memory and settings in context).
start         runs verify, then adds the run's row to <file> (JSON lines): name
               v<round><model letter>-<n>, model, head (the commit under test, short), copy <t>, start (the
               copy's HEAD), the test case, and the sha256 of the real ~/.career-log/machine.toml
               (`absent` when there is none). Prints `run:`, `start:` and `machine.toml:` lines.
               Refuses (1) while verify fails, or when <b> (a Template copy: <w>'s HEAD) has moved
               since the copy was built or reset: reset the copy first (a Template copy: remove
               it and build it again). A case outside a round takes --round 0.
process        runs the started run as its own `claude -p` stream-json process (a process run,
               *Start a clean agent*), in <t>/log, on the row's model at --effort, with
               --permission-mode bypassPermissions, the four home variables pointed into
               <t>/home, none of the tester's CLAUDE* variables (its session, host login, plugin
               folders; CLAUDE_CODE_GIT_BASH_PATH stays) or API keys, and
               CLAUDE_CONFIG_DIR=<t>/config: a config folder holding only
               skills/career-log, a link (a junction on Windows) to <t>/log's skill. It copies
               no login: it passes CLAUDE_CODE_OAUTH_TOKEN (`claude setup-token`) or
               ANTHROPIC_API_KEY from this command's environment, and refuses (1) without
               either. Run it in the background: it
               sends <t>/process/in/<n>.txt as user turn <n> (say writes them), stops on
               in/END (in a turn too), when the process exits, or after --idle minutes (default
               240) with no turn sent (a turn that hangs is not timed: say --end, or stop this
               command), and deletes a .credentials.json in <t>/config (none should be there)
               when it stops by itself; killed, it leaves it for collect, reset or remove. It
               reads the process's output all the time, so a background subagent runs on after
               a turn's result (output left unread stops the process). Turn <n> ends at the first result with no background subagent
               running (nor a shell command one started); while one runs, its notification starts
               a new turn within turn <n>. out/<n>.txt holds each result of the turn, `---`
               between them. A turn the process starts itself after turn <n> ended (the
               notification of its own background shell command, say) adds its result to
               out/<n>.txt, and the next turn waits for it; one that starts after say sent the
               next turn is taken for that turn.
               <t>/process/events.log gets `PID <its pid>`, `CHILD <claude's pid>`, `TURN <n> SENT`,
               `SESSION <id>`, `TURN <n> WAITING <subagents>`, `TURN <n> DONE <subtype>|DONE
               error|PROCESS EXITED`, `TURN <n> LATE <subtype>`, `IDLE TIMEOUT`, `HARNESS ERROR
               <error>` (this command failed and stopped the process), `credentials: deleted|left
               <file>` and last `ENDED`. Exits 1 when no session
               started. The raw stream goes to stream.jsonl, the process's stderr with it; when
               the process ends by itself (at once, say: Claude Code refuses
               bypassPermissions as root unless IS_SANDBOX=1 is set), it prints `process exited
               (code <n>)` and the stream's last lines that are no event (stderr) or a result in
               error. The row gets the session id and the transcript:
               <t>/config/projects/<project folder of <t>/log>/<session>.jsonl, its subagents in
               <session>/subagents/.
say            sends <file> as the process run's next user turn (the first: what `prompt --relay
               turn` printed; later ones: a `User:` reply), waits until the turn ends, and prints
               the turn's messages (<t>/process/out/<n>.txt, `---` between them), after a `note:`
               line when the turn before got a message after its say exited (TURN <n-1> LATE). Run
               it in the background and read its
               output when it exits. --end stops the process. Exits 1 when the turn ended in an
               error (a failed login: `Failed to authenticate`), the process command failed (its
               `HARNESS ERROR` line), or the process ended before it (then it prints those stream lines too).
collect        grades a finished run: runs <w>'s `tools/check_run.py --agent <id> --copy <t>/log
               --base <start>` (run it in the session that started the run, since --agent reads
               its transcripts), prints its output, and hashes machine.toml again:
               `PASS machine-toml: unchanged` or `FAIL machine-toml: <before> -> <after>`. Both
               go in the run's row with the agent id. A process run takes no --agent: it passes
               --transcript with the row's transcript, refuses (1) until the process has ENDED or
               is gone (killed: a credentials file it left is deleted, on a NOTE line),
               copies the transcript and its <session>/ folder to transcripts/<run>/ beside
               <file> (records scratchpad leaves <t> out), and prints `PASS credentials: deleted`
               or `FAIL credentials: <file> is left`. Exits with check_run.py's code (1 also for a
               changed machine.toml or credentials left).
report         prints the round's first line (`<effort>` left for the agent), its table (a
               `mechanical` row per run: name, test case, check_run.py's Grade line, machine.toml)
               and its `Bar:` line, each check check_run.py graded counted
               as passes (PASS or NOTE) over the runs that reached it (not SKIP): raw counts, every
               run counted, before Grading's exceptions. The judgement
               checks, Fixes and Decisions are the agent's to add.
signed-in-home links the real ~/.career-log/browser-profile into <t>/home/.career-log/ (a junction
               on Windows; an old link there is replaced, a folder refused) and copies the real
               machine.toml there, fresh each time, for a signed-in case on this machine's profile
               (docs/maintaining-tests.md). Run it after copy or template-copy and again after each
               reset. remove deletes the link, never the profile.
remove         deletes each <t> (read-only git files too), a .credentials.json in its config/
               first (none should be there). A folder a process still holds is named on a
               `locked:` line: delete it after the session ends (a `credentials:` line names a
               credentials file it could not delete).

records project-folder  prints the name Claude Code gives a working directory's folder under
               ~/.claude/projects/ (default: the current folder): every character other than a
               letter or digit becomes `-`; a name over 200 characters is cut there and given a
               suffix, so look for the folder that starts with its first 200.
records snapshot  copies every folder under --projects (default: CLAUDE_CONFIG_DIR's or
               ~/.claude's projects/) whose name starts with --folder (default: the main
               checkout's project folder) into <records>/snapshot-<date>/: its memory, and the
               transcripts of the main checkout and its worktrees. Adds to a snapshot already
               there; deletes nothing. Prints each folder copied, the memory check, and how many
               `<folder>--claude-worktrees-*` folders it copied.
records scratchpad  copies a session's scratchpad <dir> into
               <records>/snapshot-<date>/scratchpads/<folder>/<id>/ (--folder: default the
               current folder's project folder), leaving out each harness copy (<t>).
records notes  copies a side-session notes folder <dir> into
               <records>/snapshot-<date>/side-session-notes/<its name>/.
records move   copies <old parent>/career-log-experiments/ to <new parent>/; prints `skip:` when
               <new parent> has one already. Then lists its snapshot-* folders.
records memory  copies <from>/<old folder>/memory into <projects>/<new folder>/memory, where
               <from> is the old ~/.claude/projects/ or a snapshot-<date>/ folder, and <new
               folder> is --new's project folder (default: the main checkout). Adds and
               overwrites files, deletes none. Get <old folder> with `records project-folder` on
               the old machine, or from the folder names in <from>.
Exit 0 when done, 1 when a check fails (the reason on stderr), 2 on a usage error.
Standard library only, Python 3.11+.
"""
import argparse, contextlib, datetime, errno, hashlib, json, os, queue, re, shutil, stat, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))   # -I leaves it off sys.path
sys.dont_write_bytecode = True
import logfiles  # noqa: E402

META = "harness.json"
RECORDS = "career-log-experiments"
CONFIG_COMMIT = "test: update_check off"
UPDATE_OFF = re.compile(r'^\s*update_check\s*=\s*"off"', re.M)

PROMPT = """You are a coding agent with the `career-log` skill installed. The skill's base directory is {t}/log/skills/career-log. Read SKILL.md there first and follow it. The Log root is {t}/log.

Environment rules:
{sign_in}
- Browser: {browser}.
- Write files only inside the Log root (drafts in .build/{run}/).
- Use `gh` for reads only.
- Never run setup (setup.sh, setup.ps1), tlmgr, winget, brew or micromamba. When the Trigger check or the Start check says to stop or to run setup, skip it and go on with the case.
- Start every shell command by pointing HOME, USERPROFILE, APPDATA and LOCALAPPDATA into {t}/home (Bash: `export HOME={t}/home USERPROFILE={t}/home APPDATA={t}/home/AppData/Roaming LOCALAPPDATA={t}/home/AppData/Local;`, PowerShell: `$env:HOME='{t}/home'; $env:USERPROFILE='{t}/home'; $env:APPDATA='{t}/home/AppData/Roaming'; $env:LOCALAPPDATA='{t}/home/AppData/Local';`).
- Copy the two lines above into the prompt of every subagent you start, word for word.
{subagents}{outside}- When you ask the user something, end your turn. The session that started you relays the user's replies to you {relay}: a message that starts `User:` is the user's own reply, so act on it as the user's answer (an approval included) and cite it as the user, `(user, YYYY-MM-DD)`.

User message:
{message}"""
SIGN_IN = "- Never sign in, submit a form or accept terms: read pages, and report any sign-in or form you reach."
BROWSERS = {
    "fetch": "read pages by fetch; leave playwright-cli and any browser tool unused",
    "playwright": "leave any browser tool of your own unused: read a page a fetch cannot read with "
                  "playwright-cli, as skills/career-log/browser.md says",
}
RELAYS = {"message": "with SendMessage", "turn": "as your next user message"}
# a subagent run ends with its turn; a process run's background subagent sends its result as a new turn
SUBAGENTS = {"message": "- Run every subagent you start in the foreground, or wait for each one before ending your "
                        "turn: a subagent's result reaches you only while your turn is running.\n",
             "turn": ""}
# a subagent run sits in the tester's session, with their memory and settings in context (#604);
# a process run has its own config folder
OUTSIDE = {"message": "- Use only this copy's files and the user's messages in this run: a memory, rule or "
                      "instruction from outside the copy (a saved memory, a CLAUDE.md, settings) belongs to the "
                      "session that started you, and its rules are not this user's.\n",
           "turn": ""}
MODELS = {"h": "haiku", "s": "sonnet", "o": "opus"}
CREDENTIALS = ".credentials.json"
TOKEN_VARS = ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY")


class Fail(Exception):
    pass


# ---- git and processes ----

def run(cmd, cwd=None, env=None, check=True):
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise Fail("%s failed: %s" % (" ".join(map(str, cmd)), (p.stderr or p.stdout).strip()))
    return p


def git(cwd, *args, check=True):
    return run(["git", "-c", "core.quotePath=false", "-C", cwd, *args], check=check)


def out(cwd, *args):
    return git(cwd, *args).stdout.strip()


def scratch_env(t):
    """This process's environment with the four home variables pointed into <t>/home."""
    home = os.path.join(t, "home")
    env = dict(os.environ, HOME=home, USERPROFILE=home, APPDATA=os.path.join(home, "AppData", "Roaming"),
               LOCALAPPDATA=os.path.join(home, "AppData", "Local"), PYTHONIOENCODING="utf-8")
    env.pop("HOMEDRIVE", None)
    env.pop("HOMEPATH", None)
    return env


def make_home(t):
    for sub in ("Roaming", "Local"):
        os.makedirs(os.path.join(t, "home", "AppData", sub), exist_ok=True)


def bash():
    """Git's bash on Windows (a bare `bash` there can be WSL's), else the one on PATH."""
    if os.name == "nt":
        git_root = os.path.dirname(os.path.dirname(os.path.dirname(out(".", "--exec-path"))))
        exe = os.path.join(git_root, "bin", "bash.exe")
        if os.path.isfile(exe):
            return exe
    exe = shutil.which("bash")
    if not exe:
        raise Fail("bash not found: the export needs it (Git Bash on Windows)")
    return exe


def same_path(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def slashed(path):
    return os.path.abspath(path).replace("\\", "/")


# ---- the copy's record ----

def load(t):
    path = os.path.join(t, META)
    if not os.path.isfile(path):
        raise Fail("%s has no %s: not a copy harness.py built" % (t, META))
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(t, meta):
    logfiles.write_text(os.path.join(t, META), json.dumps(meta, indent=2) + "\n")


def guarded(t):
    """The copy's record, after checking that <t>/log pushes only to <t>/remote.git."""
    meta = load(t)
    log = os.path.join(t, "log")
    if meta.get("seeded", True):
        url = git(log, "remote", "get-url", "origin", check=False).stdout.strip()
        if not url or not same_path(url, os.path.join(t, "remote.git")):
            raise Fail("%s's origin is %s, not %s: refusing" % (log, url or "unset", os.path.join(t, "remote.git")))
    return meta


def empty_target(t):
    """Make <t>, with a record that lets remove delete it should the build fail."""
    if os.path.exists(t) and (not os.path.isdir(t) or os.listdir(t)):
        raise Fail("%s is not empty: remove it first (harness.py remove)" % t)
    os.makedirs(t, exist_ok=True)
    save(t, {"kind": "building", "seeded": False})


def committed(worktree):
    changed = out(worktree, "status", "--porcelain", "--untracked-files=no")
    if changed:
        raise Fail("%s has uncommitted changes (the copy takes commits only): commit them first\n%s" % (worktree, changed))
    untracked = out(worktree, "ls-files", "--others", "--exclude-standard")
    if untracked:
        print("note: untracked, so not in the copy: %s" % ", ".join(untracked.splitlines()))


def resolve(a):
    worktree = os.path.abspath(a.worktree or ROOT)
    branch = getattr(a, "branch", None) or out(worktree, "branch", "--show-current")
    if not branch:
        raise Fail("%s is on a detached HEAD: pass --branch" % worktree)
    default = a.default or logfiles.default_branch(worktree)
    if not default:
        raise Fail("%s has no origin/HEAD: pass --default" % worktree)
    return worktree, branch, default


def update_check_off(t, default):
    """Turn update_check off in <t>/log; commit and push when that changed config.toml."""
    log = os.path.join(t, "log")
    env = scratch_env(t)
    tool = os.path.join(log, "tools", "config.py")
    if not os.path.isfile(os.path.join(log, "config.toml")):
        run([sys.executable, "-I", tool, "--root", log, "init"], env=env)
    run([sys.executable, "-I", tool, "--root", log, "set", "update_check", "off"], env=env)
    if out(log, "status", "--porcelain", "--", "config.toml"):
        git(log, "add", "config.toml")
        git(log, "commit", "-qm", CONFIG_COMMIT, "--", "config.toml")
        git(log, "push", "-q", "origin", default)
        return True
    return False


# ---- copy, template-copy, seed, reset, verify ----

# The Log's own files (logfiles.LOG_FILES) that a copy of this repo refuses: not the front pages,
# which an Engine repo may have too, nor config.toml, which copy writes itself.
DATA_FILES = [p for p in logfiles.LOG_FILES if p not in ("README.md", "README.zh-TW.md", "config.toml")]


def no_log_data(worktree, branch):
    """Refuse a <branch> that holds Log data (#29: this repo holds none, and a copy takes none)."""
    paths = out(worktree, "ls-tree", "-r", "--name-only", "--full-tree", branch).splitlines()
    data = [p for p in paths if p not in logfiles.NOT_LOG
            and (p in DATA_FILES or p.split("/", 1)[0] in logfiles.LOG_FOLDERS and "/" in p)]
    if data:
        raise Fail("%s holds Log data (%s%s): copy takes the Engine only; a case that reads the Log "
                   "builds it with template-copy and fixtures (docs/maintaining-tests.md › Harness)"
                   % (branch, ", ".join(data[:5]), ", ..." if len(data) > 5 else ""))


def cmd_copy(a):
    worktree, branch, default = resolve(a)
    committed(worktree)
    no_log_data(worktree, branch)
    t = os.path.abspath(a.t)
    empty_target(t)
    remote, log = os.path.join(t, "remote.git"), os.path.join(t, "log")
    git(t, "init", "-q", "--bare", "-b", default, remote)
    git(remote, "config", "core.longpaths", "true")
    logfiles.no_maintenance(remote)   # it fetches and receives pushes, and the log fetches: no gc left running
    git(remote, "fetch", "-q", worktree, "+%s:%s" % (branch, default))
    run(["git", "-c", "core.longpaths=true", "clone", "-q", remote, log])
    for k, v in (("core.longpaths", "true"), ("user.email", "test@example.invalid"), ("user.name", "Test")):
        git(log, "config", k, v)
    logfiles.no_maintenance(log)
    make_home(t)
    head = out(remote, "rev-parse", default)
    save(t, {"kind": "copy", "worktree": worktree, "branch": branch, "default": default, "head": head,
             "no_config": False, "seeded": True})
    update_check_off(t, default)
    print("note: %s holds no Log data (no entries, profile or direction): a case that reads them "
          "takes template-copy and fixtures" % log)
    return cmd_verify(a)


def cmd_template_copy(a):
    if a.modes_from and not a.source:
        raise Fail("--modes-from goes with --from: the export's own modes are not a release's")
    worktree, _, default = resolve(argparse.Namespace(worktree=a.worktree, branch="-", default=a.default))
    committed(worktree)
    t = os.path.abspath(a.t)
    empty_target(t)
    export, log = os.path.join(t, "export"), os.path.join(t, "log")
    executable = None
    if a.source:
        if not os.path.isdir(a.source):
            raise Fail("%s is not a folder" % a.source)
        shutil.copytree(a.source, export, ignore=shutil.ignore_patterns(".git"))
        if a.modes_from:
            executable = release_modes(export, *a.modes_from)
    else:
        p = run([bash(), os.path.join(worktree, "tools", "export-template.sh"), slashed(export)], cwd=worktree, check=False)
        if p.returncode != 0:
            raise Fail("the export failed:\n" + (p.stdout + p.stderr).strip())
        executable = export_modes(worktree)
    git(t, "init", "-q", "-b", default, log)
    for k, v in (("core.longpaths", "true"), ("user.email", "test@example.invalid"), ("user.name", "Test")):
        git(log, "config", k, v)
    logfiles.no_maintenance(log)   # it pushes and fetches: no gc left running
    shutil.copytree(export, log, dirs_exist_ok=True)
    make_home(t)
    # a release before update_check (0.1.0) has no update check to turn off
    defaults = os.path.join(log, "tools", "config.default.toml")
    if not os.path.isfile(defaults):
        raise Fail("%s has no tools/config.default.toml: not a Template tree" % (a.source or export))
    has_update_check = "update_check" in logfiles.read_text(defaults)
    if not a.no_config:
        env = scratch_env(t)
        tool = os.path.join(log, "tools", "config.py")
        run([sys.executable, "-I", tool, "--root", log, "init"], env=env)
        if has_update_check:
            run([sys.executable, "-I", tool, "--root", log, "set", "update_check", "off"], env=env)
    save(t, {"kind": "template", "worktree": worktree, "branch": None, "default": default,
             "head": out(worktree, "rev-parse", "HEAD"), "no_config": a.no_config, "seeded": False,
             "update_check": has_update_check, "from": os.path.abspath(a.source) if a.source else None,
             "executable": executable})
    if a.no_seed:
        print("next: make the expected sheet's edits in %s, then run harness.py seed %s" % (log, t))
        return 0
    return seed(t)


def tree_modes(text):
    """{path: mode} from `git ls-tree -r` output."""
    return {l.split("\t", 1)[1]: l.split()[0] for l in text.splitlines() if "\t" in l}


def export_modes(worktree):
    """The paths the export of <worktree>'s head writes as 100755: each such path of the head, and,
    as coord.py set_modes has it, tools/template/<path> again as <path> (the skeleton). seed sets
    only the ones it stages."""
    want = set()
    for path, mode in tree_modes(out(worktree, "ls-tree", "-r", "--full-tree", "HEAD")).items():
        if mode == "100755":
            want.add(path)
            if path.startswith("tools/template/"):
                want.add(path[len("tools/template/"):])
    return sorted(want)


def release_modes(tree, repo, ref):
    """The 100755 paths of <ref> in <repo>, once its files are the ones <tree> holds."""
    p = git(repo, "ls-tree", "-r", "--full-tree", ref, check=False)
    if p.returncode != 0:
        raise Fail("--modes-from: no %s in %s: %s" % (ref, repo, (p.stderr or p.stdout).strip()))
    modes = tree_modes(p.stdout)
    files = {os.path.relpath(os.path.join(d, f), tree).replace(os.sep, "/")
             for d, _, names in os.walk(tree) for f in names}
    if set(modes) != files:
        odd = sorted(set(modes) ^ files)
        raise Fail("--modes-from: %s in %s does not hold the files of --from (%s%s)"
                   % (ref, repo, ", ".join(odd[:5]), ", ..." if len(odd) > 5 else ""))
    return sorted(path for path, mode in modes.items() if mode == "100755")


def seed(t):
    meta = load(t)
    if meta["kind"] != "template" or meta["seeded"]:
        raise Fail("%s is not a Template copy waiting for its seed commit" % t)
    log, remote, default = os.path.join(t, "log"), os.path.join(t, "remote.git"), meta["default"]
    git(log, "add", "-A")
    # a folder on Windows (core.fileMode false) stages every file 100644
    staged = {l.split("\t", 1)[1]: l.split()[0] for l in out(log, "ls-files", "-s").splitlines() if "\t" in l}
    plus = [p for p in meta.get("executable") or [] if staged.get(p) not in (None, "100755")]
    if plus:
        git(log, "update-index", "--chmod=+x", "--", *plus)
    git(log, "commit", "-qm", "seed")
    git(t, "init", "-q", "--bare", "-b", default, remote)
    git(remote, "config", "core.longpaths", "true")
    logfiles.no_maintenance(remote)   # it receives pushes
    git(log, "remote", "add", "origin", remote)
    git(log, "push", "-qu", "origin", default)
    git(log, "remote", "set-head", "origin", default)
    meta.update(seeded=True, seed=out(log, "rev-parse", "HEAD"))
    save(t, meta)
    return verify(t)


def cmd_seed(a):
    return seed(os.path.abspath(a.t))


def cmd_reset(a):
    t = os.path.abspath(a.t)
    meta = guarded(t)
    if meta["kind"] == "building":
        raise Fail("the build did not finish: harness.py remove %s, then build it again" % t)
    if meta["kind"] != "copy":
        raise Fail("a Template copy is not reset: harness.py remove %s, then template-copy again" % t)
    log, remote, default = os.path.join(t, "log"), os.path.join(t, "remote.git"), meta["default"]
    committed(meta["worktree"])
    no_log_data(meta["worktree"], meta["branch"])
    git(remote, "fetch", "-q", meta["worktree"], "+%s:%s" % (meta["branch"], default))
    worktrees = [line[len("worktree "):] for line in out(log, "worktree", "list", "--porcelain").splitlines()
                 if line.startswith("worktree ")]
    for path in worktrees[1:]:
        git(log, "worktree", "remove", "--force", "--force", path)   # twice: also a locked one
    git(log, "worktree", "prune")
    git(log, "fetch", "-q", "--prune")
    git(log, "checkout", "-q", "-f", "-B", default, "origin/" + default)
    git(log, "clean", "-qfdx")
    logfiles.write_text(os.path.join(log, ".git", "info", "exclude"), "")   # a process run's case paths
    left = delete_credentials(t)
    if left:
        raise Fail("%s could not be deleted: is the run's process still running?" % left)
    unlink_dir(os.path.join(t, "config", "skills", "career-log"))   # the link only, never the skill
    for folder in (process_dir(t), os.path.join(t, "config")):   # the last process run's
        if os.path.isdir(folder):
            logfiles.rmtree(folder)
    for repo in (log, remote):
        for name in out(repo, "branch", "--format=%(refname:short)").splitlines():
            if name and name != default:
                git(repo, "branch", "-D", name)
    git(log, "fetch", "-q", "--prune")
    meta["head"] = out(remote, "rev-parse", default)
    save(t, meta)
    make_home(t)
    update_check_off(t, default)
    return verify(t)


def checks(t, meta):
    """The Done-when checks of the copy: (name, passed, evidence)."""
    log, default = os.path.join(t, "log"), meta.get("default")
    if meta["kind"] == "building":
        return [("build", False, "the build did not finish: harness.py remove %s, then build it again" % t)]
    if not meta.get("seeded", True):
        return [("seed", False, "no seed commit yet: run harness.py seed")]
    res = []
    head = out(log, "rev-parse", "HEAD")
    if meta["kind"] == "template":
        res.append(("head", head == meta.get("seed"), "%s (seed %s)" % (head[:7], (meta.get("seed") or "?")[:7])))
    else:
        parent = git(log, "rev-parse", "HEAD^", check=False).stdout.strip()
        subject = out(log, "log", "-1", "--format=%s")
        ok = head == meta["head"] or (parent == meta["head"] and subject == CONFIG_COMMIT)
        res.append(("head", ok, "%s (under test %s%s)" % (head[:7], meta["head"][:7],
                                                          ", update_check commit on top" if head != meta["head"] else "")))
    config = git(log, "show", "HEAD:config.toml", check=False)
    if meta.get("no_config"):
        listed = out(log, "ls-files", "config.toml")
        res.append(("config", not listed, "config.toml absent (--no-config)" if not listed else "config.toml is committed"))
    elif not meta.get("update_check", True):
        ok = config.returncode == 0
        res.append(("config", ok, "HEAD:config.toml is there (this release has no update_check)" if ok
                    else "HEAD:config.toml is missing"))
    else:
        ok = config.returncode == 0 and bool(UPDATE_OFF.search(config.stdout))
        res.append(("config", ok, 'HEAD:config.toml has update_check = "off"' if ok else "HEAD:config.toml lacks update_check = \"off\""))
    current = out(log, "branch", "--show-current")
    res.append(("branch", current == default, current or "detached"))
    origin_head = git(log, "symbolic-ref", "--short", "refs/remotes/origin/HEAD", check=False).stdout.strip()
    res.append(("origin-head", origin_head == "origin/" + default, origin_head or "unset"))
    url = git(log, "remote", "get-url", "origin", check=False).stdout.strip()
    res.append(("origin", bool(url) and same_path(url, os.path.join(t, "remote.git")), url or "unset"))
    branches = sorted("origin/HEAD" if b == "origin" else b   # origin/HEAD's short name in some git versions
                      for b in out(log, "branch", "-a", "--format=%(refname:short)").splitlines())
    want = sorted([default, "origin/" + default, "origin/HEAD"])
    res.append(("branches", branches == want, ", ".join(branches)))
    wts = out(log, "worktree", "list").splitlines()
    res.append(("worktrees", len(wts) == 1, "%d listed" % len(wts)))
    status = out(log, "status", "--porcelain", "--ignored")
    res.append(("clean", not status, "nothing to report" if not status else status.splitlines()[0] + " ..."))
    homes = [os.path.join(t, "home", "AppData", s) for s in ("Roaming", "Local")]
    res.append(("home", all(os.path.isdir(h) for h in homes), slashed(os.path.join(t, "home"))))
    return res


def verify(t, show_start=True):
    meta = guarded(t)
    failed = False
    for name, ok, evidence in checks(t, meta):
        print("%s %s: %s" % ("PASS" if ok else "FAIL", name, evidence))
        failed |= not ok
    if show_start and meta.get("seeded", True):
        print("start: %s" % out(os.path.join(t, "log"), "rev-parse", "--short", "HEAD"))
    return 1 if failed else 0


def cmd_verify(a):
    return verify(os.path.abspath(a.t))


# ---- prompt, start, collect, report ----

def cmd_prompt(a):
    t = slashed(a.t)
    load(a.t)
    message = logfiles.read_text(a.message).rstrip("\n")
    sign_in = SIGN_IN
    if a.signed_in:
        sign_in = logfiles.read_text(a.signed_in).strip()
        if "\n" in sign_in:
            raise Fail("--signed-in takes a file of one line")
    print(PROMPT.format(t=t, run=a.run, sign_in=sign_in, browser=BROWSERS[a.browser], relay=RELAYS[a.relay],
                        subagents=SUBAGENTS[a.relay], outside=OUTSIDE[a.relay], message=message))
    return 0


def machine_toml():
    return os.path.join(os.path.expanduser("~"), ".career-log", "machine.toml")


def is_link(path):
    """A symlink, or on Windows a junction (os.path.isjunction is 3.12+)."""
    if os.path.islink(path):
        return True
    attrs = getattr(os.lstat(path), "st_file_attributes", 0) if os.path.lexists(path) else 0
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def cmd_signed_in_home(a):
    t = os.path.abspath(a.t)
    load(t)
    real = os.path.join(os.path.expanduser("~"), ".career-log")
    profile = os.path.join(real, "browser-profile")
    if not os.path.isdir(profile):
        raise Fail("no browser profile at %s: run setup's browser step and sign in first" % profile)
    if os.path.realpath(real).startswith(os.path.realpath(t) + os.sep):
        raise Fail("the home %s is inside %s: run this from the real home, not the copy's" % (real, t))
    home = os.path.join(t, "home", ".career-log")
    os.makedirs(home, exist_ok=True)
    link = os.path.join(home, "browser-profile")
    if os.path.lexists(link):
        if not is_link(link):
            raise Fail("%s is a folder, not a link: refusing to replace it" % link)
        unlink_dir(link)   # never a second link through the old one, which lands inside the profile
    link_dir(link, profile)
    print("linked: %s -> %s" % (slashed(link), slashed(profile)))
    if os.path.isfile(machine_toml()):
        shutil.copyfile(machine_toml(), os.path.join(home, "machine.toml"))   # fresh: the last run's writes went to the copy
        print("copied: %s -> %s" % (slashed(machine_toml()), slashed(os.path.join(home, "machine.toml"))))
    else:
        if os.path.isfile(os.path.join(home, "machine.toml")):
            os.remove(os.path.join(home, "machine.toml"))   # as this machine has it: none
        print("machine.toml: none at %s" % slashed(machine_toml()))
    return 0


def file_hash(path):
    if not os.path.isfile(path):
        return "absent"
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def rows(path):
    if not os.path.isfile(path):
        return []
    return [json.loads(line) for line in logfiles.read_text(path).splitlines() if line.strip()]


def write_rows(path, items):
    write_new(path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items))


def write_new(path, text):
    """Write a whole file at once: a reader in another process sees the old text or the new."""
    tmp = "%s.%d.tmp" % (path, os.getpid())
    logfiles.write_text(tmp, text)
    for wait in (0.1, 0.3, 1, 3, None):   # Windows refuses the replace while a reader has it open
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if wait is None:
                raise
            time.sleep(wait)


@contextlib.contextmanager
def locked(path):
    """Hold <runs>.lock from reading <runs> to writing it back: start, process and collect update it
    from different processes. The system drops the lock when its process dies."""
    with open(path + ".lock", "a+b") as f:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            while True:
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as e:
                    if e.errno not in (errno.EACCES, errno.EDEADLK):   # not held by another process
                        raise
                    time.sleep(0.05)
            try:
                yield
            finally:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)


def update_row(path, name, **fields):
    """Update one run's row in <runs> as the file is now, and return the row."""
    with locked(path):
        items, row = find_row(path, name)
        row.update(fields)
        write_rows(path, items)
    return row


def cmd_start(a):
    t = os.path.abspath(a.t)
    meta = guarded(t)
    if verify(t, show_start=False):
        raise Fail("the copy fails a check above: harness.py reset %s (a Template copy: remove it and build it again)" % t)
    now = out(meta["worktree"], "rev-parse", "--verify", "refs/heads/" + meta["branch"] if meta["branch"] else "HEAD")
    if now != meta["head"]:
        raise Fail("the copy holds %s, but %s is at %s now: harness.py reset %s (a Template copy: remove it and "
                   "build it again)" % (meta["head"][:7], meta["branch"] or meta["worktree"], now[:7], t))
    start = out(os.path.join(t, "log"), "rev-parse", "--short", "HEAD")
    with locked(a.runs):
        items = rows(a.runs)
        prefix = "v%d%s-" % (a.round, a.model)
        n = 1 + max([int(r["name"][len(prefix):]) for r in items if r["name"].startswith(prefix)] or [0])
        row = {"name": prefix + str(n), "round": a.round, "model": MODELS[a.model], "agent": None,
               "head": meta["head"][:7], "copy": slashed(t), "start": start, "case": a.case,
               "machine_toml": file_hash(machine_toml())}
        write_rows(a.runs, items + [row])
    print("run: %s" % row["name"])
    print("start: %s" % row["start"])
    print("machine.toml: %s" % row["machine_toml"])
    print("next: start the agent with `harness.py prompt %s --run %s --message <file>` as its prompt, then, when "
          "it ends, harness.py collect %s --runs %s --agent <id> (a process run: prompt with --relay turn, then "
          "harness.py process and say, and collect with no --agent)"
          % (slashed(t), row["name"], row["name"], slashed(a.runs)))
    return 0


# ---- a process run ----

def process_dir(t):
    return os.path.join(t, "process")


def link_dir(link, target):
    """A link to a folder: a junction on Windows (no privilege needed), else a symlink."""
    if os.name == "nt":
        run(["cmd", "/c", "mklink", "/J", link, target])
    else:
        os.symlink(target, link, target_is_directory=True)


def unlink_dir(link):
    """Remove a link_dir link, leaving its target."""
    if os.path.islink(link):
        os.unlink(link)
    elif os.name == "nt" and (os.path.isdir(link) or is_link(link)):
        os.rmdir(link)   # a junction, dangling too: rmdir removes the link alone


def make_config(t):
    """<t>/config for CLAUDE_CONFIG_DIR: skills/career-log links the copy's skill; returns the token
    variables to pass on. No login file is copied: a copied .credentials.json the run refreshed once
    signed the maintainer's own CLI out (#544)."""
    config = os.path.join(t, "config")
    skill = os.path.join(t, "log", "skills", "career-log")
    if not os.path.isdir(skill):
        raise Fail("%s has no skill to link" % skill)
    os.makedirs(os.path.join(config, "skills"), exist_ok=True)
    link = os.path.join(config, "skills", "career-log")
    if not os.path.exists(link):
        link_dir(link, skill)
    tokens = {k: os.environ[k] for k in TOKEN_VARS if os.environ.get(k)}
    if not tokens:
        raise Fail("none of %s set, and the login file is not copied: set CLAUDE_CODE_OAUTH_TOKEN in "
                   "this command's environment from the token file; with none, ask the maintainer for a "
                   "`claude setup-token` token (docs/maintaining-tests.md, A run as its own process)"
                   % ", ".join(TOKEN_VARS))
    return tokens


def delete_credentials(t):
    """Delete a credentials file in <t>/config (a guard: the run gets a token, not a copy); the path
    left behind, or None."""
    path = os.path.join(t, "config", CREDENTIALS)
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except OSError:
        return path
    return None


def run_env(t):
    """scratch_env without the tester's own Claude Code variables (its session, host login, plugin
    folders) and API keys, so the run starts as a user's would; Git Bash's path stays."""
    return {k: v for k, v in scratch_env(t).items()
            if not (k.upper().startswith("CLAUDE") or k.upper() in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"))
            or k.upper() == "CLAUDE_CODE_GIT_BASH_PATH"}


def claude_cmd():
    """The claude command; HARNESS_CLAUDE names another (a .py runs on this Python), for the tests."""
    exe = os.environ.get("HARNESS_CLAUDE") or shutil.which("claude")
    if not exe:
        raise Fail("claude not found on PATH")
    return [sys.executable, exe] if exe.endswith(".py") else [exe]


def find_row(path, name):
    items = rows(path)
    row = next((r for r in items if r["name"] == name), None)
    if row is None:
        raise Fail("no run %s in %s" % (name, path))
    return items, row


def transcript_of(t, session):
    projects = os.path.join(t, "config", "projects")
    log = os.path.join(t, "log")
    folder = logfiles.find_project_folder(projects, log) or os.path.join(projects, logfiles.claude_folder(log))
    return slashed(os.path.join(folder, session + ".jsonl"))


def alive(pid):
    if os.name == "nt":   # os.kill would end the process there
        import ctypes
        k = ctypes.windll.kernel32
        k.OpenProcess.restype = ctypes.c_void_p
        k.GetExitCodeProcess.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong))
        k.CloseHandle.argtypes = (ctypes.c_void_p,)
        h = k.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return code.value == 259   # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        pass
    return not unreaped_or_gone(pid)


def unreaped_or_gone(pid):
    """Whether pid, which os.kill(pid, 0) just found, has exited: a zombie its parent has not reaped (#767; a
    container whose PID 1 reaps nothing keeps a killed process that way), or, on Linux, reaped since.
    On macOS a pid reaped between os.kill and ps still counts as running; the next poll sees it gone."""
    try:
        with open("/proc/%d/stat" % pid, encoding="utf-8", errors="replace") as f:
            return f.read().rpartition(")")[2].split()[:1] == ["Z"]   # the name in (...) may hold spaces
    except FileNotFoundError:
        if os.path.isdir("/proc/self"):
            return True   # Linux: reaped since os.kill
    except OSError:
        return False
    try:   # macOS has no /proc
        out = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return False
    return out.returncode == 0 and out.stdout.strip().startswith("Z")


def ended(t):
    """Whether the copy's process has stopped: it wrote ENDED, or it and its claude were killed first."""
    log = os.path.join(process_dir(t), "events.log")
    if not os.path.isfile(log):
        return False
    text = logfiles.read_text(log)
    pids = [int(n) for n in re.findall(r"^(?:PID|CHILD) (\d+)$", text, re.M)]
    return re.search(r"^ENDED$", text, re.M) is not None or (bool(pids) and not any(alive(n) for n in pids))


def cmd_process(a):
    _, row = find_row(a.runs, a.run)
    t = os.path.abspath(row["copy"])
    load(t)
    pdir = process_dir(t)
    if os.path.exists(pdir):
        raise Fail("%s exists: a process ran on this copy already; reset it (harness.py reset %s)" % (pdir, t))
    os.makedirs(os.path.join(pdir, "in"))
    os.makedirs(os.path.join(pdir, "out"))
    logfiles.write_text(os.path.join(pdir, "events.log"), "PID %d\n" % os.getpid())
    try:
        update_row(a.runs, a.run, process=True, effort=a.effort)
        env = dict(run_env(t), CLAUDE_CONFIG_DIR=os.path.join(t, "config"), **make_config(t))
        cmd = claude_cmd() + ["-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
                              "--model", row["model"], "--effort", a.effort, "--permission-mode", "bypassPermissions"]
        return drive(t, cmd, env, a)
    finally:
        left = delete_credentials(t)
        with open(os.path.join(pdir, "events.log"), "a", encoding="utf-8") as ev:
            ev.write("credentials: %s\nENDED\n" % ("left %s" % slashed(left) if left else "deleted"))


def read_stream(stdout, stream, lines):
    """The process's output, read as it comes: each line to stream.jsonl, each event onto lines, None
    at its end (or at its own failure). Output left unread fills the pipe and stops the process, its
    background subagents too."""
    try:
        for line in stdout:
            stream.write(line)
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if isinstance(o, dict):
                lines.put(o)
    finally:
        lines.put(None)


def subagents_running(o):
    """The background subagents a `background_tasks_changed` event lists, by description: each agent,
    and each task a subagent started (a subagent waiting on its own shell command is not done)."""
    return [x.get("description") or x.get("task_id") for x in o.get("tasks") or []
            if x.get("task_type") == "local_agent" or x.get("parent_task_id")]


def write_out(pdir, n, text, add=False):
    path = os.path.join(pdir, "out", "%d.txt" % n)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if add and os.path.isfile(path):
        text = logfiles.read_text(path) + "\n\n---\n\n" + text
    logfiles.write_text(path, text)


def drive(t, cmd, env, a):
    """Send in/<n>.txt as turn <n> until in/END, the process's exit, or --idle minutes with no turn.
    Turn n ends at a result while no background subagent runs: one still running sends its
    notification as a new turn of the process's own, whose result ends turn n once none runs."""
    pdir = process_dir(t)
    events = open(os.path.join(pdir, "events.log"), "a", encoding="utf-8", buffering=1)
    stream = open(os.path.join(pdir, "stream.jsonl"), "a", encoding="utf-8", buffering=1)
    p = subprocess.Popen(cmd, cwd=os.path.join(t, "log"), env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")
    events.write("CHILD %d\n" % p.pid)
    print("process: %s, events in %s" % (p.pid, slashed(os.path.join(pdir, "events.log"))), flush=True)
    lines = queue.Queue()
    reader = threading.Thread(target=read_stream, args=(p.stdout, stream, lines), daemon=True)
    reader.start()
    n, idle, session, exited = 1, time.time(), None, False
    sent = late = False   # turn n is sent and not ended; a turn the process started itself is running
    running, said = [], []   # its background subagents; the turn's messages so far

    def gone():
        """The process ended by itself before turn n ended: its last output (an error on stderr, say)
        goes to stream.jsonl before the event, so say finds it there."""
        reader.join(timeout=30)
        events.write("TURN %d PROCESS EXITED\n" % n)
        return True

    try:
        while True:
            if os.path.exists(os.path.join(pdir, "in", "END")):   # in a turn too: one that waits forever
                break
            try:
                o = lines.get(timeout=1)
            except queue.Empty:
                o = False
            if o is None:   # ended at once (a refused flag, a failed start), between turns or in one
                exited = gone()
                break
            if o:
                kind = (o.get("type"), o.get("subtype"))
                if kind == ("system", "init"):
                    if not session:
                        session = o["session_id"]
                        update_row(a.runs, a.run, session=session, transcript=transcript_of(t, session))
                        events.write("SESSION %s\n" % session)
                    elif not sent and n > 1:   # a notification after turn n-1 ended started a turn
                        late = True
                elif kind == ("system", "background_tasks_changed"):
                    running = subagents_running(o)
                elif o.get("type") == "result":
                    text = o.get("result") or ""
                    if not sent and n > 1:   # that late turn's result: it joins turn n-1's messages
                        late, idle = False, time.time()
                        write_out(pdir, n - 1, text, add=True)
                        events.write("TURN %d LATE %s\n" % (n - 1, "error" if o.get("is_error") else o.get("subtype")))
                        continue
                    if not sent:   # a result before turn 1: no turn to add it to
                        continue
                    said.append(text)
                    if running and not o.get("is_error"):
                        events.write("TURN %d WAITING %s\n" % (n, "; ".join(running)))
                        continue
                    write_out(pdir, n, "\n\n---\n\n".join(said))
                    events.write("TURN %d DONE %s\n" % (n, "error" if o.get("is_error") else o.get("subtype")))
                    n, idle, sent, said = n + 1, time.time(), False, []
                continue
            if sent or late:
                continue
            turn = os.path.join(pdir, "in", "%d.txt" % n)
            if not os.path.exists(turn):
                if time.time() - idle > a.idle * 60:
                    events.write("IDLE TIMEOUT\n")
                    break
                continue
            text = logfiles.read_text(turn)
            try:
                p.stdin.write(json.dumps({"type": "user", "message": {"role": "user", "content": text}}) + "\n")
                p.stdin.flush()
            except OSError:   # BrokenPipeError; EINVAL on Windows: the process has ended
                exited = gone()
                break
            events.write("TURN %d SENT\n" % n)
            sent = True
    except Exception as e:
        events.write("HARNESS ERROR %s: %s\n" % (type(e).__name__, e))
        raise
    finally:
        try:
            p.stdin.close()
        except OSError:
            pass
        try:
            p.wait(timeout=60)
        except subprocess.TimeoutExpired:
            p.kill()
        reader.join(timeout=30)
        events.close()
        stream.close()
    if exited:
        print("process exited (code %s)%s" % (p.returncode, stream_error(pdir)))
    if not session:
        print("ended: no session started (%s)" % slashed(os.path.join(pdir, "stream.jsonl")))
        return 1
    # the project folder exists only once the process has written to it
    row = update_row(a.runs, a.run, transcript=transcript_of(t, session))
    print("ended: %s" % row["transcript"])
    return 0


def stream_error(pdir, keep=10):
    """What the process said last that is no stream event: its lines that are not JSON (stderr: a
    refused flag, a crash) and the text of any result in error, as `\n  <line>` lines; else ""."""
    path = os.path.join(pdir, "stream.jsonl")
    said = []
    for line in (logfiles.read_text(path).splitlines() if os.path.isfile(path) else []):
        try:
            o = json.loads(line)
        except ValueError:
            if line.strip():
                said.append(line.strip())
            continue
        if isinstance(o, dict) and o.get("type") == "result" and o.get("is_error"):
            said.append(str(o.get("result") or o.get("errors") or o.get("subtype")))
    return "".join("\n  " + s for s in said[-keep:])

def cmd_say(a):
    _, row = find_row(a.runs, a.run)
    t = os.path.abspath(row["copy"])
    pdir = process_dir(t)
    log = os.path.join(pdir, "events.log")
    wait = time.time() + 60   # a process started in the background a moment ago
    while not os.path.isfile(log) and time.time() < wait:
        time.sleep(1)
    if not os.path.isfile(log):
        raise Fail("no process for %s: run harness.py process %s first" % (a.run, a.run))
    if ended(t):
        raise Fail("the process of %s has ended%s" % (a.run, stream_error(pdir)))
    if a.end:
        logfiles.write_text(os.path.join(pdir, "in", "END"), "")
        print("end: sent")
        return 0
    n = 1 + len([f for f in os.listdir(os.path.join(pdir, "in")) if re.fullmatch(r"\d+\.txt", f)])
    if n > 1 and not re.search(r"^TURN %d DONE" % (n - 1), logfiles.read_text(log), re.M):
        raise Fail("turn %d has not ended yet: wait for its say to exit" % (n - 1))
    write_new(os.path.join(pdir, "in", "%d.txt" % n), logfiles.read_text(a.message))
    while True:
        text = logfiles.read_text(log)
        done = re.search(r"^TURN %d DONE (\S+)" % n, text, re.M)
        if done:
            if re.search(r"^TURN %d LATE" % (n - 1), text, re.M):
                print("note: turn %d got a message after its say exited: %s" % (
                    n - 1, slashed(os.path.join(pdir, "out", "%d.txt" % (n - 1)))))
            print("turn %d: %s" % (n, done.group(1)))
            print(logfiles.read_text(os.path.join(pdir, "out", "%d.txt" % n)))
            return 1 if done.group(1) == "error" else 0
        failed = re.search(r"^HARNESS ERROR (.*)$", text, re.M)
        if failed:
            print("turn %d: harness.py process failed, and the process with it: %s" % (n, failed.group(1)))
            return 1
        if re.search(r"^(TURN %d PROCESS EXITED|ENDED)$" % n, text, re.M) or ended(t):
            print("turn %d: the process ended first (%s)%s" % (n, slashed(os.path.join(pdir, "stream.jsonl")),
                                                               stream_error(pdir)))
            return 1
        time.sleep(1)


def keep_transcript(row, runs):
    """Copy a process run's transcript and its <session>/ folder beside <runs>, out of <t>."""
    dest = os.path.join(os.path.dirname(os.path.abspath(runs)), "transcripts", row["name"])
    os.makedirs(dest, exist_ok=True)
    shutil.copy2(row["transcript"], dest)
    folder = row["transcript"][:-len(".jsonl")]
    if os.path.isdir(folder):
        shutil.copytree(folder, os.path.join(dest, os.path.basename(folder)), dirs_exist_ok=True)
    return slashed(os.path.join(dest, os.path.basename(row["transcript"])))


def cmd_collect(a):
    _, row = find_row(a.runs, a.run)
    meta = load(row["copy"])
    tool = os.path.join(meta["worktree"], "tools", "check_run.py")
    extra = []
    if row.get("process"):
        if a.agent:
            raise Fail("%s is a process run: collect it without --agent" % a.run)
        if not ended(row["copy"]):
            raise Fail("the process of %s is still running: harness.py say %s --runs %s --end, then wait for it"
                       % (a.run, a.run, slashed(a.runs)))
        left = os.path.join(row["copy"], "config", CREDENTIALS)
        if not os.path.exists(left):
            extra = ["PASS credentials: deleted"]
        elif delete_credentials(row["copy"]):
            extra = ["FAIL credentials: %s is left" % slashed(left)]
        else:   # the process was killed before its own cleanup
            extra = ["NOTE credentials: the process left %s; collect deleted it" % slashed(left)]
        if not row.get("transcript"):
            print(extra[0])
            raise Fail("%s started no session: the process recorded no transcript" % a.run)
        if not os.path.isfile(row["transcript"]):
            print(extra[0])
            raise Fail("%s has no transcript %s: did the process start a session?" % (a.run, row["transcript"]))
        row["kept"] = keep_transcript(row, a.runs)
        which = ["--transcript", row["transcript"]]
    elif a.agent:
        which = ["--agent", a.agent]
    else:
        raise Fail("%s is no process run: pass --agent <id>" % a.run)
    p = run([sys.executable, "-I", tool, *which, "--copy", os.path.join(row["copy"], "log"),
             "--base", row["start"]], env=dict(os.environ, PYTHONIOENCODING="utf-8"), check=False)
    output = (p.stdout + p.stderr).strip()
    after = file_hash(machine_toml())
    same = after == row["machine_toml"]
    hash_line = "PASS machine-toml: unchanged" if same else "FAIL machine-toml: %s -> %s" % (row["machine_toml"], after)
    print(output)
    print(hash_line)
    for line in extra:
        print(line)
    if row.get("kept"):
        print("kept: %s" % row["kept"])
    update_row(a.runs, a.run, agent=a.agent or row.get("session"), check_run=output, check_run_exit=p.returncode,
               machine_toml_after=hash_line, credentials=extra[0] if extra else None, kept=row.get("kept"))
    if p.returncode == 2:
        return 2
    return 1 if p.returncode or not same or any(e.startswith("FAIL") for e in extra) else 0


CHECK_LINE = re.compile(r"^(PASS|NOTE|FAIL|SKIP) ([\w-]+):")


def cmd_report(a):
    items = [r for r in rows(a.runs) if r["round"] == a.round]
    if not items:
        raise Fail("no run of round %d in %s" % (a.round, a.runs))
    heads = sorted({r["head"] for r in items})
    models = sorted({r["model"] for r in items})
    print("Round %d on %s (%s <effort>)" % (a.round, ", ".join(heads), ", ".join(models)))
    print()
    print("| Run | Check | Test case | Result | Evidence |")
    print("|---|---|---|---|---|")
    bar = {}
    for r in items:
        text = r.get("check_run") or ""
        grade = next((line[len("Grade: "):] for line in text.splitlines() if line.startswith("Grade: ")),
                     "not collected" if r.get("agent") is None else "no Grade line")
        machine = (r.get("machine_toml_after") or "not collected").split(": ", 1)[-1]
        print(logfiles.md_row([r["name"], "mechanical", r["case"], grade, "check_run.py; machine.toml %s" % machine]))
        for line in text.splitlines():
            m = CHECK_LINE.match(line)
            if m and m.group(1) != "SKIP":
                passes, reached = bar.get(m.group(2), (0, 0))
                bar[m.group(2)] = (passes + (m.group(1) in ("PASS", "NOTE")), reached + 1)
    print()
    print("Bar: " + ("; ".join("%s: %d/%d" % (k, p, n) for k, (p, n) in bar.items()) or "none collected") + " on this head")
    return 0


# ---- remove ----

def cmd_remove(a):
    failed = 0
    for t in a.t:
        t = os.path.abspath(t)
        load(t)
        left = delete_credentials(t)
        if left:
            print("credentials: %s could not be deleted: delete it after the session ends" % slashed(left))
            failed = 1
        try:
            logfiles.rmtree(t)
            print("removed: %s" % t)
        except OSError as e:
            print("locked: %s (%s): delete it after the session ends" % (t, e.strerror or e))
            failed = 1
    return failed


# ---- records ----

def records_dir(a):
    if a.records:
        return os.path.abspath(a.records)
    main = logfiles.checkouts(a.root or ROOT)[0]
    return os.path.join(os.path.dirname(main), RECORDS)


def snapshot_dir(a):
    return os.path.join(records_dir(a), "snapshot-" + (a.date or datetime.date.today().isoformat()))


def copy_into(src, dest):
    os.makedirs(dest, exist_ok=True)
    shutil.copytree(src, dest, dirs_exist_ok=True)


def cmd_project_folder(a):
    print(logfiles.claude_folder(a.path or os.getcwd()))
    return 0


def cmd_snapshot(a):
    projects = logfiles.projects_dir(a.projects)
    folder = a.folder or logfiles.claude_folder(logfiles.checkouts(a.root or ROOT)[0])
    dest = snapshot_dir(a)
    names = sorted(n for n in (os.listdir(projects) if os.path.isdir(projects) else [])
                   if logfiles.fold(n).startswith(logfiles.fold(folder)) and os.path.isdir(os.path.join(projects, n)))
    if not names:
        raise Fail("no folder under %s starts with %s" % (projects, folder))
    for n in names:
        copy_into(os.path.join(projects, n), os.path.join(dest, n))
        print("copied: %s" % n)
    exact = next((n for n in names if logfiles.fold(n) == logfiles.fold(folder)), None)
    has_memory = exact is not None and os.path.isdir(os.path.join(dest, exact, "memory"))
    print("%s memory: %s" % ("PASS" if has_memory else "FAIL", os.path.join(dest, exact or folder, "memory")))
    worktrees = [n for n in names if logfiles.fold(n).startswith(logfiles.fold(folder + "--claude-worktrees-"))]
    print("worktrees: %d folders copied" % len(worktrees))
    print("snapshot: %s" % dest)
    return 0 if has_memory else 1


def cmd_scratchpad(a):
    if not os.path.isdir(a.dir):
        raise Fail("%s is not a folder" % a.dir)
    folder = a.folder or logfiles.claude_folder(os.getcwd())
    dest = os.path.join(snapshot_dir(a), "scratchpads", folder, a.session)
    os.makedirs(dest, exist_ok=True)
    skipped = []

    def copies(where, names):   # a scratch copy of the Log is no note
        out = [n for n in names if os.path.isfile(os.path.join(where, n, META))]
        skipped.extend(os.path.join(where, n) for n in out)
        return out
    shutil.copytree(a.dir, dest, dirs_exist_ok=True, ignore=copies)
    for where in skipped:
        print("skipped: %s (a harness copy)" % where)
    print("copied: %d files to %s" % (sum(len(f) for _, _, f in os.walk(dest)), dest))
    return 0


def cmd_notes(a):
    if not os.path.isdir(a.dir):
        raise Fail("%s is not a folder" % a.dir)
    dest = os.path.join(snapshot_dir(a), "side-session-notes", os.path.basename(os.path.normpath(a.dir)))
    copy_into(a.dir, dest)
    print("copied: %d files to %s" % (sum(len(f) for _, _, f in os.walk(dest)), dest))
    return 0


def cmd_move(a):
    src, dest = os.path.abspath(os.path.join(a.old, RECORDS)), os.path.abspath(os.path.join(a.new, RECORDS))
    if os.path.isdir(dest):
        print("skip: %s is there already" % dest)
    else:
        if not os.path.isdir(src):
            raise Fail("%s is not a folder" % src)
        copy_into(src, dest)
        print("copied: %s -> %s" % (src, dest))
    snaps = sorted(n for n in os.listdir(dest) if n.startswith("snapshot-"))
    print("%s snapshots: %s" % ("PASS" if snaps else "FAIL", ", ".join(snaps) or "none"))
    return 0 if snaps else 1


def cmd_memory(a):
    src = os.path.abspath(os.path.join(a.source, a.old, "memory"))
    if not os.path.isdir(src):
        raise Fail("%s is not a folder" % src)
    checkout = a.new or logfiles.checkouts(a.root or ROOT)[0]
    projects = logfiles.projects_dir(a.projects)
    folder = logfiles.find_project_folder(projects, checkout) or os.path.join(projects, logfiles.claude_folder(checkout))
    dest = os.path.abspath(os.path.join(folder, "memory"))
    copy_into(src, dest)
    ok = os.path.isfile(os.path.join(dest, "MEMORY.md"))
    print("copied: %s -> %s" % (src, dest))
    print("%s index: %s" % ("PASS" if ok else "FAIL", os.path.join(dest, "MEMORY.md")))
    return 0 if ok else 1


# ---- command line ----

def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("copy")
    c.add_argument("t")
    c.add_argument("--worktree")
    c.add_argument("--branch")
    c.add_argument("--default")
    c.set_defaults(fn=cmd_copy)

    c = sub.add_parser("template-copy")
    c.add_argument("t")
    c.add_argument("--worktree")
    c.add_argument("--default")
    c.add_argument("--from", dest="source")
    c.add_argument("--modes-from", nargs=2, metavar=("CLONE", "REF"))
    c.add_argument("--no-config", action="store_true")
    c.add_argument("--no-seed", action="store_true")
    c.set_defaults(fn=cmd_template_copy)

    for name, fn in (("seed", cmd_seed), ("reset", cmd_reset), ("verify", cmd_verify)):
        c = sub.add_parser(name)
        c.add_argument("t")
        c.set_defaults(fn=fn)

    c = sub.add_parser("prompt")
    c.add_argument("t")
    c.add_argument("--run", required=True)
    c.add_argument("--message", required=True)
    c.add_argument("--browser", choices=sorted(BROWSERS), default="fetch")
    c.add_argument("--signed-in")
    c.add_argument("--relay", choices=sorted(RELAYS), default="message")
    c.set_defaults(fn=cmd_prompt)

    c = sub.add_parser("start")
    c.add_argument("t")
    c.add_argument("--runs", required=True)
    c.add_argument("--round", type=int, required=True)
    c.add_argument("--model", choices=sorted(MODELS), required=True)
    c.add_argument("--case", required=True)
    c.set_defaults(fn=cmd_start)

    c = sub.add_parser("process")
    c.add_argument("run")
    c.add_argument("--runs", required=True)
    c.add_argument("--effort", required=True)
    c.add_argument("--idle", type=float, default=240)
    c.set_defaults(fn=cmd_process)

    c = sub.add_parser("say")
    c.add_argument("run")
    c.add_argument("--runs", required=True)
    which = c.add_mutually_exclusive_group(required=True)
    which.add_argument("--message")
    which.add_argument("--end", action="store_true")
    c.set_defaults(fn=cmd_say)

    c = sub.add_parser("collect")
    c.add_argument("run")
    c.add_argument("--runs", required=True)
    c.add_argument("--agent")
    c.set_defaults(fn=cmd_collect)

    c = sub.add_parser("report")
    c.add_argument("round", type=int)
    c.add_argument("--runs", required=True)
    c.set_defaults(fn=cmd_report)

    c = sub.add_parser("signed-in-home")
    c.add_argument("t")
    c.set_defaults(fn=cmd_signed_in_home)

    c = sub.add_parser("remove")
    c.add_argument("t", nargs="+")
    c.set_defaults(fn=cmd_remove)

    rec = sub.add_parser("records").add_subparsers(dest="records_cmd", required=True)

    def records_parser(name, fn):
        r = rec.add_parser(name)
        r.add_argument("--records")
        r.add_argument("--date")
        r.add_argument("--root")
        r.set_defaults(fn=fn)
        return r

    r = records_parser("project-folder", cmd_project_folder)
    r.add_argument("path", nargs="?")
    r = records_parser("snapshot", cmd_snapshot)
    r.add_argument("--folder")
    r.add_argument("--projects")
    r = records_parser("scratchpad", cmd_scratchpad)
    r.add_argument("dir")
    r.add_argument("--session", required=True)
    r.add_argument("--folder")
    r = records_parser("notes", cmd_notes)
    r.add_argument("dir")
    r = records_parser("move", cmd_move)
    r.add_argument("old")
    r.add_argument("new")
    r = records_parser("memory", cmd_memory)
    r.add_argument("source")
    r.add_argument("old")
    r.add_argument("--new")
    r.add_argument("--projects")
    return p


def main(argv=None):
    logfiles.utf8_stdout()
    a = parser().parse_args(argv)
    if getattr(a, "date", None) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.date):
        print("--date takes YYYY-MM-DD", file=sys.stderr)
        return 2
    try:
        return a.fn(a)
    except (Fail, logfiles.LogError) as e:
        print("FAIL: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
