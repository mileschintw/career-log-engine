#!/usr/bin/env python3
"""The maintainer's guard before a push to the Engine repo (ADR 0015): refuses commits that carry a
name from the deny list of the maintainer's own Log (its .export-deny).

  python3 -I maintainer/prepush.py scan --deny <file> <revision>...
  python3 -I maintainer/prepush.py hook <remote> [<url>]       (git's pre-push hook, refs on stdin)
  python3 -I maintainer/prepush.py check
(Windows: py -3 -I ...). Run from inside the checkout.

scan   scans the commits `git rev-list <revision>...` lists (such as `origin/master..HEAD`): each
       commit's message, and the name and contents of each file it adds or changes against its first
       parent (each file at that commit). Annotated tags named by a revision have their message
       scanned too. Each deny-list line is an extended regex matched as the export matches it
       (tools/export-template.sh: whole words, case-insensitive; tools/deny_coverage.py reads it).
hook   what maintainer/hooks/pre-push runs: reads git's `<local ref> <local sha> <remote ref>
       <remote sha>` lines and scans, for each ref pushed, the commits the remote does not have yet
       (a new branch: those no ref of <remote> reaches; a deleted ref: nothing). The deny list is
       the file the checkout's git config names under `careerlog.denylist` (a `~` is expanded),
       never a tracked file.
check  says whether the hook is active in this checkout: core.hooksPath, the configured deny list
       and its patterns.

A hit prints where it is (commit, then `message line <n>`, `file name <path>` or `<path>:<line>`),
never the deny list or the text matched. Exit 0 when nothing matched (`OK: ...`), 1 on a hit or when
the deny list is not configured, missing, empty or unreadable (`FAIL: ...`), 2 on a usage error.
It is the maintainer's guard only: a contributor without the list does not install it.
Standard library only, Python 3.11+.
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))   # -I leaves it off sys.path
sys.dont_write_bytecode = True
import deny_coverage   # noqa: E402  (the export's whole-word, case-insensitive match)

CONFIG_KEY = "careerlog.denylist"
HOOKS_PATH = "maintainer/hooks"
ZERO = "0" * 40
USAGE = ("usage: prepush.py scan --deny <file> <revision>... | prepush.py hook <remote> [<url>]"
         " | prepush.py check")


class Fail(Exception):
    pass


def git(*args, data=None, check=True):
    p = subprocess.run(["git", "-c", "core.quotePath=false", *args], input=data, capture_output=True)
    if check and p.returncode != 0:
        raise Fail("git %s: %s" % (" ".join(args), p.stderr.decode("utf-8", "replace").strip()))
    return p.stdout


def is_commit(oid):
    return subprocess.run(["git", "cat-file", "-e", oid + "^{commit}"], capture_output=True).returncode == 0


def text(data):
    return data.decode("utf-8", "replace")


def load(deny):
    """The compiled patterns of the deny list at `deny`; Fail when it is missing, empty or unreadable."""
    if not deny:
        raise Fail("no deny list configured: run git config %s <path to your Log's .export-deny>"
                   " (docs/maintaining.md > The pre-push check)" % CONFIG_KEY)
    if not os.path.isfile(deny):
        raise Fail("no deny list at %s (git config %s)" % (deny, CONFIG_KEY))
    try:
        patterns = deny_coverage.deny_patterns(deny)
    except UnicodeDecodeError:
        raise Fail("the deny list at %s is not UTF-8" % deny)
    except deny_coverage.Unreadable as e:   # its message may quote a pattern: never print that
        why = "it starts with a byte order mark" if "byte order mark" in str(e) else             "a line in it cannot be read as grep -E reads it (tools/deny_coverage.py reads it alike)"
        raise Fail("cannot read the deny list at %s: %s" % (deny, why))
    if not patterns:
        raise Fail("the deny list at %s holds no pattern" % deny)
    return patterns


def hits(patterns, value):
    """1-based numbers of the lines of `value` that a pattern matches."""
    return [n for n, line in enumerate(value.splitlines(), 1) if any(p.search(line) for p in patterns)]


def blobs(oids):
    """{oid: contents} for the given blob ids, read in one `git cat-file --batch`."""
    out = git("cat-file", "--batch", data="".join(o + "\n" for o in oids).encode())
    found, pos = {}, 0
    for oid in oids:
        end = out.index(b"\n", pos)
        header = out[pos:end].split()
        size = int(header[2])
        found[oid] = out[end + 1:end + 1 + size]
        pos = end + 1 + size + 1
    return found


def changed(commit, parents):
    """[(path, blob id)] for each file the commit adds or changes against its first parent."""
    base = ["--root", commit] if not parents else [parents[0], commit]
    out = text(git("diff-tree", "-r", "-z", "--no-renames", "--diff-filter=d", "--no-commit-id", *base))
    fields = out.split("\0")
    files = []
    for meta, path in zip(fields[0::2], fields[1::2]):
        mode, oid = meta.split()[1], meta.split()[3]
        if mode != "160000":   # a submodule's commit is not a blob here
            files.append((path, oid))
    return files


def scan(patterns, revisions):
    """Hit lines for the commits `git rev-list <revisions>` lists and the tags the revisions name."""
    found = []
    for rev in revisions:
        name = rev.lstrip("^")
        if ".." in rev or rev.startswith("-"):
            continue
        oid = text(git("rev-parse", "--verify", "--quiet", name, check=False)).strip()
        if oid and text(git("cat-file", "-t", oid)).strip() == "tag":
            body = text(git("cat-file", "tag", oid)).split("\n\n", 1)
            for n in hits(patterns, body[1] if len(body) > 1 else ""):
                found.append("tag %s: message line %d" % (oid[:10], n))
    commits = text(git("rev-list", "--parents", *revisions, "--")).split("\n")
    seen = set()
    for row in filter(None, commits):
        commit, *parents = row.split()
        where = "commit %s" % commit[:10]
        for n in hits(patterns, text(git("show", "-s", "--format=%B", commit))):
            found.append("%s: message line %d" % (where, n))
        files = changed(commit, parents)
        for path, _ in files:
            if hits(patterns, "./" + path):   # the path as the export's `find .` prints it
                found.append("%s: file name %s" % (where, path))
        new = [(path, oid) for path, oid in files if oid not in seen]
        seen.update(oid for _, oid in new)
        contents = blobs([oid for _, oid in new]) if new else {}
        for path, oid in new:
            for n in hits(patterns, text(contents[oid])):
                found.append("%s: %s:%d" % (where, path, n))
    return found


def report(found, what):
    if found:
        print("FAIL: a name from the deny list is in %s; take it out (amend or rewrite the commits),"
              " then push again:" % what)
        for line in found:
            print("  " + line)
        return 1
    print("OK: no name from the deny list in %s" % what)
    return 0


def configured():
    """The deny list path the checkout's git config names, or None."""
    value = text(git("config", "--get", CONFIG_KEY, check=False)).strip()
    return os.path.abspath(os.path.expanduser(value)) if value else None


def ranges(lines, remote):
    """rev-list arguments, one list per ref pushed, from git's pre-push stdin lines."""
    out = []
    for line in lines:
        if not line.strip():
            continue
        local_ref, local, remote_ref, remote_oid = line.split()
        if local == ZERO:   # deleting the remote ref sends nothing
            continue
        # What the remote has: its ref's old commit when it is here, and every ref of <remote> (for a
        # URL, none, so everything <local> reaches is scanned)
        exclude = ["--remotes=%s" % remote]
        if remote_oid != ZERO and is_commit(remote_oid):
            exclude.append(remote_oid)
        out.append([local, "--not", *exclude])
    return out


def main(argv, stdin=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")   # a path the console's code page cannot print
    try:
        if argv[:1] == ["scan"] and len(argv) >= 4 and argv[1] == "--deny":
            patterns = load(os.path.abspath(argv[2]))
            return report(scan(patterns, argv[3:]), " ".join(argv[3:]))
        if argv[:1] == ["hook"] and len(argv) in (2, 3):
            patterns = load(configured())
            found = []
            for revisions in ranges((stdin or sys.stdin).read().splitlines(), argv[1]):
                found += scan(patterns, revisions)
            return report(found, "the commits this push sends")
        if argv == ["check"]:
            hooks = text(git("config", "--get", "core.hooksPath", check=False)).strip()
            top = text(git("rev-parse", "--show-toplevel")).strip()
            want = os.path.normcase(os.path.abspath(os.path.join(top, HOOKS_PATH)))
            if not hooks or os.path.normcase(os.path.abspath(os.path.join(top, hooks))) != want:
                raise Fail("the hook is not active: core.hooksPath is %r, not %s"
                           " (docs/maintaining.md > The pre-push check)" % (hooks or "unset", HOOKS_PATH))
            deny = configured()
            n = len(load(deny))
            print("OK: the pre-push hook is active; it scans against %d patterns in %s" % (n, deny))
            return 0
    except Fail as e:
        print("FAIL: %s" % e)
        return 1
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
