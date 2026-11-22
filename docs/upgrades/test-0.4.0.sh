#!/bin/sh
# Build a scratch Log as a 0.3.2 user has it, to test upgrade-0.4.0.md on (maintainer only; not
# exported, not attached to the Release).
#
#   sh docs/upgrades/test-0.4.0.sh <template> <dest>
#
# <template> is a clone of the public Template that holds the tag v0.3.2; for the release test
# (docs/publishing.md › Publishing a release step 4), the staged export with its commit tagged as
# the new release. <dest> must not exist. It makes:
#   <dest>/template.git  a bare copy of <template>, standing in for the public repo and its
#                        Releases (the upgrade mode's --url)
#   <dest>/remote.git    the Log's origin
#   <dest>/log           the Log: one "Use this template" commit from v0.3.2, its config.toml as
#                        0.3.2's setup writes it, then entries, Story index items and a Talking
#                        points file written by 0.3.2's own tools/entries.py, pushed to origin
# The sample data, line by line of the guide's ## Changes (#695): one entry's `## My contribution`
# holds two Stories (a library's origin and its launch) and is listed, with no name, under three
# question types, one of which has confirmed Talking points that list it; its `#pending` key under
# two types, and another entry's `#context` under one, take no review: line. The upgrade's step 2
# prints one `review: stories.md: entries/2024-01-library.md#my-contribution: no name, in 3 rows`
# line. Answer it as the user: the Proudest project and Technical decision rows tell `origin`, the
# Delivering impact row tells `launch`. Once the guide has run:
#   grep -c 'my-contribution "origin"' "$DEST/log/stories.md"                       # prints 2
#   grep -c 'my-contribution "origin"' "$DEST/log/stories/proudest-project.md"      # prints 1
#   py -3 -I "$DEST/log/tools/entries.py" story-coverage --root "$DEST/log" \
#     --type "Proudest project" --type "Delivering impact for users or customers" | grep -c "^story carries"   # prints 0
# and the guide's script, run again, prints `OK: nothing left to migrate` with no review: line.
set -eu
TPL=$1; DEST=$2
if py -3 -c "" 2>/dev/null; then PY="py -3"; else PY=python3; fi
[ ! -e "$DEST" ] || { echo "$DEST exists" >&2; exit 2; }
mkdir -p "$DEST/log"
DEST=$(cd "$DEST" && pwd)

git -c core.longpaths=true clone -q --bare "$TPL" "$DEST/template.git"
git -C "$DEST/template.git" config core.longpaths true
git -C "$DEST/template.git" rev-parse -q --verify "refs/tags/v0.3.2" >/dev/null \
  || { echo "$TPL has no tag v0.3.2" >&2; exit 2; }

git init -q --bare -b main "$DEST/remote.git"
git -C "$DEST/remote.git" config core.longpaths true   # Windows paths pass 260 characters
cd "$DEST/log"
git init -q -b main
git config core.autocrlf false
git config core.longpaths true
git config user.email test@example.invalid
git config user.name Test
git -C "$DEST/template.git" archive v0.3.2 | tar -x
git add -A
# The release's file modes: a folder on Windows has no executable bit to stage (as harness.py
# template-copy --modes-from)
git -C "$DEST/template.git" -c core.quotePath=false ls-tree -r v0.3.2 | awk -F'\t' '$1 ~ /^100755 /{print $2}' \
  | while IFS= read -r f; do git update-index --chmod=+x -- "$f"; done
git commit -qm "Initial commit"
git remote add origin "$DEST/remote.git"
git push -qu origin main
git remote set-head origin main

# 0.3.2's setup: config.toml from 0.3.2's own tool, the update check off for a scratch Log
$PY -I tools/config.py init --root . >/dev/null
$PY -I tools/config.py set update_check off --root . >/dev/null
git add -A && git commit -qm "setup: config.toml"

# Entries, as 0.3.2's log and consolidate modes write them
$PY -I tools/entries.py new library --month 2024-01 --status imported --field "title=Example Co — Shared library" \
  --field type=work --field "period=2024-01 – 2025-06" --field "tags=go" >/dev/null
$PY -I tools/entries.py new support --month 2023-03 --status imported --field "title=Sample Inc — Support tools" \
  --field type=work --field "period=2023-03 – 2023-12" --field "tags=python" >/dev/null
$PY - <<'EOF'
p = "entries/2024-01-library.md"
s = open(p, encoding="utf-8", newline="").read()
s = s.replace("## My contribution\n", "## My contribution\n"
              "- I started the shared library after three teams copied the same retry code (user, 2025-07-01).\n"
              "- I led its launch to every service, with a migration guide and office hours (user, 2025-07-01).\n", 1)
s = s.replace("## Pending\n", "## Pending\n- 2025-07-02: a rollback during the launch week (user, 2025-07-02)\n", 1)
open(p, "w", encoding="utf-8", newline="").write(s)
EOF

# The Story index, as 0.3.2's stories, consolidate and log modes write it
add() { $PY -I tools/entries.py story-add "$1" "$2" --summary "$3" >/dev/null; }
L=entries/2024-01-library.md
add "Proudest project" "$L#my-contribution" "started the shared library"
add "A technical decision with trade-offs" "$L#my-contribution" "one library instead of copied retry code"
add "Delivering impact for users or customers" "$L#my-contribution" "the launch to every service"
add "Working under a deadline" "$L#pending" "the launch-week rollback"
add "Failure, and what you learned" "$L#pending" "the launch-week rollback"
add "Collaboration / receiving feedback" "entries/2023-03-support.md#context" "the support rota"

# Confirmed Talking points for Proudest project, listing the unnamed key first
mkdir -p stories
cat > stories/proudest-project.md <<'EOF'
---
type: Proudest project
confirmed: 2025-07-03 10:00
order: chronological
---

# Proudest project

## Stories
1. [Shared library](../entries/2024-01-library.md#my-contribution) — lead with it for a platform role

## Opening
I started a shared library that every service now uses.

## Cue lines
- three teams, one retry bug ([Context](../entries/2024-01-library.md#context))
- I wrote the first version ([My contribution](../entries/2024-01-library.md#my-contribution))

## Follow-ups
- [Likely questions](../entries/2024-01-library.md#likely-questions)
EOF
$PY -I tools/entries.py story-confirm stories/proudest-project.md --type "Proudest project" --root . >/dev/null

git add -A && git commit -qm "log: entries and Stories in 0.3.2 formats"
git push -q
echo "Log: $DEST/log  Template: $DEST/template.git"
