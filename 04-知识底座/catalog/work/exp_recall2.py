#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""召回对照实验 v2：A/B/C/D/E 五组 + 来源类型统计。只读，不改库。"""
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "/Users/longyi/project/账号对标/04-知识底座/rag")
import rag as R  # noqa: E402


def srctype(p):
    """来源类型：原文 / 笔记 / 经验 / 未判。仅凭 source_path 判。"""
    if "/secondhand/" in p:
        return "笔记"
    if any(x in p for x in ("/fulltext/law/", "/fulltext/papers/", "/fulltext/official/", "/fulltext/books/")):
        return "原文"
    if "/books/" in p:
        return "原文"
    if "/knowledge/accounts/" in p:
        return "经验"
    if "methodology__" in p or "/knowledge/methodology/" in p or "/knowledge/topics/" in p:
        return "笔记"
    if "/knowledge/" in p:
        return "笔记"
    return "未判"


QS = [
    ("Q5合规", "广告法 虚假宣传 极限词 禁止 处罚", ["/fulltext/law/"]),
    ("Q3议价", "客户说贵 便宜点", ["经营-03-议价与谈判", "objection-handling-sales"]),
    ("Q6前三秒", "一条30秒视频开头三秒抓什么", ["benchmark-teardown-content-analysis"]),
    ("Q1画像", "199元诊断卖给谁 客户画像", ["icp-stp-segmentation"]),
    ("Q7交付", "标准件交付验收要交什么", ["definition-of-done-acceptance"]),
    ("Q8合同", "客户要合同资质账期该不该接", ["profit-first-cash-flow"]),
]
Q10 = QS + [
    ("Q2定价依据", "价值证明 定价依据 为什么值这个价", ["value-based-pricing"]),
    ("Q4首询", "第一个询盘进来第一句话说什么", ["objection-handling-sales", "knowing-through-consulting"]),
    ("Q3b议价", "客户说贵 便宜点 议价 折扣", ["经营-03-议价与谈判"]),
    ("Q6b前三秒", "视频开头 完播率 黄金三秒", ["benchmark-teardown-content-analysis"]),
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
    return rrf([(R.literal_search(conn, q, 20), 0.8), (R.vector_search(conn, q, 20), 1.0)])


def dkey(h):
    t = re.sub(r"^(L\d-|methodology__)", "", (h.get("title") or "").split(" / ")[0])
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]", "", t.lower()) or h["path"].split("/")[-1]


def dedup(hits):
    seen, out = set(), []
    for h in hits:
        k = dkey(h)
        if k not in seen:
            seen.add(k)
            out.append(h)
    return out


def srcw(h):
    p = h["path"]
    if "/fulltext/law/" in p:
        return 3.0
    if re.search(r"/\d{3}-", p):
        return 1.5
    if "/knowledge/" in p:
        return 0.6
    return 1.0


def run_c(a):
    return dedup(a)


def run_d(a):
    return sorted(dedup(a), key=lambda x: -x["rrf"] * srcw(x))


def run_e(a):
    d = run_d(a)
    orig = [h for h in d if srctype(h["path"]) == "原文"]
    note = [h for h in d if srctype(h["path"]) != "原文"]
    return orig + note


def rank(hits, golds):
    for i, h in enumerate(hits[:5], 1):
        if any(g in h["path"] or g in (h.get("title") or "") for g in golds):
            return i
    return None


conn = R.connect(create=False)
R.load_license_note()
R.load_index_only(conn)

# ---- 加项1：全库三类段数
rows = conn.execute("""select d.source_path,count(*) from segments s join docs d on s.doc_id=d.id
                       group by d.id""").fetchall()
seg_by = Counter()
doc_by = Counter()
for p, n in rows:
    t = srctype(p)
    seg_by[t] += n
    doc_by[t] += 1
tot = sum(seg_by.values())
print("=== 全库来源类型（按段） ===")
for k, v in seg_by.most_common():
    print(f"  {k}: {v} 段 = {v/tot*100:.1f}%   （{doc_by[k]} 篇）")
print(f"  合计 {tot} 段 / {sum(doc_by.values())} 篇")

# ---- 五组对照
print("\n=== 五组 + 同义词列 Recall@5 ===")
print(f"{'查询':<10} {'A':>6} {'A+同义':>7} {'B':>6} {'C':>6} {'D':>6} {'E':>6}")
print("-" * 54)
score = defaultdict(int)
for name, q, golds in QS:
    a = run_a(q)
    qx, note = R.expand_query(q)
    ax = run_a(qx)
    rr = [rank(a, golds), rank(ax, golds), rank(run_b(q), golds),
          rank(run_c(a), golds), rank(run_d(a), golds), rank(run_e(a), golds)]
    for tag, r in zip(("A", "AX", "B", "C", "D", "E"), rr):
        if r:
            score[tag] += 1
    f = lambda x: f"#{x}" if x else "未召回"
    print(f"{name:<10} {f(rr[0]):>6} {f(rr[1]):>7} {f(rr[2]):>6} {f(rr[3]):>6} {f(rr[4]):>6} {f(rr[5]):>6}")
    if note:
        print(f"           └ 扩展：{note}")
print("-" * 54)
print("Recall@5:", {k: f"{v}/6" for k, v in sorted(score.items())})

# ---- 加项1后半：10 查询 top-5 构成
print("\n=== 10 查询 top-5 的来源类型构成（A 组现状） ===")
agg = Counter()
for name, q, _ in Q10:
    kinds = [srctype(h["path"]) for h in run_a(q)[:5]]
    agg.update(kinds)
    print(f"  {name}: {dict(Counter(kinds))}")
print(f"  合计: {dict(agg)}")

# ---- 加项2：规则准确率抽检 20 例
print("\n=== 自动判定抽检 20 例（判据：仅看 source_path） ===")
sample = []
for p, n in rows:
    t = srctype(p)
    sample.append((t, p.split("knowledge/sources/")[-1][:62]))
by = defaultdict(list)
for t, p in sample:
    by[t].append(p)
picked = []
for t, ps in by.items():
    picked += [(t, p) for p in ps[:max(1, 20 * len(ps) // len(sample))]]
for t, p in picked[:20]:
    print(f"  [{t}] {p}")
print(f"\n可自动判定：{sum(v for k, v in seg_by.items() if k != '未判')/tot*100:.1f}% 段"
      f"（未判 {seg_by.get('未判',0)} 段 / {doc_by.get('未判',0)} 篇）")
conn.close()
