# Plan

Last updated: 2026-11-23 03:48 -0800（新 coordinator 接手）

只寫現況。做完的搬到 `plan-history.md`，這裡留一行指標；什麼都不刪。下面這些一直留在這份：**Now** 的 session、還沒寫進 repo 文件的 **Rulings**、兩個 **Waiting for the user** 節、**Deadlines**，以及 **Handover** 裡使用者的常駐交代和 merge right。

**這個資料夾是公開的**（`project.md` › Every push is a publication）：不寫 deny list 上的名字（owner 寫 `<owner>`）、不寫 Log 的內容。私人的東西寫在 `D:\Repos\career-log-coord`。

## Handover

- **Coordinator:** title engine-coordinator-b9a6ad, worktree D:\Repos\career-log-engine\.claude\worktrees\engine-coordinator-b9a6ad, id local_9ffe4687-9b12-418a-998f-24bd9642ab18, mode normal. 2026-11-23 03:48 -0800 接手；由上一個 coordinator（local_651b2b18-d78c-4525-946a-c80da1bfbfd6，在私人記錄上做到 #818 的拆分完成）開的 session。
- **Next（2026-11-23 22:55 -0800）：** 第三輪開工：e52、e17、e29。開 session、寫 Now 列、設鬧鐘；PR CI 過就 merge。
- **Standing instructions:**
  - 2026-11-13 16:00：「重新開一次，每個新開的 worker session 都用 model opus、effort high」。之後開的 worker 都用 `model: claude-opus-5-5`、`effort: high`。
  - 2026-10-26：進行中的工作做完後，不要開始新任務；下一步只列出來，等使用者說開工。
  - 2026-10-29：「第一波請一次提出整個 frontier 和後面的依賴鏈，等我同意後再開 session。」
  - Log 的資料工作從不排 lane（`project.md` › Log data work）。
- **Merge right:** 2026-11-23 22:55 -0800，使用者 picked「開工，CI 過就 merge」（問題：照提案開第三輪的三條 lane 嗎？）：lanes e52、e17、e29。
- **Unattended log:** none

## Rulings

- **Owner 名稱和公開位址（2026-11-21，使用者 picked「留在名單，網址設例外」）：** GitHub owner 名稱留在 deny list；Engine repo 和 Template 的公開位址（`<owner>/career-log-engine`、`<owner>/career-log-template`）是預期命中，由 allow 檔遮掉，其他命中照舊要處理。
- **快照掃描裡可以留的命中（2026-11-21，使用者 picked「保留」）：** 公開位址之外，`.claude/settings.json:6`、`LICENSE:3`、`tools/template/LICENSE:3`（維護者的 GitHub 帳號名）和 `docs/guide.md:208,209`、`skills/career-log/speaking.md:8,9`（公開的面試指南 URL）可以留。E#21 要給 LICENSE 的例外加 guard。
- **記錄的位置（2026-11-23，使用者 picked「重新開始」「career-log-engine-coord」「我寫交接，開新 session」）：** Engine repo 的 `coord` 從這裡重新開始，舊記錄留在私人的 `D:\Repos\career-log-coord` 當封存；私人的東西（Log 資料 prompt、Mac 測試、會寫到名字的筆記）仍寫那裡。

## Now

"Kind" is `pr`, `run`, `audit` or `spare`, as the relay plugin's `GLOSSARY.md` defines under **Kind**.

| Key | Kind | Issues | Session | State | Parked until |
|---|---|---|---|---|---|
| e52 | pr | #52 | local_524d3b89-26bb-4cc4-bfe1-b067c354ad7a（落在 `.claude/worktrees/jovial-kapitsa-a8f724`，分支 `claude/lane-e52-366592`） | review（worker 跑第二輪 review 和 checks_for --run） | — |
| e17 | pr | #17 #49 | local_f44ecadd-26c9-4624-9d40-d9039241d4b2（落在 `.claude/worktrees/objective-yalow-5e2d4c`，分支 `claude/lane-e17-18146b`） | PR #54 open, waitchecks | — |
| e29 | pr | #29 | local_d6d20f13-f7af-44ba-9fd5-33f16f3e68a0（落在 `.claude/worktrees/lane-823-251cbd`，分支 `claude/lane-e29-8c9454`） | PR #55 open, waitchecks | — |

**Main checkout:** none.

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free`, `limited: <what>` or `parent`, as the relay plugin's `GLOSSARY.md` defines under **Kind**.

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #17 升級模式：Log 在比最新 release 新的 Dev build 上時跟著舊 release 的工具走 | 1 | none | none | `skills/career-log/modes/upgrade.md › step 1`（item 4） | 第三輪 lane e17 |
| #28 Output 對 entry 的檢查只在 audit 跑 | — | none | none | 缺 Files 節 | 不排 lane：要使用者在 Direction 的四個選項裡選（建議先 1、3，2、4 等量過成本） |
| #29 Harness：這個 repo 沒有 Log，agent case 的 copy 要有 Log 來源 | 1 | none | none | `maintainer/harness.py › copy`、`docs/maintaining-tests.md › Harness` | 第三輪 lane e29 |
| #30 Subagents：Screen 用便宜的模型 | — | none | none | 缺 Files 節 | 不排 lane：Long-term |
| #49 升級模式：Sonnet 在 step 5 摘要重複 Dev build 警告 | 1 | none | none | `skills/career-log/modes/upgrade.md › step 5` | 第三輪 lane e17 |
| #52 maintainer 工具 import `tools/logfiles.py`，但 coord／dev build／prepush 群組和 `coord-tests.yml` 沒列 | 1 | none | none | `tools/checks_for.py › GROUPS`、`coord-tests.yml › paths:`、`tools/tests/test_checks_for.py` | 第三輪 lane e52 |

## Waiting for the user to be present

none

## Waiting for the user's decision

- **第三輪結束後：** #28（四個選項選哪些，建議先 1、3）；Log 升到最新 Dev build 的 prompt（寫到私人記錄）。

## Deadlines

none
