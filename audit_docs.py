# -*- coding: utf-8 -*-
"""体检 C：文档层（01–05 云端 vs 本地、G Doc/Sheet 导出实测、README 引用 ID 核对、回收站）。"""
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()
AUTH = {"Authorization": api.__globals__["H"]["Authorization"]}

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
CACHE.mkdir(parents=True, exist_ok=True)
LOCAL = CACHE

V19 = "103fzTVsi34QCz6hkpHTzR7RJNsTmZgN-"
V17 = "1gOkAIAs2gY3uXK48R1VCwTiuagMpTOXG"
PACK = "1o6sBhOJJBfVcMJttU7YxzsCCixGdFao0"
README_ID = "1ZSZ-suR1vPyw37EgFLEEtTledCsy7hga"

problems = []


def check(cond, msg):
    if not cond:
        problems.append(msg)
    return cond


def get(url):
    req = urllib.request.Request(url, headers=AUTH)
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def list_folder(fid, fields="id,name,mimeType,size,md5Checksum,modifiedTime"):
    q = urllib.parse.quote(f"'{fid}' in parents and trashed=false")
    out, token = [], None
    while True:
        url = (f"https://www.googleapis.com/drive/v3/files?q={q}&fields=files({fields})"
               "&pageSize=200&supportsAllDrives=true")
        if token:
            url += f"&pageToken={urllib.parse.quote(token)}"
        d = api(url)
        out += d.get("files", [])
        token = d.get("nextPageToken")
        if not token:
            return out


print("=" * 84)
print("C1. V19 目录 19 项（名称 / 类型 / 体积）")
print("=" * 84)
v19 = list_folder(V19)
for f in sorted(v19, key=lambda x: x["name"]):
    print(f"  {int(f.get('size', 0)) // 1024:>6}KB  {f['mimeType']:<40}  {f['name']}")
print(f"  合计 {len(v19)} 项")

print("\n" + "=" * 84)
print("C2. 01–05 云端副本 vs 本地工作副本（md5）")
print("=" * 84)
cloud_md = {f["name"]: f for f in v19 if f["mimeType"] == "text/markdown"}
for f in sorted(cloud_md.values(), key=lambda x: x["name"]):
    p = CACHE / f["name"]
    if not p.exists():
        p.write_bytes(get(f"https://www.googleapis.com/drive/v3/files/{f['id']}?alt=media&supportsAllDrives=true"))
    ch = hashlib.md5(p.read_bytes()).hexdigest()
    local = next((q for q in LOCAL.iterdir() if q.name[:2] == f["name"][:2] and q.suffix == ".md"), None)
    lh = hashlib.md5(local.read_bytes()).hexdigest() if local else None
    same = ch == lh
    print(f"  {'同版' if same else '不同'}  {f['name'][:60]:62s} 云{int(f['size'])//1024:>5}KB"
          f" 本地{(local.stat().st_size // 1024) if local else 0:>5}KB")
    if not same:
        print(f"        云md5 {ch}\n        本md5 {lh}  本地文件 {local.name if local else '缺失'}")
    check(same, f"01–05 云端与本地不一致：{f['name']}")

print("\n" + "=" * 84)
print("C3. Google 文档 / 表格导出实测（README 交接指令是否可执行）")
print("=" * 84)
gdocs = [f for f in v19 if f["mimeType"] == "application/vnd.google-apps.document"]
gsheets = [f for f in v19 if f["mimeType"] == "application/vnd.google-apps.spreadsheet"]
print(f"  Google 文档 {len(gdocs)} 份 / Google 表格 {len(gsheets)} 份")
shot_re = re.compile(r"Shot_\d{3}")
for f in sorted(gdocs + gsheets, key=lambda x: x["name"]):
    is_doc = f["mimeType"].endswith("document")
    mime = "text/markdown" if is_doc else "text/csv"
    url = (f"https://www.googleapis.com/drive/v3/files/{f['id']}/export?mimeType={urllib.parse.quote(mime)}")
    try:
        data = get(url)
    except Exception as e:  # noqa: BLE001
        # 回退纯文本
        try:
            data = get(f"https://www.googleapis.com/drive/v3/files/{f['id']}/export?mimeType=text/plain")
            mime = "text/plain"
        except Exception as e2:  # noqa: BLE001
            print(f"  ✗ 导出失败 {f['name']}: {e} / {e2}")
            problems.append(f"导出失败：{f['name']}")
            continue
    txt = data.decode("utf-8", "replace")
    (CACHE / f"export_{f['name'].replace('/', '_')}.{'csv' if not is_doc else 'md'}").write_text(txt, encoding="utf-8")
    if is_doc:
        shots = sorted(set(shot_re.findall(txt)))
        shots2 = sorted(set(re.findall(r"Manus15s_\d{3}", txt)))
        print(f"  ✓ {f['name'][:48]:50s} 导出 {mime:<12} {len(txt)//1024:>5}KB  含 Shot_xxx {len(shots)} 个"
              f"（{shots[:1]}…{shots[-1:]}） Manus15s_xxx {len(shots2)} 个")
        check(len(shots) > 0 or len(shots2) > 0, f"{f['name']} 导出内容无镜头编号（疑似空壳）")
    else:
        lines = [ln for ln in txt.splitlines() if ln.strip()]
        cols = max((len(ln.split(",")) for ln in lines), default=0)
        print(f"  ✓ {f['name'][:48]:50s} 导出 {mime:<12} {len(txt)//1024:>5}KB  非空行 {len(lines)}  最大列数 {cols}")
        check(len(lines) >= 100, f"{f['name']} 行数偏少：{len(lines)}")

print("\n" + "=" * 84)
print("C4. README 第 8 节表格里的 File ID 是否与云端实况一致")
print("=" * 84)
readme = (ROOT / "00_README_工程总入口与交接说明.md").read_text(encoding="utf-8")
all_known = {f["id"]: f["name"] for f in v19}
for folder, label in ((V19, "V19"), (V17, "V17"), (PACK, "待重画"), ("1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG", "母带库")):
    for f in list_folder(folder):
        all_known[f["id"]] = f["name"]
readme_ids = set(re.findall(r"\b1[A-Za-z0-9_-]{32}\b", readme))
unknown = sorted(i for i in readme_ids if i not in all_known)
print(f"  README 中出现 File ID {len(readme_ids)} 个；云端可解析 {len(readme_ids) - len(unknown)} 个；无法解析 {len(unknown)} 个")
for i in unknown:
    print(f"     ? {i}")

print("\n" + "=" * 84)
print("C5. 回收站与根目录")
print("=" * 84)
trash = api("https://www.googleapis.com/drive/v3/files?q=trashed=true&fields=files(id,name,size)"
            "&pageSize=200&supportsAllDrives=true").get("files", [])
print(f"  回收站 {len(trash)} 项：")
for f in trash:
    print(f"     {f['name'][:70]:72s} {int(f.get('size', 0)) // 1024:>5}KB  {f['id']}")
root = list_folder("1ya8IwwmFgLWCSE9i_sihtXyTmdW4R528")
print(f"  根目录 {len(root)} 项：")
for f in sorted(root, key=lambda x: x["name"]):
    print(f"     {f['mimeType']:<40} {f['name'][:70]}")

print("\n" + "=" * 84)
print(f"C 段问题合计：{len(problems)}")
for i, p in enumerate(problems, 1):
    print(f"  {i}. {p}")
