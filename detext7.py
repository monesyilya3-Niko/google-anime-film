# -*- coding: utf-8 -*-
"""《暮冬念春》母带去字 v7 —— 终版。

按「文字在画面里的角色」分三种手法，每种都做过逐张视觉验收：

 A. 平面载体（卡片纸、笔记本页）→ 整框 TELEA 内容感知填补
    实测干净：纸面是近纯色，TELEA 从四周取色即可补平。
 B. 远景/小字（手机屏、代码屏、杯身 logo、海报片名、银幕）
    → 局部高斯柔化。远景屏幕上「看不清的字」本来就该看不清，
    柔化后没有任何涂抹痕迹，符合动画景深，是唯一零瑕疵的去字方式。
 C. 银幕片名 → 先柔化，再把《你的名字。》替换为原创片名「暮冬」重绘。

用法: python detext7.py            处理全部
      python detext7.py --compare  只生成对照图
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
SRC = next(d for d in list(ROOT.iterdir()) + list((ROOT / "source").iterdir())
            if d.is_dir() and d.name.startswith("40"))
OUT = ROOT / "gen_out"


def stroke_mask(gray_win):
    """返回文字笔画掩膜（uint8 0/255）。"""
    h, w = gray_win.shape[:2]
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    ops = [cv2.morphologyEx(gray_win, cv2.MORPH_BLACKHAT, k),
           cv2.morphologyEx(gray_win, cv2.MORPH_TOPHAT, k)]
    acc = np.zeros((h, w), np.float32)
    for op in ops:
        op = cv2.GaussianBlur(op, (3, 3), 0)
        thr = max(28, int(op.max() * 0.40))
        acc = np.maximum(acc, op.astype(np.float32) / max(thr, 1))
    mask = (acc >= 1.0).astype(np.uint8) * 255
    # 只保留「细长」的笔画：开运算去掉粗块，再用闭运算连回笔画
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (9, 2)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    keep = np.zeros((h, w), np.uint8)
    for i in range(1, n):
        x, y, cw, ch, a = stats[i]
        if a < MIN_PIX or cw < 8 or ch < 6:
            continue
        if cw * ch > 0.9 * 255 * 255 and a > 0.6 * cw * ch:
            continue        # 大块实心 = 背景，不是字
        keep[lab == i] = 255
    return keep


FONT = "C:/Windows/Fonts/simsun.ttc"

# 逐项指定柔化强度：字越大越要糊透
SIGMA = {
    "10_tee_print": 52.0,
    "10_screen_title": 66.0,
    "03_tee_print": 62.0,
    "03b_tee_print": 62.0,
    "23_tee_print": 46.0,
    "27_palm_handwriting": 32.0,
    "23_cup_logo": 16.0,
    "26_cup_logo": 14.0,
    "18_poster_title": 20.0,
    "18a_poster_title": 20.0,
    "06a_poster_title": 32.0,
    "18_phone_screen": 24.0,
    "18a_phone_screen": 24.0,
    "18_code_screens": 22.0,
}

# (母带前缀, 框, 标签, 手法)
#   A = 整框 TELEA   B = 局部柔化   C = 柔化 + 重绘片名「暮冬」
JOBS = [
    # A 平面载体
    ("06b_", (884, 1236, 1026, 1440), "06b_card_DBX_YXP", "A"),
    ("07_", (830, 1440, 1192, 1520), "07_nbL_DBX", "A"),
    ("07_", (2766, 1450, 3116, 1528), "07_nbR_YXP", "A"),
    ("18_", (206, 233, 446, 292), "18_poster_LOSSSANE", "A"),
    ("18a_", (206, 233, 446, 292), "18a_poster_LOSSSANE", "A"),
    # B 远景/小字
    ("18_", (1505, 775, 2000, 925), "18_phone_screen", "B"),
    ("18_", (900, 930, 2000, 1135), "18_code_screens", "B"),
    ("18a_", (1505, 775, 1900, 925), "18a_phone_screen", "B"),
    ("23_", (1852, 1366, 2072, 1462), "23_cup_logo", "B"),
    ("26_", (2392, 1348, 2580, 1412), "26_cup_logo", "B"),
    ("18_", (176, 182, 482, 254), "18_poster_title", "B"),
    ("18a_", (176, 182, 482, 254), "18a_poster_title", "B"),
    ("06a_", (1194, 1892, 1472, 2052), "06a_poster_title", "B"),
    ("06a_", (1358, 880, 1500, 972), "06a_card_YXP", "A"),
    # B/C 其它
    ("03_", (2590, 1862, 3186, 2160), "03_tee_print", "B"),
    ("03b_", (670, 1862, 1266, 2160), "03b_tee_print", "B"),
    ("23_", (1032, 1618, 1292, 1902), "23_tee_print", "B"),
    ("27_", (1842, 1648, 2172, 1802), "27_palm_handwriting", "B"),
    ("10_", (1380, 430, 2490, 780), "10_screen_title", "C"),
    ("10_", (2700, 1330, 3020, 1555), "10_tee_print", "B"),
    # 注：07_ 桌上的《小魔卡少女樱》星之杖横跨 ~860px、背景是课桌+教室纵深，
    #     局部填补会糊成一片，已改判为「必须重画换原创道具」，此处不做处理。
]


def blur_region(img, box, sigma):
    H, W = img.shape[:2]
    x1, y1, x2, y2 = box
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(W, x2), min(H, y2)
    h, w = y2 - y1, x2 - x1
    if h < 3 or w < 3:
        return img
    reg = img[y1:y2, x1:x2]
    # 边缘羽化，避免出现「一块糊」的硬边；贴到画面边的方向不羽化
    k = max(3, min(h, w) // 5)
    a = np.ones((h, w), np.float32)
    ramp = np.linspace(0, 1, k, dtype=np.float32)
    if y1 > 0:
        a[:k, :] *= ramp[:, None]
    if y2 < H:
        a[-k:, :] *= ramp[::-1][:, None]
    if x1 > 0:
        a[:, :k] *= ramp[None, :]
    if x2 < W:
        a[:, -k:] *= ramp[::-1][None, :]
    a = cv2.GaussianBlur(a, (0, 0), 2.0)
    bl = cv2.GaussianBlur(reg, (0, 0), sigma)
    out = reg.astype(np.float32) * (1 - a[..., None]) + bl.astype(np.float32) * a[..., None]
    img = img.copy()
    img[y1:y2, x1:x2] = np.clip(out, 0, 255).astype(np.uint8)
    return img


def level_fill(img, box):
    """D 手法：亮底暗字（白 T 恤印花）。
    用 blackhat 抓出笔画 -> 逐行取非笔画像素的高分位作背景 -> 覆盖笔画。
    白 T 恤近乎纯色，这样出来的结果是干净的布面，而不是一块糊影。"""
    H, W = img.shape[:2]
    x1, y1, x2, y2 = box
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(W, x2), min(H, y2)
    h, w = y2 - y1, x2 - x1
    reg = img[y1:y2, x1:x2].copy()
    gray = cv2.cvtColor(reg, cv2.COLOR_BGR2GRAY)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    bh = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, k)
    bh = cv2.GaussianBlur(bh, (3, 3), 0)
    thr = max(28, int(bh.max() * 0.42))
    m = (bh > thr).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE,
                         cv2.getStructuringElement(cv2.MORPH_RECT, (7, 2)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros((h, w), np.uint8)
    for i in range(1, n):
        x, y, cw, ch, a = stats[i]
        if a < 60 or cw < 8 or ch < 6:
            continue
        keep[lab == i] = 255
    if keep.sum() == 0:
        return img
    keep = cv2.dilate(keep, np.ones((7, 7), np.uint8), iterations=1)
    mk = keep > 0
    f = reg.astype(np.float32)
    lum = cv2.cvtColor(reg, cv2.COLOR_BGR2GRAY)
    rowcol = np.zeros((h, 3), np.float32)
    for i in range(h):
        mr = mk[i]
        if (~mr).sum() < 8:
            rowcol[i] = np.median(f[i], axis=0)
        else:
            rowcol[i] = np.percentile(f[i][~mr], 82, axis=0)
    kk = 7
    ext = np.vstack([rowcol[:1].repeat(kk // 2, 0), rowcol,
                     rowcol[-1:].repeat(kk // 2, 0)])
    smooth = np.array([ext[i:i + kk].mean(axis=0) for i in range(h)])
    fill = np.repeat(smooth[:, None, :], w, axis=1)
    f[mk] = fill[mk]
    a = cv2.GaussianBlur(mk.astype(np.float32), (0, 0), 2.0)[..., None]
    out = reg.astype(np.float32) * (1 - a) + f * a
    img = img.copy()
    img[y1:y2, x1:x2] = np.clip(out, 0, 255).astype(np.uint8)
    return img


def render_title(img, box, txt="暮冬"):
    """在银幕上用宋体重绘原创片名，带冷色辉光。"""
    H, W = img.shape[:2]
    x1, y1, x2, y2 = box
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(W, x2), min(H, y2)
    h, w = y2 - y1, x2 - x1
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert("RGBA")
    layer = Image.new("RGBA", pil.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    size = max(40, int(h * 0.72))
    f = ImageFont.truetype(FONT, size)
    tb = d.textbbox((0, 0), txt, font=f)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    px = int((x1 + x2) / 2 - tw / 2)
    py = int((y1 + y2) / 2 - th / 2 - tb[1])
    d.text((px, py), txt, font=f, fill=(255, 255, 255, 255))
    alpha = np.asarray(layer)[:, :, 3].astype(np.float32)
    out = np.asarray(Image.alpha_composite(pil, layer)).copy()
    g = cv2.GaussianBlur(alpha, (0, 0), max(8, size * 0.30)) / 255.0
    rgb = out[:, :, :3].astype(np.float32)
    rgb += g[:, :, None] * np.array([70, 105, 150], np.float32)
    out[:, :, :3] = np.clip(rgb, 0, 255)
    return cv2.cvtColor(out, cv2.COLOR_RGB2BGR)


def process(prefix):
    src = next((p for p in sorted(SRC.glob(prefix + "*.jpg"))), None)
    if not src:
        return None
    jobs = [j for j in JOBS if j[0] == prefix]
    if not jobs:
        return None
    pil = Image.open(src).convert("RGB")
    out = cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR)
    H, W = out.shape[:2]
    report = []
    for _, box, label, mode in jobs:
        x1, y1, x2, y2 = box
        if mode == "A":
            m = np.zeros((H, W), np.uint8)
            m[max(0, y1):min(H, y2), max(0, x1):min(W, x2)] = 255
            out = cv2.inpaint(out, m, 9, cv2.INPAINT_TELEA)
        elif mode == "B":
            # 字号越大糊得越狠：按框高给 σ
            sigma = SIGMA.get(label, max(3.0, min(14.0, (y2 - y1) * 0.13)))
            out = blur_region(out, box, sigma)
        elif mode == "D":
            out = level_fill(out, box)
        elif mode == "C":
            out = blur_region(out, box,
                              SIGMA.get(label, max(4.0, (y2 - y1) * 0.16)))
            out = render_title(out, box)
        report.append((label, mode))
    dst = OUT / src.name
    Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB)).save(dst, quality=96,
                                                              subsampling=0)
    return dst, report


def compare():
    tiles = []
    for prefix, box, label, mode in JOBS:
        src = next((p for p in sorted(SRC.glob(prefix + "*.jpg"))), None)
        dst = OUT / (src.name if src else "")
        if not src or not dst.exists():
            continue
        a = Image.open(src).convert("RGB")
        b = Image.open(dst).convert("RGB")
        x1, y1, x2, y2 = box
        pad = 24
        cb = (max(0, x1 - pad), max(0, y1 - pad),
              min(a.width, x2 + pad), min(a.height, y2 + pad))
        ca, cc = a.crop(cb), b.crop(cb)
        w = 320
        h = int(ca.height * w / ca.width)
        tile = Image.new("RGB", (w * 2 + 6, h + 22), (10, 10, 12))
        tile.paste(ca.resize((w, h), Image.LANCZOS), (0, 22))
        tile.paste(cc.resize((w, h), Image.LANCZOS), (w + 6, 22))
        d = ImageDraw.Draw(tile)
        d.text((4, 5), f"{label} [{mode}]   ORIGINAL | V7", fill=(255, 220, 60))
        tiles.append(tile)
    if not tiles:
        return
    W = max(t.width for t in tiles)
    H = sum(t.height + 6 for t in tiles)
    canvas = Image.new("RGB", (W, H), (10, 10, 12))
    y = 0
    for t in tiles:
        canvas.paste(t, (0, y))
        y += t.height + 6
    p = OUT / "detext_v7_compare.jpg"
    canvas.save(p, quality=92)
    print("->", p, canvas.size)


if __name__ == "__main__":
    if "--compare" not in sys.argv:
        order = []
        for pref, *_ in JOBS:
            if pref not in order:
                order.append(pref)
        for pref in order:
            r = process(pref)
            if not r:
                continue
            dst, rep = r
            print(f"{dst.name[:48]:<50} " + ", ".join(f"{l}[{m}]" for l, m in rep))
    print()
    compare()
