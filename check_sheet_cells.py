# -*- coding: utf-8 -*-
"""总表 Shot_007 三格：与 JSON 字段逐字比对 + 生成待写值（默认 dry-run）。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
SID = "10Oq8OAWJpqRMc-ze2TGqRHJY_hDkoul1DHXUpPYtwoY"
OLD_NAME = "04_图3.1_Scene01_暮冬之雪与春雨之窗_3840x2160_4K.jpg"
NEW_NAME = "01c_图0.1_上幅16x9_星河苍穹与双色彗星终幕空镜_3840x2160_4K.jpg"
OLD_ID = "1pkU017WSHLc7v3EAFPCO7y1gqmSWoVNv"
NEW_ID = "16S3Lyt2Lbf8uyU8JMy6zUayKY87aSQHT"

CACHE = Path(__file__).resolve().parent / "source" / "audit"
old = json.loads((CACHE / "cloud_current" /
                  "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json").read_text(encoding="utf-8"))
new = json.loads((Path(__file__).resolve().parent / "fixed" /
                  "180Shots_V19_shot007fix.json").read_text(encoding="utf-8"))
o7, n7 = old[6], new[6]

meta = api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}"
           "?fields=sheets(properties(title))")
sheet = meta["sheets"][0]["properties"]["title"]
q = sheet.replace("'", "''")
vals = api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/"
           f"'{q}'!A1:AF10?majorDimension=ROWS")["values"]
row = next(i for i, r in enumerate(vals, 1) if len(r) > 1 and r[1].strip() == "Shot_007")
print(f"Shot_007 行 {row}")

for col, key in (("P", "primary_image_path"), ("R", "upload_instruction"), ("AF", "cloud_dispatch_command_zh")):
    idx = 0
    for ch in col:
        idx = idx * 26 + (ord(ch) - 64)
    idx -= 1
    cur = vals[row - 1][idx] if idx < len(vals[row - 1]) else ""
    print(f"\n{col} {key}")
    print(f"  当前长度 {len(cur)}  旧 JSON 长度 {len(o7[key])}  相同={cur == o7[key]}")
    if cur != o7[key]:
        # 打印首个差异
        for i, (a, b) in enumerate(zip(cur, o7[key])):
            if a != b:
                print(f"  首个差异 @{i}: 表={a!r} JSON={b!r}")
                print(f"    表: …{cur[max(0,i-50):i+50]}…")
                print(f"    J : …{o7[key][max(0,i-50):i+50]}…")
                break
        else:
            print(f"  长度差：表尾 {cur[len(o7[key]):]!r} / JSON尾 {o7[key][len(cur):]!r}")
    repl = cur.replace(OLD_NAME, NEW_NAME).replace(OLD_ID, NEW_ID)
    print(f"  替换后与 JSON 新值相同={repl == n7[key]}  新长度={len(repl)}")
    if repl != n7[key]:
        print(f"    替换后: …{repl[:180]}…")
        print(f"    JSON新: …{n7[key][:180]}…")
