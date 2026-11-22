#!/usr/bin/env python3
"""Make a Dev build: the export of the commit checked out here, committed to a builds branch that
holds exports only, and tagged v<next version>-dev.<n> (docs/publishing.md › Dev builds).

  python3 -I maintainer/devbuild.py <dest> [--root <root>] [--releases <repo>] [--branch <name>]
                                    [--push <remote>]
(Windows: py -3 -I ...). --root defaults to the repository this script is in.

<dest>       the repository the build goes into: this repo's own checkout in CI (dev-build.yml), a
             scratch repository for a build of an unmerged commit (made with `git init` when missing).
--releases   where the release tags vX.Y.Z live (default: the public Template); its tags and <dest>'s
             own are read, and the highest is the latest release. Without --push, each of its
             release tags <dest> lacks is fetched into <dest>, so a Log can upgrade from <dest>
             alone (`--url <dest>`).
--branch     the builds branch in <dest> (default `builds`). Its first commit has no parent, so it
             shares no history with any other branch; each later build's parent is the build before.
--push       after the tag is made, push the builds branch and the tag to <remote> of <dest>, in one
             atomic push.

The next version is the release after the latest: its minor when docs/upgrades/upgrade-next.md at the
source commit holds a Log format change (its `## Changes` no longer says `No Log format change yet.`),
else its patch (docs/publishing.md › Publishing a release). <n> is one more than the highest
v<next>-dev.<n> tag in <dest>, 1 when there is none, so it starts at 1 after each release. The export
runs with --version <next>-dev.<n>, which does not refuse a next guide that holds a change and ships
it as it stands. The build's tree is the export as it is, its file modes from the source commit. It
writes only the builds branch, the tag and the release tags it fetches into <dest>: never its
checked-out branch or work tree, and --push sends only the branch and the Dev build's tag. The
build's commit ends `Exported from career-log-engine <source>`, as a release's does (coord.py). Its
commit and tag carry <dest>'s git identity (user.name, user.email); with none, it stops first.
Prints the release tags it fetched, `dev build: v<version>`, its commit and its source, and the push
command when --push is not given. Exit 0 when done, 1 when a check fails (the reason on stderr), 2 on a usage error.
Standard library only, Python 3.11+.
"""
import argparse, importlib.util, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("coord", os.path.join(HERE, "coord.py"))
coord = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coord)
Fail, git = coord.Fail, coord.git

RELEASE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
NO_CHANGE = "No Log format change yet."
NEXT_GUIDE = "docs/upgrades/upgrade-next.md"


def release_tags(names):
    """The (major, minor, patch) of each release tag vX.Y.Z in names."""
    return [tuple(int(n) for n in m.groups()) for m in map(RELEASE.match, names) if m]


def remote_tags(url):
    p = subprocess.run(["git", "ls-remote", "--tags", "--refs", url], capture_output=True, encoding="utf-8",
                       errors="replace")
    if p.returncode != 0:
        raise Fail("git ls-remote --tags %s: %s" % (url, (p.stderr or p.stdout).strip()))
    return [l.split("refs/tags/", 1)[1] for l in p.stdout.splitlines() if "refs/tags/" in l]


def next_version(latest, format_change):
    major, minor, patch = latest
    return "%d.%d.0" % (major, minor + 1) if format_change else "%d.%d.%d" % (major, minor, patch + 1)


def holds_format_change(root, source):
    p = subprocess.run(["git", "-C", root, "show", "%s:%s" % (source, NEXT_GUIDE)], capture_output=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        return False   # no next guide: nothing pending
    return NO_CHANGE not in (l.strip() for l in p.stdout.splitlines())


def dev_number(tags, version):
    want = re.compile(r"^v%s-dev\.([1-9]\d*)$" % re.escape(version))
    return max([int(m.group(1)) for m in map(want.match, tags) if m], default=0) + 1


def bring_releases(dest, url, url_tags, dest_tags):
    """Fetch into dest each release tag vX.Y.Z of url that dest does not have, so that a Log can
    upgrade with dest as its one --url: the plan reads the releases and the Log's own version there
    (#19). A tag dest has already stays as it is. Returns the tags fetched."""
    want = [n for n in url_tags if RELEASE.match(n) and n not in dest_tags]
    if want:
        git(dest, "-c", "maintenance.auto=false", "-c", "gc.auto=0", "fetch", "-q", "--no-tags", url,
            *("refs/tags/%s:refs/tags/%s" % (n, n) for n in want))
    return want


def rmtree(path):
    """shutil.rmtree that also removes git's read-only object files on Windows, and takes a file
    already gone (removed by a git process still running there) as removed."""
    def retry(func, p, exc):
        if isinstance(exc, FileNotFoundError) or (isinstance(exc, tuple) and exc[0] is FileNotFoundError):
            return
        try:
            os.chmod(p, 0o700)
            func(p)
        except FileNotFoundError:
            pass
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=retry)
    else:
        shutil.rmtree(path, onerror=retry)


def stage_tree(root, source, out, stage):
    """The export's tree, written in a scratch repository at stage with the source commit's file modes."""
    git(os.path.dirname(stage), "init", "-q", stage)
    git(stage, "config", "core.autocrlf", "false")
    shutil.copytree(out, stage, dirs_exist_ok=True, symlinks=True)
    git(stage, "add", "-A", "-f")   # -f: the export's own .gitignore does not drop a file from it
    coord.set_modes(root, source, stage)
    return git(stage, "write-tree")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dest")
    ap.add_argument("--root", default=coord.ROOT)
    ap.add_argument("--releases", default=coord.TEMPLATE_URL)
    ap.add_argument("--branch", default="builds")
    ap.add_argument("--push", metavar="REMOTE")
    a = ap.parse_args(argv)
    try:
        build(a)
    except (Fail, OSError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


def build(a):
    root, dest = os.path.abspath(a.root), os.path.abspath(a.dest)
    if not os.path.exists(dest) or not os.listdir(dest):
        os.makedirs(dest, exist_ok=True)
        git(dest, "init", "-q")
    top = git(dest, "rev-parse", "--show-toplevel", check=False)
    if not top or os.path.normcase(os.path.realpath(top)) != os.path.normcase(os.path.realpath(dest)):
        raise Fail("%s is not the top of a git repository's work tree" % dest)
    ref = "refs/heads/" + a.branch
    if git(dest, "symbolic-ref", "-q", "HEAD", check=False) == ref:
        raise Fail("%s has %s checked out; a Dev build never writes the checked-out branch" % (dest, a.branch))
    for who in ("GIT_AUTHOR_IDENT", "GIT_COMMITTER_IDENT"):   # the build's commit and tag are made in dest
        if subprocess.run(["git", "-C", dest, "var", who], capture_output=True).returncode != 0:
            raise Fail("no git identity in %s for the build's commit and tag: set user.name and user.email "
                       "(git -C %s config user.name ...), as dev-build.yml does" % (dest, dest))
    source = git(root, "rev-parse", "HEAD")
    dest_tags = git(dest, "tag", "-l").splitlines()
    # a local path, as git reads it from dest's folder as well as from here
    url = os.path.abspath(a.releases) if os.path.exists(a.releases) else a.releases
    url_tags = remote_tags(url)
    releases = release_tags(dest_tags) + release_tags(url_tags)
    if not releases:
        raise Fail("no release tag vX.Y.Z in %s or %s: a Dev build is of the release after one" % (a.releases, dest))
    version = next_version(max(releases), holds_format_change(root, source))
    version += "-dev.%d" % dev_number(dest_tags, version)
    tag = "v" + version
    parent = git(dest, "rev-parse", "-q", "--verify", ref + "^{commit}", check=False) or None
    tmp = tempfile.mkdtemp()
    try:
        out, stage = os.path.join(tmp, "export"), os.path.join(tmp, "stage")
        coord.export(root, version, out)
        tree = stage_tree(root, source, out, stage)
        carrier = git(stage, "-c", "user.name=devbuild", "-c", "user.email=devbuild@localhost",
                      "commit-tree", tree, "-m", "export")   # only carries the tree to dest
        git(stage, "update-ref", "refs/heads/export", carrier)
        # no automatic maintenance: a fetch starts `git maintenance run --auto`, whose gc detaches and
        # can still be repacking dest when the command returns
        git(dest, "-c", "maintenance.auto=false", "-c", "gc.auto=0", "fetch", "-q", "--no-tags", stage,
            "refs/heads/export")
    finally:
        rmtree(tmp)
    # a build kept here is upgraded to from here alone; one pushed (CI's) is upgraded to from where it
    # is pushed, with the releases from the Template, so it needs none here
    brought = [] if a.push else bring_releases(dest, url, url_tags, dest_tags)
    message = "Dev build %s\n\n%s\n" % (version, coord.exported_from(source))
    commit = git(dest, "commit-tree", tree, *(["-p", parent] if parent else []), "-m", message)
    git(dest, "update-ref", "-m", "dev build " + version, ref, commit, parent or "")   # "": must not exist yet
    git(dest, "tag", "-a", tag, "-m", "Dev build %s of %s %s" % (version, coord.SOURCE_REPO, source), commit)
    if brought:
        print("release tags from %s: %s" % (a.releases, ", ".join(brought)))
    print("dev build: %s" % tag)
    print("commit: %s on %s" % (commit, a.branch))
    print("source: %s" % source)
    push = ["push", "--atomic", a.push or "origin", ref, "refs/tags/" + tag]
    if a.push:
        git(dest, *push)
        print("pushed %s and %s to %s" % (a.branch, tag, a.push))
    else:
        print("to publish it: git -C %s %s" % (dest, " ".join(push)))


if __name__ == "__main__":
    sys.exit(main())
