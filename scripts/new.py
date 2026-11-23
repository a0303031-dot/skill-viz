"""產生 SSSKill/<名稱>/_build/ 骨架，省掉照抄範例的功夫。

用法：
    python new.py <名稱> --src <skill 或規格庫資料夾> [--type map|catalog]
不給 --type 就用掃描的版型建議。已存在的 _build 不會覆蓋（加 --force 才會）。

產出：
  map     → scan.json、content.json（手寫繁中的段落骨架，文字都是「（待填）」）、build.py（結構檢查＋佔位替換＋render，data.json 由它產生）
  catalog → scan.json、zh_tw.json（每個項目的繁中名稱與描述，都是「（待填）」）、extract.py（抽取＋render）
render.py 會擋「（待填）」與沒換掉的 "__KEY__" 佔位，所以骨架沒填完不可能產出頁面。
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scan_skill import RISK_KINDS, scan  # noqa: E402
from config import SCRIPTS, out_root  # noqa: E402

SSSKILL = out_root()
TODO = "（待填）"

MAP_BUILD = '''"""{name} 技能地圖：content.json（手寫繁中）＋ 原檔 → data.json → skill-viz 的 render.py（map 版型）。由 new.py 產生。

用法：python build.py
只讀 {src}，不執行裡面任何腳本。
要從原檔抽的內容（檔案卡片、表格列、範例程式碼、統計數字）：在 content.json 放 "__KEY__" 佔位字串，
在 main() 的 fill 給值，不要手抄進 content.json。共用工具見 skill-viz 的 scripts/vizlib.py。
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
VIZ = Path("{viz}")
sys.path.insert(0, str(VIZ))
from vizlib import fences, fill, numbered, rd, render, stop_if, table_rows  # noqa: E402,F401

SRC = Path("{src}")
OUT = HERE.parent / "{name}-技能地圖.html"


def structure_check():
    """上游改版時要能擋下來的檢查。依這個 skill 的實際結構補，至少一項。
    常用寫法：
      - 數量：參考檔、子命令、表格列、編號規則的個數對不上就報錯（table_rows、numbered 可直接用）
      - 名稱：頁面上寫到的檔名、指令、關鍵規則句，要在原檔裡找得到
      - 指令清單：解析 CLI 的 usage 字串，和頁面上的指令表比對
    """
    errs = []
    for must in ["SKILL.md"]:
        if not (SRC / must).exists():
            errs.append(f"缺 {{must}}")
    return errs


def main():
    stop_if(structure_check())
    data = json.loads(rd(HERE / "content.json"))
    data = fill(data, {{}})  # 例如 {{"__REFS__": refs, "__CMDS__": rows}}
    render("map", data, HERE, OUT, scan=SRC)


if __name__ == "__main__":
    main()
'''

CAT_EXTRACT = '''"""{name} 圖鑑：抽取 {glob} → data.json → skill-viz 的 render.py（catalog 版型）。由 new.py 產生。

用法：python extract.py
只讀 {src}，不執行裡面任何腳本。抽哪些章節、分類從哪來，依實際結構改 pick_sections() 與 category()。
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
VIZ = Path("{viz}")
sys.path.insert(0, str(VIZ))
from vizlib import render, stop_if  # noqa: E402

TODO = "（待填）"
SRC = Path("{src}")
GLOB = "{glob}"
OUT = HERE.parent / "{name}-圖鑑.html"
EXPECTED = {count}  # 項目數，上游增減時要更新
zh = json.loads((HERE / "zh_tw.json").read_text(encoding="utf-8"))


def pick_sections(text):
    """預設取前三個二級章節的原文。"""
    secs = re.findall(r"^## (.+?)\\n(.*?)(?=^## |\\Z)", text, re.M | re.S)
    return [{{"title": zh.get("sections", {{}}).get(t.strip(), t.strip()), "en": t.strip(), "md": b.strip()}} for t, b in secs[:3]]


def category(path):
    return "", "未分類"


def main():
    items, missing = [], []
    for p in sorted(SRC.glob(GLOB)):
        iid = p.parent.name if p.name == Path(GLOB).name else p.stem
        text = p.read_text(encoding="utf-8")
        h1 = re.search(r"^# (.+)$", text, re.M)
        tag = re.search(r"^> (.+)$", text, re.M)
        hexes = list(dict.fromkeys(h.lower() for h in re.findall(r"#[0-9A-Fa-f]{{6}}\\b", text)))
        name, summary = zh["items"].get(iid, ["", ""])
        if not name or TODO in name or not summary or TODO in summary:
            missing.append(iid)
        cat, cat_label = category(p)
        items.append({{"id": iid, "name": name or iid, "en": h1.group(1).strip() if h1 else "", "cat": cat, "catLabel": cat_label,
                      "summary": summary, "tagline": tag.group(1).strip() if tag else "", "palette": hexes[:8],
                      "paletteCount": len(hexes), "kb": round(p.stat().st_size / 1024, 1),
                      "path": str(p).replace("\\\\", "/"), "sections": pick_sections(text)}})
    data = {{"title": "{name} 圖鑑", "icon": zh.get("icon"), "lede": zh.get("lede", ""), "badges": zh.get("badges", []), "unit": zh.get("unit", "個項目"),
            "footer": zh.get("footer", ""), "security": zh.get("security"), "items": items}}
    if len(items) != EXPECTED or missing:
        stop_if([f"項目 {{len(items)}}／預期 {{EXPECTED}}，缺繁中 {{len(missing)}} 個：{{missing[:10]}}"], "zh_tw.json 或 EXPECTED")
    render("catalog", data, HERE, OUT, scan=SRC)


if __name__ == "__main__":
    main()
'''


def file_kinds(sc):
    kinds = []
    if any(f["path"] == "SKILL.md" for f in sc["files"]):
        kinds.append({"match": "^SKILL\\.md$", "kind": "skill", "label": "入口"})
    tops = sorted({f["path"].split("/")[0] for f in sc["files"] if "/" in f["path"]})
    for t in tops[:6]:
        kinds.append({"match": f"^{t}/", "kind": t, "label": TODO + t})
    kinds.append({"match": ".", "kind": "other", "label": "其他"})
    return kinds


def security_skeleton(sc):
    """安全評估骨架：掃到哪幾種風險訊號，notes 就先列哪幾種，逐項寫說明。"""
    kinds = [k for k in RISK_KINDS if any(r["kind"] == k for f in sc["files"] for r in f.get("risks", []))]
    return {
        "verdict": "未審查",
        "by": TODO + "例如「安全審查（SkillSpector 靜態掃描＋人工審查）」或「本機自建」",
        "date": TODO,
        "summary": TODO + "一兩句審查結論；跑過正式安全審查就把 verdict 改成 APPROVE、CAUTION 或 REJECT，不是 skill 就改成「不適用」",
        "conditions": [],
        "notes": {k: TODO + f"「{RISK_KINDS[k][0]}」：為什麼這樣做、碰到哪裡、風險在哪" for k in kinds},
    }


def map_skeleton(name, sc):
    return {
        "title": f"{name} 技能地圖",
        "icon": TODO + "從 scripts/icons.py 挑一個名稱",
        "lede": TODO,
        "badges": [{"text": TODO + "來源、版本、授權或審查判決"}],
        "security": security_skeleton(sc),
        "stats": [[sc["fileCount"], "個檔案"], [f"{sc['totalBytes'] / 1024:.0f} KB", "總篇幅"]],
        "sections": [
            {"id": "local", "nav": "本機規則", "blocks": [{"type": "callout", "title": "本機規則", "items": [TODO + "SKILL.md 的本機改動或審查條件；沒有就刪掉這段"]}]},
            {"id": "when", "nav": "什麼時候用", "title": "什麼時候用", "blocks": [
                {"type": "table", "rowHeader": True, "head": ["情況", "走哪"], "rows": [[TODO, TODO]]}]},
            {"id": "flow", "nav": "流程", "title": "流程", "sub": TODO, "blocks": [
                {"type": "timeline", "steps": [{"title": TODO, "text": TODO, "tags": [{"label": "讀", "items": ["SKILL.md"]}, {"label": "產出", "tone": "out", "items": [TODO]}]}]}]},
            {"id": "rules", "nav": "規則", "title": "規則", "blocks": [{"type": "cards", "items": [{"title": TODO, "text": TODO}]}]},
            {"id": "anti", "nav": "反模式", "title": "反模式", "sub": "看到自己在做這些，就停下來。", "blocks": [{"type": "anti", "items": [TODO + "只放「不要做」的事；坑加解法改用 list"]}]},
        ],
        "fileKinds": file_kinds(sc),
        "footer": "說明是本機整理，以原文為準。檔案、章節、引用關係由掃描自動產生，腳本只看不跑。",
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--src", required=True)
    ap.add_argument("--type", choices=["map", "catalog"])
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    src = Path(a.src).resolve()
    sc = scan(src)
    kind = a.type or sc["shape"]
    build = SSSKILL / a.name / "_build"
    if build.exists() and not a.force:
        sys.exit(f"{build} 已存在。要重建就直接跑裡面的建置腳本；確定要蓋掉才加 --force。")
    build.mkdir(parents=True, exist_ok=True)
    (build / "scan.json").write_text(json.dumps(sc, ensure_ascii=False, indent=1), encoding="utf-8")
    src_s = str(src).replace("\\", "/")
    VIZ_S = str(SCRIPTS).replace("\\", "/")
    if kind == "map":
        (build / "content.json").write_text(json.dumps(map_skeleton(a.name, sc), ensure_ascii=False, indent=1), encoding="utf-8")
        (build / "build.py").write_text(MAP_BUILD.format(name=a.name, src=src_s, viz=VIZ_S), encoding="utf-8")
        made = ["scan.json", "content.json", "build.py"]
    else:
        if not sc["parallelGroups"]:
            sys.exit("掃不到平行規格群組，不適合 catalog，改用 --type map")
        group = next(iter(sc["parallelGroups"]))
        glob = group if "*" in group else group.split("/(")[0] + "/*.md"
        ids = sorted({(p.parent.name if p.name == Path(glob).name else p.stem) for p in src.glob(glob)})
        zh = {"lede": TODO, "icon": TODO + "從 scripts/icons.py 挑一個名稱", "badges": [], "unit": "個項目", "footer": TODO, "security": security_skeleton(sc),
              "items": {i: [TODO, TODO] for i in ids}, "sections": {}}
        (build / "zh_tw.json").write_text(json.dumps(zh, ensure_ascii=False, indent=1), encoding="utf-8")
        (build / "extract.py").write_text(CAT_EXTRACT.format(name=a.name, src=src_s, glob=glob, count=len(ids), viz=VIZ_S), encoding="utf-8")
        made = ["scan.json", "zh_tw.json", "extract.py"]
    print(f"版型 {kind}（{sc['shapeReason']}）")
    print(f"已建立 {build}：{'、'.join(made)}")
    if kind == "map":
        print("下一步：content.json 的「（待填）」換成繁中內容；要從原檔抽的放 \"__KEY__\" 佔位並在 build.py 的 fill 給值；補 structure_check；再跑 build.py。")
    else:
        print("下一步：zh_tw.json 的「（待填）」換成繁中內容，改 pick_sections() 與 category()，再跑 extract.py。")


if __name__ == "__main__":
    main()
