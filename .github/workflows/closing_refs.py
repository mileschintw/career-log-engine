#!/usr/bin/env python3
"""Check what a pull request will close when it merges (closing-refs.yml).

  python3 -I .github/workflows/closing_refs.py <repo> <pr> [--body-file <file>]

Passes only when the issues GitHub will close (closingIssuesReferences) are exactly the numbers on
the body's `Closes #N` lines, no closing keyword (close, fix, resolve and their forms) is followed
by a reference anywhere else in the body, and none of the numbers is a pull request. GitHub reads
"the fix #86 proved" as a closing keyword: merging that body closed #86, a pull request.
--body-file checks that text in place of the pull request's body (to try a body before saving
it). Needs `gh`, signed in or with GH_TOKEN set. This repo's own CI: never exported to the Template.
"""
import json, re, subprocess, sys

# GitHub's closing keywords, with an optional colon, before #N or owner/repo#N
KEYWORD = re.compile(r"\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b:?\s+(?:([\w.-]+/[\w.-]+))?#(\d+)", re.I)
CLOSES_LINE = re.compile(r"^\s*closes #(\d+)\.?\s*$", re.I)


def gh(*args):
    p = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    if p.returncode:
        raise RuntimeError("gh %s: %s" % (" ".join(args), p.stderr.strip()))
    return json.loads(p.stdout)


def check(repo, body, closing=None, kind=None):
    """Problems, as lines. closing: the (repo, number) pairs GitHub will close. kind(n): "issue",
    "pull request", or None when #n does not exist. A draft, with no pull request yet,
    passes closing=None and kind=None: only the keywords outside
    `Closes #N` lines are checked."""
    problems = []
    closes = set()
    for lineno, line in enumerate(body.splitlines(), 1):
        m = CLOSES_LINE.match(line)
        if m:
            closes.add(int(m.group(1)))
            continue
        for k in KEYWORD.finditer(line):
            problems.append('line %d: "%s" is a closing keyword outside a `Closes #N` line, so merging may '
                            "close %s#%s; reword it" % (lineno, k.group(0), k.group(2) or "", k.group(3)))
    if closing is None:
        return problems
    api = {n for r, n in closing if r.lower() == repo.lower()}
    for r, n in sorted(closing):
        if r.lower() != repo.lower():
            problems.append("GitHub will close %s#%d, in another repository" % (r, n))
    for n in sorted(api - closes):
        problems.append("GitHub will close #%d, which has no `Closes #%d` line (a keyword in the body, or "
                        "an issue linked by hand)" % (n, n))
    for n in sorted(closes - api):
        problems.append("`Closes #%d` is in the body, but GitHub will not close #%d" % (n, n))
    for n in sorted(closes):
        k = kind(n)
        if k != "issue":
            problems.append("`Closes #%d`: #%d is %s, not an issue" % (n, n, k or "missing"))
    return problems


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = argv[1:]
    body_file = None
    if "--body-file" in args:
        i = args.index("--body-file")
        body_file = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2:
        print(__doc__)
        return 2
    repo, pr = args
    data = gh("pr", "view", pr, "-R", repo, "--json", "body,closingIssuesReferences")
    body = data["body"] or ""
    if body_file:
        with open(body_file, encoding="utf-8") as f:
            body = f.read()
    closing = {("%s/%s" % (r["repository"]["owner"]["login"], r["repository"]["name"]), r["number"])
               for r in data["closingIssuesReferences"]}

    def kind(n):
        try:
            issue = gh("api", "repos/%s/issues/%d" % (repo, n))
        except RuntimeError:
            return None
        return "a pull request" if "pull_request" in issue else "issue"

    problems = check(repo, body, closing, kind)
    for p in problems:
        print(p)
    if problems:
        print("closing references: %d problem(s) in #%s" % (len(problems), pr))
        return 1
    print("closing references: ok (%s)" % (", ".join("#%d" % n for _, n in sorted(closing)) or "closes nothing"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
