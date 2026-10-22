# -*- coding: utf-8 -*-
"""云端收尾一条龙（授权完成后跑这个）：
  1) 清理：_Trash_待清空历史废弃旧版（60+ 废弃稿） + 根目录游离文件
  2) 上传：V17_未完成清单 / V17_待重画_23张_含原图与提示词
  3) 终检：云端结构
"""
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
PY = str(ROOT.parent / "vibe-choice" / ".venv" / "Scripts" / "python.exe")

for script in ("cloud_clean.py", "upload_redraw.py", "final_check.py"):
    print("=" * 70)
    print(">>>", script)
    print("=" * 70)
    r = subprocess.run([PY, script], cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    print(out[-3000:])
    if r.returncode != 0:
        print(f"!! {script} 退出码 {r.returncode}")
        break
