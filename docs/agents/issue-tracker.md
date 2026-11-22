# Issue tracker

This repo's issues are GitHub Issues on its GitHub repo (the `origin` remote), read and written with `gh`. In `gh api` paths, `{owner}/{repo}` stands for that repo: `gh` fills it in from the checkout. Quote such a path: unquoted, PowerShell splits it at the braces. Issues, their comments and pull request bodies are written in English, with no names, employers or projects from anyone's Log.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --json number,title,body,labels,comments`.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Make an issue a sub-issue of a parent**: `gh issue create --parent <parent> ...`, or `gh issue edit <parent> --add-sub-issue <child>` afterwards (`gh` 2.94+). Older `gh`: `gh api --method POST 'repos/{owner}/{repo}/issues/<parent>/sub_issues' -F sub_issue_id=<child-db-id>` (the child's database id: `gh api 'repos/{owner}/{repo}/issues/<n>' --jq .id`). Without sub-issues, put `Part of #<parent>` at the top of the child body.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`; the labels are in [triage-labels.md](triage-labels.md).
- **Close**: `gh issue close <number> --comment "..."`

## Pull requests as a triage surface

**PRs as a request surface: yes.** _(`/triage` reads this flag.)_ The Template's front page asks its users to send pull requests here, and [publishing.md](../publishing.md) triages them from `needs-triage` like an issue.

PRs run through the same labels and states as issues, using the `gh pr` equivalents:

- **Read a PR**: `gh pr view <number> --comments` and `gh pr diff <number>` for the diff.
- **List external PRs for triage**: `gh api --paginate 'repos/{owner}/{repo}/pulls?state=open' --jq '.[] | select(.author_association | IN("OWNER","MEMBER","COLLABORATOR") | not) | {number, title, author: .user.login, author_association, labels: [.labels[].name]}'`.
- **Comment / label / close**: `gh pr comment`, `gh pr edit --add-label`/`--remove-label`, `gh pr close`.

GitHub shares one number space across issues and PRs, so a bare `#42` may be either: resolve with `gh pr view 42` and fall back to `gh issue view 42`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

## When a skill says "fetch the relevant ticket"

Read it as in **Read an issue** above.

## Blocking

A hard dependency (A needs B's result) is GitHub's native blocked-by link, the one source the relay brief's `Depends on:` and the plan's roadmap copy. Mark it with `python -I maintainer/coord.py block <A> <B>` (A is blocked by B; Windows `py -3 -I`) and follow its output. Read it with `gh api 'repos/{owner}/{repo}/issues/<A>/dependencies/blocked_by' --jq '.[].number'`.

A same-section wait (two issues change the same section, neither needs the other's result) is never a blocked-by link: it goes in the issue body as a line `Same-section wait: after #N, <file › section>`, and in the relay brief's `Waits for (same section):` line.

## Frontier query

The open issues that can start now: every open issue labelled `ready-for-agent` (triaged; [triage-labels.md](triage-labels.md)) whose blocked-by issues are all closed as completed.

```
gh issue list --state open --label ready-for-agent --limit 200 --json number,title --jq '.[].number' |
  while read n; do
    open=$(gh api "repos/{owner}/{repo}/issues/$n/dependencies/blocked_by" \
      --jq '[.[] | select(.state == "open" or .state_reason == "not_planned")] | length')
    [ "$open" = 0 ] && echo "#$n"
  done
```

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body. `gh issue create --label wayfinder:map`.
- **Child ticket**: an issue linked to the map as a sub-issue (see **Make an issue a sub-issue of a parent**). Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed, the ticket is assigned to the driving dev.
- **Blocking**: as in **Blocking** above.
- **Frontier query**: the map's open children with no open or not-planned blocker (as the **Frontier query** above counts them) and no assignee; first in map order wins. It does not filter on `ready-for-agent`.
- **Claim**: `gh issue edit <n> --add-assignee @me`, the session's first write.
- **Resolve**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then append a context pointer (gist + link) to the map's Decisions-so-far.
