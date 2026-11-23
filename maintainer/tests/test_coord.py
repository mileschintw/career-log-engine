#!/usr/bin/env python3
"""Tests for maintainer/coord.py: a stubbed gh for block, and git repositories in a temp folder (a
local bare repository as the template remote) for publish; nothing reaches GitHub.

  python3 -I maintainer/tests/test_coord.py
"""
import ast, importlib.util, io, json, os, re, shutil, subprocess, tempfile, unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, "..", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


coord = load("coord")

GH_REPO = "owner/repo"


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


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def run(*argv, gh=None):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = coord.main(list(argv), **({"run": gh} if gh else {}))
    return rc, out.getvalue(), err.getvalue()


class Temp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        rmtree(self.tmp)


class FakeGh:
    """gh stub for block: blockers (issue -> list of blocking numbers), ids (number -> GitHub id);
    a POST adds the blocker unless `ignore_posts`."""

    def __init__(self, blockers=None, ignore_posts=False):
        self.blockers, self.ignore_posts, self.calls = blockers or {}, ignore_posts, []

    def __call__(self, args):
        self.calls.append(args)
        m = re.fullmatch(r"repos/%s/issues/(\d+)/dependencies/blocked_by\?per_page=100" % GH_REPO, args[1])
        if args[0] == "api" and m:
            return json.dumps([{"number": n, "repository_url": "https://api.github.com/repos/" + GH_REPO}
                               for n in self.blockers.get(int(m.group(1)), [])])
        m = re.fullmatch(r"repos/%s/issues/(\d+)" % GH_REPO, args[1])
        if args[0] == "api" and m and args[2:] == ["-q", ".id"]:
            return "%d\n" % (9000 + int(m.group(1)))
        if args[:3] == ["api", "-X", "POST"]:
            n = int(re.fullmatch(r"repos/%s/issues/(\d+)/dependencies/blocked_by" % GH_REPO, args[3]).group(1))
            if not self.ignore_posts:
                self.blockers.setdefault(n, []).append(int(args[5].split("=")[1]) - 9000)
            return "{}"
        raise RuntimeError("unexpected gh call: %r" % args)

    def posts(self):
        return [c for c in self.calls if c[:3] == ["api", "-X", "POST"]]


class Block(unittest.TestCase):
    def test_marks_new_blockers_and_skips_listed(self):
        gh = FakeGh({20: [5]})
        rc, out, err = run("block", "20", "5", "7", "--repo", GH_REPO, gh=gh)
        self.assertEqual(rc, 0, err)
        self.assertEqual(gh.posts(), [["api", "-X", "POST", "repos/%s/issues/20/dependencies/blocked_by" % GH_REPO,
                                       "-F", "issue_id=9007"]])
        self.assertIn("already blocked by #5", out)
        self.assertIn("#20 is blocked by: #5, #7", out)

    def test_dry_run_writes_nothing(self):
        gh = FakeGh()
        rc, out, err = run("block", "20", "7", "--repo", GH_REPO, "--dry-run", gh=gh)
        self.assertEqual(rc, 0, err)
        self.assertEqual(gh.posts(), [])
        self.assertIn("would run: gh api -X POST repos/%s/issues/20/dependencies/blocked_by" % GH_REPO, out)

    def test_fails_when_github_does_not_list_it(self):
        rc, _, err = run("block", "20", "7", "--repo", GH_REPO, gh=FakeGh(ignore_posts=True))
        self.assertEqual(rc, 1)
        self.assertIn("does not list #7", err)

    def test_refuses_self(self):
        rc, _, err = run("block", "20", "20", "--repo", GH_REPO, gh=FakeGh())
        self.assertEqual(rc, 1)

    def test_refuses_a_blocker_in_another_repository(self):
        def other(args):
            return json.dumps([{"number": 3, "repository_url": "https://api.github.com/repos/else/where"}])
        rc, _, err = run("block", "20", "7", "--repo", GH_REPO, gh=other)
        self.assertEqual(rc, 1)
        self.assertIn("else/where#3", err)

    def test_lookup_failure(self):
        def broken(args):
            raise RuntimeError("HTTP 404")
        rc, _, err = run("block", "20", "7", "--repo", GH_REPO, gh=broken)
        self.assertEqual(rc, 1)
        self.assertIn("lookup for #20 failed", err)


def has_sh():
    try:
        return bool(coord.find_sh())
    except coord.Fail:
        return False


@unittest.skipUnless(has_sh(), "no sh, on PATH or from Git for Windows")
class Publish(Temp):
    """publish from a clone of this repo's HEAD into a scratch folder, against a local template repo. The
    clone's upgrade-next.* are reset to the empty skeleton, so the export accepts a release whatever
    Log format change this repo's next guide holds."""

    def setUp(self):
        super().setUp()
        self.src = os.path.join(self.tmp, "src")
        git(self.tmp, "clone", "-q", REPO, self.src)
        identity(self.src)
        upgrades = os.path.join(self.src, "docs", "upgrades")
        for ext in ("md", "py"):
            shutil.copyfile(os.path.join(upgrades, "upgrade-skeleton." + ext), os.path.join(upgrades, "upgrade-next." + ext))
        git(self.src, "commit", "-q", "--allow-empty", "-am", "no Log format change")
        self.tpl_remote = os.path.join(self.tmp, "tpl.git")
        seed = os.path.join(self.tmp, "tpl-seed")
        git(self.tmp, "init", "-q", "--bare", "-b", "main", self.tpl_remote)
        git(self.tmp, "clone", "-q", self.tpl_remote, seed)
        identity(seed)
        write(os.path.join(seed, "stale.md"), "from the last release\n")
        write(os.path.join(seed, "SETUP.md"), "old\n")
        git(seed, "add", "-A")
        git(seed, "update-index", "--chmod=+x", "SETUP.md")   # executable in the public repo, not in the source
        git(seed, "commit", "-q", "-m", "Release 0.1.0")
        git(seed, "push", "-q", "origin", "HEAD:main")
        self.scratch = os.path.join(self.tmp, "scratch")

    def publish(self, *extra):
        return run("publish", self.scratch, "--version", "9.9.9", "--summary", "a summary", "--root", self.src,
                   "--url", self.tpl_remote, *extra)

    def test_stages_the_export(self):
        rc, out, err = self.publish()
        self.assertEqual(rc, 0, err + out)
        tpl = os.path.join(self.scratch, "tpl")
        staged = git(tpl, "diff", "--cached", "--name-status").splitlines()
        self.assertIn("D\tstale.md", staged)
        self.assertIn("A\tAGENTS.md", staged)
        self.assertIn("M\tSETUP.md", staged)
        self.assertFalse(any(re.search(r"\tmaintainer/", l) for l in staged))
        self.assertEqual(read(os.path.join(tpl, "tools", "TEMPLATE_VERSION")).splitlines()[0], "9.9.9")
        sha = git(self.src, "rev-parse", "HEAD")
        self.assertEqual(read(os.path.join(self.scratch, "commit-message.txt")),
                         "Release 9.9.9: a summary\n\nExported from career-log-engine %s\n" % sha)
        self.assertEqual(git(tpl, "log", "--format=%s"), "Release 0.1.0")   # nothing committed
        want = sorted(l.split("\t")[1] for l in git(self.src, "ls-tree", "-r", "HEAD").splitlines()
                      if l.startswith("100755") and not l.split("\t")[1].startswith("maintainer/"))
        got = sorted(l.split("\t")[1] for l in git(tpl, "ls-files", "-s").splitlines() if l.startswith("100755"))
        self.assertTrue(want)
        self.assertEqual(got, want)
        self.assertIn("executable (100755): " + ", ".join(want), out)
        self.assertIn("\nguide: none\n", out)
        self.assertIn("commit -F", out)

    def test_a_new_setting_ships_the_guide(self):
        # #329: a `## 3. New settings` entry alone makes the release ship the guide, so the export
        # refuses an unrenamed upgrade-next.*, and publish names upgrade-<version>.* once renamed
        up = os.path.join(self.src, "docs", "upgrades")
        md = os.path.join(up, "upgrade-next.md")
        text = read(md)
        self.assertIn("This release adds none.", text.splitlines())
        write(md, text.replace("This release adds none.", "- `a_field` (Config, default `1`): ask."))
        git(self.src, "commit", "-q", "-am", "a new setting")
        rc, out, _ = self.publish()
        self.assertEqual(rc, 1)
        self.assertIn("holds a Log format change or a new setting", out)
        self.assertFalse(os.path.exists(os.path.join(self.scratch, "tpl")))
        for ext in ("md", "py"):
            git(self.src, "mv", "docs/upgrades/upgrade-next." + ext, "docs/upgrades/upgrade-9.9.9." + ext)
        git(self.src, "commit", "-q", "-m", "the guide of 9.9.9")
        shutil.rmtree(self.scratch)
        rc, out, err = self.publish()
        self.assertEqual(rc, 0, err + out)
        self.assertIn("\nguide: docs/upgrades/upgrade-9.9.9.md, docs/upgrades/upgrade-9.9.9.py\n", out)

    @unittest.skipUnless(os.name == "nt", "Git for Windows' sh")
    def test_finds_git_for_windows_sh_off_path(self):
        which = coord.shutil.which
        coord.shutil.which = lambda name: None
        try:
            sh, extra = coord.find_sh()
        finally:
            coord.shutil.which = which
        self.assertTrue(sh.lower().endswith(os.path.join("usr", "bin", "sh.exe")), sh)
        self.assertTrue(os.path.isfile(sh))
        self.assertEqual(extra, os.path.dirname(sh))

    def test_sh_on_path_adds_no_folder(self):
        which = coord.shutil.which
        coord.shutil.which = lambda name: "/usr/bin/sh"
        try:
            self.assertEqual(coord.find_sh(), ("/usr/bin/sh", None))
        finally:
            coord.shutil.which = which

    def test_refuses_a_non_empty_scratch(self):
        write(os.path.join(self.scratch, "x"), "x")
        rc, _, err = self.publish()
        self.assertEqual(rc, 1)
        self.assertIn("not empty", err)

    def test_export_failure_stops_it(self):
        rc, out, err = run("publish", self.scratch, "--version", "0.x", "--summary", "s", "--root", self.src,
                           "--url", self.tpl_remote)
        self.assertEqual(rc, 1)
        self.assertIn("takes a semver", out)
        self.assertFalse(os.path.exists(os.path.join(self.scratch, "tpl")))


class TemplateAddress(unittest.TestCase):
    """#23: the Template's address is tools/upgrade.py's URL, not a copy of it."""

    def test_template_url_is_upgrade_url(self):
        self.assertTrue(os.path.samefile(coord.upgrade.__file__, os.path.join(REPO, "tools", "upgrade.py")))
        self.assertEqual(coord.TEMPLATE_URL, coord.upgrade.URL)
        with open(os.path.join(HERE, "..", "coord.py"), encoding="utf-8") as f:
            tree = ast.parse(f.read())
        literals = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        self.assertFalse([s for s in literals if "career-log-template" in s], "coord.py writes the address out")


class OneExportRunner(unittest.TestCase):
    """#18: coord.export runs tools/export-template.sh for every maintainer tool, and
    coord.exported_from writes the line naming the source repo; a copy of either outside coord fails,
    printing the file, the line and the function to call instead."""

    ALLOWED = {"runner": ("coord.py", "export"), "line": ("coord.py", "exported_from")}
    # Runs of the export that rightly stay by hand, by file and source line
    BY_HAND = {
        # harness.py's template-copy exports a scratch worktree with no --version, by bash with the
        # script's full path, for a test Log: neither a release nor a Dev build, and no message
        ("harness.py", 'p = run([bash(), os.path.join(worktree, "tools", "export-template.sh"), slashed(export)], '
                       'cwd=worktree, check=False)'),
    }
    # The repo's name as a word of its own: a URL's path (".../career-log-engine") is no such line
    REPO_NAME = re.compile(r"(?<![\w/-])career-log-engine(?![\w-])")

    def scan(self, name, source):
        """[(line, what, owner, text)] for each string, docstrings aside, that names the export script
        (alone or as a path) or that writes the source line, owner the function it is in (None at module
        level), text its source line."""
        hits = []
        tree = ast.parse(source, name)
        lines = source.splitlines()
        docs = {id(n.body[0].value) for n in ast.walk(tree)
                if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}

        def walk(node, owner):
            for child in ast.iter_child_nodes(node):
                inner = child.name if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else owner
                if isinstance(child, ast.Constant) and isinstance(child.value, str) and id(child) not in docs:
                    what = ("runner" if child.value.endswith("export-template.sh") else
                            "line" if "Exported from" in child.value or self.REPO_NAME.search(child.value) else None)
                    if what:
                        hits.append((child.lineno, what, owner, lines[child.lineno - 1].strip()))
                walk(child, inner)

        walk(tree, None)
        return hits

    def copies(self, name, source):
        """(the copies outside coord's two functions, the BY_HAND entries seen)"""
        found, seen = [], set()
        for line, what, owner, text in self.scan(name, source):
            if (name, text) in self.BY_HAND:
                seen.add((name, text))
            elif (name, owner) != self.ALLOWED[what] and not (name == "coord.py" and owner is None):
                found.append("%s:%d: %s; call coord.%s instead" % (name, line, text, self.ALLOWED[what][1]))
        return found, seen

    def test_no_maintainer_tool_runs_the_export_or_writes_the_line_by_hand(self):
        found, seen = [], set()
        folder = os.path.join(HERE, "..")
        for name in sorted(os.listdir(folder)):
            if name.endswith(".py"):
                more, also = self.copies(name, read(os.path.join(folder, name)))
                found += more
                seen |= also
        self.assertEqual(found, [])
        self.assertEqual(sorted(self.BY_HAND - seen), [], "BY_HAND lists a run that is gone: drop it")

    def test_the_guard_reads_each_copy(self):
        copied = ('def export(root, version, out):\n'
                  '    subprocess.run([sh, "tools/export-template.sh", "--version", version, out])\n'
                  '    subprocess.run([sh, os.path.join(root, "tools", "export-template.sh"), out])\n'
                  'def build():\n'
                  '    message = "Dev build\\n\\nExported from career-log-engine %s\\n" % source\n'
                  '    tag = "Dev build of career-log-engine %s" % source\n'
                  '    url = "https://github.com/owner/career-log-engine"\n')
        found, _ = self.copies("devbuild.py", copied)
        self.assertEqual([l.split(":")[1] for l in found], ["2", "3", "5", "6"])
        self.assertIn("call coord.export instead", found[1])
        self.assertIn("call coord.exported_from instead", found[2])

    def test_the_line_names_this_repo(self):
        self.assertEqual(coord.SOURCE_REPO, "career-log-engine")
        self.assertEqual(coord.exported_from("abc"), "Exported from career-log-engine abc")


if __name__ == "__main__":
    unittest.main()
