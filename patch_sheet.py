# -*- coding: utf-8 -*-
"""写回 180 总表 Shot_007 的 P/R/AF 三格，并回读验证。用法：python patch_sheet.py --apply"""
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
APPLY = "--apply" in sys.argv

CACHE = Path(__file__).resolve().parent / "source" / "audit"
new = json.loads((Path(__file__).resolve().parent / "fixed" /
                  "180Shots_V19_shot007fix.json").read_text(encoding="utf-8"))[6]

meta = api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}"
           "?fields=sheets(properties(title))")
sheet = meta["sheets"][0]["properties"]["title"]
q = sheet.replace("'", "''")


def read_row():
    vals = api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/"
               f"'{q}'!A8:AF8?majorDimension=ROWS")["values"][0]
    return vals


before = read_row()
assert before[1] == "Shot_007"
idx = {"P": 15, "R": 17, "AF": 31}
for col, key in (("P", "primary_image_path"), ("R", "upload_instruction"), ("AF", "cloud_dispatch_command_zh")):
    cur = before[idx[col]]
    assert cur.replace(OLD_NAME, NEW_NAME).replace(OLD_ID, NEW_ID) == new[key], (col, key)
print("写前校验通过：三格现值可精确替换为 JSON 新值")

if not APPLY:
    print("DRY-RUN：未写入。加 --apply 执行。")
    raise SystemExit(0)

requests = []
for col, key in (("P", "primary_image_path"), ("R", "upload_instruction"), ("AF", "cloud_dispatch_command_zh")):
    requests.append({
        "range": f"'{q}'!{col}8",
        "values": [[new[key]]],
    })
resp = api(f"https://sheets.googleapis.com/v4/spreadsheets/{SID}/values:batchUpdate",
           data=json.dumps({"valueInputOption": "RAW", "data": requests}).encode(),
           method="POST", ctype="application/json; charset=UTF-8")
print(f"batchUpdate 返回更新范围 {resp.get('totalUpdatedCells')} 格 / {resp.get('totalUpdatedRanges')} 个区间")

after = read_row()
for col, key in (("P", "primary_image_path"), ("R", "upload_instruction"), ("AF", "cloud_dispatch_command_zh")):
    print(f"\n{col} {key}")
    print(f"  回读长度 {len(after[idx[col]])}  与 JSON 相同={after[idx[col]] == new[key]}")
    assert after[idx[col]] == new[key]

# 整行逐格比对：只允许 P/R/AF 变化
changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
print(f"\n整行变化列索引：{changed}")
assert changed == [15, 17, 31], changed
print("✔ 总表已修复，且仅 P/R/AF 三格变化")
