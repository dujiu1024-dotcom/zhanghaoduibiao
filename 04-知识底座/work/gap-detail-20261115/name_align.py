#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时脚本：对「只有书名」条目做模糊对齐核对，找出 metadata 已有但名不匹配的条目。只读。"""
import csv
import difflib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent
PROJECT = BASE.parent


def norm_name(s):
    s = (s or "").split("/")[0]
    s = re.sub(r"[（(].*?[)）]", "", s)
    s = re.sub(r"[\s·:：\-—，,。.、]+", "", s)
    return s.lower()


with open(BASE / "work" / "gap-detail-20261115" / "gap_detail.csv", encoding="utf-8-sig") as f:
    gaps = list(csv.DictReader(f))
with open(BASE / "knowledge" / "sources" / "metadata.csv", encoding="utf-8-sig") as f:
    meta = list(csv.DictReader(f))

gap_only_name = [g for g in gaps if g["差在哪"] == "只有书名"]
meta_names = [(r["题名"], r["本地路径"], r["质量分级"], r["入库时间"]) for r in meta]

print("== 可能只是名不匹配的条目（相似度 ≥0.62 或包含关键词重叠）==")
n = 0
for g in gap_only_name:
    key = norm_name(g["资料名称"])
    best, best_score = None, 0
    for (t, p, q, ing) in meta_names:
        k2 = norm_name(t)
        score = difflib.SequenceMatcher(None, key, k2).ratio()
        # 词元重叠
        toks1 = set(re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}", key.lower()))
        toks2 = set(re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}", (t or "").lower()))
        overlap = len(toks1 & toks2) / max(1, len(toks1))
        score = max(score, overlap)
        if score > best_score:
            best_score, best = score, (t, p, q, ing)
    if best and best_score >= 0.62:
        n += 1
        print(f"[{g['编号']}] catalog: {g['资料名称']}")
        print(f"      metadata: {best[0]} ｜ 路径: {best[1]} ｜ {best[2]} ｜ 入库 {best[3]} ｜ 相似 {best_score:.2f}")
print(f"\n共 {n} 条疑似名不匹配（其余 {len(gap_only_name)-n} 条为真缺原文）")
