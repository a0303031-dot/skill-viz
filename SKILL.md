---
name: skill-viz
description: 把一個 skill、plugin 或規格庫資料夾視覺化成單檔互動 HTML（流程型 skill 出「技能地圖」，大量平行規格出「圖鑑」），產出放輸出根目錄（預設 ~/SSSKill，可設定）。觸發：視覺化、幫我視覺化、幫我視覺化 XXX、把 XXX skill 視覺化、skill 地圖、skill 圖鑑、技能地圖、這個 skill 長什麼樣、畫出這個 skill 的結構、/skill-viz。對象是 skill 名稱、skill 資料夾路徑、plugin 或規格庫時用這個；只是要把當前討論畫成一張圖解釋，不走這裡（用 show-me 之類的解釋圖方式）。
---

# skill-viz：skill 視覺化

把一個 skill（或規格庫資料夾）讀懂後，做成一頁可以搜尋、點開、深淺色切換的單檔 HTML，放到 `<輸出根目錄>/<名稱>/`。

| 版型 | 適用 | 例子 |
|---|---|---|
| `map` 技能地圖 | 有 SKILL.md 的流程型或說明型 skill：模式、步驟、規則、參考檔、指令 | 稽核類 skill 的六階段流程、圖表類 skill 的五種圖型與 CLI |
| `catalog` 圖鑑 | 一大堆結構相同的平行規格（例如 99 份 STYLE.md） | 風格庫、範本庫、prompt 庫 |

下文的 `<skill 目錄>` 是這份 SKILL.md 所在的資料夾。腳本在 `<skill 目錄>/scripts/`，執行時一律加環境變數 `PYTHONUTF8=1`：

| 腳本 | 用途 |
|---|---|
| `scan_skill.py` | 掃描資料夾，給檔案、章節樹、互相引用與版型建議 |
| `new.py` | 產生 `_build/` 骨架（map：content.json＋build.py；catalog：zh_tw.json＋extract.py），文字全是「（待填）」 |
| `vizlib.py` | 建置腳本的共用工具：佔位替換 `fill`、結構檢查出錯就停 `stop_if`、呼叫 render 的 `render`、讀 md 表格與程式碼區塊 |
| `render.py` | 套模板產出 HTML，跑品質關卡 |
| `shot.py` | headless Edge／Chrome 截長圖再切段 |
| `textcheck.py` | 檢查任何 md 的破折號與簡體字（不要用 grep 比對中文，會誤報） |
| `regress.py` | 改過模板或關卡後一鍵回歸：自測資料＋輸出根目錄下所有成品，最後重產總覽頁 |
| `index.py` | 產生輸出根目錄的總覽頁 `index.html`，每份成品一張卡片（圖示、說明、審查結論） |

**設定**（`scripts/config.py`）：輸出根目錄依序看環境變數 `SKILL_VIZ_OUT`、`<skill 目錄>/config.json` 的 `outRoot`、最後是 `~/SSSKill`。瀏覽器找不到時用 `SKILL_VIZ_BROWSER` 指定執行檔。

## 第 0 步：確認對象

- 只說「幫我視覺化」沒講對象：看這輪對話剛提到哪個 skill。仍不確定就問一句「要視覺化哪個 skill？」，不要猜。
- 要的是「解釋當前討論」而不是某個 skill：不走這裡。
- 找路徑：專案的 `.claude/skills/<名稱>/` → 個人的 `~/.claude/skills/<名稱>/` → 使用者給的路徑。
- **外部來源**（GitHub 連結、zip、還沒裝的 plugin）：先做安全審查（有審查用的 skill 就用），使用者同意後才讀。本 skill 只讀不執行，但讀之前仍要先審。

## 第 1 步：做過就重建

`<輸出根目錄>/<名稱>/_build/` 已存在：直接跑裡面的 `build.py` 或 `extract.py`。關卡全過就跳到第 5 步。關卡說「對不上上游結構」才回頭補資料。

## 第 2 步：建骨架並掃描

```bash
PYTHONUTF8=1 python <skill 目錄>/scripts/new.py <名稱> --src <資料夾>
```

會印出版型建議與理由，並建好 `_build/scan.json`、手寫資料檔與建置腳本。不要把整個 skill 讀進 context，章節樹要用時從 scan.json 用 `python -c` 取片段。

## 第 3 步：讀重點，填資料

- 讀 SKILL.md 全文。參考檔先看 scan.json 的標題，只讀需要的段落。命令檔（例如 `commands/*.md`）常寫著真正的操作步驟，要讀全文。
- map：編輯 `content.json`（手寫繁中），區塊格式與照抄用的段落對照見 [references/map-blocks.md](references/map-blocks.md)。**能從原檔抽的不要手抄**（檔案卡片、表格列、範例程式碼、統計數字）：在 content.json 放一個整串都是 `"__KEY__"` 的佔位字串，在 build.py 用 `fill(data, {"__KEY__": 值})` 填進去，位置不限。`data.json` 由 build.py 產生，不要手改。
- catalog：填 `zh_tw.json`，按實際結構改 `extract.py` 的 `pick_sections()` 與 `category()`，格式見 [references/catalog-items.md](references/catalog-items.md)。
- 全部區塊的寫法範例在 `tests/fixture_map.json` 與 `tests/fixture_catalog.json`。
- **挑圖示**（`icon`，兩種版型都要）：從 `scripts/icons.py` 挑最接近這個 skill「在做什麼」的一個名稱，不用上游 logo，也不生圖。
- **填安全評估**（`security`，兩種版型都要）：
  - `verdict` 照實寫。跑過正式的安全審查（例如用 SkillSpector 掃描加人工審查的 skill）就填判決與日期；找不到紀錄就寫「未審查」並在 summary 說明，**不要推測判決**；不是 skill（一般專案、規格庫）寫「不適用」。審查紀錄先查 agent 的記憶或專案筆記。
  - `notes` 逐種說明掃到的訊號：讀命中的那幾行，寫為什麼這樣做、碰到哪裡；誤判（例如偵測規則字串、說明文字提到某個字）直接寫誤判。
  - 靜態掃描抓不到語意風險。像「把題目送給外部模型」這種沒有程式碼的外送，要寫進 summary 或 conditions。
- **補 `structure_check()`**：上游改版時要能擋下來。三種常用檢查：數量（參考檔、圖型個數、表格列數）、名稱（頁面寫到的檔名找得到、關鍵規則句還在）、指令清單（解析 CLI 的 usage 和頁面上的指令表比對）。

### 寫說明的規則（每條都踩過）

1. **繁體中文，不用破折號**。上游原文只放原文欄位（`md`、`tagline`、`en`、`raw`），其他欄位都是你寫的繁中。
2. **指令與函式的用途要讀實作，不要從名稱推**。曾經猜某個 `examples` 子命令是「列出範例」，實際上會把 HTML 寫回 skill 自己的資料夾；猜某個 `inspect` 通用，實際只支援一種圖型。看 CLI 的 `case '<指令>'` 分支與它呼叫的函式。
3. **流程說明逐句回原檔核對**：誰執行、讀哪個檔、產出什麼。曾經把某階段的 general agent 寫成 research agent。
4. **文件互相矛盾時，查 schema 或程式碼，頁面分情況照實寫**。曾經遇到命令檔說「座標全要自己算」，查 schema 才知道只有一種圖型如此。
5. 不確定的解讀標「本機解讀，以原文為準」。授權限制（例如 CC BY-NC）放 badges 或 footer。
6. **anti（✕）只放「不要做」的事**；「坑加解法」放 list，否則讀者會把解法誤讀成禁止事項。
7. `stats` 自己給有意義的數字（圖型數、指令數、步驟數），不要只留預設的檔案數與大小。

## 第 4 步：產出

跑 `_build/` 的建置腳本。它會先做 structure_check，再呼叫 render.py。render.py 的關卡，任一項不過就 exit 1：

- 骨架還有「（待填）」，或 `"__KEY__"` 佔位沒被 `fill` 換掉。說明文字裡單獨出現「待填」兩字不算。
- 繁中欄位有破折號或常見簡體字。
- map：未知區塊類型；時間軸與搜尋卡片寫成檔名的字串找不到檔案。
- catalog：項目缺 id、name、summary，或 id 重複。
- `icon` 不是 `scripts/icons.py` 裡的名稱。
- 安全評估：缺 `security`；`verdict` 不是 APPROVE、CAUTION、REJECT、未審查、不適用之一；`scan_skill.py` 掃到的風險訊號（連網路、執行程式、刪檔、讀帳密、安裝套件、改 Claude 設定）有哪一種沒在 `security.notes` 寫說明。通過後頁面自動多一段「安全評估」。

## 第 5 步：截圖驗證

```bash
PYTHONUTF8=1 python <skill 目錄>/scripts/shot.py <html> --out-dir <暫存目錄>
PYTHONUTF8=1 python <skill 目錄>/scripts/shot.py <html> --out-dir <暫存目錄> --light
PYTHONUTF8=1 python <skill 目錄>/scripts/shot.py <html> --out-dir <暫存目錄> --hash file=SKILL.md
```

- 截圖放暫存目錄，不要放進輸出根目錄。逐段看：反引號或星號原樣印出、色塊上的字對比、溢出、空區塊。要細看某一塊就用 PIL 裁切。
- `--hash file=<檔名>` 開 map 的檔案詳情；catalog 用 `--hash <項目 id>`。有 `--hash` 時高度自動用 1400，對話框才會在畫面內。
- headless 最小寬度約 540px，手機 390px 驗不到，回報時照實說。

## 第 6 步：回報

- 給可點的 HTML 連結，說明頁面有哪些區塊。新做的成品要跑一次 `index.py`，總覽頁才會出現它（`regress.py` 也會順便重產）。
- 照實說驗了什麼、沒驗到什麼、修過哪些錯。
- **讀原始碼時發現目標 skill 本身的問題**（文件沒寫的危險指令、文件與程式不一致、和其他 skill 搶觸發詞），另外列出來，問使用者要不要補進目標 skill。得到同意才改，改完用 `textcheck.py` 檢查。
- 不 commit、不發布、不分享，除非使用者要。

## 改 skill-viz 本身時

改了 `templates/`、`render.py`、`textrules.py`、`new.py`、`vizlib.py` 任何一個，跑：

```bash
PYTHONUTF8=1 python <skill 目錄>/scripts/regress.py --shots <暫存目錄>
```

它會跑文字規則自測、用 `tests/` 的兩份自測資料產出全區塊的自測頁、用 `new.py` 建一份暫存骨架確認關卡擋得住且填完能產出、檢查 skill 文件、重跑輸出根目錄下所有成品。**截圖要真的看**：自測頁第一次跑就抓到頁首、統計、提示框標題、表頭換行四個沒轉格式的 bug，既有成品都沒露出來，因為那些欄位剛好沒放程式碼。新增區塊或欄位時，同步加進自測資料。

## 環境的坑（Windows 實測）

- Python 印中文要 `PYTHONUTF8=1`，否則系統內碼會噴 UnicodeEncodeError。
- 需要 Python 3.9 以上與 Pillow（`shot.py` 用）。
- grep 比對中文破折號會誤報，用 `textcheck.py`。
- 用 Python 改含反斜線的檔案，不要走 bash heredoc（反斜線會被吃掉一層）；改完確認那一行。
- Edge 截圖檔有時在程序結束後才落地、設定檔會被鎖一下，shot.py 已內建等待與重試刪除。
- 錨點 `#section` 在無頭截圖不會捲動，shot.py 截整頁長圖再切段。
- 部分 agent 的內建瀏覽器打不開本機檔或 localhost，一律走 shot.py。
