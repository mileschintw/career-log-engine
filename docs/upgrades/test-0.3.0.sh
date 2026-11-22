#!/bin/sh
# Build a scratch Log as a 0.2.1 user has it, to test upgrade-0.3.0.md on (maintainer only; not
# exported, not attached to the Release).
#
#   sh docs/upgrades/test-0.3.0.sh <template> <dest> [--odd]
#
# <template> is a clone of the public Template that holds the tag v0.2.1; for the release test
# (docs/publishing.md › Publishing a release step 4), the staged export with its commit tagged
# v0.3.0. <dest> must not exist. It makes:
#   <dest>/template.git  a bare copy of <template>, standing in for the public repo and its
#                        Releases (the upgrade mode's --url)
#   <dest>/remote.git    the Log's origin
#   <dest>/log           the Log: one "Use this template" commit from v0.2.1, its config.toml as
#                        0.2.1's setup writes it, then entries and their README rows written by
#                        0.2.1's own tools/entries.py (new, readme-row), pushed to origin
#   <dest>/expected.txt  `<entry> <status>` per entry: the status its front matter must hold once
#                        the guide has run (`ask` for the one the user gives, with --odd)
# The sample data, line by line of the guide's ## Changes (#573, #574): statuses only in the
# README rows (a note in parentheses on one), a Tags column, a series in two parts with different
# statuses, an ongoing entry and a GAP period; every row reads, so step 1 settles it all.
# --odd takes the other branches of step 2 too: a row whose status the user edited into no status
# (`done`), an entry with no row, a row that links no entry (each an ask: line), and an entry with
# CRLF line ends. Once the guide has run, this prints each entry whose status differs (an `ask`
# line takes the status the user gave):
#   while read -r f s; do tr -d '\r' < "$DEST/log/$f" | grep -qxF "status: $s" || echo "$f"; done < "$DEST/expected.txt"
# The Log's README.md keeps 0.2.1's line `Entries appear here as you log them.` above the table;
# once the guide has written the table, the line is gone (#592):
#   grep -c "Entries appear here" "$DEST/log/README.md"   # prints 0
set -eu
TPL=$1; DEST=$2; ODD=${3:-}
if py -3 -c "" 2>/dev/null; then PY="py -3"; else PY=python3; fi
[ ! -e "$DEST" ] || { echo "$DEST exists" >&2; exit 2; }
mkdir -p "$DEST/log"
DEST=$(cd "$DEST" && pwd)

git -c core.longpaths=true clone -q --bare "$TPL" "$DEST/template.git"
git -C "$DEST/template.git" config core.longpaths true
git -C "$DEST/template.git" rev-parse -q --verify "refs/tags/v0.2.1" >/dev/null \
  || { echo "$TPL has no tag v0.2.1" >&2; exit 2; }

git init -q --bare -b main "$DEST/remote.git"
git -C "$DEST/remote.git" config core.longpaths true   # Windows paths pass 260 characters
cd "$DEST/log"
git init -q -b main
git config core.autocrlf false
git config core.longpaths true
git config core.safecrlf false   # the --odd CRLF entry
git config user.email test@example.invalid
git config user.name Test
git -C "$DEST/template.git" archive v0.2.1 | tar -x
git add -A && git commit -qm "Initial commit"
git remote add origin "$DEST/remote.git"
git push -qu origin main
git remote set-head origin main

# 0.2.1's setup: config.toml from 0.2.1's own tool, the update check off for a scratch Log
$PY -I tools/config.py init --root . >/dev/null
$PY -I tools/config.py set update_check off --root . >/dev/null
git add -A && git commit -qm "setup: config.toml"

# Entries and their rows, as 0.2.1's log and consolidate modes write them
new() {   # new <slug> <month> <new status> <title> <type> <period> <tags> [<series>]
  set -- "$@" ""   # so that $8 is set under set -u when no series is given
  $PY -I tools/entries.py new "$1" --month "$2" --status "$3" --field "title=$4" --field "type=$5" \
    --field "period=$6" --field "tags=$7" ${8:+--field "series=$8"} >/dev/null
}
new first-job 2016-07 imported "Example Co — First job" work "2016-07 – 2019-06" "java"
new platform 2019-07 imported "Sample Inc — Platform" work "2019-07 – 2021-01" "go, kubernetes" platform
new platform-2 2021-02 imported "Sample Inc — Platform, part 2" work "2021-02 – 2023-06" "go" platform
new current 2023-07 stub "Demo Labs — Backend" work "2023-07 – ongoing" "python, postgres"
new hackathon 2018-11 stub "Hackathon prize" award "GAP – 2018-11" "python"
$PY -I tools/entries.py readme-row entries/2016-07-first-job.md --status "consolidated (two gaps)" >/dev/null
$PY -I tools/entries.py readme-row entries/2019-07-platform.md --status consolidated >/dev/null
cat > "$DEST/expected.txt" <<'EOF'
entries/2016-07-first-job.md consolidated (two gaps)
entries/2019-07-platform.md consolidated
entries/2021-02-platform-2.md imported
entries/2023-07-current.md stub
entries/2018-11-hackathon.md stub
EOF

if [ "$ODD" = "--odd" ]; then
  new talk 2024-03 stub "Meetup talk" other "2024-03 – 2024-03" ""
  $PY - <<'EOF'
import re
def edit(p, f):
    s = open(p, encoding="utf-8", newline="").read()
    t = f(s)
    assert t != s, p
    open(p, "w", encoding="utf-8", newline="").write(t)
def sub(pattern, repl, s):
    t, n = re.subn(pattern, repl, s)
    assert n == 1, pattern
    return t
def readme(s):
    s = sub(r"(?m)^(\| [^\n]*\(entries/2023-07-current\.md\)[^\n]*\| )stub \|$", r"\1done |", s)   # no status
    s = sub(r"(?m)^\| [^\n]*\(entries/2024-03-talk\.md\)[^\n]*\n", "", s)                    # no row
    return sub(r"(?m)(^\| [^\n]*\(entries/2018-11-hackathon\.md\)[^\n]*\n)",                 # a note row
               r"\1| 2025 | Conference talks: see sources/talks/ | other | | |\n", s)
edit("README.md", readme)
edit("entries/2016-07-first-job.md", lambda s: s.replace("\r\n", "\n").replace("\n", "\r\n"))
EOF
  grep -vxF "entries/2023-07-current.md stub" "$DEST/expected.txt" > "$DEST/expected.tmp"
  printf 'entries/2023-07-current.md ask\nentries/2024-03-talk.md ask\n' >> "$DEST/expected.tmp"
  mv "$DEST/expected.tmp" "$DEST/expected.txt"
fi

git add -A && git commit -qm "log: entries in 0.2.1 formats"
git push -q
echo "Log: $DEST/log  Template: $DEST/template.git  Expected: $DEST/expected.txt"
