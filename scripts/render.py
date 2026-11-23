"""把資料 JSON 套進 skill-viz 模板，產出單檔 HTML，並跑品質關卡。

用法：
    python render.py --type map     --data data.json --out out.html --scan <skill 資料夾>
    python render.py --type catalog --data data.json --out out.html --scan <規格庫資料夾>

關卡（任一不過就回 exit 1，HTML 仍會寫出方便檢查）：
  0. 不得留有骨架標記「（待填）」或沒換掉的佔位標記 __KEY__。
  1. 含中文的字串不得有破折號（—、―）。
  2. 含中文的字串不得出現常見簡體字。
     1、2 跳過原文欄位（md、tagline、en、raw，或 data.verbatimKeys 指定的鍵），上游原文只准放在這些鍵。
  3. map：時間軸標籤與搜尋卡片裡寫成檔名的字串，必須真的存在於掃描結果。
  4. catalog：每個項目要有 id、name、summary，id 不得重複。
  5. 安全評估：data.security 要有 verdict（APPROVE／CAUTION／REJECT／未審查／不適用）與 summary，
     scan_skill 掃到的每種風險訊號都要在 security.notes 寫說明。通過後自動在頁面加「安全評估」段落。
  6. icon 要是 icons.py 裡的名稱，顯示在頁首、瀏覽器分頁與總覽卡片。
成品（data.json 在 _build/ 裡）全過關卡後，會在 _build/ 寫一份 page.json，給 index.py 產總覽頁。
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scan_skill import RISK_KINDS, scan  # noqa: E402
from icons import ICONS, listing as icon_listing, svg as icon_svg  # noqa: E402
from datetime import datetime  # noqa: E402
from urllib.parse import quote  # noqa: E402
from textrules import problems  # noqa: E402

TEMPLATES = HERE.parent / "templates"
BLOCK_TYPES = {"callout", "compare", "timeline", "tiles", "finder", "states", "ladder", "cards", "table", "list", "anti", "note", "files", "samples"}
FILE_LIKE = re.compile(r"^[\w./-]+\.(md|json|cjs|js|mjs|py|ps1|sh|txt|yaml|yml)$")


# 上游原文只能放在這些鍵，關卡不檢查（引用原文不改字）。其餘鍵都是我們寫的繁中，一律檢查。
VERBATIM_KEYS = {"md", "tagline", "en", "raw"}
TODO = "（待填）"  # new.py 骨架用的標記，說明文字裡單獨出現「待填」兩字不算
PLACEHOLDER = re.compile(r"^__[A-Z0-9_]+__$")  # content.json 的佔位標記，見 vizlib.fill


def walk_strings(o, path="$", skip=VERBATIM_KEYS):
    if isinstance(o, str):
        yield path, o
    elif isinstance(o, dict):
        for k, v in o.items():
            if k in skip:
                continue
            yield from walk_strings(v, f"{path}.{k}", skip)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk_strings(v, f"{path}[{i}]", skip)


def text_gates(data):
    errs = []
    skip = VERBATIM_KEYS | set(data.get("verbatimKeys", []))
    for p, s in walk_strings(data, skip=skip):
        for prob in problems(s):
            errs.append(f"{prob}：{p} → {s[:40]}")
    for p, s in walk_strings(data, skip=set()):
        if TODO in s:
            errs.append(f"骨架沒填完：{p} → {s[:40]}")
        if PLACEHOLDER.match(s):
            errs.append(f"佔位標記沒換掉（build.py 的 fill 沒給）：{p} → {s}")
    return errs


def map_gates(data, sc):
    errs = []
    names = {f["path"] for f in sc["files"]}
    bases = {}
    for n in names:
        bases.setdefault(n.rsplit("/", 1)[-1], []).append(n)

    def ok(t):
        return t in names or len(bases.get(t, [])) == 1

    for si, sec in enumerate(data.get("sections", [])):
        if not sec.get("id") or not sec.get("blocks"):
            errs.append(f"sections[{si}] 缺 id 或 blocks")
        for bi, b in enumerate(sec.get("blocks", [])):
            where = f"{sec.get('id')}.blocks[{bi}]({b.get('type')})"
            if b.get("type") not in BLOCK_TYPES:
                errs.append(f"{where}：未知區塊類型，可用 {sorted(BLOCK_TYPES)}")
            if b.get("type") == "timeline":
                for st in b.get("steps", []):
                    for t in st.get("tags", []):
                        for x in t.get("items", []):
                            txt = x if isinstance(x, str) else x.get("text", "")
                            if FILE_LIKE.match(txt) and not ok(txt) and not t.get("label", "").startswith("產出"):
                                errs.append(f"{where}：找不到檔案 {txt}")
            if b.get("type") == "finder":
                for it in b.get("items", []):
                    f = it.get("file")
                    if f and not ok(f):
                        errs.append(f"{where}：找不到檔案 {f}")
    return errs


VERDICTS = {"APPROVE": "green", "CAUTION": "amber", "REJECT": "red", "未審查": "gray", "不適用": "gray"}


def risk_groups(sc):
    """{kind: [(path, [行號...]), ...]}，依 RISK_KINDS 的順序。"""
    out = {}
    for k in RISK_KINDS:
        hits = [(f["path"], r["lines"]) for f in sc["files"] for r in f.get("risks", []) if r["kind"] == k]
        if hits:
            out[k] = sorted(hits, key=lambda h: -len(h[1]))
    return out


def security_gates(data, sc):
    sec = data.get("security")
    if not isinstance(sec, dict):
        return ["缺 security（安全評估）：至少要有 verdict、summary，掃到的每種風險訊號都要在 notes 寫說明，格式見 map-blocks.md"], []
    errs, warns = [], []
    if sec.get("verdict") not in VERDICTS:
        errs.append(f"security.verdict 要是 {list(VERDICTS)} 其中之一，目前是 {sec.get('verdict')!r}")
    if not sec.get("summary"):
        errs.append("security.summary 沒寫：一兩句說明審查結論或為什麼沒審")
    groups = risk_groups(sc)
    notes = sec.get("notes", {})
    for k, hits in groups.items():
        if not notes.get(k):
            errs.append(f"安全評估：掃到「{RISK_KINDS[k][0]}」訊號（{len(hits)} 個檔，例如 {hits[0][0]}），security.notes.{k} 要寫說明")
    for k in notes:
        if k not in RISK_KINDS:
            errs.append(f"security.notes.{k} 不是已知的訊號種類，可用 {list(RISK_KINDS)}")
        elif k not in groups:
            warns.append(f"security.notes.{k} 對應的訊號這次沒掃到，可以刪掉或改寫")
    return errs, warns


def security_section(sec, sc, top=5):
    v = sec["verdict"]
    meta = sec_meta(sec)
    blocks = [{"type": "states", "items": [{"title": f"審查結論：{v}", "code": meta, "text": sec["summary"], "tone": VERDICTS[v]}]}]
    if sec.get("conditions"):
        blocks.append({"type": "list", "heading": "使用條件", "items": sec["conditions"]})
    rows = []
    for k, hits in risk_groups(sc).items():
        where = "<br>".join(f"`{p}`：{'、'.join(map(str, ls[:6]))}{'…' if len(ls) > 6 else ''}" for p, ls in hits[:top])
        if len(hits) > top:
            where += f"<br>另有 {len(hits) - top} 個檔"
        rows.append([f"**{RISK_KINDS[k][0]}**<br>{len(hits)} 檔<br>{sum(len(ls) for _, ls in hits)} 行", where, sec["notes"][k]])
    tip = SAFETY_TIP
    if rows:
        blocks.append({"type": "table", "heading": "靜態掃描的風險訊號", "head": ["訊號", "主要位置（檔案：行號）", "說明"],
                       "rows": rows, "note": tip})
    else:
        blocks.append({"type": "note", "text": "靜態掃描沒有抓到風險訊號。" + tip})
    return {"id": "safety", "nav": "安全", "title": "安全評估", "sub": SAFETY_SUB, "blocks": blocks}


def sec_meta(sec):
    """審查者與日期，顯示在等寬小字裡，不轉格式，所以先拿掉反引號。"""
    return "，".join(x for x in (sec.get("by"), sec.get("date")) if x).replace("`", "")


SAFETY_SUB = "審查結論加上掃描抓到的風險訊號。訊號不等於問題，說明欄寫的是本機判讀。"
SAFETY_TIP = ("靜態掃描只看字面：連網路、執行程式、刪檔、讀帳密、安裝套件、改 Claude 設定。程式檔六種都查，Markdown 只查後三種。"
              "抓不到語意上的問題（例如文件說只讀、程式其實會改檔），結論以審查為準。")


def security_view(sec, sc, top=5):
    """catalog 模板用的扁平資料。"""
    v = sec["verdict"]
    rows = [{"label": RISK_KINDS[k][0], "range": f"{len(hits)} 個檔，{sum(len(ls) for _, ls in hits)} 行",
             "where": [f"{p}：{'、'.join(map(str, ls[:6]))}{'…' if len(ls) > 6 else ''}" for p, ls in hits[:top]]
             + ([f"另有 {len(hits) - top} 個檔"] if len(hits) > top else []), "note": sec["notes"][k]}
            for k, hits in risk_groups(sc).items()]
    return {"verdict": v, "tone": VERDICTS[v], "meta": sec_meta(sec),
            "summary": sec["summary"], "conditions": sec.get("conditions", []), "rows": rows, "sub": SAFETY_SUB, "tip": SAFETY_TIP}


def catalog_gates(data):
    errs, seen = [], set()
    for i, it in enumerate(data.get("items", [])):
        for k in ("id", "name", "summary"):
            if not it.get(k):
                errs.append(f"items[{i}] 缺 {k}")
        if it.get("id") in seen:
            errs.append(f"items[{i}] id 重複：{it.get('id')}")
        seen.add(it.get("id"))
    if not data.get("items"):
        errs.append("items 是空的")
    return errs


def slim_scan(sc):
    files = []
    for f in sc["files"]:
        g = {k: f[k] for k in ("path", "bytes", "lines", "refs", "refsIn") if k in f}
        if f.get("risks"):
            g["risks"] = [[RISK_KINDS[r["kind"]][0], r["lines"][:12]] for r in f["risks"]]
        g["headings"] = [{"level": h["level"], "text": h["text"]} for h in f.get("headings", []) if h["level"] <= 3][:40]
        files.append(g)
    return {k: sc[k] for k in ("root", "name", "description", "fileCount", "totalBytes")} | {"files": files}


def write_manifest(a, data, out):
    """成品（data.json 在某個 _build/ 裡）通過關卡後，留一份 page.json 給 index.py 做總覽。自測資料不寫。"""
    build = Path(a.data).resolve().parent
    if build.name != "_build":
        return
    sec = data.get("security", {})
    n = len(data.get("items", [])) if a.type == "catalog" else len(data.get("sections", []))
    page = {"title": data.get("title", ""), "lede": data.get("lede") or data.get("scan", {}).get("description", ""),
            "icon": data.get("icon"), "type": a.type, "count": n, "verdict": sec.get("verdict"),
            "verdictDate": sec.get("date", ""), "html": out.resolve().relative_to(build.parent).as_posix(),
            "built": datetime.now().strftime("%Y-%m-%d %H:%M")}
    (build / "page.json").write_text(json.dumps(page, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", choices=["map", "catalog"], required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scan", help="必填：要掃描的來源資料夾（列檔案與安全評估用）")
    a = ap.parse_args()

    data = json.loads(Path(a.data).read_text(encoding="utf-8"))
    if not a.scan:
        sys.exit("需要 --scan <來源資料夾>：map 用來列檔案，兩種版型都用來做安全評估")
    sc = scan(a.scan)
    errs = text_gates(data)
    sec_errs, warns = security_gates(data, sc)
    errs += sec_errs
    if a.type == "map":
        errs += map_gates(data, sc)
        data["scan"] = slim_scan(sc)
        if not sec_errs:
            data["sections"] = data.get("sections", []) + [security_section(data["security"], sc)]
    else:
        errs += catalog_gates(data)
        if not sec_errs:
            data["securityView"] = security_view(data["security"], sc)
    icon = data.get("icon")
    if icon not in ICONS:
        errs.append(f"icon 要從內建圖示挑一個，目前是 {icon!r}。可用：{icon_listing()}")
    else:
        data["iconSvg"] = icon_svg(icon, 30)

    tpl = (TEMPLATES / f"{a.type}.html").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    title = data.get("title", "skill-viz")
    favicon = "data:image/svg+xml," + quote(icon_svg(icon, 32, "#d0592f")) if icon in ICONS else ""
    html = (tpl.replace("__TITLE__", title.replace("<", "&lt;")).replace("__FAVICON__", favicon)
            .replace("/*__DATA__*/null", payload))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    if not errs:
        write_manifest(a, data, out)

    n = len(data.get("items", [])) if a.type == "catalog" else sum(len(s.get("blocks", [])) for s in data.get("sections", []))
    unit = "個項目" if a.type == "catalog" else "個區塊"
    print(f"{a.type}：{title}，{n} {unit}，輸出 {out}（{out.stat().st_size // 1024} KB）")
    for w in warns:
        print("提醒：" + w)
    if errs:
        print(f"品質關卡未過（{len(errs)} 項）：")
        for e in errs[:30]:
            print("  - " + e)
        sys.exit(1)
    print("品質關卡：通過")


if __name__ == "__main__":
    main()
