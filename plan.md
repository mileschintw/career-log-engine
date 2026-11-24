# Plan

Last updated: 2026-11-23 03:48 -0800（新 coordinator 接手）

只寫現況。做完的搬到 `plan-history.md`，這裡留一行指標；什麼都不刪。下面這些一直留在這份：**Now** 的 session、還沒寫進 repo 文件的 **Rulings**、兩個 **Waiting for the user** 節、**Deadlines**，以及 **Handover** 裡使用者的常駐交代和 merge right。

**這個資料夾是公開的**（`project.md` › Every push is a publication）：不寫 deny list 上的名字（owner 寫 `<owner>`）、不寫 Log 的內容。私人的東西寫在 `D:\Repos\career-log-coord`。

## Handover

- **Coordinator:** title engine-coordinator-b9a6ad, worktree D:\Repos\career-log-engine\.claude\worktrees\engine-coordinator-b9a6ad, id unknown, mode normal. 2026-11-23 03:48 -0800 接手；由上一個 coordinator（local_651b2b18-d78c-4525-946a-c80da1bfbfd6，在私人記錄上做到 #818 的拆分完成）開的 session。
- **Next（2026-11-23 16:49 -0800）：** 第一輪九條 lane 全部 merge（#38–#45、#47）。沒有 lane、沒有鬧鐘。等使用者：下一輪排什麼（#37、#46、#24 等）、要不要寫 Log 升到最新 Dev build 的 prompt（寫到私人記錄）。
- **Standing instructions:**
  - 2026-11-13 16:00：「重新開一次，每個新開的 worker session 都用 model opus、effort high」。之後開的 worker 都用 `model: claude-opus-5-5`、`effort: high`。
  - 2026-10-26：進行中的工作做完後，不要開始新任務；下一步只列出來，等使用者說開工。
  - 2026-10-29：「第一波請一次提出整個 frontier 和後面的依賴鏈，等我同意後再開 session。」
  - Log 的資料工作從不排 lane（`project.md` › Log data work）。
- **Merge right:** none（第一輪的已結束，在 `plan-history.md`〈第一輪結束〉）
- **Unattended log:** none

## Rulings

- **Owner 名稱和公開位址（2026-11-21，使用者 picked「留在名單，網址設例外」）：** GitHub owner 名稱留在 deny list；Engine repo 和 Template 的公開位址（`<owner>/career-log-engine`、`<owner>/career-log-template`）是預期命中，由 allow 檔遮掉，其他命中照舊要處理。
- **快照掃描裡可以留的命中（2026-11-21，使用者 picked「保留」）：** 公開位址之外，`.claude/settings.json:6`、`LICENSE:3`、`tools/template/LICENSE:3`（維護者的 GitHub 帳號名）和 `docs/guide.md:208,209`、`skills/career-log/speaking.md:8,9`（公開的面試指南 URL）可以留。E#21 要給 LICENSE 的例外加 guard。
- **記錄的位置（2026-11-23，使用者 picked「重新開始」「career-log-engine-coord」「我寫交接，開新 session」）：** Engine repo 的 `coord` 從這裡重新開始，舊記錄留在私人的 `D:\Repos\career-log-coord` 當封存；私人的東西（Log 資料 prompt、Mac 測試、會寫到名字的筆記）仍寫那裡。

## Now

"Kind" is `pr`, `run`, `audit` or `spare`, as the relay plugin's `GLOSSARY.md` defines under **Kind**.

| Key | Kind | Issues | Session | State | Parked until |
|---|---|---|---|---|---|

**Main checkout:** none.

## Roadmap

Every open issue, once. "Order" is the wave (1 = can start now). "Kind" is `free`, `limited: <what>` or `parent`, as the relay plugin's `GLOSSARY.md` defines under **Kind**.

| Issue | Order | Blocked by (GitHub) | Same-section wait | Files it owns | Kind |
|---|---|---|---|---|---|
| #17 升級模式：Log 在比最新 release 新的 Dev build 上時跟著舊 release 的工具走 | — | none | none | 缺 Files 節 | 不排 lane：needs-triage；0.4.1 發出去後錯的 `stop:` 不會再出現，剩一個假設 |
| #24 一個 rmtree helper | — | none | none | 多個測試檔和 maintainer 工具 | 不排 lane：優先度低 |
| #28 Output 對 entry 的檢查只在 audit 跑 | — | none | none | 缺 Files 節 | 不排 lane：needs-triage |
| #29 Harness：這個 repo 沒有 Log，agent case 的 copy 要有 Log 來源 | — | none | none | 缺 Files 節 | 不排 lane：needs-triage；決定之前 agent case 用 `template-copy`＋fixture |
| #30 Subagents：Screen 用便宜的模型 | — | none | none | 缺 Files 節 | 不排 lane：Long-term |
| #37 升級模式：Sonnet 沒等使用者 yes 就走過 step 2 的計畫 | — | none | after #27, `skills/career-log/modes/upgrade.md › step 2` | `skills/career-log/modes/upgrade.md › step 2` | 不排 lane：needs-triage，e20 開的；等使用者 |
| #46 `maintainer/*.py` 的 guard 不是每個 maintainer 工具都跑 | — | none | after #22, `maintainer/tests/test_devbuild.py › OneVersionForm`（如果搬） | `coord-tests.yml › paths:`、`tools/checks_for.py › GROUPS` 的 `coord`／`dev build` | 不排 lane：needs-triage，e22 開的；也涵蓋 e32 報告問的「每個 maintainer/*.py 都在 coord 群組的測試」；等使用者 |

## Waiting for the user to be present

none

## Waiting for the user's decision

- **第二輪提案（since 2026-11-23 17:18 -0800）：** e46（#46，triage 成 ready-for-agent）、e37（#37 triage，加一張新 issue：拿掉 step 1 的 Dev build 警告，e27 的建議，併進同一條 lane）、e24（#24）三條並行；問開工和 merge right。
- **Log 升到最新 Dev build 的 prompt（since 2026-11-23 17:18 -0800）：** 要不要寫到私人記錄。

## Deadlines

none
