#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 experience.csv 增加「对应子项」列，并按大类统计经验门槛。

用法：
  python3 04-知识底座/experience/add_subitem.py          # 写入列（保留原文件备份）
  python3 04-知识底座/experience/add_subitem.py --stats  # 只统计，不写文件

对应子项的判定口径：按该条经验的结论内容，挂到 catalog.csv 里最贴的细类；
一条经验最多挂 3 个细类，多个用中文顿号分隔。行业口径类（industry-lore.csv）
的证据等级 E0 永久不参与统计。
"""
import csv
import shutil
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
CATALOG = BASE / "catalog" / "catalog.csv"
EXP = HERE / "experience.csv"

# 编号 -> 对应子项（细类名，顿号分隔）
MAP = {
    "D1-01": "推荐机制、钩子与注意力",
    "D1-02": "转化路径与漏斗设计、选题与需求信号",
    "D1-03": "投放与ROI",
    "D1-04": "投放与ROI",
    "D1-05": "冷启动与账号权重",
    "D1-06": "经营核算与现金流",
    "D2-01": "合同与回款",
    "D2-02": "合同与回款、交付与验收",
    "D2-03": "合同与回款",
    "D2-04": "合同与回款",
    "D2-05": "定价与报价",
    "D2-06": "销售与谈判、合同与回款",
    "D3-01": "交付与验收、合同与回款",
    "D3-02": "合同与回款",
    "D3-03": "合同与回款、外包与产能",
    "D3-04": "外包与产能",
    "D4-01": "AI模型能力与成本边界（只收实时源）、定价与报价",
    "D4-02": "FDE技术图谱",
    "D4-03": "需求识别与JTBD",
    "D5-01": "剪辑节奏与声音",
    "D5-02": "口播与语言表达",
    "D5-03": "剪辑节奏与声音",
    "D5-04": "视听语言与镜头",
    "D6-01": "冷启动与账号权重",
    "D6-02": "转化路径与漏斗设计",
    "D6-03": "定位与差异化",
    "D7-01": "工具生态与成本",
    "D7-02": "工具生态与成本",
    "D7-03": "工具生态与成本",
    "D8-01": "定价与报价",
    "D8-02": "定价与报价",
    "D8-03": "定价与报价",
    "D8-04": "定价与报价",
    "D8-05": "定价与报价",
    "D8-06": "定价与报价",
}


def load_catalog():
    with open(CATALOG, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    item2class = {}
    for r in rows:
        item2class[r["项"]] = r["类"]
    return item2class


def load_exp():
    with open(EXP, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        return fields, list(reader)


def write_column(fields, rows):
    if "对应子项" in fields:
        return False
    backup = EXP.with_suffix(".csv.bak")
    shutil.copy2(EXP, backup)
    fields = fields + ["对应子项"]
    for r in rows:
        r["对应子项"] = MAP.get(r["编号"], "")
    with open(EXP, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return True


def split_subitems(raw, item2class):
    """按顿号分割，相邻片段拼接后若是合法细类名则合并。

    细类名自身含顿号（如「互惠、社会交换与地位」），直接 split 会拆坏，
    这里贪心合并：先把每个片段与后续片段拼接，命中目录细类名则作为一个子项。
    """
    parts = [s for s in (raw or "").split("、") if s]
    subs, i = [], 0
    while i < len(parts):
        merged = parts[i]
        j = i + 1
        while j < len(parts) and (merged + "、" + parts[j]) in item2class:
            merged = merged + "、" + parts[j]
            j += 1
        subs.append(merged)
        i = j
    return subs


def stats(rows, item2class):
    per_class = defaultdict(lambda: {"E2plus": 0, "E3E4": 0, "items": set()})
    missing = []
    for r in rows:
        subs = split_subitems(r.get("对应子项"), item2class)
        if not subs:
            missing.append(r["编号"])
        level = (r.get("证据等级") or "").strip().upper()
        for s in subs:
            cls = item2class.get(s)
            if not cls:
                missing.append(f"{r['编号']}:{s}(不在目录)")
                continue
            if level in ("E2", "E3", "E4"):
                per_class[cls]["E2plus"] += 1
            if level in ("E3", "E4"):
                per_class[cls]["E3E4"] += 1
            per_class[cls]["items"].add(s)
    return per_class, missing


def main():
    item2class = load_catalog()
    fields, rows = load_exp()
    if "--stats" not in sys.argv:
        changed = write_column(fields, rows)
        print(f"写入「对应子项」列：{'已加' if changed else '已存在，未重复加'}（备份 experience.csv.bak）")
        fields, rows = load_exp()
    per_class, missing = stats(rows, item2class)
    classes = sorted({c for c in item2class.values()})
    ok = 0
    print("\n大类经验门槛（≥3 条 E2 以上，其中 ≥1 条 E3/E4）：")
    for c in classes:
        d = per_class[c]
        passed = d["E2plus"] >= 3 and d["E3E4"] >= 1
        ok += passed
        print(f"  {'过' if passed else '不过'}  {c}：E2+ {d['E2plus']} 条，E3/E4 {d['E3E4']} 条")
    print(f"\n合计：{ok}/{len(classes)} 个大类过经验门槛")
    if missing:
        print("未挂上的编号：", "、".join(missing))


if __name__ == "__main__":
    main()
