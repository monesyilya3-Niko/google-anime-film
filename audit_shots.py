# -*- coding: utf-8 -*-
"""体检 B：180Shots / 120Shots 清单全量机器复核（账目·引用·提示词·字幕）。"""
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_v17 import api, fresh_token  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
fresh_token()
AUTH = {"Authorization": api.__globals__["H"]["Authorization"]}

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
CACHE.mkdir(parents=True, exist_ok=True)

FILES = {
    "180": ("15fC3MHNYCklvPmdmZsLba6uiqVGYhOgA",
            "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json"),
    "120": ("1I8dAlyoGJUS4H3QUqd1Y0lJ9oVwFk9Ab",
            "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json"),
}
ASSETS = "1aRc6-MNuk7wsd1OFhjZPMQGXck-OIpxG"
problems = []


def check(cond, msg):
    if not cond:
        problems.append(msg)
    return cond


def fetch_bin(fid):
    req = urllib.request.Request(
        f"https://www.googleapis.com/drive/v3/files/{fid}?alt=media&supportsAllDrives=true",
        headers=AUTH)
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def listing(folder):
    q = urllib.parse.quote(f"'{folder}' in parents and trashed=false")
    url = (f"https://www.googleapis.com/drive/v3/files?q={q}"
           "&fields=files(id,name,size)&pageSize=300&supportsAllDrives=true")
    return api(url).get("files", [])


assets = {f["name"]: f["id"] for f in listing(ASSETS)}
assets_by_id = {v: k for k, v in assets.items()}
print(f"母带库 {len(assets)} 件（引用核对基准）\n")

for tag, (fid, fname) in FILES.items():
    p = CACHE / fname
    if not p.exists():
        p.write_bytes(fetch_bin(fid))
    shots = json.loads(p.read_text(encoding="utf-8"))
    print("=" * 78)
    print(f"{tag} 轨：{fname}")
    print(f"  条目数 = {len(shots)}")
    n_expect = int(tag)
    check(len(shots) == n_expect, f"{tag} 轨条目数 {len(shots)} ≠ {n_expect}")

    # 键结构
    keys = Counter()
    for s in shots:
        keys.update(s.keys())
    print(f"  字段种类 {len(keys)}；每镜皆有：{sorted(k for k, v in keys.items() if v == len(shots))[:14]}")
    print(f"  常见字段：{sorted(keys.items(), key=lambda x: -x[1])[:14]}")

    num_key = "shot_number" if "shot_number" in shots[0] else "manus_15s_number"
    nums = [s.get(num_key) for s in shots]
    check(nums == list(range(1, len(shots) + 1)), f"{tag} 轨编号不连续：{nums[:5]}…")
    check(len(set(nums)) == len(nums), f"{tag} 轨编号有重复")

    # 时长与帧
    dur_key = next((k for k in ("duration_sec", "duration_seconds", "duration") if k in shots[0]), None)
    frame_keys = [k for k in shots[0] if "frame" in k.lower()]
    total = sum(float(s.get(dur_key, 0)) for s in shots)
    print(f"  时长字段 `{dur_key}`，合计 {total:.3f} s（目标 1800.000）")
    check(abs(total - 1800.0) < 0.01, f"{tag} 轨时长合计 {total} ≠ 1800.0")
    over = [s[num_key] for s in shots if float(s.get(dur_key, 0)) > 15.0 + 1e-6]
    print(f"  单镜 >15s 的条目：{len(over)}{'（' + str(over[:6]) + '）' if over else ''}")
    check(not over, f"{tag} 轨存在超 15s 镜头：{over[:6]}")
    print(f"  帧相关字段：{frame_keys}")

    # 子镜（子分镜）
    sub_keys = [s for s in shots[0] if any(t in s.lower() for t in ("sub", "keyframe", "frame_plan"))]
    print(f"  子镜相关字段：{sub_keys}")
    sub_total = 0
    for s in shots:
        for k in sub_keys:
            v = s.get(k)
            if isinstance(v, list):
                sub_total += len(v)
                break
    print(f"  子镜条目合计 = {sub_total}（README/04 声明 540 / 600）")

    # 图片引用
    ref_key = next((k for k in shots[0] if k.startswith("primary") and "id" in k), None)
    ref_name_key = next((k for k in shots[0] if k.startswith("primary") and ("filename" in k or "path" in k)), None)
    print(f"  主母带字段：{ref_key} / {ref_name_key}")
    miss_id, miss_name, mismatch = [], [], []
    refs = Counter()
    for s in shots:
        fid_ = s.get(ref_key, "") if ref_key else ""
        fname_ = s.get(ref_name_key, "") if ref_name_key else ""
        if fid_ and fid_ not in assets_by_id:
            miss_id.append((s[num_key], fid_))
        if fname_:
            base = Path(fname_).name
            if base not in assets:
                miss_name.append((s[num_key], base))
            elif fid_ and assets[base] != fid_:
                mismatch.append((s[num_key], base))
            refs[base] += 1
    print(f"  引用母带：{sum(refs.values())} 处 / 涉及 {len(refs)} 张；未命中 ID {len(miss_id)}，未命中文件名 {len(miss_name)}，名称-ID 错配 {len(mismatch)}")
    check(not miss_id, f"{tag} 轨有 {len(miss_id)} 处图片 ID 不存在：{miss_id[:3]}")
    check(not miss_name, f"{tag} 轨有 {len(miss_name)} 处文件名不在母带库：{miss_name[:3]}")
    check(not mismatch, f"{tag} 轨有 {len(mismatch)} 处 名称↔ID 错配：{mismatch[:3]}")

    # 提示词层
    pos_key = next((k for k in shots[0] if k in ("prompt", "manus_prompt", "positive_prompt", "prompt_cn")), None)
    neg_key = next((k for k in shots[0] if "negative" in k), None)
    en_key = next((k for k in shots[0] if "prompt" in k and "en" in k), None)
    empties = [s[num_key] for s in shots if not str(s.get(pos_key, "")).strip()]
    print(f"  提示词字段：正向 `{pos_key}` 负向 `{neg_key}` 英文 `{en_key}`；正向为空 {len(empties)}")
    check(not empties, f"{tag} 轨 {len(empties)} 镜正向提示词为空")
    if neg_key:
        no_neg = [s[num_key] for s in shots if not str(s.get(neg_key, "")).strip()]
        print(f"  负向提示词为空：{len(no_neg)}")
    ip_words = ("Kitty", "HELLO KITTY", "茶百道", "小樱", "Vintage News", "君の名は", "你的名字")
    hits = Counter()
    for s in shots:
        blob = " ".join(str(s.get(k, "")) for k in (pos_key, en_key) if k)
        for w in ip_words:
            if w in blob:
                hits[w] += 1
    print(f"  正向提示词残留第三方 IP 词：{dict(hits) if hits else '无'}")
    check(not hits, f"{tag} 轨正向提示词仍含 IP 词：{dict(hits)}")

    # 台词 / VO
    vo_keys = [k for k in shots[0] if any(t in k.lower() for t in ("vo", "line", "dialog", "subtitle"))]
    print(f"  台词/字幕字段：{vo_keys}")
    for k in vo_keys:
        vals = [s for s in shots if str(s.get(k, "")).strip()]
        print(f"    {k}: 非空 {len(vals)}/{len(shots)}")
    print()

print("=" * 78)
print(f"B 段问题合计：{len(problems)}")
for i, p in enumerate(problems, 1):
    print(f"  {i}. {p}")
