#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S1 第 6 批：对「检索不到」逐条诊断——目标文档在 top10 里排第几、被谁挤掉。中间产物。"""
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

catalog = load_catalog()
meta_rows, by_name = load_meta()
conn = rag.connect(rag.DB_PATH, create=False)
docs = load_docs(conn)

items = sys.argv[1:] if len(sys.argv) > 1 else None
for row in catalog:
    if items and row["编号"] not in items:
        continue
    meta = match_meta(row["资料名称"], by_name)
    if not meta:
        continue
    local = (meta.get("本地路径") or "").strip()
    if not local:
        continue
    path = PROJECT / "04-知识底座" / "knowledge" / "sources" / local
    if not path.exists():
        continue
    src = str(path.relative_to(PROJECT))
    doc_id = docs.get(src)
    if not doc_id:
        continue
    seg, vec, loc = None, None, None
    seg = conn.execute("SELECT COUNT(*) FROM segments WHERE doc_id=?", (doc_id,)).fetchone()[0]
    vec = conn.execute(
        "SELECT COUNT(*) FROM segments s JOIN seg_vec v ON v.rowid=s.id WHERE s.doc_id=?",
        (doc_id,)).fetchone()[0]
    loc = conn.execute(
        "SELECT COUNT(*) FROM segments WHERE doc_id=? AND TRIM(locator)<>''", (doc_id,)).fetchone()[0]
    q = (row.get("一句话它解决什么") or "").strip() or row["资料名称"]
    hits, _ = rag.search(conn, q, k=10, mode="hybrid")
    rank = None
    for i, h in enumerate(hits, 1):
        if h["path"] == src:
            rank = i
            break
    flag = f"rank={rank}" if rank else f"不在top10(段{seg}向{vec}定{loc})"
    tops = " ; ".join(f"{i}:{h['path'].split('/')[-1][:34]}({h.get('sim', 0):.3f})"
                      for i, h in enumerate(hits[:5], 1))
    print(f"{row['编号']} {flag} | Q={q[:40]}")
    print(f"    top5: {tops}")

conn.close()
