#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据自检：重复文档、metadata 缺字段、档位不一致、编号冲突。可重复跑，只读。

用法：python3 catalog/check_data.py
退出码：0 无问题；1 有需处理项（用于定时任务判断）。
"""
import csv
import os
import sqlite3
import sys
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 04-知识底座
PROJECT = os.path.dirname(BASE)
DB = os.path.join(BASE, "rag", "kbase.db")
META = os.path.join(BASE, "knowledge", "sources", "metadata.csv")
CAT = os.path.join(BASE, "catalog", "catalog.csv")

REQUIRED = ["题名", "作者", "质量分级", "授权限制", "本地路径", "采集时间"]
VALID_Q = {"可引用", "仅参考", "不可引用", "历史文本|已废止"}


def main():
    problems = 0
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    docs = [dict(zip(("id", "path", "title", "quality", "sha1"), r)) for r in
            conn.execute("select id,source_path,title,quality,sha1 from docs")]
    segs = dict(conn.execute("select doc_id,count(*) from segments group by doc_id"))
    meta = list(csv.DictReader(open(META, encoding="utf-8-sig")))

    # 1) 重复文档（同 sha1）
    g = defaultdict(list)
    for d in docs:
        g[d["sha1"]].append(d)
    dups = {k: v for k, v in g.items() if len(v) > 1}
    extra = sum(len(v) - 1 for v in dups.values())
    print(f"[重复] 组 {len(dups)}｜多余副本 {extra}｜涉及段 {sum(segs.get(d['id'], 0) for v in dups.values() for d in v[1:])}")
    if extra:
        problems += 1
        for v in list(dups.values())[:3]:
            print("   例：", "  ＝  ".join(x["path"].split("sources/")[-1] for x in v[:2]))

    # 2) metadata 缺字段
    bad_rows = []
    for r in meta:
        miss = [k for k in REQUIRED if not (r.get(k) or "").strip()]
        if miss:
            bad_rows.append((r["本地路径"][:70], ",".join(miss)))
    print(f"[metadata] 行 {len(meta)}｜缺必填 {len(bad_rows)}")
    for p, m in bad_rows[:5]:
        print(f"   缺 {m}：{p}")
    if bad_rows:
        problems += 1

    # 3) 档位与检索侧不一致
    by_path = {}
    for r in meta:
        by_path[r["本地路径"]] = r
    mis = []
    for d in docs:
        rel = d["path"].split("knowledge/sources/")[-1]
        m = by_path.get(rel)
        if m and m["质量分级"] != d["quality"]:
            mis.append((rel, d["quality"], m["质量分级"]))
        if d["quality"] not in VALID_Q:
            mis.append((rel, d["quality"], "非法档位"))
    no_meta = sum(1 for d in docs if d["path"].split("knowledge/sources/")[-1] not in by_path)
    print(f"[档位] 文档 {len(docs)}｜与 metadata 不一致 {len(mis)}｜无 metadata 行 {no_meta}")
    for x in mis[:5]:
        print("   ", x)
    if mis:
        problems += 1

    # 4) 编号冲突
    if os.path.exists(CAT):
        rows = list(csv.DictReader(open(CAT, encoding="utf-8-sig")))
        c = Counter(r["编号"] for r in rows)
        dupno = {k: v for k, v in c.items() if v > 1}
        print(f"[编号] catalog {len(rows)} 条｜重复编号 {len(dupno)}")
        for k, v in list(dupno.items())[:5]:
            print(f"   {k} 出现 {v} 次")
        if dupno:
            problems += 1

    # 5) 文件缺失（metadata 指了路径但文件不在）
    lost = []
    for r in meta:
        p = r["本地路径"]
        if not p:
            continue
        full = os.path.join(BASE, "knowledge", "sources", p)
        if not os.path.exists(full):
            lost.append(p)
    print(f"[文件] metadata 指向但不存在的文件 {len(lost)}")
    for p in lost[:5]:
        print("   ", p)
    if lost:
        problems += 1

    print("\n结论：" + ("有需处理项" if problems else "无问题"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
