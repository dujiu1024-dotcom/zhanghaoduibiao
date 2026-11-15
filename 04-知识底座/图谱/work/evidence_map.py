# -*- coding: utf-8 -*-
"""证据分级：把《L1-无数据支撑清单.md》的四类标记落到节点上。

四个类别的含义（对外引用前先看这个）：
    sourced   有出处（文献 / 官方 / 可核实事实）—— 可以直接引用
    boundary  有出处但需注意边界 —— 引用时必须带限制条件
    inferred  经验推断（作者判断 / 行业通行做法 / 项目规则）—— 不能说成「数据表明」
    none      未获取（数据不存在或拿不到）—— 不引用
    rumor     传闻（广泛流传、找不到出处）—— 不作为依据，图上一律点线标出

默认值按节点类型给：理论=sourced，动作=inferred（执行规则，不是数据结论），
指标=sourced（指标本身可测，值是否拿到见 none）。下面 OVERRIDES 逐条对齐清单。
"""

EVIDENCE = {
    "sourced": "有出处",
    "boundary": "需注意边界",
    "inferred": "经验推断",
    "none": "未获取",
    "rumor": "传闻",
}

DEFAULT = {
    "theory": "sourced",
    "action": "inferred",
    "metric": "sourced",
    "layer": "inferred",
    "expected": "none",
}

# id -> (类别, 说明)
OVERRIDES = {
    # ---- 未获取 ----
    "m-plays": ("none", "抖音后台数据，公开页不展示；当前无实测值。"),
    "m-completion": ("none", "同上：完播率在创作者后台，公开页拿不到。"),
    "m-3s-retention": ("none", "3 秒留存只在后台；对标样本也读不到。"),
    "m-5s-completion": ("none", "公开页不展示，当前只能人工推断。"),
    "m-2s-bounce": ("none", "后台指标，当前无实测值。"),
    "m-avg-watch": ("none", "后台指标，当前无实测值。"),
    "m-brand-search": ("none", "站内搜索未登录强制登录，无法采集。"),
    "m-funnel-rates": ("none", "行业平均转化率各家口径不一，未获取。"),
    "theory-platform-structure": ("none", "机制判断是经验帖；各平台用户比例与投放成本全部未获取。"),
    "theory-dou-plus": ("none", "功能与计费有官方文档；起投金额、涨粉成本、千川日预算未获取。"),
    "theory-republish": ("none", "判重阈值平台不公开，只能靠可观测信号判断。"),
    "a-avatar-set": ("none", "40 个账号抽样中头像分布未获取（未登录不渲染）。"),
    "a-pin-case": ("none", "置顶分布未获取；三条结构是经验推断。"),
    "theory-stp": ("inferred", "STP 框架是教材通说；三类人群客单价是经验推断，支付分布未获取。"),
    "m-gross-margin": ("inferred", "50–60% 为行业惯例推算，单客户真实毛利未获取。"),
    "model-compliance": ("sourced", "禁止行为有官方条文；限流阈值与敏感词库未获取。"),

    # ---- 经验推断 ----
    "m-utilization": ("inferred", "按周交付 1–2 单、客单 1–3 万推算，无实测工时。"),
    "a-no-ads-first15": ("inferred", "逻辑推导：没有转化回传时 oCPM 学不到人群。"),
    "a-weekly-rhythm": ("inferred", "平衡信任与探索，无对照实验。"),
    "theory-homepage-packaging": ("inferred", "全部标准无样本验证，40 个账号三项均未读到。"),
    "a-speech-pace": ("inferred", "行业通行做法，无完播对照。"),
    "a-cut-rhythm": ("inferred", "行业通行做法，无完播对照。"),
    "a-publish-sop": ("inferred", "标题/封面/话题规则为经验归纳；封面在账号中的分布未获取。"),
    "a-dm-first-scene": ("inferred", "私信首响 2 小时、报价 24 小时为服务惯例。"),
    "a-takeorder-sop": ("inferred", "首响与报价时限为服务惯例，无成交数据。"),
    "a-xhs-graphic": ("inferred", "20 分钟/条为自估。"),
    "a-same-topic-first5": ("inferred", "前 5 条不删是逻辑推导，无对照实验。"),
    "theory-north-star": ("inferred", "北极星框架来自经验帖；本账号选有效私信为判断。"),
    "model-six-layers": ("inferred", "本项目总纲，无外部验证；串联假设本身待数据检验。"),
    "model-review-8col": ("inferred", "本项目方法，未做方法学对照。"),
    "model-sampling-bounds": ("inferred", "本项目复盘方法。"),
    "model-public-boundary": ("inferred", "团队定的规则，置信度高但无实验。"),
    "model-monetization-forms": ("inferred", "形态来自经验归纳；营收上限为推算。"),
    "model-direction-switch": ("inferred", "四个判据的阈值全部待校准。"),
    "model-anomaly-types": ("inferred", "本项目选题框架，案例不足。"),
    "theory-funnel-six": ("inferred", "本项目归纳，段间损耗未量化。"),
    "theory-ip-lifecycle": ("inferred", "阶段划分为经验归纳，边界值未验证。"),
    "theory-assetization": ("inferred", "本项目方法。"),
    "theory-crisis-pr": ("inferred", "经验流程，无案例验证。"),
    "theory-competitive-map": ("inferred", "本项目归纳，象限边界为判断。"),
    "theory-three-choices": ("inferred", "本项目决策框架。"),
    "theory-pricing-methods": ("inferred", "行业通说，本账号未实测。"),
    "theory-negotiation": ("inferred", "砍价路径来自经验观察，样本有限。"),
    "theory-productization": ("inferred", "经验推断，尚未形成标准包。"),
    "theory-risk-hedge": ("inferred", "经验归纳。"),
    "theory-cross-platform-rewrite": ("inferred", "经验推断。"),
    "theory-completion-baseline": ("inferred", "平台未公布完播口径，只确认「完整播放比例」。"),
    "theory-private-domain": ("inferred", "行业概念。"),
    "theory-rec-flow": ("inferred", "行业共识。"),
    "theory-search-flow": ("inferred", "打法为经验帖。"),
    "theory-free-traffic-three": ("inferred", "行业通行框架。"),
    "theory-slogan": ("inferred", "结构要素为行业归纳。"),
    "theory-interest-recommend": ("sourced", "官方表述；权重与阈值未公布。"),
    "theory-cold-start": ("sourced", "官方无养号概念；初始标签依赖为经验帖。"),

    # ---- 需注意边界 ----
    "theory-high-arousal": ("boundary", "只解释转发，不解释成交。"),
    "theory-mere-exposure": ("boundary", "最优次数无统一值；实验室刺激≠短视频。"),
    "theory-loss-frame": ("boundary", "2–2.5 倍系数近年重复验证认为被高估，不作常数。"),
    "theory-asch": ("boundary", "跨文化重复存在，效应量随情境差异大。"),
    "theory-bystander": ("boundary", "Fischer 2011 元分析显示弱于原研究。"),
    "theory-peak-end": ("boundary", "基于疼痛实验，外推到短视频是类比。"),
    "theory-foot-in-door": ("boundary", "效应稳健但量中等。"),
    "theory-positioning": ("boundary", "理论，无量化验证。"),
    "theory-usp": ("boundary", "理论，无量化验证。"),
    "theory-carnegie": ("boundary", "经验总结，无对照实验，按经验帖处理。"),
    "theory-social-proof": ("boundary", "Asch 效应量随情境差异大；造假反噬更强。"),

    # ---- 传闻 ----
    "theory-rumor-coldstart": ("rumor", "养号/扶持期/一天多发/删作品/微信限流五条均无出处。"),
    "theory-traffic-pool": ("rumor", "500/1000/1 万分层无出处，只当框架。"),
    "theory-rumor-8s": ("rumor", "注意力 8 秒无可靠出处。"),
    "theory-rumor-saima": ("rumor", "行业说法，非平台机制。"),
    "m-rumor-completion30": ("rumor", "平台从未公布合格线，明确不采用。"),

    # ---- 三个空缺 ----
    "gap-publish-frequency": ("none", "没有最优频次的结论，样本也不足。"),
    "gap-capacity": ("none", "没有工时与外包口径。"),
    "theory-community-na": ("inferred", "主动判定：不适用，不是缺数据。"),
}
