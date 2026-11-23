"""產生輸出根目錄的總覽頁 index.html：每份成品一張卡片（圖示、名稱、說明、版型、審查結論、建置時間）。

用法：python index.py
資料來自各成品 _build/page.json（render.py 全過關卡時寫入）。有 _build/ 卻沒有 page.json 的，列成「尚未產出」。
regress.py 跑完會自動重產一次。只讀 page.json，不執行任何成品的建置腳本。
"""
import json
import sys
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from config import out_root  # noqa: E402
from icons import ICONS, svg  # noqa: E402
from render import VERDICTS  # noqa: E402

TEMPLATE = HERE.parent / "templates" / "index.html"


def collect(root):
    pages, missing = [], []
    for build in sorted(root.glob("*/_build")):
        name = build.parent.name
        pj = build / "page.json"
        if not pj.exists():
            missing.append(name)
            continue
        p = json.loads(pj.read_text(encoding="utf-8"))
        if not (build.parent / p["html"]).exists():
            missing.append(name)
            continue
        p["dir"] = name
        p["href"] = f"{name}/{p['html']}"
        p["iconSvg"] = svg(p["icon"], 28) if p.get("icon") in ICONS else ""
        pages.append(p)
    pages.sort(key=lambda p: p["title"].lower())
    return pages, missing


def build(root=None):
    root = Path(root or out_root())
    pages, missing = collect(root)
    data = {"title": "skill-viz 總覽", "lede": f"`{root.as_posix()}` 底下用 skill-viz 做過的頁面。點卡片打開，上方可依審查結論篩選。",
            "pages": pages, "missing": missing, "tones": VERDICTS, "verdictOrder": list(VERDICTS),
            "footer": "由 skill-viz 的 `index.py` 產生，資料來自各成品 `_build/page.json`。審查結論照各頁的安全評估，不是本頁重新判斷。"}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    fav = "data:image/svg+xml," + quote(svg("compass", 32, "#d0592f"))
    html = TEMPLATE.read_text(encoding="utf-8").replace("__TITLE__", data["title"]).replace("__FAVICON__", fav) \
        .replace("/*__DATA__*/null", payload)
    out = root / "index.html"
    out.write_text(html, encoding="utf-8")
    return out, pages, missing


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    out, pages, missing = build()
    print(f"總覽：{len(pages)} 份成品" + (f"，尚未產出 {len(missing)} 份：{'、'.join(missing)}" if missing else "") + f"，輸出 {out}")


if __name__ == "__main__":
    main()
