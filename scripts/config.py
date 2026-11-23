"""skill-viz 的設定：輸出根目錄與瀏覽器路徑。

輸出根目錄（每個 skill 的頁面放在 <根目錄>/<名稱>/）的決定順序：
  1. 環境變數 SKILL_VIZ_OUT
  2. skill 資料夾裡的 config.json 的 "outRoot"（個人設定，不要打包分享）
  3. 使用者家目錄下的 SSSKill
"""
import json
import os
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_DIR / "scripts"


def _config():
    p = SKILL_DIR / "config.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            return {}
    return {}


def out_root():
    env = os.environ.get("SKILL_VIZ_OUT")
    if env:
        return Path(env)
    cfg = _config().get("outRoot")
    if cfg:
        return Path(cfg)
    return Path.home() / "SSSKill"


def browser_override():
    return os.environ.get("SKILL_VIZ_BROWSER") or _config().get("browser")
