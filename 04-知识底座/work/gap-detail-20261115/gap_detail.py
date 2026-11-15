#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时脚本：列出 catalog 中全部不合格条目及原因，按类型分类，供评估非书缺口可否自助补。
只读，不写任何主库文件。
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent            # 04-知识底座
PROJECT = BASE.parent
RAG = BASE / "rag"
sys.path.insert(0, str(RAG))

sys.path.insert(0, str(BASE / "catalog"))
import rag  # noqa: E402
from check_gate import check_item, load_catalog, load_meta, load_docs  # noqa: E402

conn = rag.connect(rag.DB_PATH, create=False)
catalog = load_catalog()
meta_rows, by_name = load_meta()
docs = load_docs(conn)
cache = {}

rows_out = []
for row in catalog:
    ok, why = check_item(row, by_name, docs, conn, cache, "hybrid")
    if not ok:
        rows_out.append({
            "编号": row["编号"], "类": row["类"], "项": row["项"],
            "资料名称": row["资料名称"], "差在哪": why,
        })

conn.close()

# 按 差在哪 → 项 汇总
by_why = defaultdict(list)
for r in rows_out:
    by_why[r["差在哪"]].append(r)

with open(HERE / "gap_detail.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["编号", "类", "项", "资料名称", "差在哪"])
    w.writeheader()
    w.writerows(rows_out)

print(f"不合格总数：{len(rows_out)}")
for why, rs in sorted(by_why.items(), key=lambda x: -len(x[1])):
    print(f"\n== {why}：{len(rs)} 条 ==")
    # 按 项 分组显示
    by_item = defaultdict(list)
    for r in rs:
        by_item[f'{r["类"]}｜{r["项"]}'].append(r["资料名称"])
    for item, names in sorted(by_item.items()):
        print(f"  [{item}] {len(names)} 条")
