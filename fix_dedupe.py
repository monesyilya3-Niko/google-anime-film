# -*- coding: utf-8 -*-
"""定位并去除 prompt 里的整段重复粘贴。

重复形态：同一批「【标签】：内容」子块在同一个字段里被拼了两遍。
两遍之间起点会错开（不是干净的整段复制），所以按连续子串找不到，
必须先把字段切成原子段（。；】· 换行），再在原子层面找"连续重复的一段"。

保证：
  - 只删第二次出现的那一段，第一次保留
  - 删完复核：铁律1-7 / Rule1-7 齐全、File ID 齐全、括号配平
  - 输出可读的前后对照

用法:
  python fix_dedupe.py --dry
  python fix_dedupe.py --apply --out <目录>
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
V16 = next(d for d in ROOT.iterdir() if d.is_dir() and d.name.startswith("《"))

ATOM = re.compile(r'(?<=。)|(?<=；)|(?<=】)|(?<=·)|(?<=\n)')
MIN_ATOM = 18          # 短于此的原子不参与去重（避免误删"严禁出现任何人物"这类有意重复）
MIN_RUN = 2            # 至少连续 2 个原子才算一段重复


def split_atoms(s):
    """深度感知切分：只在【】配对之外的位置切，保证每段括号自平衡。"""
    atoms = []
    buf = []
    depth = 0
    for ch in s:
        buf.append(ch)
        if ch == "【":
            depth += 1
        elif ch == "】":
            depth -= 1
        elif depth <= 0 and ch in "。；·\n":
            atoms.append("".join(buf))
            buf = []
    if buf:
        atoms.append("".join(buf))
    return [a for a in atoms if a]


def balanced(s):
    return s.count("【") == s.count("】")


def dedupe_atoms(s):
    """在原子层面删除重复的连续段。

    规则：被删掉的那一段必须**自身括号自平衡**，否则留着（宁可少删也不把
    【】 拆散）。只删后面那一份，前一份保留。
    """
    atoms = split_atoms(s)
    n = len(atoms)
    removals = []          # (j, k, sample)
    for i in range(n):
        kmax = min(30, n - i)
        for k in range(kmax, MIN_RUN - 1, -1):
            run = atoms[i:i + k]
            if sum(len(a) for a in run) < 60:
                continue
            if any(len(a) < MIN_ATOM for a in run):
                continue
            if not balanced("".join(run)):
                continue
            for j in range(i + k, n - k + 1):
                if atoms[j:j + k] == run:
                    removals.append((j, k, "".join(run)[:100]))
                    break
            else:
                continue
            break
    if not removals:
        return s, 0, ""
    # 从后往前删，索引才不会失效
    removals.sort(key=lambda x: -x[0])
    used = set()
    removed = 0
    sample = ""
    for j, k, sm in removals:
        if any(idx in used for idx in range(j, j + k)):
            continue
        used.update(range(j, j + k))
        del atoms[j:j + k]
        removed += k
        if not sample:
            sample = sm
    new = "".join(atoms)
    return new, removed, sample


FIELDS = ["prompt_zh", "prompt_en", "motion_zh", "motion_en",
          "upload_instruction", "cloud_dispatch_command_zh", "audio_cue",
          "first_frame_source", "end_frame_lock", "auxiliary_cloud_md",
          "manus_mode", "gemini_muse_mode", "first_frame_cloud_filename"]

RULES = ["铁律1", "铁律2", "铁律3", "铁律4", "铁律5", "铁律6", "铁律7"]
RULES_EN = ["Rule 1", "Rule 2", "Rule 3", "Rule 4", "Rule 5", "Rule 6", "Rule 7"]


def process(shots, label, apply, outpath):
    tb = ta = 0
    touched = 0
    kinds = Counter()
    bad = []
    for s in shots:
        before = sum(len(str(s.get(f, "") or "")) for f in FIELDS)
        for f in FIELDS:
            v = s.get(f)
            if not isinstance(v, str) or len(v) < 120:
                continue
            new, removed, sample = dedupe_atoms(v)
            if removed:
                s[f] = new
                kinds[(f, sample[:46])] += 1
        after = sum(len(str(s.get(f, "") or "")) for f in FIELDS)
        tb += before
        ta += after
        if before != after:
            touched += 1
        pz = s.get("prompt_zh", "") or ""
        for r in RULES:
            if r not in pz:
                bad.append((s.get("shot_id", s.get("manus_15s_id")), f"缺{r}"))
        pe = s.get("prompt_en", "") or ""
        for r in RULES_EN:
            if r not in pe:
                bad.append((s.get("shot_id", s.get("manus_15s_id")), f"缺{r}"))
        blob = json.dumps(s, ensure_ascii=False)
        for key in ("primary_drive_file_id", "primary_cloud_filename"):
            if s.get(key) and s[key] not in blob:
                bad.append((s.get("shot_id", s.get("manus_15s_id")), f"丢了 {key}"))
        for f in ("prompt_zh", "prompt_en"):
            if (s.get(f) or "").count("【") != (s.get(f) or "").count("】"):
                bad.append((s.get("shot_id", s.get("manus_15s_id")), f"{f} 括号不配平"))

    print(f"[{label}] {len(shots)} 条 | 改动 {touched} 条 | "
          f"字符 {tb} → {ta} (省 {tb-ta}，{(tb-ta)/max(1,tb)*100:.1f}%)")
    for (f, sm), c in kinds.most_common(8):
        print(f"    ×{c:4d}  [{f}] {sm}")
    if bad:
        print(f"  ⚠ 完整性异常 {len(bad)} 处: {bad[:8]}")
    else:
        print("  ✓ 复核通过：铁律1-7 / Rule1-7 / File ID / 括号配平 全部完好")
    if apply and outpath:
        json.dump(shots, open(outpath, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"  -> {outpath}")
    return tb, ta


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    outdir = None
    if "--out" in sys.argv:
        outdir = Path(sys.argv[sys.argv.index("--out") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
    for pat, label in (("*180Shots.json", "180镜"), ("*120Shots.json", "120镜")):
        p = next(V16.glob(pat))
        shots = json.load(open(p, encoding="utf-8"))
        out = outdir / p.name if outdir else None
        process(shots, label, apply, out)
        print()
