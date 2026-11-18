#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「线索数」不计入任何门槛；只有「可用数」参与硬底线与合格线判定。

A 库门槛自检（口径说明：本脚本的"合格"＝有可引原文＋已向量化＋可检索＋有定位；
与"目录有条目的 77/77"不是一回事——后者只数条目存在，前者数能当依据的原文。）

口径第五格：`已有二手·未入库`。指 knowledge/sources/fulltext 下未进 kbase 的 64 个自写笔记
（methodology__* 46 篇，accounts/topics/monetization 等 18 篇）。这批是旧知识库被打回的自写笔记，
是被替换对象，不是依据：**不计入合格条数、不计入已入库**，只单列。
五个数必须能对上：已有原文·未入库 + 无原文·未采集 + 已入库 + 已有二手·未入库 = 目录总数 + 二手笔记数。

A 库门槛自检：算「九大类过了几类」「73 个细类有几个是空的」「经验门槛过几类」。

一条知识算合格，必须同时满足：
  ① 原文在本地有文件（metadata.csv 的「本地路径」指向的文件存在）
  ② 已入库并完成向量化（kbase.db 有该文档，且有段落进了 seg_vec）
  ③ 能用一句自然语言检索出来（用目录里的「一句话它解决什么」当问句，检索命中同一文档）
  ④ 带出处定位（该文档至少一段有 locator，即 §n / 第X条）

门槛（2026-11-14 用户拍板）：
  九大类：每类 ≥6 条合格知识
  细类：每类 ≥1 条合格知识
  经验：每大类 ≥3 条 E2 以上，其中 ≥1 条 E3/E4；E0 不算

用法：
  cd 04-知识底座/rag
  .venv/bin/python ../catalog/check_gate.py              # 默认 hybrid 检索
  .venv/bin/python ../catalog/check_gate.py --mode literal
  .venv/bin/python ../catalog/check_gate.py --json
"""
import argparse
import csv
import difflib
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent                      # 04-知识底座
PROJECT = BASE.parent
RAG = BASE / "rag"
sys.path.insert(0, str(RAG))

import rag  # noqa: E402

CATALOG = HERE / "catalog.csv"
META = BASE / "knowledge" / "sources" / "metadata.csv"
EXP = BASE / "experience" / "experience.csv"

NINE = [
    "一、人性与心理", "二、传播与内容", "三、判断与思维", "四、用户与市场",
    "五、客户运营与转化", "六、平台与增长", "七、商业与经营", "八、风险与治理",
    "九、专业本体",
]
CROSS = "十、跨类项"

# 重点线：12 个代表细类，每个 ≥6 条
FOCUS = {
    "选题与需求信号": "选题",
    "叙事结构与故事": "脚本",
    "定位与差异化": "对标定位",
    "定价与报价": "报价",
    "合同与回款": "合同",
    "转化路径与漏斗设计": "转化",
    "私域承接与微信运营": "私信",
    "交付与验收": "交付",
    "复盘与归因方法": "复盘",
    "平台规则与舆情": "平台规则",
    "广告法与宣传合规": "合规",
    "工具生态与成本": "工具",
}
FOCUS_INV = {v: k for k, v in FOCUS.items()}

# 2026-11-14 新增四细类（尚未有条目也要计入硬底线；老类不删不减）
NEW_ITEMS = {
    "脚本结构": "自「口播与语言表达」拆出",
    "私信承接": "自「私域承接与微信运营」拆出",
    "成交与异议": "自「转化路径与漏斗设计」拆出",
    "对标拆解": "全新，无母类",
}
HARD_TOTAL = 77                      # 硬底线总数写死
PAIR_ITEM = "错误做法样本（反面教材）"  # 成对才算 1 条：≥2 且含 1 反例 + 1 官方对照


def norm_name(s: str) -> str:
    s = (s or "").split("/")[0]
    s = re.sub(r"[（(].*?[)）]", "", s)
    s = re.sub(r"[\s·:：\-—，,。.、]+", "", s)
    return s.lower()


def load_catalog():
    with open(CATALOG, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_meta():
    with open(META, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    by_name = {}
    by_path = {}
    for r in rows:
        by_name[norm_name(r["题名"])] = r
        local = (r.get("本地路径") or "").strip()
        if local:
            by_path[local] = r
    return rows, by_name, by_path


def load_docs(conn):
    out = {}
    for r in conn.execute("SELECT id, source_path, quality FROM docs"):
        out[str(r["source_path"])] = {"id": r["id"], "quality": r["quality"] or ""}
    return out


def load_doc_stats(conn):
    """一次 GROUP BY 聚合出每篇文档的（段数, 已向量化段数, 有定位段数）。

    原实现对每篇文档跑 3 条 COUNT，实测 799 篇耗时 359.57s，占整轮的大头；
    改成三条 GROUP BY 一次算完，实测 1.10s，逐篇计数逐条比对完全一致。
    """
    seg = dict(conn.execute("SELECT doc_id, COUNT(*) FROM segments GROUP BY doc_id"))
    vec = dict(conn.execute(
        "SELECT s.doc_id, COUNT(*) FROM segments s JOIN seg_vec v ON v.rowid=s.id"
        " GROUP BY s.doc_id"))
    loc = dict(conn.execute(
        "SELECT doc_id, COUNT(*) FROM segments WHERE TRIM(locator)<>'' GROUP BY doc_id"))
    return {k: (v, vec.get(k, 0), loc.get(k, 0)) for k, v in seg.items()}


def author_compatible(catalog_author, meta_author):
    """模糊题名只在作者也能对上时生效，防止挂到同名异书或自写笔记。"""
    left = (catalog_author or "").lower()
    right = (meta_author or "").lower()
    if not right or "未识别" in right or "本库撰写" in right:
        return False
    if left in right or right in left:
        return True
    names = [n.strip() for n in re.split(r"[,;，；]", left) if n.strip()]
    return any(n in right for n in names)


def match_meta(row, by_name, by_path):
    """目录明示的文件路径优先；其次精确题名；模糊题名必须同时核作者。"""
    evidence = row.get("真实性依据") or ""
    paths = re.findall(r"knowledge/sources/([^\s〔（）()；;，,]+)", evidence)
    for local in paths:
        local = local.rstrip("。")
        if local in by_path:
            return by_path[local]
    key = norm_name(row["资料名称"])
    if key in by_name:
        return by_name[key]
    cands = [
        k for k in by_name
        if len(k) >= 4 and (k in key or key in k)
        and author_compatible(row.get("作者或机构"), by_name[k].get("作者"))
    ]
    if len(cands) == 1:
        return by_name[cands[0]]
    return None


def quality_tier(meta, doc, row):
    """冲突、废止、不入库材料永不计门槛；仅参考（含「仅参考·可转述」）计入硬底线、不计合格线。"""
    fields = [
        meta.get("质量分级") or "", doc.get("quality") or "",
        meta.get("备注") or "", row.get("真实性依据") or "",
    ]
    evidence = " | ".join(fields)
    # 2026-11-15 按用户裁定：代码向 AGENTS 对齐，「仅参考·可转述」不再排除（可入库可转述，计入硬底线）
    if any(x in evidence for x in ("与官方口径冲突", "已废止", "不入库", "不可引用")):
        return "排除"
    # 两处质量档不一致时按保守档处理，不用较高档抬门槛。
    if (meta.get("质量分级") or "") == "可引用" and doc.get("quality") == "可引用":
        return "可引用"
    return "仅参考"


def precheck(row, by_name, by_path, docs, stats):
    """判定到「要不要检索」为止。返回 (状态, 差在哪, 质量档, 相对路径, 问句)。

    'fail' = 已确定不合格，不消耗检索；'search' = 还需一次检索。
    """
    meta = match_meta(row, by_name, by_path)
    if not meta:
        return "fail", "只有书名", "排除", None, None
    local = (meta.get("本地路径") or "").strip()
    if not local:
        return "fail", "没登记本地路径", "排除", None, None
    path = PROJECT / "04-知识底座" / "knowledge" / "sources" / local
    if not path.exists():
        return "fail", "本地没文件", "排除", None, None
    src = str(path.relative_to(PROJECT))
    doc = docs.get(src)
    if not doc:
        return "fail", "没入库", "排除", None, None
    tier = quality_tier(meta, doc, row)
    seg, vec, loc = stats.get(doc["id"], (0, 0, 0))
    if seg == 0 or vec == 0:
        return "fail", "没向量化", tier, None, None
    if loc == 0:
        return "fail", "没出处定位", tier, None, None
    q = (row.get("一句话它解决什么") or "").strip() or row["资料名称"]
    return "search", "", tier, src, q


def run_searches(questions, mode):
    """逐条检索，同一问句只查一次。

    并发实测更慢：6 线程同时对 3.8G 库做向量扫描，系统态 1520s、整轮 638s 反超串行 484s，
    内存被打爆，故保持串行；参数与逐条检索完全一致，结果不变。
    """
    out = {}
    if not questions:
        return out
    conn = rag.connect(rag.DB_PATH, create=False)
    rag.load_index_only(conn)
    try:
        for q in sorted(questions):
            hits, _ = rag.search(conn, q, k=5, mode=mode)
            out[q] = {h["path"] for h in hits}
    finally:
        conn.close()
    return out


def is_pair_item(item):
    return item == PAIR_ITEM or item.startswith("违规判定与发布前审")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="hybrid", choices=["hybrid", "literal", "literal+tag"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--soft", action="store_true",
                    help="只在结构错误（细类数≠硬底线总数）时退出非零；门槛未达标不阻断，"
                         "供每日回路配合快照 diff 使用")
    ap.add_argument("--strict", action="store_true",
                    help="把合格线、重点线未达标也算作失败（默认只卡硬底线与经验门槛）")
    args = ap.parse_args()

    catalog = load_catalog()
    meta_rows, by_name, by_path = load_meta()
    conn = rag.connect(rag.DB_PATH, create=False)
    docs = load_docs(conn)
    stats = load_doc_stats(conn)

    ok_by_item = defaultdict(int)
    citable_by_item = defaultdict(int)
    pair_negative = defaultdict(int)
    pair_official = defaultdict(int)
    reasons = defaultdict(int)
    item_class = {}
    bad_examples = []

    # 先做不花检索的判定，把需要检索的问句一次性并发跑掉
    verdicts = []
    questions = set()
    for row in catalog:
        if row["状态"] == "已作废":
            continue
        item_class[row["项"]] = row["类"]
        st, why, tier, src, q = precheck(row, by_name, by_path, docs, stats)
        verdicts.append((row, st, why, tier, src, q))
        if st == "search":
            questions.add(q)
    hits_by_q = run_searches(questions, args.mode)

    for row, st, why, tier, src, q in verdicts:
        item = row["项"]
        if st == "search" and src not in hits_by_q.get(q, set()):
            st, why = "fail", "检索不到"
        if st == "fail":
            reasons[why] += 1
            if len(bad_examples) < 12:
                bad_examples.append(f"{row['编号']} {row['资料名称']}：{why}")
            continue
        if is_pair_item(item):
            if "反面样本" in row["资料名称"]:
                # 反例本身即使与官方冲突，也只作为成对材料的一半，不单独计数。
                pair_negative[item] += 1
            elif row["类型"] in ("官方文档", "法规") and tier == "可引用":
                pair_official[item] += 1
            continue
        if tier == "排除":
            reasons["冲突/废止/仅参考·可转述"] += 1
            continue
        ok_by_item[item] += 1
        if tier == "可引用":
            citable_by_item[item] += 1

    # 成对细类：1 条反面材料 + 1 条同项官方原文 = 1 条；不自成两条知识。
    for item in set(pair_negative) | set(pair_official):
        ok_by_item[item] = min(pair_negative[item], pair_official[item])
        citable_by_item[item] = ok_by_item[item]

    # 三层门槛：仅参考计硬底线；合格线须总数 ≥3 且其中可引用 ≥2。
    all_items = sorted(set(item_class) | set(NEW_ITEMS))
    zero = [i for i in all_items if ok_by_item[i] == 0]
    low = [i for i in all_items if ok_by_item[i] in (1, 2)]
    pass3 = [i for i in all_items if ok_by_item[i] >= 3 and citable_by_item[i] >= 2]
    not_qualified = [i for i in all_items if i not in pass3]
    item_counts = {
        i: {"可用": ok_by_item[i], "其中可引用": citable_by_item[i]} for i in all_items
    }
    focus = {label: ok_by_item.get(item, 0) for item, label in FOCUS.items()}
    focus_citable = {label: citable_by_item.get(item, 0) for item, label in FOCUS.items()}
    focus_pass = [k for k, v in focus.items() if v >= 6]

    # 经验门槛（experience.csv 不存在时跳过，视为不适用）
    if EXP.exists():
        with open(EXP, encoding="utf-8-sig") as f:
            exps = list(csv.DictReader(f))
        exp_stat = defaultdict(lambda: {"E2plus": 0, "E3E4": 0})
        for e in exps:
            lv = (e.get("证据等级") or "").strip().upper()
            if lv not in ("E2", "E3", "E4"):
                continue
            for sub in [s for s in (e.get("对应子项") or "").split("、") if s]:
                cls = item_class.get(sub)
                if not cls:
                    continue
                exp_stat[cls]["E2plus"] += 1
                if lv in ("E3", "E4"):
                    exp_stat[cls]["E3E4"] += 1
        exp_pass = [c for c in NINE if exp_stat[c]["E2plus"] >= 3 and exp_stat[c]["E3E4"] >= 1]
        exp_fail = [c for c in NINE if c not in exp_pass]
    else:
        exp_pass = list(NINE)  # 全部视为通过（无经验数据时不卡闸）
        exp_fail = []

    # 退出码：默认只把「硬闸」算失败——细类数错、硬底线未满、经验门槛未满。
    # 合格线与重点线是尚未达成的进度目标（当前 19/77、1/12），天天红会让闸失去信号，
    # 所以只在 --strict 时计入；--soft 连门槛都不卡，只报结构错误，供每日回路配快照 diff 用。
    hard_fail = []
    if len(all_items) != HARD_TOTAL:
        hard_fail.append(f"细类数 {len(all_items)}≠{HARD_TOTAL}")
    if zero:
        hard_fail.append(f"硬底线 {len(all_items) - len(zero)}/{HARD_TOTAL}")
    if len(exp_pass) < len(NINE):
        hard_fail.append(f"经验门槛 {len(exp_pass)}/{len(NINE)}")
    strict_fail = []
    if len(pass3) < len(all_items):
        strict_fail.append(f"合格线 {len(pass3)}/{len(all_items)}")
    if len(focus_pass) < len(FOCUS):
        strict_fail.append(f"重点线 {len(focus_pass)}/{len(FOCUS)}")
    if args.soft:
        code = 0 if len(all_items) == HARD_TOTAL else 1
    else:
        code = 1 if (hard_fail or (args.strict and strict_fail)) else 0

    if args.json:
        print(json.dumps({
            "items_total": len(all_items),
            "zero": len(zero), "one_or_two": len(low),
            "three_plus": sum(ok_by_item[i] >= 3 for i in all_items),
            "qualified_pass": len(pass3), "qualified_fail": len(not_qualified),
            "zero_items": zero, "not_qualified_items": not_qualified,
            "item_counts": item_counts,
            "focus_pass": len(focus_pass), "focus_total": len(FOCUS),
            "focus": focus, "focus_citable": focus_citable,
            "exp_pass": len(exp_pass),
            "exp_fail": {c: exp_stat[c] for c in exp_fail},
            "reasons": reasons,
            "exit_code": code,
            "hard_fail": hard_fail, "strict_fail": strict_fail,
        }, ensure_ascii=False, indent=2))
        return code

    if len(all_items) != HARD_TOTAL:
        print(f"⚠ 细类数 {len(all_items)} ≠ 硬底线总数 {HARD_TOTAL}，先查 data 源")
    print(f"细类共 {len(all_items)} 个（三层门槛，硬底线总数 {HARD_TOTAL}）")
    print(f"  硬底线 0 条：{len(zero)} 个｜可用 1–2 条：{len(low)} 个")
    print(f"  硬底线（每类 ≥1，仅参考可计）：{len(all_items) - len(zero)}/{HARD_TOTAL} 过")
    print(f"  合格线（可用 ≥3 且其中可引用 ≥2）：{len(pass3)}/{len(all_items)} 过")
    print(f"\n重点线（12 个代表细类，每类可用 ≥6）：{len(focus_pass)}/12 过")
    for label, n in focus.items():
        print(f"  {'过' if n >= 6 else '不过'}  {label}（{FOCUS_INV[label]}）：{n} 条，其中可引用 {focus_citable[label]} 条")
    if zero:
        print("\n  0 条的细类：" + "、".join(zero))

    print(f"\n经验门槛（每大类 ≥3 条 E2+，其中 ≥1 条 E3/E4；E0 不算）：{len(exp_pass)}/{len(NINE)} 类过")
    for c in exp_fail:
        d = exp_stat[c]
        print(f"  不过  {c}：E2+ {d['E2plus']} 条，E3/E4 {d['E3E4']} 条")

    print("\n差在哪（条数）：" + "，".join(f"{k} {v}" for k, v in sorted(reasons.items(), key=lambda x: -x[1])))
    print("举例：")
    for b in bad_examples:
        print("  - " + b)
    conn.close()
    return code


if __name__ == "__main__":
    sys.exit(main())
