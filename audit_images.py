# -*- coding: utf-8 -*-
"""体检 A：40 张母带真实像素尺寸 + 重画包 46 件与云端逐件对照。"""
import hashlib
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, fresh_token  # noqa: E402
from PIL import Image  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()
AUTH = {"Authorization": api.__globals__["H"]["Authorization"]}

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
CACHE.mkdir(parents=True, exist_ok=True)

ASSETS = "1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG"
PACK_MASTERS = "1tKk8vB5d8UUpCx0EWkFh6pjgLThsPjZO"
PACK_MARKS = "17jwfDPKUmIXpVpuqDL3RrOSdbYeBMsDV"
LOCAL_PACK = ROOT / "redraw_pack"


def listing(folder, extra=""):
    q = urllib.parse.quote(f"'{folder}' in parents and trashed=false")
    url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
           f"&fields=files(id,name,size,md5Checksum){extra}"
           "&pageSize=300&supportsAllDrives=true")
    return api(url).get("files", [])


def fetch(fid):
    req = urllib.request.Request(
        f"https://www.googleapis.com/drive/v3/files/{fid}?alt=media&supportsAllDrives=true",
        headers=AUTH)
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


print("=" * 78)
print("A1. 母带库 40 张：文件名声明尺寸 vs 实际像素")
print("=" * 78)
masters = listing(ASSETS)
assert len(masters) == 40, f"母带数量异常：{len(masters)}"
sizes_actual = Counter()
bad = []
for f in sorted(masters, key=lambda x: x["name"]):
    m = re.search(r"(\d{3,4})x(\d{3,4})_4K", f["name"])
    claim = (int(m.group(1)), int(m.group(2))) if m else None
    p = CACHE / f["name"]
    if not p.exists() or p.stat().st_size != int(f["size"]):
        p.write_bytes(fetch(f["id"]))
    with Image.open(io.BytesIO(p.read_bytes())) as im:
        act = im.size
    sizes_actual[act] += 1
    tag = "OK " if claim == act else "差异"
    if claim != act:
        bad.append((f["name"], claim, act))
    print(f"  {tag} {act[0]}x{act[1]:<5} 声明{claim}  {f['name'][:58]}")

print("\n实际尺寸分布：")
for k, v in sizes_actual.most_common():
    print(f"  {k[0]}x{k[1]}: {v} 张")
print(f"文件名声明与实际不一致：{len(bad)} 张")
for n, c, a in bad:
    print(f"   ! {n[:70]}  声明{c} 实际{a}")

print("\n" + "=" * 78)
print("A2. 重画包（V17_待重画）云端 4 项 + 46 图 vs 本地副本")
print("=" * 78)
cloud_pack = {f["name"]: f for f in listing("1o6sBhOJJBfVcMJttU7YxzsCCixGdFao0")}
print("云端待重画目录顶层：", ", ".join(sorted(cloud_pack)))
for sub_name, sub_id, local_dir in (
        ("母带原图", PACK_MASTERS, LOCAL_PACK / "母带原图"),
        ("区域标注图", PACK_MARKS, LOCAL_PACK / "区域标注图")):
    cloud_sub = {f["name"]: f for f in listing(sub_id)}
    local_files = {p.name: p for p in local_dir.iterdir() if p.is_file()}
    print(f"\n  [{sub_name}] 云端 {len(cloud_sub)} 件 / 本地 {len(local_files)} 件")
    only_cloud = set(cloud_sub) - set(local_files)
    only_local = set(local_files) - set(cloud_sub)
    mismatch = []
    for n in sorted(set(cloud_sub) & set(local_files)):
        h = hashlib.md5(local_files[n].read_bytes()).hexdigest()
        if h != cloud_sub[n].get("md5Checksum"):
            mismatch.append((n, int(cloud_sub[n]["size"]), local_files[n].stat().st_size))
    print(f"    只存在于云端：{len(only_cloud)}  只存在于本地：{len(only_local)}  md5 不一致：{len(mismatch)}")
    for n in sorted(only_cloud):
        print(f"      + 云端独有 {n}")
    for n in sorted(only_local):
        print(f"      - 本地独有 {n}")
    for n, cs, ls in mismatch:
        print(f"      ! md5 不同 {n[:56]} 云端{cs//1024}KB 本地{ls//1024}KB")

print("\n" + "=" * 78)
print("A3. 重画包 23 张底图副本 vs 母带库现版（是否已过期）")
print("=" * 78)
m_by_name = {f["name"]: f for f in masters}
cloud_orig = {f["name"]: f for f in listing(PACK_MASTERS)}
for n, f in sorted(cloud_orig.items()):
    m = m_by_name.get(n)
    if not m:
        print(f"  ! 母带库无同名：{n}")
        continue
    same = m.get("md5Checksum") == f.get("md5Checksum")
    print(f"  {'同版' if same else '过期'} {n[:58]:60s} 包{int(f['size'])//1024:>5}KB  库{int(m['size'])//1024:>5}KB"
          f"  库mod={m.get('modifiedTime', '')[:10]}")

# 保存一份汇总
summary = {
    "masters_count": len(masters),
    "dims_distribution": {f"{k[0]}x{k[1]}": v for k, v in sizes_actual.items()},
    "filename_dim_mismatch": [{"name": n, "claimed": list(c), "actual": list(a)} for n, c, a in bad],
    "pack_stale_vs_masters": [
        n for n, f in cloud_orig.items()
        if m_by_name.get(n) and m_by_name[n].get("md5Checksum") != f.get("md5Checksum")],
}
(CACHE / "audit_images_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n汇总已写入 {CACHE / 'audit_images_summary.json'}")
