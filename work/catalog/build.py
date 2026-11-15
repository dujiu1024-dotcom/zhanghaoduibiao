# -*- coding: utf-8 -*-
"""把 work/catalog/dataN.py 汇总成 catalog.csv 与九份分类 md。"""
import csv
import importlib
import os
import sys

ROOT = "/Users/longyi/project/账号对标"
OUT = os.path.join(ROOT, "04-知识底座/catalog")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

HEADER = ["编号", "类", "项", "资料名称", "类型", "作者或机构", "年份",
          "一句话它解决什么", "真实性依据", "优先级", "状态", "备注"]

PREAMBLE = {
    "06": """## 一手源与推断的分界（2026-11-14 补）

本类混着两种东西，读之前先分清：

| 用哪几项 | 是什么 | 能不能当依据 |
| --- | --- | --- |
| `6.7 工程论文`、`6.8 专利`、`6.9 技术博客与官方说明` | 一手工程源：论文/专利/平台官方公示，可点开核到题名、公开号、页面 | **能**当“机制存在”的依据；不能当“你会拿到多少流量”的依据 |
| `6.1 推荐机制`~`6.6 跨平台` 里标“推断/传闻”的条目 | 外部推演与经验总结 | **不能**当依据，只能当假设 |
| 本地 `01-推荐机制与流量池.md` 的流量池分层、`02-新号冷启动与养号.md` 的养号 | 无一手来源的二手结论 | 只能当假设，且已被一手源削弱（见文末“还缺什么”第 3 条） |

能当依据的只有三句：① 平台确实在公开层面承认“多路召回＋融合排序＋去重打散＋实时反馈”这条链路；② 判重是特征级自动检测（水印溯源、向量召回＋复核）；③ 新内容存在“小流量试探后扩缩量”的机制设计。**这三句都不含任何流量数值。**

仍是推断的：流量池分几层、新号首推给多少、完播权重占比、养号是否有效。谁把这三句往数值上推，谁就是在编。""",
}

rows = []
cats = []
for i in range(1, 11):
    path = os.path.join(HERE, f"data{i}.py")
    if not os.path.exists(path):
        continue
    mod = importlib.import_module(f"data{i}")
    catname = mod.CAT
    catnum = f"{i:02d}" if i < 10 else "X"
    notes = getattr(mod, "NOTES", {})
    seq = 0
    items_meta = []
    for item, entries in mod.ITEMS:
        items_meta.append([item, len(entries)])
        for e in entries:
            seq += 1
            name, typ, author, year, solves, evid, prio, status = e[:8]
            num = e[8] if len(e) > 8 else f"{catnum}-{seq:02d}"   # 第 9 位：显式编号（新增条目从 51 起）
            it = e[9] if len(e) > 9 else item                     # 第 10 位：显式归属细类（新条目放类尾也不串格）
            rows.append([num, catname, it, name, typ, author, year,
                         solves, evid, prio, status, notes.get(name, "")])
    # 显式归属（第 10 位）的条目按实际 项 计数，避免出现分组名冒充细类
    seen = {}
    for r in rows:
        if r[1] == catname:
            seen[r[2]] = seen.get(r[2], 0) + 1
    items_meta = [[k, v] for k, v in seen.items()]
    cats.append({"num": catnum, "name": catname, "items": items_meta,
                 "note": getattr(mod, "NOTE", ""), "count": seq})

os.makedirs(OUT, exist_ok=True)

with open(os.path.join(OUT, "catalog.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(HEADER)
    w.writerows(rows)

for c in cats:
    fn = os.path.join(OUT, f"{c['num']}-{c['name'].split('、', 1)[1]}.md")
    lines = [f"# {c['name']}｜资料清单（{c['count']} 条）", ""]
    lines.append("字段口径见 [README.md](README.md)。**待核**＝有存在线索但未核到出版社/期刊/署名页，不得直接引用。")
    lines.append("")
    if c["num"] in PREAMBLE:
        lines.append(PREAMBLE[c["num"]])
        lines.append("")
    lines.append("| 编号 | 项 | 资料名称 | 类型 | 作者/机构 | 年份 | 一句话它解决什么 | 真实性依据 | 优先级 | 状态 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        if r[1] != c["name"]:
            continue
        vals = [r[0], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10]]
        vals = [v.replace("|", "／") for v in vals]
        lines.append("| " + " | ".join(vals) + " |")
    lines.append("")
    lines.append("## 本类各项条数")
    for item, n in c["items"]:
        lines.append(f"- {item}：{n} 条")
    lines.append("")
    lines.append("## 本类还缺什么")
    lines.append("")
    lines.append(c["note"] if c["note"] else "（待补）")
    lines.append("")
    with open(fn, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

print("categories:", len(cats), "rows:", len(rows))
for c in cats:
    print(c["num"], c["name"], c["count"], [f"{k}:{v}" for k, v in c["items"]])
