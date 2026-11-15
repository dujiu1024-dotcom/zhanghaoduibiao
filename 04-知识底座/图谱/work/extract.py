#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识图谱构建脚本。

用法：
    python3 extract.py            # 重新扫描知识库，生成 graph.json + index.html
    python3 extract.py --ack      # 复核完变更后，把当前文档指纹记为「已复核」
    python3 extract.py --check    # 只做校验与差异报告，不写文件

它做五件事：
1. 扫描 knowledge/ 下所有 .md，记录路径、最后修改时间、内容指纹；
2. 校验 curated_nodes.py 里的节点与边（端点存在、类型合法、动作有无关联）；
3. 补齐六层「应有清单」里没有对应节点的占位节点（status=expected）；
4. 比对上一次 graph.json，报出新增节点与「文档改过但节点没复核」的条目；
5. 渲染单文件网页。
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # 04-知识底座/图谱
OUT = ROOT                              # graph.json / index.html 直接放在图谱目录
KB = ROOT.parent / "knowledge"          # 04-知识底座/knowledge
GRAPH_JSON = OUT / "graph.json"
INDEX_HTML = OUT / "index.html"
TEMPLATE = HERE / "template.html"
REVIEWED = HERE / "reviewed.json"
PROPOSALS = HERE / "proposals.json"

sys.path.insert(0, str(HERE))
import curated_nodes as C               # noqa: E402
import expected as E                    # noqa: E402
import evidence_map as EV               # noqa: E402

STATUSES = {"supported", "mentioned", "missing", "unverified", "expected", "na"}

# 五层知识维度（L1 知识 / L2 战略 / L3 战术 / L4 方法论 / L5 工具），按文档归属
DIM_LABELS = {
    "k1": "L1 知识", "k2": "L2 战略", "k3": "L3 战术", "k4": "L4 方法论", "k5": "L5 工具",
}
DIM_OVERRIDE = {
    "model-review-8col": "k5", "a-review-8col": "k5", "a-review-order": "k5",
    "a-trigger-adjust": "k5", "a-quote-onepager": "k5", "a-dm-log": "k5",
    "a-own-baseline": "k5", "a-weekly-review": "k5", "a-publish-sop": "k4",
    "a-takeorder-sop": "k4", "m-homepage-3s": "k5",
}


def dim_of(doc: str) -> str:
    for prefix, dim in (("methodology/L4-", "k4"), ("methodology/L3-", "k3"),
                        ("methodology/L2-", "k2"), ("methodology/L1-", "k1"),
                        ("methodology/制作-02", "k4"), ("methodology/制作-01", "k1"),
                        ("methodology/经营-", "k2"), ("methodology/00-", "k2"),
                        ("methodology/01-", "k1"), ("methodology/02-", "k1"),
                        ("methodology/03-", "k1"),
                        ("methodology/公开内容边界", "k3"), ("methodology/抽样", "k4"),
                        ("methodology/理论到操盘", "k5"), ("topics/选题库", "k3"),
                        ("topics/方向备选", "k2"), ("accounts/", "k1"),
                        ("monetization/", "k2")):
        if doc.startswith(prefix):
            return dim
    return "k1"

GENERIC_HEADINGS = {
    "一句话结论", "关联", "目录", "更新", "修订记录", "素材", "局限", "使用",
    "字段说明", "怎么写一条", "条目", "当前缺口", "本轮新增交付物", "当前采集通道",
    "命名与链接规则", "更新纪律", "状态词表", "平台覆盖", "账号清单", "分析分区",
    "为什么这条边界必须硬", "自检", "填表要求", "共性结论（可迁移）", "不能确认的部分",
    "逐条要点（只看形式）", "汇总表", "规范", "背景", "原则", "要解决的问题",
    "挂哪些理论", "必须做的动作", "怎么判断成了", "最常见的死法", "这层不成立时",
    "层与层之间的传导", "自检：现有理论的挂载位置 / 孤岛清单", "一句话",
    "反常类型", "方向备选与切换判据", "一、判「抖音不认」的四个指标",
}


def sha1_of(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts).astimezone().isoformat(timespec="seconds")


def norm(s: str) -> str:
    s = re.sub(r"^[#>\-\*\s\d\.、]+", "", s)
    s = re.sub(r"[（(].*?[)）]", "", s)
    s = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]", "", s)
    return s.strip().lower()


def scan_docs():
    docs = {}
    for p in sorted(KB.rglob("*.md")):
        rel = p.relative_to(KB).as_posix()
        st = p.stat()
        docs[rel] = dict(path=rel, mtime=iso(st.st_mtime), sha1=sha1_of(p),
                         size=st.st_size, text=p.read_text(encoding="utf-8", errors="replace"))
    return docs


def headings_of(text: str):
    out = []
    for line in text.splitlines():
        m = re.match(r"^(#{2,3})\s+(.+?)\s*$", line)
        if m:
            title = m.group(2).strip()
            if len(norm(title)) >= 2 and title not in GENERIC_HEADINGS:
                out.append(title)
    return out


def build(dry_run=False):
    docs = scan_docs()
    prev = {}
    if GRAPH_JSON.exists():
        try:
            for n in json.loads(GRAPH_JSON.read_text(encoding="utf-8"))["nodes"]:
                prev[n["id"]] = n
        except Exception as exc:                       # noqa: BLE001
            print(f"! 读取上一次 graph.json 失败，按首次运行处理：{exc}")
    reviewed = {}
    if REVIEWED.exists():
        reviewed = json.loads(REVIEWED.read_text(encoding="utf-8"))

    nodes, errors, warnings = [], [], []

    # ---------- 1. 人工节点 ----------
    for raw in C.NODES + C.LAYERS:
        n = dict(raw)
        n.setdefault("type", "layer")
        n.setdefault("status", "supported")
        n.setdefault("note", "")
        n.setdefault("label", n.get("name", ""))
        doc = n.get("doc", "")
        meta = docs.get(doc)
        if doc and not meta:
            errors.append(f"节点 {n['id']} 的 doc 不存在：{doc}")
            meta = None
        n["doc_mtime"] = meta["mtime"] if meta else ""
        n["doc_sha1"] = meta["sha1"] if meta else ""
        ev, ev_note = EV.OVERRIDES.get(n["id"], (EV.DEFAULT.get(n["type"], "sourced"), ""))
        n["evidence"] = ev
        n["evidence_note"] = ev_note
        n["dim"] = DIM_OVERRIDE.get(n["id"], dim_of(doc))
        if n["status"] not in STATUSES:
            errors.append(f"节点 {n['id']} 的 status 非法：{n['status']}")
        old = prev.get(n["id"])
        if not reviewed.get(doc):
            n["review_state"] = "待复核" if old and old.get("doc_sha1") != n["doc_sha1"] else (
                "首次" if not old else "已确认")
        else:
            n["review_state"] = "已复核" if reviewed.get(doc) == n["doc_sha1"] else "待复核"
        nodes.append(n)

    ids = {n["id"] for n in nodes}
    if len(ids) != len(nodes):
        dup = sorted({n["id"] for n in nodes if [x["id"] for x in nodes].count(n["id"]) > 1})
        errors.append(f"节点 id 重复：{dup}")

    # ---------- 2. 应有清单 -> 占位节点 ----------
    covered_slots, placeholders = [], []
    for slot in E.EXPECTED:
        if any(cid in ids for cid in slot.get("covered_by", [])):
            covered_slots.append(slot["id"])
            continue
        pid = "ph-" + slot["id"]
        partial = [p for p in slot.get("partial", []) if p in ids]
        nodes.append(dict(
            id=pid, label=slot["label"], type=slot["type"], layer=slot["layer"],
            status="expected",
            definition="六层主干里应该有、但知识库还没有对应内容：" + slot["why"],
            citation="", doc="", section="应有清单", doc_mtime="", doc_sha1="",
            note=slot["why"], expected_slot=slot["id"], partial=partial,
            review_state="占位", evidence="none", evidence_note="应有但没有对应内容。",
            dim="k2",
        ))
        placeholders.append(pid)

    ids = {n["id"] for n in nodes}

    # ---------- 3. 边 ----------
    edges, seen = [], set()

    def add(src, dst, typ, note=""):
        if src not in ids or dst not in ids:
            errors.append(f"边端点不存在：{src} -[{typ}]-> {dst}")
            return
        key = (src, dst, typ)
        if key in seen:
            return
        seen.add(key)
        edges.append(dict(id=f"e{len(edges) + 1}", source=src, target=dst, type=typ, note=note))

    for n in nodes:
        if n["type"] == C.THEORY and n.get("layer"):
            add(n["id"], n["layer"], "belongs", "归属依据：六层主干 / 理论到操盘动作映射表")
    for src, dst, note in C.DRIVES:
        add(src, dst, "drives", note)
    for src, dst, note in C.MEASURES:
        add(src, dst, "measures", note)
    for src, dst, note in C.REFERENCES:
        add(src, dst, "cites", note)
    for src, dst, note in C.DEPENDS:
        add(src, dst, "depends", note)

    # ---------- 4. 统计 ----------
    layer_stats = {}
    for layer in C.LAYERS:
        layer_stats[layer["id"]] = dict(
            theory=0, action=0, metric=0,
            missing=0, unverified=0, expected=0, na=0, total=0,
            evidence={k: 0 for k in EV.EVIDENCE})
    for n in nodes:
        if n["type"] == "layer":
            continue
        lid = n.get("layer")
        if lid not in layer_stats:
            continue
        st = layer_stats[lid]
        st["total"] += 1
        if n["type"] in ("theory", "action", "metric"):
            st[n["type"]] += 1
        st["evidence"][n.get("evidence", "sourced")] += 1
        if n["status"] == "expected":
            st["expected"] += 1
            st["missing"] += 1
        elif n["status"] == "missing":
            st["missing"] += 1
        elif n["status"] == "mentioned":
            st["missing"] += 1
        elif n["status"] == "na":
            st["na"] += 1
        elif n["status"] == "unverified":
            st["unverified"] += 1

    deg = {}
    for e in edges:
        deg[e["source"]] = deg.get(e["source"], 0) + 1
        deg[e["target"]] = deg.get(e["target"], 0) + 1
    for n in nodes:
        if n["status"] == "expected":
            continue
        if n["type"] == "action" and not deg.get(n["id"]):
            warnings.append(f"动作节点没有任何边：{n['label']}（{n['id']}）")
        if n["type"] == "theory" and deg.get(n["id"], 0) == 0:
            warnings.append(f"理论节点没有任何边：{n['label']}（{n['id']}）")

    status_counts, type_counts = {}, {}
    for n in nodes:
        type_counts[n["type"]] = type_counts.get(n["type"], 0) + 1
        status_counts[n["status"]] = status_counts.get(n["status"], 0) + 1

    # ---------- 5. 差异 / 缺文档 ----------
    new_nodes = [n for n in nodes if n["id"] not in prev]
    gone_nodes = [prev[i] for i in prev if i not in ids]
    stale_docs = {}
    for n in nodes:
        if n["doc"] and n["review_state"] == "待复核":
            stale_docs.setdefault(n["doc"], []).append(n["id"])

    indexed = {"README.md", "INDEX.md", "methodology/README.md", "topics/README.md",
               "monetization/README.md", "attachments/README.md",
               "methodology/00-知识覆盖矩阵.md", "methodology/L1-无数据支撑清单.md"}
    has_node = {}
    for n in nodes:
        if n["doc"]:
            has_node[n["doc"]] = has_node.get(n["doc"], 0) + 1
    uncovered = [d for d in docs if d not in has_node and d not in indexed
                 and not d.startswith("_templates/") and not d.startswith("attachments/")
                 and not d.startswith("accounts/")]

    labels_norm = [norm(n["label"]) for n in nodes if n["status"] != "expected"]
    candidates = []
    for d, meta in docs.items():
        if not (d.startswith("methodology/") or d.startswith("topics/") or d.startswith("monetization/")):
            continue
        # 只对「新进来、还没抽过」的文档提候选；已经抽透的文档不再刷屏
        if has_node.get(d, 0) >= 3:
            continue
        for h in headings_of(meta["text"]):
            hh = norm(h)
            if not hh:
                continue
            if any(hh and (hh in ln or ln in hh) for ln in labels_norm):
                continue
            candidates.append(dict(doc=d, heading=h, kind="未匹配的小节"))
    candidates = candidates[:40]

    # ---------- 6. 输出 ----------
    layers = []
    for layer in C.LAYERS:
        item = dict(layer)
        item["stats"] = layer_stats[layer["id"]]
        layers.append(item)

    graph = dict(
        meta=dict(
            schema_version="1.0",
            generated_at=datetime.now().astimezone().isoformat(timespec="seconds"),
            knowledge_dir=str(KB),
            doc_url_prefix=os.path.relpath(str(KB), str(OUT)) + "/",
            docs_scanned=len(docs),
            node_count=len(nodes),
            edge_count=len(edges),
            type_counts=type_counts,
            status_counts=status_counts,
            evidence_counts={k: sum(1 for n in nodes if n.get("evidence") == k) for k in EV.EVIDENCE},
            dim_counts={k: sum(1 for n in nodes if n.get("dim") == k) for k in DIM_LABELS},
            missing_total=sum(1 for n in nodes if n["status"] in
                              ("expected", "missing", "mentioned")),
            na_total=sum(1 for n in nodes if n["status"] == "na"),
            unverified_total=sum(1 for n in nodes if n["status"] == "unverified"),
            placeholder_total=len(placeholders),
            expected_slots=len(E.EXPECTED),
            uncovered_docs=uncovered,
            type_labels=dict(theory="理论/模型", action="动作", metric="指标", layer="层级"),
            status_labels=dict(supported="已有文档支撑", mentioned="只有提及没有展开",
                               missing="缺失", unverified="待确认", expected="应有但缺失",
                               na="不适用"),
            evidence_labels=EV.EVIDENCE,
            dim_labels=DIM_LABELS,
            edge_labels=dict(belongs="属于", drives="驱动", measures="度量",
                             depends="依赖", cites="引用"),
            edge_notes=dict(
                belongs="理论归属某一层",
                drives="理论驱动某动作",
                measures="动作影响某指标",
                depends="箭头由前层指向后层，表示后层依赖前层成立",
                cites="文档之间的显式引用，挂在承载该概念的节点上",
            ),
        ),
        layers=layers,
        nodes=nodes,
        edges=edges,
    )

    report = dict(
        generated_at=graph["meta"]["generated_at"],
        docs=len(docs),
        nodes=len(nodes),
        edges=len(edges),
        new_nodes=[dict(id=n["id"], label=n["label"], type=n["type"]) for n in new_nodes],
        gone_nodes=[dict(id=n["id"], label=n["label"], type=n["type"]) for n in gone_nodes],
        stale_docs={k: v for k, v in sorted(stale_docs.items())},
        uncovered_docs=uncovered,
        candidates=candidates,
        errors=errors,
        warnings=warnings,
        layer_stats=layer_stats,
        evidence_counts=graph["meta"]["evidence_counts"],
        dim_counts=graph["meta"]["dim_counts"],
    )

    if errors:
        print("\n".join("× " + e for e in errors))
        print(f"\n校验失败，共 {len(errors)} 处，未写入文件。")
        return report, 1

    if dry_run:
        return report, 0

    OUT.mkdir(parents=True, exist_ok=True)
    GRAPH_JSON.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    PROPOSALS.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    html = TEMPLATE.read_text(encoding="utf-8").replace(
        "__GRAPH_JSON__", json.dumps(graph, ensure_ascii=False, separators=(",", ":")))
    INDEX_HTML.write_text(html, encoding="utf-8")
    return report, 0


def print_report(report):
    m = report
    print(f"文档 {m['docs']} 篇 · 节点 {m['nodes']} 个 · 边 {m['edges']} 条")
    ev = m.get("evidence_counts", {})
    print("证据分级：" + " · ".join(f"{EV.EVIDENCE[k]} {v}" for k, v in ev.items()))
    print("\n每层：理论 / 动作 / 指标 / 缺 / 不适用")
    for lid, st in m["layer_stats"].items():
        name = next(l["name"] for l in C.LAYERS if l["id"] == lid)
        print(f"  {name:<6} {st['theory']:>2} / {st['action']:>2} / {st['metric']:>2}"
              f" / {st['missing']:>2} / {st['na']:>2}")
    if m["new_nodes"]:
        print(f"\n新增节点 {len(m['new_nodes'])} 个：")
        for n in m["new_nodes"][:40]:
            print(f"  + {n['label']}（{n['type']}）")
    if m["gone_nodes"]:
        print(f"\n消失节点 {len(m['gone_nodes'])} 个：")
        for n in m["gone_nodes"]:
            print(f"  - {n['label']}（{n['type']}）")
    if m["stale_docs"]:
        print("\n文档改过、节点待复核：")
        for doc, nids in m["stale_docs"].items():
            print(f"  · {doc}（{len(nids)} 个节点）")
        print("  复核完跑：python3 extract.py --ack")
    if m["uncovered_docs"]:
        print("\n有文档但没有节点：")
        for d in m["uncovered_docs"]:
            print("  · " + d)
    if m["candidates"]:
        print(f"\n未匹配的小节 {len(m['candidates'])} 条（可能是新概念，见 work/proposals.json）")
    if m["warnings"]:
        print("\n提醒：")
        for w in m["warnings"]:
            print("  · " + w)


def ack():
    docs = scan_docs()
    ids = set()
    for n in C.NODES:
        ids.add(n.get("doc", ""))
    data = {d: docs[d]["sha1"] for d in ids if d in docs}
    REVIEWED.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已把 {len(data)} 篇文档的当前指纹记为「已复核」：{REVIEWED.name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ack", action="store_true", help="把当前文档指纹记为已复核")
    ap.add_argument("--check", action="store_true", help="只校验，不写文件")
    args = ap.parse_args()
    if args.ack:
        ack()
        sys.exit(0)
    report, code = build(dry_run=args.check)
    print_report(report)
    if args.check:
        print("\n（--check：只校验与报告，未写入文件）")
    else:
        print(f"\n已写出：{GRAPH_JSON}\n         {INDEX_HTML}")
    sys.exit(code)
