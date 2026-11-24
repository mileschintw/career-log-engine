#!/usr/bin/env python3
"""Tests for maintainer/devbuild.py: a Dev build from a clone of this repo's HEAD into scratch
repositories in a temp folder, with a local repository standing in for the Template's release tags;
nothing reaches GitHub.

  python3 -I maintainer/tests/test_devbuild.py
"""
import filecmp, importlib.util, io, os, re, shutil, subprocess, sys, tarfile, tempfile, unittest, unittest.mock
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

spec = importlib.util.spec_from_file_location("devbuild", os.path.join(HERE, "..", "devbuild.py"))
devbuild = importlib.util.module_from_spec(spec)
spec.loader.exec_module(devbuild)


rmtree = devbuild.logfiles.rmtree


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
        self.assertEqual(devbuild.next_version("0.4.0", False), "0.4.1")
        self.assertEqual(devbuild.next_version("0.4.2", True), "0.5.0")

    def test_dev_number(self):
        tags = ["v0.4.1-dev.1", "v0.4.1-dev.10", "v0.4.1-dev.2", "v0.5.0-dev.7", "v0.4.1", "v0.4.1-dev.x",
                "v0.4.10-dev.30", "v0.4.1-dev.01", "0.4.1-dev.40"]
        self.assertEqual(devbuild.dev_number(tags, "0.4.1"), 11)
        self.assertEqual(devbuild.dev_number(tags, "0.4.2"), 1)   # starts at 1 after a release

    def test_release_tags(self):
        self.assertEqual(devbuild.release_tags(["v0.4.0", "v0.10.1", "v0.4.1-dev.1", "0.5.0", "v1.2",
                                                "v١.٢.٣", "v0.4.0\n"]),
                         ["0.4.0", "0.10.1"])

    def test_latest_release_in_upgrades_order(self):
        self.assertEqual(devbuild.latest_release(["v0.9.0", "v0.10.0", "v0.10.1-dev.3", "v0.2.0"]), "0.10.0")
        self.assertIsNone(devbuild.latest_release(["v0.4.1-dev.1", "main"]))

    def test_reads_the_forms_from_upgrade(self):
        # #22: devbuild takes the forms from tools/upgrade.py; a form changed there changes here.
        # OneVersionForm below fails on a form written anywhere else
        with unittest.mock.patch.object(devbuild.upgrade, "VERSION", re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-rc\.(\d+))?\Z")):
            self.assertEqual(devbuild.release_tags(["v0.4.0", "v0.4.1-rc.2", "v0.4.1-dev.1"]), ["0.4.0"])
            self.assertEqual(devbuild.dev_number(["v0.4.1-rc.2", "v0.4.1-dev.5"], "0.4.1"), 3)


class OneVersionForm(unittest.TestCase):
    """#22: tools/tests/test_logfiles.py's OneVersionForm guard, for maintainer/*.py: the checks run
    this file on a change there (coord-tests.yml), where they do not run test_logfiles.py."""

    def test_no_maintainer_tool_writes_a_version_form_of_its_own(self):
        spec = importlib.util.spec_from_file_location("test_logfiles", os.path.join(REPO, "tools", "tests",
                                                                                     "test_logfiles.py"))
        test_logfiles = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_logfiles)
        self.assertEqual(test_logfiles.copied_version_forms("maintainer"), [])


@unittest.skipUnless(shutil.which("sh") or os.name == "nt", "no sh to run tools/export-template.sh")
class Build(unittest.TestCase):
    """A Dev build from a clone of this repo's HEAD (its next guide reset to the empty skeleton) into a
    scratch dest with a commit on master, the latest release v0.4.0 in a scratch releases repo."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # a global git config of the test's own, as on a CI runner: no identity but what a repo sets,
        # here or in the new <dest>'s case below
        self.global_config = os.path.join(self.tmp, "gitconfig")
        with open(self.global_config, "w", encoding="utf-8") as f:
            # and no automatic maintenance: the commits and fetches here would start a gc that detaches
            # and can still be repacking a repository when tearDown removes it
            f.write("[user]\n\tuseConfigOnly = true\n[maintenance]\n\tauto = false\n[gc]\n\tauto = 0\n")
        self.env = unittest.mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": self.global_config})
        self.env.start()
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
        self.env.stop()
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
        source = git(self.src, "rev-parse", "HEAD")
        self.assertEqual(git(self.dest, "log", "-1", "--format=%B", "builds"),
                         "Dev build 0.4.1-dev.2\n\nExported from career-log-engine %s" % source)
        self.assertEqual(git(self.dest, "tag", "-l", "--format=%(contents)", "v0.4.1-dev.2"),
                         "Dev build 0.4.1-dev.2 of career-log-engine %s" % source)
        git(self.dest, "tag", "v0.4.1")   # a release in dest counts too, and <n> starts over
        rc, out, err = self.build()
        self.assertEqual(rc, 0, out + err)
        self.assertIn("dev build: v0.4.2-dev.1", out)

    def test_tree_is_the_export(self):
        rc, out, err = self.build()
        self.assertEqual(rc, 0, out + err)
        want = os.path.join(self.tmp, "export")
        with redirect_stdout(io.StringIO()):
            devbuild.coord.export(self.src, "0.4.1-dev.1", want)
        got = os.path.join(self.tmp, "got")
        os.makedirs(got)
        tar = os.path.join(self.tmp, "got.tar")
        git(self.dest, "archive", "-o", tar, "v0.4.1-dev.1")
        with tarfile.open(tar) as t:
            t.extractall(got, **({"filter": "tar"} if hasattr(tarfile, "tar_filter") else {}))   # 3.11.4+
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
        # and the release tags, as the releases repo has them, for an upgrade from <dest> (#19)
        self.assertEqual(git(self.dest, "tag", "-l").split(), ["v0.3.9", "v0.4.0", "v0.4.1-dev.1"])
        self.assertEqual(git(self.dest, "rev-parse", "v0.4.0"), git(self.rel, "rev-parse", "v0.4.0"))

    def test_keeps_a_release_tag_dest_has(self):
        git(self.dest, "tag", "v0.4.0")   # dest's own v0.4.0, another commit than the releases repo's
        git(self.rel, "commit", "-q", "--allow-empty", "-m", "second")
        git(self.rel, "tag", "-f", "v0.4.0")
        rc, out, err = self.build()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(git(self.dest, "rev-parse", "v0.4.0"), git(self.dest, "rev-parse", "master"))
        self.assertEqual(git(self.dest, "rev-parse", "v0.3.9"), git(self.rel, "rev-parse", "v0.3.9"))

    def test_builds_while_the_guide_holds_a_change(self):
        self.guide_change()
        rc, out, err = self.build()
        self.assertEqual(rc, 0, out + err)
        self.assertIn("dev build: v0.5.0-dev.1", out)
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(devbuild.Fail):   # a release is still refused
            devbuild.coord.export(self.src, "0.5.0", os.path.join(self.tmp, "rel-export"))
        self.assertIn("holds a Log format change or a new setting", out.getvalue())

    def test_push(self):
        remote = os.path.join(self.tmp, "remote.git")
        git(self.tmp, "init", "-q", "--bare", remote)
        git(self.dest, "remote", "add", "origin", remote)
        rc, out, err = self.build("--push", "origin")
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(git(remote, "rev-parse", "builds"), git(self.dest, "rev-parse", "builds"))
        self.assertEqual(git(remote, "tag", "-l"), "v0.4.1-dev.1")
        # a build that is pushed is upgraded to from there, with the Template's releases: none fetched here
        self.assertEqual(git(self.dest, "tag", "-l"), "v0.4.1-dev.1")

    def test_into_a_new_repo(self):
        self.dest = os.path.join(self.tmp, "new")
        rc, out, err = self.build()   # a new repo has no identity of its own: stops before the export
        self.assertEqual(rc, 1, out + err)
        self.assertIn("no git identity", err)
        self.assertEqual(out, "")
        self.assertEqual(git(self.dest, "tag", "-l"), "")
        identity(self.dest)
        rc, out, err = self.build()
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(git(self.dest, "tag", "-l").split(), ["v0.3.9", "v0.4.0", "v0.4.1-dev.1"])

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
        with open(os.path.join(self.dest, "sub", "f.txt"), "w") as f:   # not empty: never made a repo
            f.write("x\n")
        rc, out, err = run(os.path.join(self.dest, "sub"), "--root", self.src, "--releases", self.rel)
        self.assertEqual(rc, 1)
        self.assertIn("not the top", err)
        self.assertEqual(git(self.dest, "tag", "-l"), "")


@unittest.skipUnless(shutil.which("sh") or os.name == "nt", "no sh to run tools/export-template.sh")
class UpgradeToALocalBuild(unittest.TestCase):
    """#19: a Dev build made into an empty folder is a --url the upgrade tool takes, for a Log on the
    latest release and for a Log on an earlier Dev build of the same version. The releases repo holds a
    real release, v0.4.0, the export of the source as it was; the Log is made from it."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.global_config = os.path.join(self.tmp, "gitconfig")
        with open(self.global_config, "w", encoding="utf-8") as f:
            f.write("[user]\n\tuseConfigOnly = true\n[maintenance]\n\tauto = false\n[gc]\n\tauto = 0\n"
                    "[core]\n\tautocrlf = false\n")
        # the identity <dest> gets nowhere else: it is an empty folder before the build
        who = {"GIT_%s_%s" % (r, k): v for r in ("AUTHOR", "COMMITTER")
               for k, v in (("NAME", "Test"), ("EMAIL", "test@example.com"))}
        self.env = unittest.mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": self.global_config, **who})
        self.env.start()
        self.src, self.dest, self.rel, self.log = (os.path.join(self.tmp, n) for n in ("src", "dest", "rel", "log"))
        git(self.tmp, "clone", "-q", REPO, self.src)
        up = os.path.join(self.src, "docs", "upgrades")
        for ext in ("md", "py"):   # whatever upgrade-next.* holds now, start from an empty guide
            shutil.copyfile(os.path.join(up, "upgrade-skeleton." + ext), os.path.join(up, "upgrade-next." + ext))
        git(self.src, "commit", "-q", "--allow-empty", "-am", "an empty next guide")
        # the release: the export of the source at 0.4.0, as the Template holds it
        git(self.tmp, "init", "-q", "-b", "main", self.rel)
        with redirect_stdout(io.StringIO()):
            devbuild.coord.export(self.src, "0.4.0", os.path.join(self.tmp, "release"))
        shutil.copytree(os.path.join(self.tmp, "release"), self.rel, dirs_exist_ok=True)
        git(self.rel, "add", "-A", "-f")
        git(self.rel, "commit", "-q", "-m", "Release 0.4.0")
        git(self.rel, "tag", "v0.4.0")
        # the Log: a new repository with the release's files, as the Template's "Use this template" makes one
        git(self.tmp, "init", "-q", "-b", "main", self.log)
        tar = os.path.join(self.tmp, "release.tar")
        git(self.rel, "archive", "-o", tar, "v0.4.0")
        with tarfile.open(tar) as t:
            t.extractall(self.log, **({"filter": "tar"} if hasattr(tarfile, "tar_filter") else {}))
        git(self.log, "add", "-A")
        git(self.log, "commit", "-q", "-m", "Initial commit")
        self.tool = os.path.join(self.src, "tools", "upgrade.py")

    def tearDown(self):
        self.env.stop()
        rmtree(self.tmp)

    def change_and_build(self, text):
        """A commit to the source's AGENTS.md, then its Dev build into dest; the build's version."""
        with open(os.path.join(self.src, "AGENTS.md"), "a", encoding="utf-8", newline="\n") as f:
            f.write("\n%s\n" % text)
        git(self.src, "commit", "-q", "-am", text)
        rc, out, err = run(self.dest, "--root", self.src, "--releases", self.rel)
        self.assertEqual(rc, 0, out + err)
        return out.split("dev build: v", 1)[1].split()[0]

    def upgrade(self, version):
        """plan --to <version> --url <dest>, then engine and a commit, as the upgrade mode runs them."""
        def tool(*args):
            p = subprocess.run([sys.executable, "-I", self.tool, *args], capture_output=True, encoding="utf-8")
            return p.returncode, p.stdout.splitlines()
        rc, out = tool("plan", self.log, "--to", version, "--url", self.dest)
        self.assertEqual(rc, 0, out)
        self.assertEqual(out[1], "to: " + version)
        self.assertEqual([l for l in out if l.startswith("step: ")], ["step: " + version])
        rc, out = tool("engine", self.log, version)
        self.assertEqual(rc, 0, out)
        git(self.log, "add", "-A")
        git(self.log, "commit", "-q", "-m", "upgrade: Template " + version)
        with open(os.path.join(self.log, "tools", "TEMPLATE_VERSION"), encoding="utf-8") as f:
            self.assertEqual(f.readline().strip(), version)

    def agents(self):
        with open(os.path.join(self.log, "AGENTS.md"), encoding="utf-8") as f:
            return f.read()

    def test_from_the_release_then_from_an_earlier_dev_build(self):
        os.makedirs(self.dest)   # an empty folder
        first = self.change_and_build("first change")
        self.assertEqual(first, "0.4.1-dev.1")
        self.upgrade(first)   # the Log on the latest release
        self.assertIn("first change", self.agents())
        second = self.change_and_build("second change")
        self.assertEqual(second, "0.4.1-dev.2")
        self.upgrade(second)   # the Log on an earlier Dev build of the same version
        self.assertIn("second change", self.agents())


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


if __name__ == "__main__":
    unittest.main()
