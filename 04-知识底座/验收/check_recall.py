#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A 库（04-知识底座）检索验收：按职责分组跑题库，出分、判通过/不通过、出补料清单。

只读：不写 kbase.db，不改库内任何数据。检索一律走日常入口：
    rag/.venv/bin/python rag/rag.py search "<问题>" -k 10 --json

用法：
    python3 验收/check_recall.py                 # 跑全部组，写报告
    python3 验收/check_recall.py --group 06      # 只跑第 6 组
    python3 验收/check_recall.py --group 06 --group 09
    python3 验收/check_recall.py --no-report     # 只在终端出分
"""

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
QB_DIR = HERE / "题库"
RAG_DIR = BASE / "rag"
RAG_PY = RAG_DIR / "rag.py"
RAG_VENV = RAG_DIR / ".venv" / "bin" / "python"
DB = Path(os.environ.get("KBASE_DB", str(RAG_DIR / "kbase.db"))).expanduser().resolve()

COLUMNS = ["题号", "问题原文", "gold路径", "gold段号", "判定标准",
           "期望能否引原文", "期望", "无料归因", "补料建议"]
ATTRS = ["缺资料", "需实测", "待查"]
PASS_RECALL5 = 0.70
PASS_ORIGIN5 = 0.60
PASS_GROUP_RECALL5 = 0.50
FULL_GROUP = 20


# ---------------------------------------------------------------- 路径归一

def canon(path: str) -> str:
    """把库内 source_path 与题库里的相对路径归一成同一写法。

    - 去掉 04-知识底座/knowledge/ 前缀
    - sources/fulltext/knowledge/ 下的是自撰笔记副本（methodology__X.txt），
      归一到 methodology/X.md，避免同一段内容因路径不同被判成两个文档。
    """
    p = (path or "").replace("\\", "/").strip()
    p = p.removeprefix("04-知识底座/knowledge/")
    prefix = "sources/fulltext/knowledge/"
    if p.startswith(prefix):
        p = p[len(prefix):]
        p = p.replace("__", "/")
        if p.endswith(".txt"):
            p = p[:-4] + ".md"
    return p


def source_type(path: str) -> str:
    c = canon(path)
    if c.startswith("experience/"):
        return "经验"
    if c.startswith("sources/fulltext/"):
        return "原文"
    return "笔记"


def norm_locator(loc: str) -> str:
    return (loc or "").strip().replace(" ", "")


# ---------------------------------------------------------------- 题库

def load_questions(selected: list[str]):
    files = sorted(QB_DIR.glob("*.csv"))
    if not files:
        sys.exit(f"题库目录为空：{QB_DIR}")
    groups, rows = [], []
    for f in files:
        code, name = f.stem.split("-", 1)
        if selected and code not in selected:
            continue
        group = {"code": code, "name": name, "file": f, "rows": []}
        with f.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
            if missing:
                sys.exit(f"{f.name} 缺列：{missing}")
            for r in reader:
                if not (r.get("题号") or "").strip():
                    continue
                row = {k: (r.get(k) or "").strip() for k in COLUMNS}
                if row["期望"] not in ("命中", "无料"):
                    sys.exit(f"{f.name} {row['题号']}：期望只能是 命中/无料，当前 {row['期望']!r}")
                if row["期望"] == "命中" and not row["gold路径"]:
                    sys.exit(f"{f.name} {row['题号']}：期望=命中 但没有 gold路径")
                if row["期望"] == "无料" and row["无料归因"] not in ATTRS:
                    sys.exit(f"{f.name} {row['题号']}：无料题必须填 无料归因（缺资料/需实测/待查）")
                group["rows"].append(row)
        groups.append(group)
        rows.extend(group["rows"])
    ids = [r["题号"] for r in rows]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        sys.exit(f"题号重复：{sorted(dup)}")
    return groups, rows


# ---------------------------------------------------------------- gold 校验

def load_gold_index(golds):
    """返回 canon_path -> (doc_ids, locators, qualities)。只读打开数据库。"""
    con = sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    docs = con.execute("SELECT id, source_path, quality FROM docs").fetchall()
    by_path = {}
    for d in docs:
        by_path.setdefault(canon(d["source_path"]), {"ids": [], "locs": set(), "qualities": set()})
        item = by_path[canon(d["source_path"])]
        item["ids"].append(d["id"])
        item["qualities"].add(d["quality"])
    wanted = {canon(g) for g in golds if g}
    for cp in wanted:
        if cp not in by_path:
            continue
        ids = by_path[cp]["ids"]
        ph = ",".join("?" * len(ids))
        for r in con.execute(f"SELECT locator FROM segments WHERE doc_id IN ({ph})", ids):
            by_path[cp]["locs"].add(norm_locator(r["locator"]))
    con.close()
    return by_path


def verify_gold(rows, index):
    bad = []
    for r in rows:
        if r["期望"] != "命中":
            continue
        cp = canon(r["gold路径"])
        item = index.get(cp)
        if not item:
            bad.append((r["题号"], f"gold 路径库内不存在：{r['gold路径']}"))
            continue
        if "[文档级]" not in r["判定标准"]:
            if norm_locator(r["gold段号"]) not in item["locs"]:
                bad.append((r["题号"], f"gold 段号库内不存在：{r['gold路径']} {r['gold段号']}"))
    if bad:
        for qid, msg in bad:
            print(f"[gold无效] {qid} {msg}", file=sys.stderr)
        sys.exit("题库里有 gold 指不到真实文档/段号，按规则不许跑。")
    return True


# ---------------------------------------------------------------- 检索

def run_search_k(question: str, k: int = 10, mode: str = "", no_xling: bool = False):
    cmd = [str(RAG_VENV), str(RAG_PY), "search", question, "-k", str(k), "--json"]
    if mode:
        cmd += ["--mode", mode]
    if no_xling:
        cmd.append("--no-xling")
    started = time.perf_counter()
    proc = subprocess.run(cmd, cwd=str(RAG_DIR), capture_output=True, text=True, timeout=300)
    elapsed = time.perf_counter() - started
    if proc.returncode != 0:
        raise RuntimeError(f"rag.py 退出码 {proc.returncode}：{(proc.stderr or '').strip()[-400:]}")
    lines = proc.stdout.splitlines()
    start = next((i for i, l in enumerate(lines) if l.strip() == "{"), None)
    if start is None:
        raise RuntimeError(f"未找到 JSON 输出：{proc.stdout.strip()[:300]}")
    data = json.loads("\n".join(lines[start:]))
    hits = data.get("hits", []) if data.get("status") == "ok" else []
    return data, hits, elapsed


def run_search(question: str):
    return run_search_k(question, 10)


def find_gold_rank(row, hits):
    """在给定命中列表里找 gold，返回 (名次, 命中记录)。段级要求段号一致，文档级只要求路径一致。"""
    cp = canon(row["gold路径"]) if row["gold路径"] else ""
    strict = "[文档级]" not in row["判定标准"]
    for i, h in enumerate(hits, 1):
        if canon(h.get("path", "")) != cp:
            continue
        if strict:
            hl, gl = norm_locator(h.get("locator", "")), norm_locator(row["gold段号"])
            if not (hl == gl or hl.startswith(gl + ".")):
                continue
        return i, h
    return None, None


def judge_row(row, index):
    data, hits, elapsed = run_search(row["问题原文"])
    status = data.get("status", "unknown")
    low_conf = (data.get("answered") is False) or any(h.get("confidence") == "low" for h in hits)
    top5_hits, top10_hits = hits[:5], hits[:10]
    gold_rank, gold_hit = find_gold_rank(row, top10_hits)
    cp = canon(row["gold路径"]) if row["gold路径"] else ""
    gold_is_origin = cp.startswith("sources/fulltext/")
    comp = {"原文": 0, "笔记": 0, "经验": 0}
    for h in top10_hits:
        comp[source_type(h.get("path", ""))] += 1
    origin5 = any(source_type(h.get("path", "")) == "原文" and h.get("quality") == "可引用"
                  for h in top5_hits)
    return {
        **row,
        "status": status,
        "answered": data.get("answered"),
        "low_conf": low_conf,
        "candidates": data.get("candidates", {}),
        "hits": hits,
        "n_hits": len(hits),
        "rank": gold_rank,
        "gold_hit": gold_hit,
        "gold_is_origin": gold_is_origin,
        "gold_type_label": source_type(row["gold路径"]) if row["gold路径"] else "—",
        "gold_quality": ("/".join(sorted(index.get(cp, {}).get("qualities", [])))
                         if cp in index else ""),
        "top5": [h.get("path", "") for h in top5_hits],
        "comp": comp,
        "origin5": origin5,
        "elapsed": elapsed,
        "empty": not hits,
    }


# ---------------------------------------------------------------- 深诊断（--deep）

def cjk_ratio(s: str) -> float:
    if not s:
        return 0.0
    return len(re.findall(r"[\u4e00-\u9fff]", s)) / len(s)


def load_gold_texts(golds):
    """只读取出 gold 段原文，用于段长与段内位置统计。返回 (canon_path, 段号) -> 文本。"""
    wanted = {canon(g) for g in golds if g}
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    out = {}
    for p, loc, txt in con.execute(
            "SELECT d.source_path, s.locator, s.text FROM segments s JOIN docs d ON d.id=s.doc_id"):
        cp = canon(p)
        if cp in wanted:
            out[(cp, norm_locator(loc))] = txt or ""
    con.close()
    return out


def norm_space(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


STOP_GRAMS = ["怎么", "什么", "如何", "是否", "哪些", "应该", "可以", "到底", "为什么",
              "这个", "那个", "一下", "时候", "要不", "能不", "是不是", "有没有"]


def seg_position(question: str, text: str) -> str:
    """【推算】用问句字组在 gold 段里首次出现的位置粗判答案在段首/段中/段尾。
    只是切段长度排查用的近似，不是语义标注。"""
    if not text:
        return "—"
    q = norm_space(question)
    for w in STOP_GRAMS:
        q = q.replace(w, "")
    toks = {q[i:i + 2] for i in range(len(q) - 1)}
    toks = [t for t in toks if len(t) == 2 and not re.search(r"[\s，。？！、]", t)]
    idxs = [text.find(t) for t in toks if text.find(t) >= 0]
    if not idxs:
        return "未匹配"
    rel = min(idxs) / max(len(text), 1)
    return "段首" if rel < 0.33 else ("段中" if rel < 0.67 else "段尾")


def deep_row(row, texts, kdiag=50):
    """记 gold 在全量候选里的名次、每路原始名次、四分类、段长与段内位置。

    kdiag 上限只能是 51：检索器内部把向量池放大 10 倍再乘 8 取 KNN，
    sqlite-vec 的 KNN LIMIT 上限是 4096，k=200 会直接报错（k*10*8=16000）。
    这是检索侧约束，不改 rag.py 就只能探到 50 名这一层。
    """
    if row["期望"] == "无料":
        return {"category": "无料", "recall50": None, "rank50": None, "rank_diag": None,
                "chan": {}, "probe": {}, "cross": False, "xling_off": False, "note": "",
                "seg_chars": None, "seg_pos": "—", "q_lang": "中", "g_lang": "—", "cell": "—"}

    xling_off = False
    try:
        d50, h50, _ = run_search_k(row["问题原文"], kdiag)
    except RuntimeError as e:
        # 跨语言扩写会把内部 k 放大到 2 倍，k=50 时 KNN LIMIT 超 4096；关掉扩写才跑得动。
        if "knn query too large" not in str(e):
            raise
        d50, h50, _ = run_search_k(row["问题原文"], kdiag, no_xling=True)
        xling_off = True
    rank_diag, hit_diag = find_gold_rank(row, h50)
    cross = bool(hit_diag.get("cross")) if hit_diag else False
    chan = dict(hit_diag.get("channels") or {}) if hit_diag else {}

    # 融合结果里找不到 gold 时，再用单路模式确认「是不是根本没进任何一路候选」
    probe = {}
    if rank_diag is None:
        for mode in ("literal", "tag"):
            _, hm, _ = run_search_k(row["问题原文"], kdiag, mode)
            rr, _ = find_gold_rank(row, hm)
            if rr:
                probe[mode] = rr
    cp = canon(row["gold路径"])
    same_doc = sum(1 for h in h50 if canon(h.get("path", "")) == cp)
    # 关掉跨语言扩写才跑得动的题，k=50 可能反而漏掉 k=10 已经命中的 gold；
    # 这种情况以生产口径（k=10）的名次为准，不记成「不在前50」。
    if xling_off and rank_diag is None and row["rank"]:
        rank_diag = row["rank"]

    r10 = row["rank"]
    if r10 and r10 <= 5:
        cat = "命中"
    elif cross and r10 and r10 <= 10:
        cat = "进前10但被跨语言规则顶出前5"
    elif rank_diag is not None or probe or same_doc >= 2:
        cat = "在某路候选，融合后掉出前5"
    else:
        cat = "不在任何一路候选"

    note = []
    if rank_diag is None and same_doc >= 2:
        note.append(f"同文档已有 {same_doc} 条进候选，gold 段被 per_doc 截断或未召回")
    if rank_diag is None and not probe:
        note.append("字面/标签单路也无；向量单路无法单独探测，按融合结果判")
    if cross:
        note.append("gold 命中被标为跨语言")
    if xling_off:
        note.append(f"k={kdiag} 会超 KNN 上限，本次关闭跨语言扩写后测得")

    text = texts.get((cp, norm_locator(row["gold段号"])), "") if row["gold段号"] else ""
    ql = "中" if cjk_ratio(row["问题原文"]) >= 0.3 else "英"
    gl = ("中" if cjk_ratio(text) >= 0.1 else "英") if text else "—"
    return {
        "category": cat,
        "recall50": bool(rank_diag),
        "rank50": rank_diag,
        "rank_diag": rank_diag,
        "chan": chan,
        "probe": probe,
        "cross": cross,
        "xling_off": xling_off,
        "note": "；".join(note),
        "seg_chars": len(text) if text else None,
        "seg_pos": seg_position(row["问题原文"], text),
        "q_lang": ql,
        "g_lang": gl,
        "cell": f"{ql}→{gl}" if gl != "—" else "—",
    }


CATS = ["命中", "在某路候选，融合后掉出前5", "进前10但被跨语言规则顶出前5", "不在任何一路候选", "无料"]
BUCKETS = ["1", "2-5", "6-10", "11-20", "21-50", "不在前50"]


def bucket_of(rank):
    if rank is None:
        return "不在前50"
    if rank == 1:
        return "1"
    if rank <= 5:
        return "2-5"
    if rank <= 10:
        return "6-10"
    if rank <= 20:
        return "11-20"
    return "21-50"


def deep_stats(rows):
    scored = [r for r in rows if r["期望"] == "命中"]
    deep = [r["deep"] for r in scored if r.get("deep")]
    cats = {c: 0 for c in CATS}
    for d in deep:
        cats[d["category"]] = cats.get(d["category"], 0) + 1
    buckets = {b: 0 for b in BUCKETS}
    for d in deep:
        buckets[bucket_of(d["rank_diag"])] += 1
    hit5 = sum(1 for r in scored if r["rank"] and r["rank"] <= 5)
    hit50 = sum(1 for d in deep if d["recall50"])
    cells = {}
    for d in deep:
        cells.setdefault(d["cell"], [0, 0])
        cells[d["cell"]][0] += 1
        if d["rank_diag"]:
            cells[d["cell"]][1] += 1
    lens = [d["seg_chars"] for d in deep if d["seg_chars"]]
    bins = {"<200": 0, "200-400": 0, "400-800": 0, "800-1500": 0, ">1500": 0}
    for n in lens:
        bins[len_bin(n)] += 1
    return {
        "n": len(scored), "cats": cats, "buckets": buckets,
        "r5": (hit5 / len(scored)) if scored else None,
        "r50": (hit50 / len(deep)) if deep else None,
        "cells": cells,
        "len_bins": bins,
        "len_med": (sorted(lens)[len(lens) // 2] if lens else None),
        "len_n": len(lens),
        "pos": {p: sum(1 for d in deep if d["seg_pos"] == p)
                for p in ("段首", "段中", "段尾", "未匹配")},
        "deep": deep,
    }


def len_bin(n):
    if n is None:
        return None
    if n < 200:
        return "<200"
    if n < 400:
        return "200-400"
    if n < 800:
        return "400-800"
    if n < 1500:
        return "800-1500"
    return ">1500"


# ---------------------------------------------------------------- 统计

def pct(x):
    return "—" if x is None else f"{x * 100:.1f}%"


def group_stats(rows):
    scored = [r for r in rows if r["期望"] == "命中"]
    no_material = [r for r in rows if r["期望"] == "无料"]
    n = len(scored)
    hit5 = sum(1 for r in scored if r["rank"] and r["rank"] <= 5)
    hit10 = sum(1 for r in scored if r["rank"] and r["rank"] <= 10)
    mrr = sum((1.0 / r["rank"]) for r in scored if r["rank"] and r["rank"] <= 10)
    origin5 = sum(1 for r in scored if r["origin5"])
    origin_rows = [r for r in scored if r["gold_is_origin"]]
    origin_hit5 = sum(1 for r in origin_rows if r["origin5"])
    return {
        "n": len(rows),
        "n_scored": n,
        "recall5": (hit5 / n) if n else None,
        "recall10": (hit10 / n) if n else None,
        "mrr": (mrr / n) if n else None,
        "origin5_all": (origin5 / n) if n else None,
        "origin_gold_n": len(origin_rows),
        "origin_gold_rate": (origin_hit5 / len(origin_rows)) if origin_rows else None,
        "origin_gold_share": (len(origin_rows) / n) if n else None,
        "n_no_material": len(no_material),
        "good_refuse": sum(1 for r in no_material if r["empty"]),
        "avg_time": (sum(r["elapsed"] for r in rows) / len(rows)) if rows else None,
        "empty_rows": [r for r in scored if r["empty"]],
        "miss_rows": [r for r in scored if not r["rank"]],
        "full": len(rows) >= FULL_GROUP,
    }


def verdict(groups, all_stats):
    fails = []
    non_empty_scored = [r for g in groups for r in g["rows"] if r["期望"] == "命中"]
    empty = [r for r in non_empty_scored if r["empty"]]
    if empty:
        fails.append(f"规则1 空结果：{len(empty)} 道非无料题返回空结果（{'、'.join(r['题号'] for r in empty)}）")
    if all_stats["recall5"] is None or all_stats["recall5"] < PASS_RECALL5:
        fails.append(f"规则2 总 Recall@5 {pct(all_stats['recall5'])} < {pct(PASS_RECALL5)}")
    if all_stats["origin_gold_rate"] is None or all_stats["origin_gold_rate"] < PASS_ORIGIN5:
        fails.append(
            f"规则3 原文命中率（分母=gold为原文的题，n={all_stats['origin_gold_n']}）"
            f" {pct(all_stats['origin_gold_rate'])} < {pct(PASS_ORIGIN5)}")
    for g in groups:
        st = group_stats(g["rows"])
        if st["full"] and (st["recall5"] is None or st["recall5"] < PASS_GROUP_RECALL5):
            fails.append(f"规则4 {g['code']}-{g['name']} Recall@5 {pct(st['recall5'])} < {pct(PASS_GROUP_RECALL5)}")
    bad_no_material = [r for g in groups for r in g["rows"]
                       if r["期望"] == "无料" and (r["无料归因"] not in ATTRS or not r["补料建议"])]
    if bad_no_material:
        fails.append(f"规则5 无料题缺归因/补料建议：{'、'.join(r['题号'] for r in bad_no_material)}")
    return fails


# ---------------------------------------------------------------- 输出

def fmt_rank(r):
    if r["期望"] == "无料":
        return "无料题"
    return f"#{r['rank']}" if r["rank"] else "未召回"


def print_terminal(groups, all_stats, fails):
    print("\n" + "=" * 108)
    print(f"验收结论：{'通过' if not fails else '不通过'}")
    if len(groups) < 12:
        print(f"注：本次只跑了 {len(groups)} 组，结论只对本次子集有效；正式验收要跑全部 12 组。")
    if fails:
        for f in fails:
            print(f"  ✗ {f}")
    print("=" * 108)
    print(f"{'职责':<22}{'题数':>5}{'R@5':>8}{'R@10':>8}{'MRR':>8}{'原文率':>9}{'gold原文占比':>13}"
          f"{'无料':>5}{'拒答':>5}{'平均秒':>8}  本组判定")
    for g in groups:
        st = group_stats(g["rows"])
        gv = (f"暂不作数（本组仅{st['n']}题）" if not st["full"] else (
            "通过" if (st["recall5"] or 0) >= PASS_GROUP_RECALL5 and not st["empty_rows"] else "不通过"))
        print(f"{g['code']}-{g['name']:<18}{st['n']:>5}{pct(st['recall5']):>8}"
              f"{pct(st['recall10']):>8}{(f'{st["mrr"]:.2f}' if st['mrr'] is not None else '—'):>8}"
              f"{pct(st['origin_gold_rate']):>9}{pct(st['origin_gold_share']):>13}"
              f"{st['n_no_material']:>5}{st['good_refuse']:>5}"
              f"{(f'{st['avg_time']:.2f}' if st['avg_time'] else '—'):>8}  {gv}")
    s = all_stats
    print("-" * 108)
    print(f"{'总计':<20}{s['n']:>7}{pct(s['recall5']):>8}{pct(s['recall10']):>8}"
          f"{(f'{s['mrr']:.2f}' if s['mrr'] is not None else '—'):>8}"
          f"{pct(s['origin_gold_rate']):>9}{pct(s['origin_gold_share']):>13}"
          f"{s['n_no_material']:>5}{s['good_refuse']:>5}"
          f"{(f'{s['avg_time']:.2f}' if s['avg_time'] else '—'):>8}")
    print("\n逐题：")
    for g in groups:
        for r in g["rows"]:
            comp = f"原文{r['comp']['原文']}/笔记{r['comp']['笔记']}/经验{r['comp']['经验']}"
            if r["期望"] == "无料":
                mark = "正确拒答" if r["empty"] else "返回了结果(待人工复看)"
                print(f"  {r['题号']} 无料·{mark}  {comp}  {r['elapsed']:.2f}s  {r['问题原文']}")
            else:
                conf = "·低置信" if r["low_conf"] else ""
                print(f"  {r['题号']} 5@{fmt_rank(r)} 10@{('#' + str(r['rank'])) if r['rank'] else '未召回'}"
                      f"{conf}  gold={r['gold路径']} {r['gold段号']}  {comp}  {r['elapsed']:.2f}s  {r['问题原文']}")
    miss = s["miss_rows"]
    print(f"\n补料清单：缺资料 {sum(1 for r in miss if r['无料归因']=='缺资料')} / "
          f"需实测 {sum(1 for r in miss if r['无料归因']=='需实测')} / "
          f"待查 {sum(1 for r in miss if r['无料归因'] not in ('缺资料','需实测'))}（未召回题默认待查）")
    print("详见报告。")


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join(["---"] * len(headers)) + " |"]
    out += ["| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |" for r in rows]
    return "\n".join(out)


def needs_rows(groups):
    """补料清单：已知无料题 + 未召回题，按归因分组。"""
    buckets = {a: [] for a in ATTRS}
    for g in groups:
        for r in g["rows"]:
            if r["期望"] == "无料":
                attr = r["无料归因"]
                buckets[attr].append({
                    "题号": r["题号"], "问题": r["问题原文"], "建议": r["补料建议"],
                    "为什么": ("已知无料" if r["empty"] else
                              "已知无料，但检索返回了结果（需人工复看是否真无料）"),
                })
            elif not r["rank"] and r["n_hits"] == 0:
                attr = r["无料归因"] if r["无料归因"] in ATTRS else "待查"
                default = ("先换同义说法、拆成单词、去掉「怎么/为什么/到底」再问一遍；"
                           "复测仍无命中才改判 缺资料 或 需实测")
                buckets[attr].append({
                    "题号": r["题号"], "问题": r["问题原文"],
                    "gold": f"{r['gold路径']} {r['gold段号']}".strip(),
                    "建议": r["补料建议"] or default,
                    "为什么": r["empty"] and "空结果" or "未召回",
                })
    return buckets


def write_report(groups, all_stats, fails, path):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# A 库检索验收报告 — {now}", ""]
    lines.append(f"## 验收结论：{'通过' if not fails else '不通过'}")
    lines.append("")
    if fails:
        lines.append("未达标项：")
        lines += [f"- {f}" for f in fails]
    else:
        lines.append("- 五项通过线全部满足。")
    if len(groups) < 12:
        lines.append("")
        lines.append(f"> 注：本次只跑了 {len(groups)} 组，结论只对本次子集有效；正式验收要跑全部 12 组。")
    short = [g for g in groups if len(g["rows"]) < FULL_GROUP]
    if short:
        lines.append("")
        lines.append(f"> 注：本报告为骨架基线，{len(short)} 组未满 {FULL_GROUP} 题"
                     f"（{'、'.join(f'{g["code"]} {len(g["rows"])}/{FULL_GROUP}' for g in short)}）。"
                     "按规则，未满组的组级判定暂不作数；总分也仅作基线参考。")
    lines += ["", "## 一、12 项职责 × 各指标", ""]
    table_rows = []
    for g in groups:
        st = group_stats(g["rows"])
        gv = (f"暂不作数（本组仅{st['n']}题）" if not st["full"] else (
            "通过" if (st["recall5"] or 0) >= PASS_GROUP_RECALL5 and not st["empty_rows"] else "不通过"))
        table_rows.append([
            f"{g['code']}-{g['name']}", f"{st['n']}/{FULL_GROUP}", pct(st["recall5"]), pct(st["recall10"]),
            f"{st['mrr']:.2f}" if st["mrr"] is not None else "—", pct(st["origin_gold_rate"]),
            pct(st["origin_gold_share"]), st["n_no_material"], st["good_refuse"],
            f"{st['avg_time']:.2f}" if st["avg_time"] else "—", gv,
        ])
    s = all_stats
    table_rows.append([
        "总计", f"{s['n']}", pct(s["recall5"]), pct(s["recall10"]),
        f"{s['mrr']:.2f}" if s["mrr"] is not None else "—", pct(s["origin_gold_rate"]),
        pct(s["origin_gold_share"]), s["n_no_material"], s["good_refuse"],
        f"{s['avg_time']:.2f}" if s["avg_time"] else "—",
        "通过" if not fails else "不通过",
    ])
    lines.append(md_table(
        ["职责", "题数", "Recall@5", "Recall@10", "MRR", "原文命中率(gold原文)", "gold原文占比",
         "无料题", "无料拒答", "平均耗时(s)", "本组判定"],
        table_rows))
    lines += ["", f"通过线：总 Recall@5 ≥ {pct(PASS_RECALL5)}；"
                  f"原文命中率（分母=gold为原文的题）≥ {pct(PASS_ORIGIN5)}；"
                  f"每组（满 {FULL_GROUP} 题时）Recall@5 ≥ {pct(PASS_GROUP_RECALL5)}；"
                  "非无料题不得返回空结果；无料题不计分但必须有归因与补料建议。",
              "",
              f"两个原文指标：`原文命中率(gold原文)` = gold 为原文的题里，top-5 出现可引原文的比例"
              f"（分母 {s['origin_gold_n']} 题）；`gold原文占比` = 全部计分题里 gold 为原文的比例。"
              "只拿笔记当 gold 的题永远命中不了原文，所以不放进原文命中率的分母。"]
    lines += ["", "## 二、未通过项明细", ""]
    if fails:
        lines += [f"- {f}" for f in fails]
    for g in groups:
        st = group_stats(g["rows"])
        if st["empty_rows"] or st["miss_rows"]:
            lines.append("")
            lines.append(f"### {g['code']}-{g['name']}")
            if st["empty_rows"]:
                lines.append(f"- 空结果：{'、'.join(r['题号'] for r in st['empty_rows'])}")
            if st["miss_rows"]:
                lines.append(f"- 未召回：{'、'.join(r['题号'] for r in st['miss_rows'])}")
            if st["full"] and (st["recall5"] or 0) < PASS_GROUP_RECALL5:
                lines.append(f"- 组 Recall@5 {pct(st['recall5'])} 低于 {pct(PASS_GROUP_RECALL5)}")
    ranking = [r for g in groups for r in g["rows"]
               if r["期望"] == "命中" and not r["rank"] and r["n_hits"] > 0]
    if ranking:
        lines.append("")
        lines.append(f"- 有候选但 gold 未进 top10（排序问题，不进补料清单）："
                     f"{'、'.join(r['题号'] for r in ranking)}")
    if not any(group_stats(g["rows"])["empty_rows"] or group_stats(g["rows"])["miss_rows"] for g in groups):
        lines.append("- 无。")
    lines += ["", "## 三、逐题明细", ""]
    detail = []
    for g in groups:
        for r in g["rows"]:
            comp = f"原文{r['comp']['原文']}/笔记{r['comp']['笔记']}/经验{r['comp']['经验']}"
            if r["期望"] == "无料":
                detail.append([r["题号"], r["问题原文"], "—", "无料", "无料题",
                               "正确拒答" if r["empty"] else "返回结果(待复看)", "不适用",
                               "—", "—", comp, f"{r['elapsed']:.2f}"])
            else:
                detail.append([r["题号"], r["问题原文"], f"{r['gold路径']} {r['gold段号']}",
                               "命中", fmt_rank(r),
                               f"#{r['rank']}" if r["rank"] else "未召回", r["期望能否引原文"],
                               "低" if r["low_conf"] else "高",
                               r["gold_quality"] or "—", comp, f"{r['elapsed']:.2f}"])
    lines.append(md_table(
        ["题号", "问题", "gold", "期望", "top-5", "top-10", "期望引原文", "置信", "gold质量", "top10 来源构成", "耗时(s)"],
        detail))
    lines += ["", "## 四、已知无料题（单列，不计分）", ""]
    nm_rows = []
    for g in groups:
        for r in g["rows"]:
            if r["期望"] == "无料":
                nm_rows.append([r["题号"], r["问题原文"], r["无料归因"], r["补料建议"],
                                "正确拒答" if r["empty"] else "返回结果(待复看)"])
    lines.append(md_table(["题号", "问题", "归因", "补料建议", "检索状态"], nm_rows) if nm_rows else "（无）")
    lines += ["", "## 五、补料清单", "",
              "> 规则：跑分未召回不许直接判「库里没料」。先按 5.3 换词复测；换词仍无命中，"
              "才可在题库里把该题改为「缺资料」或「需实测」，并补一句补料建议。", ""]
    buckets = needs_rows(groups)
    titles = {
        "缺资料": "5.1 缺资料（公开可得但我们没采）",
        "需实测": "5.2 需实测（只有真跑业务才会产生）",
        "待查": "5.3 待查（可能库里有，检索没捞到）",
    }
    for attr in ATTRS:
        lines += [f"### {titles[attr]}", ""]
        items = buckets[attr]
        if not items:
            lines += ["（无）", ""]
            continue
        if attr == "待查":
            lines.append(md_table(["题号", "问题", "gold（已确认在库）", "换哪些问法再试", "复测结论"],
                                  [[i["题号"], i["问题"], i.get("gold", "—"), i["建议"],
                                    "gold 已确认在库，属有料但难捞；待换词复测"] for i in items]))
        else:
            lines.append(md_table(["题号", "问题", "为什么进这张表", "补什么 / 去哪补 / 自动化还是人工"],
                                  [[i["题号"], i["问题"], i["为什么"], i["建议"]] for i in items]))
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------- 深诊断报告

def retrieval_fingerprint():
    """记录本次跑分对应的检索侧版本，避免「改前」「改后」两版对不上号。"""
    bits = []
    for name in ("rag.py", "terms.csv", "synonyms.json"):
        p = RAG_DIR / name
        if p.exists():
            h = hashlib.sha1(p.read_bytes()).hexdigest()[:8]
            mt = datetime.fromtimestamp(p.stat().st_mtime).strftime("%m-%d %H:%M")
            bits.append(f"{name} {mt}/{h}")
    return "；".join(bits)


def write_deep_report(groups, rows, kdiag, path):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    all_d = deep_stats(rows)
    lines = [f"# Gold 名次与四分类诊断 — {now}", "",
             f"- 检索侧快照：{retrieval_fingerprint()}。另一条线正在改检索，"
             "本报告只对应上面这个版本，之后改了什么都要重跑才可比。",
             f"- 口径：每题跑两次 `rag.py search \"<问题>\" -k 10 / -k {kdiag} --json`。"
             f"实测 Recall@5 取 `-k 10`（与验收基线同口径）；候选上界与名次分档都取 `-k {kdiag}`。",
             f"- **名次上限说明**：检索器内部把向量池放大 10 倍（`pool = max(k*10, 50)`）再乘 8 取 KNN，"
             f"sqlite-vec 的 KNN LIMIT 上限是 4096，所以 k 最大只能到 51，k=200 会直接报 "
             f"`k value in knn query too large`。不改 rag.py 就只能探到 50 名这一层，"
             f"所以最后一档是「不在前50」，不再区分 >50 与完全不在候选。",
             "- 每路原始名次：取命中记录里的 `channels` 字段（literal / tag / vector 三路各自的名次）。"
             "gold 不在融合候选里时，再单独跑 `--mode literal` / `--mode tag` 确认是否在某路候选中；"
             "`--mode vector` 目前返回空（`search()` 只在 hybrid 下取向量），所以向量单路无法单独探测。",
             "- 四分类：命中＝融合前 5；在某路候选但掉出前 5＝融合结果里能找到但名次 >5（含被 per_doc 截断、"
             "或只在单路候选中）；被跨语言顶出前 5＝融合进前 10 且该条被标 `cross`（`fuse()` 把 cross 统一排到最后）；"
             "不在任何一路候选＝融合、字面单路、标签单路三处都找不到。",
             "- 段内位置为【推算】：用问句字组在 gold 段里首次出现的位置粗判，不是语义标注。",
             "", "## 一、四分类（按组）", ""]
    t = []
    for g in groups:
        st = deep_stats(g["rows"])
        c = st["cats"]
        t.append([f"{g['code']}-{g['name']}", st["n"], c["命中"], c["在某路候选，融合后掉出前5"],
                  c["进前10但被跨语言规则顶出前5"], c["不在任何一路候选"],
                  sum(1 for r in g["rows"] if r["期望"] == "无料")])
    c = all_d["cats"]
    t.append(["总计", all_d["n"], c["命中"], c["在某路候选，融合后掉出前5"],
              c["进前10但被跨语言规则顶出前5"], c["不在任何一路候选"],
              sum(1 for r in rows if r["期望"] == "无料")])
    lines.append(md_table(["组", "计分题", "命中", "候选内但掉出前5", "跨语言顶出前5", "不在任何一路候选", "无料"], t))

    lines += ["", "## 二、候选上界 vs 实测（两者的差＝排序损失）", ""]
    t = []
    for g in groups:
        st = deep_stats(g["rows"])
        loss = (st["r50"] - st["r5"]) if (st["r50"] is not None and st["r5"] is not None) else None
        t.append([f"{g['code']}-{g['name']}", st["n"], pct(st["r5"]), pct(st["r50"]), pct(loss)])
    loss = (all_d["r50"] - all_d["r5"]) if (all_d["r50"] is not None and all_d["r5"] is not None) else None
    t.append(["总计", all_d["n"], pct(all_d["r5"]), pct(all_d["r50"]), pct(loss)])
    lines.append(md_table(["组", "计分题", f"实测 Recall@5（k=10）", f"候选上界 Recall@{kdiag}", "排序损失"], t))

    lines += ["", f"## 三、gold 名次分档（k={kdiag} 融合候选）", ""]
    t = []
    for g in groups:
        st = deep_stats(g["rows"])
        b = st["buckets"]
        t.append([f"{g['code']}-{g['name']}", st["n"]] + [b[x] for x in BUCKETS])
    b = all_d["buckets"]
    t.append(["总计", all_d["n"]] + [b[x] for x in BUCKETS])
    lines.append(md_table(["组", "计分题", "第1名", "2-5", "6-10", "11-20", "21-50", "不在前50"], t))

    lines += ["", "## 四、06 合规 / 09 流量承接 逐题名次", ""]
    for g in [x for x in groups if x["code"] in ("06", "09")]:
        lines += [f"### {g['code']}-{g['name']}", ""]
        t = []
        for r in g["rows"]:
            if r["期望"] == "无料":
                t.append([r["题号"], r["问题原文"], "—", "—", "—", "—", "—", "—", "无料", "—"])
                continue
            d = r["deep"]
            chan = " ".join(f"{k}#{v}" for k, v in d["chan"].items()) or "—"
            probe = " ".join(f"{k}#{v}" for k, v in d["probe"].items())
            if probe:
                chan = (chan + " / 单路 " + probe).strip(" /")
            rank = f"#{d['rank_diag']}" if d["rank_diag"] else f"不在前{kdiag}"
            t.append([r["题号"], r["问题原文"], f"{r['gold路径']} {r['gold段号']}".strip(),
                      r["gold_type_label"], chan, rank, bucket_of(d["rank_diag"]),
                      d["category"], d["note"] or "—"])
        lines.append(md_table(["题号", "问题", "gold", "类型", "每路名次(路#名次)", "融合名次",
                               "档位", "四分类", "备注"], t))
        lines.append("")

    lines += ["", "## 五、gold 段长分布", ""]
    t = []
    for g in groups:
        st = deep_stats(g["rows"])
        lb = st["len_bins"]
        t.append([f"{g['code']}-{g['name']}", st["len_n"], lb["<200"], lb["200-400"], lb["400-800"],
                  lb["800-1500"], lb[">1500"], st["len_med"] if st["len_med"] is not None else "—"])
    lb = all_d["len_bins"]
    t.append(["总计", all_d["len_n"], lb["<200"], lb["200-400"], lb["400-800"], lb["800-1500"],
              lb[">1500"], all_d["len_med"] if all_d["len_med"] is not None else "—"])
    lines.append(md_table(["组", "有段长", "<200字", "200-400", "400-800", "800-1500", ">1500", "中位数"], t))
    p = all_d["pos"]
    lines += ["", f"答案在 gold 段内的位置（推算）：段首 {p['段首']} / 段中 {p['段中']} / "
                  f"段尾 {p['段尾']} / 未匹配 {p['未匹配']}（共 {all_d['len_n']} 题）。", ""]

    lines += ["## 六、四格（问句语言 → gold 文档语言）", ""]
    t = []
    for cell in ("中→中", "中→英", "英→中", "英→英"):
        n, hit = all_d["cells"].get(cell, [0, 0])
        t.append([cell, n, hit, pct(hit / n) if n else "—"])
    lines.append(md_table(["格", "题数", "gold 进了候选", "候选内占比"], t))
    lines += ["", "> 当前所有问句都是中文，所以实际只有「中→中」「中→英」两格有数；"
                  "「英→中」「英→英」字段照留，等有英文问句再填。"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    csv_path = path.with_name(path.stem.replace("名次分布", "名次明细") + ".csv")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_ALL)
        w.writerow(["题号", "职责", "问题", "gold", "gold类型", "top5名次", "诊断名次",
                    "字面路", "标签路", "向量路", "跨语言", "四分类", "档位", "段长", "段内位置",
                    "问句语言", "gold语言", "备注"])
        for g in groups:
            for r in g["rows"]:
                if r["期望"] == "无料":
                    w.writerow([r["题号"], f"{g['code']}-{g['name']}", r["问题原文"], "", "—",
                                "—", "—", "—", "—", "—", "—", "无料", "无料", "", "", "—", "—", ""])
                    continue
                d = r["deep"]
                w.writerow([r["题号"], f"{g['code']}-{g['name']}", r["问题原文"],
                            f"{r['gold路径']} {r['gold段号']}".strip(), r["gold_type_label"],
                            f"#{r['rank']}" if r["rank"] else "未进前10",
                            f"#{d['rank_diag']}" if d["rank_diag"] else f"不在前{kdiag}",
                            d["chan"].get("literal") or d["probe"].get("literal") or "—",
                            d["chan"].get("tag") or d["probe"].get("tag") or "—",
                            d["chan"].get("vector") or "—",
                            "是" if d["cross"] else "否", d["category"], bucket_of(d["rank_diag"]),
                            d["seg_chars"] if d["seg_chars"] is not None else "—",
                            d["seg_pos"], d["q_lang"], d["g_lang"], d["note"]])
    print(f"明细：{csv_path}")
    return path


# ---------------------------------------------------------------- 主流程

def main():
    ap = argparse.ArgumentParser(description="A 库检索验收：按职责分组跑题库并判定通过/不通过")
    ap.add_argument("--group", action="append", default=[], help="只跑指定组，如 06；可重复")
    ap.add_argument("--no-report", action="store_true", help="只出终端结果，不写报告")
    ap.add_argument("--report", default="", help="报告路径；默认 验收/报告-YYYYMMDD-HHMM.md")
    ap.add_argument("--deep", action="store_true",
                    help="加深诊断：候选上界、gold 名次分档、每路原始名次、四分类、段长分布")
    ap.add_argument("--kdiag", type=int, default=50,
                    help="深诊断的候选深度，默认 50；上限 51（sqlite-vec KNN LIMIT 4096 / k*80）")
    args = ap.parse_args()

    groups, rows = load_questions(args.group)
    if not groups:
        sys.exit(f"没有匹配的组：{args.group}")
    golds = [r["gold路径"] for r in rows if r["期望"] == "命中"]
    index = load_gold_index(golds)
    verify_gold(rows, index)
    texts = load_gold_texts(golds) if args.deep else {}

    print(f"题库：{len(groups)} 组 / {len(rows)} 题；检索入口：{RAG_VENV} rag.py search -k 10 --json")
    for g in groups:
        print(f"  跑 {g['code']}-{g['name']}（{len(g['rows'])} 题）…")
        for r in g["rows"]:
            judged = judge_row(r, index)
            r.clear()
            r.update(judged)
            if args.deep:
                r["deep"] = deep_row(r, texts, args.kdiag)

    all_stats = group_stats(rows)
    fails = verdict(groups, all_stats)
    print_terminal(groups, all_stats, fails)

    if args.deep:
        d = deep_stats(rows)
        c = d["cats"]
        print("\n" + "=" * 108)
        print(f"四分类：命中 {c['命中']} / 候选内但掉出前5 {c['在某路候选，融合后掉出前5']} / "
              f"跨语言顶出前5 {c['进前10但被跨语言规则顶出前5']} / 不在任何一路候选 {c['不在任何一路候选']}")
        print(f"候选上界 Recall@{args.kdiag} {pct(d['r50'])}　实测 Recall@5 {pct(d['r5'])}"
              f"　排序损失 {pct((d['r50'] - d['r5']) if (d['r50'] is not None and d['r5'] is not None) else None)}")
        lb = d["len_bins"]
        print(f"gold 段长：中位数 {d['len_med']} 字；"
              + " / ".join(f"{k} {v}" for k, v in lb.items())
              + f"；段内位置 段首 {d['pos']['段首']} / 段中 {d['pos']['段中']} / "
                f"段尾 {d['pos']['段尾']} / 未匹配 {d['pos']['未匹配']}")
        path = HERE / f"名次分布-{datetime.now():%Y%m%d-%H%M}.md"
        write_deep_report(groups, rows, args.kdiag, path)
        print(f"名次分布报告：{path}")

    if not args.no_report:
        path = Path(args.report) if args.report else HERE / f"报告-{datetime.now():%Y%m%d-%H%M}.md"
        write_report(groups, all_stats, fails, path)
        print(f"\n报告：{path}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
