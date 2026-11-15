#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按功能归类目录：日期目录拆掉，知识库整体迁入 04-知识底座，并修复引用。

只做移动与路径引用改写，不改正文内容。
"""
import csv
import os
import re
import shutil
from pathlib import Path

ROOT = Path("/Users/longyi/project/账号对标")

# 目录级规则：旧前缀 -> 新前缀
RULES = [
    ("2026-11-13/demand-signal/", "02-调研与对标/demand-signal/"),
    ("2026-11-13/douyin-benchmark/", "02-调研与对标/douyin-benchmark/"),
    ("2026-11-13/fast-growth-cases/", "02-调研与对标/fast-growth-cases/"),
    ("2026-11-13/format-samples/", "02-调研与对标/format-samples/"),
    ("2026-11-13/handoff-audit/", "02-调研与对标/handoff-audit/"),
    ("2026-11-13/roadmap/", "99-归档/roadmap/"),
    ("2026-11-13/see-and-sell/", "00-战略与目标/see-and-sell/"),
    ("2026-11-13/track-positioning/", "00-战略与目标/track-positioning/"),
    ("2026-11-14/benchmark-menu/", "02-调研与对标/benchmark-menu/"),
    ("2026-11-14/control-plan/", "03-决策与复盘/control-plan/"),
    ("2026-11-14/decision-log/", "03-决策与复盘/decision-log/"),
    ("2026-11-14/material-audit/", "02-调研与对标/material-audit/"),
    ("2026-11-14/packaging-check/", "02-调研与对标/packaging-check/"),
    ("2026-11-14/plan-30d/", "00-战略与目标/plan-30d/"),
    ("2026-11-14/strategy/", "00-战略与目标/strategy/"),
    ("2026-11-14/translation-benchmark/", "02-调研与对标/translation-benchmark/"),
    ("2026-11-14/viral-video-types/", "02-调研与对标/viral-video-types/"),
    ("2026-11-14/tool-stack/outputs/01-tool-stack.md", "02-调研与对标/tool-stack/01-tool-stack.md"),
    ("2026-11-14/tool-stack/outputs/02-checklist.md", "01-执行包/02-checklist.md"),
    ("2026-11-14/business-loop/outputs/01-business-loop.md", "00-战略与目标/business-loop/outputs/01-business-loop.md"),
    ("2026-11-14/business-loop/outputs/02-price-sheet.xlsx", "01-执行包/02-price-sheet.xlsx"),
    ("2026-11-14/business-loop/outputs/03-xianyu-199.md", "01-执行包/03-xianyu-199.md"),
    ("2026-11-14/business-loop/work/", "00-战略与目标/business-loop/work/"),
    ("2026-11-14/scripts-v1/outputs/02-video1-final.md", "01-执行包/02-video1-final.md"),
    ("2026-11-14/scripts-v1/outputs/03-zhihu-rewrite.md", "01-执行包/03-zhihu-rewrite.md"),
    ("2026-11-14/scripts-v1/outputs/04-shoot-list.md", "01-执行包/04-shoot-list.md"),
    ("2026-11-14/scripts-v1/outputs/", "99-归档/scripts-v1/"),
    ("2026-11-14/knowledge-graph/README.md", "04-知识底座/图谱/README.md"),
    ("2026-11-14/knowledge-graph/outputs/", "04-知识底座/图谱/"),
    ("2026-11-14/knowledge-graph/work/", "04-知识底座/图谱/work/"),
    ("knowledge/", "04-知识底座/knowledge/"),
    (".trae-html-share-packages/", "99-归档/旧分享包/"),
    # 原始素材单独归入 05
    ("2026-11-13/douyin-benchmark/work/screenshots/", "05-素材与附件/抖音页面截图/"),
    ("2026-11-14/material-audit/work/raw-scan.txt", "05-素材与附件/扫描日志/raw-scan.txt"),
    ("2026-11-14/material-audit/work/anomaly-grep.txt", "05-素材与附件/扫描日志/anomaly-grep.txt"),
]

KEEP_AT_ROOT = {"AGENTS.md"}


def map_path(rel: str):
    for old, new in RULES:
        if rel.startswith(old):
            return new + rel[len(old):]
    return None


def walk_files():
    out = []
    for p in ROOT.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith("work/") or rel.startswith(".") and rel.split("/")[0] in (".git",):
            continue
        out.append(rel)
    return sorted(out)


def main():
    files = [f for f in walk_files() if not f.startswith("work/") and f != ".DS_Store"]
    file_map = {}
    unclassified = []
    for rel in files:
        new = map_path(rel)
        if new is None:
            if rel in KEEP_AT_ROOT:
                continue
            if rel == ".screenshots/.tmp":
                new = "99-归档/空目录/.screenshots/.tmp"
            elif rel == "AGENTS.md":
                continue
            else:
                unclassified.append(rel)
                continue
        file_map[rel] = new

    # 目录映射（含空目录）
    dir_map = {}
    for p in ROOT.rglob("*"):
        if not p.is_dir():
            continue
        rel = p.relative_to(ROOT).as_posix() + "/"
        if rel.startswith("work/") or rel == "./":
            continue
        new = map_path(rel)
        if new is not None:
            dir_map[rel] = new

    # 空目录单独搬：两个 outputs 空壳进 99，保持父目录干净
    empty_moves = {}
    for rel in ("2026-11-14/translation-benchmark/outputs/", "2026-11-13/demand-signal/outputs/"):
        src = ROOT / rel
        if src.is_dir() and not any(src.iterdir()):
            empty_moves[rel] = "99-归档/空目录/" + rel.strip("/").replace("/", "-") + "/"

    # 1) 搬空目录
    for old, new in empty_moves.items():
        dst = ROOT / new
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(ROOT / old), str(dst))
        dir_map.pop(old, None)

    # 2) 搬文件（长的先搬，避免父目录先被移走）
    moved = []
    for rel in sorted(file_map, key=lambda x: -len(x)):
        src = ROOT / rel
        dst = ROOT / file_map[rel]
        if not src.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        moved.append(rel)

    # 3) 清理空掉的原目录
    removed_dirs = []
    for p in sorted([x for x in ROOT.rglob("*") if x.is_dir()], key=lambda x: -len(str(x))):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith("work") or rel.startswith("04-知识底座") or rel.startswith("99-归档"):
            continue
        if p.exists() and not any(p.iterdir()):
            p.rmdir()
            removed_dirs.append(rel)

    print("moved files:", len(moved))
    print("unclassified:", unclassified)
    print("empty dirs moved:", empty_moves)
    print("pruned dirs:", removed_dirs)

    # 4) 修引用
    report = fix_refs(file_map, dir_map)

    # 5) 映射表
    write_mapping(file_map, moved, report, unclassified)


def abs_map(file_map, dir_map, rel_abs: str) -> str:
    """旧项目内绝对（相对仓库根）路径 -> 新路径；找不到返回 None。"""
    if rel_abs in file_map:
        return file_map[rel_abs]
    key = rel_abs.rstrip("/") + "/"
    if key in dir_map:
        return dir_map[key]
    return None


LINK = re.compile(r"(\[[^\]]*\]\()([^)\s]+)(\))")


def relink(md_new: Path, target: str) -> str:
    if target.startswith(("http://", "https://", "mailto:", "#", "tel:")):
        return target
    anchor = ""
    core = target
    if "#" in core:
        core, anchor = core.split("#", 1)
        anchor = "#" + anchor
    if not core:
        return target
    trail = "/" if core.endswith("/") else ""
    old_abs = os.path.normpath(os.path.join(str(md_old_dir(md_new)), core))
    new_abs = abs_map(FILE_MAP, DIR_MAP, Path(old_abs).as_posix())
    if new_abs is None:
        return None
    new_rel = os.path.relpath(str(ROOT / new_abs), str(md_new.parent))
    return new_rel + trail + anchor


FILE_MAP = {}
DIR_MAP = {}


def md_old_dir(md_new: Path) -> str:
    """md 文件的新目录在旧结构里的等价位置，用来解析旧相对链接。"""
    new_rel = md_new.relative_to(ROOT).as_posix()
    for old, new in FILE_MAP.items():
        if new == new_rel:
            return str((ROOT / old).parent)
    return str(md_new.parent)


def fix_refs(file_map, dir_map):
    global FILE_MAP, DIR_MAP
    FILE_MAP, DIR_MAP = file_map, dir_map
    changed, unresolved = [], []

    for old_rel, new_rel in sorted(file_map.items()):
        target = ROOT / new_rel
        if target.suffix.lower() not in (".md", ".html"):
            continue
        try:
            text = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        orig = text

        def sub(m):
            before, tgt, after = m.group(1), m.group(2), m.group(3)
            new_t = relink(target, tgt)
            if new_t is None:
                unresolved.append((new_rel, tgt))
                return m.group(0)
            return before + new_t + after

        text = LINK.sub(sub, text)
        if text != orig:
            target.write_text(text, encoding="utf-8")
            changed.append(new_rel)

    # 手工补：正文里以反引号/纯文本写下的路径
    manual = {
        "00-战略与目标/plan-30d/outputs/01-30day-plan.md": [
            ("`2026-11-14/material-audit/`", "`02-调研与对标/material-audit/`"),
            ("`2026-11-14/scripts-v1/`", "`01-执行包/`"),
            ("`2026-11-13/format-samples/`", "`02-调研与对标/format-samples/`"),
            ("`2026-11-14/viral-video-types/`", "`02-调研与对标/viral-video-types/`"),
            ("`2026-11-13/fast-growth-cases/`", "`02-调研与对标/fast-growth-cases/`"),
            ("`2026-11-13/track-positioning/`", "`00-战略与目标/track-positioning/`"),
            ("`2026-11-13/handoff-audit/`", "`02-调研与对标/handoff-audit/`"),
            ("`2026-11-13/roadmap/outputs/01-30day-schedule.md`", "`99-归档/roadmap/outputs/01-30day-schedule.md`"),
        ],
        "02-调研与对标/douyin-benchmark/outputs/01-douyin-fde-benchmark.md": [
            ("`work/screenshots/search-gate.png`", "`05-素材与附件/抖音页面截图/search-gate.png`"),
            ("`work/screenshots/douyin-app2.png`", "`05-素材与附件/抖音页面截图/douyin-app2.png`"),
            ("截图在 `work/screenshots/`", "截图在 `05-素材与附件/抖音页面截图/`"),
        ],
        "02-调研与对标/material-audit/outputs/01-material-audit.md": [
            ("`../work/raw-scan.txt`", "`../../05-素材与附件/扫描日志/raw-scan.txt`"),
            ("`../work/anomaly-grep.txt`", "`../../05-素材与附件/扫描日志/anomaly-grep.txt`"),
        ],
        "00-战略与目标/business-loop/outputs/01-business-loop.md": [
            ("`02-price-sheet.xlsx`", "`01-执行包/02-price-sheet.xlsx`"),
        ],
        "04-知识底座/图谱/决策使用记录.md": [
            ("`2026-11-14/scripts-v1/outputs/02-video1-final.md`", "`01-执行包/02-video1-final.md`"),
            ("`2026-11-14/plan-30d/outputs/01-30day-plan.md`", "`00-战略与目标/plan-30d/outputs/01-30day-plan.md`"),
        ],
        "04-知识底座/图谱/README.md": [
            ("看图：`outputs/index.html`", "看图：`index.html`"),
            ("数据：`outputs/graph.json`", "数据：`graph.json`"),
            ("决策记录：`outputs/决策使用记录.md`", "决策记录：`决策使用记录.md`"),
            ("cd 2026-11-14/knowledge-graph/work", "cd 04-知识底座/图谱/work"),
            (
                "knowledge-graph/\n"
                "├── README.md                 # 本文件\n"
                "├── outputs/\n"
                "│   ├── graph.json            # 机器可读：节点、边、层级统计、元信息\n"
                "│   ├── index.html            # 单文件网页：图谱数据已内嵌\n"
                "│   └── 决策使用记录.md        # 用图谱做决定的记录（六类决策、三档判定）\n"
                "└── work/",
                "图谱/\n"
                "├── README.md                 # 本文件\n"
                "├── graph.json                # 机器可读：节点、边、层级统计、元信息\n"
                "├── index.html                # 单文件网页：图谱数据已内嵌\n"
                "├── 决策使用记录.md            # 用图谱做决定的记录（六类决策、三档判定）\n"
                "└── work/",
            ),
            ("`outputs/` 是产物，可以随时删掉重建", "`graph.json` / `index.html` 是产物，可以随时删掉重建"),
            ("`outputs/决策使用记录.md` 是图谱的使用台账", "`决策使用记录.md` 是图谱的使用台账"),
            ("相对路径 `../../../knowledge/...`", "相对路径 `../knowledge/...`"),
        ],
    }
    manual_changed = []
    for rel, pairs in manual.items():
        p = ROOT / rel
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        o = t
        for a, b in pairs:
            t = t.replace(a, b)
        if t != o:
            p.write_text(t, encoding="utf-8")
            manual_changed.append(rel)

    print("links fixed in md/html:", len(changed))
    print("manual path fixes:", manual_changed)
    print("unresolved links:", len(unresolved))
    for u in unresolved[:30]:
        print("  ", u)
    return {"changed": set(changed) | set(manual_changed), "unresolved": unresolved}


def category_of(rel: str) -> str:
    if rel.startswith("00-战略与目标/"):
        return "00-战略与目标"
    if rel.startswith("01-执行包/"):
        return "01-执行包"
    if rel.startswith("02-调研与对标/"):
        return "02-调研与对标"
    if rel.startswith("03-决策与复盘/"):
        return "03-决策与复盘"
    if rel.startswith("04-知识底座/"):
        return "04-知识底座"
    if rel.startswith("05-素材与附件/"):
        return "05-素材与附件"
    if rel.startswith("99-归档/"):
        return "99-归档"
    return "根目录"


def write_mapping(file_map, moved, report, unclassified):
    path = ROOT / "_映射表.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["原路径", "新路径", "所属分类", "是否已修引用", "备注"])
        for old in sorted(file_map):
            new = file_map[old]
            if new in report["changed"]:
                fix = "是"
            elif new.endswith((".md", ".html", ".py", ".csv", ".json")):
                fix = "无需（无跨目录引用）"
            else:
                fix = "无需"
            note = ""
            if new.startswith("99-归档/scripts-v1/03-video2-3-drafts.md"):
                note = "待定：第二三条初稿，尚未定稿"
            if new.startswith("99-归档/旧分享包"):
                note = "待定：知识图谱网页的导出 zip，与 04 的 index.html 重复"
            if new.startswith("99-归档/roadmap/"):
                note = "被 00-战略与目标/plan-30d 替代"
            if old in moved and not (ROOT / new).exists():
                fix = "否（文件缺失）"
            w.writerow([old, new, category_of(new), fix, note])
        for rel in unclassified:
            w.writerow([rel, "（未归类）", "未归类", "否", "脚本未匹配规则，需人工判断"])
    print("mapping rows:", len(file_map) + len(unclassified))


if __name__ == "__main__":
    main()
