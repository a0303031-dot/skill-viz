"""檢查任何文字檔的繁中規則（破折號、常見簡體字），精確比對 Unicode。

為什麼有這支：這台的 grep 用位元組比對中文，找破折號會誤報（2026-11-19 踩到）。

用法：
    python textcheck.py <檔案或資料夾> [...] [--ext md,json,html]
    python textcheck.py --selftest
只檢查含中文的行，跳過 ``` 程式碼區塊。上游英文原文行不含中文，不受影響。
有問題 exit 1。
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from textrules import SIMP, TRAD_SAMPLE, problems  # noqa: E402


def check_file(p):
    hits, in_code = [], False
    for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for prob in problems(line):
            hits.append((i, prob, line.strip()[:60]))
    return hits


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--ext", default="md")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        mixed = sorted(SIMP & TRAD_SAMPLE)
        print("簡體清單混入繁體：", mixed or "無")
        sys.exit(1 if mixed else 0)
    exts = {"." + e.strip().lstrip(".") for e in a.ext.split(",")}
    files = []
    for x in a.paths:
        p = Path(x)
        files += [f for f in p.rglob("*") if f.suffix in exts and f.is_file()] if p.is_dir() else [p]
    total = 0
    for f in files:
        for i, prob, txt in check_file(f):
            print(f"{f}:{i}  {prob}  {txt}")
            total += 1
    print(f"檢查 {len(files)} 個檔，{total} 個問題")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
