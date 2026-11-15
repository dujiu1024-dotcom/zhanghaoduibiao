#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查 E0（行业口传口径）有没有被合规/报价/平台规则/合同四类判断引用。

E0 永久不得充数，也不得进这四类判断。本脚本扫：
  00-战略与目标/道法术器/**/*.md
  03-决策与复盘/**/*.md
凡一行里同时出现四类关键词之一 + 任一 E0 编号，就算违规命中。

用法：python3 04-知识底座/experience/check_e0.py
输出：命中清单（文件:行号 编号）；没有命中时输出「0 处」。
退出码：0 = 没有违规引用；1 = 有命中。与其他闸一致，便于自动化直接判定。
"""
import csv
import glob
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
LORE = HERE / "industry-lore.csv"
KW = ("合规", "报价", "平台规则", "合同")


def main():
    with open(LORE, encoding="utf-8-sig") as f:
        ids = [r["编号"] for r in csv.DictReader(f) if (r.get("等级") or "").upper() == "E0"]
    if not ids:
        print("0 条 E0，无需检查")
        return 0
    hits = []
    roots = [PROJECT / "00-战略与目标/道法术器", PROJECT / "03-决策与复盘"]
    for root in roots:
        for f in glob.glob(str(root / "**/*.md"), recursive=True):
            with open(f, encoding="utf-8") as fh:
                for i, line in enumerate(fh, 1):
                    if not any(k in line for k in KW):
                        continue
                    for x in ids:
                        if x in line:
                            hits.append(f"{Path(f).relative_to(PROJECT)}:{i} {x}")
    if hits:
        print(f"命中 {len(hits)} 处（E0 不得进这四类判断）：")
        print("\n".join(hits))
        return 1
    print(f"0 处：{len(ids)} 条 E0 均未被合规/报价/平台规则/合同引用")
    return 0


if __name__ == "__main__":
    sys.exit(main())
