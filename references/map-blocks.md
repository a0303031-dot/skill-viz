# map 版型的 data.json 格式

頂層欄位：

| 鍵 | 必填 | 說明 |
|---|---|---|
| `title` | 是 | 頁面標題，例如「security-audit 技能地圖」 |
| `icon` | 是 | 內建圖示名稱（`scripts/icons.py`），顯示在頁首、瀏覽器分頁與總覽卡片 |
| `lede` | 否 | 一句話說明，省略時用 SKILL.md 的 description |
| `badges` | 否 | `[{"text": "...", "tone": "warn｜ok｜accent｜"}]`，放審查判決、上游版本、授權 |
| `stats` | 否 | `[[數值, "標籤"], ...]`，省略時自動給檔案數與總篇幅 |
| `sections` | 是 | 區塊段落，見下 |
| `fileKinds` | 否 | 檔案清單的分類規則 `[{"match": "正則", "kind": "代號", "label": "中文"}]`，由上往下第一個符合者勝出，最多 8 色 |
| `files` | 否 | 設 `false` 就不自動加「檔案清單」段落 |
| `footer` | 否 | 頁尾說明，可用 `` `code` `` 與 `**粗體**` |
| `verbatimKeys` | 否 | 額外的原文欄位鍵名（預設 md、tagline、en、raw） |
| `security` | 是 | 安全評估，render.py 據此在檔案清單前加「安全評估」段落。見下方說明 |

`security` 的欄位：

| 鍵 | 必填 | 說明 |
|---|---|---|
| `verdict` | 是 | `APPROVE`、`CAUTION`、`REJECT`（安全審查判決）、`未審查`、`不適用`（不是 skill） |
| `summary` | 是 | 一兩句結論；未審查就寫找不到紀錄與建議 |
| `by`、`date` | 否 | 誰審、哪個版本、日期 |
| `conditions` | 否 | 使用條件清單 |
| `notes` | 視掃描 | `{"network｜exec｜delete｜secrets｜install｜config": "說明"}`，掃到的每一種都要寫，掃不到的會被提醒刪掉 |

訊號由 `scan_skill.py` 產生：程式檔查六種，Markdown 只查 secrets、install、config。點檔案清單的列，詳情視窗也會列出該檔的訊號與行號。

`sections` 每段：`{"id": "anchor", "nav": "導覽列名稱", "title": "標題", "sub": "副標", "blocks": [...]}`。每個 block 都可以加 `"heading"` 在上方放小標題。

所有文字欄位都支援 `` `code` `` 與 `**粗體**`。寫成檔名（例如 `HUNTING.md`）的 chip 會自動連到檔案詳情視窗。

## 區塊類型

| type | 用途 | 欄位 |
|---|---|---|
| `callout` | 本機條件、警告 | `title`, `items[]`, `ordered`(預設 true), `tone`("info" 為藍色，預設橘色) |
| `compare` | 兩三種模式並排比較 | `cards[{title,en,badge,tone,rows:[[k,v]]}]`, `note`, `noteLabel` |
| `timeline` | 階段流程 | `steps[{n,title,en,text,tags:[{label,tone,items[]}]}]`, `end{title,items[],note}` |
| `tiles` | 一組短名詞（類別、角色） | `items[{title,sub}]` |
| `finder` | 可搜尋的卡片（參考檔、子模組） | `placeholder`, `empty`, `items[{title,file,meta,text,chips[]}]` |
| `states` | 狀態、角色、選項卡片 | `items[{title,code,text,tone}]`, `compact` |
| `ladder` | 分級（嚴重度、優先度） | `items[{label,code,text,level:1-5}]`, `note` |
| `cards` | 原則、要點 | `items[{title,text,chips[]}]`, `numbered` |
| `table` | 對照表 | `head[]`, `rows[[]]`, `rowHeader`, `note` |
| `list` | 步驟清單 | `items[]`, `ordered`, `note` |
| `anti` | 反模式（✕）或該做的事（`tone:"do"` 顯示 ✓） | `items[]`, `tone` |
| `note` | 一行小字 | `text` |
| `samples` | 程式碼或格式範例卡片（例如七種圖形長什麼樣） | `items[{title,en,text,lang,raw,empty}]`；`raw` 是原文欄位，原樣顯示在等寬區塊，不轉格式、不受繁中關卡限制 |

timeline 的 tag `tone`：`agent`（藍）、`out`（綠）、`warn`（橘）。items 可以是字串，或 `{"text": "...", "href": "#anchor"}` 做頁內連結。

states 的 `tone`：`red`、`amber`、`gray`、`blue`、`green`（左邊色條）。

ladder 的 `level`：5 最重（深紅）到 1 最輕（灰）。

## 一般流程型 skill 的建議段落

不是每個 skill 都有這些，挑存在的做，沒有就不要硬湊：

1. 本機規則（callout）：SKILL.md 有本機改動或審查條件時放最前面。
2. 什麼時候用（table「情況｜走哪」或 compare）：觸發條件、模式、不適用時改走哪個 skill。
3. 流程（timeline）：每步的「讀」「指令」「產出」三種 tag。
4. 參考檔、子模組或子型別（finder）：每份一張卡，附「什麼時候讀它」，讓人用情境搜尋。
5. 指令（table「指令｜做什麼｜什麼時候用」）：用途要讀實作，危險指令直接寫「別跑」。
6. 規則與分級（cards、states、ladder）。
7. 證據或產出物（states、table）。
8. 反模式與紅線（anti）。
9. 檔案清單（自動）。

對照範例（作者本機做過的兩份，示範同一種內容在不同 skill 怎麼放）：

| 內容 | security-audit | archify |
|---|---|---|
| 本機條件 | callout | callout |
| 模式或分流 | compare（兩種模式） | table（五種情況）＋ compare（兩段式） |
| 步驟 | timeline 六階段，tag：執行者、讀、產出 | timeline Step -1 到 5，tag：讀、指令、產出，end 放交付 checklist |
| 子項目 | finder：10 份領域參考檔 | finder：五種圖型 |
| 分級 | ladder：五級嚴重度 | 無 |
| 證據 | states：三種紀錄狀態 | states：三種證據 |
| 禁止事項 | anti：反模式 | anti：紅線；坑加解法用 list |

## 選區塊的注意事項

- **anti（✕）只放「不要做」的事**。「坑：X。解法：Y。」這種要放 `list`，打叉會讓解法被誤讀成禁止事項。
- table 表頭要換行寫 `<br>`，其他 HTML 不支援。
- 每個文字欄位都支援 `` `code` `` 與 `**粗體**`，包括標題、統計數值、頁首說明。

## 最小範例

```json
{
  "title": "xxx 技能地圖",
  "badges": [{"text": "skill-audit CAUTION（2026-11-11）", "tone": "warn"}],
  "sections": [
    {"id": "flow", "nav": "流程", "title": "流程", "blocks": [
      {"type": "timeline", "steps": [
        {"title": "掃描", "text": "讀進資料夾。", "tags": [{"label": "讀", "items": ["SKILL.md"]}, {"label": "產出", "tone": "out", "items": ["scan.json"]}]}
      ]}
    ]}
  ],
  "fileKinds": [{"match": "^SKILL\\.md$", "kind": "skill", "label": "入口"}, {"match": "\\.py$", "kind": "script", "label": "腳本"}]
}
```
