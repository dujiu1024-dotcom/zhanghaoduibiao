#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对「检索不到」条目做诊断：问句检索 top5 命中了什么、目标文档排名与相似度。只读。"""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent
PROJECT = BASE.parent
RAG = BASE / "rag"
sys.path.insert(0, str(RAG))
sys.path.insert(0, str(BASE / "catalog"))
import rag  # noqa: E402
from check_gate import load_catalog, load_meta, load_docs, match_meta  # noqa: E402

conn = rag.connect(rag.DB_PATH, create=False)
catalog = {r["编号"]: r for r in load_catalog()}
meta_rows, by_name = load_meta()
docs = load_docs(conn)

DIAG = ["04-14", "05-24", "06-27", "08-22"]

for no in DIAG:
    row = catalog[no]
    meta = match_meta(row["资料名称"], by_name)
    if not meta:
        print(f"{no} {row['资料名称']}: metadata 没匹配上")
        continue
    local = meta.get("本地路径", "").strip()
    src = str((PROJECT / "04-知识底座" / "knowledge" / "sources" / local).relative_to(PROJECT))
    q = (row.get("一句话它解决什么") or "").strip()
    hits, _ = rag.search(conn, q, k=5, mode="hybrid")
    print(f"\n[{no}] {row['资料名称'][:40]}")
    print(f"  问句: {q}")
    print(f"  目标文档: {src}  在库doc_id: {docs.get(src)}")
    for i, h in enumerate(hits, 1):
        mark = " ←目标" if h["path"] == src else ""
        print(f"  top{i}: {h['path'].split('/')[-1][:50]}  score={h.get('score', '?'):.3f}{mark}")
    # 目标文档的实际排名
    hits_wide, _ = rag.search(conn, q, k=50, mode="hybrid")
    rank = next((i for i, h in enumerate(hits_wide, 1) if h["path"] == src), None)
    print(f"  目标在 top50 中的排名: {rank}")
conn.close()
