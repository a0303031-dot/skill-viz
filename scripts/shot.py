"""用 headless Edge（找不到就用 Chrome）把 HTML 截成長圖，再切段給 Claude 看。

用法：
    python shot.py <html> [--out-dir DIR] [--light] [--hash file=SKILL.md] [--width 1280] [--seg 1500]

輸出 <名稱>_<dark|light>_segN.png，印出每段路徑。
注意：錨點（#section）在無頭截圖不會捲動，所以截整頁長圖再切；--hash 只用來觸發頁面自己的行為（例如開詳情視窗）。
臨時瀏覽器設定檔建在 out-dir 底下，跑完刪掉。
"""
import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import browser_override  # noqa: E402

CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]
ON_PATH = ["msedge", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]


def browser():
    o = browser_override()
    if o:
        if Path(o).exists():
            return o
        sys.exit(f"SKILL_VIZ_BROWSER／config.json 指定的瀏覽器不存在：{o}")
    for c in CANDIDATES:
        if Path(c).exists():
            return c
    for n in ON_PATH:
        w = shutil.which(n)
        if w:
            return w
    sys.exit("找不到 Edge 或 Chrome。可用環境變數 SKILL_VIZ_BROWSER 指定瀏覽器執行檔的完整路徑。")


def content_bottom(im):
    w, h = im.size
    bg = im.getpixel((5, h - 5))
    for y in range(h - 1, 0, -10):
        for x in range(60, w - 60, 30):
            p = im.getpixel((x, y))
            if sum(abs(p[i] - bg[i]) for i in range(3)) > 30:
                return min(h, y + 40)
    return h


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--out-dir")
    ap.add_argument("--light", action="store_true")
    ap.add_argument("--hash", default="")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, help="預設 12000（整頁）；有 --hash 時預設 1400，否則對話框會置中在長視窗的半腰")
    ap.add_argument("--seg", type=int, default=1500)
    ap.add_argument("--max-seg", type=int, default=8)
    a = ap.parse_args()
    if a.height is None:
        a.height = 1400 if a.hash else 12000

    html = Path(a.html).resolve()
    out = Path(a.out_dir or html.parent / "_shots").resolve()
    out.mkdir(parents=True, exist_ok=True)
    mode = "light" if a.light else "dark"
    stem = f"{html.stem}_{mode}" + (f"_{a.hash.replace('=', '-').replace('/', '-')}" if a.hash else "")
    full = out / f"{stem}_full.png"
    full.unlink(missing_ok=True)
    prof = out / f"_prof_{int(time.time())}"
    url = html.as_uri() + (f"#{a.hash}" if a.hash else "")
    cmd = [browser(), "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}",
           f"--window-size={a.width},{a.height}", "--virtual-time-budget=4000", f"--screenshot={full}",
           f"--blink-settings=preferredColorScheme={1 if a.light else 0}", url]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    for _ in range(60):  # 截圖檔有時在程序結束後才落地
        if full.exists() and full.stat().st_size > 0:
            break
        time.sleep(0.5)
    for _ in range(20):  # 瀏覽器子程序可能還鎖著設定檔，等它放手再刪
        shutil.rmtree(prof, ignore_errors=True)
        if not prof.exists():
            break
        time.sleep(0.5)
    if prof.exists():
        print(f"注意：臨時設定檔沒刪乾淨，可手動刪除 {prof}")
    if not full.exists():
        sys.exit("截圖失敗：瀏覽器沒有產出檔案")

    im = Image.open(full).convert("RGB")
    bottom = content_bottom(im)
    if bottom >= a.height - 20:
        print(f"注意：頁面可能比 {a.height}px 長，被截斷了，可加大 --height")
    n = 0
    for top in range(0, bottom, a.seg):
        if n >= a.max_seg:
            print(f"注意：只輸出前 {a.max_seg} 段，其餘略過")
            break
        p = out / f"{stem}_seg{n}.png"
        im.crop((0, top, im.width, min(top + a.seg, bottom))).save(p)
        print(p)
        n += 1
    full.unlink(missing_ok=True)
    print(f"頁面高度約 {bottom}px，共 {n} 段")


if __name__ == "__main__":
    main()
