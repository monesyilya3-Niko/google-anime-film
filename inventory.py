# -*- coding: utf-8 -*-
"""暮冬念春 全资产盘点：本地工作区 + Google Drive。

用法:
  python inventory.py local          本地 novel/ 下的相关目录
  python inventory.py drive          云端 gdrive2 的完整清单
  python inventory.py all
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
CONF = Path(os.environ["APPDATA"]) / "rclone" / "rclone.conf"

# 目录名里含这些字眼的都算本项目（用码点写，避开终端编码问题）
KEY = ["\u66ae\u51ac\u5ff5\u6625",          # 暮冬念春
       "\u5ff5\u9645"]                        # 忆隙


def local():
    novel = REPO / "novel"
    if not novel.exists():
        print("no novel dir")
        return
    for d in sorted(novel.iterdir()):
        if not d.is_dir():
            continue
        if not any(k in d.name for k in KEY):
            continue
        print("=" * 78)
        print("DIR:", d.name)
        print("=" * 78)
        for p in sorted(d.rglob("*")):
            if p.is_dir():
                continue
            rel = p.relative_to(d)
            print(f"  {rel}   [{p.stat().st_size/1024:.1f} KB]")
        print()


def token(remote="gdrive2"):
    txt = CONF.read_text(encoding="utf-8")
    m = re.search(rf"(?ms)^\[{remote}\](.*?)(?=^\[|\Z)", txt)
    if not m:
        raise SystemExit(f"no [{remote}] in rclone.conf")
    tk = re.search(r"token = (\{.*?\})", m.group(1))
    return json.loads(tk.group(1))["access_token"]


def api(url, tok):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def drive():
    tok = token()
    q = urllib.parse.quote("trashed=false")
    url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
           "&fields=files(id,name,mimeType,size,parents,md5Checksum,trashed,webViewLink)"
           "&orderBy=folder,name&pageSize=1000&supportsAllDrives=true"
           "&includeItemsFromAllDrives=true")
    files = api(url, tok).get("files", [])
    by_id = {f["id"]: f for f in files}
    # 建目录树
    kids = {}
    for f in files:
        for p in f.get("parents", []):
            kids.setdefault(p, []).append(f)
    roots = [f for f in files if not f.get("parents") or
             not any(p in by_id for p in f.get("parents", []))]
    tot_n = tot_b = 0
    native = 0

    def walk(fid, depth, prefix):
        nonlocal tot_n, tot_b, native
        for f in sorted(kids.get(fid, []), key=lambda x: x["name"]):
            isdir = f["mimeType"] == "application/vnd.google-apps.folder"
            sz = int(f.get("size") or 0)
            if isdir:
                print(f"{prefix}  {f['name']}/")
                walk(f["id"], depth + 1, prefix + "  ")
            else:
                tot_n += 1
                tot_b += sz
                tag = ""
                if f["mimeType"].startswith("application/vnd.google-apps."):
                    native += 1
                    tag = "  [原生 " + f["mimeType"].split(".")[-1] + "]"
                print(f"{prefix}  {f['name']}   {sz/1024:9.1f} KB{tag}")

    for r in roots:
        print("=" * 78)
        print("ROOT:", r["name"], f"  ({r['id']})")
        print("=" * 78)
        walk(r["id"], 1, "  ")
    print("-" * 78)
    print(f"合计: {tot_n} 个文件, {tot_b/1024/1024:.2f} MB, 其中原生 Google 文件 {native} 个")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("local", "all"):
        local()
    if what in ("drive", "all"):
        drive()
