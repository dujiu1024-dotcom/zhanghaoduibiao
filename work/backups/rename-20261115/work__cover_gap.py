# -*- coding: utf-8 -*-
"""12-覆盖缺口总账：以 13-三源齐备度.csv（现场数）为底，join 11-按格找料.csv 的渠道状态。"""
import csv

B = '04-知识底座/catalog/'
src = list(csv.DictReader(open(B + '13-三源齐备度.csv', encoding='utf-8-sig')))
plan = {r['细类']: r for r in csv.DictReader(open(B + '11-按格找料.csv', encoding='utf-8-sig'))}

KEY = {"钩子与注意力", "口播与语言表达", "推荐机制", "冷启动与账号权重", "私信承接", "转化路径与漏斗设计",
       "定价与报价", "合同与回款", "广告法与宣传合规", "个保法与数据安全",
       "违规判定与发布前审（并库原文）", "对标拆解"}

H = ["格编号", "所属类", "细类名", "可引用书", "其中NC", "仅参考书", "摘要二手", "论文法规",
     "经验E1", "经验E2", "经验E3", "可引用合计", "三源合计", "达标档", "12重点", "渠道状态", "还差多少到合格线"]

rows = []
stat = {"三源全零": 0, "只有1条": 0, "达硬底线": 0, "达合格线": 0}
for r in src:
    if r['格编号'] == '合计':
        continue
    book = int(r['书可引用本数']); nc = int(r['其中NC限制']); note = int(r['摘要份数'])
    paper = int(r['论文法规篇数']); re_n = int(r['经验条数'])
    e1, e2, e3 = int(r['E1']), int(r['E2']), int(r['E3'])
    cite = book + paper
    tot = book + note + paper + re_n
    if tot == 0:
        tier = "三源全零"
    elif tot == 1:
        tier = "只有1条"
    elif tot >= 3 and cite >= 2:
        tier = "达合格线"
    else:
        tier = "达硬底线（未达合格）"
    stat[tier if tier != "达硬底线（未达合格）" else "达硬底线"] += 1
    p = plan.get(r['细类名'], {})
    kind = p.get('分档', '')
    if tot == 0:
        if kind == "只能实测":
            ch = "已试尽：公版/OA/官方均无，只能自采实测"
        elif kind == "必须买书":
            ch = "已试尽：仅剩付费购买，未买"
        elif kind == "已有原文":
            ch = "口径问题：原文归在主题格，元类未挂"
        else:
            ch = "未找：有公开路径，尚未采"
    else:
        ch = "已有材料"
    need = max(0, 3 - tot) if tier != "达合格线" else 0
    rows.append([r['格编号'], r['所属类'], r['细类名'], book, nc, int(r['原文但不可引用']), note, paper,
                 e1, e2, e3, cite, tot, tier, "是" if r['细类名'] in KEY else "", ch, need])

with open(B + '12-覆盖缺口总账.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f); w.writerow(H); w.writerows(rows)

L = ["# 覆盖缺口总账：77 格现场数", "",
     "数据源：`13-三源齐备度.csv`（以 metadata.csv 落盘与 kbase.db 段数现场统计）、"
     "`11-按格找料.csv`（渠道分档）、`experience/experience.csv`。**数字均为现场数，不估。**", "",
     "口径：可引用合计＝可引用书＋论文法规（摘要与仅参考书不算可引用）；"
     "达合格线＝三源合计≥3 且可引用合计≥2；三源合计＝可引用书＋摘要＋论文法规＋经验。", "",
     "| 档 | 格数 |", "| --- | ---: |"]
for k in ["三源全零", "只有1条", "达硬底线", "达合格线"]:
    L.append(f"| {k} | {stat[k]} |")
L.append(f"| 合计 | {sum(stat.values())} |")
L += ["", "| " + " | ".join(H) + " |", "| " + " | ".join(["---"] * len(H)) + " |"]
for r in rows:
    L.append("| " + " | ".join(str(x) for x in r) + " |")
open(B + '12-覆盖缺口总账.md', 'w', encoding='utf-8').write("\n".join(L) + "\n")

print(stat)
print("零格", [r[2] for r in rows if r[13] == "三源全零"])
print("未找零格", [r[2] for r in rows if r[13] == "三源全零" and r[15].startswith("未找")])
print("12重点达标", [(r[2], r[12], r[13], r[15]) for r in rows if r[14] == "是"])
