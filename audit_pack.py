# -*- coding: utf-8 -*-
"""体检 E：05 任务卡直链 vs 母带库、重画清单.csv、辅助槽位 3 个 ID 解析、02/04 关键声明抽查。"""
import csv
import io
import json
import re
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, list_in, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
LOCAL = CACHE
ASSETS = "1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG"
PACK = "1o6sBhOJJBfVcMJttU7YxzsCCixGdFao0"

assets = list_in(ASSETS)
by_id = {f["id"]: n for n, f in assets.items()}

print("=" * 84)
print("E1. 辅助槽位 3 个真实 ID 指向哪张母带")
print("=" * 84)
for i in ("16_EbUVTBnl1JrXxnJQjCG9yg2vVrgB_c", "1rw2CxZ5n1dtQJzUY1eQ-aRRa6BvbUJ35",
          "1xs8JeeE86UUaUtlD2mUY0auSXY278fFk"):
    print(f"  {i} → {by_id.get(i, '【不在母带库】')}")

print("\n" + "=" * 84)
print("E2. 05 任务卡底图直链 vs 母带库现版")
print("=" * 84)
doc = next(LOCAL.glob("05_*.md")).read_text(encoding="utf-8")
cards = re.findall(r"^### 任务 ([0-9a-z]+) · `([^`]+)`", doc, re.M)
print(f"  任务卡 {len(cards)} 张：{[c[0] for c in cards]}")
links = re.findall(r"https://drive\.google\.com/file/d/([A-Za-z0-9_-]{28,40})", doc)
print(f"  文档内 drive 直链 {len(links)} 个；去重 {len(set(links))} 个")
bad = [i for i in set(links) if i not in by_id]
print(f"  不在母带库的直链：{len(bad)} {bad}")
print("  任务卡编号 ↔ 母带：")
for num, name in cards:
    fid = assets.get(name, {}).get("id")
    ok = "✔" if fid else "✘ 名称不在母带库"
    print(f"     {num:<4} {ok}  {name[:66]}")
    if not fid:
        continue
    # 该卡下方 2000 字内出现的第一个 drive 链接是否等于该母带 ID
    pos = doc.find(name)
    seg = doc[pos:pos + 3000]
    m = re.search(r"https://drive\.google\.com/file/d/([A-Za-z0-9_-]{28,40})", seg)
    if m and m.group(1) != fid:
        print(f"          ! 卡片内直链 {m.group(1)} ≠ 母带库 ID {fid}（{by_id.get(m.group(1))}）")

print("\n" + "=" * 84)
print("E3. 重画清单.csv（云端 + 本地）")
print("=" * 84)
local_csv = ROOT / "redraw_pack" / "重画清单.csv"
rows = list(csv.reader(io.StringIO(local_csv.read_text(encoding="utf-8-sig"))))
print(f"  本地 重画清单.csv：{len(rows)} 行（含表头），列数 {len(rows[0])}")
print(f"  表头：{rows[0]}")
nums = [r[0] for r in rows[1:] if r]
print(f"  数据行 {len(nums)}：{nums}")
pack_names = {n for n in list_in(list_in(PACK)['母带原图']['id'])}
csv_names = {r[1] if len(r) > 1 else '' for r in rows[1:]}
print(f"  CSV 文件名 ∩ 重画包 母带原图：{len(csv_names & pack_names)} / {len(pack_names)}")
print(f"  CSV 独有：{sorted(csv_names - pack_names)[:5]}")

print("\n" + "=" * 84)
print("E4. 02 / 04 关键声明抽查")
print("=" * 84)
for fn in sorted(LOCAL.glob("0[24]_*.md")):
    txt = fn.read_text(encoding="utf-8")
    print(f"\n--- {fn.name}（{len(txt)} 字）---")
    for kw in ("540", "395", "40 字段", "字段", "27", "V18_FIX", "已合入", "11 张", "唯一"):
        for m in re.finditer(kw, txt):
            a, b = max(0, m.start() - 60), min(len(txt), m.end() + 60)
            print(f"  [{kw}] …{txt[a:b].replace(chr(10), ' ')}…")
            break
