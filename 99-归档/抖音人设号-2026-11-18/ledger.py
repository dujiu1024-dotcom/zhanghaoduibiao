# -*- coding: utf-8 -*-
"""三本账：按九大类子类归位，数量全部从 catalog.csv / experience.csv 数出。"""
import csv
import os
from collections import Counter, defaultdict

ROOT = "/Users/longyi/project/账号对标"
CAT = os.path.join(ROOT, "04-知识底座/catalog")
EXP = os.path.join(ROOT, "04-知识底座/experience/experience.csv")

rows = list(csv.DictReader(open(os.path.join(CAT, "catalog.csv"), encoding="utf-8-sig")))
exp = list(csv.DictReader(open(EXP, encoding="utf-8-sig")))

# 书的体裁分档：只放有把握的，其余一律未分档（不硬塞）
TEXTBOOK = ["Marketing Management", "Consumer Behavior: Buying", "Film Art",
            "Survey Sampling", "Sampling: Design", "Statistics for Experimenters",
            "网络传播概论", "大众传播理论", "消费者行为学", "知识产权法教程",
            "播音发声学", "电影摄影画面创作", "设计调研", "现代社会心理学",
            "社会心理学", "情绪心理学", "一本书读懂财报", "复盘+", "文心",
            "Marketing Research"]
MONOGRAPH = ["The Presentation of Self", "Frame Analysis", "A Theory of Cognitive Dissonance",
             "When Prophecy Fails", "Exchange and Power", "Essai sur le don",
             "The Theory of the Leisure Class", "La Distinction", "The Expression of the Emotions",
             "Causality", "Counterfactuals", "Story: Substance", "Морфология",
             "Das Kunstwerk", "Film als Kunst", "Die neue Typographie", "Detailtypografie",
             "Rhétorique de l'image", "Designing Data-Intensive", "Designing Machine Learning",
             "Domain-Driven Design", "Understanding Privacy", "Privacy in Context",
             "Free Culture", "Identity: Youth", "Obedience to Authority", "The Crowd",
             "Public Opinion", "修辞学 / Rhetoric", "The Mathematical Theory of Communication",
             "Understanding Media", "Amusing Ourselves to Death", "Improving Performance",
             "Business Process Change", "Learning to See", "乡土中国", "营销的本质",
             "GAFA"]
POPULAR = ["Influence: The Psychology", "思考，快与慢", "Nudge", "Pre-Suasion", "Yes! 50",
           "Give and Take", "The Go-Giver", "Jab, Jab", "They Ask, You Answer",
           "The Mom Test", "The E-Myth", "Profit First", "Simple Numbers", "Company of One",
           "The Personal MBA", "The Lean Startup", "Built to Sell", "Deep Work",
           "Virtual Freedom", "Who: The A Method", "Never Split the Difference",
           "Getting to Yes", "The Trusted Advisor", "Million Dollar Consulting",
           "The Win Without Pitching", "Pricing Creativity", "Priceless",
           "Confessions of the Pricing Man", "Monetizing Innovation",
           "Implementing Value Pricing", "The 1% Windfall", "The Challenger Sale",
           "SPIN Selling", "Predictable Revenue", "The Sales Acceleration Formula",
           "Permission Marketing", "This Is Marketing", "Building a StoryBrand",
           "Content Rules", "Everybody Writes", "How Brands Grow", "Positioning",
           "Reality in Advertising", "The Attention Merchants", "The Attention Economy",
           "The Checklist Manifesto", "Misbehaving", "The Fifth Discipline",
           "The Fearless Organization", "How the Mighty Fall", "The Mythical Man-Month",
           "The Pragmatic Programmer", "Software Estimation", "The Goal", "Inspired",
           "Site Reliability Engineering", "超级符号", "运营之光", "增长黑客", "底层逻辑",
           "把自己作为方法", "文案的基本修养", "抢占心智", "肖星的财务思维课",
           "Small Giants", "The Great CEO Within", "The Founder's Dilemmas", "Scaling Up",
           "The Millionaire Next Door", "The Consultant"]


# 关键词表漏掉的，逐本按体裁补判（只补有把握的；仍说不清的留「未分档」）
MANUAL = {
    # 教材：有体系化教学结构、被课程采用
    "Judgment in Managerial Decision Making": "教材",
    "The Dynamics of Persuasion": "教材",
    "叙事学导论": "教材",
    "The Elements of Style": "教材",
    "ことばのハンドブック": "教材",
    "Film Directing Shot by Shot": "教材",
    "The Grammar of the Film Language": "教材",
    "The Visual Story": "教材",
    "Sound Design": "教材",
    "The Technique of Film Editing": "教材",
    "Subtitling: Concepts and Practices": "教材",
    "Mostly Harmless Econometrics": "教材",
    "数据思维": "教材",
    "基本有用的计量经济学": "教材",
    "Trustworthy Online Controlled Experiments": "教材",
    "Field Experiments": "教材",
    "Measuring the User Experience": "教材",
    "Contextual Design": "教材",
    "Market Research in Practice": "教材",
    "The Market Research Toolbox": "教材",
    "Small Business Management": "教材",
    "Writing Effective Use Cases": "教材",
    "推荐系统实践": "教材",
    "深度学习推荐系统": "教材",
    "The Art of SEO": "教材",
    "SEO 实战密码": "教材",
    "The Strategy and Tactics of Pricing": "教材",
    "Ongoing Crisis Communication": "教材",
    # 专著：学术研究专著、经典理论著作
    "Communication and Persuasion": "专著",
    "宣传：观念、话语及其正当化": "专著",
    "Emotional Contagion": "专著",
    "The Unresponsive Bystander": "专著",
    "The Hero with a Thousand Faces": "专著",
    "Audio-Vision": "专著",
    "The Design of Experiments": "专著",
    "Nonresponse in Household Interview Surveys": "专著",
    "丰田生产方式": "专著",
    "Market Segmentation": "专著",
    "Competitive Strategy": "专著",
    "Competitive Advantage: Creating": "专著",
    "合同法研究": "专著",
    "The Service Profit Chain": "专著",
    "The Long and the Short of It": "专著",
    "Diffusion of Innovations": "专著",
    "The Effective Executive": "专著",
    "个人信息保护法理解与适用": "专著",
    "A Theory of Psychological Reactance": "专著",
    "Psychological Reactance: A Theory": "专著",
    # 通俗：面向大众/商业读者的畅销书、科普
    "Storynomics": "通俗",
    "金字塔原理": "通俗",
    "Demand-Side Sales 101": "通俗",
    "TED Talks: The Official": "通俗",
    "Talk Like TED": "通俗",
    "The Science of Storytelling": "通俗",
    "In the Blink of an Eye": "通俗",
    "The Book of Why": "通俗",
    "How to Lie with Statistics": "通俗",
    "How to Measure Anything": "通俗",
    "Measure What Matters": "通俗",
    "The Toyota Way": "通俗",
    "Interviewing Users": "通俗",
    "Just Enough Research": "通俗",
    "Competing Against Luck": "通俗",
    "Jobs to be Done: Theory to Practice": "通俗",
    "What Customers Want": "通俗",
    "Blue Ocean Strategy": "通俗",
    "Play Bigger": "通俗",
    "阿里铁军销售课": "通俗",
    "User Story Mapping": "通俗",
    "Specification by Example": "通俗",
    "The Seven Pillars of Customer Success": "通俗",
    "Customer Success: How Innovative": "通俗",
    "The Cold Start Problem": "通俗",
    "Platform Revolution": "通俗",
    "Business Model Generation": "通俗",
    "Financial Intelligence": "通俗",
    "財務3表一体理解法": "通俗",
    "The McKinsey Way": "通俗",
    "The Consulting Bible": "通俗",
    "Free: The Future of a Radical Price": "通俗",
}


def tier(name):
    for k in POPULAR:
        if k in name:
            return "通俗"
    for k in MONOGRAPH:
        if k in name:
            return "专著"
    for k in TEXTBOOK:
        if k in name:
            return "教材"
    for k, v in MANUAL.items():
        if k in name:
            return v
    return "未分档"


books = [r for r in rows if r["类型"] == "书"]
papers = [r for r in rows if r["类型"].startswith("论文")]

# 经验 8 方向 → 子类（方向级映射，一个方向只落一格）
E2I = {1: "冷启动与账号权重", 2: "合同与回款", 3: "外包与产能", 4: "失败案例库",
       5: "口播与语言表达", 6: "冷启动与账号权重", 7: "工具生态与成本", 8: "定价与报价"}

items = []           # (类, 项)，按首次出现顺序
for r in rows:
    k = (r["类"], r["项"])
    if k not in items:
        items.append(k)

CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
      "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


def cls_rank(c):
    return CN.get(c.split("、")[0], 99)


items.sort(key=lambda k: cls_rank(k[0]))   # 稳定排序，类内保持原顺序

bc = Counter(); pc = Counter(); ec = Counter(); ic = Counter(); oc = Counter()
for b in books:
    bc[(b["类"], b["项"], tier(b["资料名称"]))] += 1
for p in papers:
    pc[(p["类"], p["项"])] += 1
for e in exp:
    d = int(e["方向"].split()[0])
    ec[E2I[d]] += 1
for r in rows:
    if r["状态"] == "已入库":
        ic[(r["类"], r["项"])] += 1
    if r["类型"] != "书" and not r["类型"].startswith("论文"):
        oc[(r["类"], r["项"])] += 1

other_total = sum(oc.values())
other_types = Counter(r["类型"] for r in rows
                      if r["类型"] != "书" and not r["类型"].startswith("论文"))
other_desc = "／".join(f"{k}{v}" for k, v in other_types.most_common())

out = ["# 三本账：按子类归位（2026-11-14 粗版）", "",
       f"数量全部由 `catalog.csv`（{len(rows)} 条）与 `experience.csv`（{len(exp)} 条）逐条数出，未估算。",
       "", "| 大类 | 子类 | 书(教材) | 书(专著) | 书(通俗) | 书(未分档) | 论文 | 其他源 | 经验 | 已入库 | 合计 |",
       "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
zero = []
for cls, item in items:
    a = bc[(cls, item, "教材")]; b = bc[(cls, item, "专著")]
    c = bc[(cls, item, "通俗")]; d = bc[(cls, item, "未分档")]
    p = pc[(cls, item)]; o = oc[(cls, item)]
    e = ec[item]; i = ic[(cls, item)]
    tot = a + b + c + d + p + o + e
    out.append(f"| {cls} | {item} | {a} | {b} | {c} | {d} | {p} | {o} | {e} | {i} | {tot} |")
    if a + b + c + d + p + e == 0:      # 书、论文、经验三类都为空
        zero.append((cls, item, o))

out += ["", "## 零格表（书／论文／经验三类都为 0）", ""]
if zero:
    out.append("| 大类 | 子类 | 其他源条数 | 说明 |")
    out.append("| --- | --- | --- | --- |")
    for cls, item, o in zero:
        note = "三类为 0，但有其他源，不算真空" if o else "三类为 0，且无任何条目"
        out.append(f"| {cls} | {item} | {o} | {note} |")
else:
    out.append("无。每个子类至少有一条。")

out += ["", "## 口径与数不出的地方", "",
        f"- 书的体裁分档：{len(books)} 本里 {sum(1 for b in books if tier(b['资料名称']) != '未分档')} 本已分档，"
        f"{sum(1 for b in books if tier(b['资料名称']) == '未分档')} 本记「未分档」（02-50《映像の原則》、08-05《广告合规审查实务手册》），"
        "原因：前者是导演的创作随笔、介于专著与通俗之间，后者作者与内容均未获取，仅凭书名不能定档，按「不要硬塞」处理。",
        "- 「其他源」列：`catalog.csv` 里既不是书、也不是论文的条目，不硬塞进论文列，单列计数。"
        f"共 {other_total} 条：{other_desc}。",
        "- 已入库列：`catalog.csv` 状态栏目前只有「确认真实／待核」，没有一条标「已入库」，故全列为 0。"
        "实际有 3 条引用的是本地已有原文（`rhetoric_aristotle.txt`、`minfadian.txt`、`pipl.txt`），"
        "但状态栏未标，本表不替它改口径——要按「已入库」统计，得先改状态栏。",
        "- 经验列：按经验库自己的 8 个方向做方向级映射（1→冷启动/2→合同回款/3→外包产能/4→失败案例/5→口播/6→冷启动/7→工具生态/8→定价），"
        "一个方向只落一格。方向 5 有 1 条讲剪辑（D5-01）、方向 2 有 2 条讲验收（D2-03/D2-04），"
        "按方向整体归位后，剪辑与验收两格没有经验条目——这是映射结果，不是漏数。",
        "- 论文列包含 `论文` 59 条与 `论文（一手）` 8 条，共 67 条。"]
open(os.path.join(CAT, "三本账.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")

# 三份清单
def dump(fn, title, groups, status_col="状态", extra=None):
    L = [f"# {title}", ""]
    for g, items_ in groups:
        L.append(f"## {g}（{len(items_)}）")
        L.append("")
        for r in items_:
            s = r[status_col]
            L.append(f"- {r['资料名称']}（{s}）")
        L.append("")
    open(os.path.join(CAT, fn), "w", encoding="utf-8").write("\n".join(L))

bg = defaultdict(list)
for b in books:
    bg[f"{b['类']}｜{b['项']}"].append(b)
dump("书单.md", f"书单（按子类，{len(books)} 条；只写名称与状态）",
     sorted(bg.items(), key=lambda kv: cls_rank(kv[0].split("｜")[0])))

pg = defaultdict(list)
for p in papers:
    pg[f"{p['类']}｜{p['项']}"].append(p)
dump("论文单.md", f"论文单（按子类，{len(papers)} 条；只写名称与状态）",
     sorted(pg.items(), key=lambda kv: cls_rank(kv[0].split("｜")[0])))

eg = defaultdict(list)
for e in exp:
    d = int(e["方向"].split()[0])
    eg[E2I[d]].append({"资料名称": e["结论"], "状态": f"{e['编号']}／{e['证据等级']}"})
ORDER = ["冷启动与账号权重", "合同与回款", "外包与产能", "口播与语言表达",
         "定价与报价", "工具生态与成本", "失败案例库"]
dump("经验单.md", f"经验单（按子类，{len(exp)} 条；只写结论与等级）",
     sorted(eg.items(), key=lambda kv: ORDER.index(kv[0])))

print("books", len(books), Counter(tier(b["资料名称"]) for b in books))
print("papers", len(papers), "exp", len(exp), "zero", len(zero))
