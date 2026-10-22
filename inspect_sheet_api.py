# -*- coding: utf-8 -*-
"""读取 180 总表真实结构：tab、Shot_007 行号、三格现值。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
SID = "10Oq8OAWJpqRMc-ze2TGqRHJY_hDkoul1DHXUpPYtwoY"

meta = api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}"
           "?fields=properties(title),sheets(properties(sheetId,title,gridProperties))")
print("表格：", meta["properties"]["title"])
for s in meta["sheets"]:
    p = s["properties"]
    print(f"  sheetId={p['sheetId']}  title={p['title']!r}  {p['gridProperties']}")

sheet = meta["sheets"][0]["properties"]["title"]
q = sheet.replace("'", "''")
vals = api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/"
           f"'{q}'!A1:AF200?majorDimension=ROWS")["values"]
print(f"\n读取 {len(vals)} 行（A:AF）")

row = None
for i, r in enumerate(vals, 1):
    if len(r) > 1 and r[1].strip() == "Shot_007":
        row = i
        print(f"\nShot_007 位于第 {i} 行")
        break
if row is None:
    raise SystemExit("未找到 Shot_007")

hdr = vals[0]
print(f"表头列数 {len(hdr)}")
for col in ("P", "R", "AF"):
    idx = 0
    for ch in col:
        idx = idx * 26 + (ord(ch) - 64)
    idx -= 1
    v = vals[row - 1][idx] if idx < len(vals[row - 1]) else ""
    print(f"\n{col}（列 {idx} / 0-based）表头={hdr[idx] if idx < len(hdr) else '?'}")
    print(f"  长度 {len(v)}")
    print(f"  值 = {v!r}")
