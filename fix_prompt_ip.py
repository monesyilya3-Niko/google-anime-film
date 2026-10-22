# -*- coding: utf-8 -*-
"""
Phase 2 · 180/120 提示词层 IP 残留替换（默认 dry-run，--apply 才写本地文件）

只改 prompt_zh / prompt_en / motion_zh / motion_en 四个字段；
严禁碰文件名引用、日语/中文台词（「…」内）、ID/指令字段。

道具口径（--bookmark 控制）：
  --bookmark=05   默认：统一为 05 台账'带流苏木制书签（尾端黄铜色彗星挂坠）'，
                  同时替换 6/5 处星之杖残留与 20/15 处'粉金星翼彗星书签挂坠'，
                  以及英文 Cardcaptor/pink-and-gold/star-comet 短语。
  --bookmark=keep 保留现有'粉金星翼彗星书签挂坠'造型，仅把星之杖残留
                  改成'粉金星翼彗星书签挂坠'；此时须改 05 重画提示词以对齐母带。

输出（--apply 时）：
  fixed/180Shots_V19_prompt_ip.json
  fixed/120Shots_V19_prompt_ip.json
本脚本不负责上传；执行后须人工复核 dry-run 报告，再决定上传。
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "source" / "audit"
FIXED = ROOT / "fixed"
REPORT = ROOT / "prompt_ip_dryrun_report.txt"

FILES = {
    "180": CACHE / "暮冬念春_Manus(单镜≤15s双轨)_180镜540子镜24fps关键帧清单_180Shots_V19.json",
    "120": CACHE / "暮冬念春_Manus(单镜15s满格)_120镜600子镜360帧全同步清单_120Shots_V19.json",
}
OUTPUTS = {
    "180": FIXED / "180Shots_V19_prompt_ip.json",
    "120": FIXED / "120Shots_V19_prompt_ip.json",
}
ALLOWED_FIELDS = ("prompt_zh", "prompt_en", "motion_zh", "motion_en")

# 文件名（.jpg/.png 片段）与台词（「…」内）保护
FILENAME_RE = re.compile(r"[^\s，。；、（）()【】\[\]]*\.(?:jpg|jpeg|png)")
DIALOGUE_RE = re.compile(r"「[^」]*」")


def build_mappings(bookmark_mode: str):
    """返回有序替换表：每条 (名称, 旧词, 新词)，按旧词长度降序执行。"""
    zh = [
        # —— 桌面书签（星之杖替代物）——
        # “金翼摇曳”整句先改，避免替换后出现“木书签的金翼”病句
        ("bookmark_zh", "粉金星翼彗星挂坠的金翼在微风中轻轻摇曳", "带流苏木制书签的流苏在微风中轻轻摇曳"),
        ("bookmark_zh", "粉金星翼彗星书签挂坠", "带流苏的木制书签（尾端黄铜色彗星挂坠）"),
        ("bookmark_zh", "粉金星翼彗星挂坠", "带流苏的木制书签（尾端黄铜色彗星挂坠）"),
        ("bookmark_zh", "粉金星翼彗星", "带流苏木制书签"),
        ("bookmark_zh", "小樱粉色星之杖", "带流苏的木制书签（尾端黄铜色彗星挂坠）"),
        # —— 相机白猫吊坠 → 黄铜色小彗星吊坠 ——
        ("whitecat_zh", "相机白猫吊坠", "相机上的黄铜色小彗星吊坠"),
        ("whitecat_zh", "带白色小猫吊坠", "带黄铜色小彗星吊坠"),
        ("whitecat_zh", "白色小猫吊坠", "黄铜色小彗星吊坠"),
        ("whitecat_zh", "带白猫吊坠", "带黄铜色小彗星吊坠"),
        ("whitecat_zh", "白猫吊坠", "黄铜色小彗星吊坠"),
        ("whitecat_zh", "小猫吊坠", "黄铜色小彗星吊坠"),
        # —— 奶茶杯品牌视觉（字面茶百道不在此列）——
        ("cup_zh", "蓝白熊猫标志杯身", "米白杯身"),
        ("cup_zh", "蓝白熊猫标志", "无字纯色"),
        ("cup_zh", "蓝白熊猫杯", "无字纯色奶茶杯"),
        ("cup_zh", "熊猫标志杯身", "米白杯身"),
        ("cup_zh", "熊猫保温杯套", "纯色保温杯套"),
        ("cup_zh", "熊猫保温套", "纯色保温套"),
        ("cup_zh", "熊猫套奶茶杯", "纯色杯套奶茶杯"),
        # 两处既有重复/病句顺手收敛（长词优先，先于通用“熊猫保温套”）
        ("cup_zh", "套着立体熊猫保温套、带立体熊猫保温套的手作热奶茶", "套着立体纯色保温套的手作热奶茶"),
        ("cup_zh", "立体熊猫保温杯套上的熊猫保温套杯身", "立体纯色保温杯套与米白杯身"),
        ("cup_zh", "手作蓝白熊猫杯温热奶茶", "手作温热奶茶"),  # 原句重复“手作…杯”的既有笔误
        ("cup_zh", "熊猫杯奶茶", "纯色奶茶杯"),  # 段落标签用，避免“奶茶杯奶茶”
        ("cup_zh", "熊猫杯", "无字纯色奶茶杯"),
        ("cup_zh", "熊猫标志", "无字纯色"),
    ]
    en = [
        # —— 桌面书签 ——
        ("bookmark_en", "Cardcaptor Sakura golden-winged pink winged star-comet charm",
         "wooden bookmark with a tassel ending in a small brass comet-shaped pendant"),
        ("bookmark_en", "Cardcaptor Sakura pink winged star-comet charm",
         "wooden bookmark with a tassel ending in a small brass comet-shaped pendant"),
        ("bookmark_en", "pink-and-gold winged star-comet charm",
         "wooden bookmark with a tassel ending in a small brass comet-shaped pendant"),
        ("bookmark_en", "winged star-comet charm",
         "wooden bookmark with a tassel ending in a small brass comet-shaped pendant"),
        # —— 白猫吊坠 ——
        ("whitecat_en", "white-cat-charm", "brass-comet-charm"),
        ("whitecat_en", "white cat charm", "brass comet charm"),
        # —— 奶茶杯品牌视觉（负向句先改，避免把 negative 改成病句）——
        ("cup_en", "no brand text on milk tea cup above panda logo", "no brand text on milk tea cup"),
        ("cup_en", "ChaPanda panda milk tea cups", "plain solid-color milk tea cups"),
        ("cup_en", "ChaPanda panda milk tea cup", "plain solid-color milk tea cup"),
        ("cup_en", "ChaPanda panda cup", "plain solid-color milk tea cup"),
        ("cup_en", "ChaPanda Soy Milk Mochi Cups", "Plain Soy Milk Mochi Cups"),
        ("cup_en", "ChaPanda Milk Tea", "Plain Milk Tea"),
        ("cup_en", "ChaPanda milk tea", "plain milk tea"),
        ("cup_en", "panda-cup 'Soy Milk Mochi' hot milk tea cup", "plain solid-color 'Soy Milk Mochi' hot milk tea cup"),
        ("cup_en", "panda-sleeved milk tea cup", "plain solid-color milk tea cup"),
        ("cup_en", "two panda-cup 'Soy Milk Mochi' panda-logo cups", "two plain solid-color 'Soy Milk Mochi' cups"),
        ("cup_en", "panda-logo cups", "plain solid-color cups"),
        ("cup_en", "panda-logo cup", "plain solid-color cup"),
        ("cup_en", "panda-logo milk tea cup", "plain solid-color milk tea cup"),
        ("cup_en", "panda-logo milk tea", "plain solid-color milk tea"),
        ("cup_en", "blue-and-white panda logo cup", "off-white cup body"),
        ("cup_en", "panda-cup 'Soy Milk Mochi' milk tea cup", "plain solid-color 'Soy Milk Mochi' milk tea cup"),
        ("cup_en", "panda-cup 'Soy Milk Mochi' panda-logo milk tea", "plain solid-color 'Soy Milk Mochi' milk tea"),
        ("cup_en", "panda-cup 'Soy Milk Mochi' milk tea", "plain solid-color 'Soy Milk Mochi' milk tea"),
        ("cup_en", "3D panda thermal sleeve", "3D plain thermal sleeve"),
        ("cup_en", "3D panda sleeve", "3D plain thermal sleeve"),
        ("cup_en", "panda thermal sleeve", "plain thermal sleeve"),
        ("cup_en", "panda sleeve", "plain sleeve"),
        ("cup_en", "warm panda cup", "warm milk tea cup"),
        ("cup_en", "panda logo", "plain solid-color"),
        ("cup_en", "panda-cup", "plain solid-color cup"),
        ("cup_en", "panda cup", "plain cup"),
        # —— Kitty 镜（仅视觉；文件名 Kitty镜 不含空格，不会命中）——
        ("kitty_en", "pink Kitty mirror", "pink-rimmed plain silver mirror"),
        ("kitty_en", "pink Kitty Mirror", "pink-rimmed Plain Silver Mirror"),
        ("kitty_en", "Kitty Mirror Lock", "Plain Silver Mirror Lock"),
        ("kitty_en", "Kitty mirror", "plain silver mirror"),
        ("kitty_en", "Kitty Mirror", "Plain Silver Mirror"),
    ]
    if bookmark_mode == "keep":
        # 保留粉金星翼造型：不替换既有粉金星翼表达，只把星之杖/Cardcaptor 残留改回既有原创表达
        zh = [
            (n, o, t)
            for n, o, t in zh
            if not (n == "bookmark_zh" and o.startswith("粉金星翼"))
        ]
        zh = [
            (n, o, "粉金星翼彗星书签挂坠" if o == "小樱粉色星之杖" else t)
            for n, o, t in zh
        ]
        en = [
            (n, o, t)
            for n, o, t in en
            if not (n == "bookmark_en" and o in (
                "Cardcaptor Sakura golden-winged pink winged star-comet charm",
                "Cardcaptor Sakura pink winged star-comet charm",
                "pink-and-gold winged star-comet charm",
                "winged star-comet charm",
            ))
        ]
        en += [
            ("bookmark_en", "Cardcaptor Sakura golden-winged pink winged star-comet charm",
             "pink-and-gold winged star-comet charm"),
            ("bookmark_en", "Cardcaptor Sakura pink winged star-comet charm",
             "pink-and-gold winged star-comet charm"),
        ]
    # 按旧词长度降序，长词优先，避免子串先被替换
    mappings = [(n, o, t) for n, o, t in zh + en]
    mappings.sort(key=lambda x: len(x[1]), reverse=True)
    return mappings


def mask(text: str):
    """把文件名与「台词」替换为占位符，返回 (掩码文本, 恢复表)。"""
    store = []

    def _sub(m):
        store.append(m.group(0))
        return f"\x00{len(store) - 1}\x00"

    masked = FILENAME_RE.sub(_sub, text)
    masked = DIALOGUE_RE.sub(_sub, masked)
    return masked, store


def unmask(text: str, store):
    for i, original in enumerate(store):
        text = text.replace(f"\x00{i}\x00", original)
    return text


def apply_field(text: str, mappings, counter: Counter):
    masked, store = mask(text)
    for name, old, new in mappings:
        if old in masked:
            counter[name] += masked.count(old)
            masked = masked.replace(old, new)
    result = unmask(masked, store)
    # 硬校验：每个被保护的文件名/台词段必须原样保留
    for seg in store:
        if seg not in result:
            raise AssertionError(f"保护段丢失：{seg[:80]!r}")
    return result


def dumps_crlf(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=1).replace("\n", "\r\n").encode("utf-8")


LEFTOVER_TERMS = (
    "小樱粉色星之杖", "粉金星翼", "白猫吊坠", "小猫吊坠", "Cardcaptor Sakura",
    "white cat charm", "white-cat-charm", "Kitty mirror", "Kitty Mirror", "pink Kitty",
    "ChaPanda", "panda", "蓝白熊猫", "熊猫杯", "熊猫标志", "熊猫保温",
)


def main():
    ap = argparse.ArgumentParser(description="Phase 2 提示词 IP 残留替换（默认 dry-run）")
    ap.add_argument("--apply", action="store_true", help="写本地 fixed/*.json（不上传）")
    ap.add_argument("--bookmark", choices=("05", "keep"), default="05",
                    help="05=统一为木制书签（默认）；keep=保留粉金星翼造型")
    args = ap.parse_args()

    mappings = build_mappings(args.bookmark)
    report = [f"Phase 2 提示词 IP 替换 · bookmark={args.bookmark} · apply={args.apply}", ""]
    for tag, path in FILES.items():
        raw = path.read_bytes()
        shots = json.loads(raw.decode("utf-8"))
        original_shots = copy.deepcopy(shots)
        if dumps_crlf(shots) != raw:
            raise SystemExit(f"[{tag}] 序列化往返不一致，拒绝继续（格式假设失败）")

        counter: Counter = Counter()
        changed_fields = []
        for s in shots:
            label = s.get("shot_id") or s.get("manus_15s_id")
            for k in ALLOWED_FIELDS:
                old = s.get(k)
                if not isinstance(old, str) or not old:
                    continue
                new = apply_field(old, mappings, counter)
                if new != old:
                    s[k] = new
                    changed_fields.append((label, k, old, new))

        report.append("=" * 88)
        report.append(f"{tag} 轨 · 替换统计（{len(changed_fields)} 个字段被修改）")
        report.append("=" * 88)
        for name, n in sorted(counter.items()):
            report.append(f"  {name}: {n} 处")
        report.append("")
        report.append("  前 6 个修改字段的抽样（改前 → 改后）：")
        for label, k, old, new in changed_fields[:6]:
            for name, o, t in mappings:
                if o in old:
                    i = old.find(o)
                    report.append(f"    [{label}.{k}] …{old[max(0, i - 60):i + 80]}…")
                    j = new.find(t[:20])
                    report.append(f"      → …{new[max(0, j - 60):j + 100]}…")
                    break
        report.append("")

        # 改后复核：只允许四个 prompt/motion 字段变化（逐镜逐键对比原始对象）
        illegal = []
        for orig, new in zip(original_shots, shots):
            for k in set(orig) | set(new):
                if orig.get(k) != new.get(k) and k not in ALLOWED_FIELDS:
                    illegal.append((orig.get("shot_id") or orig.get("manus_15s_id"), k))
        if illegal:
            raise SystemExit(f"[{tag}] 非法字段被修改，拒绝继续：{illegal[:5]}")
        report.append(f"  字段边界复核：仅 {len(ALLOWED_FIELDS)} 个 prompt/motion 字段可变化 ✔")

        # 变更字段清单（完整可追溯）
        report.append("  变更字段清单（镜号.字段）：")
        names = [f"{label}.{k}" for label, k, _, _ in changed_fields]
        for i in range(0, len(names), 8):
            report.append("    " + "  ".join(names[i:i + 8]))
        report.append("")

        # 残留检查（排除文件名/台词保护段）
        report.append(f"  {tag} 轨残留检查（文件名与「台词」已排除）：")
        leftover_terms = tuple(
            t for t in LEFTOVER_TERMS
            if not (args.bookmark == "keep" and t == "粉金星翼")
        )
        leftovers = Counter()
        samples = {}
        for s in shots:
            label = s.get("shot_id") or s.get("manus_15s_id")
            for k in ALLOWED_FIELDS:
                v = s.get(k, "")
                if not isinstance(v, str):
                    continue
                masked, _ = mask(v)
                for term in leftover_terms:
                    c = masked.count(term)
                    if c:
                        leftovers[term] += c
                        samples.setdefault(term, [])
                        if len(samples[term]) < 2:
                            i = masked.find(term)
                            samples[term].append(f"[{label}.{k}] …{masked[max(0, i-70):i+90]}…")
        if leftovers:
            for term, n in sorted(leftovers.items(), key=lambda x: -x[1]):
                report.append(f"    ⚠ {term}: {n} 处")
                for smp in samples[term]:
                    report.append(f"       {smp}")
        else:
            report.append("    ✔ 无残留")
        report.append("")

        if args.apply:
            FIXED.mkdir(exist_ok=True)
            out = OUTPUTS[tag]
            out.write_bytes(dumps_crlf(shots))
            report.append(f"  已写出：{out} （{out.stat().st_size:,}B）")
        else:
            report.append("  （dry-run，未写文件；确认无误后加 --apply）")
        report.append("")

    REPORT.write_text("\n".join(report), encoding="utf-8")
    print(f"written {REPORT} ({REPORT.stat().st_size}B)")
    print("dry-run 完成。" if not args.apply else "已写出本地修复件（未上传）。")


if __name__ == "__main__":
    main()
