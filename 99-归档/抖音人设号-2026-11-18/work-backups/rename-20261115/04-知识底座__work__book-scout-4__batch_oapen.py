#!/usr/bin/env python3
"""OAPEN 批量取回（按缺口格优先排序）。

排序：定价与报价 → 销售与谈判 → 定位与差异化 → 交付与验收 → 其余格按相关本书量降序。
节流：并发 1，每本间隔随机 30–60 秒（实测 25 秒在 OAPEN 反爬眼里偏快）。
重试：429 三级退避 90/180/300；5xx 退避 10/30/60；网络层中断 5/15/30；三类各最多 3 次，分开计数。
断点续跑：manifest 原地更新（不追加重复行），OK 与「仅 EPUB」不再重试，其余 FAIL 可重下。
输出：oapen/<格>/<编号>-<slug>.pdf、oapen/manifest_oapen.csv
"""
import csv
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
from collections import Counter

import license as LIC
import oapen

OUT = "oapen"
MAN = os.path.join(OUT, "manifest_oapen.csv")
STATE = os.path.join(OUT, "_state.json")
TMP = MAN + ".tmp"

FIRST = ["定价与报价", "销售与谈判", "定位与差异化", "交付与验收"]
COLS = ["编号", "书名", "出版社", "原始URL", "页数", "有无文字层", "内页许可原文全文",
        "许可类型", "命中格", "下载状态", "引用口径", "文件", "备注"]

CELL_KW = {
    "定价与报价": ["pricing", "price", "willingness to pay", "revenue", "margin", "monetiz"],
    "定位与差异化": ["positioning", "differentiat", "brand", "competitive advantage", "market segment"],
    "B2B采购决策链": ["business-to-business", "b2b", "organizational buy", "buying cent", "procurement",
                    "industrial market", "purchasing"],
    "行业场景知识": ["industry", "sector", "logistics", "construction", "hospitality", "manufactur"],
    "个体老板与小额采购": ["small business", "sme", "micro-enterprise", "microenterprise", "self-employed",
                     "sole proprietor", "small firm"],
    "销售与谈判": ["negotiation", "negotiat", "sales", "selling", "bargain"],
    "交付与验收": ["project management", "project delivery", "contract", "acceptance",
                "quality assurance", "service level"],
    "商业模式设计": ["business model", "value proposition", "revenue model", "canvas"],
    "一人公司的协作与招人": ["freelance", "self-employed", "solo", "one-person", "creative worker", "gig"],
    "行业方案库": ["case stud", "best practice", "consultanc", "consulting", "toolkit"],
}

LOCK = threading.Lock()
_pace = [0.0]


def throttle(lo=30.0, hi=60.0):
    """每本之间随机 30–60 秒。23–26 秒的固定节奏已被 OAPEN 判为异常请求。"""
    with LOCK:
        w = random.uniform(lo, hi) - (time.time() - _pace[0])
        if w > 0:
            time.sleep(w)
        _pace[0] = time.time()


def slug(s, n=44):
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")[:n] or "untitled"


def hits(title):
    t = title.lower()
    return [c for c, kws in CELL_KW.items() if any(k in t for k in kws)]


def inspect(path):
    """页数、文字层字符数、许可整句（只用 PDF 内文字，抽不到就是「未找到许可」）。"""
    info = subprocess.run(["pdfinfo", path], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", info)
    pages = int(m.group(1)) if m else 0
    txt = subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True).stdout
    sent, _why = LIC.extract(txt)
    return pages, len(txt), sent


def build(limit):
    d = json.load(open("raw/records_all.json", encoding="utf-8"))
    seen, rows = set(), []
    for v in d.values():
        us = [u for u in v["pdf_urls"] if "library.oapen.org" in u]
        if not us or v["title"].lower().startswith("chapter") or v["score"] < 1:
            continue
        key = v["title"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append({"cell": v["cell"], "title": v["title"], "url": us[0],
                     "publisher": "; ".join(v["publisher"][:1]),
                     "year": (v["date"] or [""])[-1][:4], "score": v["score"]})
    cnt = {c: sum(1 for r in rows if r["cell"] == c) for c in CELL_KW}
    rest = sorted([c for c in cnt if c not in FIRST], key=lambda c: -cnt[c])
    order = FIRST + rest
    rows.sort(key=lambda r: (order.index(r["cell"]) if r["cell"] in order else 99, -r["score"]))
    print("各格候选数：", {c: cnt[c] for c in order}, flush=True)
    return rows[:limit]


def load_manifest():
    if not os.path.exists(MAN):
        return []
    with open(MAN, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save_manifest(rows):
    """原子替换，进程被杀也不会写出半截文件。"""
    with open(TMP, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in COLS})
    os.replace(TMP, MAN)


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 148
    built = build(limit)
    rows = load_manifest()
    by_url = {r["原始URL"]: r for r in rows if r.get("原始URL")}
    used = {int(r["编号"]) for r in rows if str(r.get("编号", "")).isdigit()}
    next_no = [max(used) + 1 if used else 1]

    # 待处理：无记录 / FAIL 且不是「仅 EPUB」
    todo = []
    for r in built:
        old = by_url.get(r["url"])
        if old and old.get("下载状态") == "OK":
            continue
        if old and "仅 EPUB" in (old.get("备注") or ""):
            continue
        todo.append((r, old))
    print(f"manifest 已有 {len(rows)} 行，本轮待处理 {len(todo)} 本", flush=True)

    reasons = Counter()

    def one(r, old):
        rec = {k: (old or {}).get(k, "") for k in COLS} if old else {
            "编号": "", "书名": r["title"], "出版社": r["publisher"], "原始URL": r["url"],
            "页数": "", "有无文字层": "", "内页许可原文全文": "", "许可类型": "",
            "命中格": "", "下载状态": "FAIL", "引用口径": "", "文件": "", "备注": ""}
        rec.update({"书名": r["title"], "出版社": r["publisher"],
                    "命中格": "；".join(hits(r["title"])) or (r["cell"] or "未分类")})
        cell = r["cell"] or "未分类"
        d = os.path.join(OUT, cell)
        os.makedirs(d, exist_ok=True)
        no = rec.get("编号") or f"{next_no[0]:03d}"
        rec["编号"] = no
        fn = (old or {}).get("文件") or os.path.join(d, f"{no}-{slug(r['title'])}.pdf")
        try:
            throttle()
            ok, msg, reason = oapen.download(r["url"], fn)
            # EPUB/ZIP：先看 OAPEN 上是否有同名 PDF 版本
            if not ok and reason == "epub":
                alt = r["url"].replace(".epub", ".pdf")
                if alt != r["url"]:
                    print(f"    返回 EPUB，试同目录 PDF：{alt.split('/')[-1]}", flush=True)
                    throttle()
                    ok2, msg2, reason2 = oapen.download(alt, fn)
                    if ok2:
                        ok, msg, reason = ok2, msg2 + "（EPUB 换 PDF 成功）", "ok"
                    else:
                        msg, reason = msg2, reason2
            if ok:
                pages, chars, lic = inspect(fn)
                lt = LIC.kind(lic)
                rec.update({"下载状态": "OK", "文件": fn, "页数": pages,
                            "有无文字层": "有" if chars > 3000 else "无（疑似扫描件）",
                            "内页许可原文全文": lic, "许可类型": lt,
                            "引用口径": LIC.QUOTA.get(lt, "未找到许可，不可引用"),
                            "备注": msg if "换 PDF" in msg else
                                    ("文字层不足 3000 字符，按扫描件处理" if chars <= 3000 else "")})
            else:
                rec.update({"下载状态": "FAIL", "文件": "", "备注": f"[{reason}] {msg}"})
                if reason == "epub":
                    rec["备注"] = f"[epub] 仅 EPUB，不入库；{msg}"
                if os.path.exists(fn) and os.path.getsize(fn) == 0:
                    os.remove(fn)
            reasons[reason] += 1
        except Exception as e:
            rec["备注"] = f"处理异常 {type(e).__name__}: {e}"
            reasons["exception"] += 1
        return rec

    for i, (r, old) in enumerate(todo, start=1):
        rec = one(r, old)
        if old:
            old.update(rec)
        else:
            rec["编号"] = f"{next_no[0]:03d}"
            next_no[0] += 1
            rows.append(rec)
            by_url[r["url"]] = rec
        save_manifest(rows)
        json.dump({x["原始URL"]: x.get("下载状态", "FAIL") for x in rows if x.get("原始URL")},
                  open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"[{i}/{len(todo)}] {rec['下载状态']:<4} {r['cell']} | {r['title'][:40]} | "
              f"{rec['页数']}p {rec['许可类型']} {rec['备注'][:60]}", flush=True)

    ok_n = sum(1 for x in rows if x["下载状态"] == "OK")
    print(f"batch done | 总 {len(rows)} 行 OK {ok_n} FAIL {len(rows) - ok_n}", flush=True)
    print(f"本轮原因分布：{dict(reasons)}", flush=True)


if __name__ == "__main__":
    main()
