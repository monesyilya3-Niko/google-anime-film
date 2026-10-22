# -*- coding: utf-8 -*-
"""把「母带去字修订稿」原地提升回真母带库。

用 Drive `files.update` 覆盖二进制内容，**File ID 不变**，
所以 180Shots.json / 120Shots.json 里的 primary_drive_file_id 继续有效，
清单一个字都不用改。

用法:  python promote_fixes.py --yes      # 真执行
      python promote_fixes.py             # 只看将要做什么
"""
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, list_in, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

ASSETS = "1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG"
CAND = "1bMyJPEwrfUsnzLhO7soamlvFEVHxkGwy"     # 母带去字修订稿_待人工确认

EXCLUDE = {"05a_", "05b_"}    # 这两张早已原地替换过，不要重复提升

real = {f["name"]: f for f in list_in(ASSETS).values()}
fix = {f["name"]: f for f in list_in(CAND).values()}

plan = []
for name, f in sorted(fix.items()):
    if not name.startswith("FIX_"):
        continue
    target = name[4:]
    pref = target[:3]
    if pref in EXCLUDE:
        continue
    r = real.get(target)
    if not r:
        print(f"  ! 真母带库找不到 {target}（跳过）")
        continue
    plan.append((target, r["id"], f["id"], f.get("size", 0), r.get("size", 0)))

print(f"将要原地提升 {len(plan)} 张：\n")
for t, rid, fid, s1, s0 in plan:
    print(f"  {t[:60]:62s} {int(s0)//1024:>6}KB -> {int(s1)//1024:>6}KB  (FileID {rid[:12]}…)")

if "--yes" not in sys.argv:
    print("\n这是预演。加 --yes 执行。")
    raise SystemExit(0)

print("\n执行中…")
for t, rid, fid, s1, s0 in plan:
    # 先把修好的稿下载到内存，再用 files.update 覆盖真母带
    data = api(f"https://www.googleapis.com/drive/v3/files/{fid}"
               "?alt=media&supportsAllDrives=true")
    if not isinstance(data, (bytes, bytearray)):
        print(f"  ✗ 下载失败 {t}")
        continue
    api(f"https://www.googleapis.com/upload/drive/v3/files/{rid}"
        "?uploadType=media&supportsAllDrives=true&fields=id,name,size",
        data=bytes(data), method="PATCH", ctype="image/jpeg")
    print(f"  ✓ 已提升 {t[:56]}")

print("\n完成。File ID 全部未变，清单无需修改。")
