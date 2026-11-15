import csv, json, datetime

W = '04-知识底座/work/books/'
rows = list(csv.DictReader(open(W + 'worklist.csv', encoding='utf-8-sig')))
dl = json.load(open(W + 'delivered.json', encoding='utf-8'))
r2 = json.load(open(W + 'round2_github.json', encoding='utf-8'))
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

FOCUS = ["钩子与注意力", "口播与语言表达", "推荐机制", "冷启动与账号权重", "私域承接与微信运营",
         "转化路径与漏斗设计", "定价与报价", "合同与回款", "广告法与宣传合规",
         "个保法与数据安全", "违规判定与发布前审（并库原文）", "对标拆解"]
ACADEMIC = ("Kahneman", "Thaler", "Sunstein", "Cialdini", "Petty", "Ajzen", "Fishbein",
            "Rogers", "Kotler", "Simon", "Nagle", "Ramanujam", "Baker", "Rackham")


def suggest(r, status):
    if status == '已采集':
        return ''
    author = r.get('作者') or ''
    cn = r.get('中英名') or ''
    if any(a.lower() in author.lower() for a in ACADEMIC):
        return '用替代论文'
    if '/' in cn or '中译' in cn:
        return '图书馆借阅'
    return '购买'


out = []
for r in rows:
    k = r['no']
    name = (r['名称'] or '').strip()
    hit = dl.get(k)
    if hit:
        st, path, prob = '已采集', hit['文件名'], ''
    elif not r2.get(k, {}).get('candidates'):
        st, path, prob = '待采集', '', '需你买或借，已试渠道：公版库、GitHub'
    else:
        st, path, prob = '待采集', '', '有候选但非同书，需人工判断；需你买或借，已试渠道：公版库、GitHub'
    out.append({"编号": r['编号'], "书籍名称": name, "作者": r.get('作者', ''),
                "是否采集到": [st], "路径": path, "遇到问题": prob,
                "采集人": ["操盘手"] if hit else [], "最后更新时间": now})
json.dump(out, open('/tmp/books2.json', 'w'), ensure_ascii=False)

# 排序：12 重点类优先 → 优先级 → 编号
pri = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
wait = [r for r in rows if r['no'] not in dl and not r2.get(r['no'], {}).get('candidates')]
def key(r):
    cls = r['项']
    return (FOCUS.index(cls) if cls in FOCUS else 99, pri.get(r.get('优先级'), 9), r['编号'])
wait.sort(key=key)

L = ["# 待你处理清单（书籍）", "",
     f"共 {len(wait)} 本。排序：12 个重点细类优先 → 优先级 → 编号。", "",
     "这 61 本**只查过公版库（Gutenberg/IA）与 GitHub**，付费购买、图书馆借阅、出版社电子版一次都没查。"
     "标「待你处理」不是判死，是需要你或外部协作者用付费/借阅渠道确认。", ""]
cur = None
for r in wait:
    cls = r['项']
    if cls != cur:
        cur = cls
        head = "★ 重点类" if cls in FOCUS else ""
        L += ["", f"## {cls} {head}".rstrip(), ""]
    L.append(f"- **{r['名称']}** ｜ {r.get('作者') or '作者未记录'} ｜ 细类：{cls} ｜ "
             f"已试：Gutenberg、GitHub 关键词检索 ｜ {r.get('优先级')}")
open('04-知识底座/catalog/待你处理清单.md', 'w', encoding='utf-8').write("\n".join(L) + "\n")

from collections import Counter
print(len(out), Counter(x['是否采集到'][0] for x in out))

print('清单', len(wait))
