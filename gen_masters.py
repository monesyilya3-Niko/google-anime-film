# -*- coding: utf-8 -*-
"""批量重出《暮冬念春》有问题的 4K 母带。

流程：Gemini 网页版改图 → 下载原图 → 1.4x 放大到 3840×2160 → 存到 gen_out/
规格沿用项目自己的铁律（画幅/色温/构图/锁脸），并按母带逐张给出针对性指令。

用法: python gen_masters.py [批次名]
"""
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
SRC = next(d for d in list(ROOT.iterdir()) + list((ROOT / "source").iterdir())
            if d.is_dir() and d.name.startswith("40"))
OUT = ROOT / "gen_out"
OUT.mkdir(exist_ok=True)

STYLE = ("新海诚×京阿尼剧场版画风，4K 24.000fps，16:9 全出血 3840×2160，"
         "18%高光柔和辉光(Bloom)，丁达尔体积光，通透细腻的皮肤质感，"
         "高对比电影级调色")
NO_TEXT = "画面内严禁出现任何文字、字母、汉字、数字、标语、logo、品牌标识、水印、字幕、招牌字样"

# 母带前缀 -> (修复指令, 输出名后缀)
JOBS = {
    "02_": ("【角色锁脸基准图】把人物改成中性半身正面肖像：女主角的脸、五官比例、"
            "发型、眼型、肤色必须与原图完全一致，不许重新设计五官；"
            "去掉粉色毛绒外套和白色围巾，改成纯白衬衫（领口敞开一颗扣）+ 极简深灰领结；"
            "肩线以上入画，纯净中性冷灰背景，不要任何环境物件与道具；"
            "保留原图柔三点布光与通透皮肤质感；" + STYLE + "；" + NO_TEXT,
            "02_图2.1_女主角雨绪偏DBX_真人锁脸唯一颜值基准与第219帧_3840x2160_4K"),
    "10_": ("【私人放映室】只改两处，其余一律保持原图不变："
            "①银幕上原本的日文片名换成两枚原创汉字『暮冬』，字形端正、"
            "白色宋体 Light、字距宽、像影院字幕，不要日文假名；"
            "②男主 T 恤上的英文单词『Vintage News』彻底抹掉，改成纯色米白 T 恤，"
            "保留领口罗纹与版型；"
            "深红丝绒座椅、双色彗星投在幕布上的光影、女主手中的粉色相机与猫挂件全部保持原样；"
            + STYLE + "；除『暮冬』二字外，" + NO_TEXT,
            "10_图3.7a_Scene07_私人放映室同看你的名字双色彗星_3840x2160_4K"),
    "07_": ("【Scene04 高三同桌】只改一处，其余一律保持原图不变："
            "男女主手里举着的笔记本，封面和内页上原本的英文字母代号全部抹掉，"
            "改成素色笔记本封面 + 无法辨识的手写笔迹痕迹（不可读出任何字符）；"
            "教室黑板、窗外樱花、桌面文具、两人的姿态与表情、光影色调全部保持原样；"
            + STYLE + "；" + NO_TEXT,
            "07_图3.4_Scene04_4月1日高三同桌竖起DBX与YXP笔记本_3840x2160_4K"),
    "27_": ("【Scene22 次年早春融雪窗边】只改一处，其余一律保持原图不变："
            "两人掌心交叠处原本写着的英文字母全部抹掉，改成两人各用一根手指"
            "在对方掌心划出一道浅痕，不出现任何字符；"
            "窗外融雪、窗框、两人的侧脸与泪光、衣服、光影全部保持原样；"
            + STYLE + "；" + NO_TEXT,
            "27_图3.22_Scene22_次年早春融雪窗边左手托左掌写下DBX与YXP_3840x2160_4K"),
}


def upscale_to_4k(src_png, dst_jpg, W=3840, H=2160, q=95):
    from PIL import Image, ImageFilter
    im = Image.open(src_png).convert("RGB")
    w, h = im.size
    if abs(w / h - 16 / 9) > 0.02:
        # 比例不对就按中心裁成 16:9 再放大
        tw = int(h * 16 / 9)
        if tw <= w:
            x0 = (w - tw) // 2
            im = im.crop((x0, 0, x0 + tw, h))
        else:
            th = int(w * 9 / 16)
            y0 = (h - th) // 2
            im = im.crop((0, y0, w, y0 + th))
    up = im.resize((W, H), Image.LANCZOS)
    up = up.filter(ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=3))
    up.save(dst_jpg, quality=q, subsampling=0, optimize=True)
    return dst_jpg


def main():
    batch = sys.argv[1] if len(sys.argv) > 1 else "all"
    jobs = [(k, v) for k, v in JOBS.items() if batch == "all" or k.startswith(batch)]
    for pref, (instr, outname) in jobs:
        src = next((p for p in sorted(SRC.glob(pref + "*.jpg"))), None)
        if not src:
            print(f"SKIP {pref} (找不到源图)")
            continue
        tmp = ROOT / "gen_out" / ("_tmp_" + pref)
        tmp.mkdir(parents=True, exist_ok=True)
        print(f"\n=== {src.name} ===", flush=True)
        r = subprocess.run(
            ["node", str(ROOT / "gemini_driver.mjs"), str(src), instr, str(tmp), "280"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(r.stdout.strip()[-600:])
        outs = [p for p in tmp.glob("gemini_out.*")]
        if not outs:
            print("  !! 没出图")
            continue
        dst = OUT / (outname + ".jpg")
        upscale_to_4k(outs[0], dst)
        from PIL import Image
        print(f"  ✓ {dst.name}  {Image.open(dst).size}  {dst.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
