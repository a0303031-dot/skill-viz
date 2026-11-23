# skill-viz

把一個 AI agent skill（或一整包規格文件）做成一頁可以搜尋、點開、深淺色切換的單檔 HTML，方便快速看懂一個 skill 在做什麼、流程怎麼走、有哪些規則與檔案。

裝好之後對 agent 說「**幫我視覺化 XXX**」（XXX 是 skill 名稱或資料夾路徑）就會觸發。

## 會做出兩種頁面

| 版型 | 什麼時候 | 頁面長相 |
|---|---|---|
| 技能地圖 | 一般的 skill：有 SKILL.md、有步驟、規則、參考檔 | 本機規則提示框、流程時間軸、可搜尋的參考檔卡片、指令表、反模式、安全評估、自動產生的檔案清單 |
| 圖鑑 | 一大堆同結構的規格檔（風格庫、範本庫） | 卡片牆，可依分類篩選、搜尋，點開看色票與原文章節；下方附安全評估 |

agent 會自己判斷用哪種。產出的 HTML 是單一檔案，不需網路，雙擊就能開。

## 需要什麼

- 支援 skills 的 agent（例如 Claude Code）。
- Python 3.9 以上，加裝 Pillow（`pip install pillow`）。只有截圖驗證會用到。
- Edge 或 Chrome，給截圖驗證用。找不到時設環境變數 `SKILL_VIZ_BROWSER` 指到瀏覽器執行檔。

不需要 npm、不需要任何雲端服務，所有腳本只讀你指定的資料夾，不執行裡面的任何程式。

## 怎麼安裝

1. 用 `git clone` 或下載解壓縮，把整個 `skill-viz` 資料夾放進 skills 目錄：
   - 個人層（所有專案都能用）：`~/.claude/skills/skill-viz/`
   - 或專案層：`<專案>/.claude/skills/skill-viz/`
2. 重開 agent，確認 skill 清單裡有 `skill-viz`。
3. （選配）改輸出位置：預設產出放 `~/SSSKill/<名稱>/`。想放別處，設環境變數 `SKILL_VIZ_OUT`，或在 skill 資料夾放一份 `config.json`：

   ```json
   { "outRoot": "D:/my-skill-maps" }
   ```

4. （選配）驗證安裝：

   ```bash
   PYTHONUTF8=1 python ~/.claude/skills/skill-viz/scripts/regress.py
   ```

   看到「失敗 0 項」就是好的。它會用內附的自測資料產出兩頁範例，路徑會印在最後一行，可以打開看長相。

## 用之前先知道六件事

1. **它會讀原始碼核對說明**。頁面上的流程與指令說明是 agent 讀過 SKILL.md 與實作後寫的繁中摘要，不確定的地方會標「本機解讀，以原文為準」。
2. **品質關卡會擋東西**：繁中說明有破折號或簡體字、骨架沒填完、頁面提到的檔案不存在，都會讓產出失敗。這是故意的。
3. **外部來源先審查**：要視覺化從網路下載的 skill，先做安全審查再讓 agent 讀。
4. **產出的 HTML 內含本機路徑**：頁尾與「開啟原檔」按鈕會帶原檔的絕對路徑（例如含你的使用者名稱）。頁面要轉給別人前留意這點。
5. **每頁都有安全評估**：寫審查結論（安全審查的判決、未審查或不適用），加上靜態掃描抓到的風險訊號（連網路、執行程式、刪檔、讀帳密、安裝套件、改 Claude 設定）與逐項說明。沒寫就產不出頁面。掃描只看字面，不能取代正式的安全審查。
6. **輸出根目錄有一頁總覽**：`index.html` 把做過的頁面排成卡片牆，每張有內建圖示與審查結論。新做的頁面跑一次 `scripts/index.py`（或回歸測試）就會出現。

## 資料夾內容

```
skill-viz/
├── SKILL.md             # agent 讀的主檔：六個步驟與寫說明的規則
├── README.md            # 這份
├── scripts/             # scan_skill、new、render、shot、textcheck、regress、index、vizlib、icons、config、textrules
├── templates/           # map.html（技能地圖）、catalog.html（圖鑑）、index.html（總覽）
├── references/          # 兩種版型的資料格式說明
└── tests/               # 自測資料，也是全部區塊的寫法範例
```

## 去識別化聲明

本分享版移除了原作者的個人路徑、內部工具名稱與個人設定（`config.json` 不隨包附上）。SKILL.md 裡「曾經踩過」的案例只保留教訓，不含任何專案或客戶資訊。
