# -*- coding: utf-8 -*-
"""体检 B3：IP 词的上下文性质、540/600 子镜计数、第 7 镜引用错配定位。"""
import json
import re
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()

CACHE = Path(__file__).resolve().parent / "source" / "audit"
F180 = CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json"
F120 = CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json"
RAILS = {"180": F180, "120": F120}

print("=" * 78)
print("B3-1. IP 词在 prompt_zh / prompt_en 中的上下文性质（禁止式 vs 正向描述）")
print("=" * 78)
NEG_CUES = ("严禁", "禁止", "不得", "杜绝", "移除", "抹除", "不出现", "无文字", "无任何", "去字",
            "must not", "no ", "never", "avoid", "remove", "without", "forbidden", "zero")
for tag, path in RAILS.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    print(f"\n--- {tag} 轨 ---")
    for field in ("prompt_zh", "prompt_en"):
        for w in ("Kitty", "茶百道", "Vintage News", "小樱", "你的名字", "君の名は"):
            hits = []
            for s in shots:
                txt = str(s.get(field, ""))
                for m in re.finditer(re.escape(w), txt):
                    a, b = max(0, m.start() - 70), min(len(txt), m.end() + 70)
                    hits.append((s.get("shot_number") or s.get("manus_15s_number"), txt[a:b].replace("\n", " ")))
            if not hits:
                continue
            neg = sum(1 for _, ctx in hits if any(c in ctx for c in NEG_CUES))
            print(f"  {field} / {w}: {len(hits)} 处；疑似“禁止/排除”语境 {neg} 处")
            for num, ctx in hits[:2]:
                print(f"     镜{num}: …{ctx}…")

print("\n" + "=" * 78)
print("B3-2. 540 / 600 子镜计数（motion_zh 里的 Sub-Cut 段）")
print("=" * 78)
for tag, path in RAILS.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    dist = Counter()
    total = 0
    for s in shots:
        n = len(re.findall(r"Sub-Cut\s*[α-ωa-z0-9]", str(s.get("motion_zh", ""))))
        dist[n] += 1
        total += n
    print(f"  {tag} 轨：每镜 Sub-Cut 段数分布 {dict(sorted(dist.items()))}，合计 {total}")
    # 子镜时长/帧号是否连续
    bad = []
    for s in shots:
        txt = str(s.get("motion_zh", ""))
        subs = re.findall(r"Sub-Cut\s*[α-ω]\s*·\s*([\d.]+)[–-]([\d.]+)秒", txt)
        if subs:
            spans = [(float(a), float(b)) for a, b in subs]
            dur = float(s.get("duration_sec", 0))
            if abs(spans[0][0]) > 1e-6 or abs(spans[-1][1] - dur) > 1e-6:
                bad.append((s.get("shot_number") or s.get("manus_15s_number"), spans[0][0], spans[-1][1], dur))
            for (a1, b1), (a2, b2) in zip(spans, spans[1:]):
                if abs(b1 - a2) > 1e-6:
                    bad.append((s.get("shot_number") or s.get("manus_15s_number"), "断裂", b1, a2))
    print(f"     子镜时间轴不闭合/断裂：{len(bad)} 处 {bad[:4]}")

print("\n" + "=" * 78)
print("B3-3. 第 7 镜主母带名称↔ID 错配定位")
print("=" * 78)
ASSETS = "1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG"
q = urllib.parse.quote(f"'{ASSETS}' in parents and trashed=false")
assets = {f["name"]: f["id"] for f in api(
    f"https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name)&pageSize=300"
    "&supportsAllDrives=true").get("files", [])}
by_id = {v: k for k, v in assets.items()}
shots = json.loads(F180.read_text(encoding="utf-8"))
for s in shots:
    nm = s.get("primary_image_path")
    fid = s.get("primary_drive_file_id")
    if nm and fid and assets.get(Path(nm).name) != fid:
        print(f"  镜 {s['shot_number']} ({s['shot_id']})")
        print(f"     清单名称：{Path(nm).name}")
        print(f"     清单 ID ：{fid}  → 实指：{by_id.get(fid)}")
        print(f"     同名实际 ID：{assets.get(Path(nm).name)}")
        print(f"     first_frame_source：{s.get('first_frame_source', '')[:180]}")

print("\n" + "=" * 78)
print("B3-4. 铁律覆盖与 VO / 台词统计")
print("=" * 78)
for tag, path in RAILS.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    rule_zh = sum(1 for s in shots if "铁律" in str(s.get("prompt_zh", "")))
    rule_en = sum(1 for s in shots if "Rule" in str(s.get("prompt_en", "")))
    vo = sum(1 for s in shots if "VO" in str(s.get("audio_cue", "")))
    sfx = sum(1 for s in shots if "SFX" in str(s.get("audio_cue", "")))
    bgm = sum(1 for s in shots if "BGM" in str(s.get("audio_cue", "")))
    audio_empty = sum(1 for s in shots if not str(s.get("audio_cue", "")).strip())
    print(f"  {tag} 轨：含铁律 {rule_zh}/{len(shots)}（EN {rule_en}）｜含 VO {vo}｜含 SFX {sfx}｜含 BGM {bgm}｜audio 为空 {audio_empty}")
    # 铁律条数
    cnt = Counter(len(set(re.findall(r"铁律\s*([0-9]+(?:\.[0-9])?)", str(s.get("prompt_zh", ""))))) for s in shots)
    print(f"     每镜出现的不同铁律编号数分布：{dict(sorted(cnt.items()))}")
    print(f"     出现过的铁律编号：{sorted(set(re.findall(r'铁律\\s*([0-9]+(?:\\.5)?)', ' '.join(str(s.get('prompt_zh','')) for s in shots))), key=float)}")

print("\n" + "=" * 78)
print("B3-5. 模式标签分布 / 时长分布")
print("=" * 78)
for tag, path in RAILS.items():
    shots = json.loads(path.read_text(encoding="utf-8"))
    modes = Counter(str(s.get("manus_mode", "")).split("：")[0].strip() for s in shots)
    durs = Counter(float(s.get("duration_sec", 0)) for s in shots)
    print(f"  {tag} 轨：模式 {dict(sorted(modes.items()))}")
    print(f"     时长分布 {dict(sorted(durs.items()))}")
