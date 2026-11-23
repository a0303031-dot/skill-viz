"""改過模板、render.py 或關卡之後的回歸測試。

1. 文字規則自測（簡體清單沒誤收繁體字）。
2. 用 tests/ 的兩份自測資料產出地圖與圖鑑（涵蓋全部區塊類型）。
   另用 new.py 在暫存目錄建一份 map 骨架：沒填要被擋，填完要能產出。
3. 重跑輸出根目錄（見 config.py）底下 */_build/ 的每一支建置腳本，最後重產總覽頁 index.html（index.py）。
任一項失敗就 exit 1。加 --shots <目錄> 會再把自測頁截圖，交給 Claude 逐段看。

用法：python regress.py [--shots <scratchpad 目錄>]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
from config import out_root  # noqa: E402

SSSKILL = out_root()
ENV = {**os.environ, "PYTHONUTF8": "1"}


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, env=ENV, capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
    return r.returncode, tail


def skeleton_smoke(py, out):
    """在暫存輸出根目錄用 new.py 建 skill-viz 自己的 map 骨架：
    沒填時建置要被「（待填）」關卡擋下；把標記換成文字後要能產出。"""
    root = out / "new-smoke"
    shutil.rmtree(root, ignore_errors=True)
    env = {**ENV, "SKILL_VIZ_OUT": str(root)}

    def go(cmd, cwd=None):
        r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        return r.returncode, r.stdout + r.stderr

    code, log = go([py, str(HERE / "new.py"), "smoke", "--src", str(SKILL), "--type", "map"])
    if code:
        return 1, ["new.py 失敗"] + log.strip().splitlines()[-2:]
    build = root / "smoke" / "_build"
    code, log = go([py, "build.py"], cwd=build)
    if code == 0 or "骨架沒填完" not in log:
        return 1, ["沒填的骨架沒被擋下"] + log.strip().splitlines()[-2:]
    content = build / "content.json"
    filled = json.loads(content.read_text(encoding="utf-8").replace("（待填）", "示範"))
    filled["icon"] = "map"
    content.write_text(json.dumps(filled, ensure_ascii=False), encoding="utf-8")
    code, log = go([py, "build.py"], cwd=build)
    if code:
        return 1, ["填完的骨架產不出頁面"] + log.strip().splitlines()[-3:]
    return 0, []


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots")
    a = ap.parse_args()
    out = Path(tempfile.gettempdir()) / "skill-viz-selftest"
    out.mkdir(exist_ok=True)
    py = sys.executable
    results = []

    results.append(("文字規則自測", *run([py, str(HERE / "textcheck.py"), "--selftest"])))
    fm, fc = out / "selftest-map.html", out / "selftest-catalog.html"
    results.append(("自測：地圖全區塊", *run([py, str(HERE / "render.py"), "--type", "map", "--data", str(SKILL / "tests/fixture_map.json"),
                                          "--out", str(fm), "--scan", str(SKILL)])))
    results.append(("自測：圖鑑", *run([py, str(HERE / "render.py"), "--type", "catalog", "--data", str(SKILL / "tests/fixture_catalog.json"),
                                      "--out", str(fc), "--scan", str(SKILL)])))
    results.append(("骨架：new.py 產出的 map 骨架", *skeleton_smoke(py, out)))
    results.append(("skill 文件繁中檢查", *run([py, str(HERE / "textcheck.py"), str(SKILL)])))

    for build in sorted(SSSKILL.glob("*/_build")):
        script = next((build / n for n in ("build.py", "extract.py") if (build / n).exists()), None)
        if script:
            results.append((f"成品：{build.parent.name}", *run([py, str(script)], cwd=build)))
    results.append(("總覽頁 index.html", *run([py, str(HERE / "index.py")])))

    bad = 0
    for name, code, tail in results:
        mark = "通過" if code == 0 else "失敗"
        bad += code != 0
        print(f"[{mark}] {name}")
        if code:
            for t in tail:
                print("        " + t)
    print(f"共 {len(results)} 項，失敗 {bad} 項。自測頁：{fm}、{fc}")

    if a.shots:
        for page, extra in ((fm, []), (fm, ["--light"]), (fc, ["--hash", "alpha"])):
            code, tail = run([py, str(HERE / "shot.py"), str(page), "--out-dir", a.shots, *extra])
            print(f"截圖 {page.name} {' '.join(extra)}：{tail[-1] if tail else ''}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
