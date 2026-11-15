#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""召回对照实验：同一批查询跑 A/B/C/D 四组，记正确答案在 top-5 的排位。"""
import re
import sys
from collections import defaultdict

sys.path.insert(0, "/Users/longyi/project/账号对标/04-知识底座/rag")
import rag as R  # noqa: E402

QS = [
    ("Q5合规", "广告法 虚假宣传 极限词 禁止 处罚", ["/fulltext/law/"]),
    ("Q3议价", "客户说贵 便宜点", ["经营-03-议价与谈判", "objection-handling-sales"]),
    ("Q6前三秒", "一条30秒视频开头三秒抓什么", ["benchmark-teardown-content-analysis"]),
    ("Q1画像", "199元诊断卖给谁 客户画像", ["icp-stp-segmentation"]),
    ("Q7交付", "标准件交付验收要交什么", ["definition-of-done-acceptance"]),
    ("Q8合同", "客户要合同资质账期该不该接", ["profit-first-cash-flow"]),
]


def rrf(pairs):
    m = {}
    for lst, w in pairs:
        for i, r in enumerate(lst, 1):
            k = r["seg_id"]
            if k not in m:
                m[k] = {**r, "rrf": 0.0}
            m[k]["rrf"] += w / (60 + i)
    return sorted(m.values(), key=lambda x: -x["rrf"])


def run_a(q):
    lit = R.literal_search(conn, q, 20)
    tags, _ = R.tag_search(conn, q, 20)
    vec = R.vector_search(conn, q, 20)
    return rrf([(lit, 0.8), (tags, 1.1), (vec, 1.0)])


def run_b(q):
    lit = R.literal_search(conn, q, 20)
    vec = R.vector_search(conn, q, 20)
    return rrf([(lit, 0.8), (vec, 1.0)])


def dkey(h):
    t = (h.get("title") or "").split(" / ")[0]
    t = re.sub(r"^(L\d-|methodology__)", "", t)
    k = re.sub(r"[^0-9a-z\u4e00-\u9fff]", "", t.lower())
    return k or h["path"].split("/")[-1]


def dedup(hits):
    best = {}
    order = []
    for h in hits:
        k = dkey(h)
        if k not in best:
            best[k] = h
            order.append(k)
    return [best[k] for k in order]


def srcw(h):
    p = h["path"]
    if "/fulltext/law/" in p:
        return 3.0
    if re.search(r"/\d{3}-", p):
        return 1.5
    if "/knowledge/" in p:
        return 0.6
    return 1.0


def run_d(hits):
    out = dedup(hits)
    for h in out:
        h = h
    return sorted(out, key=lambda x: -x["rrf"] * srcw(x))


def rank(hits, golds):
    for i, h in enumerate(hits[:5], 1):
        if any(g in h["path"] or g in (h.get("title") or "") for g in golds):
            return i
    return None


conn = R.connect(create=False)
R.load_license_note()
R.load_index_only(conn)

print(f"{'查询':<10} {'A现状':>8} {'B去标签':>8} {'C去重':>8} {'D去重+权重':>10}")
print("-" * 50)
score = defaultdict(int)
for name, q, golds in QS:
    a = run_a(q)
    b = run_b(q)
    c = dedup(a)
    d = run_d(a)
    ra, rb, rc, rd = rank(a, golds), rank(b, golds), rank(c, golds), rank(d, golds)
    for tag, r in (("A", ra), ("B", rb), ("C", rc), ("D", rd)):
        if r:
            score[tag] += 1
    f = lambda x: f"#{x}" if x else "未召回"
    print(f"{name:<10} {f(ra):>8} {f(rb):>8} {f(rc):>8} {f(rd):>10}")
print("-" * 50)
print("Recall@5:", {k: f"{v}/6" for k, v in sorted(score.items())})

print("\n各查询 A 组 top-5 来源构成：")
for name, q, golds in QS:
    a = run_a(q)[:5]
    kinds = []
    for h in a:
        p = h["path"]
        if "/fulltext/law/" in p:
            kinds.append("法规")
        elif re.search(r"/\d{3}-", p):
            kinds.append("编号书")
        elif "/knowledge/" in p:
            kinds.append("本库笔记")
        elif "/books/" in p:
            kinds.append("书")
        else:
            kinds.append("其他")
    print(f"  {name}: {' / '.join(kinds)}")
conn.close()
