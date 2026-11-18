#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B 库构建脚本（可重跑）
输入（只读，不重新抓取）：
  - 02-调研与对标/demand-signal/work/fs.json            24 条元素样本（页面正文：时长/评论/章节）
  - 02-调研与对标/benchmark-menu/outputs/01-benchmark-menu.md  40 条对标视频
  - 00-战略与目标/plan-30d/work/base-content-records.json       15 条已排期选题
输出：
  - 02-调研与对标/b-base/bbase.db
规则：
  - 9 个分析列只填有出处的值；没有就 NULL，不猜。
  - 证据类型：实看 / 仅二手描述 / 仅标题可读。
  - 不写入 A 库（04-知识底座）任何内容。
"""
import json
import os
import re
import sqlite3
from datetime import date

ROOT = "/Users/longyi/project/账号对标"
OUT_DIR = os.path.join(ROOT, "02-调研与对标", "b-base")
DB_PATH = os.environ.get("BBASE_DB", os.path.join(OUT_DIR, "bbase.db"))
VIDEO_REVIEW = os.path.join(OUT_DIR, "video-review-24.json")
FS_JSON = os.path.join(ROOT, "02-调研与对标/demand-signal/work/fs.json")
BENCH_MD = os.path.join(ROOT, "02-调研与对标/benchmark-menu/outputs/01-benchmark-menu.md")
PLAN_JSON = os.path.join(ROOT, "00-战略与目标/plan-30d/work/base-content-records.json")

TIME_RE = re.compile(r"^(\d+(?:分钟|小时|天|周|月|年)前|昨天|前天|刚刚)·")
TAGS = {"作者", "作者赞过", "作者回复过", "置顶", "已编辑"}

# ---------------------------------------------------------------- 评论解析
def parse_comments(cmt: str):
    """从页面正文里切出评论区。返回 [(text, like_raw)]。"""
    s = (cmt or "").split("登录后即可参与互动讨论")[0]
    out = []
    for chunk in s.split("分享 | 回复"):
        toks = [t.strip() for t in chunk.split("|")]
        toks = [t for t in toks if t and t != "..."]
        toks = [t for t in toks if not re.match(r"^展开\d+条回复$", t)]
        # 去掉评论区头部标签；"大家都在搜：" 后紧跟搜索词，一并去掉
        while toks:
            if toks[0] in ("全部评论", "请先登录后发表评论"):
                toks.pop(0)
            elif toks[0] == "大家都在搜：":
                toks.pop(0)
                if toks:
                    toks.pop(0)
            else:
                break
        idx = next((i for i, t in enumerate(toks) if TIME_RE.match(t)), None)
        if idx is None:
            continue
        ti = idx - 1
        while ti >= 0 and toks[ti] in TAGS:
            ti -= 1
        text = toks[ti] if ti >= 1 else ""
        like_raw = ""
        if idx + 1 < len(toks) and re.match(r"^\d+(?:\.\d+)?万?$", toks[idx + 1]):
            like_raw = toks[idx + 1]
        out.append((text, like_raw))
    return out


def likes_num(x: str) -> int:
    if not x:
        return 0
    if x.endswith("万"):
        return int(float(x[:-1]) * 10000)
    return int(x)


def top_comment(cmt: str):
    cs = [(t, l) for t, l in parse_comments(cmt) if t.strip()]
    if not cs:
        return None, None
    cs.sort(key=lambda c: likes_num(c[1]), reverse=True)
    t, l = cs[0]
    return t, likes_num(l)


# ---------------------------------------------------------------- 24 条元素样本
FS_ACCOUNT = {
    "7495978368250350863": "于叁岁",
    "7674806616105045282": "华清远见沈阳中心-元仔",
    "7694607181097864474": "宁可为官方旗舰店",
    "7703148892443273834": "王聪",
    "7505282961488317707": "小苹果",
    "7698598885039688969": "牛哥讲装修",
    "7680361304552377651": "小椰子专栏",
    "7624181640370436466": "子真",
    "7635249869787364338": "未获取",
    "7577703220647186354": "艾蜜主题蛋糕(弘盛华庭店)",
    "7703449073718555766": "唯 E",
    "7596154032058617114": "911·暗黑影视",
    "7677130083787091880": "六八八吃瓜瓜",
    "7664943417382300392": "小马",
    "7666396360429636906": "楷模COOMO｜私人整家定制",
    "7431430467582266676": "设计师石空",
    "7699437608338652921": "咪咪圆滚滚",
    "7679765798873887866": "dannar",
    "7696880131406575729": "梅天涯",
    "7682754914384203023": "糖果小奇",
    "7686411393561545594": "赵小五剪辑日记",
    "7693340365575386021": "旺财和nico的两脚兽",
    "7680888707977868401": "要种好多莓",
    "7699034844491255080": "你的商律",
}

FS_CATEGORY = {
    "7495978368250350863": "剧情/搞笑合集",
    "7674806616105045282": "AI 教程",
    "7694607181097864474": "测评/带货",
    "7703148892443273834": "剧情/搞笑",
    "7505282961488317707": "生活记录/翻车",
    "7698598885039688969": "家装科普/避坑",
    "7680361304552377651": "知识科普/口播观点",
    "7624181640370436466": "生活记录/翻车",
    "7635249869787364338": "测评",
    "7577703220647186354": "生活记录/vlog",
    "7703449073718555766": "搞笑/生活",
    "7596154032058617114": "影视解说",
    "7677130083787091880": "动手改造",
    "7664943417382300392": "动手改造",
    "7666396360429636906": "动手改造/设计",
    "7431430467582266676": "设计展示/专业翻译",
    "7699437608338652921": "宠物 vlog",
    "7679765798873887866": "生活记录/骑行",
    "7696880131406575729": "美食",
    "7682754914384203023": "开箱",
    "7686411393561545594": "剪辑教程/知识",
    "7693340365575386021": "生活记录/宠物",
    "7680888707977868401": "生活记录/种植",
    "7699034844491255080": "专业翻译/法律",
}

# 结构标签：只给有文档依据的样本打标，来源见 evidence_note
FS_STRUCTURE = {
    "7694607181097864474": "冲突开场",
    "7505282961488317707": "冲突开场",
    "7698598885039688969": "冲突开场/判断型",
    "7680361304552377651": "冲突开场/判断型",
    "7624181640370436466": "冲突开场",
    "7577703220647186354": "冲突开场",
    "7703449073718555766": "冲突开场",
    "7679765798873887866": "冲突开场",
    "7677130083787091880": "结果前置",
    "7664943417382300392": "结果前置",
    "7666396360429636906": "结果前置",
    "7431430467582266676": "结果前置/判断型",
    "7686411393561545594": "结果前置/判断型",
    "7699034844491255080": "结果前置/判断型",
}

# 需求信号：依据可读评论里出现的最高一级信号；广告/刷单污染或无评论 → NULL
FS_DEMAND = {
    "7703148892443273834": "纯情绪",
    "7505282961488317707": "求教程/求方法",
    "7680361304552377651": "纯情绪",
    "7624181640370436466": "纯情绪",
    "7703449073718555766": "纯情绪",
    "7677130083787091880": "技术讨论/同行提问",
    "7666396360429636906": "纯情绪",
    "7431430467582266676": "纯情绪",
    "7699437608338652921": "纯情绪",
    "7679765798873887866": "纯情绪",
    "7696880131406575729": "技术讨论/同行提问",
    "7682754914384203023": "纯情绪",
    "7686411393561545594": "技术讨论/同行提问",
    "7693340365575386021": "纯情绪",
    "7680888707977868401": "求教程/求方法",
    "7699034844491255080": "技术讨论/同行提问",
}

FS_DEMAND_NOTE = {
    "7698598885039688969": "评论区全部为净水器广告，无真实需求信号，留 NULL",
    "7577703220647186354": "评论区为刷单式好评与作者回复，非真实用户反馈，留 NULL",
    "7680888707977868401": "“想要链接，明年种”是求购买入口，按求方法记，非求教程",
    "7699034844491255080": "评论在讨论嫁妆方案本身，按技术讨论记，非同行提问",
    "7677130083787091880": "最高赞是观众给改造建议，按技术讨论记",
}

# 结果/结论出现秒数：只填章节要点或元素取样文档明确写了的
FS_RESULT = {
    "7699034844491255080": (1, "平台章节要点：00:01 陪嫁房子（结论先行）"),
    "7686411393561545594": (36, "平台章节要点：00:36 新手剪辑成片（结果前置）"),
    "7664943417382300392": (0, "元素取样文档：0 秒即成品（未逐帧，二手）"),
    "7666396360429636906": (0, "元素取样文档：0 秒即落地实拍（未逐帧，二手）"),
    "7677130083787091880": (5, "元素取样文档：0–5 秒给改造后房车，约 5 秒切施工（未逐帧，二手）"),
    "7431430467582266676": (0, "元素取样/对标文档：00:00 先给对比结论（二手，未逐帧）"),
}

FS_TURN = {
    "7680361304552377651": (28, "平台章节要点：00:28 佛山胡闹厨房事故（事件/冲突进入点）"),
}


def load_fs_samples():
    data = json.load(open(FS_JSON, encoding="utf-8"))
    out = []
    for x in data:
        vid = x["id"]
        cmt = x.get("cmt") or ""
        chap = x.get("chap") or ""
        dur = x.get("dur")
        tc, tl = top_comment(cmt)
        # 证据类型：有平台章节摘要或文档写明的时间点 → 仅二手描述；否则只有标题/时长/评论反应 → 仅标题可读
        has_secondhand = bool(chap.strip()) or vid in FS_RESULT or vid in FS_TURN
        if has_secondhand:
            etype = "仅二手描述"
            note = "平台章节摘要/元素取样文档可读；画面、台词、字幕未采集"
        elif x.get("dur") is None and not cmt.strip():
            etype = "仅标题可读"
            note = "页面无时长、无评论、无章节，只有标题"
        elif cmt.strip():
            etype = "仅标题可读"
            note = "只有标题、时长与评论反应；无章节、画面、台词"
        else:
            etype = "仅标题可读"
            note = "只有标题与时长；无评论、章节、画面、台词"
        result_sec, result_note = FS_RESULT.get(vid, (None, None))
        turn_sec, turn_note = FS_TURN.get(vid, (None, None))
        extra = []
        if result_note:
            extra.append(result_note)
        if turn_note:
            extra.append(turn_note)
        if vid in FS_DEMAND_NOTE:
            extra.append(FS_DEMAND_NOTE[vid])
        if vid in FS_STRUCTURE:
            extra.append(f"结构标签来源：元素取样/对标文档判断（{FS_STRUCTURE[vid]}）")
        if extra:
            note = note + "；" + "；".join(extra)
        raw_title = x.get("title", "")
        if raw_title.startswith("在抖音记录美好生活"):
            raw_title = x.get("bingTitle") or raw_title
            note += "；视频页标题为通用占位，标题取自搜索结果页"
        out.append(dict(
            source_ref=vid,
            account=FS_ACCOUNT.get(vid, "未获取"),
            url=f"https://www.douyin.com/video/{vid}",
            collected_on="2026-11-13",
            evidence_type=etype,
            evidence_note=note,
            duration_sec=round(float(dur), 1) if dur is not None else None,
            first3_visual=None,
            first_line=None,
            turn_sec=turn_sec,
            result_sec=result_sec,
            ending_action=None,
            subtitle_style=None,
            top_comment=tc,
            top_comment_likes=tl,
            demand_level=FS_DEMAND.get(vid),
            category=FS_CATEGORY.get(vid, "未获取"),
            structure_tag=FS_STRUCTURE.get(vid),
            migration_note=None,
            raw_title=raw_title,
            source_file="02-调研与对标/demand-signal/work/fs.json",
        ))
    return out


# ---------------------------------------------------------------- 40 条对标视频
def load_bench_samples():
    md = open(BENCH_MD, encoding="utf-8").read()
    out = []
    for line in md.splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 7:  # 只要 40 条视频表（20 账号表是 8 列）
            continue
        num = int(cells[0])
        typ = cells[1]
        lm = re.search(r"\[([^\]]+)\]\(([^)]+)\)", cells[2])
        title, url = (lm.group(1), lm.group(2)) if lm else (cells[2], "")
        open3, dur_txt, hot, migration = cells[3], cells[4], cells[5], cells[6]
        vid = None
        m = re.search(r"/video/(\d+)", url)
        if m:
            vid = m.group(1)
        source_ref = vid if vid else f"bench-#{num}"
        dur = None
        dm = re.match(r"^(\d{1,2}):(\d{2})$", dur_txt)
        if dm:
            dur = int(dm.group(1)) * 60 + int(dm.group(2))
        chapter_based = open3.startswith("【章节要点】")
        etype = "仅二手描述" if chapter_based else "仅标题可读"
        note = f"对标菜单第 {num} 行；开头 3 秒备注原文：{open3}（不是逐帧画面）；爆点判断：{hot}"
        if not vid:
            note += "；链接是账号主页，不是具体视频页"
        if dur is None:
            note += "；时长未获取"
        out.append(dict(
            source_ref=source_ref,
            account="未获取",
            url=url,
            collected_on="2026-11-14",
            evidence_type=etype,
            evidence_note=note,
            duration_sec=dur,
            first3_visual=None,
            first_line=None,
            turn_sec=None,
            result_sec=None,
            ending_action=None,
            subtitle_style=None,
            top_comment=None,
            top_comment_likes=None,
            demand_level=None,
            category=typ,
            structure_tag=None,
            migration_note=migration,
            raw_title=title,
            source_file="02-调研与对标/benchmark-menu/outputs/01-benchmark-menu.md",
        ))
    return out


# ---------------------------------------------------------------- 合并去重
def merge_samples(fs_rows, bench_rows):
    """以视频 id 去重：元素样本优先，补上对标表的类型与迁移判断。"""
    by_ref = {}
    for r in fs_rows:
        by_ref[r["source_ref"]] = r
    for b in bench_rows:
        key = b["source_ref"]
        if key in by_ref:
            cur = by_ref[key]
            if cur["evidence_type"] == "仅标题可读" and b["evidence_type"] == "仅二手描述":
                cur["evidence_type"] = "仅二手描述"
            if not cur.get("category") or cur["category"] == "未获取":
                cur["category"] = b["category"]
            cur["migration_note"] = b["migration_note"]
            cur["evidence_note"] += f"；另见对标菜单：{b['evidence_note']}"
        else:
            by_ref[key] = b
    return sorted(by_ref.values(), key=lambda r: (r["source_file"], r["source_ref"]))


# ---------------------------------------------------------------- 选题
TARGET = "中小企业老板 / 业务负责人（不缺演示，缺敢交付的人）"

PLAN_PATHS = {
    "01": "agency/state/gui/gui-20261111-173755-1fbd/",
    "02": "功能缺口清单.md",
    "03": "2026-11-13/real-data-体检报告.md",
    "04": "2026-11-13/acceptance/",
    "05": "WorkBuddy/Agent场景/README",
    "06": "recruitment-browser-mcp/README.md",
    "07": ".logs/dev.log、web/",
    "08": "看板/js/data.js、高管看板/",
    "09": "prototype/demo/审查报告.md",
    "10": "UI深度审查报告.md",
    "11": "焦虑期陪伴产品定稿审查报告.md",
    "12": "情绪陪伴产品设计方案_V2.0.md、DEMO/",
    "13": None,
    "14": "2026-11-13/real-data-体检报告.md",
    "15": "agency/state/gui/173415-bebf/",
}

PERSONA = {
    "01": "敢把被自己规则拦下的记录摊开：我定的规矩先管住我自己。",
    "02": "敢承认 24/24 是自评，不把自评当完成。",
    "03": "能把“记了但没记住”讲成一句人话：我分得清记录和理解。",
    "04": "宁可界面难看，也不编一个数字：我不糊弄。",
    "05": "能把技术评分翻成业务语言：同一件事换个说法就从不行变行。",
    "06": "真踩过平台的坑，知道哪里会翻车。",
    "07": "遇到门锁就自己开窗：我有动手能力。",
    "08": "能把复杂漏斗讲成一条线：我有翻译能力。",
    "09": "不迷信产量，我验收质量。",
    "10": "能看出“设计稿全有、点下去没反应”：我有验收能力。",
    "11": "盯闭环，不放过半成品。",
    "12": "能把模糊需求写成规则：我有翻译能力。",
    "13": "会查它为什么没用上手边素材：我有复盘能力。",
    "14": "能分清“记得”和“理解”：我有翻译能力。",
    "15": "知道系统为什么会停手：我有专业判断。",
}

# 结构 → 样本（只挂有文档依据结构标签的 24 条元素样本）
STRUCTURE_SAMPLES = {
    "结果前置": ["7677130083787091880", "7664943417382300392", "7666396360429636906",
                 "7431430467582266676", "7686411393561545594", "7699034844491255080"],
    "冲突开场": ["7694607181097864474", "7505282961488317707", "7698598885039688969",
                 "7680361304552377651", "7624181640370436466", "7577703220647186354",
                 "7703449073718555766", "7679765798873887866"],
    "判断型": ["7698598885039688969", "7680361304552377651", "7431430467582266676",
               "7686411393561545594", "7699034844491255080"],
    "自嘲": [],
    "旁人视角": [],
}


def load_topics():
    recs = json.load(open(PLAN_JSON, encoding="utf-8"))["create_records"]
    out = []
    for r in recs:
        no = r["条号"]
        structs = r.get("结构类型") or []
        linked = []
        for s in structs:
            linked += STRUCTURE_SAMPLES.get(s, [])
        linked = sorted(set(linked))
        status = "立项" if len(linked) >= 2 else "未立项"
        reason = f"结构 {'/'.join(structs)} 命中 {len(linked)} 条样本"
        if status == "未立项":
            reason += "；少于 2 条，按规则标未立项"
        if PLAN_PATHS.get(no) is None:
            reason += "；计划表未标注素材路径"
        out.append(dict(
            topic_name=r["翻译主题（这句大白话是什么）"],
            target_audience=TARGET,
            persona_point=PERSONA[no],
            own_material_path=PLAN_PATHS.get(no),
            status=status,
            note=f"计划第 {no} 条｜{r['素材来源项目']}｜{reason}｜要讲的事：{r['要讲的那件事']}",
            linked=linked,
        ))
    return out


# ---------------------------------------------------------------- 建库
SCHEMA = """
DROP VIEW IF EXISTS v_sample_completeness;
DROP VIEW IF EXISTS v_topic_sample_count;
DROP VIEW IF EXISTS v_unfiled_topics;
DROP VIEW IF EXISTS v_samples_cn;
DROP TABLE IF EXISTS sample_topics;
DROP TABLE IF EXISTS topics;
DROP TABLE IF EXISTS samples;

CREATE TABLE samples (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  source_ref        TEXT UNIQUE NOT NULL,
  account           TEXT,
  url               TEXT,
  collected_on      TEXT NOT NULL,
  evidence_type     TEXT NOT NULL CHECK (evidence_type IN ('实看','抽帧看过','仅标题推断')),
  evidence_note     TEXT,
  duration_sec      REAL,
  first3_visual     TEXT,
  first_line        TEXT,
  first_line_proofread TEXT,          -- 人工校对后的第一句话（与原始识别并存）
  turn_sec          REAL,
  result_sec        REAL,
  ending_action     TEXT,
  subtitle_style    TEXT,
  has_subtitle      INTEGER,          -- 1=前三秒画面有字幕条 0=无 NULL=未判读
  actual_duration_sec REAL,           -- 实际下载文件测得时长（区别于页面口径 duration_sec）
  quality_tier      TEXT,             -- 实际拿到的清晰度档位
  top_comment       TEXT,
  top_comment_likes INTEGER,
  demand_level      TEXT CHECK (demand_level IS NULL OR demand_level IN
                     ('求定制/求代做','求教程/求方法','技术讨论/同行提问','纯情绪')),
  category          TEXT,
  structure_tag     TEXT,
  migration_note    TEXT,
  raw_title         TEXT,
  source_file       TEXT NOT NULL
);

CREATE TABLE topics (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  topic_name        TEXT NOT NULL,
  target_audience   TEXT,
  persona_point     TEXT,
  own_material_path TEXT,
  status            TEXT NOT NULL CHECK (status IN ('立项','未立项')),
  note              TEXT
);

CREATE TABLE sample_topics (
  sample_id INTEGER NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
  topic_id  INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  PRIMARY KEY (sample_id, topic_id)
);

CREATE INDEX idx_samples_duration ON samples(duration_sec);
CREATE INDEX idx_samples_demand   ON samples(demand_level);
CREATE INDEX idx_samples_evidence ON samples(evidence_type);

CREATE VIEW v_sample_completeness AS
SELECT
  s.id,
  s.source_ref,
  s.account,
  (s.duration_sec IS NOT NULL)
  + (s.first3_visual IS NOT NULL)
  + (s.first_line IS NOT NULL)
  + (s.turn_sec IS NOT NULL)
  + (s.result_sec IS NOT NULL)
  + (s.ending_action IS NOT NULL)
  + (s.subtitle_style IS NOT NULL)
  + (s.top_comment IS NOT NULL)
  + (s.demand_level IS NOT NULL) AS filled_cols,
  CASE WHEN ((s.duration_sec IS NOT NULL)
  + (s.first3_visual IS NOT NULL)
  + (s.first_line IS NOT NULL)
  + (s.turn_sec IS NOT NULL)
  + (s.result_sec IS NOT NULL)
  + (s.ending_action IS NOT NULL)
  + (s.subtitle_style IS NOT NULL)
  + (s.top_comment IS NOT NULL)
  + (s.demand_level IS NOT NULL)) >= 6 THEN 1 ELSE 0 END AS usable_6
FROM samples s;

CREATE VIEW v_topic_sample_count AS
SELECT t.id, t.topic_name, t.status,
       COUNT(st.sample_id) AS sample_count
FROM topics t
LEFT JOIN sample_topics st ON st.topic_id = t.id
GROUP BY t.id;

CREATE VIEW v_unfiled_topics AS
SELECT t.id, t.topic_name, t.target_audience, t.persona_point,
       t.own_material_path, t.status, t.note,
       COUNT(st.sample_id) AS sample_count
FROM topics t
LEFT JOIN sample_topics st ON st.topic_id = t.id
GROUP BY t.id
HAVING t.status = '未立项' OR COUNT(st.sample_id) < 2;

CREATE VIEW v_samples_cn AS
SELECT
  id                                                        AS 编号,
  account                                                   AS 账号名,
  raw_title                                                 AS 标题,
  url                                                       AS 链接,
  collected_on                                              AS 采集日期,
  evidence_type                                             AS 证据类型,
  duration_sec                                              AS 时长秒,
  first3_visual                                             AS 前三秒画面,
  first_line                                                AS 第一句话,
  turn_sec                                                  AS 转折秒,
  result_sec                                                AS 结果秒,
  ending_action                                             AS 结尾动作,
  subtitle_style                                            AS 字幕样式,
  top_comment                                               AS 最高赞评论,
  top_comment_likes                                         AS 最高赞数,
  demand_level                                              AS 需求信号,
  category                                                  AS 类型,
  structure_tag                                             AS 结构标签,
  migration_note                                            AS 迁移判断,
  evidence_note                                             AS 证据备注,
  source_file                                               AS 来源文件
FROM samples;
"""


def load_video_review():
    """读取 24 条元素样本的人工判读与机器转写结果（key = source_ref）。

    这批数据来自「把视频真看一遍」的离线流水线，无法从原始抓取文件重新推导，
    因此单独存成 video-review-24.json 作为建库输入，保证重建可再现。
    """
    if not os.path.exists(VIDEO_REVIEW):
        print("WARN: 缺少 video-review-24.json，前四列将为空")
        return {}
    with open(VIDEO_REVIEW, encoding="utf-8") as f:
        return json.load(f)


def derive_has_subtitle(style):
    """由 subtitle_style 判定前三秒是否有字幕条；判不出返回 None。

    规则：前三秒画面上存在成行的字幕/文字条（台词字幕、片名字幕条、花字标题）记为 1；
    纯品牌角标、无任何文字覆盖记为 0。个别案例（如只有品牌角标）在 JSON 里显式给值覆盖。
    """
    if not style:
        return None
    return 0 if style.startswith("前三秒画面无字幕") else 1


def main():
    fs_rows = load_fs_samples()
    bench_rows = load_bench_samples()
    samples = merge_samples(fs_rows, bench_rows)
    topics = load_topics()

    os.makedirs(OUT_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)

    cols = ["source_ref", "account", "url", "collected_on", "evidence_type", "evidence_note",
            "duration_sec", "first3_visual", "first_line", "turn_sec", "result_sec",
            "ending_action", "subtitle_style", "top_comment", "top_comment_likes",
            "demand_level", "category", "structure_tag", "migration_note", "raw_title",
            "source_file"]
    sql = f"INSERT INTO samples ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
    for r in samples:
        # 三档口径：两边的原始 loader 仍产出旧值（仅二手描述/仅标题可读），
        # 入库统一按「没看过画面」记为仅标题推断，后面的 UPDATE 再把抽帧看过的 24 条抬档
        r = dict(r, evidence_type="仅标题推断")
        con.execute(sql, [r.get(c) for c in cols])

    # 证据档位三档重写：24 条抽帧看过 → 抽帧看过，其余没看过画面 → 仅标题推断
    con.execute("UPDATE samples SET evidence_type='仅标题推断'")
    con.execute("UPDATE samples SET evidence_type='抽帧看过' WHERE source_file LIKE '%fs.json'")

    # 回填 24 条元素样本的四列判读结果 + 三项过程数据
    review = load_video_review()
    applied = 0
    for ref, v in review.items():
        hs = v.get("has_subtitle")
        if hs is None:
            hs = derive_has_subtitle(v.get("subtitle_style"))
        cur = con.execute(
            "UPDATE samples SET first3_visual=?, first_line=?, first_line_proofread=?,"
            " subtitle_style=?, ending_action=?, actual_duration_sec=?, quality_tier=?,"
            " has_subtitle=?, evidence_type=? WHERE source_ref=?",
            (v.get("first3_visual"), v.get("first_line"), v.get("first_line_proofread"),
             v.get("subtitle_style"), v.get("ending_action"), v.get("actual_duration_sec"),
             v.get("quality_tier"), hs, v.get("evidence_type") or "抽帧看过", ref))
        applied += cur.rowcount
    print("review applied:", applied, "/", len(review))

    id_by_ref = dict(con.execute("SELECT source_ref, id FROM samples"))
    for t in topics:
        cur = con.execute(
            "INSERT INTO topics (topic_name,target_audience,persona_point,own_material_path,status,note) "
            "VALUES (?,?,?,?,?,?)",
            (t["topic_name"], t["target_audience"], t["persona_point"],
             t["own_material_path"], t["status"], t["note"]))
        tid = cur.lastrowid
        for ref in t["linked"]:
            if ref in id_by_ref:
                con.execute("INSERT OR IGNORE INTO sample_topics (sample_id,topic_id) VALUES (?,?)",
                            (id_by_ref[ref], tid))
    con.commit()

    # 控制台摘要
    total = con.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
    print("DB:", DB_PATH)
    print("samples:", total, "| topics:", con.execute("SELECT COUNT(*) FROM topics").fetchone()[0])
    print("evidence:", con.execute("SELECT evidence_type, COUNT(*) FROM samples GROUP BY 1").fetchall())
    print("filled_cols:", con.execute("SELECT filled_cols, COUNT(*) FROM v_sample_completeness GROUP BY 1").fetchall())
    print("usable_6:", con.execute("SELECT COUNT(*) FROM v_sample_completeness WHERE usable_6=1").fetchone()[0])
    print("unfiled:", con.execute("SELECT topic_name, sample_count FROM v_unfiled_topics").fetchall())
    con.close()


if __name__ == "__main__":
    main()
