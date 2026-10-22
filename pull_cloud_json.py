# -*- coding: utf-8 -*-
"""拉取云端当前 180/120 JSON，与本地缓存比对，定位差异。"""
import hashlib
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
CACHE = Path(__file__).resolve().parent / "source" / "audit"
CUR = CACHE / "cloud_current"
CUR.mkdir(exist_ok=True)

IDS = {
    "180": ("15fC3MHNYCklvPmdmZsLba6uiqVGYhOgA",
            "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json"),
    "120": ("1I8dAlyoGJUS4H3QUqd1Y0lJ9oVwFk9Ab",
            "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json"),
}

for tag, (fid, name) in IDS.items():
    raw = api(f"https://www.googleapis.com/drive/v3/files/{fid}?alt=media&supportsAllDrives=true", raw=True)
    p = CUR / name
    p.write_bytes(raw)
    old = (CACHE / name).read_bytes() if (CACHE / name).exists() else b""
    print(f"{tag} 云端 {len(raw)}B  md5 {hashlib.md5(raw).hexdigest()}")
    print(f"{tag} 缓存 {len(old)}B  md5 {hashlib.md5(old).hexdigest()}")
    if raw != old:
        a = json.loads(old)
        b = json.loads(raw)
        print(f"  条目数 缓存 {len(a)} / 云端 {len(b)}")
        # 找字段集合差异
        keys_a = set().union(*(x.keys() for x in a)) if a else set()
        keys_b = set().union(*(x.keys() for x in b)) if b else set()
        print(f"  仅缓存有字段: {sorted(keys_a - keys_b)}")
        print(f"  仅云端有字段: {sorted(keys_b - keys_a)}")
        # 逐条找不同
        diffs = 0
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                diffs += 1
                if diffs <= 5:
                    dk = [k for k in set(x) | set(y) if x.get(k) != y.get(k)]
                    print(f"  第{i+1}条 {x.get('shot_id')}: 差异字段 {dk[:8]}")
                    for k in dk[:3]:
                        print(f"     {k}: 缓存={str(x.get(k))[:120]!r}")
                        print(f"     {k}: 云端={str(y.get(k))[:120]!r}")
        print(f"  差异条目 {diffs}")
    else:
        print("  ✔ 完全一致")
    print()
