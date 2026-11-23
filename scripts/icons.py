"""內建圖示：一組本機手繪的簡單線條符號（24×24、線寬 1.8、顏色跟著主題），頁首、瀏覽器分頁小圖與總覽卡片共用。

資料裡寫 "icon": "<名稱>"，名稱必須在 ICONS 裡。挑最接近 skill「在做什麼」的一個，不求寫實。
不放上游的 logo（商標與授權問題），也不用生圖（風格不一致、單檔 HTML 會變大）。
"""
ICONS = {
    "map": ("地圖", '<path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2z"/><path d="M9 4v14M15 6v14"/>'),
    "flow": ("流程圖", '<rect x="3" y="4" width="6" height="5" rx="1"/><rect x="15" y="15" width="6" height="5" rx="1"/><path d="M6 9v4a2 2 0 0 0 2 2h7"/>'),
    "shield": ("盾牌，安全", '<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/>'),
    "search": ("放大鏡，查找", '<circle cx="11" cy="11" r="6"/><path d="M16 16l4 4"/>'),
    "clock": ("時鐘，時間範圍", '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'),
    "globe": ("地球，網路", '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/>'),
    "palette": ("調色盤，風格", '<path d="M12 3a9 9 0 1 0 0 18c1.1 0 1.5-.8 1.5-1.6 0-1.3-1-1.6-1-2.9 0-1 .8-1.5 1.8-1.5H17a4 4 0 0 0 4-4c0-4.4-4-8-9-8z"/><circle cx="7.5" cy="11" r="1"/><circle cx="10" cy="7" r="1"/><circle cx="15" cy="7.5" r="1"/>'),
    "brain": ("大腦，推理", '<path d="M10 4a3 3 0 0 0-3 3 3 3 0 0 0-2.5 4.5A3 3 0 0 0 6 17a3 3 0 0 0 4 3V4z"/><path d="M14 4a3 3 0 0 1 3 3 3 3 0 0 1 2.5 4.5A3 3 0 0 1 18 17a3 3 0 0 1-4 3V4z"/>'),
    "eye": ("眼睛，看懂", '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>'),
    "chart": ("長條圖，數據", '<path d="M4 4v16h16"/><path d="M8 16v-4M12 16V8M16 16V11"/>'),
    "image": ("圖片", '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>'),
    "film": ("影片", '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4"/>'),
    "book": ("書，文件庫", '<path d="M5 4h12a2 2 0 0 1 2 2v14H7a2 2 0 0 1-2-2z"/><path d="M5 18a2 2 0 0 1 2-2h12"/>'),
    "doc": ("文件", '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>'),
    "terminal": ("終端機，CLI", '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 9l3 3-3 3M13 15h4"/>'),
    "code": ("程式碼", '<path d="M9 7l-5 5 5 5M15 7l5 5-5 5"/>'),
    "layers": ("圖層，多層架構", '<path d="M12 3l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>'),
    "compass": ("指南針，導覽", '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>'),
    "chat": ("對話", '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9h8M8 12h5"/>'),
    "gear": ("齒輪，設定與自動化", '<circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/>'),
}


def svg(name, size=24, color="currentColor"):
    body = ICONS[name][1]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
            f'stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>')


def listing():
    return "、".join(f"{k}（{v[0]}）" for k, v in ICONS.items())
