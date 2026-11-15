#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 books/ 下全部书籍逐本对到 77 个细类，输出书籍级与细类级两张 CSV。

依据：
1. OAPEN 批直接取 manifest_oapen.csv 的「命中格」（下载时按主题判过）；
2. 其余按书的正题/副题关键词对齐细类定义（规则见 RULES，命中词写进依据列）；
3. 对不上的一律「未归类」，不硬塞。
"""
import csv
import os
import re
from collections import Counter, OrderedDict

BASE = "/Users/longyi/project/账号对标/04-知识底座"
CAT = f"{BASE}/catalog/catalog.csv"
MAN = f"{BASE}/work/book-scout-4/oapen/manifest_oapen.csv"
BOOKS = f"{BASE}/knowledge/sources/books"
OUTDIR = f"{BASE}/catalog/work"


def norm(s):
    s = (s or "").split("/")[0]
    s = re.sub(r"[（(].*?[)）]", "", s)
    s = re.sub(r"[\s·:：\-—，,。.、]+", "", s)
    return s.lower()


def load_subs():
    """77 个细类：catalog.csv 的「项」归一化去重，编号 = 大类号-类内序号。"""
    rows = list(csv.DictReader(open(CAT, encoding="utf-8-sig")))
    order, cat = [], {}
    for r in rows:
        it = (r.get("项") or "").strip()
        n = (r.get("编号") or "").strip()
        if not it:
            continue
        k = norm(it)
        if k not in cat:
            cat[k] = it.split("/")[0].strip()
            order.append((k, cat[k], n[:2] if re.match(r"^\d{2}-", n) else "99"))
    subs = OrderedDict()
    cnt = Counter()
    for k, name, big in order:
        cnt[big] += 1
        subs[k] = {"编号": f"{big}-{cnt[big]:02d}", "名称": name, "大类": big}
    return subs


# 细类名 → 编号（由 load_subs 填）
def cell_map(subs):
    return {v["名称"]: v["编号"] for v in subs.values()}


# 关键词规则：按优先级从窄到宽，命中即止（除多细类允许并列）
RULES = [
    ("从众与社会认同", [r"the crowd a study of the popular mind", r"lois de l imitation", r"imitation", r"conformity", r"social proof", r"social influence"]),
    ("身份认同与自我呈现", [r"leisure class", r"conspicuous", r"self-presentation", r"identity"]),
    ("群体情境与旁观者效应", [r"group mind", r"group psychology", r"bystander", r"group dynamics"]),
    ("互惠、社会交换与地位", [r"moral sentiments", r"reciprocity", r"social exchange"]),
    ("修辞与说服性写作", [r"elements of style", r"\brhetoric", r"persuasive writing", r"copywriting"]),
    ("视听语言与镜头", [r"photoplay", r"cinematograph", r"film theory"]),
    ("钩子与注意力", [r"attention econom", r"\bhooks?\b", r"captology", r"markets of attention", r"misinformation"]),
    ("知识产权", [r"free culture", r"copyright", r"intellectual property", r"\bpatent"]),
    ("B2B采购决策链", [r"\bB2B\b", r"\bbtb\b", r"procurement", r"purchasing", r"supplier selection", r"buyer-supplier"]),
    ("个体老板与小额采购决策", [r"small and medium enterprise", r"\bSMEs?\b", r"small firms?", r"micro-?enterprise", r"family business"]),
    ("定价与报价", [r"\bpricing\b", r"\bprice\b", r"prices", r"revenue management", r"tariff", r"monetiz"]),
    ("商业模式设计", [r"business model", r"platform strategy", r"value proposition"]),
    ("成本与税务", [r"\bcosts?\b", r"taxation", r"tax policy"]),
    ("外包与产能", [r"outsourc", r"offshor", r"capacity planning"]),
    ("经营核算与现金流", [r"cash flow", r"financial accounting", r"management accounting", r"financial statement"]),
    ("一人公司的协作与招人", [r"freelanc", r"self-?employ", r"solo self", r"gig work", r"precarity"]),
    ("销售与谈判", [r"never split the difference", r"\bselling\b", r"\bsales\b", r"negotiat", r"salesmanship"]),
    ("方案书与报价呈现", [r"proposal writing", r"bid", r"tender"]),
    ("交付与验收", [r"\bdelivery\b", r"project management", r"acceptance", r"quality assurance"]),
    ("合同与回款", [r"\bcontract", r"payment collection", r"credit management"]),
    ("客户成功与转介绍", [r"noncomplainer", r"complaint management", r"customer success", r"customer retention", r"loyalty", r"referral"]),
    ("私域承接与微信运营", [r"private domain", r"wechat", r"weixin"]),
    ("私信承接", [r"direct message", r"\bDM\b"]),
    ("成交与异议", [r"objection handling", r"closing the sale"]),
    ("转化路径与漏斗设计", [r"\bfunnel\b", r"conversion rate", r"customer journey", r"purchase funnel"]),
    ("线索分级与询盘", [r"lead generation", r"lead qualification", r"inquiry"]),
    ("需求转译（翻译方法）", [r"requirement engineering", r"requirement analysis"]),
    ("定位与差异化", [r"positioning", r"differentiat", r"\bbranding\b", r"brand strategy", r"competitive advantage"]),
    ("钩子与注意力", [r"attention econom", r"\bhooks?\b", r"captology"]),
    ("修辞与说服性写作", [r"\brhetoric", r"persuasive writing", r"copywriting"]),
    ("议程设置与框架", [r"agenda[- ]setting", r"\bframing\b", r"propaganda", r"public opinion"]),
    ("叙事结构与故事", [r"narrative", r"storytelling"]),
    ("口播与语言表达", [r"public speaking", r"oral communication"]),
    ("视觉语言与镜头", []),
    ("传播模型与媒介环境", [r"communication theory", r"media studies", r"media environment", r"mass media"]),
    ("选题与需求信号", [r"trend", r"demand signal"]),
    ("脚本结构", [r"screenwrit", r"script"]),
    ("统计与因果推断", [r"causal inference", r"statistic", r"econometric", r"regression", r"causal analysis", r"quantitative method", r"panel data", r"multilevel model", r"longitudinal model"]),
    ("实验设计与A/B", [r"experiment", r"randomized", r"\bA/B\b", r"field experiment", r"replication"]),
    ("抽样与样本偏差", [r"sampling", r"survey method", r"sample bias", r"research method", r"research design", r"demographic"]),
    ("指标口径与度量", [r"measurement", r"\bmetrics\b", r"indicator"]),
    ("复盘与归因方法", [r"attribution", r"retrospective", r"after[- ]action"]),
    ("用户访谈与观察", [r"interview", r"ethnograph", r"qualitative method", r"observation", r"in the field"]),
    ("需求识别与JTBD", [r"jobs[- ]to[- ]be[- ]done", r"needs assessment"]),
    ("客户画像与分层", [r"segmentation", r"customer profile", r"persona"]),
    ("赛道结构与竞争格局", [r"industry structure", r"market structure", r"competition policy", r"competitive landscape"]),
    ("市场调研与行业数据", [r"market research", r"industry data", r"market analysis"]),
    ("消费者行为与决策旅程", [r"principles of marketing", r"consumer behavio", r"consumer decision", r"buying behavio"]),
    ("行业场景知识", [r"industry case", r"sector study"]),
    ("行业方案库", [r"industrial services", r"industry solution", r"solution design"]),
    ("对标拆解", [r"benchmark", r"competitive analysis"]),
    ("推荐机制", [r"recommendation system", r"recommender", r"algorithmic feed"]),
    ("冷启动与账号权重", [r"cold start", r"account growth"]),
    ("搜索与关键词", [r"search engine", r"\bSEO\b", r"keyword research"]),
    ("投放与ROI", [r"emarketing", r"e-?marketing", r"digital marketing", r"advertising", r"\bad spend", r"\bROI\b", r"media buying"]),
    ("截流与矩阵", [r"traffic intercept", r"account matrix"]),
    ("跨平台迁移与改写", [r"cross-?platform", r"repurpos"]),
    ("广告法与宣传合规", [r"advertising law", r"advertising regulation"]),
    ("个保法与数据安全", [r"data protection", r"privacy", r"\bGDPR\b", r"personal data"]),
    ("知识产权", [r"copyright", r"intellectual property", r"\bpatent"]),
    ("平台规则与舆情", [r"platform governance", r"content moderation", r"public sentiment"]),
    ("平台经营合规", [r"platform regulation", r"e-?commerce law"]),
    ("消费者保护", [r"consumer protection", r"consumer law"]),
    ("价格与促销合规", [r"price regulation", r"promotion law"]),
    ("认知偏差与判断启发", [r"\bbias", r"heuristic", r"judgment under uncertainty", r"decision making"]),
    ("说服与态度改变", [r"persuasion", r"attitude change", r"influence"]),
    ("从众与社会认同", [r"conformity", r"social proof", r"social influence"]),
    ("承诺一致与门槛效应", [r"commitment and consistency", r"foot-in-the-door"]),
    ("互惠、社会交换与地位", [r"reciprocity", r"social exchange", r"status"]),
    ("情绪与唤醒", [r"emotion", r"arousal"]),
    ("身份认同与自我呈现", [r"identity", r"self-presentation"]),
    ("群体情境与旁观者效应", [r"bystander", r"group dynamics"]),
    ("利他与价值前置", [r"altruism", r"prosocial"]),
    ("心理阻抗与说服反噬", [r"reactance", r"backfire"]),
    ("FDE技术图谱", [r"\bFDE\b"]),
    ("失败案例库", [r"failure", r"postmortem"]),
    ("工具生态与成本", [r"\btools?\b", r"software ecosystem"]),
    ("AI模型能力与成本边界（只收实时源）", [r"\bLLM\b", r"language model"]),
]

CELL2SUB = {
    "定价与报价": "定价与报价", "销售与谈判": "销售与谈判", "定位与差异化": "定位与差异化",
    "交付与验收": "交付与验收", "B2B采购决策链": "B2B采购决策链",
    "行业场景知识": "行业场景知识", "行业方案库": "行业方案库",
    "商业模式设计": "商业模式设计", "个体老板与小额采购": "个体老板与小额采购决策",
    "一人公司的协作与招人": "一人公司的协作与招人",
}


def load_license():
    """授权限制 → 三档：可引原文 / 可转述 / 不可用 / 未知。"""
    m = {}
    for r in csv.DictReader(open(f"{BASE}/knowledge/sources/metadata.csv", encoding="utf-8-sig")):
        p = (r.get("本地路径") or "").strip()
        v = (r.get("授权限制") or "").strip()
        if not p:
            continue
        m[os.path.splitext(os.path.basename(p))[0]] = v
    return m


def tier(v):
    """两档：可引原文 / 可转述。保留所有权利也归可转述（2026-11-15 第二次裁定）。"""
    if not v:
        return "未知"
    if "保留所有权利" in v:
        return "可转述"
    if v.startswith("无限制") or "可引用原文" in v or ("CC BY-SA" in v and "NC" not in v):
        return "可引原文"
    return "可转述"


def clean_title(fn):
    t = os.path.splitext(fn)[0]
    t = re.sub(r"^(ocr-)?(Files__|Option-|Core-)", "", t)
    t = re.sub(r"^[A-Za-z]+-\d+-", "", t)
    t = re.sub(r"^Files__(Core|Option)__", "", t)
    t = re.sub(r"\.(txt|md|pdf)$", "", t)
    t = re.sub(r"[._]+", " ", t)
    t = re.sub(r"\b[0-9a-f]{24,}\b", "", t)
    return t.strip(" -_")


def load_manifest():
    m = {}
    for r in csv.DictReader(open(MAN, encoding="utf-8-sig")):
        if (r.get("下载状态") or "").strip() != "OK":
            continue
        stem = os.path.splitext(os.path.basename(r.get("文件") or ""))[0]
        cell = (r.get("命中格") or "").split("；")[0].strip()
        m[stem] = {"编号": r["编号"], "书名": r.get("书名", ""), "格": cell,
                   "可引用": (r.get("引用口径") or "").strip()}
    return m


def match_rules(title):
    low = re.sub(r"[-_]+", " ", title).lower()
    hits = []
    for sub, pats in RULES:
        for p in pats:
            if re.search(p, low, re.I):
                hits.append((sub, p))
                break
    return hits


def main():
    subs = load_subs()
    c2s = cell_map(subs)
    man = load_manifest()
    lic = load_license()
    books = []
    seen = {}
    for d in sorted(os.listdir(BOOKS)):
        p = os.path.join(BOOKS, d)
        if not os.path.isdir(p):
            continue
        for f in sorted(os.listdir(p)):
            fp = os.path.join(p, f)
            if not os.path.isfile(fp) or f.endswith(".csv") or f.startswith("_"):
                continue
            stem = os.path.splitext(f)[0]
            key = (d, stem)
            ext = os.path.splitext(f)[1].lower()
            if key in seen:
                # 同一本书的多种载体只算 1 本，优先 md > txt > pdf
                rank = {".md": 0, ".txt": 1, ".pdf": 2}
                if rank.get(ext, 9) < rank.get(os.path.splitext(seen[key][1])[1].lower(), 9):
                    seen[key] = (fp, f)
                continue
            seen[key] = (fp, f)
    for (d, _), (fp, f) in sorted(seen.items()):
        books.append((d, f, fp))

    rows = []
    for d, f, fp in books:
        stem = os.path.splitext(f)[0]
        m = man.get(stem)
        title = (m["书名"] if m else "") or clean_title(f)
        subs_hit, basis, citable = [], "", "未知"
        if m and m.get("格"):
            sub = CELL2SUB.get(m["格"])
            if sub and sub in c2s:
                subs_hit = [sub]
                basis = f"manifest 命中格「{m['格']}」"
                citable = "可引用" if "可引用" in m["可引用"] and "不" not in m["可引用"] else ("仅参考" if "仅参考" in m["可引用"] else "不可引用")
        if not subs_hit:
            hits = match_rules(title)
            if hits:
                subs_hit = [h[0] for h in hits]
                basis = "书名关键词：" + "；".join(f"{h[0]}←{h[1]}" for h in hits)
        if not subs_hit:
            low = re.sub(r"[-_]+", " ", title).lower()
            if re.search(r"ddia|data intensive", low):
                basis = "未归类：争点在 09-01 FDE技术图谱（数据系统架构属技术底座）与 09-04 工具生态与成本（选型成本）之间，两者定义都不精确覆盖"
            elif re.search(r"pragmatic programmer", low):
                basis = "未归类：争点在 09-01 FDE技术图谱（工程实践）与 09-04 工具生态与成本（工具链）之间，偏个人工程习惯，非选型成本"
            elif re.search(r"dynamics in logistics", low):
                basis = "未归类：争点在 04-06 行业场景知识（物流行业）与 09-02 行业方案库（服务方案）之间，该书是运筹建模教材，两侧都不精确"
            elif re.search(r"small ones|periphery", low):
                basis = "未归类：争点在 04-09 个体老板与小额采购决策（small ones）与 04-05 赛道结构（periphery），副题是政策—社会互动，主体不是采购决策"
            elif re.search(r"organizational behavio", low):
                basis = "未归类：争点在 07-06 一人公司的协作与招人（组织与人员）与 01-05 互惠、社会交换与地位（组织内社会交换）之间"
            elif re.search(r"human nature|human nature in politics", low):
                basis = "未归类：属「人性」总论，01 类细类均为具体机制（偏差/从众/互惠等），无总论型细类可落"
            elif re.search(r"educational psychology", low):
                basis = "未归类：教育心理学教材，01 类细类均针对说服与判断，非学习与教学场景"
            elif re.search(r"principles of|introduction to|handbook of|textbook|essentials of|\b\d+e\b", low):
                basis = "未归类：通用学科教材，内容跨多个细类，无单一归属"
            elif d.startswith("00"):
                basis = "未归类：学术专著（社会学/心理学/传播学分支），细类定义为业务操作层，无可对应"
            elif re.search(r"sociolog|anthropolog|political science|philosoph", low):
                basis = "未归类：学科基础理论，与账号经营无直接对应"
            else:
                basis = "未归类：书名未命中细类定义关键词，需人工判争点"
        rows.append({"目录": d, "文件名": f, "书名": title,
                     "细类": "；".join(f"{c2s.get(s, '?')} {s}" for s in subs_hit) or "未归类",
                     "依据": basis, "引用口径": tier(lic.get(stem, "")),
                     "原编号": (m or {}).get("编号", "")})

    # 细类汇总
    cnt = Counter()
    cite1 = Counter()
    cite2 = Counter()
    names = {}
    for r in rows:
        for part in r["细类"].split("；"):
            if part == "未归类":
                continue
            code = part.split(" ")[0]
            cnt[code] += 1
            names[code] = part[len(code) + 1:]
            if r["引用口径"] == "可引原文":
                cite1[code] += 1
            elif r["引用口径"] == "可转述":
                cite2[code] += 1
    unclass = sum(1 for r in rows if r["细类"] == "未归类")

    os.makedirs(OUTDIR, exist_ok=True)
    day = "20261115"
    p1 = f"{OUTDIR}/书籍细类归位-逐本-{day}.csv"
    with open(p1, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["目录", "文件名", "书名", "细类", "依据", "引用口径", "原编号"])
        w.writeheader()
        w.writerows(rows)

    p2 = f"{OUTDIR}/细类归位汇总-77-{day}.csv"
    with open(p2, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["细类编号", "细类名称", "本数", "书名清单", "可引原文本数", "可转述本数"])
        bysub = {}
        for r in rows:
            for part in r["细类"].split("；"):
                if part == "未归类":
                    continue
                code = part.split(" ")[0]
                bysub.setdefault(code, []).append(r["书名"][:60])
        for v in sorted(subs.values(), key=lambda x: x["编号"]):
            code, name = v["编号"], v["名称"]
            lst = bysub.get(code, [])
            w.writerow([code, name, len(lst), "；".join(lst), cite1[code], cite2[code]])
        # 未归类单列一行，保证两列相加等于总本数
        unc = [r for r in rows if r["细类"] == "未归类"]
        w.writerow(["未归类", "不落任何细类", len(unc), "；".join(r["书名"][:60] for r in unc),
                    sum(1 for r in unc if r["引用口径"] == "可引原文"),
                    sum(1 for r in unc if r["引用口径"] == "可转述")])
        # 合计两行：累加口径（多细类重复计）与唯一书口径
        w.writerow(["合计", "按细类累加（18 本多细类重复计）", sum(cnt.values()) + len(unc), "",
                    sum(cite1.values()) + sum(1 for r in unc if r["引用口径"] == "可引原文"),
                    sum(cite2.values()) + sum(1 for r in unc if r["引用口径"] == "可转述")])
        w.writerow(["合计", "按唯一书去重（应等于总本数）", len(rows), "",
                    sum(1 for r in rows if r["引用口径"] == "可引原文"),
                    sum(1 for r in rows if r["引用口径"] == "可转述")])

    print(f"书籍总数={len(rows)} 未归类={unclass} 有书细类={len([c for c in cnt if cnt[c]>0])} 零本细类={77-len([c for c in cnt if cnt[c]>0])}")
    print(f"逐本 → {p1}")
    print(f"汇总 → {p2}")
    top = cnt.most_common(8)
    print("命中最多:", [(c, n, names.get(c, '')) for c, n in top])


if __name__ == "__main__":
    main()
