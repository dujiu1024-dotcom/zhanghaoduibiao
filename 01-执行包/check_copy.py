#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文案/脚本合规扫描，分两级。

硬禁（命中必须改，改到 0 才许发）：
  - 《广告法》第九条明列：国家级／最高级／最佳
  - 承诺效果：保证、包涨粉、一定行、百分百、稳赚、回本、三天上线
  - 医疗金融：治疗、治愈、包治、保本、收益率、秒批、下款
  - 《抖音社区自律公约》明禁行为：隐私（13）、谣言（21）、卖惨与虚假人设（35）、
    知识产权（25）、刷量（32）、无资质医疗金融（33）、骗互动（35）、假冒官方（37）

软禁／提示级（命中只提示，不强改）：
  - 抖音生活服务《虚假宣传—涉及绝对化用语》实施细则。逐条拆出 105 个表述，
    去掉与硬禁重复的 3 条（国家级／最高级／最佳）后实收 102 条。
    该细则只管生活服务创作者；我们不是商家，命中只作提醒，不挂广告法。
  - 第 23 条「不欢迎」：炫富、富豪人设、虚假剧情，属降权提示。
  - 第 34／36 条导流：只拦二维码、微信、手机号、邮箱、网址；
    「私信我」「评论区置顶」「主页简介」是通过口径，不拦；
    只提外平台名、没有具体联系方式的，转人工复核。

用法：
  python3 01-执行包/check_copy.py 01-执行包/02-video1-final.md
  python3 01-执行包/check_copy.py --text "这段话全网第一，包涨粉一万"
  python3 01-执行包/check_copy.py --selftest

退出码：有硬禁命中 = 1；只有软禁或全干净 = 0。
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
RULE = PROJECT / "04-知识底座/knowledge/sources/fulltext/official/douyin-lifexue-jueduihua-yongyu-xize.txt"
REPLACE = PROJECT / "04-知识底座/knowledge/sources/口播替换表.md"
WHITELIST = HERE / "check_copy_whitelist.json"

# 硬禁词：只留广告法第九条明列的三个
HARD_WORDS = ["国家级", "最高级", "最佳"]

# 硬禁：承诺效果 / 医疗金融（正则）
HARD_PATTERNS = [
    r"保证.{0,8}(省|赚|涨|过|回本|效果|收益|成功|通过|上线|做到|学会)",
    r"包(涨粉|涨|过|回本|上线|成功|学会|就业|过审)",
    r"一定(能|可以|行|做得到|有效)",
    r"百分百|100\s*%|百分之百",
    r"稳赚|零风险|无风险|不赔|必赚",
    r"(月|年)(入|赚).{0,4}(万|千|元)",
    r"(三|3|七|7|一|1)\s*天.{0,6}(上线|见效|涨粉|回本)",
    r"翻(一|两|三|四|五|\d+)\s*倍",
    r"治疗|治愈|药到病除|包治|根治",
    r"保本|收益率|投资回报|秒批|下款|放款|贷款包过",
]

# 硬禁：自律公约明禁行为（条款号即依据）
HARD_BEHAVIORS = [
    (r"(?<!\d)1[3-9]\d{9}(?!\d)", "第13条 隐私·手机号"),
    (r"(?<!\d)\d{17}[\dXx](?!\d)", "第13条 隐私·身份证号"),
    (r"(?<!\d)\d{16,19}(?!\d)", "第13条 隐私·银行卡号"),
    (r"(身份证|社保号|护照号|银行卡号).{0,4}(截图|照片|直接发|曝光)", "第13条 隐私"),
    (r"造谣|谣言|编造数据|伪造截图|假新闻|P图造假", "第21条 不实信息"),
    (r"卖惨|装惨|编造身世|虚假人设|假人设|演戏炒作|虚构经历", "第35条 虚假人设/卖惨带货"),
    (r"洗稿|盗图|盗用他人|未授权转载|未经授权转载|抄袭", "第25条 知识产权"),
    (r"刷量|刷赞|刷粉|买赞|买粉|互赞|互评|涨粉神器|批量注册|非正常涨粉", "第32条 作弊与垃圾信息"),
    (r"(医疗|诊疗|药品|医疗器械|金融|贷款|理财|基金|保险|证券).{0,6}(推广|代办|代理|包过|咨询|办理|开户)", "第33条 无资质医疗/金融"),
    (r"扣1|扣一|点赞过百|点赞过千|关注后私信|骗互动", "第35条 骗取互动"),
    (r"(我是|我们是|本号|本账号|获得).{0,6}(抖音官方|官方授权|官方合作|官方认证)", "第37条 假冒/仿冒官方"),
    (r"抖音(官方账号|官方认证|工作人员|内部渠道|官方指定)", "第37条 假冒/仿冒官方"),
]

# 第 34／36 条：私域导流。只拦“落地”动作，不拦站内路径
DIVERSION_BLOCK = [
    (r"(加|添加|联系).{0,3}(微信|威信|薇信|V信|vx|VX|Vx)", "第34/36条 导流·微信"),
    (r"加\s*[Vv](?![A-Za-z0-9])", "第34/36条 导流·加V"),
    (r"二维码|扫码|扫我|扫下方", "第34/36条 导流·二维码"),
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "第34/36条 导流·邮箱"),
    (r"https?://\S+|www\.\S+", "第34/36条 导流·网址"),
]
DIVERSION_WARN = [
    (r"(看|去|到)主页.{0,4}(加|联系|找我)", "第34条 导流·人工复核（主页加我）"),
    (r"(闲鱼|小红书|淘宝|公众号|B站|Bilibili|知乎).{0,6}(搜|找|同名|名字)", "第34条 导流·人工复核（外平台搜我）"),
]
# 通过口径（不拦）：私信 / 评论区置顶 / 主页简介
DIVERSION_PASS = re.compile(r"私信|评论区置顶|主页简介|置顶")

# 第 23 条「不欢迎」：降权提示，不是硬禁
WARN_TIER23 = [
    (r"炫富|富豪人设|身家过亿|开豪车|住豪宅|奢侈生活", "第23条 不欢迎·炫富"),
    (r"流量至上|审丑|博眼球|猎奇噱头", "第23条 不欢迎·不良价值导向"),
]

# 软禁兜底词表（细则文件解析失败时用）
SOFT_FALLBACK = [
    "最优", "最优秀", "最好", "最大", "最低", "最便宜", "最低价", "最流行",
    "最受欢迎", "最时尚", "最符合", "最舒适", "最先", "最先进", "最新科技",
    "最新科学", "最新技术", "最奢侈", "顶级", "顶尖", "尖端", "极致", "极佳",
    "绝佳", "极品", "终极", "首个", "首家", "首选", "首款", "独家", "唯一",
    "独一无二", "仅此一家", "仅此一次", "一流", "天花板", "王者", "巅峰", "至尊",
    "问鼎", "之王", "万能", "绝对", "永久", "史无前例", "前无古人", "世界级",
    "全球级", "宇宙级", "领先", "销量冠军", "全国销量冠军",
]

# 软表词的误伤护栏：命中这些后缀就不算
SOFT_GUARD = {
    "唯一": "性",               # 唯一性测试
    "第一": "条集步次天个版期章节阶段人称届批轮位句手",  # 第一步、第一集、第一条
}


def _clean_term(s):
    """去掉括号注与引号，只留词本身。"""
    s = re.sub(r"（[^）]*）", "", s)
    s = re.sub(r"\([^)]*\)", "", s)
    return s.strip().strip("“”\"' ").strip()


def load_soft():
    """从细则正文解析软表；解析不到就兜底，并打印警告。"""
    if not RULE.exists():
        print(f"[警告] 细则文件不存在：{RULE}；已降级为兜底 {len(SOFT_FALLBACK)} 词。", file=sys.stderr)
        return SOFT_FALLBACK, f"兜底（细则文件不存在，{len(SOFT_FALLBACK)} 词）"
    text = RULE.read_text(encoding="utf-8")
    start = text.find("涉及绝对化用语，包括但不限于")
    end = text.find("违规类型与示例", start)
    block = text[start:end] if start >= 0 and end > start else ""
    terms = []
    # 长引号段落整段取出，再按顿号/逗号/分号拆
    for quoted in re.findall(r"“([^”]+)”", block):
        for part in re.split(r"[、，,；;]", _clean_term(quoted)):
            part = _clean_term(part)
            if 2 <= len(part) <= 20:
                terms.append(part)
    terms = [t for t in dict.fromkeys(terms) if t not in HARD_WORDS]
    if len(terms) < 30:
        print(
            f"[警告] 软禁词表解析失败（只得到 {len(terms)} 条，阈值 30）："
            f"已降级为兜底 {len(SOFT_FALLBACK)} 词，本次软禁扫描结果不完整。",
            file=sys.stderr,
        )
        return SOFT_FALLBACK, f"兜底（细则解析不足 30 词，{len(SOFT_FALLBACK)} 词）"
    return terms, f"细则原文（{len(terms)} 条）"


def _term_regex(term):
    """软表词转正则；带护栏的词后面加否定后缀。"""
    pat = re.escape(term)
    guard = SOFT_GUARD.get(term)
    if guard:
        pat += "(?![" + re.escape(guard) + "])"
    return re.compile(pat)


def _dedupe(hits):
    """同一行里被更长命中包住的短命中去掉（如「行业第一」不再重复报「第一」）。"""
    hits.sort(key=lambda h: (h[0], -(h[2] - h[1])))
    kept, spans = [], []
    for no, s, e, w, why in hits:
        if any(no == n and s >= a and e <= b for n, a, b in spans):
            continue
        spans.append((no, s, e))
        kept.append((no, w, why))
    return kept


def scan(text):
    hard_raw, soft_raw = [], []
    lines = text.splitlines() or [text]
    soft_terms, _ = load_soft()
    soft_res = [(w, _term_regex(w)) for w in soft_terms]
    for no, line in enumerate(lines, 1):
        for w in HARD_WORDS:
            for m in re.finditer(re.escape(w), line):
                hard_raw.append((no, m.start(), m.end(), m.group(0), "广告法第九条"))
        for p in HARD_PATTERNS:
            for m in re.finditer(p, line):
                hard_raw.append((no, m.start(), m.end(), m.group(0), "承诺效果/医疗金融"))
        for p, why in HARD_BEHAVIORS + DIVERSION_BLOCK:
            for m in re.finditer(p, line):
                hard_raw.append((no, m.start(), m.end(), m.group(0), why))
        for w, rx in soft_res:
            if any(h in w for h in HARD_WORDS):
                continue
            for m in rx.finditer(line):
                soft_raw.append((no, m.start(), m.end(), m.group(0), "生活服务细则软表·提示级"))
        for p, why in DIVERSION_WARN + WARN_TIER23:
            for m in re.finditer(p, line):
                soft_raw.append((no, m.start(), m.end(), m.group(0), why))
    # 硬禁只去完全重复项，重叠的不同违规都保留
    hard_out = [(n, w, why) for n, s, e, w, why in dict.fromkeys(hard_raw)]
    return hard_out, _dedupe(soft_raw), len(lines)


def selftest():
    groups = [
        ("A 该硬禁命中",
         "这条三天上线，包涨粉一万，保证一个月回本，百分百有效，国家级水准。加微信 vx123，手机 13800138000。",
         1),
        ("B 该只在提示层",
         "全网最好的方案，唯一选择，第一步先看场景，唯一性测试也做了。",
         0),
        ("C 该放过",
         "最后一步是交付，我一直按这个流程做，唯一性测试通过，第一集讲背景。私信我或看主页简介。",
         0),
    ]
    ok = True
    for name, text, expect in groups:
        hard, soft, n = scan(text)
        print(f"\n[{name}] 期望退出码 {expect}；实测：硬禁 {len(hard)} 处，提示 {len(soft)} 处")
        for no, w, why in hard:
            print(f"  [硬禁] 「{w}」——{why}")
        for no, w, why in soft:
            print(f"  [提示] 「{w}」——{why}")
        actual = 1 if hard else 0
        if actual != expect:
            ok = False
            print(f"  ✗ 不符合预期（硬禁应为 {expect}）")
        else:
            print("  ✓ 符合预期")
    _, src = load_soft()
    print(f"\n软表来源：{src}")
    print("自测" + ("通过" if ok else "失败"))
    return 0 if ok else 1


def load_whitelist():
    """误报白名单：file + phrase + reason。只豁免命中，不改扫描规则。"""
    if not WHITELIST.exists():
        return []
    try:
        data = json.loads(WHITELIST.read_text(encoding="utf-8"))
    except Exception as e:  # 白名单坏了不影响主扫描
        print(f"[警告] 白名单解析失败：{e}；按空白名单处理。", file=sys.stderr)
        return []
    return data.get("entries", [])


def split_whitelisted(hard, lines, name, wl):
    """把硬禁命中拆成（仍要改的, 误报豁免的）。"""
    key = Path(name).name
    kept, waived = [], []
    for hit in hard:
        no = hit[0]
        line = lines[no - 1] if 0 <= no - 1 < len(lines) else ""
        entry = next(
            (e for e in wl if e.get("file") == key and e.get("phrase") and e["phrase"] in line),
            None,
        )
        if entry:
            waived.append((hit, entry))
        else:
            kept.append(hit)
    return kept, waived


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", help="要扫的文件")
    ap.add_argument("--text", help="直接扫一段文字")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    if args.text:
        text, name = args.text, "命令行文字"
    elif args.path:
        p = Path(args.path)
        if not p.exists():
            sys.exit(f"文件不存在：{p}")
        text, name = p.read_text(encoding="utf-8"), str(p)
    else:
        sys.exit("给一个文件路径，或 --text，或 --selftest")

    hard, soft, n = scan(text)
    lines = text.splitlines() or [text]
    hard, waived = split_whitelisted(hard, lines, name, load_whitelist())
    print(f"扫描：{name}（{n} 行）")
    if hard:
        print(f"\n硬禁 {len(hard)} 处（必须改到 0 才许发）：")
        for no, w, why in hard:
            print(f"  第 {no} 行「{w}」——{why}")
    else:
        print("\n硬禁 0 处" + (f"（另有 {len(waived)} 处误报已白名单豁免）" if waived else ""))
    if waived:
        print(f"\n白名单豁免 {len(waived)} 处（误报，不改文字）：")
        for (no, w, why), e in waived:
            print(f"  第 {no} 行「{w}」——{e.get('reason', '')}")
    if soft:
        print(f"\n提示 {len(soft)} 处（提示级，自行判断）：")
        for no, w, why in soft:
            print(f"  第 {no} 行「{w}」——{why}")
    else:
        print("提示 0 处")
    print(f"\n结论：{'不许发，先改硬禁' if hard else '可以发（提示级自行判断）'}")
    sys.exit(1 if hard else 0)


if __name__ == "__main__":
    main()
