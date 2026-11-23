"""通用 skill／規格庫資料夾掃描器，只讀不改。

輸出：每個檔案的大小、類型、Markdown 章節樹、粗體小標、互相引用，SKILL.md 的 frontmatter，
以及版型建議（catalog 圖鑑 或 map 地圖）。

用法：
    python scan_skill.py <資料夾> [--out scan.json] [--summary]
--summary 只印精簡摘要（省 context），完整 JSON 寫進 --out。
也可在其他腳本 import：from scan_skill import scan
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

LINK_RE = re.compile(r"\]\(([^)#\s]+?\.(?:md|json|cjs|js|mjs|py|ps1|sh|txt))(?:#[^)]*)?\)")
CODE_REF_RE = re.compile(r"`([A-Za-z0-9_./-]+\.(?:md|json|cjs|js|mjs|py|ps1|sh))`")
HEAD_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*$")
BOLD_HEAD_RE = re.compile(r"^\*\*([^*]{2,80})\*\*\s*(\(.*\))?\s*$")
FM_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
TEXT_EXT = {".json", ".cjs", ".js", ".mjs", ".py", ".ps1", ".sh", ".yaml", ".yml", ".toml"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}

# 安全評估用的風險訊號：只看字面，抓不到語意（例如「文件說只讀、程式其實會改檔」），所以只當輔助，結論以正式的安全審查為準。
# 程式檔六種都查；Markdown 是給 agent 照做的指示，只查安裝、帳密、改設定三種，其餘在文件裡太常出現，雜訊太多。
CODE_EXT = {".py", ".js", ".cjs", ".mjs", ".ts", ".sh", ".bash", ".ps1", ".psm1", ".bat", ".cmd"}
RISK_KINDS = {
    "network": ("連網路", re.compile(r"https?://(?!localhost|127\.0\.0\.1)|\brequests\.|\burllib|\bhttp\.client|\bsocket\.|\bfetch\(|\baxios\b|\bcurl\s|\bwget\s|Invoke-(?:WebRequest|RestMethod)|\biwr\s", re.I)),
    "exec": ("執行程式", re.compile(r"\bsubprocess\b|\bos\.(?:system|popen|exec\w*)|child_process|\bexecSync\b|\bspawn(?:Sync)?\(|(?<![.\w])eval\(|(?<![.\w])exec\(|Start-Process|Invoke-Expression|\biex\b")),
    "delete": ("刪檔", re.compile(r"\brmtree\b|\bos\.(?:remove|unlink|rmdir)\b|\.unlink\(|\bunlinkSync\b|\brmSync\b|fs\.rm\b|\brm\s+-[a-z]*[rf]|Remove-Item|\bdel\s+/[fsq]", re.I)),
    "secrets": ("讀帳密", re.compile(r"(?<![\w.])\.env\b|\bcookies?\b|api[_-]?key|\bpassword\b|\bcredentials?\b|\bkeychain\b|\bsecret[_-]?key\b|\baccess[_-]?token\b|\bbearer\b", re.I)),
    "install": ("安裝套件", re.compile(r"\bpip3?\s+install\b|\bnpm\s+(?:install|i)\b|\bnpx\s|\bwinget\s+install\b|\bbrew\s+install\b|\bapt(?:-get)?\s+install\b|(?:curl|wget|iwr|irm|Invoke-\w+)\b[^|\n]*\|\s*(?:ba|z)?sh\b|\|\s*iex\b", re.I)),
    "config": ("改 Claude 設定", re.compile(r"settings(?:\.local)?\.json|\"hooks\"\s*:|\bPreToolUse\b|\bPostToolUse\b|~/\.claude/(?!skills\b)", re.I)),
}
MD_RISK_KINDS = {"secrets", "install", "config"}


def risk_signals(text, suf):
    kinds = RISK_KINDS if suf in CODE_EXT else {k: RISK_KINDS[k] for k in MD_RISK_KINDS} if suf == ".md" else {}
    hits = defaultdict(list)
    for i, line in enumerate(text.splitlines(), start=1):
        for k, (_, rx) in kinds.items():
            if rx.search(line):
                hits[k].append(i)
    return [{"kind": k, "lines": v} for k, v in hits.items()]


def frontmatter(text):
    m = FM_RE.match(text)
    if not m:
        return {}
    out, key = {}, None
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if kv:
            key = kv.group(1)
            out[key] = kv.group(2).strip()
        elif key and line.startswith(" "):
            out[key] += " " + line.strip()
    return out


def scan_markdown(text):
    heads, bolds, in_code = [], [], False
    body = FM_RE.sub("", text)
    offset = text.count("\n", 0, len(text) - len(body))
    for i, line in enumerate(body.splitlines(), start=1 + offset):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = HEAD_RE.match(line)
        if m:
            heads.append({"level": len(m.group(1)), "text": m.group(2), "line": i})
            continue
        b = BOLD_HEAD_RE.match(line)
        if b:
            bolds.append({"text": b.group(1).strip(), "note": (b.group(2) or "").strip("() "), "line": i})
    return heads, bolds


def h2_signature(heads):
    return tuple(re.sub(r"^\d+[.)]\s*", "", h["text"]).lower() for h in heads if h["level"] == 2)


def shape_hint(root, files):
    """回傳 (shape, reason, groups)。groups 是「平行規格」群組。"""
    groups = defaultdict(list)
    # 型一：<dir>/*/<同名檔>.md，例如 styles/*/STYLE.md
    for f in files:
        parts = f["path"].split("/")
        if len(parts) >= 3 and parts[-1].endswith(".md"):
            groups[("/".join(parts[:-2]) + "/*/" + parts[-1])].append(f["path"])
    # 型二：同一層多份 md 共用相同的二級標題結構
    sig = Counter()
    by_sig = defaultdict(list)
    for f in files:
        s = h2_signature(f.get("headings", []))
        if len(s) >= 3:
            by_sig[(str(Path(f["path"]).parent), s)].append(f["path"])
    for (parent, s), paths in by_sig.items():
        if len(paths) >= 2:
            groups[f"{parent}/(共用 {len(s)} 個二級標題)"] = paths
    best = max(groups.items(), key=lambda kv: len(kv[1]), default=(None, []))
    has_skill = (root / "SKILL.md").exists()
    n = len(best[1])
    if n >= 20:
        return "catalog", f"{best[0]} 有 {n} 份平行規格", groups
    if has_skill:
        return "map", "有 SKILL.md，屬流程或說明型 skill" + (f"（另有 {n} 份平行參考檔，可放進地圖的卡片區）" if n >= 4 else ""), groups
    if n >= 8:
        return "catalog", f"{best[0]} 有 {n} 份平行規格", groups
    return "map", "沒有明顯的平行規格群", groups


def scan(root):
    root = Path(root).resolve()
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        rel = p.relative_to(root).as_posix()
        item = {"path": rel, "bytes": p.stat().st_size, "ext": p.suffix.lower().lstrip(".") or "(無)"}
        suf = p.suffix.lower()
        if suf in (".md", ".txt"):
            text = p.read_text(encoding="utf-8", errors="replace")
            item["lines"] = text.count("\n") + 1
            if suf == ".md":
                item["headings"], item["boldHeads"] = scan_markdown(text)
                refs = set(LINK_RE.findall(text)) | set(CODE_REF_RE.findall(text))
                base = Path(rel).parent
                item["refs"] = sorted({(base / r).as_posix() if (root / base / r).exists() else r for r in refs} - {rel})
                item["risks"] = risk_signals(text, suf)
        elif suf in TEXT_EXT or suf in CODE_EXT:
            text = p.read_text(encoding="utf-8", errors="replace")
            item["lines"] = text.count("\n") + 1
            item["risks"] = risk_signals(text, suf)
        if not item.get("risks"):
            item.pop("risks", None)
        files.append(item)

    names = {f["path"] for f in files}
    base_names = defaultdict(list)
    for n in names:
        base_names[n.rsplit("/", 1)[-1]].append(n)
    for f in files:
        resolved = []
        for r in f.get("refs", []):
            if r in names:
                resolved.append(r)
            elif len(base_names.get(r.rsplit("/", 1)[-1], [])) == 1:
                resolved.append(base_names[r.rsplit("/", 1)[-1]][0])
        f["refs"] = sorted(set(resolved) - {f["path"]})
    for f in files:
        f["refsIn"] = sorted(g["path"] for g in files if f["path"] in g.get("refs", []))

    skill_md = root / "SKILL.md"
    fm = frontmatter(skill_md.read_text(encoding="utf-8")) if skill_md.exists() else {}
    shape, reason, groups = shape_hint(root, files)
    return {
        "root": str(root).replace("\\", "/"),
        "name": fm.get("name", root.name),
        "description": fm.get("description", ""),
        "fileCount": len(files),
        "totalBytes": sum(f["bytes"] for f in files),
        "shape": shape,
        "shapeReason": reason,
        "parallelGroups": {k: len(v) for k, v in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:5]},
        "files": files,
    }


def summary(d):
    lines = [
        f"名稱：{d['name']}",
        f"根目錄：{d['root']}",
        f"檔案：{d['fileCount']} 個，共 {d['totalBytes'] / 1024:.0f} KB",
        f"版型建議：{d['shape']}（{d['shapeReason']}）",
    ]
    if d["parallelGroups"]:
        lines.append("平行群組：" + "；".join(f"{k} ×{v}" for k, v in d["parallelGroups"].items()))
    lines.append("最大的檔案：")
    for f in sorted(d["files"], key=lambda x: -x["bytes"])[:12]:
        h = len(f.get("headings", []))
        lines.append(f"  {f['bytes'] / 1024:7.1f} KB  {f['path']}" + (f"  （{h} 個標題，引用 {len(f.get('refs', []))}）" if h else ""))
    if d["fileCount"] > 12:
        lines.append(f"  ……其餘 {d['fileCount'] - 12} 個見 --out 的 JSON")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--out")
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    data = scan(a.root)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(summary(data) if a.summary or a.out else json.dumps(data, ensure_ascii=False, indent=1))
