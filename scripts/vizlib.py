"""各成品建置腳本（<輸出根目錄>/<名稱>/_build/build.py、extract.py）共用的小工具。

用法（VIZ 是 skill-viz 的 scripts 資料夾）：
    sys.path.insert(0, str(VIZ))
    from vizlib import fill, rd, render, stop_if

- stop_if(errs)：structure_check 有錯就逐條印出並 exit 1。
- fill(data, {"__KEY__": 值})：資料裡「整個字串剛好是 __KEY__」的值換成對應內容，位置不限
  （items、rows、stats、timeline 的 end.items 都可以）。給了卻沒用到的鍵直接報錯；
  content.json 裡沒換掉的標記由 render.py 的關卡擋。
- render(kind, data, here, out, scan=None)：寫 data.json、呼叫 render.py，以它的 exit code 結束。
- Markdown 解析：table_rows（表格列）、numbered（某個二級章節裡的編號清單）、fences（程式碼區塊）、unlink（連結只留文字）。
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def rd(p):
    return Path(p).read_text(encoding="utf-8")


def stop_if(errs, hint="content.json 或 build.py"):
    if errs:
        print(f"對不上上游結構，先更新 {hint}：")
        for e in errs:
            print("  - " + e)
        sys.exit(1)


def fill(data, mapping):
    used = set()

    def walk(o):
        if isinstance(o, str) and o in mapping:
            used.add(o)
            return mapping[o]
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(v) for v in o]
        return o

    out = walk(data)
    unused = sorted(set(mapping) - used)
    if unused:
        sys.exit(f"資料裡找不到這些佔位標記：{unused}")
    return out


def render(kind, data, here, out, scan=None):
    here = Path(here)
    (here / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    cmd = [sys.executable, str(HERE / "render.py"), "--type", kind, "--data", str(here / "data.json"), "--out", str(out)]
    if scan:
        cmd += ["--scan", str(scan)]
    sys.exit(subprocess.run(cmd, env={**os.environ, "PYTHONUTF8": "1"}).returncode)


def table_rows(md, header_re):
    """header_re 是表頭那一行的正則（記得跳脫 |），回傳表頭下方每一列的儲存格。"""
    m = re.search(header_re + r"\n\|[-| :]+\|\n((?:\|.*\|\n?)+)", md)
    return [[c.strip() for c in line.strip().strip("|").split("|")]
            for line in (m.group(1) if m else "").strip().splitlines()]


def numbered(md, heading):
    """「## heading」章節裡第一段連續的編號清單，去掉編號。"""
    sec = re.search(rf"^## {heading}\n(.*?)(?=^## |\Z)", md, re.M | re.S)
    m = re.search(r"((?:^\d+\. .+\n?)+)", sec.group(1) if sec else "", re.M)
    return [re.sub(r"^\d+\. ", "", line) for line in (m.group(1) if m else "").strip().splitlines()]


def fences(md):
    """[(語言, 內容), ...]，內容含結尾換行。"""
    return re.findall(r"^```(\w*)\n(.*?)^```", md, re.M | re.S)


def unlink(s):
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
