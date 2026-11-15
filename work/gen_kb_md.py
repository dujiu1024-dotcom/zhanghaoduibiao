import csv, re

cat = list(csv.DictReader(open('04-知识底座/catalog/catalog.csv', encoding='utf-8-sig')))
avail = {r['编号']: r for r in csv.DictReader(open('04-知识底座/catalog/可得性.csv', encoding='utf-8-sig'))}

NEW = ["脚本结构", "私信承接", "成交与异议", "对标拆解"]
FOCUS = {"钩子与注意力", "口播与语言表达", "推荐机制", "冷启动与账号权重", "私域承接与微信运营",
         "转化路径与漏斗设计", "定价与报价", "合同与回款", "广告法与宣传合规", "个保法与数据安全",
         "违规判定与发布前审（并库原文）", "对标拆解"}

order, agg = [], {}
for r in cat:
    k = (r['类'], r['项'])
    if k not in agg:
        agg[k] = {'n': 0, 'ink': 0, 'types': {}}
        order.append(k)
    a = agg[k]
    a['n'] += 1
    a['ink'] += 1 if r['状态'] == '已入库' else 0
    a['types'][r['类型']] = a['types'].get(r['类型'], 0) + 1

for nm in NEW:
    cls = '二、传播与内容' if nm == '脚本结构' else '四、用户与市场' if nm == '对标拆解' else '五、客户运营与转化'
    k = (cls, nm)
    if k not in agg:
        agg[k] = {'n': 0, 'ink': 0, 'types': {}}
        order.append(k)


def motive(a):
    if a['ink'] > 0 and a['n'] >= 3:
        return '—'
    if a['ink'] > 0:
        return '已开格，待补到 3 条'
    if a['n'] == 0:
        return '还没开始采'
    papers = sum(v for t, v in a['types'].items() if '论文' in t)
    if papers * 3 >= a['n']:
        return '期刊付费墙'
    books = sum(v for t, v in a['types'].items() if t == '书')
    if books * 10 >= a['n'] * 8:
        return '只有书目，没开采'
    return '只有二手'


rows = []
for k in order:
    a = agg[k]
    eff = a['n'] - (1 if k[1] == '错误做法样本（反面教材）' else 0)
    rows.append((k[0], k[1], a['n'], '过' if eff >= 1 else '不过', '过' if eff >= 3 else '不过',
                 '是' if k[1] in FOCUS else '', a['ink'], max(0, 3 - eff), motive(a)))

L = ["# 004 新媒体操盘智能体｜A 库清单（2026-11-14）", "",
     f"细类 {len(rows)} 个，条目 {len(cat)} 条。口径：硬底线≥1、合格线≥3；「错误做法样本」按成对计 1 条（2 条原始条目→有效 1）。", "",
     "## 主表：77 个细类聚合", "",
     "| 大类 | 细类 | 现有条数 | 硬底线(≥1) | 合格线(≥3) | 12重点类 | 已有原文 | 缺口(差几条到3) | 卡在哪 |",
     "| --- | --- | ---: | --- | --- | --- | ---: | ---: | --- |"]
for r in rows:
    L.append("| " + " | ".join(str(x) for x in r) + " |")


def kind(t):
    return {'法规': '法规', '官方文档': '官方', '书': '原著', '论文': '论文', '论文（一手）': '论文',
            '分享': '二手', '方法论': '二手', '专利（一手）': '论文', '技术博客（一手）': '二手',
            '官方文档（一手）': '官方'}.get(t, '二手')


ink = [r for r in cat if r['状态'] == '已入库']
L += ["", "## 附表一：已入库清单（有本地原文）", "", f"共 {len(ink)} 条。", "",
      "| 编号 | 名称 | 类型 | 质量档 | 文件位置 | 出处定位方式 |", "| --- | --- | --- | --- | --- | --- |"]
for r in ink:
    m = re.search(r'knowledge/sources/([a-zA-Z0-9_\-/\.]+\.(?:txt|pdf))', r['真实性依据'])
    path = m.group(1) if m else '见依据栏'
    q = '仅参考·与官方口径冲突' if '仅参考' in r['真实性依据'] else ('摘录·非逐字' if '摘录' in r['真实性依据'] else '可引用')
    loc = '条号/行号（依据栏写明）' if ('条' in r['真实性依据'] and '第' in r['真实性依据']) else '文首来源行＋章节标题'
    L.append(f"| {r['编号']} | {r['资料名称']} | {kind(r['类型'])} | {q} | {path} | {loc} |")

wait = []
for num, a in avail.items():
    if a['可得性'] == '不可得':
        wait.append((num, a['资料名称'], a['渠道或原因'], 'OpenAlex / DOI 直链、出版社页面', '换渠道或等用户'))
wait += [
    ("—", "抖音创作者中心", "登录墙，无公开镜像", "官网、搜索引擎", "等用户登录导出"),
    ("—", "混沌学园", "付费墙", "官网", "等用户"),
    ("—", "生财有术", "付费墙、无公开目录", "官网", "等用户"),
    ("—", "Demand Curve", "页面 404；archive.org 本机不可达", "官网、Wayback", "换镜像或放弃"),
    ("—", "CSDN 起号 SOP", "正文未取到", "搜索引擎", "换渠道"),
    ("—", "私信承接（细类）", "平台无私信规则专页；话术帖未取", "抖音规则中心、知乎、V2EX", "改采官方客服文档＋E2 帖"),
    ("—", "成交与异议（细类）", "SPIN/RAIN 为付费课程；OA 论文未取", "arXiv、SSRN、机构库", "换 OA 论文"),
    ("—", "对标拆解（细类）", "编码手册多为付费教材", "OpenAlex、机构库", "换 OA 编码手册"),
]
L += ["", "## 附表二：待取清单", "", f"共 {len(wait)} 条。", "",
      "| 编号 | 名称 | 卡在哪 | 试过哪些渠道 | 下一步 |", "| --- | --- | --- | --- | --- |"]
for w in wait:
    L.append("| " + " | ".join(str(x) for x in w) + " |")

open('_kb.md', 'w', encoding='utf-8').write("\n".join(L))
print('主表', len(rows), '附表一', len(ink), '附表二', len(wait))
