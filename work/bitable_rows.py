import csv, json, re

cat = list(csv.DictReader(open('04-知识底座/catalog/catalog.csv', encoding='utf-8-sig')))
avail = {r['编号']: r for r in csv.DictReader(open('04-知识底座/catalog/可得性.csv', encoding='utf-8-sig'))}
NEW = ["脚本结构", "私信承接", "成交与异议", "对标拆解"]
FOCUS = {"钩子与注意力", "口播与语言表达", "推荐机制", "冷启动与账号权重", "私域承接与微信运营",
         "转化路径与漏斗设计", "定价与报价", "合同与回款", "广告法与宣传合规", "个保法与数据安全",
         "违规判定与发布前审（并库原文）", "对标拆解"}
PAIR = "错误做法样本（反面教材）"

order, agg = [], {}
for r in cat:
    k = (r['类'], r['项'])
    if k not in agg:
        agg[k] = {'n': 0, 'ink': 0, 'types': {}}
        order.append(k)
    a = agg[k]; a['n'] += 1
    a['ink'] += 1 if r['状态'] == '已入库' else 0
    a['types'][r['类型']] = a['types'].get(r['类型'], 0) + 1
for nm in NEW:
    cls = '二、传播与内容' if nm == '脚本结构' else '四、用户与市场' if nm == '对标拆解' else '五、客户运营与转化'
    if (cls, nm) not in agg:
        agg[(cls, nm)] = {'n': 0, 'ink': 0, 'types': {}}; order.append((cls, nm))


def motive(a):
    if a['n'] == 0: return '还没开始采'
    if a['ink'] > 0: return '已开格，待补到 3 条'
    papers = sum(v for t, v in a['types'].items() if '论文' in t)
    if papers * 3 >= a['n']: return '期刊付费墙'
    books = sum(v for t, v in a['types'].items() if t == '书')
    if books * 10 >= a['n'] * 8: return '只有书目，没开采'
    return '只有二手'


def num(x): return x if isinstance(x, (int, float)) else None


t1 = []
for k in order:
    a = agg[k]; eff = a['n'] - (1 if k[1] == PAIR else 0)
    t1.append({"细类": k[1], "大类": k[0], "现有条数": a['n'], "合格条数": eff,
               "硬底线": "过" if eff >= 1 else "不过", "合格线": "过" if eff >= 3 else "不过",
               "12重点类": "是" if k[1] in FOCUS else "否", "已有原文条数": a['ink'],
               "缺口条数": max(0, 3 - eff), "主要卡点": motive(a)})
json.dump(t1, open('/tmp/t1.json', 'w'), ensure_ascii=False)

TYPE = {'书': '书', '论文': '论文', '论文（一手）': '论文', '法规': '法规', '官方文档': '官方文档',
        '官方文档（一手）': '官方文档', '专利（一手）': '专利', '技术博客（一手）': '博客',
        '分享': '分享', '方法论': '方法论'}
t2 = []
for r in cat:
    av = avail.get(r['编号'], {})
    m = re.search(r'knowledge/sources/([a-zA-Z0-9_\-/\.]+\.(?:txt|pdf))', r['真实性依据'])
    q = '仅参考·与官方口径冲突' if '仅参考' in r['真实性依据'] else ('可引用' if r['状态'] == '已入库' else '待核')
    # 用途按「质量档」字段判定，不做同句双词匹配（06-46 教训）
    use = '只能当反面教材' if q == '仅参考·与官方口径冲突' else ('可直接引用' if r['状态'] == '已入库' else '只能指路')
    t2.append({"名称": r['资料名称'], "编号": r['编号'], "类型": [TYPE.get(r['类型'], '分享')],
               "大类": r['类'], "细类": r['项'], "质量档": [q],
               "可得性": [av.get('可得性') or '未标'],
               "采集时间": av.get('采集时间', '未获取'), "入库时间": av.get('入库时间', '未入库'),
               "文件位置": m.group(1) if m else '', "来源渠道": av.get('渠道或原因', ''),
               "备注": r['真实性依据'][:180], "原始状态": r['状态'], "这一条能干什么": [use]})
json.dump(t2, open('/tmp/t2.json', 'w'), ensure_ascii=False)

wait = []
for numx, a in avail.items():
    if a['可得性'] == '不可得':
        wait.append({"名称": a['资料名称'], "编号": numx, "卡在哪": a['渠道或原因'],
                     "试过哪些渠道": "OpenAlex / DOI 直链、出版社页面", "下一步": ["换渠道"],
                     "最后尝试时间": "2026-11-14"})
extra = [("抖音创作者中心", "登录墙，无公开镜像", "官网、搜索引擎", "等用户"),
         ("混沌学园", "付费墙", "官网", "等用户"),
         ("生财有术", "付费墙、无公开目录", "官网", "等用户"),
         ("Demand Curve", "页面 404；archive.org 本机不可达", "官网、Wayback", "换渠道"),
         ("CSDN 起号 SOP", "正文未取到", "搜索引擎", "换渠道"),
         ("私信承接（细类）", "平台无私信规则专页；话术帖未取", "抖音规则中心、知乎、V2EX", "换渠道"),
         ("成交与异议（细类）", "SPIN/RAIN 付费课程；OA 论文未取", "arXiv、SSRN、机构库", "换渠道"),
         ("对标拆解（细类）", "编码手册多为付费教材", "OpenAlex、机构库", "换渠道")]
for nm, why, ch, nxt in extra:
    wait.append({"名称": nm, "编号": "—", "卡在哪": why, "试过哪些渠道": ch,
                 "下一步": [nxt], "最后尝试时间": "未记录"})
json.dump(wait, open('/tmp/t3.json', 'w'), ensure_ascii=False)

t4 = []
for row in csv.DictReader(open('04-知识底座/catalog/采集入库台账.csv', encoding='utf-8-sig')):
    t4.append({"批次号": row['批次号'], "开始时间": row['开始时间'], "结束时间": row['结束时间'],
               "采集条数": int(row['采集条数'] or 0), "入库条数": int(row['入库条数'] or 0),
               "待入库条数": int(row['待入库条数'] or 0), "渠道": row['渠道'], "卡住原因": row['卡住原因']})
json.dump(t4, open('/tmp/t4.json', 'w'), ensure_ascii=False)
print(len(t1), len(t2), len(wait), len(t4))
