#!/usr/bin/env python3
"""Tests for maintainer/prepush.py and maintainer/hooks/pre-push: git repositories in a temp folder (a
local bare repository as the remote) and a scratch deny list; nothing reaches GitHub.

  python3 -I maintainer/tests/test_prepush.py
"""
import importlib.util, io, os, shutil, subprocess, sys, tempfile, unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
HOOKS = os.path.normpath(os.path.join(HERE, "..", "hooks"))
ZERO = "0" * 40
DENY = "# scratch deny list\nacme\nzork[^[:alnum:]]*labs\n"
PATTERNS = ("zork[^[:alnum:]]*labs", "deny list:")   # the list's lines never show, nor a dump of them


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, "..", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


prepush = load("prepush")


def rmtree(path):
    """shutil.rmtree that also removes git's read-only object files on Windows."""
    def retry(func, p, _):
        os.chmod(p, 0o700)
        func(p)
    shutil.rmtree(path, onerror=retry)


def git(cwd, *args, check=True):
    p = subprocess.run(["git", "-C", cwd, "-c", "core.autocrlf=false", *args], capture_output=True,
                       encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise AssertionError("git %s: %s" % (" ".join(args), p.stderr))
    return p


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


class Repo(unittest.TestCase):
    """A repository with one commit pushed to a bare remote `origin`, and a scratch deny list."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo, self.remote = os.path.join(self.tmp, "repo"), os.path.join(self.tmp, "remote.git")
        self.deny = os.path.join(self.tmp, "deny", ".export-deny")
        write(self.deny, DENY)
        git(self.tmp, "init", "-q", "--bare", "-b", "master", self.remote)
        git(self.tmp, "init", "-q", "-b", "master", self.repo)
        for k, v in (("user.email", "test@example.com"), ("user.name", "Test")):
            git(self.repo, "config", k, v)
        git(self.repo, "remote", "add", "origin", self.remote)
        self.commit({"README.md": "hello\n"}, "Start")
        git(self.repo, "push", "-q", "origin", "master")
        self.cwd = os.getcwd()
        os.chdir(self.repo)

    def tearDown(self):
        os.chdir(self.cwd)
        rmtree(self.tmp)

    def commit(self, files, message):
        for path, text in files.items():
            write(os.path.join(self.repo, path), text)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "--allow-empty", "-m", message)
        return git(self.repo, "rev-parse", "HEAD").stdout.strip()

    def run_main(self, *argv, stdin=""):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = prepush.main(list(argv), stdin=io.StringIO(stdin))
        text = out.getvalue() + err.getvalue()
        for pat in PATTERNS:   # the deny list never shows
            self.assertNotIn(pat, text.lower())
        return rc, text

    def scan(self, *revisions):
        return self.run_main("scan", "--deny", self.deny, *(revisions or ("origin/master..HEAD",)))


class Scan(Repo):
    def test_content_hit(self):
        sha = self.commit({"docs/a.md": "one\ntwo\nWorked at ACME.\n"}, "Add a")
        rc, out = self.scan()
        self.assertEqual(rc, 1)
        self.assertIn("FAIL:", out)
        self.assertIn("commit %s: docs/a.md:3" % sha[:10], out)
        self.assertNotIn("worked at", out.lower())   # the line itself is not printed

    def test_file_name_hit(self):
        sha = self.commit({"notes/Zork-Labs.md": "x\n"}, "Add notes")
        self.commit({}, "Later")
        rc, out = self.scan()
        self.assertEqual(rc, 1)
        self.assertIn("commit %s: file name notes/Zork-Labs.md" % sha[:10], out)

    def test_message_hit(self):
        sha = self.commit({"a.md": "x\n"}, "Add a\n\nFor the acme job.")
        rc, out = self.scan()
        self.assertEqual(rc, 1)
        self.assertIn("commit %s: message line 3" % sha[:10], out)
        self.assertNotIn("acme", out.lower())

    def test_hit_taken_out_later_still_refused(self):
        sha = self.commit({"a.md": "acme\n"}, "Add a")
        self.commit({"a.md": "clean\n"}, "Clean a")
        rc, out = self.scan()
        self.assertEqual(rc, 1)
        self.assertIn("commit %s: a.md:1" % sha[:10], out)

    def test_clean_range_passes(self):
        self.commit({"a.md": "acmex, xacme and zorklabsx are other words\n", "b/c.md": "fine\n"}, "Add a")
        self.commit({}, "Empty")
        rc, out = self.scan()
        self.assertEqual(rc, 0, out)
        self.assertIn("OK:", out)

    def test_already_pushed_hit_is_not_scanned(self):
        self.commit({"a.md": "acme\n"}, "Old")
        git(self.repo, "push", "-q", "origin", "master")
        self.commit({"b.md": "fine\n"}, "New")
        self.assertEqual(self.scan()[0], 0)

    def test_merge_and_root(self):
        git(self.repo, "switch", "-q", "-c", "side")
        self.commit({"s.md": "side\n"}, "Side")
        git(self.repo, "switch", "-q", "master")
        self.commit({"m.md": "main\n"}, "Main")
        git(self.repo, "merge", "-q", "--no-edit", "side")
        self.assertEqual(self.scan()[0], 0)
        self.assertEqual(self.scan("HEAD")[0], 0)   # from the root commit

    def test_annotated_tag_message(self):
        self.commit({"a.md": "x\n"}, "Add a")
        git(self.repo, "tag", "-a", "v1", "-m", "Release for Acme")
        rc, out = self.scan("v1", "--not", "--remotes=origin")
        self.assertEqual(rc, 1)
        self.assertIn(": message line 1", out)
        self.assertIn("tag ", out)

    def test_missing_empty_and_unreadable_deny_list(self):
        self.commit({"a.md": "x\n"}, "Add a")
        rc, out = self.run_main("scan", "--deny", os.path.join(self.tmp, "nope"), "HEAD")
        self.assertEqual(rc, 1)
        self.assertIn("no deny list at", out)
        write(self.deny, "# only a comment\n\n")
        self.assertEqual(self.scan()[0], 1)
        write(self.deny, "acme(?i)zork\n")
        rc, out = self.scan()
        self.assertEqual(rc, 1)
        self.assertIn("cannot be read as grep -E", out)

    def test_usage(self):
        self.assertEqual(self.run_main("scan", "HEAD")[0], 2)
        self.assertEqual(self.run_main()[0], 2)


class Hook(Repo):
    def configure(self, path=None):
        git(self.repo, "config", prepush.CONFIG_KEY, path or self.deny)

    def line(self, ref="refs/heads/master", remote_ref=None, remote_oid=None):
        local = git(self.repo, "rev-parse", "HEAD").stdout.strip()
        if remote_oid is None:
            remote_oid = git(self.repo, "rev-parse", "origin/master").stdout.strip()
        return "%s %s %s %s\n" % (ref, local, remote_ref or ref, remote_oid)

    def test_no_configured_path_refuses(self):
        self.commit({"a.md": "x\n"}, "Add a")
        rc, out = self.run_main("hook", "origin", self.remote, stdin=self.line())
        self.assertEqual(rc, 1)
        self.assertIn("no deny list configured", out)

    def test_configured_path_with_no_file_refuses(self):
        self.configure(os.path.join(self.tmp, "gone", ".export-deny"))
        self.commit({"a.md": "x\n"}, "Add a")
        rc, out = self.run_main("hook", "origin", self.remote, stdin=self.line())
        self.assertEqual(rc, 1)
        self.assertIn("no deny list at", out)

    def test_existing_branch(self):
        self.configure()
        self.commit({"a.md": "x\n"}, "Add a")
        self.assertEqual(self.run_main("hook", "origin", self.remote, stdin=self.line())[0], 0)
        self.commit({"b.md": "acme\n"}, "Add b")
        rc, out = self.run_main("hook", "origin", self.remote, stdin=self.line())
        self.assertEqual(rc, 1)
        self.assertIn("b.md:1", out)

    def test_new_branch(self):
        self.configure()
        git(self.repo, "switch", "-q", "-c", "topic")
        self.commit({"a.md": "x\n"}, "Add a")
        new = self.line("refs/heads/topic", remote_oid=ZERO)
        rc, out = self.run_main("hook", "origin", self.remote, stdin=new)
        self.assertEqual(rc, 0, out)
        self.commit({"b.md": "x\n"}, "Zork Labs")
        rc, out = self.run_main("hook", "origin", self.remote, stdin=self.line("refs/heads/topic", remote_oid=ZERO))
        self.assertEqual(rc, 1)
        self.assertIn("message line 1", out)

    def test_deleted_branch(self):
        self.configure()
        rc, out = self.run_main("hook", "origin", self.remote,
                                stdin="(delete) %s refs/heads/old %s\n" % (ZERO, "1" * 40))
        self.assertEqual(rc, 0, out)

    def test_remote_oid_not_here(self):
        """A remote ref that moved since the last fetch: its old commit is unknown here."""
        self.configure()
        self.commit({"a.md": "x\n"}, "Add a")
        self.assertEqual(self.run_main("hook", "origin", self.remote, stdin=self.line(remote_oid="2" * 40))[0], 0)

    def test_check(self):
        rc, out = self.run_main("check")
        self.assertEqual(rc, 1)
        self.assertIn("not active", out)
        git(self.repo, "config", "core.hooksPath", "maintainer/hooks")
        self.assertIn("no deny list configured", self.run_main("check")[1])
        self.configure()
        rc, out = self.run_main("check")
        self.assertEqual(rc, 0, out)
        self.assertIn("2 patterns", out)


class RealPush(Repo):
    """`git push` through maintainer/hooks/pre-push itself, as git runs it."""

    def push(self, *args):
        p = git(self.repo, "-c", "core.hooksPath=" + HOOKS.replace("\\", "/"), "push", "origin", *args, check=False)
        text = p.stdout + p.stderr
        for pat in PATTERNS + ("acme",):
            self.assertNotIn(pat, text.lower())
        return p.returncode, text

    def test_push(self):
        self.commit({"a.md": "x\n"}, "Add a")
        rc, out = self.push("master")
        self.assertNotEqual(rc, 0)   # no deny list configured
        self.assertIn("no deny list configured", out)
        git(self.repo, "config", prepush.CONFIG_KEY, self.deny)
        self.assertEqual(self.push("master")[0], 0)
        self.commit({"b.md": "ACME\n"}, "Add b")
        rc, out = self.push("master")
        self.assertNotEqual(rc, 0)
        self.assertIn("b.md:1", out)
        git(self.repo, "reset", "-q", "--hard", "HEAD~1")
        git(self.repo, "switch", "-q", "-c", "topic")
        self.commit({"c.md": "fine\n"}, "Add c")
        self.assertEqual(self.push("topic")[0], 0)            # a new branch
        self.assertEqual(self.push("--delete", "topic")[0], 0)  # a deleted one


if __name__ == "__main__":
    unittest.main()
