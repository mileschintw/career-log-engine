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

## 第一輪 merge：e32（2026-11-23 16:00 -0800）

PR #44（#32、#36）CI 過後依第一輪 merge right merge。確認 blank issue 已關：開 `/issues/new/choose` 只看到兩個表單。Now 列：

| e32 | pr | #32 #36 | local_0da5bc93-857e-49fc-86d7-73b77172a54b（卡片；`.claude/worktrees/objective-yalow-5e2d4c`，分支 `claude/objective-yalow-5e2d4c`） | PR #44 open, waitchecks | — |

## 第一輪 merge：e33（2026-11-23 16:20 -0800）

PR #45（#33）CI 過後（新的 `template-checks` job 第一次跑也過）依第一輪 merge right merge；push run 在 369b5195 成功。送 GO #e22。Now 列：

| e33 | pr | #33 | local_abb44ce2-5b42-4ddf-974a-5208f544844d（落在已 archive 的 `.claude/worktrees/lane-e18-c7297e`，分支 `claude/lane-e33-*`） | PR #45 open, waitchecks | — |

## 第一輪結束：e22（2026-11-23 16:49 -0800）

PR #47（#22）CI 過後 merge。第一輪九條 lane 全部 merge。Merge right 結束，原文：

- **Merge right:** 2026-11-23 15:14 -0800，使用者 picked「開工，CI 過就 merge」（問題：照提案開第一輪的 9 條 lane 嗎？）：lanes e33、e15、e20、e21、e23、e27、e31、e32、e22。

Now 列：

| e22 | pr | #22 | local_496ef204-860b-447d-9383-905d0c9f9661（卡片；`.claude/worktrees/jovial-kapitsa-a8f724`，分支 `claude/jovial-kapitsa-a8f724`） | PR #47 open, waitchecks | — |

使用者說「Archive them」：第一輪九個 lane session 已 archive（worktree 都乾淨、都已在 master）。

使用者說「Delete them」：第一輪九條已 merge 的遠端分支已刪。

## 第二輪 merge：e46（2026-11-23 17:45 -0800）

PR #50（#46）template-checks 第一次偶發 fail（rmtree 撞 git maintenance.lock，#24 的問題），使用者 picked「重跑那個 job」，重跑通過後依第二輪 merge right merge；push run 在 8af5412e 成功。Now 列：

| e46 | pr | #46 | local_f0e93011-09b8-4f6c-a556-9e3bb87b05f6（落在已 archive 的 `.claude/worktrees/jovial-kapitsa-a8f724`，分支 `claude/lane-e46-0d3d17`） | PR #50: template-checks 偶發 fail（rmtree 撞 git maintenance.lock，#24），使用者 picked「重跑那個 job」，重跑中 | — |

## 第二輪 merge：e37（2026-11-23 17:46 -0800）

PR #51（#37、#48）：使用者 picked「開 PR，剩的留 #49」；template-checks 同樣偶發 fail，重跑通過後 merge。#48 第三條 Sonnet 0.4.0 的重複留在 #49。Now 列：

| e37 | pr | #37 #48 | local_ce3c81e2-c1be-48fb-b734-b260e75431a1（落在已 archive 的 `.claude/worktrees/objective-yalow-5e2d4c`，分支 `claude/lane-e37-be3720`） | PR #51 open, waitchecks | — |

## 第二輪結束：e24（2026-11-23 18:15 -0800）

PR #53（#24）CI 16 項全過後 merge。第二輪三條 lane 全部 merge。Merge right 結束，原文：

- **Merge right:** 2026-11-23 17:22 -0800，使用者 picked「開工，CI 過就 merge」（問題：照提案開第二輪的 3 條 lane 嗎？）：lanes e46、e37、e24。

Now 列：

| e24 | pr | #24 | local_fb3ec7ec-9018-4991-91b5-6622fdb72507（落在已 archive 的 `.claude/worktrees/lane-823-251cbd`，分支 `claude/lane-e24-48edc9`） | PR #53 open, waitchecks | — |

2026-11-23 21:22 -0800 使用者說「Archive 並刪分支」：第二輪三個 lane session（e46、e37、e24）已 archive（worktree 乾淨、都已在 master），三條遠端分支 `claude/lane-e46-0d3d17`、`claude/lane-e37-be3720`、`claude/lane-e24-48edc9` 已刪。

- **第三輪（2026-11-23 22:55 -0800）：** 使用者說開工。#17、#29、#49、#52 triage 成 ready-for-agent；#52 加了 guard 的 acceptance，#29 記下使用者選的 template-copy＋fixture，#17、#29 補了 Files 節。

## e17 merged（2026-11-24 07:17Z）

PR #54 merged，關閉 #17、#49；master push run 在 46ed16aa 通過（Dev build）。報告 `reports/e17.md`。Now 列：

| e17 | pr | #17 #49 | local_f44ecadd-26c9-4624-9d40-d9039241d4b2（落在 `.claude/worktrees/objective-yalow-5e2d4c`，分支 `claude/lane-e17-18146b`） | PR #54 open, waitchecks | — |
| #17 升級模式：Log 在比最新 release 新的 Dev build 上時跟著舊 release 的工具走 | 1 | none | none | `skills/career-log/modes/upgrade.md › step 1`（item 4） | 第三輪 lane e17 |
| #49 升級模式：Sonnet 在 step 5 摘要重複 Dev build 警告 | 1 | none | none | `skills/career-log/modes/upgrade.md › step 5` | 第三輪 lane e17 |

## e29 merged（2026-11-24 07:18Z）

PR #55 merged，關閉 #29；master push run 在 662a9ea5 通過（Dev build）。`harness.py copy` 留著但拒絕 Log 資料；讀 Log 的 case 用 template-copy＋每個 case 自己的 fixture。報告 `reports/e29.md`。Now 列：

| e29 | pr | #29 | local_d6d20f13-f7af-44ba-9fd5-33f16f3e68a0（落在 `.claude/worktrees/lane-823-251cbd`，分支 `claude/lane-e29-8c9454`） | PR #55 open, waitchecks | — |
| #29 Harness：這個 repo 沒有 Log，agent case 的 copy 要有 Log 來源 | 1 | none | none | `maintainer/harness.py › copy`、`docs/maintaining-tests.md › Harness` | 第三輪 lane e29 |

- **e52 第 4 輪 review 仍有 blocker（since 2026-11-24 00:30 -0800）：** fix（約 10 行，對不到 repo 檔的 untold join 算 untold）再跑第 5 輪，或 revert 回 457f2c2 的讀法。建議 fix。 → 使用者 picked「Fix，跑第 5 輪」。

## e52 merged（2026-11-24 08:36Z）

PR #56 merged，關閉 #52；master push run 在 d216eb1e 通過（Dev build v0.4.2-dev.17）。guard `EveryImport` 以 check 為單位判定涵蓋，`template_checks.py` 的 import 放在 `LEFT_OUT`（理由在 PR body）。報告 `reports/e52.md`。Now 列：

- **Merge right:** 2026-11-23 22:55 -0800，使用者 picked「開工，CI 過就 merge」（問題：照提案開第三輪的三條 lane 嗎？）：lanes e52、e17、e29。
| e52 | pr | #52 | local_524d3b89-26bb-4cc4-bfe1-b067c354ad7a（落在 `.claude/worktrees/jovial-kapitsa-a8f724`，分支 `claude/lane-e52-366592`） | PR #56 open, waitchecks | — |
| #52 maintainer 工具 import `tools/logfiles.py`，但 coord／dev build／prepush 群組和 `coord-tests.yml` 沒列 | 1 | none | none | `tools/checks_for.py › GROUPS`、`coord-tests.yml › paths:`、`tools/tests/test_checks_for.py` | 第三輪 lane e52 |

## 第三輪結束（2026-11-24 00:37 -0800）

- **Merge right:** 2026-11-23 22:55 -0800，使用者 picked「開工，CI 過就 merge」（問題：照提案開第三輪的三條 lane 嗎？）：lanes e52、e17、e29。

2026-11-24 00:44 -0800 使用者說「Archive 並刪分支」：第三輪三個 lane session（e52、e17、e29）已 archive（worktree 乾淨、都已在 master），三條遠端分支 `claude/lane-e52-366592`、`claude/lane-e17-18146b`、`claude/lane-e29-8c9454` 已刪。

- **第四輪（2026-11-24 04:20 -0800）：** 使用者 picked「1、2、3 都做」。#28 triage 成 ready-for-agent，issue 補了 Decision、Acceptance criteria、Files。

- **PR #57 CI 失敗（since 2026-11-24 04:55 -0800）：** `tools/entries.py` 新增 `import check_save`，讓每個 import entries 的測試都連到 check_save 的整串 import，#56 的 guard 報 38 個缺口。建議退回 e28 修（不 import check_save，或把用到的函式移到不連帶整串的地方），修完再跑 CI。 → 使用者 picked「退回 e28 修」。

## e28 merged（2026-11-25 09:35Z）

PR #57 merged，關閉 #28（選項 1、2、3）；master push run 在 de37903b 通過（Dev build v0.4.2-dev.18）。第一次 CI 的 template-checks 失敗：`entries.py` 新 import `check_save`，#56 的 guard 抓到 38 個缺口；使用者 picked「退回 e28 修」，修正 1ce7ae6 把 report marker helpers 移進 entries.py，CI 全過。報告 `reports/e28.md`。Now 列：

| e28 | pr | #28 | local_18b5216e-470a-4017-aafa-15f4848e9bfd（落在 `.claude/worktrees/lane-823-251cbd`，分支 `claude/lane-e28-194730`，基於 d216eb1） | working：使用者 picked「退回 e28 修」，已送修正請求（entries.py 不 import check_save）；push 後 PR #57 重跑 CI | — |
| #28 Output 對 entry 的檢查只在 audit 跑 | 1 | none | none | `tools/check.py`、`tools/entries.py`、`modes/consolidate.md`、`interview.md`、`stories.md`、`write.md` | 第四輪 lane e28（選項 1、2、3） |

## 第四輪結束（2026-11-25 01:36 -0800）

- **Merge right:** 2026-11-24 04:20 -0800，使用者 picked「1、2、3 都做」（問題：#28 要照建議先做選項 1 和 3 嗎？；問題前說明選好後照前三輪的做法開 lane、CI 過就 merge）：lane e28。

2026-11-25 02:12 -0800 使用者說「都做」：e28 session 已 archive（worktree 乾淨、已在 master），遠端分支 `claude/lane-e28-194730` 已刪；Log 升到最新 Dev build 的 prompt 寫進私人記錄的 prompts/。

2026-11-25 15:23 -0800 Log 升級（使用者自己開的 session）：0.4.2-dev.1 → 0.4.2-dev.18，plan 沒有 stop／removed／edited／overwritten 行；plan 後和 push 前都停下等 yes；Dev build 警告只說一次（plan 訊息）；升級指南回 nothing left to migrate；audit 和升級前相比沒有新行。coordinator 核對過 Log repo：版本、commit 已 push、升級暫存已清。

- **第五輪（2026-11-26 16:44 -0800）：** 使用者 picked「開工，CI 過就 merge」。#58 triage 成 ready-for-agent。

## e58 merged（2026-11-27 01:11Z）

PR #59 merged，關閉 #58；master push run 在 983ece73 通過（Dev build v0.4.2-dev.19）。import guard 在 tools/、maintainer/、docs/upgrades/ 的任何 .py 改動時都跑；test_checks_for.py 從 122 s 降到 9 s。報告 `reports/e58.md`。Now 列：

| e58 | pr | #58 | local_74820ac2-90e9-4915-baca-bbac4768c7ec（使用者從卡片開，分支 `claude/wonderful-neumann-98dc7a`） | PR open, waitchecks | — |
| #58 本機改了某檔的 import 時不跑 import guard（`EveryImport`） | 1 | none | none | `tools/checks_for.py › GROUPS`、`checks-for-tests.yml › paths:` | 第五輪 lane e58 |

## 第五輪結束（2026-11-26 17:12 -0800）

- **Merge right:** 2026-11-26 16:44 -0800，使用者 picked「開工，CI 過就 merge」（問題：要現在開一輪做 #58 嗎？）：lane e58。
