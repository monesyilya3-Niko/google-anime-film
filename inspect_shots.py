# -*- coding: utf-8 -*-
"""体检 B2：把 180/120 轨的字段结构摊开看，并定位可疑字段值。"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
CACHE = Path(__file__).resolve().parent / "source" / "audit"
F180 = CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json"
F120 = CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json"

for tag, path in (("180", F180), ("120", F120)):
    shots = json.loads(path.read_text(encoding="utf-8"))
    print("=" * 78)
    print(f"{tag} 轨 · 第 1 镜完整字段（值截断 300 字符）")
    print("=" * 78)
    for k, v in shots[0].items():
        s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
        s = s.replace("\n", " ⏎ ")
        print(f"  {k}: {s[:300]}")
    print()
    # 字段出现率
    cnt = Counter()
    for s in shots:
        for k in s:
            cnt[k] += 1
    rare = sorted(k for k, v in cnt.items() if v != len(shots))
    print(f"  非全员字段：{rare}")
    print()

# 可疑词出现在哪个字段
for tag, path in (("180", F180), ("120", F120)):
    shots = json.loads(path.read_text(encoding="utf-8"))
    print("=" * 78)
    print(f"{tag} 轨：第三方 IP 词出现的字段分布")
    print("=" * 78)
    words = ("Kitty", "茶百道", "Vintage News", "小樱", "你的名字", "君の名は")
    where = Counter()
    samples = {}
    for s in shots:
        for k, v in s.items():
            blob = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
            for w in words:
                if w in blob:
                    where[(k, w)] += 1
                    samples.setdefault((k, w), (s.get("shot_number") or s.get("manus_15s_number"),
                                                blob[:220].replace("\n", " ")))
    for (k, w), n in sorted(where.items()):
        num, snap = samples[(k, w)]
        print(f"  {k:<28} {w:<14} {n:>3} 次   例：镜{num} … {snap[:150]}")
    print()

# 名称↔ID 错配定位
print("=" * 78)
print("180 轨：名称↔ID 错配逐条定位")
print("=" * 78)
import urllib.parse  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, fresh_token  # noqa: E402
fresh_token()
ASSETS = "1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG"
q = urllib.parse.quote(f"'{ASSETS}' in parents and trashed=false")
assets = {f["name"]: f["id"] for f in api(
    f"https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)&pageSize=300"
    "&supportsAllDrives=true").get("files", [])}
by_id = {v: k for k, v in assets.items()}
for tag, path in (("180", F180), ("120", F120)):
    shots = json.loads(path.read_text(encoding="utf-8"))
    for s in shots:
        for k in s:
            if k.endswith("drive_file_id"):
                fid = s[k]
                if not fid:
                    continue
                expect_name = by_id.get(fid)
                name_key = k.replace("drive_file_id", "cloud_filename").replace("drive_file_id", "image_path")
                nm = s.get(name_key)
                if nm and expect_name and Path(nm).name != expect_name:
                    print(f"  [{tag}] 镜 {s.get('shot_number') or s.get('manus_15s_number')} 字段 {k}")
                    print(f"       清单写：{Path(nm).name}")
                    print(f"       该 ID 实指：{expect_name}")
                    print(f"       ID：{fid}  →  https://drive.google.com/file/d/{fid}/view")
