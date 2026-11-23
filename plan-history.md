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
