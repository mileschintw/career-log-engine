#!/usr/bin/env python3
"""The maintainer's steps that write: blocked-by marks on GitHub and a Template release's staging.
Run a subcommand, then follow what it prints.

  python3 -I maintainer/coord.py block <issue> <blocker>... [--repo <owner/name>] [--dry-run]
  python3 -I maintainer/coord.py publish <scratch> --version <semver> --summary <text> [--root <root>]
                                 [--url <template repo>]
(Windows: py -3 -I ...). --root defaults to the repository this script is in.

block    marks <issue> as blocked by each <blocker> on GitHub (the hard dependencies,
         docs/agents/issue-tracker.md › Blocking), skipping blockers already listed, then lists them
         again. --dry-run prints the `gh api` calls that would write and writes nothing. --repo
         defaults to the repository `gh` finds from the current folder. Refuses (1) when <issue>
         already lists a blocker in another repository.
publish  stages a Template release (docs/publishing.md, the export, clone, copy and `git add -A`
         steps) in <scratch>: exports --version to <scratch>/export, clones --url (default the public
         Template) to <scratch>/tpl, replaces everything in it but .git with the export and stages
         it with the exported commit's file modes (a copy on Windows loses the executable bit; it
         fails if the index's 100755 paths differ from that commit's), then prints the staged diff's
         summary, the 100755 paths and `guide:` (docs/upgrades/upgrade-<version>.* when the export
         holds them, else `none`), and writes the release commit's message to
         <scratch>/commit-message.txt. The export refuses while docs/upgrades/upgrade-next.* holds
         a Log format change or a new setting (docs/publishing.md step 1 renames them to
         upgrade-<version>.*). It never commits or pushes: reviewing, testing, committing and
         the Release stay the agent's, on the user's yes. <scratch> must be empty or missing.
Exit 0 when done, 1 when a check fails (the reason on stderr), 2 on a usage error.
Standard library only, Python 3.11+.
"""
import argparse, json, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))   # -I leaves it off sys.path
import upgrade   # noqa: E402

TEMPLATE_URL = upgrade.URL   # the Template's one address, which tools/skill_lint.py checks the others against
# The repo an export is made from, as a release's and a Dev build's messages name it (ADR 0015)
SOURCE_REPO = "career-log-engine"


class Fail(Exception):
    pass


def git(cwd, *args, check=True):
    p = subprocess.run(["git", "-c", "core.quotePath=false", "-C", cwd, *args], capture_output=True, encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise Fail("git %s: %s" % (" ".join(args), (p.stderr or p.stdout).strip()))
    return p.stdout.strip()


def find_sh():
    """(sh, extra PATH folder) for tools/export-template.sh: the sh on PATH (no extra folder), else Git for
    Windows' own with its folder, which holds the grep and sed the script calls (never WSL's bash)."""
    found = shutil.which("sh")
    if found:
        return found, None
    if os.name == "nt":
        exec_path = git(os.getcwd(), "--exec-path", check=False)   # <Git>/mingw64/libexec/git-core
        if exec_path:
            sh = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(exec_path))), "usr", "bin", "sh.exe")
            if os.path.isfile(sh):
                return sh, os.path.dirname(sh)
    raise Fail("no sh found to run tools/export-template.sh (on Windows it comes with Git for Windows)")


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def read(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read()


def gh_cli(args):
    """Run gh; return its stdout, or raise RuntimeError with its message."""
    try:
        p = subprocess.run(["gh"] + args, capture_output=True, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise RuntimeError("gh not found")
    if p.returncode != 0:
        lines = (p.stderr or p.stdout).strip().splitlines()
        raise RuntimeError(lines[-1] if lines else "gh exited %d" % p.returncode)
    return p.stdout


# --- block ----------------------------------------------------------------------------------------

def blocked_by(run, repo, n):
    """The issue numbers GitHub lists as blocking issue n; raises for one in another repository."""
    # One page: GitHub allows far fewer than 100 blockers per issue.
    out, other = set(), []
    try:
        listed = json.loads(run(["api", "repos/%s/issues/%d/dependencies/blocked_by?per_page=100" % (repo, n)]))
    except ValueError as e:
        raise RuntimeError("gh printed no JSON: %s" % e)
    for i in listed:
        r = (i.get("repository_url") or "").split("/repos/", 1)[-1]
        if r and r.lower() != repo.lower():
            other.append("%s#%d" % (r, i["number"]))
        else:
            out.add(i["number"])
    if other:
        raise RuntimeError("blocked by an issue in another repository: %s" % ", ".join(other))
    return sorted(out)


def cmd_block(a, run):
    repo = a.repo or run(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]).strip()
    blockers = sorted(set(a.blockers))
    if a.issue in blockers:
        raise Fail("#%d cannot block itself" % a.issue)
    try:
        listed = blocked_by(run, repo, a.issue)
    except RuntimeError as e:
        raise Fail("blocked-by lookup for #%d failed: %s" % (a.issue, e))
    for b in blockers:
        if b in listed:
            print("#%d is already blocked by #%d" % (a.issue, b))
            continue
        post = ["api", "-X", "POST", "repos/%s/issues/%d/dependencies/blocked_by" % (repo, a.issue),
                "-F", "issue_id=<id of #%d>" % b]
        if a.dry_run:
            print("would run: gh api repos/%s/issues/%d -q .id" % (repo, b))
            print("would run: gh %s" % " ".join(post))
            continue
        try:
            issue_id = run(["api", "repos/%s/issues/%d" % (repo, b), "-q", ".id"]).strip()
            if not issue_id.isdigit():
                raise RuntimeError("no id for #%d: %r" % (b, issue_id))
            post[-1] = "issue_id=" + issue_id
            run(post)
        except RuntimeError as e:
            raise Fail("marking #%d blocked by #%d failed: %s" % (a.issue, b, e))
        print("marked #%d blocked by #%d" % (a.issue, b))
    if a.dry_run:
        return
    try:
        now_listed = blocked_by(run, repo, a.issue)
    except RuntimeError as e:
        raise Fail("re-reading #%d's blockers failed: %s" % (a.issue, e))
    missing = [b for b in blockers if b not in now_listed]
    print("#%d is blocked by: %s" % (a.issue, ", ".join("#%d" % n for n in now_listed) or "none"))
    if missing:
        raise Fail("GitHub does not list %s as blocking #%d" % (", ".join("#%d" % n for n in missing), a.issue))


# --- publish --------------------------------------------------------------------------------------

def exported_from(source):
    """The line a release's commit message and a Dev build's end with."""
    return "Exported from %s %s" % (SOURCE_REPO, source)


def export(root, version, out):
    """Run tools/export-template.sh --version <version> <out> from root, passing its output on: for
    publish here and for devbuild.py."""
    sh, extra = find_sh()
    env = dict(os.environ, PATH=extra + os.pathsep + os.environ.get("PATH", "")) if extra else None
    p = subprocess.run([sh, "tools/export-template.sh", "--version", version, out], cwd=root, env=env,
                       capture_output=True, encoding="utf-8", errors="replace")
    sys.stdout.write(p.stdout)
    if p.returncode != 0:
        raise Fail("tools/export-template.sh failed (exit %d): %s" % (p.returncode, (p.stderr or "").strip()))


def index_modes(repo, *args):
    """{path: mode} from `git ls-files -s` (args empty) or `git ls-tree -r <commit>`."""
    out = git(repo, *(args or ("ls-files", "-s"))).splitlines()
    return {l.split("\t", 1)[1]: l.split()[0] for l in out if "\t" in l}


def set_modes(root, source, tpl):
    """Give tpl's index the file modes of the exported commit: a copy on Windows (core.fileMode false)
    stages a new file as 100644 and keeps an existing one's old mode. Returns the 100755 paths."""
    staged = index_modes(tpl)
    want = set()
    for path, mode in index_modes(root, "ls-tree", "-r", source).items():
        if mode != "100755":
            continue
        # the export holds tools/template/<path> twice: as itself and, from the skeleton, as <path>
        for p in (path, path[len("tools/template/"):] if path.startswith("tools/template/") else None):
            if p and p in staged:
                want.add(p)
    plus = sorted(p for p in want if staged[p] != "100755")
    minus = sorted(p for p, m in staged.items() if m == "100755" and p not in want)
    if plus:
        git(tpl, "update-index", "--chmod=+x", "--", *plus)
    if minus:
        git(tpl, "update-index", "--chmod=-x", "--", *minus)
    got = sorted(p for p, m in index_modes(tpl).items() if m == "100755")
    if got != sorted(want):
        raise Fail("tpl's index has 100755 on %s, not on %s" % (", ".join(got) or "nothing", ", ".join(sorted(want))))
    return got


def cmd_publish(a):
    scratch = os.path.abspath(a.scratch)
    if os.path.exists(scratch) and os.listdir(scratch):
        raise Fail("%s exists and is not empty" % scratch)
    find_sh()   # no sh: stop before the scratch folder is made
    os.makedirs(scratch, exist_ok=True)
    out, tpl = os.path.join(scratch, "export"), os.path.join(scratch, "tpl")
    export(a.root, a.version, out)
    p = subprocess.run(["git", "clone", "-q", a.url, tpl], capture_output=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise Fail("git clone %s failed: %s" % (a.url, p.stderr.strip()))
    for name in os.listdir(tpl):
        if name != ".git":
            path = os.path.join(tpl, name)
            shutil.rmtree(path) if os.path.isdir(path) and not os.path.islink(path) else os.remove(path)
    shutil.copytree(out, tpl, dirs_exist_ok=True, symlinks=True)
    git(tpl, "add", "-A")
    lines = read(os.path.join(tpl, "tools", "TEMPLATE_VERSION")).splitlines()
    if not lines or lines[0].strip() != a.version:
        raise Fail("tpl/tools/TEMPLATE_VERSION says %r, not %s" % (lines[:1], a.version))
    source = next((l.split()[1] for l in lines if l.startswith("source ") and len(l.split()) > 1), None)
    if not source:
        raise Fail("tpl/tools/TEMPLATE_VERSION names no source commit")
    executable = set_modes(a.root, source, tpl)
    message = os.path.join(scratch, "commit-message.txt")
    write_text(message, "Release %s: %s\n\n%s\n" % (a.version, a.summary, exported_from(source)))
    print(git(tpl, "diff", "--cached", "--stat") or "(no change staged)")
    print("executable (100755): %s" % (", ".join(executable) or "none"))
    guide = sorted("docs/upgrades/" + n for n in os.listdir(os.path.join(tpl, "docs", "upgrades"))
                   if n.startswith("upgrade-%s." % a.version))
    print("guide: %s" % (", ".join(guide) or "none"))
    print("\nstaged in %s; commit message in %s" % (tpl, message))
    print("next (docs/publishing.md): review `git -C %s diff --cached` (Engine and skeleton only, nothing "
          "from the Log); test a release with a guide; on the user's yes, `git -C %s commit -F %s`, push "
          "to main and publish the Release, the `guide:` files as its assets." % (tpl, tpl, message))


def main(argv=None, run=gh_cli):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("block", help="mark an issue blocked by others on GitHub")
    s.add_argument("issue", type=int)
    s.add_argument("blockers", type=int, nargs="+")
    s.add_argument("--repo", help="owner/name; default: the repository gh finds from here")
    s.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("publish", help="stage a Template release in a scratch folder")
    s.add_argument("scratch")
    s.add_argument("--version", required=True)
    s.add_argument("--summary", required=True)
    s.add_argument("--root", default=ROOT)
    s.add_argument("--url", default=TEMPLATE_URL)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "block":
            cmd_block(a, run)
        else:
            cmd_publish(a)
    except (Fail, OSError, RuntimeError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
