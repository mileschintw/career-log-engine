#!/usr/bin/env python3
"""Tests for maintainer/harness.py: a small repository in a temp folder stands in for the branch's
worktree (the real tools/config.py, a stub export and a stub check_run.py), and every copy, home,
projects folder and records folder is in that temp folder; nothing reaches the real profile.

  python3 -I maintainer/tests/test_harness.py
"""
import importlib.util, io, json, os, shutil, subprocess, sys, tempfile, time, unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, "..", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


harness = load("harness")
sys.path.insert(0, os.path.join(REPO, "tools"))
import chat_export, logfiles  # noqa: E402

EXPORT = """#!/usr/bin/env bash
# stub of the export: the skeleton, with no config.toml
set -e
mkdir -p "$1/tools"
cp tools/config.py tools/config.default.toml tools/logfiles.py "$1/tools/"
echo "# Log" > "$1/README.md"
"""
OLD_CONFIG = """import os, shutil, sys
# stub of 0.1.0's tools/config.py: init copies the defaults; it knows no update_check
root = sys.argv[sys.argv.index("--root") + 1]
if "update_check" in sys.argv:
    sys.exit("update_check is not a Config field")
shutil.copy(os.path.join(root, "tools", "config.default.toml"), os.path.join(root, "config.toml"))
"""
CHECK_RUN = """import sys
if "--agent" in sys.argv:
    print("transcript: /x/agent-" + sys.argv[sys.argv.index("--agent") + 1] + ".jsonl")
else:
    print("transcript: " + sys.argv[sys.argv.index("--transcript") + 1])
print("PASS subagent-model: ok")
print("FAIL call-lines: missing")
print("SKIP map-count: no map")
print("NOTE outside-root: one file")
print("Grade: FAIL (1 FAIL)")
sys.exit(1)
"""

FAKE_CLAUDE = r'''import json, os, sys
# stub of `claude -p` stream-json: one init line, then per user line a result; writes a transcript
# where Claude Code would, and what it saw to <t>/seen.json
cfg = os.environ["CLAUDE_CONFIG_DIR"]
t = os.path.dirname(cfg)
skill = os.path.join(cfg, "skills", "career-log")
with open(os.path.join(t, "seen.json"), "w", encoding="utf-8") as f:
    json.dump({"credentials": os.path.isfile(os.path.join(cfg, ".credentials.json")),
               "skill": os.path.realpath(skill) if os.path.isdir(skill) else None,
               "plugins": os.environ.get("CLAUDE_CODE_PLUGIN_DIRS"), "cwd": os.getcwd(),
               "home": os.environ.get("HOME"), "argv": " ".join(sys.argv[1:]),
               "token": os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")}, f)
refuse = os.environ.get("FAKE_REFUSE")   # "start": ends at once; "pipe": closes stdin first, then ends
if refuse:
    print("Error: --dangerously-skip-permissions cannot be used with root/sudo privileges", file=sys.stderr, flush=True)
    if refuse == "pipe":
        import time
        os.close(0)
        time.sleep(5)   # alive while say writes turn 1, so the write fails, not the poll
    sys.exit(1)
def tasks(items):
    return {"type": "system", "subtype": "background_tasks_changed", "tasks": items}
folder = os.path.join(cfg, "projects", "".join(c if c.isalnum() else "-" for c in os.path.abspath(os.getcwd())))
os.makedirs(os.path.join(folder, "sess-1", "subagents"), exist_ok=True)
open(os.path.join(folder, "sess-1", "subagents", "agent-a1.jsonl"), "w").close()
print(json.dumps({"type": "system", "subtype": "init", "session_id": "sess-1"}), flush=True)
for line in sys.stdin:
    text = json.loads(line)["message"]["content"]
    with open(os.path.join(folder, "sess-1.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"type": "user", "text": text}) + "\n")
    if text.startswith("EXIT"):
        sys.exit(3)
    if text.startswith("LOGIN"):
        print(json.dumps({"type": "result", "subtype": "success", "is_error": True,
                          "result": "Failed to authenticate"}), flush=True)
        continue
    print(json.dumps({"type": "assistant", "text": "working"}), flush=True)
    if text.startswith(("BG", "HANG")):   # a background subagent outlives the turn, as Claude Code 2.1.310 does it
        print(json.dumps(tasks([{"task_id": "a1", "task_type": "local_agent", "description": "reviewer"}])), flush=True)
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "reply to: " + text}),
          flush=True)
    if text.startswith("BG"):
        for _ in range(2000):   # 400 kB more than any pipe holds: unread, it would stop this process here
            print(json.dumps({"type": "system", "subtype": "task_progress", "pad": "x" * 200}), flush=True)
        print(json.dumps(tasks([])), flush=True)
        print(json.dumps({"type": "system", "subtype": "init", "session_id": "sess-1"}), flush=True)
        print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "reviewed"}), flush=True)
    for _ in range(150 if text.startswith("HANG") else 0):   # the subagent never reports, its progress keeps coming
        print(json.dumps({"type": "system", "subtype": "task_progress"}), flush=True)
        import time
        time.sleep(0.1)
    if text.startswith("HANG"):
        sys.exit(0)
    if text.startswith("LATE"):   # a notification starts a turn of the process's own once this one ended
        print(json.dumps({"type": "system", "subtype": "init", "session_id": "sess-1"}), flush=True)
        import time
        time.sleep(2)
        print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "late reply"}), flush=True)
'''


def git(cwd, *args):
    return subprocess.run(["git", "-C", cwd, "-c", "core.autocrlf=false", *args], check=True,
                          capture_output=True, encoding="utf-8").stdout.strip()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = harness.main(list(argv))
    return rc, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(logfiles.rmtree, self.tmp)
        self.wt = os.path.join(self.tmp, "wt")
        os.makedirs(self.wt)
        git(self.wt, "init", "-q", "-b", "feature")
        logfiles.no_maintenance(self.wt)   # a commit starts git's maintenance too: none left running at tearDown
        git(self.wt, "config", "user.email", "test@example.com")
        git(self.wt, "config", "user.name", "Test")
        os.makedirs(os.path.join(self.wt, "tools"))
        for name in ("config.py", "config.default.toml", "logfiles.py"):
            shutil.copy(os.path.join(REPO, "tools", name), os.path.join(self.wt, "tools", name))
        shutil.copy(os.path.join(REPO, "tools", "config.default.toml"), os.path.join(self.wt, "config.toml"))
        write(os.path.join(self.wt, "tools", "export-template.sh"), EXPORT)
        write(os.path.join(self.wt, "tools", "check_run.py"), CHECK_RUN)
        write(os.path.join(self.wt, ".gitignore"), ".build/\n")
        git(self.wt, "add", "-A")
        git(self.wt, "commit", "-qm", "engine")
        self.t = os.path.join(self.tmp, "t")
        self.log = os.path.join(self.t, "log")

    def copy(self, *extra):
        return run("copy", self.t, "--worktree", self.wt, "--default", "master", *extra)

    def config_off(self):
        return 'update_check = "off"' in git(self.log, "show", "HEAD:config.toml")


class TestCopy(Base):
    def test_copy_builds_a_checked_copy(self):
        rc, out, err = self.copy()
        self.assertEqual(rc, 0, out + err)
        self.assertNotIn("FAIL", out)
        self.assertTrue(self.config_off())
        self.assertEqual(git(self.log, "log", "-1", "--format=%s"), harness.CONFIG_COMMIT)
        self.assertEqual(git(self.log, "rev-parse", "HEAD^"), git(self.wt, "rev-parse", "HEAD"))
        self.assertEqual(git(self.log, "branch", "--show-current"), "master")
        self.assertEqual(git(self.log, "config", "user.email"), "test@example.invalid")
        self.assertEqual(git(os.path.join(self.t, "remote.git"), "rev-parse", "master"), git(self.log, "rev-parse", "HEAD"))
        for sub in ("Roaming", "Local"):
            self.assertTrue(os.path.isdir(os.path.join(self.t, "home", "AppData", sub)))
        self.assertIn("start: " + git(self.log, "rev-parse", "--short", "HEAD"), out)

    def test_update_check_already_off_adds_no_commit(self):
        path = os.path.join(self.wt, "config.toml")
        write(path, read(path).replace('update_check = "on"', 'update_check = "off"'))
        git(self.wt, "commit", "-qam", "off")
        rc, out, _ = self.copy()
        self.assertEqual(rc, 0, out)
        self.assertEqual(git(self.log, "rev-parse", "HEAD"), git(self.wt, "rev-parse", "HEAD"))

    def test_copy_without_config_toml_writes_one(self):
        git(self.wt, "rm", "-q", "config.toml")
        git(self.wt, "commit", "-qm", "no config")
        rc, out, _ = self.copy()
        self.assertEqual(rc, 0, out)
        self.assertTrue(self.config_off())

    def test_tools_run_with_the_scratch_home(self):
        env = harness.scratch_env(self.t)
        home = os.path.join(self.t, "home")
        self.assertEqual(env["HOME"], home)
        self.assertEqual(env["USERPROFILE"], home)
        self.assertEqual(env["APPDATA"], os.path.join(home, "AppData", "Roaming"))
        self.assertEqual(env["LOCALAPPDATA"], os.path.join(home, "AppData", "Local"))
        seen = []
        real = harness.run

        def spy(cmd, cwd=None, env=None, check=True):
            if any(str(c).endswith("config.py") for c in cmd):
                seen.append(env)
            return real(cmd, cwd=cwd, env=env, check=check)
        with mock.patch.object(harness, "run", spy):
            rc, out, _ = self.copy()
        self.assertEqual(rc, 0, out)
        self.assertTrue(seen)
        for e in seen:
            for k in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA"):
                self.assertTrue(e[k].startswith(home), (k, e[k]))

    def test_refuses_uncommitted_changes(self):
        write(os.path.join(self.wt, "config.toml"), "x = 1\n")
        rc, _, err = self.copy()
        self.assertEqual(rc, 1)
        self.assertIn("uncommitted", err)
        self.assertFalse(os.path.exists(self.t))

    def test_refuses_a_folder_that_is_not_empty(self):
        write(os.path.join(self.t, "x"), "x")
        rc, _, err = self.copy()
        self.assertEqual(rc, 1)
        self.assertIn("not empty", err)

    def test_says_the_copy_holds_no_log_data(self):
        """#29: this repo holds no Log, so the copy is the Engine only, and says so."""
        rc, out, _ = self.copy()
        self.assertEqual(rc, 0, out)
        self.assertIn("note: %s holds no Log data" % self.log, out)
        self.assertIn("template-copy", out)

    def test_refuses_a_branch_that_holds_log_data(self):
        """#29: copy never takes a real record; a case that reads the Log takes template-copy and fixtures."""
        for path in ("profile.md", "entries/2026-01-01-x.md", "outputs/x.md"):
            with self.subTest(path=path):
                write(os.path.join(self.wt, path), "x\n")
                git(self.wt, "add", path)
                git(self.wt, "commit", "-qm", "data")
                rc, _, err = self.copy()
                self.assertEqual(rc, 1)
                self.assertIn(path, err)
                self.assertIn("template-copy", err)
                self.assertFalse(os.path.exists(self.t))
                git(self.wt, "rm", "-q", path)
                git(self.wt, "commit", "-qm", "no data")

    def test_takes_the_entry_template(self):
        """entries/_template.md is the Engine's, not Log data."""
        write(os.path.join(self.wt, "entries", "_template.md"), "x\n")
        git(self.wt, "add", "entries/_template.md")
        git(self.wt, "commit", "-qm", "template")
        rc, out, _ = self.copy()
        self.assertEqual(rc, 0, out)


class TestReset(Base):
    def test_reset_cleans_the_last_run_and_takes_the_new_head(self):
        self.assertEqual(self.copy()[0], 0)
        git(self.log, "checkout", "-qb", "run-branch")
        write(os.path.join(self.log, "entry.md"), "x\n")
        git(self.log, "add", "entry.md")
        git(self.log, "commit", "-qm", "save")
        git(self.log, "push", "-q", "origin", "run-branch")
        git(self.log, "checkout", "-q", "master")
        write(os.path.join(self.log, "saved.md"), "x\n")
        git(self.log, "add", "saved.md")
        git(self.log, "commit", "-qm", "save on master")
        git(self.log, "push", "-q", "origin", "master")
        git(self.log, "worktree", "add", "-q", os.path.join(self.t, "wt2"), "-b", "wt-branch")
        write(os.path.join(self.log, ".build", "draft.md"), "x\n")
        rc, out, _ = run("verify", self.t)
        self.assertEqual(rc, 1)
        for check in ("head", "branches", "worktrees", "clean"):
            self.assertIn("FAIL %s:" % check, out)

        write(os.path.join(self.wt, "fix.md"), "fix\n")
        git(self.wt, "add", "fix.md")
        git(self.wt, "commit", "-qm", "fix")
        rc, out, err = run("reset", self.t)
        self.assertEqual(rc, 0, out + err)
        self.assertNotIn("FAIL", out)
        self.assertEqual(git(self.log, "rev-parse", "HEAD^"), git(self.wt, "rev-parse", "HEAD"))
        self.assertFalse(os.path.exists(os.path.join(self.log, "saved.md")))
        self.assertFalse(os.path.exists(os.path.join(self.log, ".build")))
        self.assertEqual(git(os.path.join(self.t, "remote.git"), "branch", "--format=%(refname:short)"), "master")
        self.assertTrue(self.config_off())

    def test_refuses_a_folder_it_did_not_build(self):
        os.makedirs(self.t)
        rc, _, err = run("reset", self.t)
        self.assertEqual(rc, 1)
        self.assertIn("harness.json", err)

    def test_refuses_a_copy_whose_origin_moved(self):
        self.assertEqual(self.copy()[0], 0)
        git(self.log, "remote", "set-url", "origin", self.wt)
        rc, _, err = run("reset", self.t)
        self.assertEqual(rc, 1)
        self.assertIn("refusing", err)

    def test_refuses_a_branch_that_now_holds_log_data(self):
        self.assertEqual(self.copy()[0], 0)
        head = git(self.log, "rev-parse", "HEAD")
        write(os.path.join(self.wt, "direction.md"), "x\n")
        git(self.wt, "add", "direction.md")
        git(self.wt, "commit", "-qm", "data")
        rc, _, err = run("reset", self.t)
        self.assertEqual(rc, 1)
        self.assertIn("direction.md", err)
        self.assertEqual(git(os.path.join(self.t, "remote.git"), "rev-parse", "master"), head)


@unittest.skipUnless(shutil.which("bash"), "bash not on PATH")
class TestTemplateCopy(Base):
    def test_template_copy_seeds_a_new_log(self):
        rc, out, err = run("template-copy", self.t, "--worktree", self.wt, "--default", "master")
        self.assertEqual(rc, 0, out + err)
        self.assertNotIn("FAIL", out)
        self.assertEqual(git(self.log, "log", "--format=%s"), "seed")
        self.assertTrue(self.config_off())
        self.assertTrue(os.path.isdir(os.path.join(self.t, "home", "AppData", "Local")))
        rc, _, err = run("reset", self.t)
        self.assertEqual(rc, 1)
        self.assertIn("not reset", err)

    def test_seed_takes_the_heads_modes(self):
        """#535: core.fileMode false (Windows) stages the export's files 100644; the head has 100755."""
        write(os.path.join(self.wt, "tools", "setup.sh"), "#!/bin/sh\n")
        write(os.path.join(self.wt, "tools", "template", "start.sh"), "#!/bin/sh\n")
        write(os.path.join(self.wt, "tools", "export-template.sh"), EXPORT + (
            'cp tools/setup.sh tools/export-template.sh "$1/tools/"\n'
            'mkdir -p "$1/tools/template" && cp tools/template/start.sh "$1/tools/template/" && cp tools/template/start.sh "$1/"\n'))
        git(self.wt, "add", "-A")
        git(self.wt, "update-index", "--chmod=+x", "tools/setup.sh", "tools/export-template.sh", "tools/template/start.sh")
        git(self.wt, "commit", "-qm", "scripts")
        env = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.fileMode", "GIT_CONFIG_VALUE_0": "false"}
        with mock.patch.dict(os.environ, env):
            rc, out, err = run("template-copy", self.t, "--worktree", self.wt, "--default", "master")
        self.assertEqual(rc, 0, out + err)
        modes = {l.split("\t")[1]: l.split()[0] for l in git(self.log, "ls-tree", "-r", "HEAD").splitlines()}
        for path in ("tools/setup.sh", "tools/export-template.sh", "tools/template/start.sh", "start.sh"):
            self.assertEqual(modes[path], "100755", path)
        self.assertEqual(modes["README.md"], "100644")
        self.assertEqual(modes["config.toml"], "100644")

    def test_no_config_no_seed_then_seed(self):
        rc, out, err = run("template-copy", self.t, "--worktree", self.wt, "--default", "master",
                           "--no-config", "--no-seed")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("harness.py seed", out)
        self.assertEqual(run("verify", self.t)[0], 1)
        write(os.path.join(self.log, "edit.md"), "the expected sheet's edit\n")
        rc, out, err = run("seed", self.t)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("PASS config: config.toml absent", out)
        self.assertIn("edit.md", git(self.log, "ls-files"))


class TestTemplateFrom(Base):
    def test_from_takes_a_tree_in_place_of_the_export(self):
        tree = os.path.join(self.tmp, "release")
        os.makedirs(os.path.join(tree, "tools"))
        for name in ("config.py", "config.default.toml", "logfiles.py"):
            shutil.copy(os.path.join(REPO, "tools", name), os.path.join(tree, "tools", name))
        write(os.path.join(tree, "README.md"), "# an older release\n")
        rc, out, err = run("template-copy", self.t, "--worktree", self.wt, "--default", "master", "--from", tree)
        self.assertEqual(rc, 0, out + err)
        self.assertNotIn("FAIL", out)
        self.assertEqual(read(os.path.join(self.log, "README.md")), "# an older release\n")
        self.assertNotIn("check_run.py", git(self.log, "ls-files"))
        self.assertTrue(self.config_off())

    def test_from_a_release_before_update_check(self):
        tree = os.path.join(self.tmp, "release")
        default = read(os.path.join(REPO, "tools", "config.default.toml"))
        write(os.path.join(tree, "tools", "config.default.toml"),
              "\n".join(line for line in default.splitlines() if "update_check" not in line) + "\n")
        write(os.path.join(tree, "tools", "config.py"), OLD_CONFIG)
        rc, out, err = run("template-copy", self.t, "--worktree", self.wt, "--default", "master", "--from", tree)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("PASS config: HEAD:config.toml is there (this release has no update_check)", out)
        self.assertNotIn("FAIL", out)

    def release(self):
        """A clone tagged v1 whose tools/setup.sh is 100755, and its files in a folder with no executable bit."""
        clone, tree = os.path.join(self.tmp, "clone"), os.path.join(self.tmp, "release")
        files = {"README.md": "# a release\n", "tools/setup.sh": "#!/bin/sh\n"}
        for name in ("config.py", "config.default.toml", "logfiles.py"):
            files["tools/" + name] = read(os.path.join(REPO, "tools", name))
        for root in (clone, tree):
            for path, text in files.items():
                write(os.path.join(root, path), text)
        git(clone, "init", "-q")
        git(clone, "add", "-A")
        git(clone, "update-index", "--chmod=+x", "tools/setup.sh")
        git(clone, "-c", "user.name=T", "-c", "user.email=t@example.invalid", "commit", "-qm", "v1")
        git(clone, "tag", "v1")
        return clone, tree

    def test_modes_from_gives_the_seed_the_releases_modes(self):
        """#534: core.fileMode false (Windows) stages the folder's files 100644; the release has 100755."""
        clone, tree = self.release()
        argv = ("template-copy", self.t, "--worktree", self.wt, "--default", "master", "--from", tree)
        env = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.fileMode", "GIT_CONFIG_VALUE_0": "false"}
        with mock.patch.dict(os.environ, env):
            rc, out, err = run(*argv, "--modes-from", clone, "v1", "--no-seed")
            self.assertEqual(rc, 0, out + err)
            write(os.path.join(self.log, "tools", "added.sh"), "#!/bin/sh\n")   # an expected sheet's edit
            rc, out, err = run("seed", self.t)
        self.assertEqual(rc, 0, out + err)
        modes = {l.split("\t")[1]: l.split()[0] for l in git(self.log, "ls-tree", "-r", "HEAD").splitlines()}
        self.assertEqual(modes["tools/setup.sh"], "100755")
        self.assertEqual(modes["README.md"], "100644")
        self.assertEqual(modes["tools/added.sh"], "100644")
        logfiles.rmtree(self.t)
        with mock.patch.dict(os.environ, env):
            rc, out, err = run(*argv)   # without it, as before
        self.assertEqual(rc, 0, out + err)
        self.assertIn("100644 ", git(self.log, "ls-files", "-s", "tools/setup.sh"))

    def test_modes_from_refuses_a_ref_that_is_not_the_folder(self):
        clone, tree = self.release()
        write(os.path.join(tree, "extra.md"), "not in v1\n")
        rc, _, err = run("template-copy", self.t, "--worktree", self.wt, "--default", "master", "--from", tree,
                         "--modes-from", clone, "v1")
        self.assertEqual(rc, 1)
        self.assertIn("does not hold the files of --from (extra.md)", err)
        logfiles.rmtree(self.t)
        rc, _, err = run("template-copy", self.t, "--worktree", self.wt, "--default", "master",
                         "--from", tree, "--modes-from", clone, "v9")
        self.assertEqual(rc, 1)
        self.assertIn("--modes-from: no v9 in", err)
        logfiles.rmtree(self.t)
        rc, _, err = run("template-copy", self.t, "--worktree", self.wt, "--default", "master",
                         "--modes-from", clone, "v1")
        self.assertEqual(rc, 1)
        self.assertIn("--modes-from goes with --from", err)
        self.assertFalse(os.path.exists(self.t))

    def test_a_failed_build_can_be_removed(self):
        rc, _, err = run("template-copy", self.t, "--worktree", self.wt, "--default", "master",
                         "--from", os.path.join(self.tmp, "missing"))
        self.assertEqual(rc, 1)
        rc, out, _ = run("verify", self.t)
        self.assertIn("FAIL build:", out)
        self.assertEqual(run("remove", self.t)[0], 0)
        self.assertFalse(os.path.exists(self.t))


class TestRuns(Base):
    def setUp(self):
        super().setUp()
        self.assertEqual(self.copy()[0], 0)
        self.runs = os.path.join(self.tmp, "runs.jsonl")
        self.home = os.path.join(self.tmp, "realhome")
        self.machine = os.path.join(self.home, ".career-log", "machine.toml")
        write(self.machine, "a = 1\n")
        patch = mock.patch.dict(os.environ, {"HOME": self.home, "USERPROFILE": self.home})
        patch.start()
        self.addCleanup(patch.stop)

    def test_prompt_holds_the_real_profile_lines(self):
        msg = os.path.join(self.tmp, "msg.txt")
        write(msg, "Log this:\n  a milestone | with a pipe\n")
        rc, out, _ = run("prompt", self.t, "--run", "v1s-1", "--message", msg)
        self.assertEqual(rc, 0)
        self.assertIn("(drafts in .build/v1s-1/)", out)
        t = os.path.abspath(self.t).replace("\\", "/")
        self.assertIn("The Log root is %s/log." % t, out)
        self.assertIn(harness.SIGN_IN, out)
        lines = out.splitlines()
        for start in ("- Never run setup", "- Start every shell command", "- Copy the two lines above"):
            self.assertTrue(any(line.startswith(start) for line in lines), start)
        self.assertIn("export HOME=%s/home USERPROFILE=%s/home APPDATA=%s/home/AppData/Roaming" % (t, t, t), out)
        self.assertNotIn("\\", out.split("User message:")[0])
        self.assertTrue(out.rstrip("\n").endswith("User message:\nLog this:\n  a milestone | with a pipe"))
        self.assertIn(harness.BROWSERS["fetch"], out)

    def test_prompt_browser_and_signed_in(self):
        msg, line = os.path.join(self.tmp, "msg.txt"), os.path.join(self.tmp, "line.txt")
        write(msg, "hi\n")
        write(line, "- Read the sites the test plan lists, signed in through p.\n")
        rc, out, _ = run("prompt", self.t, "--run", "v1s-1", "--message", msg, "--browser", "playwright",
                         "--signed-in", line)
        self.assertEqual(rc, 0)
        self.assertNotIn(harness.SIGN_IN, out)
        self.assertIn("- Read the sites the test plan lists, signed in through p.", out)
        self.assertIn(harness.BROWSERS["playwright"], out)

    def test_start_collect_report(self):
        rc, out, _ = run("start", self.t, "--runs", self.runs, "--round", "1", "--model", "s", "--case", "log a | milestone")
        self.assertEqual(rc, 0, out)
        self.assertIn("run: v1s-1", out)
        self.assertIn("machine.toml: " + harness.file_hash(self.machine), out)
        rc, out, _ = run("start", self.t, "--runs", self.runs, "--round", "1", "--model", "s", "--case", "second")
        self.assertIn("run: v1s-2", out)
        row = json.loads(read(self.runs).splitlines()[0])
        self.assertEqual(row["head"], git(self.wt, "rev-parse", "--short=7", "HEAD"))
        self.assertEqual(row["start"], git(self.log, "rev-parse", "--short", "HEAD"))
        self.assertEqual(row["model"], "sonnet")

        rc, out, _ = run("collect", "v1s-1", "--runs", self.runs, "--agent", "abc")
        self.assertEqual(rc, 1)
        self.assertIn("transcript: /x/agent-abc.jsonl", out)
        self.assertIn("PASS machine-toml: unchanged", out)
        write(self.machine, "a = 2\n")
        rc, out, _ = run("collect", "v1s-2", "--runs", self.runs, "--agent", "def")
        self.assertIn("FAIL machine-toml:", out)
        row = json.loads(read(self.runs).splitlines()[0])
        self.assertEqual(row["agent"], "abc")
        self.assertEqual(row["check_run_exit"], 1)

        rc, out, _ = run("report", "1", "--runs", self.runs)
        self.assertEqual(rc, 0)
        self.assertIn("| v1s-1 | mechanical | log a \\| milestone | FAIL (1 FAIL) | check_run.py; machine.toml unchanged |", out)
        self.assertIn("subagent-model: 2/2", out)
        self.assertIn("call-lines: 0/2", out)
        self.assertIn("outside-root: 2/2", out)
        self.assertNotIn("map-count", out)

    def test_machine_toml_absent_both_times_is_unchanged(self):
        os.remove(self.machine)
        run("start", self.t, "--runs", self.runs, "--round", "2", "--model", "o", "--case", "c")
        _, out, _ = run("collect", "v2o-1", "--runs", self.runs, "--agent", "x")
        self.assertIn("PASS machine-toml: unchanged", out)

    def test_start_refuses_a_copy_behind_the_branch(self):
        write(os.path.join(self.wt, "fix.md"), "fix\n")
        git(self.wt, "add", "fix.md")
        git(self.wt, "commit", "-qm", "fix")
        rc, _, err = run("start", self.t, "--runs", self.runs, "--round", "1", "--model", "s", "--case", "c")
        self.assertEqual(rc, 1)
        self.assertIn("harness.py reset", err)
        self.assertEqual(run("reset", self.t)[0], 0)
        rc, out, _ = run("start", self.t, "--runs", self.runs, "--round", "1", "--model", "s", "--case", "c")
        self.assertEqual(rc, 0, out)
        self.assertEqual(json.loads(read(self.runs))["head"], git(self.wt, "rev-parse", "--short=7", "HEAD"))
        self.assertEqual(out.count("start: "), 1)

    def test_start_refuses_a_copy_not_reset(self):
        write(os.path.join(self.log, ".build", "d.md"), "x\n")
        rc, out, err = run("start", self.t, "--runs", self.runs, "--round", "1", "--model", "s", "--case", "c")
        self.assertEqual(rc, 1)
        self.assertIn("FAIL clean:", out)
        self.assertIn("harness.py reset", err)
        self.assertFalse(os.path.exists(self.runs))


class TestProcess(Base):
    """A process run against a fake claude: the config folder, the turns, the transcript, the credentials."""

    def setUp(self):
        super().setUp()
        write(os.path.join(self.wt, "skills", "career-log", "SKILL.md"), "# skill\n")
        git(self.wt, "add", "-A")
        git(self.wt, "commit", "-qm", "skill")
        self.assertEqual(self.copy()[0], 0)
        self.runs = os.path.join(self.tmp, "runs.jsonl")
        self.real = os.path.join(self.tmp, "realcfg")
        write(os.path.join(self.real, harness.CREDENTIALS), '{"token": "x"}\n')
        self.fake = os.path.join(self.tmp, "fake_claude.py")
        write(self.fake, FAKE_CLAUDE)
        home = os.path.join(self.tmp, "realhome")
        patch = mock.patch.dict(os.environ, {"HOME": home, "USERPROFILE": home, "CLAUDE_CONFIG_DIR": self.real,
                                             "HARNESS_CLAUDE": self.fake, "CLAUDE_CODE_PLUGIN_DIRS": "/tester/plugins",
                                             "CLAUDE_CODE_OAUTH_TOKEN": "tok"})
        patch.start()
        self.addCleanup(patch.stop)
        self.assertEqual(run("start", self.t, "--runs", self.runs, "--round", "1", "--model", "h", "--case", "c")[0], 0)

    def process(self, *extra):
        p = subprocess.Popen([sys.executable, "-I", os.path.join(REPO, "maintainer", "harness.py"), "process", "v1h-1",
                              "--runs", self.runs, "--effort", "medium", *extra],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
        self.addCleanup(lambda: p.poll() is None and p.kill())
        return p

    def say(self, text):
        msg = os.path.join(self.tmp, "say.txt")
        write(msg, text)
        return run("say", "v1h-1", "--runs", self.runs, "--message", msg)

    def test_turns_transcript_and_credentials(self):
        p = self.process()
        rc, out, _ = self.say("first turn")
        self.assertEqual(rc, 0, out)
        self.assertIn("turn 1: success\nreply to: first turn", out)
        seen = json.loads(read(os.path.join(self.t, "seen.json")))
        self.assertFalse(seen["credentials"])   # #544: the token, not a copy of the real login
        self.assertEqual(seen["token"], "tok")
        self.assertEqual(read(os.path.join(self.real, harness.CREDENTIALS)), '{"token": "x"}\n')
        self.assertTrue(os.path.samefile(seen["skill"], os.path.join(self.log, "skills", "career-log")))
        self.assertFalse(seen["plugins"])
        self.assertTrue(os.path.samefile(seen["cwd"], self.log))   # #766: macOS gives /private/var for /var
        self.assertTrue(seen["home"].replace("\\", "/").endswith("/t/home"))
        self.assertIn("--model haiku --effort medium", seen["argv"])
        rc, out, _ = self.say("User: yes")
        self.assertIn("turn 2: success\nreply to: User: yes", out)
        rc, _, err = run("collect", "v1h-1", "--runs", self.runs)
        self.assertEqual(rc, 1)
        self.assertIn("still running", err)
        self.assertEqual(run("say", "v1h-1", "--runs", self.runs, "--end")[0], 0)
        p.wait(timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr.read())
        self.assertFalse(os.path.exists(os.path.join(self.t, "config", harness.CREDENTIALS)))
        self.assertTrue(os.path.isfile(os.path.join(self.real, harness.CREDENTIALS)))
        row = json.loads(read(self.runs))
        self.assertEqual(row["session"], "sess-1")
        self.assertTrue(row["process"])
        self.assertTrue(os.path.isfile(row["transcript"]))
        self.assertIn("/t/config/projects/", row["transcript"])

        rc, out, _ = run("collect", "v1h-1", "--runs", self.runs)
        self.assertEqual(rc, 1)   # the stub check_run.py exits 1
        self.assertIn("transcript: " + row["transcript"], out)
        self.assertIn("PASS credentials: deleted", out)
        kept = os.path.join(self.tmp, "transcripts", "v1h-1")
        self.assertTrue(os.path.isfile(os.path.join(kept, "sess-1.jsonl")))
        self.assertTrue(os.path.isfile(os.path.join(kept, "sess-1", "subagents", "agent-a1.jsonl")))
        self.assertEqual(json.loads(read(self.runs))["agent"], "sess-1")

    def test_a_turn_waits_for_its_background_subagent(self):
        p = self.process()
        rc, out, _ = self.say("BG review")
        self.assertEqual(rc, 0, out)
        self.assertIn("turn 1: success\nreply to: BG review\n\n---\n\nreviewed", out)
        events = read(os.path.join(self.t, "process", "events.log"))
        self.assertIn("TURN 1 SENT\nTURN 1 WAITING reviewer\nTURN 1 DONE success\n", events)
        self.assertIn("reply to: User: yes", self.say("User: yes")[1])
        run("say", "v1h-1", "--runs", self.runs, "--end")
        p.wait(timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr.read())

    def test_a_late_turn_joins_the_last_turn_and_the_next_waits(self):
        p = self.process()
        self.assertIn("turn 1: success\nreply to: LATE", self.say("LATE")[1])
        rc, out, _ = self.say("User: next")
        self.assertIn("note: turn 1 got a message after its say exited: ", out)
        self.assertIn("turn 2: success\nreply to: User: next", out)
        events = read(os.path.join(self.t, "process", "events.log"))
        self.assertIn("TURN 1 DONE success\nTURN 1 LATE success\nTURN 2 SENT\n", events)
        self.assertEqual(read(os.path.join(self.t, "process", "out", "1.txt")), "reply to: LATE\n\n---\n\nlate reply")
        run("say", "v1h-1", "--runs", self.runs, "--end")
        p.wait(timeout=60)

    def test_end_stops_a_turn_that_waits_forever(self):
        p = self.process()
        msg = os.path.join(self.tmp, "say.txt")
        write(msg, "HANG")
        say = subprocess.Popen([sys.executable, "-I", os.path.join(REPO, "maintainer", "harness.py"), "say", "v1h-1",
                                "--runs", self.runs, "--message", msg], stdout=subprocess.PIPE, encoding="utf-8")
        self.addCleanup(lambda: say.poll() is None and say.kill())
        events = os.path.join(self.t, "process", "events.log")
        for _ in range(60):
            if os.path.isfile(events) and "TURN 1 WAITING reviewer" in read(events):
                break
            time.sleep(0.5)
        self.assertEqual(run("say", "v1h-1", "--runs", self.runs, "--end")[0], 0)
        p.wait(timeout=60)
        out = say.communicate(timeout=60)[0]
        self.assertEqual(say.returncode, 1)
        self.assertIn("turn 1: the process ended first", out)
        self.assertNotIn("PROCESS EXITED", read(events))   # END stopped it, not the fake's own end
        self.assertIn("credentials: deleted\nENDED\n", read(events))

    def test_a_missing_out_folder_is_made_again(self):
        p = self.process()
        self.assertEqual(self.say("hi")[0], 0)
        logfiles.rmtree(os.path.join(self.t, "process", "out"))   # #513's v2s-3: out/ was gone when its turn ended
        rc, out, _ = self.say("User: again")
        self.assertEqual(rc, 0, out)
        self.assertIn("reply to: User: again", out)
        run("say", "v1h-1", "--runs", self.runs, "--end")
        p.wait(timeout=60)

    def test_a_harness_error_is_named_and_stops_the_process(self):
        p = self.process()
        self.assertEqual(self.say("hi")[0], 0)
        logfiles.rmtree(os.path.join(self.t, "process", "out"))
        write(os.path.join(self.t, "process", "out"), "")   # a file where the folder goes
        rc, out, _ = self.say("User: again")
        self.assertEqual(rc, 1)
        self.assertIn("turn 2: harness.py process failed, and the process with it: FileExistsError", out)
        p.wait(timeout=60)
        events = read(os.path.join(self.t, "process", "events.log"))
        self.assertIn("credentials: deleted\nENDED\n", events)
        self.assertFalse(os.path.exists(os.path.join(self.t, "config", harness.CREDENTIALS)))

    def left_credentials(self):
        """A credentials file in <t>/config, as if the process had written one."""
        write(os.path.join(self.t, "config", harness.CREDENTIALS), "x\n")

    def test_credentials_go_when_the_process_dies(self):
        self.left_credentials()
        p = self.process()
        rc, out, _ = self.say("EXIT now")
        self.assertEqual(rc, 1)
        self.assertIn("the process ended first", out)
        p.wait(timeout=60)
        self.assertFalse(os.path.exists(os.path.join(self.t, "config", harness.CREDENTIALS)))
        self.assertIn("credentials: deleted\nENDED\n", read(os.path.join(self.t, "process", "events.log")))

    def test_a_killed_process_counts_as_ended_and_collect_deletes_its_credentials(self):
        self.left_credentials()
        p = self.process()
        self.assertEqual(self.say("hi")[0], 0)
        p.kill()
        p.wait(timeout=60)
        for _ in range(60):   # the fake claude ends once its stdin closes
            if harness.ended(self.t):
                break
            time.sleep(0.5)
        self.assertTrue(os.path.exists(os.path.join(self.t, "config", harness.CREDENTIALS)))
        rc, out, _ = run("collect", "v1h-1", "--runs", self.runs)
        self.assertIn("NOTE credentials: the process left", out)
        self.assertFalse(os.path.exists(os.path.join(self.t, "config", harness.CREDENTIALS)))
        rc, _, err = run("collect", "v1h-1", "--runs", self.runs, "--agent", "x")
        self.assertIn("without --agent", err)

    @unittest.skipIf(os.name == "nt", "a symlink needs extra rights on Windows")
    def test_the_transcript_of_a_log_under_a_symlink_is_found_by_its_real_path(self):
        # #766: macOS's /var is /private/var, and Claude Code names the folder from the resolved path
        real = os.path.join(self.tmp, "real")
        os.makedirs(os.path.join(real, "log"))
        link = os.path.join(self.tmp, "link")
        os.symlink(real, link)
        folder = os.path.join(link, "config", "projects", logfiles.claude_folder(os.path.realpath(os.path.join(real, "log"))))
        write(os.path.join(folder, "s.jsonl"), "")
        self.assertTrue(os.path.isfile(harness.transcript_of(link, "s")))

    @unittest.skipIf(os.name == "nt", "Windows has no zombies: alive() asks for the exit code there")
    def test_a_killed_child_not_yet_reaped_is_not_alive(self):
        # #767: a container with no reaping init keeps a killed process as a zombie
        p = subprocess.Popen([sys.executable, "-I", "-c", "import time; time.sleep(60)"])
        self.addCleanup(p.wait)
        self.assertTrue(harness.alive(p.pid))
        p.kill()
        for _ in range(100):   # no wait(): the child stays a zombie of this test
            if harness.unreaped_or_gone(p.pid):
                break
            time.sleep(0.1)
        self.assertFalse(harness.alive(p.pid))

    def test_a_process_that_ends_at_once_prints_its_error(self):
        with mock.patch.dict(os.environ, {"FAKE_REFUSE": "start"}):
            p = self.process()
            out, _ = p.communicate(timeout=60)
        self.assertEqual(p.returncode, 1)
        self.assertIn("process exited (code 1)\n  Error: --dangerously-skip-permissions cannot be used", out)
        self.assertIn("ended: no session started", out)
        events = read(os.path.join(self.t, "process", "events.log"))
        self.assertIn("TURN 1 PROCESS EXITED\ncredentials: deleted\nENDED\n", events)
        rc, _, err = self.say("hi")
        self.assertEqual(rc, 1)
        self.assertIn("has ended\n  Error: --dangerously-skip-permissions", err)
        rc, out, err = run("collect", "v1h-1", "--runs", self.runs)   # #540 (4): no "transcript None"
        self.assertEqual(rc, 1)
        self.assertIn("PASS credentials: deleted", out)
        self.assertIn("v1h-1 started no session: the process recorded no transcript", err)
        self.assertNotIn("None", err)

    def test_a_broken_pipe_prints_the_error_not_a_traceback(self):
        with mock.patch.dict(os.environ, {"FAKE_REFUSE": "pipe"}):
            p = self.process()
            rc, out, _ = self.say("hi")
            perr = p.communicate(timeout=60)[1]
        self.assertEqual(rc, 1)
        self.assertIn("turn 1: the process ended first", out)
        self.assertIn("\n  Error: --dangerously-skip-permissions", out)
        self.assertEqual(p.returncode, 1)
        self.assertNotIn("Traceback", perr)
        self.assertNotIn("TURN 1 SENT", read(os.path.join(self.t, "process", "events.log")))   # the write failed

    def test_rows_written_meanwhile_are_kept(self):
        p = self.process()
        self.assertEqual(self.say("hi")[0], 0)
        with open(self.runs, "a", encoding="utf-8") as f:   # another run's start or collect meanwhile
            f.write(json.dumps({"name": "v1h-9", "round": 1}) + "\n")
        run("say", "v1h-1", "--runs", self.runs, "--end")
        p.wait(timeout=60)
        names = [json.loads(line)["name"] for line in read(self.runs).splitlines()]
        self.assertEqual(names, ["v1h-1", "v1h-9"])

    def test_a_failed_login_ends_the_turn_in_error(self):
        p = self.process()
        rc, out, _ = self.say("LOGIN fails")
        self.assertEqual(rc, 1)
        self.assertIn("turn 1: error\nFailed to authenticate", out)
        run("say", "v1h-1", "--runs", self.runs, "--end")
        p.wait(timeout=60)

    def test_no_token_refuses_though_a_credentials_file_is_there(self):
        self.assertTrue(os.path.isfile(os.path.join(self.real, harness.CREDENTIALS)))
        with mock.patch.dict(os.environ):
            for k in harness.TOKEN_VARS:
                os.environ.pop(k, None)
            p = self.process()
            p.wait(timeout=60)
        self.assertEqual(p.returncode, 1)
        self.assertIn("the login file is not copied", p.stderr.read())
        self.assertIn("ENDED", read(os.path.join(self.t, "process", "events.log")))
        self.assertFalse(os.path.exists(os.path.join(self.t, "config", harness.CREDENTIALS)))

    def test_prompt_relay_turn(self):
        msg = os.path.join(self.tmp, "msg.txt")
        write(msg, "hi\n")
        _, out, _ = run("prompt", self.t, "--run", "v1h-1", "--message", msg, "--relay", "turn")
        self.assertIn("relays the user's replies to you as your next user message: a message that starts `User:`", out)
        self.assertNotIn("SendMessage", out)
        self.assertNotIn("in the foreground", out)
        self.assertIn("word for word.\n- When you ask", out)
        _, out, _ = run("prompt", self.t, "--run", "v1h-1", "--message", msg)
        self.assertIn("relays the user's replies to you with SendMessage", out)
        self.assertIn("word for word.\n- Run every subagent you start in the foreground", out)

    def test_prompt_outside_rules_subagent_run_only(self):
        # a subagent run sits in the tester's session, with their memory in context (#604)
        msg = os.path.join(self.tmp, "msg.txt")
        write(msg, "hi\n")
        line = "- Use only this copy's files and the user's messages in this run"
        _, out, _ = run("prompt", self.t, "--run", "v1h-1", "--message", msg)
        self.assertEqual(out.count(line), 1)
        self.assertIn("are not this user's", out)
        _, out, _ = run("prompt", self.t, "--run", "v1h-1", "--message", msg, "--relay", "turn")
        self.assertNotIn(line, out)

    def test_subagents_running(self):
        # background_tasks_changed as Claude Code 2.1.310 wrote it (#513's experiment, trimmed)
        agent = {"task_id": "abb196eda6bf9a5dc", "task_type": "local_agent", "subagent_type": "general-purpose",
                 "description": "sleeper"}
        own = {"task_id": "bredi3cus", "task_type": "local_bash", "description": "sleep 45",
               "parent_task_id": "abb196eda6bf9a5dc"}
        main = {"task_id": "b86868z0r", "task_type": "local_bash", "description": "dev server"}
        event = lambda *tasks: {"type": "system", "subtype": "background_tasks_changed", "tasks": list(tasks)}
        self.assertEqual(harness.subagents_running(event(agent, main)), ["sleeper"])
        self.assertEqual(harness.subagents_running(event(own, main)), ["sleep 45"])   # its subagent goes on after
        self.assertEqual(harness.subagents_running(event(main)), [])
        self.assertEqual(harness.subagents_running(event()), [])

    def test_collect_without_agent_for_a_subagent_run(self):
        rc, _, err = run("collect", "v1h-1", "--runs", self.runs)
        self.assertEqual(rc, 1)
        self.assertIn("pass --agent", err)

    def test_reset_clears_the_process_run(self):
        p = self.process()
        self.assertEqual(self.say("hi")[0], 0)
        run("say", "v1h-1", "--runs", self.runs, "--end")
        p.wait(timeout=60)
        write(os.path.join(self.log, ".git", "info", "exclude"), ".claude/\n")
        rc, out, _ = run("reset", self.t)
        self.assertEqual(rc, 0, out)
        for gone in ("process", "config"):
            self.assertFalse(os.path.exists(os.path.join(self.t, gone)), gone)
        self.assertTrue(os.path.isfile(os.path.join(self.log, "skills", "career-log", "SKILL.md")))
        self.assertEqual(read(os.path.join(self.log, ".git", "info", "exclude")), "")

    def test_remove_deletes_left_credentials(self):
        write(os.path.join(self.t, "config", harness.CREDENTIALS), "x\n")
        self.assertEqual(run("remove", self.t)[0], 0)
        self.assertFalse(os.path.exists(self.t))


class TestSignedInHome(Base):
    """#540 (1, 2): a fake real home in the temp folder; the real profile is never touched."""
    def setUp(self):
        super().setUp()
        self.real = os.path.join(self.tmp, "realhome")
        self.profile = os.path.join(self.real, ".career-log", "browser-profile")
        write(os.path.join(self.profile, "Cookies"), "x\n")
        write(os.path.join(self.real, ".career-log", "machine.toml"), 'poppler = "own"\n')
        patch = mock.patch.dict(os.environ, {"HOME": self.real, "USERPROFILE": self.real})
        patch.start()
        self.addCleanup(patch.stop)
        self.link = os.path.join(self.t, "home", ".career-log", "browser-profile")
        self.copied = os.path.join(self.t, "home", ".career-log", "machine.toml")

    def test_links_the_profile_and_copies_machine_toml_again_after_reset(self):
        self.assertEqual(self.copy()[0], 0)
        rc, out, err = run("signed-in-home", self.t)
        self.assertEqual(rc, 0, out + err)
        self.assertTrue(harness.is_link(self.link))
        self.assertTrue(os.path.isfile(os.path.join(self.link, "Cookies")))
        self.assertEqual(read(self.copied), 'poppler = "own"\n')
        write(self.copied, 'poppler = "micromamba"\n')   # the run's write lands on the copy
        self.assertEqual(run("reset", self.t)[0], 0)
        rc, out, err = run("signed-in-home", self.t)
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(os.listdir(self.profile), ["Cookies"])   # no link inside the old one
        self.assertEqual(read(self.copied), 'poppler = "own"\n')
        self.assertEqual(run("remove", self.t)[0], 0)
        self.assertEqual(os.listdir(self.profile), ["Cookies"])
        self.assertEqual(read(os.path.join(self.real, ".career-log", "machine.toml")), 'poppler = "own"\n')

    def test_replaces_a_dangling_link_and_drops_a_copy_this_machine_has_not(self):
        self.assertEqual(self.copy()[0], 0)
        gone = os.path.join(self.tmp, "gone")
        os.makedirs(gone)
        os.makedirs(os.path.dirname(self.link), exist_ok=True)
        harness.link_dir(self.link, gone)
        os.rmdir(gone)   # the link now points nowhere
        write(self.copied, "stale\n")
        os.remove(os.path.join(self.real, ".career-log", "machine.toml"))
        rc, out, err = run("signed-in-home", self.t)
        self.assertEqual(rc, 0, out + err)
        self.assertTrue(os.path.isfile(os.path.join(self.link, "Cookies")))
        self.assertIn("machine.toml: none at", out)
        self.assertFalse(os.path.exists(self.copied))

    def test_refuses_a_folder_and_a_missing_profile(self):
        self.assertEqual(self.copy()[0], 0)
        write(os.path.join(self.link, "x"), "a real folder\n")
        rc, _, err = run("signed-in-home", self.t)
        self.assertEqual(rc, 1)
        self.assertIn("is a folder, not a link", err)
        self.assertTrue(os.path.isfile(os.path.join(self.link, "x")))
        logfiles.rmtree(self.profile)
        rc, _, err = run("signed-in-home", self.t)
        self.assertEqual(rc, 1)
        self.assertIn("no browser profile at", err)
        self.assertFalse(os.path.exists(self.profile))


class TestRemove(Base):
    def test_remove_leaves_a_linked_folder_s_target(self):
        """The real profile linked into <t>/home (*The real profile*): remove deletes the link only."""
        self.assertEqual(self.copy()[0], 0)
        target = os.path.join(self.tmp, "browser-profile")
        write(os.path.join(target, "Cookies"), "x\n")
        os.makedirs(os.path.join(self.t, "home", ".career-log"), exist_ok=True)
        harness.link_dir(os.path.join(self.t, "home", ".career-log", "browser-profile"), target)
        self.assertEqual(run("remove", self.t)[0], 0)
        self.assertFalse(os.path.exists(self.t))
        self.assertTrue(os.path.isfile(os.path.join(target, "Cookies")))

    def test_remove_deletes_the_copy(self):
        self.assertEqual(self.copy()[0], 0)
        rc, out, _ = run("remove", self.t)
        self.assertEqual(rc, 0)
        self.assertIn("removed:", out)
        self.assertFalse(os.path.exists(self.t))

    def test_remove_refuses_another_folder(self):
        rc, _, err = run("remove", self.wt)
        self.assertEqual(rc, 1)
        self.assertIn("harness.json", err)
        self.assertTrue(os.path.isdir(self.wt))


UPDATER = """import importlib.util, os, sys, time
spec = importlib.util.spec_from_file_location("harness", sys.argv[1])
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)
runs, name, go = sys.argv[2], sys.argv[3], sys.argv[4]
while not os.path.exists(go):
    time.sleep(0.01)
for i in range(1, 41):
    harness.update_row(runs, name, count=i)
"""


class TestLock(unittest.TestCase):
    def test_two_processes_update_two_rows_and_both_are_kept(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(logfiles.rmtree, tmp)
        runs, go, script = (os.path.join(tmp, n) for n in ("runs.jsonl", "go", "updater.py"))
        write(runs, "".join(json.dumps({"name": n, "round": 1}) + "\n" for n in ("v1h-1", "v1h-2")))
        write(script, UPDATER)
        procs = [subprocess.Popen([sys.executable, "-I", script, os.path.join(REPO, "maintainer", "harness.py"),
                                   runs, name, go]) for name in ("v1h-1", "v1h-2")]
        write(go, "")   # both start at once
        for p in procs:
            self.assertEqual(p.wait(timeout=120), 0)
        self.assertEqual({r["name"]: r.get("count") for r in harness.rows(runs)}, {"v1h-1": 40, "v1h-2": 40})


class TestRecords(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(logfiles.rmtree, self.tmp)
        self.records = os.path.join(self.tmp, "records")
        self.projects = os.path.join(self.tmp, "projects")

    def test_project_folder_is_the_one_rule(self):
        path = os.path.join(self.tmp, "a_b c.d")
        rc, out, _ = run("records", "project-folder", path)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), logfiles.claude_folder(path))
        self.assertTrue(out.strip().endswith("a-b-c-d"))
        self.assertRegex(out.strip(), r"^[A-Za-z0-9-]+$")
        self.assertIs(chat_export.claude_folder, logfiles.claude_folder)

    @unittest.skipIf(os.name == "nt", "a symlink needs extra rights on Windows")
    def test_project_folder_through_a_symlink_is_the_resolved_paths(self):
        # #788: the name Claude Code gives, which it takes from the resolved working directory
        real = os.path.join(self.tmp, "real")
        os.makedirs(os.path.join(real, "log"))
        os.symlink(real, os.path.join(self.tmp, "link"))
        rc, out, _ = run("records", "project-folder", os.path.join(self.tmp, "link", "log"))
        self.assertEqual(rc, 0)
        rc, want, _ = run("records", "project-folder", os.path.realpath(os.path.join(real, "log")))
        self.assertEqual(out.strip(), want.strip())

    @unittest.skipIf(os.name == "nt", "a symlink needs extra rights on Windows")
    def test_memory_new_through_a_symlink_writes_the_resolved_paths_folder(self):
        src = os.path.join(self.tmp, "old-projects")
        write(os.path.join(src, "D--old", "memory", "MEMORY.md"), "- index\n")
        real = os.path.join(self.tmp, "real")
        os.makedirs(os.path.join(real, "checkout"))
        os.symlink(real, os.path.join(self.tmp, "link"))
        rc, out, _ = run("records", "memory", src, "D--old", "--new", os.path.join(self.tmp, "link", "checkout"),
                         "--projects", self.projects)
        self.assertEqual(rc, 0, out)
        name = logfiles.claude_folder(os.path.realpath(os.path.join(real, "checkout")))
        self.assertEqual(os.listdir(self.projects), [name])

    def test_snapshot(self):
        for name in ("D--x-log", "D--x-log--claude-worktrees-a", "D--x-log-experiments", "D--other"):
            write(os.path.join(self.projects, name, "s.jsonl"), "{}\n")
        write(os.path.join(self.projects, "D--x-log", "memory", "MEMORY.md"), "- a\n")
        rc, out, _ = run("records", "snapshot", "--folder", "D--x-log", "--projects", self.projects,
                         "--records", self.records, "--date", "2026-01-02")
        self.assertEqual(rc, 0, out)
        snap = os.path.join(self.records, "snapshot-2026-01-02")
        self.assertEqual(sorted(os.listdir(snap)), ["D--x-log", "D--x-log--claude-worktrees-a", "D--x-log-experiments"])
        self.assertIn("PASS memory:", out)
        self.assertIn("worktrees: 1 folders copied", out)

    def test_snapshot_without_memory_fails(self):
        write(os.path.join(self.projects, "D--x-log", "s.jsonl"), "{}\n")
        rc, out, _ = run("records", "snapshot", "--folder", "D--x-log", "--projects", self.projects,
                         "--records", self.records, "--date", "2026-01-02")
        self.assertEqual(rc, 1)
        self.assertIn("FAIL memory:", out)

    def test_scratchpad_and_notes(self):
        pad, notes = os.path.join(self.tmp, "pad"), os.path.join(self.tmp, "notes", "local_1")
        write(os.path.join(pad, "round.md"), "r\n")
        write(os.path.join(pad, "t", harness.META), "{}")
        write(os.path.join(pad, "t", "log", "big.md"), "x\n")
        write(os.path.join(notes, "n.md"), "n\n")
        rc, _, _ = run("records", "scratchpad", pad, "--session", "s1", "--folder", "D--x",
                       "--records", self.records, "--date", "2026-01-02")
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.records, "snapshot-2026-01-02", "scratchpads", "D--x", "s1", "round.md")))
        self.assertFalse(os.path.exists(os.path.join(self.records, "snapshot-2026-01-02", "scratchpads", "D--x", "s1", "t")))
        rc, _, _ = run("records", "notes", notes, "--records", self.records, "--date", "2026-01-02")
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.records, "snapshot-2026-01-02", "side-session-notes", "local_1", "n.md")))

    def test_move(self):
        old, new = os.path.join(self.tmp, "old"), os.path.join(self.tmp, "new")
        write(os.path.join(old, "career-log-experiments", "snapshot-2026-01-02", "x"), "x")
        os.makedirs(new)
        rc, out, _ = run("records", "move", old, new)
        self.assertEqual(rc, 0, out)
        self.assertIn("PASS snapshots: snapshot-2026-01-02", out)
        rc, out, _ = run("records", "move", old, new)
        self.assertIn("skip:", out)

    def test_memory_adds_and_keeps(self):
        src = os.path.join(self.tmp, "old-projects")
        write(os.path.join(src, "D--old", "memory", "MEMORY.md"), "- new index\n")
        new_checkout = os.path.join(self.tmp, "checkout")
        dest = os.path.join(self.projects, logfiles.claude_folder(new_checkout), "memory")
        write(os.path.join(dest, "kept.md"), "kept\n")
        rc, out, _ = run("records", "memory", src, "D--old", "--new", new_checkout, "--projects", self.projects)
        self.assertEqual(rc, 0, out)
        self.assertEqual(read(os.path.join(dest, "MEMORY.md")), "- new index\n")
        self.assertTrue(os.path.isfile(os.path.join(dest, "kept.md")))
        rc, _, err = run("records", "memory", src, "D--missing", "--new", new_checkout, "--projects", self.projects)
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
