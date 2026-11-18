#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精确词组统计抖音合集索引的供给密度（coll_index.json: 10000 条合集标题）"""
import json, re, collections, os, sys

SRC = "/Users/longyi/project/账号对标/02-调研与对标/douyin-benchmark/work/coll_index.json"
raw = open(SRC, encoding="utf-8").read()
data = json.loads(raw)
print("total collections:", len(data))

POOLS = {
    "A_AI应用与工具": {
        "强": ["智能体", "AI编程", "提示词", "AI教程", "AI工具", "大模型", "AI应用", "工作流", "自动化"],
        "弱": ["零基础", "保姆级", "入门", "从0", "教程", "教学"],
    },
    "B_科技硬核与手搓": {
        "强": ["手搓", "自制", "ESP32", "单片机", "嵌入式", "开源硬件", "电路", "机器人", "DIY"],
        "弱": ["硬核", "焊接", "3D打印", "树莓派", "Arduino", "极客", "机械"],
    },
    "C_过程记录与创业": {
        "强": ["创业日记", "还债", "开店", "装修", "摆摊", "挑战", "每天", "第1集", "第一集"],
        "弱": ["记录", "日常", "vlog", "日记", "全过程", "我是怎么"],
    },
}

def hits(titles, kws):
    c = collections.Counter()
    for t in titles:
        for k in kws:
            if k.lower() in t.lower():
                c[k] += 1
    return c

for pool, groups in POOLS.items():
    print("\n===", pool, "===")
    allhit = set()
    for level, kws in groups.items():
        c = hits([d["title"] for d in data], kws)
        print(f"-- {level} --")
        for k, v in c.most_common():
            print(f"  {k}\t{v}")
        for d in data:
            if any(k.lower() in d["title"].lower() for k in kws):
                allhit.add(d["id"])
    print(f"  => 命中合集数(去重): {len(allhit)} / {len(data)} = {len(allhit)/len(data)*100:.2f}%")

# 同质化：标题结构模板
print("\n=== 标题模板同质化（全库） ===")
patterns = {
    "第N集/期/讲": r"第\s*[0-9一二三四五六七八九十百]+\s*[集期讲]",
    "含'教程'": r"教程",
    "含'合集'": r"合集",
    "含'零基础/入门/保姆级'": r"零基础|入门|保姆级",
    "含'挑战/天'": r"挑战|[0-9]+\s*天",
    "含数字编号开头": r"^[0-9]+",
}
for name, pat in patterns.items():
    n = sum(1 for d in data if re.search(pat, d["title"]))
    print(f"{name}\t{n}\t{n/len(data)*100:.2f}%")

# 打印各池命中的样本标题，供人工判断噪声
print("\n=== 各池命中标题样本(前25) ===")
for pool, groups in POOLS.items():
    kws = groups["强"]
    print("\n--", pool, "--")
    n = 0
    for d in data:
        if any(k.lower() in d["title"].lower() for k in kws):
            print("  ", d["title"], "|", d["id"])
            n += 1
            if n >= 25: break
