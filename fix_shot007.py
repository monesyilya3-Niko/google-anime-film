# -*- coding: utf-8 -*-
"""Shot_007 三处 V18 残留修复（仅本地生成 fixed 文件，不上传）。

修复字段：
  - primary_image_path:        04_图3.1 → 01c_图0.1
  - upload_instruction:        04_图3.1 + 1pkU017 → 01c_图0.1 + 16S3Lyt2
  - cloud_dispatch_command_zh: 同上
严格要求：除这三处外，180 条 JSON 逐条完全不变；保留原 CRLF 与 indent=1 排版。
"""
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
SRC = CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json"
OUT = ROOT / "fixed" / "180Shots_V19_shot007fix.json"

OLD_NAME = "04_图3.1_Scene01_暮冬之雪与春雨之窗_3840x2160_4K.jpg"
NEW_NAME = "01c_图0.1_上幅16x9_星河苍穹与双色彗星终幕空镜_3840x2160_4K.jpg"
OLD_ID = "1pkU017WSHLc7v3EAFPCO7y1gqmSWoVNv"
NEW_ID = "16S3Lyt2Lbf8uyU8JMy6zUayKY87aSQHT"

raw = SRC.read_bytes()
print(f"源文件 {len(raw)}B  md5 {hashlib.md5(raw).hexdigest()}")
crlf = b"\r\n" in raw
lf_only = raw.count(b"\n") - raw.count(b"\r\n")
print(f"行尾：CRLF={crlf}  LF-only={lf_only}")

text = raw.decode("utf-8")
shots = json.loads(text)

# 字节级往返验证（保留 CRLF）
rt = json.dumps(shots, ensure_ascii=False, indent=1)
if crlf and "\r\n" not in rt:
    rt = rt.replace("\n", "\r\n")
print(f"往返字节一致：{rt.encode('utf-8') == raw}")

s7 = next(s for s in shots if s.get("shot_number") == 7)
print("\n修复前：")
print(f"  primary_image_path = {s7['primary_image_path']}")
print(f"  upload 旧名出现 {s7['upload_instruction'].count(OLD_NAME)} 次 / 旧ID {s7['upload_instruction'].count(OLD_ID)} 次")
print(f"  dispatch 旧名出现 {s7['cloud_dispatch_command_zh'].count(OLD_NAME)} 次 / 旧ID {s7['cloud_dispatch_command_zh'].count(OLD_ID)} 次")

assert s7["primary_image_path"] == OLD_NAME, "primary_image_path 不是预期旧值，终止"
assert s7["upload_instruction"].count(OLD_NAME) == 1
assert s7["upload_instruction"].count(OLD_ID) == 1
assert s7["cloud_dispatch_command_zh"].count(OLD_NAME) == 1
assert s7["cloud_dispatch_command_zh"].count(OLD_ID) == 1

s7["primary_image_path"] = NEW_NAME
for k in ("upload_instruction", "cloud_dispatch_command_zh"):
    s7[k] = s7[k].replace(OLD_NAME, NEW_NAME).replace(OLD_ID, NEW_ID)

# 逐条比对：除第 7 条外必须完全一致；第 7 条只允许三个字段变化
before = json.loads(text)
after = shots
for i, (a, b) in enumerate(zip(before, after)):
    if a != b:
        changed = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
        assert a["shot_number"] == 7, f"第 {a['shot_number']} 条也被改动：{changed}"
        assert set(changed) == {"primary_image_path", "upload_instruction", "cloud_dispatch_command_zh"}, changed
        print(f"\n第 {a['shot_number']} 条变化字段：{sorted(changed)}")

# 生成输出
out = json.dumps(shots, ensure_ascii=False, indent=1)
if crlf:
    out = out.replace("\n", "\r\n")
data = out.encode("utf-8")
OUT.parent.mkdir(exist_ok=True)
OUT.write_bytes(data)
print(f"\n输出 {OUT}")
print(f"  {len(data)}B  md5 {hashlib.md5(data).hexdigest()}")

# 回读验证
chk = json.loads(OUT.read_text(encoding="utf-8"))
c7 = next(s for s in chk if s["shot_number"] == 7)
assert c7["primary_image_path"] == NEW_NAME
assert c7["upload_instruction"].count(NEW_NAME) == 1 and c7["upload_instruction"].count(NEW_ID) == 1
assert c7["cloud_dispatch_command_zh"].count(NEW_NAME) == 1 and c7["cloud_dispatch_command_zh"].count(NEW_ID) == 1
assert OLD_NAME not in c7["upload_instruction"] and OLD_ID not in c7["upload_instruction"]
assert OLD_NAME not in c7["cloud_dispatch_command_zh"] and OLD_ID not in c7["cloud_dispatch_command_zh"]
print("  ✔ 回读校验通过")
print(f"  01c 引用：primary={c7['primary_image_key']} / cloud={c7['primary_cloud_filename']} / id={c7['primary_drive_file_id']}")
