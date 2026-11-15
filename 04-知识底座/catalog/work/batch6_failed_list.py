#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S1 第 6 批辅助：复用 check_gate 的判定逻辑，导出「没入库」「检索不到」的精确清单。中间产物，不入主库。"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent               # work → catalog → 04-知识底座
PROJECT = BASE.parent
RAG = BASE / "rag"
sys.path.insert(0, str(RAG))
sys.path.insert(0, str(BASE / "catalog"))

import rag  # noqa: E402
from check_gate import load_catalog, load_meta, load_docs, match_meta, doc_stats  # noqa: E402

catalog = load_catalog()
meta_rows, by_name = load_meta()
conn = rag.connect(rag.DB_PATH, create=False)
docs = load_docs(conn)

fail = defaultdict(list)
for row in catalog:
    meta = match_meta(row["资料名称"], by_name)
    if not meta:
        fail["只有书名"].append((row["编号"], row["类"], row["项"], row["资料名称"], ""))
        continue
    local = (meta.get("本地路径") or "").strip()
    if not local:
        fail["没登记本地路径"].append((row["编号"], row["类"], row["项"], row["资料名称"], ""))
        continue
    path = PROJECT / "04-知识底座" / "knowledge" / "sources" / local
    if not path.exists():
        fail["本地没文件"].append((row["编号"], row["类"], row["项"], row["资料名称"], str(path)))
        continue
    src = str(path.relative_to(PROJECT))
    doc_id = docs.get(src)
    if not doc_id:
        fail["没入库"].append((row["编号"], row["类"], row["项"], row["资料名称"], src))
        continue
    seg, vec, loc = doc_stats(conn, doc_id)
    if seg == 0 or vec == 0:
        fail["没向量化"].append((row["编号"], row["类"], row["项"], row["资料名称"], src))
        continue
    if loc == 0:
        fail["没出处定位"].append((row["编号"], row["类"], row["项"], row["资料名称"], src))
        continue
    q = (row.get("一句话它解决什么") or "").strip() or row["资料名称"]
    hits, _ = rag.search(conn, q, k=5, mode="hybrid")
    if src not in {h["path"] for h in hits}:
        fail["检索不到"].append((row["编号"], row["类"], row["项"], row["资料名称"], src))

for why, items in fail.items():
    print(f"\n===== {why}（{len(items)}）=====")
    for no, cls, item, name, p in items:
        print(f"{no}｜{item}｜{name[:45]}｜{p}")

conn.close()
