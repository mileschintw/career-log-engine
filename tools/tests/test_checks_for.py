#!/usr/bin/env python3
"""Tests for tools/checks_for.py: the checks it prints for typical changes, the changed paths it
reads from git, and, in the Template's source, that each workflow in .github/workflows/ runs on
the same `paths:` and the same steps as its groups in GROUPS together (skipped in a Template, which
has none).

  python3 -I tools/tests/test_checks_for.py

The parity test compares the steps that run a test or a script: `python -I <script>`,
`sh -n <script>`, the PowerShell parse of `Resolve-Path <script>`, and tools/export-template.sh,
and fails on a run: line naming python, sh or the like in any other form, and on a path filter
other than `paths:` under `pull_request:`.

EveryImport (#52) reads each py check's imports with ast, through every repo module they reach:
import statements anywhere in a file (resolved beside it, then in tools/), and modules loaded by
path or name (spec_from_file_location, import_module, __import__) whose argument it can tell. It
fails on a module no group running the check has among its triggers (LEFT_OUT lists the rightful
exceptions), or that their workflows' paths: lack. Standard and third-party modules, a script run
as a subprocess, and a file loaded from a path it cannot tell (a scratch Log's copy) are left out.
"""
import ast, contextlib, importlib.util, io, os, re, shutil, subprocess, sys, tempfile, time, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
REPO = os.path.dirname(TOOLS)
WORKFLOWS = os.path.join(REPO, ".github", "workflows")
# The Template's source: a Template or a Log has no maintainer/, and so none of its checks (#33)
SOURCE = os.path.isdir(os.path.join(REPO, "maintainer"))
# closing-refs.yml runs on every pull request with a closing keyword, not on paths; dev-build.yml on
# each push to master, its test in coord-tests.yml
NO_PATHS = {"closing-refs.yml", "dev-build.yml"}

spec = importlib.util.spec_from_file_location("checks_for", os.path.join(TOOLS, "checks_for.py"))
checks_for = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks_for)

STEP = re.compile(r"(?:python3?|py -3) -I (\S+\.py)|sh -n (\S+)|Resolve-Path (\S+?)\)|(?:ba)?sh (tools/export-template\.sh)")


def runs(paths):
    """The run: and do: lines for paths, against this repo."""
    return [l for l in checks_for.report(paths, REPO) if l.startswith(("run: ", "do: "))]


def scripts(lines):
    return [next(g for g in m.groups() if g) for l in lines for m in STEP.finditer(l)]


def indent(line):
    return len(line) - len(line.lstrip())


def workflow_paths(text):
    """The `paths:` list under `pull_request:`, or None; and the other path filters (paths: under
    another trigger, paths-ignore:), which the parity test does not read."""
    out, others, trigger = None, [], None
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^(\s+)([\w-]+):\s*$", line)
        if m and indent(line) == 2:
            trigger = m.group(2)
        if re.match(r"^\s+(paths|paths-ignore):", line):
            if trigger != "pull_request" or not re.match(r"^\s+paths:\s*$", line):
                others.append(line.strip())
                continue
            out = []
            for item in lines[i + 1:]:
                if item.lstrip().startswith("#"):
                    continue
                m = re.match(r"""^\s+-\s+["']?([^"'#]+?)["']?\s*$""", item)
                if not m:
                    break
                out.append(m.group(1))
    return out, others


def run_lines(text):
    """Every command line of the workflow's `run:` steps, a block's lines one by one."""
    out, lines = [], text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(\s+)(?:- )?run:\s*(.*)$", line)
        if not m:
            continue
        if m.group(2) not in ("|", ">", "|-", ">-"):
            out.append(m.group(2))
            continue
        for item in lines[i + 1:]:
            if item.strip() and indent(item) <= indent(line):
                break
            if item.strip():
                out.append(item.strip())
    return out


def workflow_steps(text):
    """The scripts the run: steps run, and the lines that look like a check STEP does not read."""
    found, unread = set(), []
    for cmd in (c.strip() for line in run_lines(text) for c in re.split(r"&&|\|\||;", line)):
        got = scripts([cmd])
        found.update(got)
        if not got and re.search(r"\b(python3?|py|pytest|unittest|sh|bash|pwsh)\b", cmd):
            unread.append(cmd)
    return sorted(found), unread


def as_globs(triggers):
    return sorted(t + "**" if t.endswith("/") else t for t in triggers)


def named(names, one, many):
    """`group a has` for one name, `groups a, b have` for more."""
    return "group %s %s" % (names[0], one) if len(names) == 1 else "groups %s %s" % (", ".join(names), many)


def compare(groups, name, text, root=REPO):
    """Problems between the groups that name a workflow and its text; [] when they agree."""
    problems, names = [], [g[0] for g in groups]
    have = {g[0]: set(as_globs(checks_for.triggers(g, root))) for g in groups}
    want = set().union(*have.values())
    got, others = workflow_paths(text)
    problems += ["%s: a path filter the map cannot hold: %s" % (name, o) for o in others]
    if got is None:
        return problems + ["%s: no paths: list under pull_request:" % name]
    for p in sorted(want - set(got)):
        problems.append("%s: paths: lacks %s (%s it)" % (name, p, named([g for g in have if p in have[g]], "has", "have")))
    for p in sorted(set(got) - want):
        problems.append("%s: paths: has %s (%s it)" % (name, p, named(names, "lacks", "lack")))
    checks = [c for g in groups for c in g[3]]
    mine = sorted(set([c[1] for c in checks if c[0] == "py"]
                      + scripts([c[1] for c in checks if c[0] in ("sh", "ps")])))
    steps, unread = workflow_steps(text)
    if steps != mine:
        problems.append("%s: runs %s, %s %s" % (name, steps, named(names, "runs", "run"), mine))
    problems += ["%s: a step the parity test cannot read: %s" % (name, u) for u in unread]
    return problems


def dotted(node):
    """`os.path.join` for the expression os.path.join, None for anything but names and attributes."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        head = dotted(node.value)
        return head and head + "." + node.attr
    return None


def value(node, env, path):
    """A string expression's value, from constants, names in env, `__file__` (path), `+` and
    os.path.join, dirname, abspath, normpath and realpath; None when it needs anything else."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return path if node.id == "__file__" else env.get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        parts = [value(node.left, env, path), value(node.right, env, path)]
        return None if None in parts else parts[0] + parts[1]
    if isinstance(node, ast.Call) and not node.keywords:
        args = [value(a, env, path) for a in node.args]
        if None in args or not args:
            return None
        fn = dotted(node.func)
        if fn == "os.path.join":
            return os.path.join(*args)
        if fn == "os.path.dirname" and len(args) == 1:
            return os.path.dirname(args[0])
        if fn in ("os.path.abspath", "os.path.normpath", "os.path.realpath") and len(args) == 1:
            return os.path.normpath(args[0])
    return None


def loaded(rel, root=REPO):
    """The repo modules the Python file rel (repo-relative) loads itself, as repo-relative paths:
    those its import statements name (anywhere in the file), resolved in its own folder, then in
    tools/, where every file that imports a tool puts it on sys.path; and those it loads by path or
    by name: importlib.util.spec_from_file_location, importlib.import_module and __import__, whose
    argument value() can tell, a helper's parameter taking each constant its calls in the file pass.
    Anything else, a standard or third-party module included, is not a repo module and is left out."""
    path = os.path.join(root, rel)
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), rel)
    env = {}
    for stmt in tree.body:   # the module's constants: HERE, TOOLS, TOOL and the like
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            got = value(stmt.value, env, path)
            if got is not None:
                env.setdefault(stmt.targets[0].id, got)
    calls = {}   # a function's name: the constant positional arguments of each call to it
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute)):
            name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr
            calls.setdefault(name, []).append([value(a, {}, path) for a in node.args])
    paths, names = set(), set()
    for scope in [tree] + [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        envs = [env]
        if scope is not tree:   # each call's constants for the parameters
            params = [a.arg for a in scope.args.posonlyargs + scope.args.args]
            envs += [dict(env, **{p: a for p, a in zip(params, args) if a is not None})
                     for args in calls.get(scope.name, [])]
        nested = [n for n in ast.walk(scope) if n is not scope and isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        inner = {id(m) for n in nested for m in ast.walk(n)}
        for node in ast.walk(scope):
            if id(node) in inner:   # read with the function it is in
                continue
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call) and node.args:
                fn = dotted(node.func) or ""
                if fn.endswith("spec_from_file_location") and len(node.args) > 1:
                    paths.update(value(node.args[1], e, path) for e in envs)
                elif fn == "__import__" or fn.endswith("import_module"):
                    names.update(value(node.args[0], e, path) for e in envs)
    out = set()
    for p in paths - {None}:
        p = os.path.relpath(os.path.normpath(os.path.join(os.path.dirname(path), p)), root).replace("\\", "/")
        if p.endswith(".py") and not p.startswith("../") and os.path.isfile(os.path.join(root, p)):
            out.add(p)
    for n in names - {None}:
        for folder in (os.path.dirname(rel), "tools"):
            p = (folder + "/" if folder else "") + n.split(".")[0] + ".py"
            if os.path.isfile(os.path.join(root, p)):
                out.add(p)
                break
    out.discard(rel)
    return out


def imported(rel, root=REPO):
    """rel and every repo module it loads, directly or through other repo modules (loaded())."""
    seen, todo = set(), [rel]
    while todo:
        p = todo.pop()
        if p not in seen:
            seen.add(p)
            todo += loaded(p, root)
    return seen


# (check, module): a module the check imports that its group's triggers in GROUPS rightly leave out,
# with why; its workflow's paths: still take it. test_the_list_holds_only_gaps fails on a stale entry.
LEFT_OUT = {
    # template_checks.py runs every test again in a fresh export, so only its own script triggers it
    # (#33); a change to either module runs that module's own tests, and template-scan.yml's paths:
    # (the whole export, tools/ included) runs template_checks.py on it in CI
    ("maintainer/template_checks.py", "tools/checks_for.py"): "runs every test again",
    ("maintainer/template_checks.py", "tools/logfiles.py"): "runs every test again",
}


def import_gaps(groups, root=REPO, workflows=None, left_out=LEFT_OUT):
    """#52: each module a py check imports (imported()) that a change to would not run it: one no
    group running that check has among its triggers (GROUPS), unless left_out lists it, or, given
    workflows ({name: text}), none of those groups' workflows has in its paths:. A check whose script
    is not in root (maintainer/ in a Template) is left out. [] when every module is covered."""
    runners = {}
    for g in groups:
        for c in g[3]:
            if c[0] == "py" and checks_for.present(c, root):
                runners.setdefault(c[1], []).append(g)
    problems = []
    for script, gs in sorted(runners.items()):
        names = ", ".join(g[0] for g in gs)
        triggers = [t for g in gs for t in checks_for.triggers(g, root)]
        flows = sorted({g[1] for g in gs if g[1] and workflows and g[1] in workflows})
        paths = [p[:-2] if p.endswith("/**") else p for f in flows for p in workflow_paths(workflows[f])[0] or []]
        for module in sorted(imported(script, root)):
            if (script, module) not in left_out and not any(checks_for.matches(module, t) for t in triggers):
                problems.append("%s imports %s: no group that runs it (%s) has it in tools/checks_for.py GROUPS"
                                % (script, module, names))
            if flows and not any(checks_for.matches(module, p) for p in paths):
                problems.append("%s imports %s: the paths: of %s lack it" % (script, module, ", ".join(flows)))
    return problems


class Typical(unittest.TestCase):
    """The checks for typical changes, as SETUP.md step 7 lists them."""

    def test_one_mode_file(self):
        self.assertEqual(scripts(runs(["skills/career-log/modes/fit.md"])),
                         ["tools/export-template.sh", "tools/tests/test_guide.py",
                          "tools/tests/test_skill_lint.py", "tools/skill_lint.py"])

    def test_modes_the_grader_reads(self):
        got = scripts(runs(["skills/career-log/modes/scan.md"]))
        self.assertIn("tools/tests/test_check_run.py", got)
        self.assertIn("tools/skill_lint.py", got)

    def test_scan(self):
        # check_save.py imports dashboard.py, which imports scan.py; check.py and application.py load
        # check_save.py (#52)
        self.assertEqual(scripts(runs(["tools/scan.py"])),
                         ["tools/export-template.sh", "tools/tests/test_check_run.py", "tools/tests/test_check_save.py",
                          "tools/tests/test_check.py", "tools/tests/test_scan.py", "tools/tests/test_fit.py",
                          "tools/tests/test_dashboard.py", "tools/tests/test_application.py",
                          "tools/tests/test_logfiles.py"])

    def test_entries(self):
        # tools/logfiles.py is imported by every tool tools/entries.py is, and by tools/sync.py and
        # tools/config.py (which test_guide.py and test_upgrade.py load too), tools/resume.py and tools/chat_export.py
        # (which test_perplexity.py loads); test_chat_export.py loads entries.py itself, and
        # maintainer/prepush.py imports deny_coverage.py, which imports both (#52)
        both = ["tools/export-template.sh", "tools/tests/test_chat_export.py", "tools/tests/test_check_run.py",
                "tools/tests/test_check_save.py", "tools/tests/test_deny_coverage.py", "tools/tests/test_logfiles.py",
                "tools/tests/test_entries.py"]
        self.assertEqual(scripts(runs(["tools/entries.py"])), both + [
            "tools/tests/test_check.py", "tools/tests/test_scan.py",
            "tools/tests/test_fit.py", "tools/tests/test_dashboard.py"]
            + (["maintainer/tests/test_prepush.py"] if SOURCE else []) + [
            "tools/tests/test_writing_lint.py", "tools/tests/test_application.py"])
        self.assertEqual(scripts(runs(["tools/logfiles.py"])), both + [
            "tools/tests/test_config.py", "tools/tests/test_check.py", "tools/tests/test_speech.py",   # speech.py imports logfiles (#773)
            "tools/tests/test_resume.py", "tools/tests/test_guide.py", "tools/tests/test_skill_lint.py", "tools/skill_lint.py", "tools/tests/test_scan.py",
            "tools/tests/test_fit.py", "tools/tests/test_dashboard.py", "tools/tests/test_sponsorship.py", "tools/tests/test_perplexity.py",
            "tools/tests/test_upgrade.py"]
            + (["maintainer/tests/test_coord.py", "maintainer/tests/test_devbuild.py",   # #52
                "maintainer/tests/test_prepush.py", "maintainer/tests/test_harness.py"] if SOURCE else []) + [
            "tools/tests/test_writing_lint.py", "tools/tests/test_application.py",
            "tools/tests/test_sync.py", "tools/tests/test_checks_for.py"])

    def test_writing_md(self):
        # tools/writing_lint.py reads its word lists from writing.md
        self.assertIn("tools/tests/test_writing_lint.py", scripts(runs(["skills/career-log/writing.md"])))

    def test_template_front_page(self):
        lines = checks_for.report(["tools/template/README.md"], REPO)
        self.assertTrue(any(l.startswith("warn: tools/template/README.md changed but tools/template/README.zh-TW.md")
                            for l in lines))
        self.assertIn("tools/skill_lint.py", scripts(lines))
        both = checks_for.report(list(checks_for.FRONT_PAGES), REPO)
        self.assertFalse(any(l.startswith("warn:") for l in both))

    def test_setup_script(self):
        got = runs(["tools/setup.ps1"])
        self.assertTrue(any(l.startswith("do: run SETUP.md step 5") for l in got))
        self.assertIn("tools/setup.ps1", scripts(got))

    def test_setup_parse_only_for_the_scripts(self):
        self.assertNotIn("tools/setup.sh", scripts(runs(["tools/check.py"])))
        got = runs([".github/workflows/machine-check.yml"])
        self.assertIn("tools/setup.ps1", scripts(got))
        self.assertFalse(any(l.startswith("do: ") for l in got), got)

    def test_chat_export_and_check_run_apart(self):
        # check_run.py imports chat_export.py; chat_export.py imports neither of them
        self.assertEqual(scripts(runs(["tools/check_run.py"]))[1:],
                         ["tools/tests/test_check_run.py", "tools/tests/test_check_save.py", "tools/tests/test_logfiles.py"])
        self.assertEqual(scripts(runs(["tools/tests/fixtures/x.json"])),
                         ["tools/export-template.sh", "tools/tests/test_chat_export.py", "tools/tests/test_logfiles.py"])
        self.assertEqual(scripts(runs(["tools/chat_export.py"]))[:4],
                         ["tools/export-template.sh", "tools/tests/test_chat_export.py",
                          "tools/tests/test_check_run.py", "tools/tests/test_check_save.py"])

    def test_check_run_and_save_imports(self):
        # check_run.py imports fit.py, check_save.py imports sponsorship.py, and dashboard.py inside one function
        for path in ("tools/fit.py", "tools/sponsorship.py", "tools/dashboard.py"):
            got = scripts(runs([path]))
            self.assertIn("tools/tests/test_check_run.py", got, path)
            self.assertIn("tools/tests/test_check_save.py", got, path)

    def test_sync_runs_check_save(self):
        # #732: check_save.py --commit calls tools/sync.py commit
        got = scripts(runs(["tools/sync.py"]))
        self.assertIn("tools/tests/test_sync.py", got)
        self.assertIn("tools/tests/test_check_save.py", got)

    @unittest.skipUnless(SOURCE, "not the Template's source: no maintainer/")
    def test_closing_refs_apart(self):
        self.assertNotIn("maintainer/tests/test_closing_refs.py", scripts(runs(["tools/deny_coverage.py"])))
        got = scripts(runs([".github/workflows/closing_refs.py"]))
        self.assertIn("maintainer/tests/test_closing_refs.py", got)
        self.assertNotIn("maintainer/tests/test_coord.py", got)

    @unittest.skipUnless(SOURCE, "not the Template's source: no maintainer/")
    def test_every_maintainer_tool_runs_both_guards(self):
        # #46: OneExportRunner (test_coord.py) and OneVersionForm (test_devbuild.py) read every
        # maintainer/*.py, so a change to any of them, a new one too, runs both
        names = sorted(n for n in os.listdir(os.path.join(REPO, "maintainer")) if n.endswith(".py"))
        for name in names + ["new_tool.py"]:
            got = scripts(runs(["maintainer/" + name]))
            self.assertIn("maintainer/tests/test_coord.py", got, name)
            self.assertIn("maintainer/tests/test_devbuild.py", got, name)
        # a file in a folder below is no maintainer tool: the hook runs test_prepush.py alone
        self.assertEqual(scripts(runs(["maintainer/hooks/pre-push"])), ["maintainer/tests/test_prepush.py"])

    def test_glob_trigger(self):
        # a trigger's * matches as in a workflow's paths:, within one folder
        self.assertTrue(checks_for.matches("maintainer/x.py", "maintainer/*.py"))
        self.assertFalse(checks_for.matches("maintainer/tests/x.py", "maintainer/*.py"))
        self.assertFalse(checks_for.matches("maintainer/x.pyc", "maintainer/*.py"))
        self.assertFalse(checks_for.matches("maintainerXx.py", "maintainer/*.py"))

    def test_resume(self):
        got = runs(["tools/resume.py"])
        self.assertIn("tools/tests/test_resume.py", scripts(got))
        self.assertIn("tools/tests/test_check.py", scripts(got))
        self.assertIn("tools/tests/test_check_save.py", scripts(got))
        self.assertIn("tools/tests/test_resume.py", scripts(runs(["skills/career-log/examples/resume.tex"])))

    def test_each_command_once_with_its_check(self):
        lines = checks_for.report(["tools/config.py", "tools/check.py"], REPO)
        self.assertEqual(sum(1 for l in lines if l.startswith("run: ") and "test_check.py" in l), 1)
        for i, l in enumerate(lines):
            if l.startswith("run: "):
                self.assertTrue(lines[i + 1].startswith("check: "), lines[i:i + 2])

    def test_guide_write_hint(self):
        lines = checks_for.report(["docs/guide.md"], REPO)
        self.assertTrue(any("tools/guide.py write" in l for l in lines if l.startswith("check: ")))

    def test_nothing_matches(self):
        self.assertEqual(checks_for.report(["profile.md"], REPO), ["not engine: profile.md", "run: none (no check covers these paths)"])


class Kinds(unittest.TestCase):
    """On a root built like the Template's source: the export script, ALLOW's folders, maintainer/."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        for d in ("tools", "skills", "docs/adr", "maintainer"):
            os.makedirs(os.path.join(self.root, d))
        shutil.copy(os.path.join(TOOLS, "export-template.sh"), os.path.join(self.root, "tools"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_kinds(self):
        for path, want in [("tools/entries.py", "engine"), ("docs/guide.md", "engine"),
                           ("docs/social-preview/banner.svg", "engine"), ("docs/social-preview/x.png", "not engine"),
                           ("LICENSE", "engine"), ("maintainer/coord.py", "engine"),
                           ("docs/maintaining-tests.md", "engine"), (".github/workflows/x.yml", "engine"),
                           (".export-deny", "guard"), (".export-cleared", "guard"),
                           ("entries/2024-01-x.md", "not engine"),
                           ("entries/_template.md", "engine"), (".claude/settings.json", "engine"),
                           ("docs/agents/issue-tracker.md", "engine"), (".claude/worktrees/x/a.md", "not engine")]:
            self.assertEqual(checks_for.kind(path, self.root), want, path)

    def test_allow_read_from_the_export(self):
        self.assertIn("docs/guide.md", checks_for.allow(self.root))
        self.assertIn("skills/", checks_for.export_triggers(self.root))


class InATemplate(unittest.TestCase):
    """A root without maintainer/ leaves its checks out; a root without ALLOW is an error."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "tools", "tests"))
        shutil.copy(os.path.join(TOOLS, "export-template.sh"), os.path.join(self.root, "tools"))
        open(os.path.join(self.root, "tools", "tests", "test_entries.py"), "w").close()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_missing_script_left_out(self):
        lines = checks_for.report(["maintainer/coord.py", "tools/tests/test_entries.py"], self.root)
        self.assertFalse(any("test_coord" in l for l in lines))
        self.assertTrue(any("test_entries.py" in l for l in lines if l.startswith("run: ")))

    def test_source_only_engine_paths(self):
        self.assertEqual(checks_for.kind("maintainer/coord.py", self.root), "not engine")
        self.assertEqual(checks_for.kind(".github/workflows/x.yml", self.root), "not engine")
        self.assertEqual(checks_for.kind("LICENSE", self.root), "not engine")   # a Log's comes from the Template

    def test_no_allow(self):
        with open(os.path.join(self.root, "tools", "export-template.sh"), "w") as f:
            f.write("#!/bin/sh\n")
        with self.assertRaises(checks_for.ChecksError):
            checks_for.report(["tools/x.py"], self.root)


class TestNext(unittest.TestCase):
    """A change to upgrade-next.* prints the test-next.sh step only once that script is in the repo."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "tools"))
        os.makedirs(os.path.join(self.root, "docs", "upgrades"))
        shutil.copy(os.path.join(TOOLS, "export-template.sh"), os.path.join(self.root, "tools"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def steps(self):
        return [l for l in checks_for.report(["docs/upgrades/upgrade-next.md"], self.root) if "test-next.sh" in l]

    def test_only_when_present(self):
        self.assertEqual(self.steps(), [])
        open(os.path.join(self.root, "docs", "upgrades", "test-next.sh"), "w").close()
        got = self.steps()
        self.assertEqual(len(got), 1)
        self.assertTrue(got[0].startswith("do: run docs/upgrades/test-next.sh"), got)


class Run(unittest.TestCase):
    """--run: the py and sh checks side by side, each one's result in order, then the rest."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "tools"))
        shutil.copy(os.path.join(TOOLS, "export-template.sh"), os.path.join(self.root, "tools"))
        self.groups = checks_for.GROUPS
        self.write("pass.py", "print('OK')\n")
        self.write("fail.py", "import sys\nprint('boom')\nsys.exit(1)\n")
        self.write("skip.py", "print('OK (skipped=1)')\n")

    def tearDown(self):
        checks_for.GROUPS = self.groups
        shutil.rmtree(self.root, ignore_errors=True)

    def write(self, rel, text):
        with open(os.path.join(self.root, rel), "w", newline="\n") as f:
            f.write(text)

    def run_checks(self, checks, jobs=4):
        checks_for.GROUPS = [("g", None, ["x"], checks)]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = checks_for.run(["x"], self.root, jobs)
        return code, out.getvalue().splitlines()

    def test_results_in_order_and_the_rest_after(self):
        code, lines = self.run_checks([checks_for.py("pass.py"), checks_for.py("fail.py"),
                                       checks_for.py("skip.py", "one skipped"),
                                       ("ps", "$e", "it prints nothing"), checks_for.do("by hand")])
        self.assertEqual(code, 1)
        self.assertEqual(lines[0], "not engine: x")
        self.assertRegex(lines[1], r"^ok: +\d+s \S.* -I pass\.py: OK$")
        self.assertRegex(lines[2], r"^FAIL: +\d+s \S.* -I fail\.py: boom$")
        self.assertEqual(lines[3], "      | boom")
        self.assertRegex(lines[4], r"^ok: .* skip\.py: OK \(skipped=1\)$")
        self.assertEqual(lines[5], "      check: one skipped")
        self.assertTrue(lines[6].startswith("ran 3 checks side by side in "), lines[6])
        self.assertIn("1 failed", lines[6])
        self.assertEqual(lines[7:], ["run: $e", "check: it prints nothing", "do: by hand"])

    def test_all_pass(self):
        code, lines = self.run_checks([checks_for.py("pass.py")])
        self.assertEqual(code, 0)
        self.assertTrue(lines[-1].endswith(": all exited 0"), lines)

    def test_side_by_side(self):
        self.write("slow.py", "import time\ntime.sleep(4)\nprint('OK')\n")
        self.write("slow2.py", "import time\ntime.sleep(4)\nprint('OK')\n")
        start = time.monotonic()
        code, _ = self.run_checks([checks_for.py("slow.py"), checks_for.py("slow2.py")], jobs=2)
        self.assertEqual(code, 0)
        self.assertLess(time.monotonic() - start, 7.5)   # one after the other: 8s and more

    @unittest.skipUnless(checks_for.find_sh()[0], "no sh")
    def test_sh_with_scratch(self):
        self.write("mk.sh", 'mkdir "$1" && echo "note: made $1" && echo OK\n')
        code, lines = self.run_checks([checks_for.sh("sh mk.sh <scratch>/out", "it made the folder")])
        self.assertEqual(code, 0, lines)
        self.assertRegex(lines[1], r"^ok: +\d+s sh mk\.sh <scratch>/out: OK$")
        made = lines[2].strip()[len("note: made "):]
        self.assertTrue(lines[2].startswith("      note: made ") and made.endswith("/out"), lines)
        self.assertFalse(os.path.exists(made))   # the scratch folder is removed

    @unittest.skipUnless(checks_for.find_sh()[0], "no sh")
    def test_scratch_with_a_space(self):
        self.write("mk.sh", '[ $# = 1 ] && mkdir "$1" && echo OK\n')
        spaced = os.path.join(self.root, "a b")
        os.makedirs(spaced)
        real = checks_for.tempfile.mkdtemp
        checks_for.tempfile.mkdtemp = lambda **kw: spaced
        try:
            code, lines = self.run_checks([checks_for.sh("sh mk.sh <scratch>/out", "it made the folder")])
        finally:
            checks_for.tempfile.mkdtemp = real
        self.assertEqual(code, 0, lines)   # mk.sh got one argument

    def test_only_steps_by_hand(self):
        code, lines = self.run_checks([checks_for.do("by hand")])
        self.assertEqual((code, lines), (0, ["not engine: x", "do: by hand"]))

    def test_nothing_to_run(self):
        checks_for.GROUPS = []
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(checks_for.run(["x"], self.root, 1), 0)
        self.assertEqual(out.getvalue().splitlines(), ["not engine: x", "run: none (no check covers these paths)"])


class FromGit(unittest.TestCase):
    def git(self, *args):
        subprocess.run(["git", "-C", self.root] + list(args), check=True, capture_output=True)

    def write(self, rel, text="x\n"):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        self.write("tools/old.py")
        self.write("tools/staged.py")
        self.write("tools/edited.py")
        self.git("add", "-A")
        self.git("commit", "-qm", "base")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_committed_staged_unstaged_untracked_and_renamed(self):
        self.git("mv", "tools/old.py", "tools/new.py")
        self.git("commit", "-qm", "rename")
        self.write("tools/staged.py", "y\n")
        self.git("add", "tools/staged.py")
        self.write("tools/edited.py", "y\n")
        self.write("tools/untracked dir/file.py")
        self.assertEqual(checks_for.changed(self.root, "HEAD~1"),
                         ["tools/edited.py", "tools/new.py", "tools/old.py", "tools/staged.py",
                          "tools/untracked dir/file.py"])

    def test_bad_base(self):
        with self.assertRaises(checks_for.ChecksError):
            checks_for.changed(self.root, "no-such-ref")

    def test_cli(self):
        p = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "checks_for.py"), "--paths", "tools/scan.py"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("engine: tools/scan.py", p.stdout)
        p = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "checks_for.py")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        p = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "checks_for.py"), "--paths", "./tools/scan.py",
                            "entries/2024-\u00e9.md"], capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        out = p.stdout.decode("utf-8")
        self.assertIn("engine: tools/scan.py", out)
        self.assertIn("not engine: entries/2024-\u00e9.md", out)
        p = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "checks_for.py"), "--help"], capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_absolute_paths(self):
        self.assertEqual(checks_for.relative(os.path.join(REPO, "tools", "scan.py"), REPO), "tools/scan.py")
        with self.assertRaises(checks_for.ChecksError):
            checks_for.relative(os.path.dirname(REPO), REPO)


@unittest.skipUnless(os.path.isdir(WORKFLOWS), "no .github/workflows/ (a Template)")
class Parity(unittest.TestCase):
    def test_every_workflow_matches_its_group(self):
        groups = {}
        for g in checks_for.GROUPS:
            if g[1]:
                groups.setdefault(g[1], []).append(g)
        problems = []
        for name in sorted(os.listdir(WORKFLOWS)):
            if not name.endswith(".yml") or name in NO_PATHS:
                continue
            with open(os.path.join(WORKFLOWS, name), encoding="utf-8") as f:
                text = f.read()
            if name not in groups:
                problems.append("%s: no group in tools/checks_for.py GROUPS" % name)
                continue
            problems += compare(groups.pop(name), name, text)
        problems += ["group %s: no .github/workflows/%s" % (g[0], name) for name, gs in groups.items() for g in gs]
        self.assertEqual(problems, [])

    def test_a_changed_workflow_fails(self):
        name = "scan-tests.yml"
        with open(os.path.join(WORKFLOWS, name), encoding="utf-8") as f:
            text = f.read()
        group = [g for g in checks_for.GROUPS if g[1] == name]
        self.assertEqual(compare(group, name, text), [])
        dropped = text.replace('      - "tools/entries.py"\n', "")
        self.assertEqual(compare(group, name, dropped),
                         ["scan-tests.yml: paths: lacks tools/entries.py (groups scan, dashboard have it)"])
        dropped = text.replace('      - "tools/tests/test_dashboard.py"\n', "")
        self.assertEqual(compare(group, name, dropped),
                         ["scan-tests.yml: paths: lacks tools/tests/test_dashboard.py (group dashboard has it)"])
        added = text.replace('      - "tools/scan.py"\n', '      - "tools/scan.py"\n      - "tools/x.py"\n')
        self.assertEqual(compare(group, name, added),
                         ["scan-tests.yml: paths: has tools/x.py (groups scan, dashboard, sponsorship lack it)"])
        self.assertIn("scan-tests.yml: paths: has tools/x.py (group scan lacks it)", compare(group[:1], name, added))
        left_out = text.replace("        run: python -I tools/tests/test_sponsorship.py -v\n", "        run: echo\n")
        self.assertEqual(len(compare(group, name, left_out)), 1)   # one group's step missing
        step = text.replace("tools/tests/test_scan.py -v", "tools/tests/test_other.py -v")
        self.assertEqual(len(compare(group, name, step)), 1)
        for extra in ["python tools/tests/test_other.py -v", "python3 -I -m unittest discover"]:
            more = text.rstrip("\n") + "\n      - name: More\n        run: %s\n" % extra
            self.assertEqual(compare(group, name, more), ["scan-tests.yml: a step the parity test cannot read: " + extra])
        block = text.rstrip("\n") + "\n      - name: More\n        run: |\n          echo hi\n          python -I tools/tests/test_other.py\n"
        self.assertEqual(len(compare(group, name, block)), 1)
        chained = text.replace("tools/tests/test_scan.py -v", "tools/tests/test_scan.py -v && python tools/b.py")
        self.assertEqual(compare(group, name, chained), ["scan-tests.yml: a step the parity test cannot read: python tools/b.py"])
        push = text.replace("  pull_request:\n    paths:", "  pull_request:\n  push:\n    paths:")
        self.assertIn("scan-tests.yml: a path filter the map cannot hold: paths:", compare(group, name, push))


def read_workflows():
    """{name: text} of .github/workflows/*.yml, {} in a Template."""
    if not os.path.isdir(WORKFLOWS):
        return {}
    out = {}
    for name in os.listdir(WORKFLOWS):
        if name.endswith(".yml"):
            with open(os.path.join(WORKFLOWS, name), encoding="utf-8") as f:
                out[name] = f.read()
    return out


class EveryImport(unittest.TestCase):
    """#52: a change to a module runs every check that imports it, directly or through other repo
    modules, locally (GROUPS) and in CI (the workflows' paths:), as #46 and #52 found by hand."""

    def test_every_import_is_a_trigger(self):
        self.assertEqual(import_gaps(checks_for.GROUPS, REPO, read_workflows()), [])

    @unittest.skipUnless(SOURCE, "not the Template's source: no maintainer/")
    def test_the_list_holds_only_gaps(self):
        # each LEFT_OUT entry is still imported and still missing from its groups' triggers
        self.assertEqual(sorted(import_gaps(checks_for.GROUPS, left_out={})),
                         sorted("%s imports %s: no group that runs it (template checks) has it in tools/checks_for.py "
                                "GROUPS" % k for k in LEFT_OUT))

    @unittest.skipUnless(SOURCE, "not the Template's source: no maintainer/")
    def test_a_planted_gap_fails(self):
        # #52 itself: the coord group without tools/logfiles.py, which test_coord.py imports
        def without(group, path):
            return (group[0], group[1], [t for t in group[2] if t != path], group[3])
        groups = [without(g, "tools/logfiles.py") if g[0] == "coord" else g for g in checks_for.GROUPS]
        self.assertEqual(import_gaps(groups), ["maintainer/tests/test_coord.py imports tools/logfiles.py: no group "
                                               "that runs it (coord) has it in tools/checks_for.py GROUPS"])
        flows = read_workflows()
        flows["coord-tests.yml"] = flows["coord-tests.yml"].replace('      - "tools/logfiles.py"\n', "")
        self.assertIn("maintainer/tests/test_prepush.py imports tools/logfiles.py: the paths: of coord-tests.yml lack it",
                      import_gaps(checks_for.GROUPS, REPO, flows))

    def test_a_group_that_runs_it_is_enough(self):
        # test_check.py runs in three groups; the machine check group's triggers cover what it imports
        self.assertIn("tools/upgrade.py", imported("tools/tests/test_check.py"))
        self.assertNotIn("tools/upgrade.py", [t for g in checks_for.GROUPS if g[0] == "config" for t in g[2]])


class ReadsEveryImport(unittest.TestCase):
    """loaded() on a scratch repo: each way a file loads a repo module, and what it leaves out."""

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def write(self, rel, text=""):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def test_each_way(self):
        for name in ("plain", "dotted", "fromed", "nested", "bypath", "helper", "dunder", "bymodule", "near"):
            self.write("tools/%s.py" % name)
        self.write("maintainer/tool.py")
        self.write("tools/tests/test_x.py", "\n".join([
            "import os, sys, json, importlib, importlib.util",
            "import plain, dotted.sub",
            "from fromed import thing",
            "from collections import Counter",
            "HERE = os.path.dirname(os.path.abspath(__file__))",
            "TOOL = os.path.join(HERE, '..', 'bypath.py')",
            "spec = importlib.util.spec_from_file_location('anything', TOOL)",
            "spec = importlib.util.spec_from_file_location('m', os.path.join(HERE, '..', '..', 'maintainer', 'tool.py'))",
            "def load(name):",
            "    return importlib.util.spec_from_file_location(name, os.path.join(HERE, '..', name + '.py'))",
            "def module(name):",
            "    return __import__(name)",
            "helper = load('helper')",
            "dunder = module('dunder')",
            "importlib.import_module('bymodule')",
            "def later():",
            "    import nested",
            "import near",   # tools/tests/near.py first, beside the file
            "spec = importlib.util.spec_from_file_location('gone', os.path.join(HERE, 'nothing.py'))",
            "spec = importlib.util.spec_from_file_location('unknown', os.path.join(somewhere(), 'x.py'))",
            ""]))
        self.write("tools/tests/near.py")
        # json, importlib, collections: not repo modules; nothing.py: no such file; somewhere(): not told
        self.assertEqual(sorted(loaded("tools/tests/test_x.py", self.root)), [
            "maintainer/tool.py", "tools/bymodule.py", "tools/bypath.py", "tools/dotted.py", "tools/dunder.py",
            "tools/fromed.py", "tools/helper.py", "tools/nested.py", "tools/plain.py", "tools/tests/near.py"])

    def test_through_other_modules_and_from_maintainer(self):
        # a maintainer tool puts tools/ on sys.path and imports a tool, which imports another
        self.write("maintainer/tool.py", "import sys\nsys.path.insert(0, 'tools')\nimport a\n")
        self.write("maintainer/tests/test_tool.py",
                   "import importlib.util, os\nHERE = os.path.dirname(os.path.abspath(__file__))\n"
                   "spec = importlib.util.spec_from_file_location('tool', os.path.join(HERE, '..', 'tool.py'))\n")
        self.write("tools/a.py", "import b\n")
        self.write("tools/b.py", "import os\n")
        self.assertEqual(sorted(imported("maintainer/tests/test_tool.py", self.root)),
                         ["maintainer/tests/test_tool.py", "maintainer/tool.py", "tools/a.py", "tools/b.py"])

    def test_a_planted_gap_in_a_scratch_map(self):
        self.write("tools/export-template.sh", 'ALLOW="tools"\n')
        self.write("tools/a.py", "import b\n")
        self.write("tools/b.py")
        self.write("tools/tests/test_a.py",
                   "import importlib.util, os\nHERE = os.path.dirname(os.path.abspath(__file__))\n"
                   "spec = importlib.util.spec_from_file_location('a', os.path.join(HERE, '..', 'a.py'))\n")
        group = ("a", "a-tests.yml", ["tools/a.py", "tools/tests/test_a.py"], [checks_for.py("tools/tests/test_a.py")])
        flow = 'on:\n  pull_request:\n    paths:\n      - "tools/a.py"\n      - "tools/tests/test_a.py"\n'
        self.assertEqual(import_gaps([group], self.root, {"a-tests.yml": flow}), [
            "tools/tests/test_a.py imports tools/b.py: no group that runs it (a) has it in tools/checks_for.py GROUPS",
            "tools/tests/test_a.py imports tools/b.py: the paths: of a-tests.yml lack it"])
        fixed = (group[0], group[1], group[2] + ["tools/b.py"], group[3])
        flow += '      - "tools/b.py"\n'
        self.assertEqual(import_gaps([fixed], self.root, {"a-tests.yml": flow}), [])
        # a folder trigger covers what is under it, in GROUPS and as dir/** in paths:
        folder = (group[0], group[1], ["tools/"], group[3])
        self.assertEqual(import_gaps([folder], self.root, {"a-tests.yml": flow.replace('"tools/a.py"', '"tools/**"')}), [])


if __name__ == "__main__":
    unittest.main()
