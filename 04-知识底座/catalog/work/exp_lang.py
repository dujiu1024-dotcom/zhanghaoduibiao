#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语言错配诊断：语言构成 / 段长分布 / 自查询召回。只读。"""
import re
import statistics as st
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "/Users/longyi/project/账号对标/04-知识底座/rag")
import rag as R  # noqa: E402

DB = "/Users/longyi/project/账号对标/04-知识底座/rag/kbase.db"


def srctype(p):
    if "/secondhand/" in p:
        return "笔记"
    if any(x in p for x in ("/fulltext/law/", "/fulltext/papers/", "/fulltext/official/", "/fulltext/books/")):
        return "原文"
    if "/books/" in p:
        return "原文"
    if "/knowledge/accounts/" in p:
        return "经验"
    if "/knowledge/" in p:
        return "笔记"
    return "未判"


def lang(t):
    if not t:
        return "空"
    n = sum(1 for c in t if ord(c) > 127)
    r = n / len(t)
    if r > 0.15:
        return "中文"
    if r < 0.02:
        return "英文"
    return "混合"


conn = R.connect(create=False)
rows = conn.execute("""select s.doc_id,s.text,s.char_len,d.source_path from segments s
                       join docs d on s.doc_id=d.id""").fetchall()

# 1. 语言构成（段级 + 文档级）
doc_lang = {}
seg_lang = Counter()
seg_by_type_lang = defaultdict(Counter)
for did, txt, cl, p in rows:
    L = lang(txt)
    seg_lang[L] += 1
    seg_by_type_lang[srctype(p)][L] += 1
    doc_lang.setdefault(did, Counter())[L] += 1
doc_level = Counter()
for did, c in doc_lang.items():
    doc_level[c.most_common(1)[0][0]] += 1
tot = sum(seg_lang.values())
print("=== 1. 语言构成 ===")
print(f"  段级（{tot} 段）：" + "  ".join(f"{k} {v} ({v/tot*100:.1f}%)" for k, v in seg_lang.most_common()))
print(f"  文档级（{sum(doc_level.values())} 篇）：" + "  ".join(f"{k} {v} ({v/sum(doc_level.values())*100:.1f}%)"
                                                       for k, v in doc_level.most_common()))
for t in ("原文", "笔记"):
    c = seg_by_type_lang[t]
    s = sum(c.values())
    print(f"  {t} 内部：{dict((k, f'{v} ({v/s*100:.0f}%)') for k, v in c.most_common())}")

# 2. 段长对比
print("\n=== 2. 段长分布（字符） ===")
for t in ("原文", "笔记"):
    ls = [cl or len(txt or "") for _, _, cl, p in rows if srctype(p) == t]
    if not ls:
        continue
    ls.sort()
    print(f"  {t}: n={len(ls)}  中位={st.median(ls):.0f}  均值={st.mean(ls):.0f}  "
          f"p90={ls[int(len(ls)*0.9)]}  最长={ls[-1]}")

# 4. 自查询召回
print("\n=== 4. 自查询：20 段用自己的话搜自己 ===")
import random
random.seed(42)
cand = [(s, txt, p) for s, txt, cl, p in rows
        if srctype(p) == "原文" and txt and len(txt) > 200]
pick = random.sample(cand, 20)
hit5 = hit20 = 0
for sid, txt, p in pick:
    probe = txt[8:88]
    v = R.vector_search(conn, probe, 20)
    ids = [x["seg_id"] for x in v]
    if sid in ids[:5]:
        hit5 += 1
    if sid in ids:
        hit20 += 1
print(f"  自己出现在 top-5：{hit5}/20　出现在 top-20：{hit20}/20")
print(f"  抽样文档示例：{pick[0][2].split('sources/')[-1][:60]}")

# 向量覆盖
nv = conn.execute("select count(*) from segment_vec").fetchone()[0] if conn.execute(
    "select name from sqlite_master where name='segment_vec'").fetchone() else -1
print(f"  向量索引行数：{nv}　segments 行数：{tot}")
conn.close()
