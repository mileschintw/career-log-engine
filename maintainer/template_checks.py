#!/usr/bin/env python3
"""Run the checks the Template ships in a fresh export of this repo's HEAD, as a Template user or a
Log runs them (#33): a check that reads a file only the Template's source has fails here before a
release.

  python3 -I maintainer/template_checks.py [--jobs <n>]      (Windows: py -3 -I ...)

It exports HEAD with tools/export-template.sh into a temporary folder, makes that folder a git repo
of one commit (what "Use this template" makes), then runs, from there, tools/skill_lint.py and every
tools/tests/test_*.py side by side (--jobs at a time, default one per CPU). For each, in that order:
`ok:` or `FAIL:`, its seconds, its command and its last line, and a failure's last 40 lines. Then
a `ran <n> checks` line, and last `OK`, or `FAIL: <n> of <m> failed`. A test skips what only the
source has (maintainer/, upgrade-next.*, the workflows): that is the `skipped=` count in its line.
Uncommitted edits are not exported: commit first.

Exit 0 when every check passed, 1 when one failed or the export did, 2 on a bad argument. Standard
library only, Python 3.11+. The temporary folder is removed at the end.
"""
import argparse, glob, os, shutil, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:   # -I leaves the script's folder off sys.path, and this is not tools/
    sys.path.insert(0, TOOLS)
sys.dont_write_bytecode = True
import checks_for

LINT = "tools/skill_lint.py"


def git(cwd, *args):
    subprocess.run(["git", "-C", cwd, "-c", "core.autocrlf=false", *args], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def export(scratch):
    """The exported Template's folder, a git repo of one commit; raises RuntimeError on a failure."""
    out = scratch + "/template"
    ok, _, text = checks_for.run_one(checks_for.sh("sh tools/export-template.sh <scratch>/template", ""), ROOT,
                                     scratch, checks_for.find_sh())
    lines = text.rstrip().splitlines()
    for line in lines:
        if line.startswith("note:"):
            print(line, flush=True)
    if not ok:
        raise RuntimeError("the export failed:\n" + "\n".join("  | " + l for l in lines[-40:]))
    try:
        git(out, "init", "-q", "-b", "main")
        git(out, "add", "-A")
        git(out, "-c", "user.name=Template checks", "-c", "user.email=template-checks@example.com",
            "commit", "-q", "-m", "Initial commit")
    except subprocess.CalledProcessError as e:
        raise RuntimeError("git in the export: %s" % (e.stderr or b"").decode("utf-8", "replace").strip())
    return out


def rmtree(path):
    """shutil.rmtree that also removes git's read-only object files on Windows."""
    def retry(func, p, _):
        os.chmod(p, 0o700)
        func(p)
    shutil.rmtree(path, onerror=retry)


def scripts(template):
    """The lint, then every test the export ships, as repo-relative paths."""
    tests = sorted(os.path.relpath(p, template).replace(os.sep, "/")
                   for p in glob.glob(os.path.join(template, "tools", "tests", "test_*.py")))
    return [LINT] + tests


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 1, help="checks at a time (default: CPUs)")
    args = ap.parse_args(argv)
    scratch = tempfile.mkdtemp(prefix="template_checks-").replace("\\", "/")
    start, failed = time.monotonic(), 0
    try:
        try:
            template = export(scratch)
        except RuntimeError as e:
            print("FAIL: %s" % e)
            return 1
        found = [checks_for.py(s) for s in scripts(template)]
        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            futures = [(c, pool.submit(checks_for.run_one, c, template, scratch, (None, None))) for c in found]
            for c, f in futures:
                ok, secs, out = f.result()
                lines = out.rstrip().splitlines() or ["(no output)"]
                print("%s %4.0fs %s: %s" % ("ok:  " if ok else "FAIL:", secs, checks_for.command(c), lines[-1].strip()))
                if not ok:
                    failed += 1
                    print("\n".join("      | " + l for l in lines[-40:]))
                sys.stdout.flush()
        print("ran %d checks in an export of HEAD in %.0fs" % (len(found), time.monotonic() - start))
        print("FAIL: %d of %d failed" % (failed, len(found)) if failed else "OK")
        return 1 if failed else 0
    finally:
        rmtree(scratch)


if __name__ == "__main__":
    sys.exit(main())
