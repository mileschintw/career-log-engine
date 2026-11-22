#!/usr/bin/env python3
"""Tests for maintainer/devbuild.py: a Dev build from a clone of this repo's HEAD into scratch
repositories in a temp folder, with a local repository standing in for the Template's release tags;
nothing reaches GitHub.

  python3 -I maintainer/tests/test_devbuild.py
"""
import filecmp, importlib.util, io, os, shutil, subprocess, tarfile, tempfile, unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

spec = importlib.util.spec_from_file_location("devbuild", os.path.join(HERE, "..", "devbuild.py"))
devbuild = importlib.util.module_from_spec(spec)
spec.loader.exec_module(devbuild)


def rmtree(path):
    """shutil.rmtree that also removes git's read-only object files on Windows."""
    def retry(func, p, _):
        os.chmod(p, 0o700)
        func(p)
    shutil.rmtree(path, onerror=retry)


def git(cwd, *args):
    return subprocess.run(["git", "-C", cwd, "-c", "core.autocrlf=false", *args], check=True,
                          capture_output=True, encoding="utf-8").stdout.strip()


def identity(repo):
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test")


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = devbuild.main(list(argv))
    return rc, out.getvalue(), err.getvalue()


class Numbers(unittest.TestCase):
    def test_next_version(self):
        self.assertEqual(devbuild.next_version((0, 4, 0), False), "0.4.1")
        self.assertEqual(devbuild.next_version((0, 4, 2), True), "0.5.0")

    def test_dev_number(self):
        tags = ["v0.4.1-dev.1", "v0.4.1-dev.10", "v0.4.1-dev.2", "v0.5.0-dev.7", "v0.4.1", "v0.4.1-dev.x"]
        self.assertEqual(devbuild.dev_number(tags, "0.4.1"), 11)
        self.assertEqual(devbuild.dev_number(tags, "0.4.2"), 1)   # starts at 1 after a release

    def test_release_tags(self):
        self.assertEqual(devbuild.release_tags(["v0.4.0", "v0.10.1", "v0.4.1-dev.1", "0.5.0", "v1.2"]),
                         [(0, 4, 0), (0, 10, 1)])


@unittest.skipUnless(shutil.which("sh") or os.name == "nt", "no sh to run tools/export-template.sh")
class Build(unittest.TestCase):
    """A Dev build from a clone of this repo's HEAD (its next guide reset to the empty skeleton) into a
    scratch dest with a commit on master, the latest release v0.4.0 in a scratch releases repo."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.src, self.dest, self.rel = (os.path.join(self.tmp, n) for n in ("src", "dest", "rel"))
        git(self.tmp, "clone", "-q", REPO, self.src)
        identity(self.src)
        up = os.path.join(self.src, "docs", "upgrades")
        for ext in ("md", "py"):   # whatever upgrade-next.* holds now, start from an empty guide
            shutil.copyfile(os.path.join(up, "upgrade-skeleton." + ext), os.path.join(up, "upgrade-next." + ext))
        git(self.src, "commit", "-q", "--allow-empty", "-am", "an empty next guide")
        for repo in (self.dest, self.rel):
            git(self.tmp, "init", "-q", "-b", "master", repo)
            identity(repo)
            git(repo, "commit", "-q", "--allow-empty", "-m", "first")
        git(self.rel, "tag", "v0.4.0")
        git(self.rel, "tag", "v0.3.9")

    def tearDown(self):
        rmtree(self.tmp)

    def build(self, *extra):
        return run(self.dest, "--root", self.src, "--releases", self.rel, *extra)

    def guide_change(self):
        p = os.path.join(self.src, "docs", "upgrades", "upgrade-next.md")
        with open(p, encoding="utf-8") as f:
            text = f.read()
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text.replace(devbuild.NO_CHANGE, "- a format change, step 1"))
        git(self.src, "commit", "-q", "-am", "a Log format change")

    def test_numbers_and_a_second_run(self):
        rc, out, err = self.build()
        self.assertEqual(rc, 0, out + err)
        self.assertIn("dev build: v0.4.1-dev.1", out)
        first = git(self.dest, "rev-parse", "builds")
        rc, out, err = self.build()
        self.assertEqual(rc, 0, out + err)
        self.assertIn("dev build: v0.4.1-dev.2", out)
        self.assertEqual(git(self.dest, "rev-parse", "v0.4.1-dev.2^{commit}"), git(self.dest, "rev-parse", "builds"))
        self.assertEqual(git(self.dest, "rev-parse", "builds^"), first)
        self.assertEqual(git(self.dest, "cat-file", "-t", "v0.4.1-dev.2"), "tag")   # annotated: --follow-tags
        git(self.dest, "tag", "v0.4.1")   # a release in dest counts too, and <n> starts over
        rc, out, err = self.build()
        self.assertEqual(rc, 0, out + err)
        self.assertIn("dev build: v0.4.2-dev.1", out)

    def test_tree_is_the_export(self):
        rc, out, err = self.build()
        self.assertEqual(rc, 0, out + err)
        want = os.path.join(self.tmp, "export")
        devbuild.export(self.src, "0.4.1-dev.1", want)
        got = os.path.join(self.tmp, "got")
        os.makedirs(got)
        tar = os.path.join(self.tmp, "got.tar")
        git(self.dest, "archive", "-o", tar, "v0.4.1-dev.1")
        with tarfile.open(tar) as t:
            t.extractall(got, filter="tar")
        self.assertEqual(diff(want, got), [])
        with open(os.path.join(got, "tools", "TEMPLATE_VERSION"), encoding="utf-8") as f:
            self.assertEqual(f.read().splitlines(), ["0.4.1-dev.1", "source " + git(self.src, "rev-parse", "HEAD")])
        modes = {l.split("\t")[1] for l in git(self.dest, "ls-tree", "-r", "v0.4.1-dev.1").splitlines()
                 if l.startswith("100755")}
        self.assertIn("tools/export-template.sh", modes)   # the source's modes, on Windows too
        self.assertIn("docs/upgrades/upgrade-next.md", got_files(got))   # the next guide as it stands

    def test_writes_only_the_builds_branch(self):
        master = git(self.dest, "rev-parse", "master")
        rc, out, err = self.build()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(git(self.dest, "rev-parse", "master"), master)
        self.assertEqual(git(self.dest, "status", "--porcelain"), "")
        self.assertEqual(git(self.dest, "for-each-ref", "--format=%(refname)", "refs/heads"),
                         "refs/heads/builds\nrefs/heads/master")
        p = subprocess.run(["git", "-C", self.dest, "merge-base", "builds", "master"], capture_output=True)
        self.assertEqual(p.returncode, 1)   # no common history
        self.assertEqual(git(self.dest, "rev-list", "--count", "builds"), "1")

    def test_builds_while_the_guide_holds_a_change(self):
        self.guide_change()
        rc, out, err = self.build()
        self.assertEqual(rc, 0, out + err)
        self.assertIn("dev build: v0.5.0-dev.1", out)
        rc, out, err = run_export(self.src, "--version", "0.5.0", os.path.join(self.tmp, "rel-export"))
        self.assertEqual(rc, 1, out)   # a release is still refused
        self.assertIn("holds a Log format change or a new setting", out)

    def test_push(self):
        remote = os.path.join(self.tmp, "remote.git")
        git(self.tmp, "init", "-q", "--bare", remote)
        git(self.dest, "remote", "add", "origin", remote)
        rc, out, err = self.build("--push", "origin")
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(git(remote, "rev-parse", "builds"), git(self.dest, "rev-parse", "builds"))
        self.assertEqual(git(remote, "tag", "-l"), "v0.4.1-dev.1")

    def test_into_a_new_repo(self):
        self.dest = os.path.join(self.tmp, "new")
        rc, out, err = self.build()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(git(self.dest, "tag", "-l"), "v0.4.1-dev.1")

    def test_refusals(self):
        git(self.rel, "tag", "-d", "v0.4.0")
        git(self.rel, "tag", "-d", "v0.3.9")
        rc, out, err = self.build()
        self.assertEqual(rc, 1)
        self.assertIn("no release tag", err)
        git(self.rel, "tag", "v0.4.0")
        git(self.dest, "switch", "-q", "--orphan", "builds")
        rc, out, err = self.build()
        self.assertEqual(rc, 1)
        self.assertIn("checked out", err)
        os.makedirs(os.path.join(self.dest, "sub"))
        rc, out, err = run(os.path.join(self.dest, "sub"), "--root", self.src, "--releases", self.rel)
        self.assertEqual(rc, 1)
        self.assertIn("not the top", err)
        self.assertEqual(git(self.dest, "tag", "-l"), "")


def got_files(root):
    return {os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/") for d, _, fs in os.walk(root) for f in fs}


def diff(a, b):
    """The relative paths that differ between two folders: missing on one side, or other bytes."""
    fa, fb = got_files(a), got_files(b)
    out = sorted(fa ^ fb)
    for p in sorted(fa & fb):
        if not filecmp.cmp(os.path.join(a, p), os.path.join(b, p), shallow=False):
            out.append(p)
    return out


def run_export(root, *args):
    sh, extra = devbuild.coord.find_sh()
    env = dict(os.environ, PATH=extra + os.pathsep + os.environ.get("PATH", "")) if extra else None
    p = subprocess.run([sh, "tools/export-template.sh", *args], cwd=root, env=env, capture_output=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout


if __name__ == "__main__":
    unittest.main()
