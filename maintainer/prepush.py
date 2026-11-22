#!/usr/bin/env python3
"""The maintainer's guard before a push to the Engine repo (ADR 0015): refuses commits that carry a
name from the deny list of the maintainer's own Log (its .export-deny).

  python3 -I maintainer/prepush.py scan --deny <file> <revision>...
  python3 -I maintainer/prepush.py hook <remote> [<url>]       (git's pre-push hook, refs on stdin)
  python3 -I maintainer/prepush.py check
(Windows: py -3 -I ...). Run from inside the checkout.

scan   scans the commits `git rev-list <revision>...` lists (such as `origin/master..HEAD`): each
       commit's message, and the name and contents of each file it adds or changes against its first
       parent (each file at that commit). Annotated tags a revision names (not after --not or a ^)
       have their message scanned too. Each deny-list line is an extended regex matched as the export
       matches it (tools/export-template.sh: whole words, case-insensitive; tools/deny_coverage.py
       reads it).
hook   what maintainer/hooks/pre-push runs: reads git's `<local ref> <local sha> <remote ref>
       <remote sha>` lines and scans, for each ref pushed, the commits the remote does not have yet
       (a new branch: those no ref of <remote> reaches; a deleted ref: nothing). The deny list is
       the file the checkout's own git config (`--local`) names under `careerlog.denylist` (a `~` is
       expanded), never a tracked file.
check  says whether the hook is active in this checkout: core.hooksPath is the absolute path of a
       checkout's maintainer/hooks (a relative one is read in each worktree, and a worktree whose
       branch lacks the hook, such as coord, would push unchecked), and the configured deny list
       reads.

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
    return bool(git("rev-parse", "--verify", "--quiet", oid + "^{commit}", check=False).strip())


def decode(data):
    return data.decode("utf-8", "replace")


def load_deny(deny):
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
        why = ("it starts with a byte order mark" if "byte order mark" in str(e) else
               "a line in it cannot be read as grep -E reads it (tools/deny_coverage.py reads it alike)")
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
        if len(header) != 3:   # `<oid> missing`: a commit's file this clone does not hold
            raise Fail("cannot read file %s from git (%s)" % (oid, decode(out[pos:end])))
        size = int(header[2])
        found[oid] = out[end + 1:end + 1 + size]
        pos = end + 1 + size + 1
    return found


def changed(commit, parents):
    """[(path, blob id)] for each file the commit adds or changes against its first parent."""
    base = ["--root", commit] if not parents else [parents[0], commit]
    out = decode(git("diff-tree", "-r", "-z", "--no-renames", "--diff-filter=d", "--no-commit-id", *base))
    fields = out.split("\0")
    files = []
    for meta, path in zip(fields[0::2], fields[1::2]):
        mode, oid = meta.split()[1], meta.split()[3]
        if mode != "160000":   # a submodule's commit is not a blob here
            files.append((path, oid))
    return files


def scan(patterns, revisions):
    """Hit lines for the commits `git rev-list <revisions>` lists and the tags the revisions name."""
    found, negated = [], False
    for rev in revisions:
        negated ^= rev == "--not"
        if negated or ".." in rev or rev.startswith(("-", "^")):   # not sent, or not a tag name
            continue
        oid = decode(git("rev-parse", "--verify", "--quiet", rev, check=False)).strip()
        while oid and decode(git("cat-file", "-t", oid)).strip() == "tag":   # a tag of a tag too
            head, _, body = decode(git("cat-file", "tag", oid)).partition("\n\n")
            for n in hits(patterns, body):
                found.append("tag %s: message line %d" % (oid[:10], n))
            oid = head.split("\n", 1)[0].split()[1]   # its `object <oid>` line
    commits = decode(git("rev-list", "--parents", *revisions, "--")).split("\n")
    seen = set()
    for row in filter(None, commits):
        commit, *parents = row.split()
        where = "commit %s" % commit[:10]
        for n in hits(patterns, decode(git("show", "-s", "--format=%B", commit))):
            found.append("%s: message line %d" % (where, n))
        files = changed(commit, parents)
        for path, _ in files:
            if hits(patterns, "./" + path):   # the path as the export's `find .` prints it
                found.append("%s: file name %s" % (where, path))
        new = [(path, oid) for path, oid in files if oid not in seen]
        seen.update(oid for _, oid in new)
        contents = blobs([oid for _, oid in new]) if new else {}
        for path, oid in new:
            for n in hits(patterns, decode(contents[oid])):
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
    value = decode(git("config", "--local", "--get", CONFIG_KEY, check=False)).strip()
    return os.path.abspath(os.path.expanduser(value)) if value else None


def ranges(lines, remote):
    """rev-list arguments, one list per ref pushed, from git's pre-push stdin lines."""
    out = []
    for line in lines:
        if not line.strip():
            continue
        try:
            local_ref, local, remote_ref, remote_oid = line.split()
        except ValueError:
            raise Fail("cannot read the line git passed to the hook: %r" % line)
        if set(local) == {"0"}:   # deleting the remote ref sends nothing
            continue
        # What the remote has: its ref's old commit when it is here, and every ref of <remote> (for a
        # URL, none, so everything <local> reaches is scanned)
        exclude = ["--remotes=%s" % remote]
        if set(remote_oid) != {"0"} and is_commit(remote_oid):
            exclude.append(remote_oid)
        out.append([local, "--not", *exclude])
    return out


def main(argv, stdin=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")   # a path the console's code page cannot print
    try:
        if argv[:1] == ["scan"] and len(argv) >= 4 and argv[1] == "--deny":
            patterns = load_deny(os.path.abspath(argv[2]))
            return report(scan(patterns, argv[3:]), " ".join(argv[3:]))
        if argv[:1] == ["hook"] and len(argv) in (2, 3):
            patterns = load_deny(configured())
            found = []
            for revisions in ranges((stdin or sys.stdin).read().splitlines(), argv[1]):
                found += scan(patterns, revisions)
            return report(found, "the commits this push sends")
        if argv == ["check"]:
            # Absolute, so a worktree whose branch lacks the hook (the coord branch, a branch from
            # before it) still runs it: git reads a relative core.hooksPath in each worktree's own files
            hooks = os.path.expanduser(decode(git("config", "--get", "core.hooksPath", check=False)).strip())
            if not (hooks and os.path.isabs(hooks) and os.path.isfile(os.path.join(hooks, "pre-push"))
                    and os.path.isfile(os.path.join(hooks, "..", "prepush.py"))):
                raise Fail("the hook is not active: core.hooksPath is %r, not the absolute path of"
                           " a checkout's %s (docs/maintaining.md > The pre-push check)"
                           % (hooks or "unset", HOOKS_PATH))
            deny = configured()
            n = len(load_deny(deny))
            print("OK: the pre-push hook is active; it scans against %d patterns in %s" % (n, deny))
            return 0
    except Fail as e:
        print("FAIL: %s" % e)
        return 1
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
