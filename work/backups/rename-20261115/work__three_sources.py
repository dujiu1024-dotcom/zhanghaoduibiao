# -*- coding: utf-8 -*-
"""13-三源齐备度：77 细类 × 书/摘要/论文法规/经验。以落盘与入库为准。"""
import csv, os, sqlite3, collections

BASE = '04-知识底座/'
meta = list(csv.DictReader(open(BASE + 'knowledge/sources/metadata.csv', encoding='utf-8-sig')))
cat = list(csv.DictReader(open(BASE + 'catalog/catalog.csv', encoding='utf-8-sig')))
exp = list(csv.DictReader(open(BASE + 'experience/experience.csv', encoding='utf-8-sig')))
db = sqlite3.connect(BASE + 'rag/kbase.db')

# 段数：按 source_path 统计
seg = collections.Counter()
for sp, n in db.execute("select d.source_path, count(s.rowid) from docs d join segments s on s.doc_id=d.id group by d.id"):
    seg[os.path.basename(sp)] = n

CLASS = []
CMAP = {}
for r in cat:
    if r['项'] not in CMAP:
        CMAP[r['项']] = r['类']
        CLASS.append(r['项'])
for n, c in [("脚本结构", "二、传播与内容"), ("私信承接", "五、客户运营与转化"),
             ("成交与异议", "五、客户运营与转化"), ("对标拆解", "二、传播与内容")]:
    if n not in CMAP:
        CMAP[n] = c; CLASS.append(n)

KEY = [
    ("recommend", "推荐机制"), ("cold-start", "冷启动与账号权重"), ("cold start", "冷启动与账号权重"),
    ("retrieval", "冷启动与账号权重"), ("ctr prediction", "推荐机制"), ("kuairec", "推荐机制"), ("kuairand", "推荐机制"),
    ("spectrum", "推荐机制"), ("pepnet", "推荐机制"), ("idproxy", "冷启动与账号权重"), ("notellm", "推荐机制"),
    ("youtube recommendations", "推荐机制"), ("item-to-item", "推荐机制"), ("viral", "情绪与唤醒"),
    ("popularity", "推荐机制"), ("attention economy", "钩子与注意力"), ("attention brokers", "钩子与注意力"),
    ("pricing", "定价与报价"), ("price", "定价与报价"), ("pricing of consumer", "定价与报价"),
    ("elaboration likelihood", "说服与态度改变"), ("fear appeals", "说服与态度改变"), ("curiosity", "钩子与注意力"),
    ("transportation", "叙事结构与故事"), ("framing", "议程设置与框架"), ("narrative", "叙事结构与故事"),
    ("heuristic", "认知偏差与判断启发"), ("judgment under uncertainty", "认知偏差与判断启发"),
    ("propensity score", "统计与因果推断"), ("scales of measurement", "指标口径与度量"),
    ("controlled experiments", "实验设计与A/B"), ("representative method", "抽样与样本偏差"),
    ("social identity", "从众与社会认同"), ("bystander", "群体情境与旁观者效应"), ("obedience", "群体情境与旁观者效应"),
    ("social behavior as exchange", "互惠、社会交换与地位"), ("cooperation", "互惠、社会交换与地位"),
    ("awe", "情绪与唤醒"), ("gratitude", "互惠、社会交换与地位"), ("emotional responses to music", "情绪与唤醒"),
    ("first impressions", "身份认同与自我呈现"), ("self-", "身份认同与自我呈现"),
    ("customer-based brand", "客户画像与分层"), ("customer experience", "客户成功与转介绍"),
    ("referral", "客户成功与转介绍"), ("organizational buying", "B2B采购决策链"),
    ("returns to advertising", "投放与ROI"), ("crisis", "平台规则与舆情"),
    ("technical debt", "失败案例库"), ("gratitude", "互惠、社会交换与地位"),
    ("politics and the english language", "修辞与说服性写作"), ("rhétorique", "修辞与说服性写作"),
    ("persuasion", "说服与态度改变"), ("compliance", "承诺一致与门槛效应"),
    ("recriprocal concessions", "承诺一致与门槛效应"), ("reciprocal concessions", "承诺一致与门槛效应"),
    ("reactance", "心理阻抗与说服反噬"), ("bystander-effect", "群体情境与旁观者效应"),
    ("museum", "视听语言与镜头"), ("film", "视听语言与镜头"),
]
CN = [("道德情操论", "互惠、社会交换与地位"), ("有闲阶级", "互惠、社会交换与地位"), ("人性论", "认知偏差与判断启发"),
      ("心理学原理", "认知偏差与判断启发"), ("政治中的人性", "认知偏差与判断启发"), ("群体心理学", "群体情境与旁观者效应"),
      ("群体心理", "群体情境与旁观者效应"), ("模仿律", "从众与社会认同"), ("舆论的结晶", "议程设置与框架"),
      ("舆论", "议程设置与框架"), ("宣传", "议程设置与框架"), ("电影", "视听语言与镜头"),
      ("演说的艺术", "口播与语言表达"), ("修辞学", "修辞与说服性写作"),
      ("增值税", "成本与税务"), ("所得税", "成本与税务"), ("小规模纳税人", "成本与税务"),
      ("合同编", "合同与回款")]
EN = [("the crowd", "从众与社会认同"), ("leisure class", "互惠、社会交换与地位"),
      ("expression of the emotions", "情绪与唤醒"), ("public opinion", "议程设置与框架"),
      ("elements of style", "修辞与说服性写作"), ("free culture", "知识产权"),
      ("principles of marketing", "消费者行为与决策旅程"), ("digital marketer", "转化路径与漏斗设计"),
      ("reality lost", "传播模型与媒介环境"), ("firm competitive", "客户成功与转介绍"),
      ("noncomplainer", "客户成功与转介绍"), ("procurement", "B2B采购决策链"),
      ("dynamics in logistics", "行业场景知识"), ("periphery and small", "个体老板与小额采购决策"),
      ("contracting and safety", "外包与产能"), ("business model innovation", "商业模式设计"),
      ("pricing of consumer", "定价与报价"), ("performing artists", "一人公司的协作与招人"),
      ("modern industrial", "行业方案库"), ("site reliability", "复盘与归因方法"),
      ("pragmatic programmer", "工具生态与成本"), ("designing data-intensive", "工具生态与成本"),
      ("never split", "销售与谈判"), ("introduction to sociology", "从众与社会认同"),
      ("organizational behavior", "群体情境与旁观者效应"), ("principles of economics", "成本与税务"),
      ("principles of management", "一人公司的协作与招人"), ("psychology 2e", "认知偏差与判断启发"),
      ("educational psychology", "说服与态度改变"), ("emarketing", "转化路径与漏斗设计"),
      ("data science for psychologists", "统计与因果推断"), ("antifragile", "失败案例库"),
      ("atomic habits", "承诺一致与门槛效应"), ("breakthrough advertising", "钩子与注意力"),
      ("second brain", "工具生态与成本"), ("black box thinking", "复盘与归因方法"),
      ("bounce", "失败案例库")]
LAW = [("广告法", "广告法与宣传合规"), ("绝对化", "广告法与宣传合规"), ("互联网广告", "广告法与宣传合规"),
       ("个人信息", "个保法与数据安全"), ("pipl", "个保法与数据安全"), ("民法典", "合同与回款"),
       ("合同", "合同与回款"), ("电子商务法", "平台经营合规"), ("网络交易", "平台经营合规"),
       ("消费者权益", "消费者保护"), ("消保", "消费者保护"), ("价格", "价格与促销合规"), ("明码标价", "价格与促销合规"),
       ("自律公约", "违规判定与发布前审（并库原文）"), ("社区", "违规判定与发布前审（并库原文）"),
       ("微信", "私域承接与微信运营"), ("公众号", "私域承接与微信运营"), ("外链", "私域承接与微信运营"),
       ("openai", "AI模型能力与成本边界（只收实时源）"), ("anthropic", "AI模型能力与成本边界（只收实时源）"),
       ("模型", "AI模型能力与成本边界（只收实时源）"), ("抖音", "推荐机制"), ("电商", "平台经营合规")]


NAME = [("个人信息", "个保法与数据安全"), ("人格权编", "个保法与数据安全"), ("数据安全法", "个保法与数据安全"),
        ("网络安全法", "个保法与数据安全"), ("民法典", "合同与回款"), ("合同编", "合同与回款"),
        ("增值税", "成本与税务"), ("所得税", "成本与税务"), ("广告法", "广告法与宣传合规"),
        ("互联网广告", "广告法与宣传合规"), ("绝对化用语", "广告法与宣传合规"), ("反不正当竞争", "广告法与宣传合规"),
        ("广告违法典型案例", "广告法与宣传合规"), ("著作权", "知识产权"), ("信息网络传播权", "知识产权"),
        ("商标法", "知识产权"), ("生态治理", "平台规则与舆情"), ("算法推荐管理", "推荐机制"),
        ("社区自律公约", "违规判定与发布前审（并库原文）"), ("社区公约", "违规判定与发布前审（并库原文）"),
        ("社区管理规范", "违规判定与发布前审（并库原文）"), ("电子商务法", "平台经营合规"),
        ("网络交易", "平台经营合规"), ("消费者权益", "消费者保护"), ("价格法", "价格与促销合规"),
        ("明码标价", "价格与促销合规"), ("NIST AI", "AI模型能力与成本边界（只收实时源）"),
        ("API Pricing", "AI模型能力与成本边界（只收实时源）"), ("模型", "AI模型能力与成本边界（只收实时源）"),
        ("备案", "AI模型能力与成本边界（只收实时源）"), ("个性化推荐算法", "推荐机制"),
        ("JLREQ", "字幕与信息密度"), ("Subtitle Guidelines", "字幕与信息密度"),
        ("互联网络发展状况", "市场调研与行业数据"), ("企业微信", "私域承接与微信运营"),
        ("小微经营者", "个体老板与小额采购决策")]


def by_key(title):
    t = title.lower()
    for k, c in CN:
        if k in title: return c
    for k, c in EN:
        if k in t: return c
    for k, c in KEY:
        if k in t:
            return c
    return None


def classify(row):
    p = row['本地路径'].split('/')
    title = row['题名']
    tl0 = title.lower()
    for k, c in NAME:
        if k.lower() in tl0 or k in title:
            return c, None
    alias = {"实验设计与AB": "实验设计与A/B"}
    if len(p) > 2 and (p[1] in CMAP or p[1] in alias):
        return alias.get(p[1], p[1]), None
    d = p[1] if len(p) > 1 else ''
    tl = title.lower()
    if d == 'official':
        for k, c in LAW:
            if k.lower() in tl or k.lower() in row['本地路径'].lower():
                return c, None
        return None, None
    if d == 'patents':
        return "专利（一手工程源）", None
    if d == 'blogs':
        return "技术博客与官方说明（一手工程源）", None
    if d == 'papers':
        return by_key(title), 'paper'
    if d == 'copywriting-vault':
        return "修辞与说服性写作", 'note'
    if d == 'behavioral-economics-notes':
        return "认知偏差与判断启发", 'note'
    if d == 'knowledge':
        if title in ('INDEX', 'README') or '_templates' in row['本地路径']:
            return 'SKIP', 'note'
        if 'accounts__' in row['本地路径']:
            return "对标拆解", 'note'
        if 'topics__' in row['本地路径']:
            return "选题与需求信号", 'note'
        return 'SKIP', 'note'
    if d in ('books-for-agents',):
        return by_key(title), 'note'
    if d == 'thirdparty':
        return "错误做法样本（反面教材）", 'note'
    if d == 'law':
        for k, c in LAW:
            if k.lower() in row['本地路径'].lower() or k.lower() in tl:
                return c, None
        return by_key(title), None
    return by_key(title), None


stat = {c: {'书': 0, 'NC': 0, '书段': 0, '待购': 0, '摘': 0, '摘段': 0, '论文': 0, '经验': 0,
            'E4': 0, 'E3': 0, 'E2': 0, 'E1': 0, 'E0': 0} for c in CLASS}
un = collections.Counter()

for r in meta:
    c, hint = classify(r)
    q = r['质量分级']
    d = r['本地路径'].split('/')[1] if '/' in r['本地路径'] else ''
    is_note = d in ('knowledge', 'behavioral-economics-notes', 'copywriting-vault', 'thirdparty')
    is_paper = d in ('papers', 'patents', 'blogs') or hint == 'paper'
    if c == 'SKIP':
        continue
    if not c:
        un[(d, q)] += 1
        continue
    s = stat[c]
    n = seg.get(os.path.basename(r['本地路径']), 0)
    if is_note:
        s['摘'] += 1; s['摘段'] += n
    elif is_paper:
        s['论文'] += 1
    elif q == '可引用':
        s['书'] += 1; s['书段'] += n
        if 'NC' in (r['授权限制'] or '').upper() or '非商业' in (r['授权限制'] or ''):
            s['NC'] += 1
    else:
        s['待购'] += 1

import re as _re
for e in exp:
    hits = [x.strip() for x in _re.split(r"[、，,／/]", e.get('对应子项') or '') if x.strip() in stat]
    if not hits:
        hits = [x.strip() for x in _re.split(r"[、，,／/]", e.get('对应判断') or '') if x.strip() in stat]
    lv = (e['证据等级'] or 'E0').strip().upper()
    for c in hits:
        stat[c]['经验'] += 1
        stat[c][lv] = stat[c].get(lv, 0) + 1

H = ["格编号", "所属类", "细类名", "书可引用本数", "其中NC限制", "书段数", "原文但不可引用", "摘要份数",
     "摘要段数", "论文法规篇数", "经验条数", "E4", "E3", "E2", "E1", "E0", "合计", "缺口判断"]
rows, zero, both = [], [], 0
for i, c in enumerate(CLASS, 1):
    s = stat[c]
    tot = s['书'] + s['摘'] + s['论文'] + s['经验']
    if tot == 0:
        j = "零"
    elif s['书'] >= 3 and (s['摘'] + s['论文'] + s['经验']) >= 2 and s['论文'] >= 1:
        j = "够"
    else:
        j = "偏薄"
    if j == "零":
        zero.append(c)
    if s['书'] > 3 and s['摘'] > 3:
        both += 1
    rows.append([f"G{i:02d}", CMAP[c], c, s['书'], s['NC'], s['书段'], s['待购'], s['摘'], s['摘段'],
                 s['论文'], s['经验'], s['E4'], s['E3'], s['E2'], s['E1'], s['E0'], tot, j])

T = [sum(r[k] for r in rows) for k in range(3, 17)]
rows.append(["合计", "", "77 格"] + T + [""])
with open(BASE + 'catalog/13-三源齐备度.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f); w.writerow(H); w.writerows(rows)

L = ["# 三源齐备度：77 格 × 书／摘要／论文法规／经验", "",
     "口径：书＝metadata 里质量档「可引用」且已落盘的整本原文；摘要＝二手笔记与提炼（knowledge/、behavioral-economics-notes/、copywriting-vault/、thirdparty/）；"
     "论文法规＝papers/、patents/、blogs/ 与 law/、official/ 下的官方文本；经验＝experience.csv 按方向归格。**按实际落盘计数，不估算。**", "",
     "「仅参考·来源待购」（Oxford 那批）**算书但不算可引用**，单独一列，不进「书可引用本数」。", "",
     "缺口判断：够＝书≥3 且 论文≥1 且（摘要＋论文＋经验）≥2；偏薄＝有料但不达；零＝四类全 0。", "",
     "计数口径补充：书按**文件**计（如 ds4psy 16 章算 16 份、民法典被两个条目引用只算 1 份）；"
     "经验 127 条 > experience.csv 的 %d 行，因为一条经验可挂 2–3 个细类，按「多挂全算」处理。" % len(exp), "",
     "未归格 %d 份（主要是 books-for-agents 的 50 份二手书摘，按书名无法可靠判定细类，未擅自分配；"
     "另有 official 仅参考 2 份、books 仅参考 1 份等），这些**没有计入任何一格**。" % sum(un.values()), "",
     "| " + " | ".join(H) + " |", "| " + " | ".join(["---"] * len(H)) + " |"]
for r in rows:
    L.append("| " + " | ".join(str(x) for x in r) + " |")
open(BASE + 'catalog/13-三源齐备度.md', 'w', encoding='utf-8').write("\n".join(L) + "\n")

print("书", T[0], "NC", T[1], "书段", T[2], "待购", T[3], "摘", T[4], "摘段", T[5], "论文", T[6], "经验", T[7])
print("零", len(zero), zero)
print("书>3且摘>3", both)
print("未归类", sum(un.values()), un.most_common(6))
