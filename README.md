# 《暮冬念春》动漫 V19 · 本地工程目录

云端是唯一事实源（`nikoaa666666@gmail.com` → 《暮冬念春（暮冬の雪、春雨を想う）》30分钟电影集 · 4K原画母带与180镜全案工程总库）。
本仓库是动漫单项目独立仓库；本地路径 `Documents/Studio/anime-mudong`，远端 `google-anime-film`。
本目录只保留 **V19 唯一有效方案**：工具脚本、交付文档、V19 审计快照与 23 张待重画资产。云端仍是唯一事实源；V17/V18 只作为图片工作资产，不作为方案版本。

> 2026-10-22 清理：已删除本地 V17 计划文档（`v17/`）、V17 Act 分册（`v17_out/`）、旧 05a/05b 候选图（`fixed_assets/`）、V16 结构化 JSON 与临时产物。当前只保留 **V19** 工程；云端 V17 目录仅存图片工作资产，不再是方案版本。V16/V17 历史脚本（`audit_v16.py` / `fix_v16.py` / `fix_docs.py` / `pull_v16.py` / `fix_05a05b.py` / `verify_05a05b.py`）未迁入本仓库。

## 云端结构（当前）

```
《暮冬念春…》30分钟电影集 · 4K原画母带与180镜全案工程总库 (V19七维铁律死锁终极精修版)   ← 根目录
├── 40幅真4K超清主母带与单屏子母带 (assets_4k_all)      40 张 4K 母带
├── V19_院线电影级全帧540子镜终极精修版 (2026-10-21)     ← 当前唯一有效方案版
│   ├── 00–05 支持文档 / Act1–Act7 分幕手册
│   ├── 180Shots_V19.json / 120Shots_V19.json
│   └── 180/120 全量总表 / 总控 / 导演全案
└── V17_深度体检修复版 (2026-10-19)                     ← 仅图片工作资产
    ├── V17_待重画_23张_含原图与提示词 (2026-10-21)
    ├── V18_母带去字精修定稿_12张无涂抹4K版 (2026-10-21)
    └── V17_未完成清单 (2026-10-21)（历史文档，现状以 V19/04 为准）
```

## 本地保留（V19 唯一版）

- `fixed/180Shots_V19_shot007fix.json`：V19 180 镜 Shot_007 修复件（md5 `ab4edeb1…`）
- `docs_fix/02.md` / `04.md`：V19 02/04 修复版
- `source/audit/`：V19 云端审计快照（40 张母带 + V19 文档/JSON）
- `redraw_pack/`：23 张待重画母带原图 + 区域标注（当前唯一待办）

## 工具

| 脚本 | 作用 |
|---|---|
| `detext7.py` | 去字引擎终版：A 整框内容感知填补 / B 局部柔化 / C 柔化+同字体重绘 |
| `detext_qc.py` | 去字质量机器验收（高通能量残留率） |
| `master_issues.py` | 40 张逐张问题 / 屏内文字坐标 / IP 清单（台账数据源） |
| `master_ledger.py` | 生成 `母带台账_40张.md` + `.csv` |
| `recompose_06.py` | 06_ = 06a_ + 06b_ 的重拼（偏移 1924） |
| `promote_fixes.py` | 12 张修好稿原地提升回母带库（File ID 不变，清单零改动） |
| `redraw_prompts.py` / `build_redraw_pack.py` | 23 张重画数据 / 交付包生成器 |
| `scan_all.py` / `zoom_list.py` | 40 张全幅扫描 / 定点高分辨率放大复核 |
| `upload_v17.py` | Drive API 封装（当前复用其 API helper；旧 V17 上传路径已停用） |
| `upload_fixed.py` / `upload_redraw.py` | 上传修好稿+文档 / 上传未完成清单+待重画包 |
| `cloud_clean.py` / `scan_cloud.py` / `final_check.py` | 云端清理 / 全盘扫描 / 结构终检 |
| `gemini_driver.mjs` / `gemini_web.py` | Gemini 网页版 CDP 生图管线（备用生图后端） |
| `oauth_consent.mjs` | CDP 驱动 OAuth 授权页（自动选账号/填邮箱/点同意） |
| `cloud_finish.py` | 授权完成后自动跑云端收尾 |

> V16/V17 历史脚本未迁入；当前工具只服务 V19 与 23 张重画。

## Git 边界与忽略项

本仓库是动漫单项目独立仓库，远端 `google-anime-film`，不包含小说、Vibe 或工作区代码。

以下不入库（本地/云端保留）：

- `source/audit/*.jpg` / `*.jpeg` / `*.png`（40 张 4K 母带）
- `redraw_pack/**/*.jpg` / `*.jpeg` / `*.png`（23 张待重画原图与区域图）
- `gen_out/` / `gen_test/` / `__pycache__/` / `*.pyc`

入库：`source/audit` 的 JSON/MD、`fixed/180Shots_V19_shot007fix.json`、`docs_fix/`、`redraw_pack` 的提示词/清单、V19 文档与脚本。
