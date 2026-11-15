# -*- coding: utf-8 -*-
"""六层主干「应有清单」——用来检查每一层该有的理论/动作/指标是否有着落。

规则：
- 一个槽位 = 一个概念位置，不是一篇文档；covered_by 里只要有一个节点存在就算有着落。
- covered_by 为空的槽位，extract.py 会生成占位节点（status=expected），视觉上与真实节点区分。
- 当前空缺口径以《methodology/00-知识覆盖矩阵.md》为准：3 个（发布频次、产能上限与外包、
  社群运营）。前两个由 curated_nodes.py 里的 gap-* 节点承载，第三个是 status=na，
  因此本清单里三处都指向已有节点，不再额外生成占位。
- 补篇之后要新增检查项，在这里加一条；想让某个槽位重新变成「空缺」，把 covered_by 清空即可。
"""

EXPECTED = [
    # ---------------- 第 1 层 被看见 ----------------
    dict(id="x1-recall", layer="layer-seen", type="theory", label="推荐机制与冷启动",
         why="决定内容有没有机会被推。",
         covered_by=["theory-recall-ranking", "theory-interest-recommend", "theory-cold-start"]),
    dict(id="x1-hook", layer="layer-seen", type="theory", label="钩子与注意力心理",
         why="前 3 秒留人的心理机制。",
         covered_by=["theory-curiosity-gap", "theory-high-arousal", "theory-peak-end",
                     "theory-rumor-8s"]),
    dict(id="x1-publish", layer="layer-seen", type="action", label="发布与完播口径",
         why="发布动作 + 判断标准。",
         covered_by=["a-publish-sop", "a-own-baseline", "theory-completion-baseline"]),
    dict(id="x1-exposure", layer="layer-seen", type="metric", label="曝光与留存指标",
         why="判断这一层成没成。",
         covered_by=["m-plays", "m-2s-bounce", "m-5s-completion", "m-completion",
                     "m-avg-watch", "m-3s-retention"]),
    dict(id="x1-frequency", layer="layer-seen", type="metric", label="发布频次与最优间隔",
         why="一周几条、间隔几天最优；覆盖矩阵记为空缺 1（已有战术排期，无独立篇）。",
         covered_by=["gap-publish-frequency"]),

    # ---------------- 第 2 层 被记住 ----------------
    dict(id="x2-position", layer="layer-remembered", type="theory", label="定位、人群与竞争位",
         why="占哪个空位、对谁说话。",
         covered_by=["theory-positioning", "theory-usp", "theory-stp", "theory-competitive-map"]),
    dict(id="x2-memory", layer="layer-remembered", type="theory", label="记忆、联想与可复制性",
         why="凭什么被想起、被转述。",
         covered_by=["theory-cbbe", "theory-availability", "theory-mere-exposure",
                     "theory-meme", "theory-slogan"]),
    dict(id="x2-identity", layer="layer-remembered", type="action", label="身份与联想落位",
         why="把定位写成简介、口号、固定句式。",
         covered_by=["a-bio-identity", "a-main-slogan", "a-assoc-words", "a-positioning-statement"]),
    dict(id="x2-metric", layer="layer-remembered", type="metric", label="记忆效果指标",
         why="判断别人是否记住了你。",
         covered_by=["m-identity-recall", "m-profile-visits", "m-brand-search"]),

    # ---------------- 第 3 层 被信任 ----------------
    dict(id="x3-trust", layer="layer-trusted", type="theory", label="关系、说服与社会认同",
         why="从内容关系转成人际信任。",
         covered_by=["theory-parasocial", "theory-narrative-transport", "theory-central-route",
                     "theory-social-proof", "theory-asch"]),
    dict(id="x3-persona", layer="layer-trusted", type="theory", label="自我呈现与风险",
         why="演什么、不演什么、出事怎么办。",
         covered_by=["theory-goffman", "theory-crisis-pr", "model-public-boundary",
                     "model-compliance"]),
    dict(id="x3-proof", layer="layer-trusted", type="action", label="可信度动作",
         why="数字、判断句、失败记录、真实评价。",
         covered_by=["a-number-each", "a-refutable-claim", "a-admit-failure", "a-real-review"]),
    dict(id="x3-metric", layer="layer-trusted", type="metric", label="信任信号指标",
         why="评论区问方法/问价的原话。",
         covered_by=["m-demand-signal", "m-comments", "m-favorites"]),

    # ---------------- 第 4 层 被找到 ----------------
    dict(id="x4-search", layer="layer-found", type="theory", label="搜索、承接与主页包装",
         why="需求发生时能不能找到你、找到后看到什么。",
         covered_by=["theory-search-flow", "theory-free-traffic-three", "theory-private-domain",
                     "theory-homepage-packaging", "theory-diversion-boundary"]),
    dict(id="x4-platform", layer="layer-found", type="theory", label="平台结构与跨平台",
         why="同一内容不能平移。",
         covered_by=["theory-platform-structure", "theory-cross-platform-rewrite",
                     "theory-republish", "theory-two-step-flow"]),
    dict(id="x4-entry", layer="layer-found", type="action", label="主页与入口动作",
         why="头像、三行简介、置顶、入口边界。",
         covered_by=["a-avatar-set", "a-bio-three-lines", "a-pin-case", "a-no-contact-public",
                     "a-minimal-private"]),
    dict(id="x4-metric", layer="layer-found", type="metric", label="承接效率指标",
         why="访问→私信→加微。",
         covered_by=["m-profile-to-dm", "m-dm-to-wechat", "m-contact-list", "m-search-dm"]),
    dict(id="x4-community", layer="layer-found", type="theory", label="社群运营",
         why="一次性项目制、客户数 <50，主动判定不适用；标 na 而不是缺失。",
         covered_by=["theory-community-na"]),

    # ---------------- 第 5 层 被成交 ----------------
    dict(id="x5-pricing", layer="layer-closed", type="theory", label="报价、框架与决策心理",
         why="锚定、损失框架、快慢系统、象限判断。",
         covered_by=["theory-anchoring", "theory-loss-frame", "theory-dual-system", "theory-fcb"]),
    dict(id="x5-exchange", layer="layer-closed", type="theory", label="交换、互惠与门槛",
         why="降低互动成本、提高回报确定性。",
         covered_by=["theory-social-exchange", "theory-reciprocal-altruism",
                     "theory-foot-in-door", "theory-bystander"]),
    dict(id="x5-business", layer="layer-closed", type="theory", label="商业、定价与谈判",
         why="接什么、怎么报价、怎么让步。",
         covered_by=["theory-pricing-methods", "theory-productization", "theory-negotiation",
                     "model-monetization-forms", "theory-north-star", "theory-dou-plus"]),
    dict(id="x5-close", layer="layer-closed", type="action", label="成交动作",
         why="报价、范围、接单流程、私信阶梯。",
         covered_by=["a-anchor-quote", "a-quote-onepager", "a-takeorder-sop", "a-scope-io",
                     "a-scope-not-price", "a-refuse-five"]),
    dict(id="x5-metric", layer="layer-closed", type="metric", label="成交链路指标",
         why="私信→报价→成单→客单→占比。",
         covered_by=["m-effective-dm", "m-price-dm", "m-quotes", "m-close-rate",
                     "m-order-value", "m-client-share"]),
    dict(id="x5-capacity", layer="layer-closed", type="metric", label="产能上限与外包",
         why="覆盖矩阵明确标空缺：只有营收上限的经验推断，没有工时与外包口径。",
         covered_by=["gap-capacity"]),

    # ---------------- 第 6 层 被转介绍 ----------------
    dict(id="x6-referral", layer="layer-referred", type="theory", label="复购与推荐机制",
         why="为什么会有人替你说话。",
         covered_by=["theory-nps-referral", "theory-reciprocal-altruism"]),
    dict(id="x6-actions", layer="layer-referred", type="action", label="评价与定期触达",
         why="索要评价、截图置顶、季度问候。",
         covered_by=["a-ask-review", "a-review-to-pin", "a-quarterly-touch"]),
    dict(id="x6-metric", layer="layer-referred", type="metric", label="转介绍效果指标",
         why="公开评价与主动推荐。",
         covered_by=["m-public-reviews", "m-referrals"]),
]
