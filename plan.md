# Plan

Last updated: 2026-11-23 03:48 -0800（新 coordinator 接手）

只寫現況。做完的搬到 `plan-history.md`，這裡留一行指標；什麼都不刪。下面這些一直留在這份：**Now** 的 session、還沒寫進 repo 文件的 **Rulings**、兩個 **Waiting for the user** 節、**Deadlines**，以及 **Handover** 裡使用者的常駐交代和 merge right。

**這個資料夾是公開的**（`project.md` › Every push is a publication）：不寫 deny list 上的名字（owner 寫 `<owner>`）、不寫 Log 的內容。私人的東西寫在 `D:\Repos\career-log-coord`。

## Handover

- **Coordinator:** title engine-coordinator-b9a6ad, worktree D:\Repos\career-log-engine\.claude\worktrees\engine-coordinator-b9a6ad, id unknown, mode normal. 2026-11-23 03:48 -0800 接手；由上一個 coordinator（local_651b2b18-d78c-4525-946a-c80da1bfbfd6，在私人記錄上做到 #818 的拆分完成）開的 session。
- **Next（2026-11-23）：** 接手時跑過 `ready`（沒有 lane），比對過 `gh issue list`（開著的 issue 和 Roadmap 一致）、`gh pr list`（沒有開著的 PR）、`git branch -r`（`claude/lane-*` 八條遠端分支都已併進 `master`）。沒有 lane、沒有鬧鐘。使用者確認了三件決定（見 `plan-history.md`），#31–#33 已開，13 個 lane session 已 archive，8 條分支已刪。第一輪已開工（merge right 見下）：e33、e15、e20、e21、e23 在跑；e27、e31、e32、e22 是卡片，app 一次最多開 5 個，等使用者按卡片。卡片開的 session 分支名由 app 取，對 Now 表時看 session 的 branch。
- **Standing instructions:**
  - 2026-11-13 16:00：「重新開一次，每個新開的 worker session 都用 model opus、effort high」。之後開的 worker 都用 `model: claude-opus-5-5`、`effort: high`。
  - 2026-10-26：進行中的工作做完後，不要開始新任務；下一步只列出來，等使用者說開工。
  - 2026-10-29：「第一波請一次提出整個 frontier 和後面的依賴鏈，等我同意後再開 session。」
  - Log 的資料工作從不排 lane（`project.md` › Log data work）。
- **Merge right:** 2026-11-23 15:14 -0800，使用者 picked「開工，CI 過就 merge」（問題：照提案開第一輪的 9 條 lane 嗎？）：lanes e33、e15、e20、e21、e23、e27、e31、e32、e22。
- **Unattended log:** none

## Rulings

- **Owner 名稱和公開位址（2026-11-21，使用者 picked「留在名單，網址設例外」）：** GitHub owner 名稱留在 deny list；Engine repo 和 Template 的公開位址（`<owner>/career-log-engine`、`<owner>/career-log-template`）是預期命中，由 allow 檔遮掉，其他命中照舊要處理。
- **快照掃描裡可以留的命中（2026-11-21，使用者 picked「保留」）：** 公開位址之外，`.claude/settings.json:6`、`LICENSE:3`、`tools/template/LICENSE:3`（維護者的 GitHub 帳號名）和 `docs/guide.md:208,209`、`skills/career-log/speaking.md:8,9`（公開的面試指南 URL）可以留。E#21 要給 LICENSE 的例外加 guard。
- **記錄的位置（2026-11-23，使用者 picked「重新開始」「career-log-engine-coord」「我寫交接，開新 session」）：** Engine repo 的 `coord` 從這裡重新開始，舊記錄留在私人的 `D:\Repos\career-log-coord` 當封存；私人的東西（Log 資料 prompt、Mac 測試、會寫到名字的筆記）仍寫那裡。

## Now

"Kind" is `pr`, `run`, `audit` or `spare`, as the relay plugin's `GLOSSARY.md` defines under **Kind**.

| Key | Kind | Issues | Session | State | Parked until |
|---|---|---|---|---|---|
| e33 | pr | #33 | local_abb44ce2-5b42-4ddf-974a-5208f544844d（落在已 archive 的 `.claude/worktrees/lane-e18-c7297e`，分支 `claude/lane-e33-*`） | started | — |
| e15 | pr | #15 | local_c068efcd-7d35-45a8-a8de-e767f7bb9f52（落在已 archive 的 `.claude/worktrees/lane-e14-296d3a`，分支 `claude/lane-e15-*`） | started | — |
| e20 | pr | #20 | local_bbf40246-872b-40df-b77c-682c478b5ee5（落在已 archive 的 `.claude/worktrees/lane-e8-2d4a83`，分支 `claude/lane-e20-*`） | started | — |
| e21 | pr | #21 | local_6dca5a18-ff19-4fdd-91bb-7b06a4b65673（落在已 archive 的 `.claude/worktrees/lane-e7-af6541`，分支 `claude/lane-e21-*`） | started | — |
| e23 | pr | #23 | local_a4f94a65-33f2-4e28-b6e1-0f9bb83fd226（落在已 archive 的 `.claude/worktrees/lane-825-379001`，分支 `claude/lane-e23-*`） | started | — |
| e27 | pr | #27 | 卡片 task_2e9a3682，等使用者按（app 一次最多 5 個在跑） | not started | — |
| e31 | pr | #31 | 卡片 task_d54a03ac，等使用者按 | not started | — |
| e32 | pr | #32 | 卡片 task_396ec7b4，等使用者按 | not started | — |
| e22 | pr | #22 | 卡片 task_bf318c97，等使用者按 | not started | #33 merges（GO #e22） |

**Main checkout:** none.

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free`, `limited: <what>` or `parent`, as the relay plugin's `GLOSSARY.md` defines under **Kind**.

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #15 Log 在 Dev build 上時 check.py 沒有 update 行 | 1 | none | none | `tools/check.py`、`tools/tests/test_check.py` | 第一輪 lane e15 |
| #17 升級模式：Log 在比最新 release 新的 Dev build 上時跟著舊 release 的工具走 | — | none | none | 缺 Files 節 | 不排 lane：needs-triage；0.4.1 發出去後錯的 `stop:` 不會再出現，剩一個假設 |
| #20 既有 Log 升級後 front page 的 Upstream／Upgrade 兩段是舊文字 | 1 | none | none | `tools/upgrade.py`、`modes/upgrade.md` | 第一輪 lane e20 |
| #21 pre-push：hook 檔頭的舊安裝指令、LICENSE 例外的 guard | 1 | none | none | `maintainer/hooks/pre-push`、`maintainer/tests/test_prepush.py` | 第一輪 lane e21 |
| #22 版本字串只定義一次 | 2 | none | after #33, `tools/tests/test_upgrade.py › Export` | `maintainer/devbuild.py`、`tools/tests/test_upgrade.py`、`maintainer/tests/test_devbuild.py` | 第一輪 lane e22，parked until #33 merges |
| #23 兩個 repo 位址的 guard | 1 | none | none | `tools/skill_lint.py` 或測試、`maintainer/coord.py` | 第一輪 lane e23 |
| #24 一個 rmtree helper | — | none | none | 多個測試檔和 maintainer 工具 | 不排 lane：優先度低 |
| #27 升級模式：舊版 Log 升到 Dev build 時讀不到「不保證穩定」的警告 | 1 | none | none | `skills/career-log/modes/upgrade.md › step 2` | 第一輪 lane e27 |
| #28 Output 對 entry 的檢查只在 audit 跑 | — | none | none | 缺 Files 節 | 不排 lane：needs-triage |
| #29 Harness：這個 repo 沒有 Log，agent case 的 copy 要有 Log 來源 | — | none | none | 缺 Files 節 | 不排 lane：needs-triage；決定之前 agent case 用 `template-copy`＋fixture |
| #30 Subagents：Screen 用便宜的模型 | — | none | none | 缺 Files 節 | 不排 lane：Long-term |
| #31 `config.py set`：檔裡沒有的欄位加在檔尾、沒有註解 | 1 | none | none | `tools/config.py › set_field`、`tools/tests/test_config.py` | 第一輪 lane e31 |
| #32 關 blank issue；#18 的 guard 測試對每個 maintainer 工具都跑 | 1 | none | none | `.github/ISSUE_TEMPLATE/config.yml`（新）、`tools/checks_for.py › GROUPS` 的 `coord` 群組、`coord-tests.yml › paths:` | 第一輪 lane e32 |
| #33 匯出帶的檢查在 Template 和每個 Log 裡 fail（讀只在原始碼的檔） | 1 | none | none | `tools/skill_lint.py`、`tools/tests/test_skill_lint.py`、`test_logfiles.py › TableHelpers`、`test_checks_for.py › Typical`、`test_upgrade.py › Source／Export／NextGuide`、匯出用的 workflow 和它在 `checks_for.py` map 的項目 | 第一輪 lane e33 |

## Waiting for the user to be present

none

## Waiting for the user's decision

- **四張 lane 卡片（since 2026-11-23）：** e27、e31、e32、e22 等使用者按卡片開 session（e22 開了會 park 到 #33 merge）。

## Deadlines

none
