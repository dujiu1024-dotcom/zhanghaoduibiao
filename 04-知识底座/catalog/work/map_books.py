#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把库内书籍逐本对到 77 个细类，输出书籍级与细类级两张 CSV。

2026-11-15 20:50 修复四个 bug（旧版由扫目录取数，导致合计与明细不平）：
1. 取数：改为读 kbase.db 的 books 层 docs，不再扫 books/ 目录；
   去重改为「书名归一」合成一组（同一本书多载体只算一次），不再用 (目录,文件名)。
2. 细类名：load_subs 原来用 it.split("/")[0] 截断，把「实验设计与A/B」截成「实验设计与A」；
   现只在 " / "（两侧带空格）时截断。RULES 里对不上 77 细类的名字直接报错退出，不再产出 "?"。
3. 合计：显式排除 "?"；单列「未匹配到细类」行，「明细 + 未匹配 = 合计」必须可验算。
4. 授权档：取 metadata.csv 的「质量分级」与「授权限制」，不再取 manifest 的「引用口径」。

口径提示：未归类的书按「背景知识」留在库里，可检索、可作理解用，但不计入 77 格覆盖度——
77 细类是按作业动作分的，不对应动作的专著不硬归。
"""
import csv
import os
import re
import sys
from collections import Counter

BASE = "/Users/longyi/project/账号对标/04-知识底座"
CAT = f"{BASE}/catalog/catalog.csv"
MAN = f"{BASE}/work/book-scout-4/oapen/manifest_oapen.csv"
OUTDIR = f"{BASE}/catalog/work"
P0DIR = "16-P0替代材料"
DAY = "20261115"


def norm(s):
    """归一化用于比对：只在 " / " 处截断翻译，保留书名内的 "/"。"""
    s = re.split(r"\s+/\s+", (s or "").strip())[0]
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
            cat[k] = re.split(r"\s+/\s+", it)[0].strip()
            order.append((k, cat[k], n[:2] if re.match(r"^\d{2}-", n) else "99"))
    subs = {}
    cnt = Counter()
    for k, name, big in order:
        cnt[big] += 1
        subs[k] = {"编号": f"{big}-{cnt[big]:02d}", "名称": name, "大类": big}
    return subs


def cell_map(subs):
    return {v["名称"]: v["编号"] for v in subs.values()}


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
    ("议程设置与框架", [r"agenda[- ]setting", r"\bframing\b", r"propaganda", r"public opinion"]),
    ("叙事结构与故事", [r"narrative", r"storytelling"]),
    ("口播与语言表达", [r"public speaking", r"oral communication"]),
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
    ("平台规则与舆情", [r"platform governance", r"content moderation", r"public sentiment"]),
    ("平台经营合规", [r"platform regulation", r"e-?commerce law"]),
    ("消费者保护", [r"consumer protection", r"consumer law"]),
    ("价格与促销合规", [r"price regulation", r"promotion law"]),
    ("认知偏差与判断启发", [r"\bbias", r"heuristic", r"judgment under uncertainty", r"decision making"]),
    ("说服与态度改变", [r"persuasion", r"attitude change", r"influence"]),
    ("承诺一致与门槛效应", [r"commitment and consistency", r"foot-in-the-door"]),
    ("情绪与唤醒", [r"emotion", r"arousal"]),
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


def books_docs():
    sys.path.insert(0, f"{BASE}/rag")
    import rag
    con = rag.connect()
    return list(con.execute(
        "select source_path, title from docs where source_path like '%/books/%' order by source_path"))


def load_license():
    m = {}
    for r in csv.DictReader(open(f"{BASE}/knowledge/sources/metadata.csv", encoding="utf-8-sig")):
        p = (r.get("本地路径") or "").strip()
        if not p:
            continue
        m[os.path.splitext(os.path.basename(p))[0]] = ((r.get("质量分级") or "").strip(),
                                                       (r.get("授权限制") or "").strip())
    return m


def tier(q, lic):
    """两档：可引原句 / 可转述。只认 metadata。"""
    return "可引原句" if (q == "可引用" or lic.startswith("无限制")) else "可转述"


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
        m[stem] = {"编号": r["编号"], "书名": r.get("书名", ""),
                   "格": (r.get("命中格") or "").split("；")[0].strip()}
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


def title_key(stem, title):
    t = (title or stem).lower()
    t = re.sub(r"^(ocr-|pg\d+\s*)", "", t)
    t = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", t)
    return t or stem


def main():
    subs = load_subs()
    c2s = cell_map(subs)
    man = load_manifest()
    lic = load_license()

    # 规则名校验：对不上就报错退出，禁止静默产出 "?"
    bad = sorted({n for n, _ in RULES if n not in c2s})
    if bad:
        sys.exit("错：RULES 里这些细类名在 77 细类中不存在，请先改名再跑：\n  " + "\n  ".join(bad))

    # 分组：同一本书多载体只算一次
    groups = {}
    for sp, title in books_docs():
        d = os.path.basename(os.path.dirname(sp))
        stem = os.path.splitext(os.path.basename(sp))[0]
        groups.setdefault(title_key(stem, title), []).append(
            {"路径": sp, "目录": d, "stem": stem, "书名": (title or stem)[:80]})

    rows, p0 = [], []
    for _, carriers in groups.items():
        rep = next((c for c in carriers if (man.get(c["stem"]) or {}).get("格")), carriers[0])
        ok = any(tier(*lic.get(c["stem"], ("", ""))) == "可引原句" for c in carriers)
        rec = {"目录": rep["目录"], "路径": rep["路径"], "书名": rep["书名"], "stem": rep["stem"],
               "引用口径": "可引原句" if ok else "可转述", "载体数": len(carriers)}
        (p0 if all(c["目录"] == P0DIR for c in carriers) else rows).append(rec)

    cnt, cite, trans, lists = Counter(), Counter(), Counter(), {}
    unmatched = []
    for r in rows:
        codes, basis = [], ""
        m = man.get(r["stem"])
        if m and m.get("格"):
            s = CELL2SUB.get(m["格"])
            if s in c2s:
                codes = [c2s[s]]
                basis = f"manifest 命中格「{m['格']}」"
        if not codes:
            hits = match_rules((man.get(r["stem"]) or {}).get("书名") or clean_title(r["stem"]))
            codes = list(dict.fromkeys(c2s[n] for n, _ in hits))
            basis = "书名关键词" if codes else "未匹配"
        r["细类"] = "；".join(f"{c} {v['名称']}" for c, v in
                             ((x, next(y for y in subs.values() if y["编号"] == x)) for x in codes)) or "未匹配到细类"
        r["依据"] = basis
        if not codes:
            unmatched.append(r)
            continue
        for c in codes:
            cnt[c] += 1
            lists.setdefault(c, []).append(r["书名"])
            (cite if r["引用口径"] == "可引原句" else trans)[c] += 1

    names = {v["编号"]: v["名称"] for v in subs.values()}

    os.makedirs(OUTDIR, exist_ok=True)
    p1 = f"{OUTDIR}/书籍细类归位-逐本-{DAY}.csv"
    with open(p1, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["目录", "路径", "书名", "细类", "依据", "引用口径", "载体数"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    p2 = f"{OUTDIR}/细类归位汇总-77-{DAY}.csv"
    with open(p2, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["# 2026-11-15 20:50 复核发现旧表合计与明细不平，已由本表替代，旧数作废；"
                    "本表以 kbase.db 为唯一事实源，可引/可转述取自 metadata 授权字段"])
        w.writerow(["# 未归类的书按「背景知识」留库，可检索、可作理解用，但不计入 77 格覆盖度"
                    "——77 细类按作业动作划分，不对应动作的专著不硬归、不开新细类"])
        w.writerow(["细类编号", "细类名称", "本数", "其中可引原句", "其中可转述", "书名清单（前 6 本）"])
        for v in sorted(subs.values(), key=lambda x: x["编号"]):
            c = v["编号"]
            w.writerow([c, names[c], cnt[c], cite[c], trans[c], "；".join(lists.get(c, [])[:6])])
        w.writerow(["未归类", "背景知识·不计入覆盖度", len(unmatched),
                    sum(1 for r in unmatched if r["引用口径"] == "可引原句"),
                    sum(1 for r in unmatched if r["引用口径"] == "可转述"), ""])
        w.writerow([])
        w.writerow(["合计", f"按细类累加（含 {sum(1 for r in rows if r['细类'].count('；') > 0)} 本落两个细类，重复计；含未归类）",
                    sum(cnt.values()) + len(unmatched),
                    sum(cite.values()) + sum(1 for r in unmatched if r["引用口径"] == "可引原句"),
                    sum(trans.values()) + sum(1 for r in unmatched if r["引用口径"] == "可转述"), ""])
        w.writerow(["合计", "去重后总数（按书名归一去重，不含 P0 替代材料）", len(rows),
                    sum(1 for r in rows if r["引用口径"] == "可引原句"),
                    sum(1 for r in rows if r["引用口径"] == "可转述"), ""])
        w.writerow(["附", "P0 替代材料（非原书，不计入本数）", len(p0),
                    sum(1 for r in p0 if r["引用口径"] == "可引原句"),
                    sum(1 for r in p0 if r["引用口径"] == "可转述"), ""])

    print(f"书(去P0)={len(rows)}｜P0={len(p0)}｜未匹配到细类={len(unmatched)}｜"
          f"可引={sum(1 for r in rows if r['引用口径']=='可引原句')}｜"
          f"可转述={sum(1 for r in rows if r['引用口径']=='可转述')}")
    print(f"校验 明细{sum(cnt.values())} + 未归类{len(unmatched)} = {sum(cnt.values()) + len(unmatched)}")
    print(f"逐本 → {p1}\n汇总 → {p2}")


if __name__ == "__main__":
    main()
