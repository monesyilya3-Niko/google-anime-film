# -*- coding: utf-8 -*-
"""《暮冬念春》V17 交付终检：云端结构 + 本地产物 + 清单完整性。"""
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, list_in, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

V16 = "1ya8IwwmFgLWCSE9i_sihtXyTmdW4R528"
ASSETS = "1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG"
V17 = "1gOkAIAs2gY3uXK48R1VCwTiuagMpTOXG"

print("=" * 72)
print("云端结构")
print("=" * 72)
for label, fid in (("V16 全案总库", V16), ("V17 修复版", V17), ("4K 母带库", ASSETS)):
    items = list_in(fid)
    print(f"\n{label}  ({len(items)} 项)")
    for n, f in sorted(items.items()):
        kind = "DIR" if f["mimeType"].endswith("folder") else (
            "GDOC" if f["mimeType"].endswith("document") else
            "SHEET" if f["mimeType"].endswith("spreadsheet") else "FILE")
        kb = int(f.get("size", 0)) // 1024
        print(f"   [{kind:5s}] {n[:62]:<62} {kb:>6} KB")

# V17 里的子文件夹（候选稿）
q = urllib.parse.quote(f"'{V17}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false")
subs = api(f"https://www.googleapis.com/drive/v3/files?q={q}"
           "&fields=files(id,name)&pageSize=20&supportsAllDrives=true"
           "&includeItemsFromAllDrives=true").get("files", [])
for s in subs:
    print(f"\n  子目录: {s['name']}")
    for n in sorted(list_in(s["id"]).keys()):
        print(f"     · {n[:66]}")

print()
print("=" * 72)
print("清单完整性（本地修复产物）")
print("=" * 72)
ROOT = Path(__file__).resolve().parent
for pat, label, n_expect in (("fixed/*180Shots.json", "180 镜", 180),
                             ("fixed/*120Shots.json", "120 镜", 120)):
    for p in ROOT.glob(pat):
        S = json.load(open(p, encoding="utf-8"))
        assert len(S) == n_expect, f"{label} 数量不符"
        nums = [s.get("shot_number", s.get("manus_15s_number")) for s in S]
        ok_n = nums == list(range(1, n_expect + 1))
        ban = sum(1 for s in S if "画面内严禁出现任何文字" in (s.get("prompt_zh") or ""))
        ben = sum(1 for s in S if "no text or letters" in (s.get("prompt_en") or ""))
        brk = sum(1 for s in S if (s.get("prompt_zh") or "").count("【") !=
                   (s.get("prompt_zh") or "").count("】"))
        named = sum(1 for s in S if "VINTAGE NEWS" in (s.get("prompt_zh") or "")
                    or "严禁出现任何文字或片名" in (s.get("prompt_zh") or "")
                    or "严禁出现任何文字或代号" in (s.get("prompt_zh") or "")
                    or "掌心严禁出现" in (s.get("prompt_zh") or ""))
        male = sum(1 for s in S
                   if any((a.get("filename") or "").startswith(("03", "03a", "03b"))
                          for a in (s.get("auxiliary_cloud_assets") or [])))
        hero = sum(1 for s in S
                   if any((a.get("filename") or "").startswith("02")
                          for a in (s.get("auxiliary_cloud_assets") or [])))
        need = sum(1 for s in S if "冬冰絮" in (s.get("prompt_zh") or "") or
                   "YXP" in (s.get("prompt_zh") or ""))
        print(f"\n  {label} ({p.name[:44]})")
        print(f"    编号 1..{n_expect} 连续      : {ok_n}")
        print(f"    禁文字条款(中/英)          : {ban}/{n_expect} · {ben}/{n_expect}")
        print(f"    点名具体禁制元素           : {named}")
        print(f"    括号配平异常                : {brk}")
        print(f"    锁脸基准覆盖 女主/男主      : {hero} / {male} (需要男主的镜头 {need})")

print()
print("=" * 72)
print("本地交付件")
print("=" * 72)
for p in sorted((ROOT / "v17").glob("*")):
    print(f"  {p.name[:60]:<60} {p.stat().st_size//1024:>5} KB")
