# Plan history

Finished work moved out of `plan.md`, oldest first (append each block at the end), for checking only; the plan is the source for anything current. Each block names when it moved and the coordinator that moved it.

## 之前的記錄（2026-11-23，coordinator local_651b2b18-d78c-4525-946a-c80da1bfbfd6）

這個資料夾 2026-11-23 起才使用，是公開的。之前的 plan、plan-history、briefs、reports、status、PR body 草稿和 prompts（Engine 開發到 0.4.1、#818 的拆分、Log 的資料工作）都留在維護者私人的記錄 `D:\Repos\career-log-coord`（private Log repo 的 `coord` 分支），不搬過來：裡面有 Log 和求職的內容。這裡的 Roadmap 是從那裡的 plan 改寫的，只留 Engine 的事。

拆分的結果：Engine repo 是 Engine 的原始碼（public）；Template 是它的匯出，第一個 release `v0.4.1`（d3ceb654）；維護者的 Log 由舊的 private repo 轉成（private 的 #827），升到 Dev build `0.4.2-dev.1`。拆分期間的凍結已解除。

## 接手後的三件決定（2026-11-23，coordinator engine-coordinator-b9a6ad）

另一個 session 轉達、使用者在這裡確認（picked「三件都照做」）：
- 兩張新 issue 都開：匯出檢查在 Template 和 Log 裡 fail（高優先）、`config.py set` 的新欄位位置（#31，低優先）。
- 關 blank issue 和 #18 的 guard 測試掛進 `checks_for.py`，併成一張（#32）。
- archive 拆分的 13 個 lane session（819、820、830、827、821–825、e7、e8、e14、e18）：已 archive；worktree 都乾淨、沒有沒 push 的 commit，共用筆記資料夾是空的。刪掉 8 條已 merge 的遠端 `claude/lane-*` 分支：已刪。

## 第一輪 merge：e15、e21、e27、e31（2026-11-23 15:37 -0800，coordinator engine-coordinator-b9a6ad）

PR #38（#15）、#39（#21）、#40（#27）、#41（#31）CI 過後依第一輪 merge right merge；master 的 push run（Dev build）在 43201d0c 成功。各 lane 的 Now 列：

| e15 | pr | #15 | local_c068efcd-7d35-45a8-a8de-e767f7bb9f52（落在已 archive 的 `.claude/worktrees/lane-e14-296d3a`，分支 `claude/lane-e15-*`） | PR #38 open, waitchecks | — |
| e21 | pr | #21 | local_6dca5a18-ff19-4fdd-91bb-7b06a4b65673（落在已 archive 的 `.claude/worktrees/lane-e7-af6541`，分支 `claude/lane-e21-*`） | PR #39 open, waitchecks | — |
| e27 | pr | #27 | local_2b4f703a-dc6d-449b-b5ec-c27e246311a5（使用者按卡片開；落在已 archive 的 `.claude/worktrees/lane-824-c07deb`，分支 `claude/keen-hellman-848c87`） | PR #40 open, waitchecks | — |
| e31 | pr | #31 | local_de73c331-cd14-4bfa-862c-705c4a6a065b（卡片；落在已 archive 的 `.claude/worktrees/lane-823-251cbd`，分支 `claude/xenodochial-grothendieck-a9c012`） | PR #41 open, waitchecks | — |

## 第一輪 merge：e23（2026-11-23 15:38 -0800）

PR #42（#23）CI 過後依第一輪 merge right merge。Now 列：

| e23 | pr | #23 | local_a4f94a65-33f2-4e28-b6e1-0f9bb83fd226（落在已 archive 的 `.claude/worktrees/lane-825-379001`，分支 `claude/lane-e23-*`） | started | — |

## 第一輪 merge：e20（2026-11-23 16:00 -0800）

PR #43（#20）CI 過後依第一輪 merge right merge；push run 在 acfcdcc5 成功。使用者在 e20 的 session picked「沒改過換、改過問」。Now 列：

| e20 | pr | #20 | local_bbf40246-872b-40df-b77c-682c478b5ee5（落在已 archive 的 `.claude/worktrees/lane-e8-2d4a83`，分支 `claude/lane-e20-*`） | PR #43 open, waitchecks | — |

