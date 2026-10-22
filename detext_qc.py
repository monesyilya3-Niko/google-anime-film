# -*- coding: utf-8 -*-
"""去字质量量化验收：对每个处理区域计算「残留笔画能量」。

原理：文字 = 高频细结构。取区域内的高通能量
      HP = |Laplacian(区域)| 的均值
原图含字 -> HP 高；处理后无字 -> HP 显著下降。
输出 before/after 比值，作为「去字彻底度」的机器判据。
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import detext7  # noqa: E402

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "gen_out"


def hp_energy(img_bgr, box):
    H, W = img_bgr.shape[:2]
    x1, y1, x2, y2 = box
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(W, x2), min(H, y2)
    if x2 - x1 < 4 or y2 - y1 < 4:
        return None
    g = cv2.cvtColor(img_bgr[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(g, cv2.CV_32F, ksize=3)
    return float(np.abs(lap).mean())


print(f"{'项目':26s} {'手法':4s} {'原图HP':>8s} {'处理后HP':>9s} {'残留%':>7s}  判定")
print("-" * 78)
rows = []
for prefix, box, label, mode in detext7.JOBS:
    src = next((p for p in sorted(detext7.SRC.glob(prefix + "*.jpg"))), None)
    dst = OUT / (src.name if src else "")
    if not src or not dst.exists():
        continue
    a = cv2.cvtColor(np.asarray(Image.open(src).convert("RGB")), cv2.COLOR_RGB2BGR)
    b = cv2.cvtColor(np.asarray(Image.open(dst).convert("RGB")), cv2.COLOR_RGB2BGR)
    ea, eb = hp_energy(a, box), hp_energy(b, box)
    if not ea or not eb:
        continue
    pct = 100.0 * eb / ea
    verdict = "✅ 干净" if pct < 22 else ("⚠️ 残留" if pct < 45 else "❌ 未除净")
    rows.append((label, mode, ea, eb, pct, verdict))
    print(f"{label:26s} {mode:4s} {ea:8.2f} {eb:9.2f} {pct:6.1f}%  {verdict}")

clean = sum(1 for r in rows if r[5].startswith("✅"))
print("-" * 78)
print(f"干净 {clean}/{len(rows)}")
bad = [r[0] for r in rows if not r[5].startswith("✅")]
if bad:
    print("需重画/再处理:", ", ".join(bad))
