# -*- coding: utf-8 -*-
"""人工复核过的节点与边：这张图谱的唯一事实来源。

改这里 -> 跑 extract.py -> 重新生成 outputs/graph.json 与 outputs/index.html。
字段说明见 ../README.md 与 extract.py 顶部注释。
"""

# ---------- 文档路径（相对 knowledge/） ----------
D00 = "methodology/00-操盘主干.md"
DAD = "methodology/广告理论-定位到说服.md"
DSPREAD = "methodology/传播理论-情绪到说服路径.md"
DTRAFFIC = "methodology/流量理论-推荐到搜索.md"
DGROWTH = "methodology/增长理论-AARRR到复购.md"
DMAP = "methodology/理论到操盘动作映射表.md"
DPSY1 = "methodology/心理-01-准社会关系.md"
DPSY2 = "methodology/心理-02-好奇心缺口.md"
DPSY3 = "methodology/心理-03-叙事传输.md"
DPSY4 = "methodology/心理-04-行为经济学.md"
DHUM1 = "methodology/人性-01-人性的弱点.md"
DHUM2 = "methodology/人性-02-注意力商品化.md"
DHUM3 = "methodology/人性-03-互惠利他.md"
DHUM4 = "methodology/人性-04-地位理论.md"
DHUM5 = "methodology/人性-05-社会交换理论.md"
DREC = "methodology/01-推荐机制与流量池.md"
DCOLD = "methodology/02-新号冷启动与养号.md"
DRED = "methodology/03-违规红线.md"
DCRAFT = "methodology/制作-01-口播与剪辑手艺.md"
DREVIEW = "methodology/制作-02-单条视频复盘方法.md"
DPUB = "methodology/公开内容边界.md"
DSAMPLE = "methodology/抽样与归因的边界.md"
DBIZ = "methodology/经营-01-五种变现形态.md"
DTOPIC = "topics/选题库.md"
DDIR = "topics/方向备选与切换判据.md"
DMR = "monetization/README.md"

THEORY, ACTION, METRIC, LAYER = "theory", "action", "metric", "layer"
SUPPORTED, MENTIONED, MISSING, UNVERIFIED = "supported", "mentioned", "missing", "unverified"

# ---------- 六层 ----------
LAYERS = [
    dict(
        id="layer-seen", order=1, name="被看见",
        problem="让系统把你推给对的人，且他们没在前 3 秒划走。",
        success="5 秒完播率 ≥50%，完播率与同长度同类可比；评论区出现具体追问而不只是「没看懂」。",
        death="开头自我介绍；标题写品类词；一条开三个缺口；日更但题材乱跳。",
        if_broken="后面五层全部归零——没人看见，记忆、信任、成交都没有输入。",
        doc=D00, section="第一层：被看见",
    ),
    dict(
        id="layer-remembered", order=2, name="被记住",
        problem="看完之后，观众能用一个词或一句话说出你是谁。",
        success="评论区有人用你的句式接话，或直接叫出定位词；主页访问率持续上升。",
        death="每期换题材；今天讲技术、明天讲创业；口号一周一改。",
        if_broken="播放再高也换不来私信，第三层的信任没有对象可依附。",
        doc=D00, section="第二层：被记住",
    ),
    dict(
        id="layer-trusted", order=3, name="被信任",
        problem="让观众相信这个人说的话有依据，且他真做过。",
        success="评论区出现 L2（求方法）或 L1（求定制/问价）原话；私信里出现「我看了你那条 XX」。",
        death="只讲信息不给判断；全是成功案例；出现一次效果承诺。",
        if_broken="第四层即使发生，找到的只是一个报价页——没有信任的询价会直接进入比价。",
        doc=D00, section="第三层：被信任",
    ),
    dict(
        id="layer-found", order=4, name="被找到",
        problem="有人真想解决这个问题时，能在哪找到你，且找到的是「人」不是「号」。",
        success="私信第一句出现「我搜 XX 找到你的」；主页访问→私信转化率可手工计算。",
        death="简介写满形容词没有事实；置顶是自我介绍；所有标题只写反常。",
        if_broken="需求发生时找不到入口，第三层积累的信任无法兑现。",
        doc=D00, section="第四层：被找到",
    ),
    dict(
        id="layer-closed", order=5, name="被成交",
        problem="把「有兴趣」变成「有报价、有订单」。",
        success="有效私信数（出现多少钱/能不能做）≥3 条；报价数、成单数、客单价可手工记。",
        death="一上来甩报价；同时要四个动作；承诺效果；客户名单留在平台里。",
        if_broken="第六层没有交付事实可引用，整个链路退化成流量生意。",
        doc=D00, section="第五层：被成交",
    ),
    dict(
        id="layer-referred", order=6, name="被转介绍",
        problem="让交付过的客户愿意公开说一句，并带来下一个客户。",
        success="老客户主动推荐数 ≥1；公开评价 ≥3 条。",
        death="交付完即失联；只敢要好话；把转介绍做成返佣。",
        if_broken="每一单都要重新买流量，账号永远停在获客阶段，没有复利。",
        doc=D00, section="第六层：被转介绍",
    ),
]

NODES = []


def T(id, label, layer, definition, citation="", doc=D00, section="", status=SUPPORTED, note=""):
    NODES.append(dict(id=id, label=label, type=THEORY, layer=layer, status=status,
                      definition=definition, citation=citation, doc=doc, section=section, note=note))


def A(id, label, layer, definition, doc=D00, section="", status=SUPPORTED, note=""):
    NODES.append(dict(id=id, label=label, type=ACTION, layer=layer, status=status,
                      definition=definition, citation="", doc=doc, section=section, note=note))


def M(id, label, layer, definition, doc=D00, section="", status=SUPPORTED, note=""):
    NODES.append(dict(id=id, label=label, type=METRIC, layer=layer, status=status,
                      definition=definition, citation="", doc=doc, section=section, note=note))


# ============================ 理论 / 模型 ============================
# ---- 第 1 层：被看见 ----
T("theory-recall-ranking", "召回-排序-重排", "layer-seen",
  "平台先从百万级候选里召回几百条（粗筛看相似度），再排序（预估点击/时长/转化），最后重排（多样性、去重）。内容没被推，多数是召回阶段就没进候选，不是排序输了。",
  "Covington et al., RecSys 2016；周国睿等, KDD 2018", DTRAFFIC, "1. 推荐系统的基本逻辑")
T("theory-explore-exploit", "探索-利用", "layer-seen",
  "系统必须拿一部分流量试新内容/新题材，否则只会推已知会爆的。探索流量很小，只够评估内容，不够起量。",
  "Sutton & Barto, 1998", DTRAFFIC, "2. 探索与利用")
T("theory-traffic-pool", "流量池分层", "layer-seen",
  "行业说法：作品先进小池，指标达标再进更大池。具体层级与阈值找不到任何官方或学术来源，按【传闻】处理。当解释框架可以，当规则执行不行。",
  "无出处（行业通行说法）", DTRAFFIC, "3. 流量池分层与冷启动",
  status=UNVERIFIED, note="出处待确认：文档明确标注【传闻】，500/1000/1 万这类层级数字无来源。")
T("theory-interest-recommend", "去中心化兴趣推荐", "layer-seen",
  "抖音采用兴趣推荐而非粉丝全量触达；账号标签影响分发人群，但官方从未公布权重、阈值与判定公式。",
  "抖音创作者服务中心【官方】", DREC, "一、能确认的")
T("theory-cold-start", "新号冷启动与内容标签", "layer-seen",
  "官方没有「养号」概念，新号作品同样进推荐候选；初始人群依赖内容标签，连续同题材能更快找到对的人（【经验帖】）。前几条播放低是常态，不是处罚（【实测】）。",
  "抖音官方文档【官方】+ 项目实测", DCOLD, "一、能确认的")
T("theory-curiosity-gap", "好奇心缺口", "layer-seen",
  "好奇不是「想知道更多」，而是意识到自己有一个具体的缺口。缺口越具体、越接近可填补，好奇越强；模糊的「秘密」不产生好奇，开了不填会掉信任。",
  "Loewenstein, Psychological Bulletin, 1994", DPSY2, "全文")
T("theory-high-arousal", "高唤醒情绪", "layer-seen",
  "驱动转发的是唤醒度而不是正负情绪：愤怒、敬畏、焦虑促进转发，悲伤、满足抑制。本项目样本中 AI 剧情号高唤醒但 L1/L2 为 0【实测】，故只取「敬畏/意外」。",
  "Berger & Milkman, JMR, 2012", DSPREAD, "1. 情绪传播")
T("theory-rec-flow", "推荐流量", "layer-seen",
  "推荐流量靠前 3 秒抓注意力，适合泛人群；标题写反常。与搜索流量是两套标题、两套打法。",
  "行业共识【经验帖】", DTRAFFIC, "5. 搜索流量 vs 推荐流量")
T("theory-search-flow", "搜索流量", "layer-found",
  "搜索流量靠标题命中关键词 + 内容给答案，适合已有明确问题的人（「AI 智能体怎么落地」「企业怎么用 agent」）。搜索量太小的词不值得做。",
  "抖音搜索产品表述【官方】+ 打法【经验帖】", DTRAFFIC, "5. 搜索流量 vs 推荐流量")
T("theory-free-traffic-three", "免费流量三来源", "layer-found",
  "推荐靠算法、搜索靠需求、社交靠转发。抖音的社交分发权重很低，微信/群才是社交流量主场。",
  "行业通行框架【经验帖】", DTRAFFIC, "6. 免费流量的三种来源")

# ---- 第 2 层：被记住 ----
T("theory-positioning", "定位理论", "layer-remembered",
  "竞争发生在用户心智里，要占一个空位而不是比别人更好；做不到第一就重新定位对手。品类未成形时无位可占；定位越强、体验落差越伤。",
  "Al Ries & Jack Trout, 1981", DAD, "1. 定位理论")
T("theory-usp", "USP 独特销售主张", "layer-remembered",
  "每条广告给一个竞争对手没有或没说过的具体主张，且能拉动销售。主张无法被验证时会反噬。",
  "Rosser Reeves, 1961", DAD, "2. USP")
T("theory-cbbe", "品牌联想网络（CBBE）", "layer-remembered",
  "品牌是记忆里的一个节点，连着属性、利益、态度三类联想。同一维度被反复强化才形成强联想；联想分散时任何单个联想都弱到无法被记住。",
  "Kevin Lane Keller, Journal of Marketing, 1993", DAD, "6. 品牌联想网络")
T("theory-availability", "可得性启发", "layer-remembered",
  "人判断「哪个更常见/更好」靠能不能想起来，不靠真实概率。用户没有比较标准时最有效；有采购清单时让位于资质与报价。",
  "Tversky & Kahneman, Cognitive Psychology, 1973", DAD, "7. 可得性启发")
T("theory-slogan", "口号结构", "layer-remembered",
  "好口号 = 短（≤12 字）+ 能复读 + 有节奏 + 指向一个具体利益。没有重复曝光预算时，抽象口号等于没有口号。",
  "USP 见 Reeves 1961；结构要素为行业归纳【经验帖】", DAD, "8. 口号与记忆点")
T("theory-mere-exposure", "重复曝光（曝光效应）", "layer-remembered",
  "重复接触提升好感，但呈倒 U；峰值次数研究间差异极大、无统一数字，实验室「无意义刺激」与短视频不可直接类比。做法是形式重复、内容不重复。",
  "Zajonc, JPSP, 1968；Bornstein, Psychological Bulletin, 1989", DAD, "10. 曝光效应")
T("theory-meme", "模因", "layer-remembered",
  "能被复制的内容 = 低复制成本 + 高变异空间 + 可识别立场。纯知识内容缺立场，只能被收藏、不能被模仿。",
  "Dawkins, 1976；Shifman, 2014", DSPREAD, "2. 模因与模仿")

# ---- 第 3 层：被信任 ----
T("theory-parasocial", "准社会关系", "layer-trusted",
  "观众对屏幕里的人产生单向的、拟人际的关系感，靠三件事建立：持续出现、对镜头说话、暴露私人细节。只讲信息不暴露自己，观众记住的是信息不是你。",
  "Horton & Wohl, Psychiatry, 1956", DPSY1, "全文")
T("theory-narrative-transport", "叙事传输", "layer-trusted",
  "人被故事「传送」进去时反驳机制降低，态度改变更持久；察觉「在演」则传输中断、防御更强。顺序是故事在前、道理在后。",
  "Green & Brock, JPSP, 2000", DPSY3, "全文")
T("theory-central-route", "中心路径（ELM）", "layer-trusted",
  "高卷入 + 有能力加工时看论据。B 端采购属高卷入决策，没有论据与信任，报价只会被比价。",
  "Petty & Cacioppo, 1986", DSPREAD, "4. 说服的中心路径与边缘路径")
T("theory-peripheral-route", "边缘路径（ELM）", "layer-seen",
  "低卷入或没能力加工时看信源、气氛、数量。前 3 秒靠真人 + 现场 + 一句话身份建立可信；把边缘技巧用在高卷入决策上会被识破。",
  "Petty & Cacioppo, 1986", DSPREAD, "4. 说服的中心路径与边缘路径")
T("theory-social-proof", "社会认同", "layer-trusted",
  "人用他人行为判断正确行为，不确定性越高越依赖。造假（刷评）被识破后反噬更强。",
  "Cialdini, Influence, 1984", DAD, "5. 广告起作用的三种方式")
T("theory-prestige-status", "声望型地位", "layer-trusted",
  "获得地位有两条路：支配型（压制、资源控制，跟随是被迫）与声望型（展示能力与慷慨，跟随是自愿）。声望型扩散更快更持久，但缺强制力。",
  "Henrich & Gil-White, 2001", DHUM4, "全文")
T("theory-carnegie", "人性的弱点（三条）", "layer-trusted",
  "经验总结与案例汇编，无对照实验、无数据，按【经验帖】处理，不要当理论引用。可用三条：谈对方的利益、记住名字、让对方保住面子。",
  "Dale Carnegie, 1936【经验帖】", DHUM1, "全文",
  note="非科学：文档明确要求不当理论引用，用过头会变成套路感。")

# ---- 第 4 层：被找到 ----
T("theory-attention-commodity", "注意力商品化", "layer-found",
  "平台不生产内容，平台生产并出售受众注意力；创作者是可替换的内容供应商，客户名单留在平台手里。这是结构性判断，不告诉你下一条怎么拍。",
  "Smythe, 1977（并及马克思, 1867）", DHUM2, "全文")
T("theory-two-step-flow", "两级传播", "layer-found",
  "信息先到意见领袖再传给普通人。决策受人际影响大、信息不对称强的领域（B 端采购）仍成立；推荐算法已部分替代人际中转，解释力下降。",
  "Lazarsfeld et al., 1944；Katz & Lazarsfeld, 1955", DSPREAD, "3. 两级传播")
T("theory-private-domain", "私域与公域承接", "layer-found",
  "公域负责获客、私域负责复购与转介绍，承接结构决定 LTV。一次性项目制复购天然低，且平台对站外导流有限制。",
  "行业概念【经验帖】", DGROWTH, "3. 私域与公域的承接结构")

# ---- 第 5 层：被成交 ----
T("theory-anchoring", "锚定效应", "layer-closed",
  "先出现的数字会影响后续判断，即使无关。报价先给锚点，不要从低往高报。",
  "Tversky & Kahneman, Science, 1974", DPSY4, "核心主张·锚定")
T("theory-loss-frame", "损失厌恶与框架效应", "layer-closed",
  "同等金额的损失比收益更痛；常引用的 2–2.5 倍系数被大样本重复验证认为效应存在但被高估，不当精确常数。同一事实换说法，选择会变。",
  "Kahneman & Tversky, Econometrica, 1979；Kahneman, 2011", DPSY4, "核心主张·损失厌恶/框架")
T("theory-dual-system", "双系统", "layer-closed",
  "快系统（直觉、自动、省力）与慢系统（分析、费力）。短视频只能激活快系统，开头不给数字堆叠，给画面和一句话事实。",
  "Kahneman, Thinking Fast and Slow, 2011", DPSY4, "核心主张·双系统")
T("theory-fcb", "FCB 网格", "layer-closed",
  "按「卷入度 × 理性/情感」分四象限。B 端接单属高卷入理性，信息:情绪 ≈ 7:3。判错象限会做出热闹但没人问价的内容。",
  "Richard Vaughn, JAR, 1980", DAD, "9. 情感诉求与理性诉求")
T("theory-social-exchange", "社会交换理论", "layer-closed",
  "互动被当作交换来评估：成本（时间、注意力、暴露自己）对回报（信息、身份感、情绪、利益）。回报不确定时，人选成本更低的动作（划走、看完不评）。",
  "Homans, 1958；Blau, 1964", DHUM5, "全文")
T("theory-reciprocal-altruism", "互惠利他", "layer-closed",
  "人愿意帮将来可能回报自己的对象，前提是能识别、能记住、回报可延迟。给得太完整对方拿完就走；给了就催回报会被识别为交易。",
  "Trivers, 1971；Dawkins, 1976", DHUM3, "全文",
  note="同时支撑第 6 层：先给后取在长期客户关系里成立。")
T("theory-performance-ad", "效果广告 CPA/oCPM", "layer-closed",
  "投放按「预估转化率 × 出价」排序分配曝光。没有转化回传时 oCPM 学不到人群，退化成买曝光；当前阶段不该投。",
  "巨量引擎文档【官方】；Skok, 2010", DAD, "4. 效果广告的核心指标与投放逻辑")
T("theory-interest-ecommerce", "兴趣电商", "layer-closed",
  "用户没有明确需求、被内容激发后下单，适合低客单冲动型。高客单 B 端不适用——成交发生在私信/线下，不在小黄车。",
  "抖音电商, 2021【官方】", DTRAFFIC, "4. 内容电商与兴趣电商")
T("theory-aida", "AIDA 与漏斗", None,
  "注意→兴趣→欲望→行动。短视频是非线性的，把 AIDA 当顺序执行会做出「先自我介绍再讲正事」的开头；只借「四件事都要有」，不借顺序。",
  "E. St. Elmo Lewis, 1898；Kotler, 2017", DAD, "3. AIDA 与漏斗",
  status=UNVERIFIED, note="归属待确认：跨层的漏斗模型，文档明确否定其顺序，未归入任何单一层。")
T("theory-north-star", "北极星指标", "layer-closed",
  "全团队唯一要拉动的那个数。本账号北极星 = 有效私信数（出现「多少钱/能不能做」的私信条数），不是粉丝数。",
  "Sean Ellis【经验帖】", DGROWTH, "1. AARRR 与北极星指标")
T("theory-aarrr", "AARRR", None,
  "获取→激活→留存→收入→推荐。内容账号没有「激活/留存」的用户概念，取关成本为零；只保留获取（播放）与收入（有效私信）两段。",
  "Dave McClure, 2007", DGROWTH, "1. AARRR 与北极星指标",
  note="跨层使用：只保留获取段（第 1 层）与收入段（第 5 层）。")
T("theory-nps-referral", "NPS 与复购转介绍", "layer-referred",
  "获客成本要靠生命周期价值摊平，转介绍是最便宜的获客，K>1 才自增长。客户数 <50 时 K 因子无统计意义；改为交付后要一句可公开的评价。",
  "Reichheld, HBR, 2003", DGROWTH, "5. 复购与转介绍的经济学")
T("theory-rfm", "RFM", None,
  "按最近一次行为、频次、金额分层。当前没有用户级交易数据，分层无统计意义。替代动作：手工维护 10 行私信表。",
  "Arthur Hughes, 1994", DGROWTH, "2. 用户生命周期与分层",
  note="孤岛：文档自列为「找不到合适位置、不硬塞」的三个模型之一。")
T("theory-k-factor", "K 因子与 CLV/CAC", None,
  "K = 邀请数 × 转化率，K>1 才自增长；CLV/CAC 用来判断获客是否划算。客户数 <50、项目制、转介绍周期长时，指标不成立。",
  "Skok, SaaS Metrics 2.0, 2010", DGROWTH, "5. 复购与转介绍的经济学",
  note="孤岛：客户数 <50，统计无意义。")
T("theory-ab-test", "增长实验（A/B）", None,
  "把想法写成可证伪假设，用最小样本验证再决定加码或放弃。几百播放时无统计功效，实验退化为观察，延后到单条稳定过万播放。",
  "Eric Ries, 2011；Kohavi et al., 2020", DGROWTH, "4. 增长实验",
  note="孤岛：延后使用。")

# ---- 横切：模型 / 框架 ----
T("model-six-layers", "六层链路（串联电路）", None,
  "前一层不成立，后一层做了也白做：流量在先、记忆在信任之前、信任在成交之前、成交在转介绍之前。断一层，后面全黑。",
  "本项目总纲", D00, "原则 / 层与层之间的传导")
T("model-review-8col", "单条视频复盘（8 列法）", None,
  "48 小时内只看四个数（5 秒完播、完播率、评论数、私信数），记 8 列（编号/选题类型/开头方式/时长/发布时段/播放/完播率/评论·私信）；一次只改一个变量。",
  "本项目方法", DREVIEW, "一至三节")
T("model-sampling-bounds", "抽样与归因四问", None,
  "下结论前四问：分母是谁？是「没观察到」还是「测到没有」？自变量分布开了吗？删掉形容词还是事实吗？四问有一个答不上来，只能写「样本内观察」。",
  "本项目复盘方法", DSAMPLE, "全文")
T("model-public-boundary", "公开内容边界（给判断不给步骤）", None,
  "公开内容只交付判断，操作步骤留给私域。步骤招来「求源码/求提示词」的人，判断招来「我也遇到过」的人。唯一转化句：「想看这类情况的处理教程，私聊我。」",
  "本项目规则（团队定，置信度高）", DPUB, "全文",
  note="横切规则，主要作用于第 3 层（信任）与第 4 层（承接）。")
T("model-compliance", "违规红线", None,
  "官方明文禁止：搬运、重复低质、诱导互动、诱导站外导流、虚假宣传、无资质敏感领域。限流阈值、敏感词库、重复判定相似度均未获取。",
  "《抖音社区自律公约》等【官方】", DRED, "一、有官方条文的行为",
  note="横切约束：不属于任何一层，但每层都受它限制。")
T("model-monetization-forms", "五种变现形态", "layer-closed",
  "接服务、卖课、卖产品、接广告、换股权/顾问。主线只做接服务（单人年营收上限约 30–60 万，经验推断），课程只做私域钩子，不接无关商单。",
  "经验推断【经验帖】", DBIZ, "全文",
  note="主挂第 5 层，辅挂第 6 层。")
T("model-direction-switch", "方向切换判据", None,
  "抖音不认时的四个判据（前 3 秒留存、完播率、评论区接话率、私信/加微转化），三种外壳从轻到重：结果前置 → 替别人解决麻烦 → 转拆解评测。人设内核不动。",
  "本项目规则", DDIR, "全文",
  note="四个判据的阈值全部「待校准」，见 index.md 缺口节。")
T("model-anomaly-types", "反常选题六型", None,
  "内容单位 = 一次反常：一个 AI 不听话/出乎意料的瞬间 + 当时的判断。六型：权限边界拒绝、听懂但做错、过度谨慎、自作主张、答非所问、记忆错乱。",
  "本项目选题框架", DTOPIC, "反常类型")

# ============================ 动作 ============================
# ---- 第 1 层 ----
A("a-same-topic-first5", "前 5 条固定同一题材", "layer-seen",
  "标题与口播固定出现「智能体 / 客户现场 / 交付」三个词，连续 5 条不换。换题材等于重新冷启动一次。", D00, "第一层·必须做的动作")
A("a-anomaly-first3s", "前 3 秒给一个具体反常", "layer-seen",
  "第一帧/第一句就是具体反常，不出现人脸打招呼、不出现片头。", D00, "第一层·必须做的动作")
A("a-one-gap", "一条只开一个缺口，15 秒合一半", "layer-seen",
  "每条只开一个好奇心缺口，15 秒内合上一半，结尾再开下一个。", D00, "第一层·必须做的动作")
A("a-cut-rhythm", "每 3–5 秒一次画面变化", "layer-seen",
  "切镜/推近/字卡/录屏缩放，每 3–5 秒一次；开头 3 秒至少一次变化。", DCRAFT, "二、剪辑")
A("a-speech-pace", "口播节奏（280–320 字/分）", "layer-seen",
  "每分钟 280–320 字，单句 ≤15 字，转折前停 0.5–0.8 秒，每句只放一个重音。35 秒约 160–180 字，按字数倒推写稿。", DCRAFT, "一、口播")
A("a-audio-floor", "录音与录屏下限", "layer-seen",
  "室内也必须用领夹麦；窗户侧光，不顶光不背光；录屏前关通知，IDE 字号 ≥16px。", DCRAFT, "三、设备下限")
A("a-one-variable", "每条只改一个变量", "layer-seen",
  "开头方式 / 时长 / 落点 / 发布时段，四选一，每组 3 条。同时改三个，爆了也不知道为什么。", DTRAFFIC, "2. 探索与利用")
A("a-no-cart", "不挂车、不带货", "layer-seen",
  "高客单 B 端不适用兴趣电商。把「让人愿意私信」这一步留下，剩下交给人工。", DTRAFFIC, "4. 内容电商与兴趣电商")
A("a-peripheral-first3s", "前 3 秒走边缘路径", "layer-seen",
  "真人出镜 + 现场感 + 一句话身份建立可信，中段再上论据。只走边缘会变成人设号没干货，只走中心会变成教程号没人看。", DSPREAD, "4. 说服的中心路径与边缘路径")
A("a-no-number-opening", "开头不给数字堆叠", "layer-seen",
  "短视频只能激活快系统，开头给画面和一句话事实，把数字放到中段。", DPSY4, "这个账号上的动作·4")

# ---- 第 2 层 ----
A("a-bio-identity", "改简介：第一行只写一个身份", "layer-remembered",
  "第一行只出现一个身份（能把 AI 讲成人话、还能替你落地的人），不出现「爱好者/学习者/分享者」。", DAD, "1. 定位理论·动作")
A("a-main-slogan", "定主口号，30 天不改", "layer-remembered",
  "建议主口号「AI 不听话的时候，我在场」；简介第一行用信息完整的版本，片尾字幕用短的版本。", D00, "第二层·必须做的动作")
A("a-assoc-words", "只强化 A 组联想词", "layer-remembered",
  "只强化「现场 · 交付 · 跑通」一组，连续 10 条不换；简介、置顶、片尾都只放这三个词。", DAD, "12. 实操：5 组候选联想词")
A("a-fixed-phrase", "每条结尾固定句式", "layer-remembered",
  "固定「我让它做 X，它……」，让观众能套自己的经历，这是唯一能带来 UGC 的结构。", DSPREAD, "2. 模因与模仿")
A("a-fixed-intro", "固定片头 0.5 秒同一动作", "layer-remembered",
  "同一位置、同一动作/同一句话，让「又是他」的识别发生在 1 秒内。不做长片头。", DAD, "10. 曝光效应·动作")
A("a-two-day-cadence", "两天一更，不日更", "layer-remembered",
  "形式重复、内容不重复；间隔太密会提前进入曝光效应的下降段，同质内容高频发布也可能被判低质。", DAD, "10. 曝光效应·动作")

# ---- 第 3 层 ----
A("a-number-each", "每条至少一个可核对数字", "layer-trusted",
  "跑了多少单、原来几小时、现在几分钟、错误率多少。不用「效果很好」。", DMAP, "直接说服 / 中心路径")
A("a-refutable-claim", "每条一个可反驳的判断句", "layer-trusted",
  "「Agent 的边界应该写在职责里，不是写在提示词里」这类能被反驳的判断，不是「AI 很重要」。", D00, "第三层·必须做的动作")
A("a-admit-failure", "主动讲一次失败/判断错误", "layer-trusted",
  "不每条都成功；给一个私人细节（判断错了、被客户拒绝、熬到几点），这是准社会关系的必需品。", DPSY1, "这个账号上的动作·2")
A("a-face-to-camera", "每条露脸并对镜头说一句话", "layer-trusted",
  "不是全程旁白配录屏。对镜头说话是打破第四面墙，让关系从「内容」转向「人」。", DPSY1, "这个账号上的动作·1")
A("a-reply-restate", "回评论先复述对方问题", "layer-trusted",
  "「你说的是 XX 那种情况吧」再回答，比直接给答案更让人觉得被听见。用第一人称、带情绪，不用客服口气。", DHUM1, "这个账号上的动作·2")
A("a-judgment-only", "公开内容只给判断不给步骤", "layer-trusted",
  "步骤、提示词全文、参数值、完整代码、分步编号一律不给；给判断、反常表现、代价、可迁移的观点。", DPUB, "一句话规则")
A("a-no-effect-promise", "不承诺效果", "layer-trusted",
  "不写「包」「保证」「百分百」「稳赚」，不说「省 80%」，改成可核对的事实句。", DRED, "五、这个账号意味着什么")
A("a-real-review", "用真实客户评价截图", "layer-trusted",
  "不用「很多人都在用」；截图必须是真实评价，造假被识破后反噬更强。", DAD, "5. 广告起作用的三种方式")
A("a-not-expert-intro", "不说「我是 XX 专家」", "layer-trusted",
  "改说「我最近在给一家公司做 XX」——前者是支配型宣告，后者是声望型展示。", DHUM4, "这个账号上的动作·2")
A("a-no-peer-bashing", "不贬低同行", "layer-trusted",
  "贬低是支配型动作，会吸引来怕你的人，不是跟你做事的人。", DHUM4, "这个账号上的动作·3")
A("a-client-situation", "描述客户处境不写自己辛苦", "layer-trusted",
  "「他们每天有个人专门对表」而不是「我熬夜改到三点」——谈对方的利益，不谈自己的成就。", DHUM1, "这个账号上的动作·1")
A("a-story-first", "故事在前、道理在后", "layer-trusted",
  "给真实场景三要素（谁、在干什么、卡在哪），结尾才给判断句，顺序不能反。", DPSY3, "这个账号上的动作·1/4")
A("a-first-person-now", "第一人称现在时讲自己的案例", "layer-trusted",
  "「我点开它，它回我一句：这不在我的职责里」，不用「曾经有一次」；不讲别人的成功案例。", DPSY3, "这个账号上的动作·2/3")
A("a-blur-client", "客户素材打码化名", "layer-trusted",
  "所有客户画面打码，名称用「一家做 XX 的公司」，并在视频里说一句「已获客户许可」。", DRED, "四、对 FDE 账号的高危点·1")

# ---- 第 4 层 ----
A("a-bio-three-lines", "简介三行（身份/做过什么/入口）", "layer-found",
  "身份一句话 / 做过什么 / 入口一句话，30 天不动。写事实不写形容词。", D00, "第四层·必须做的动作")
A("a-pin-case", "置顶放一条交付案例", "layer-found",
  "不是自我介绍。客户进来先看案例，不看朋友圈。", D00, "第四层·必须做的动作")
A("a-two-titles", "同内容两套标题", "layer-found",
  "推荐版写反常，搜索版写问题词，搜索版晚 3–7 天发或做成合集标题。", DTRAFFIC, "5. 搜索流量 vs 推荐流量")
A("a-share-to-peers", "每条成片发 3–5 个同行", "layer-found",
  "发给已经在做企业服务的同行、前同事，请他们转群——比投流便宜，也比等算法快。", DSPREAD, "3. 两级传播")
A("a-dm-only-asset", "每条留一个只能私信拿到的东西", "layer-found",
  "一份流程清单、一个报价口径、一份验收清单。把一次性注意力转成可联系的人。", DHUM2, "这个账号上的动作·1")
A("a-own-contact-list", "客户名单自己建表", "layer-found",
  "加微信后建表：行业、问题、预算、时间。平台只做入口，不做仓库。", DHUM2, "这个账号上的动作·2")
A("a-minimal-private", "私域只做一个微信 + 一条置顶案例", "layer-found",
  "不做社群运营，不做朋友圈人设。客户进来先看案例。", DGROWTH, "3. 私域与公域的承接结构")
A("a-no-irrelevant-ads", "不接与能力无关的商单", "layer-found",
  "商单是把注意力卖给第三方，卖错一次人设就变成恰饭号；只接云厂商、开发工具这类相关方。", DHUM2, "这个账号上的动作·3")

# ---- 第 5 层 ----
A("a-anchor-quote", "报价先给锚点", "layer-closed",
  "先摆完整版价格，再说轻量版；只给两个方案 + 一个明显不划算的参照，让人在快系统里就能选。", DPSY4, "这个账号上的动作·1/3")
A("a-loss-frame", "标题用损失框架", "layer-closed",
  "「这套没做，每天多花 3 小时」，不用「效率提升 300%」（后者是效果承诺，有合规风险）。", DPSY4, "这个账号上的动作·2")
A("a-info-emotion-73", "信息:情绪 ≈ 7:3", "layer-closed",
  "信息为主（数字、流程、失败记录），情感只用于让人愿意看完（意外、挫败、现场感）。", DAD, "9. FCB 网格·动作")
A("a-dm-first-scene", "私信第一轮只要一句话场景", "layer-closed",
  "不要预算和电话。把互动成本降到最低，回报做得确定。", DHUM5, "这个账号上的动作·3")
A("a-first3-no-cta", "前 3 条不提转化", "layer-closed",
  "先给三次再提要求；第 4 条起才出现「想要的私信我」。", DHUM3, "这个账号上的动作·3")
A("a-low-cost-gift", "每条留一个低成本可用的东西", "layer-closed",
  "「这套东西的验收清单我整理过，要的私信我」——给完还能留一个动作。", DHUM3, "这个账号上的动作·2")
A("a-one-cta", "每条只提一个动作", "layer-closed",
  "同时要赞、要评、要关注、要私信，等于成本翻四倍，结果一个都不做。", DHUM5, "这个账号上的动作·4")
A("a-binary-comment", "评论门槛给二选一", "layer-closed",
  "「A 还是 B」而不是「你们怎么看」；这是第 1 层想法征集段的低成本写法。", DHUM5, "这个账号上的动作·1")
A("a-promise-reply", "承诺「评论区问的下条答」", "layer-closed",
  "把回报变得确定，让人知道评论有回音。", DHUM5, "这个账号上的动作·2")
A("a-no-ads-first15", "前 15 条不投流", "layer-closed",
  "没有转化回传前投 DOU+ 只能买播放；出现 ≥3 个私信问价后，只把那条投 100 元验证人群。", DAD, "4. 效果广告·动作")
A("a-quote-onepager", "报价口径一页纸", "layer-closed",
  "范围、交付物、修改次数、周期、付款节点、不做什么。预付 30–50%，尾款验收后结。", DBIZ, "六、对这个账号意味着什么·5")
A("a-service-only", "主线只做接服务", "layer-closed",
  "卖课/卖产品/接广告/换股权作为第 2 年之后的选项，前 6 个月不启动；课程只做私域钩子。", DBIZ, "六、对这个账号意味着什么")
A("a-dm-log", "手工私信表（每周记问价条数）", "layer-closed",
  "10 行以内，不上系统：谁问过、问什么、有没有预算、有没有报价。每周记一次有效私信数。", DGROWTH, "2. 用户生命周期与分层")
A("a-no-ab", "前 15 条不做 A/B", "layer-closed",
  "只做「每 5 条复盘一次类型配比」，等单条稳定过 1 万播放再谈对照实验。", DGROWTH, "4. 增长实验·动作")

# ---- 第 6 层 ----
A("a-ask-review", "交付当天要一句可公开的评价", "layer-referred",
  "不要求好评，只要具体。「不要设计推荐有礼，量太小」——评价是唯一能积累的社会认同资产。", DGROWTH, "5. 复购与转介绍·动作")
A("a-review-to-pin", "评价截图进置顶", "layer-referred",
  "把公开评价变成可被后来者看到的证据，替代「很多人都在用」。", DBIZ, "六、对这个账号意味着什么·3")
A("a-quarterly-touch", "每季度给老客户发一次同类问题", "layer-referred",
  "「我看到一个跟你类似的问题」，不问单。维持关系，等待转介绍自然发生。", D00, "第六层·必须做的动作")
A("a-no-referral-gift", "不设计「推荐有礼」", "layer-referred",
  "客户数 <50，K 因子无统计意义；返佣会把转介绍变成交易，损伤声望型地位。", DGROWTH, "5. 复购与转介绍·动作")
A("a-no-equity", "不接股权换服务", "layer-referred",
  "除非对方已付费且金额覆盖成本。用服务换股份，常见结局是既没收到钱也没拿到股权。", DBIZ, "六、对这个账号意味着什么·4")

# ---- 横切 ----
A("a-compliance-4q", "发布前合规四问", None,
  "有没有承诺效果？有没有出现客户信息？有没有引导站外？有没有资质外内容（医疗/金融/法律建议）？", DRED, "五、这个账号意味着什么·1")
A("a-review-8col", "复盘记 8 列 / 48 小时看四数", None,
  "一条一行，存在一张表里；48 小时后数据基本定型。列多了会变成「看数据」而不是「改动作」。", DREVIEW, "一至三节")
A("a-review-order", "判定顺序：开头→观点→人设", None,
  "先看 2 秒跳出（开头），再看评论（有没有观点），最后看主页访问（人设）。不要一上来就怀疑选题。", DREVIEW, "四、判定")
A("a-topic-twice", "同一选题最多试两次", None,
  "两种开头都低就判死，不第三次，避免在讲不明白的题上反复消耗。", DREVIEW, "四、判定")

# ============================ 指标 ============================
M("m-plays", "播放量", "layer-seen", "分发规模。只作分母，不单独看。", DREVIEW, "一、48 小时内看哪几个数")
M("m-2s-bounce", "2 秒跳出率", "layer-seen", "开头是否成立。高 = 第一帧/第一句不成立，换第一句而不是换选题。", DREVIEW, "一、48 小时内看哪几个数")
M("m-5s-completion", "5 秒完播率", "layer-seen", "钩子是否成立。<50% 说明开头有问题【经验帖】。", DREVIEW, "一、48 小时内看哪几个数")
M("m-completion", "完播率", "layer-seen", "内容是否撑得住。必须与时长一起看，35 秒与 6 分钟不可比。", DREVIEW, "一、48 小时内看哪几个数")
M("m-avg-watch", "平均播放时长", "layer-seen", "观众在哪掉。结合进度条曲线看掉点位置。", DREVIEW, "一、48 小时内看哪几个数")
M("m-3s-retention", "前 3 秒留存", "layer-seen", "算法推不推的第一判据（创作者中心「3 秒完播率」）。阈值待校准。", DDIR, "一、判「抖音不认」的四个指标")
M("m-followers", "涨粉数", "layer-seen", "阶段目标的量级指标（30 天 1 万），但不是北极星。", DGROWTH, "1. AARRR 与北极星指标")
M("m-same-audience", "同类人群完播", "layer-seen", "不追「进池」，只追同类人看完并接话。比播放量有意义。", DTRAFFIC, "3. 流量池分层与冷启动")
M("m-profile-visits", "主页访问", "layer-remembered", "人设是否成立。播放高但主页访问低 = 只看内容不认人。", DREVIEW, "一、48 小时内看哪几个数")
M("m-brand-search", "品牌词搜索量", "layer-remembered",
  "被记住的强证据（有人主动搜你）。当前外部通道不可测，只能靠后台或站内搜索人工看。", D00, "第二层·怎么判断成了",
  status=SUPPORTED, note="当前采集通道拿不到：未登录无法查品牌词搜索量。")
M("m-identity-recall", "定位词/句式复述", "layer-remembered",
  "评论区有人用你的句式接话，或直接叫出你的定位词。可观测，不需要后台数据。", D00, "第二层·怎么判断成了")
M("m-comments", "评论数", "layer-trusted", "是否产生「想留」的动作。纯情绪与具体追问要分开看。", DREVIEW, "一、48 小时内看哪几个数")
M("m-favorites", "收藏数", "layer-trusted", "收藏 > 点赞 = 信息型内容；点赞 > 收藏 = 情绪型内容。", DREVIEW, "一、48 小时内看哪几个数")
M("m-demand-signal", "评论需求信号（L1/L2）", "layer-trusted",
  "L1 求定制/问价、L2 求方法的原话条数。比播放量更能判断加推质量。", D00, "第三层·怎么判断成了")
M("m-search-dm", "搜索来源私信", "layer-found", "私信第一句出现「我搜 XX 找到你的」。证明搜索标题命中。", D00, "第四层·怎么判断成了")
M("m-profile-to-dm", "主页访问→私信转化率", "layer-found", "私信数 ÷ 主页访问（后台有访问数）。", D00, "第四层·怎么判断成了")
M("m-dm-to-wechat", "私信→加微转化率", "layer-found", "加微数 ÷ 私信数。衡量承接结构是否顺畅。", DDIR, "一、判「抖音不认」的四个指标")
M("m-contact-list", "客户名单数", "layer-found", "留下了几个能联系的人。粉丝是平台的，联系人是你的。", DHUM2, "这个账号上的动作·4")
M("m-effective-dm", "有效私信数（北极星）", "layer-closed",
  "出现「多少钱/能不能做/什么价」的私信条数。北极星指标，不是粉丝数。", DMAP, "北极星指标")
M("m-price-dm", "私信问价条数", "layer-closed", "≥3 条才考虑投流验证人群；每条视频带来 ≥1 条问价私信即为有效。", DREVIEW, "一、48 小时内看哪几个数")
M("m-quotes", "报价数", "layer-closed", "发出报价的条数，手工记。有效私信 → 报价的流失能看出方案问题。", D00, "第五层·怎么判断成了")
M("m-close-rate", "成交率", "layer-closed", "报价 → 成单。没有信任的询价会直接进入比价，成交率是信任的终点指标。", D00, "第五层·怎么判断成了")
M("m-order-value", "客单价", "layer-closed", "手工记。接服务的单笔金额，决定单人产能下的营收上限。", DBIZ, "一、接服务")
M("m-payment-cycle", "回款周期", "layer-closed", "预付 30–50%，尾款验收后结；回款周期 1–3 个月，淡旺季明显（经验推断）。", DBIZ, "一、接服务")
M("m-public-reviews", "公开评价数", "layer-referred", "≥3 条。转介绍的地基。", D00, "第六层·怎么判断成了")
M("m-referrals", "老客户主动推荐数", "layer-referred", "≥1。唯一能证明复利存在的指标。", D00, "第六层·怎么判断成了")

# ============================ 缺口（文档提到但没展开 / 缺失） ============================
# ============================ 第二批（L1–L4 补篇） ============================
DHOME = "methodology/L1-主页包装与转化路径.md"
DFUNNEL = "methodology/L1-内容营销漏斗.md"
DPLAT = "methodology/L1-平台-七大平台对照.md"
DIP = "methodology/L2-战略-IP操盘.md"
DSTP = "methodology/L2-战略-STP与人群.md"
DCHOICE = "methodology/L2-战略-三个未决选择.md"
DBIZMODEL = "methodology/L2-战略-商业模式与定价.md"
DWEEK = "methodology/L3-战术-一周内容节奏.md"
DREPLY = "methodology/L3-战术-评论区与私信话术.md"
DXPLAT = "methodology/L3-战术-跨平台改写.md"
DSOP1 = "methodology/L4-SOP-起号.md"
DSOP2 = "methodology/L4-SOP-发布.md"
DSOP3 = "methodology/L4-SOP-接单.md"
DSOP4 = "methodology/L4-SOP-复盘.md"
DPROD = "methodology/经营-02-产品化.md"
DNEGO = "methodology/经营-03-议价与谈判.md"
DRISK = "methodology/经营-04-品牌风险与对冲.md"

T("theory-homepage-packaging", "主页包装标准", "layer-found",
  "头像、名字、简介三行、置顶三条、背景图五项。验收标准只有一个：陌生人看主页 3 秒，能说出「这人做什么的」。",
  "经验推断（头像/置顶/封面在 40 个账号抽样中读不到）", DHOME, "一、主页包装",
  note="全部为经验推断，无样本验证：未登录时主页元素不渲染。")
T("theory-diversion-boundary", "站外导流边界", "layer-found",
  "私信、评论区、主页、企业号四个入口各自能做什么、风控触发点在哪。顺序原则：公开区只引发对话，联系方式只在私信里、且对方先开口后给。",
  "《抖音社区自律公约》【官方】+ 经验【经验帖】", DHOME, "二、转化路径细则")
T("theory-funnel-six", "内容营销漏斗（六段）", None,
  "曝光→停留→认同→关注→私信→成交，每段有各自的损耗点与测法。短视频账号的漏斗不是线性的，但损耗点可以逐段定位。",
  "本项目归纳", DFUNNEL, "一、六段漏斗",
  note="跨层：六段与六层主干一一对应，但不完全等同（认同段横跨第 2/3 层）。")
T("theory-platform-structure", "平台分发结构差异", None,
  "只有抖音是纯推荐起量；视频号靠社交、小红书靠搜索、知乎靠问题页、B站靠完播。同一套内容逻辑不能平移。B 端客户在视频号/微信生态，不在抖音。",
  "行业通行描述【经验帖】（比例与成本均未获取）", DPLAT, "二、三条结构性判断")
T("theory-goffman", "自我呈现（前台/后台）", "layer-trusted",
  "人在前台表演一个角色，在后台卸下；前台的稳定性决定别人信不信。划法：能力不能演，态度可以演；经历不能编，表达可以设计。",
  "Erving Goffman, 1959", DIP, "一、人设怎么搭")
T("theory-ip-lifecycle", "IP 生命周期四阶段", None,
  "识别期（0–1 万）→ 信任期（1–10 万）→ 规模期（10–50 万）→ 资产期（50 万+），每阶段该做与不该做不同。判断当前阶段只看私信里问价的比例。",
  "本项目归纳", DIP, "二、IP 生命周期四阶段",
  note="跨层：当前在识别期，只做固定句式与固定题材。")
T("theory-assetization", "内容资产化", "layer-remembered",
  "一条视频至少沉淀四样：判断句、案例卡（场景+数字+前后对比）、开头模板、客户问题。只贡献播放、没产出任何一样的，是消耗品不是资产。",
  "本项目归纳", DIP, "三、内容资产化")
T("theory-crisis-pr", "危机公关四步", "layer-trusted",
  "2 小时内不删不辩论、先确认事实；当天发「事实+做了什么+何时给结果」；48 小时私下给补救；一周后经客户同意把处理做成内容。三条禁忌：删评、对喷、找水军。",
  "经验流程【经验帖】", DIP, "四、危机公关处置流程")
T("theory-stp", "STP 与人群选择", "layer-remembered",
  "按身份、痛点强度、决策链长度三个变量细分；细分成立的标准是这群人能不能在同一个地方被触达。本账号先选「中小企业老板」，同行只作流量池。",
  "STP 为教材通说【文献】；客单价为经验推断", DSTP, "一至三节")
T("theory-competitive-map", "竞争地图（技术深度 × 是否到场）", "layer-remembered",
  "四象限里，浅+不到场是教程号，深+不到场是大厂，浅+到场是外包公司；「深 + 到场」是空位，也是 FDE 唯一该占的格。",
  "本项目归纳", DSTP, "四、竞争地图")
T("theory-three-choices", "平台/人群/形态三选择", None,
  "三个未决选择互相耦合：平台决定客户在哪，人群决定话术，形态决定现金流。不能同时选最重的一档。",
  "本项目归纳", DCHOICE, "三个选择的耦合关系")
T("theory-pricing-methods", "定价三法", "layer-closed",
  "成本加成算底线、价值定价报出去、竞争定价只做校验。顺序不能反：先算底线，再按客户省的钱报，最后才看同行。",
  "行业通说【经验帖】", DBIZMODEL, "二、定价三法")
T("theory-negotiation", "议价路径与让步规律", "layer-closed",
  "小 B 客户砍价按四步发生：便宜点→拆单→比价→账期。每一次让步都会引出下一次试探，第一次让步的方式决定后面四步的强度。原则：降范围，不降价。",
  "经验推断【经验帖】", DNEGO, "一、小 B 客户的砍价路径")
T("theory-productization", "产品化（标准包）", "layer-closed",
  "按「输入-输出」划范围而不是按工作量；一个硬边界：不在清单里的需求就是新项目。同一需求被问 3 次以上、交付物开始同构，才值得做标准包。",
  "经验推断【经验帖】", DPROD, "一至四节")
T("theory-risk-hedge", "四类品牌风险与对冲", None,
  "单点依赖、平台依赖、声誉风险、被抄袭。风险不是单独一层，而是同时作用在第 2–4 层：平台依赖伤被看见，单点依赖伤被成交，声誉风险伤被信任。",
  "经验推断【经验帖】", DRISK, "全文",
  note="横切：对冲动作分散在各层，不集中在某一层。")
T("theory-cross-platform-rewrite", "跨平台改写（不能平移）", "layer-found",
  "开头、时长、引导语、封面都要按平台重做：抖音要反常第一帧，视频号要先给身份与背景，小红书标题即搜索词，B站先给问题。直接同步会被各平台限流。",
  "经验推断【经验帖】", DXPLAT, "二、四条改写原则")

A("a-avatar-set", "头像/昵称/背景三件套", "layer-found",
  "头像真人正脸、深色纯背景、脸部占 50–60%、缩到 40px 仍能认出；昵称「称呼+定位词」≤10 字；背景用工作场景、压暗 30%。", DHOME, "一、主页包装")
A("a-no-contact-public", "公开区不写联系方式", "layer-found",
  "简介、评论区、视频里都不写微信/手机号/二维码；替代写法「案例在置顶」「评论区说下你的场景」「合作备注来意」。", DHOME, "二、转化路径细则")
A("a-weekly-focus", "每周只盯漏斗的一段", "layer-closed",
  "第 1 周盯开头（第 2 段），第 2 周盯私信（第 5 段），不全都看。第 5 段的动作最便宜：置顶加一条案例 + 评论置顶加需求模板。", DFUNNEL, "五、对这个账号意味着什么")
A("a-platform-priority", "抖音主战场 + 视频号第二落点", "layer-found",
  "抖音要量（第 1 层），视频号要人（第 4 层）。小红书只做图文，B站/知乎暂不做，微博/快手不做。", DPLAT, "三、对 FDE 账号意味着什么")
A("a-xhs-graphic", "小红书图文版（20 分钟）", "layer-found",
  "把一条视频的判断句 + 3 张截图做成笔记，标题写成搜索词，成本约 20 分钟，占搜索位。", DXPLAT, "三、成本与排期")
A("a-asset-four", "每条沉淀四样资产", "layer-remembered",
  "判断句、案例卡、开头模板、客户问题，四样至少产出一件；否则这条白拍。", DIP, "三、内容资产化")
A("a-crisis-four-step", "危机处置按四步走", "layer-trusted",
  "2 小时确认事实 → 当天简短说明 → 48 小时私下补救 → 一周后经同意做成内容。不删评、不对喷、不找水军。", DIP, "四、危机公关处置流程")
A("a-positioning-statement", "定位陈述一句话模板", "layer-remembered",
  "「为已经有 AI 想法但落不了地的中小企业，提供从流程诊断到系统上线的一次交付……不同于教程号和外包公司，因为我到场做过，且能给出可核对的前后数字。」写进简介第一行，30 天不改。", DSTP, "五、定位陈述")
A("a-boss-three-questions", "每条回答老板三问", "layer-trusted",
  "这要花多少钱、跟我像不像、做完谁在用。三条内容分别对应成本、案例、交付。", DSTP, "六、对这个账号意味着什么·2")
A("a-payment-willingness-3q", "支付意愿三问", "layer-closed",
  "看他已经在为什么付钱（招人/外包/SaaS）；问「这类事你们去年花过多少钱」；看谁签字。写进接单 SOP 第 2 步。", DSTP, "三、支付意愿怎么判断")
A("a-deep-onsite-only", "只占「深 + 到场」一格", "layer-closed",
  "纯咨询、纯卖课、纯不到的活都不接；竞争地图只占一格，任何「不到场」的收入都不做。", DSTP, "六、对这个账号意味着什么·3")
A("a-cashflow-rules", "现金流三条硬规则", "layer-closed",
  "预付 50% 才开工、尾款验收 7 天内；单客户收入占比 ≤40%；保留 3 个月固定支出的现金。", DBIZMODEL, "三、现金流三条硬规则")
A("a-cost-first-pricing", "报价三步（成本底线→价值定价→不跟价）", "layer-closed",
  "先用成本加成算底线（(工时×时薪)÷(1−毛利率)），再按客户省的钱报价值价，最后用同行价只做校验、不跟价。", DBIZMODEL, "五、对这个账号意味着什么·2")
A("a-log-hours", "每单记工时", "layer-closed",
  "3 单后回头校正时薪；现在的毛利率是推断不是事实。", DBIZMODEL, "五、对这个账号意味着什么·3")
A("a-weekly-rhythm", "一周节奏（精品 3 : 测试 1）", "layer-seen",
  "精品条 3 条/2 周（有数字、有前后对比），测试条 1 条/周（只改一个变量）。全是测试条没有资产，全是精品条不知道哪种有效。", DWEEK, "一、两类条目的配比")
A("a-fixed-slot", "固定发布时段，30 天不变", "layer-seen",
  "建议 19:00–21:00 里的同一时段；时段随机，复盘时无法排除时间因素。", DSOP2, "5. 发布时间")
A("a-same-agent-limit4", "同一智能体纵深 ≤4 条", "layer-remembered",
  "超过 4 条必须换案例，防止审美疲劳；纵深是形式重复、内容不重复的边界。", DWEEK, "三、三条硬规则·3")
A("a-comment-templates", "评论区五种场景话术", "layer-trusted",
  "问怎么做→「没讲步骤，讲的是判断，私信说场景」；问工具→不报工具名；被质疑→承认特例并给条件；同行挑衅→只回一句；纯喷→不回不删。", DREPLY, "一、评论区")
A("a-pinned-self-comment", "置顶自评抛二选一", "layer-seen",
  "每条发完自己置顶一条：「这次我想错了，你觉得该怎么做？」给一个具体二选一。", DREPLY, "一、评论区·置顶自评")
A("a-ladder", "评论→私信三级阶梯，不跳级", "layer-closed",
  "看（0 成本）→ 评论区二选一（低成本）→ 私信一句话场景（中成本）。视频里直接喊「私信我报价」等于让陌生人第一次接触就付最高成本。", DREPLY, "三、三级阶梯")
A("a-scope-not-price", "降范围不降价", "layer-closed",
  "「这个预算能做，范围砍到只做 X，Y 和 Z 下次再加」。价格是能力的信号，一降就再难涨回去。", DNEGO, "二、四种压价话术与应对")
A("a-refuse-five", "五条拒单标准", "layer-closed",
  "预算低于最低时薪×工时、要求先做后付、合同前改需求 3 次、决策人非付款人、无对价排他。触发即拒，不临场心软。", DNEGO, "四、什么时候该拒单")
A("a-material-audit-15", "起号前盘点 ≥15 个反常瞬间", "layer-seen",
  "按五类归档存量素材；≥15 个才开工，<15 缩到 10 条排期。边拍边想，第 3 条就断更。", DSOP1, "6. 素材盘点")
A("a-publish-sop", "发布 SOP 八步", "layer-seen",
  "定稿四问 → 标题「具体对象+反常结果」≤20 字（另备搜索版）→ 封面用信息量最大一帧 + 6–10 字 → 话题 3 个 → 固定时段 → 手机端发布 → 2 小时回评 → 24 小时记 8 列。", DSOP2, "全文")
A("a-topic-tags", "话题三个：垂类 + 问题 + 泛流量", "layer-seen",
  "1 个垂类（#智能体）+ 1 个问题（#AI落地）+ 1 个泛流量，总数 ≤4，不堆 10 个蹭流量。", DSOP2, "4. 话题")
A("a-reply-2h", "发布后 2 小时回评，回复率 100%", "layer-trusted",
  "每条评论带具体回答，不用「谢谢」；同时置顶一条自评。", DSOP2, "7. 发布后 2 小时")
A("a-weekly-review", "每周一复盘 30 分钟（五步）", None,
  "补 8 列 → 看四数 → 每条定性一类（开头失败/无观点/人设弱/选题不行）→ 与上周比哪类占比变化最大 → 写一句「下周只改 ___」。", DSOP4, "全文")
A("a-trigger-adjust", "触发式调整，不按心情", None,
  "连续 3 条 5 秒完播 <40% → 停更一周重写开头库；单条稳定 >1 万播放 → 开始 A/B；一周 ≥3 条问价 → 投 100 元测试；连续 2 周 0 私信 → 查第 3 层，不加更。", DSOP4, "什么时候调整")
A("a-takeorder-sop", "接单 SOP 八步", "layer-closed",
  "2 小时首响 → 需求三问 → 按标准包核对能不能做 → 只发一页报价单 + 一条最像他场景的案例 → 报价（完整版在前）→ 砍价只降范围 → 收 50% 定金并发启动确认 → 不能做就推荐同行。", DSOP3, "全文")
A("a-quote-two-materials", "只发两样材料", "layer-closed",
  "一页报价单 + 一条最像他场景的案例视频；不发作品集 PDF（没人看）。", DSOP3, "4. 发材料")
A("a-scope-io", "按输入-输出划范围", "layer-closed",
  "输入：客户提供什么；输出：一个能跑的流程 + 1 次培训 + 1 份文档。范围用「不超过」表述：3 个流程、2 个系统、10 个账号。", DPROD, "一、怎么划范围")
A("a-revision-cap", "两轮修改上限，第 3 轮按小时计费", "layer-closed",
  "每轮一次性汇总反馈；合同写死「两轮内免费调整，范围变更按 800 元/小时计」。无限修改是项目制亏损第一大来源。", DPROD, "二、修改次数上限")
A("a-negotiation-anchor", "锚在客户省了多少", "layer-closed",
  "算给对方听：「每天 1 人 3 小时，一个月 60 小时；这套做完 10 分钟。按 60 元/小时，一年省 4 万多」，再报 1.8 万。只给算式和事实，不承诺百分比。", DNEGO, "三、锚在客户省了多少")
A("a-risk-hedge", "风险对冲四动作", None,
  "任一客户占比 ≤40% 且保持 2 个在谈线索；每 5 条内容 1 条同步 B站/视频号；准备一页不依赖平台的落地页；被抄只投诉不骂战。", DRISK, "全文")
A("a-client-concentration", "客户收入占比表", "layer-closed",
  "一张表记每个客户月度收入，超 40% 立刻找新单。", DRISK, "五、这个账号意味着什么·1")

M("m-homepage-3s", "主页 3 秒识别", "layer-found",
  "让陌生人看主页 3 秒，说出「这人做什么的」。说不出就重做简介第 1/3 行。", DHOME, "一、主页包装·验收")
M("m-funnel-rates", "各段转化率（曝光→停留→私信）", None,
  "漏斗六段各自的转化率。当前全部未获取：无曝光数、无后台转化，只能算相对上周的变化。",
  DFUNNEL, "四、测法",
  status=SUPPORTED, note="曝光数与各段转化率均拿不到；行业基准也没有，只能比自己上周。")
M("m-quote-ratio", "私信问价比例", "layer-closed",
  "私信里问价的比例，是判断 IP 阶段的唯一指标：0 = 识别期，开始出现 = 信任期。粉丝可以买，问价不能。", DIP, "二、IP 生命周期四阶段")
M("m-gross-margin", "毛利率", "layer-closed",
  "毛利 = 报价 − 交付工时 × 时薪 − 外包。经验推断 50–60%，未验证；3 单后用真实工时校正。", DBIZMODEL, "四、成本结构",
  status=SUPPORTED, note="只有经验推断值，没有实测毛利。")
M("m-client-share", "单客户收入占比", "layer-closed",
  "任一客户月度收入占比，红线 40%。超过就说明单点依赖，现金流随时会断。", DRISK, "1. 单点依赖")

# ============================ 第三批（覆盖矩阵第二轮） ============================
# ---- 三个空缺：两个缺、一个主动判不适用 ----
M("gap-publish-frequency", "发布频次与最优间隔", "layer-seen",
  "一周几条、间隔几天最优。一周节奏给了「两周 3 条精品 + 1 条周测」的排期，但没有独立篇、没有数据支撑，覆盖矩阵记为「部分 / 空缺 1」。",
  DWEEK, "一、两类条目的配比",
  status=MENTIONED, note="有战术排期，没有最优频次结论；对标样本也不足。")
M("gap-capacity", "产能上限与外包", "layer-closed",
  "一周最多交付几个项目、哪些环节可以外包、外包后毛利还剩多少。经营 01 只有「单人年营收 30–60 万」的经验推断，没有工时与外包口径。",
  DBIZ, "一、接服务",
  status=MISSING, note="覆盖矩阵建议补的一篇；当前只有营收上限的经验推断。")
T("theory-community-na", "社群运营", "layer-found",
  "社群运营（拉群、日常维护、群内转化）。本项目一次性项目制、客户数 <50，主动判定不适用，不补文档。",
  "主动判定", DMR, "当前缺口",
  status="na", note="不适用：不是没写，是判断不该做。避免为了「补全」去维护一个没有复利的群。")

# ---- 传闻类：把「不能对外引用」直接画出来 ----
T("theory-rumor-coldstart", "冷启动五条传闻", "layer-seen",
  "养号、新号扶持期、一天多发会限流、删作品掉权重、说「微信」就被限流——五条都广泛流传、都找不到出处。真正的问题不是关键词，是导流行为。",
  "无出处（行业通行说法）", DCOLD, "三、无法确认的",
  status=UNVERIFIED, note="传闻：五条均无出处；冷启动只按「同题材、标签准」执行。")
T("theory-rumor-saima", "赛马机制（传闻）", None,
  "平台故意让几个新号互相竞争、只推赢的那个。平台不会特意让账号互斗，各号只是独立进入推荐。",
  "无出处（行业通行说法）", "methodology/L1-矩阵与投放.md", "一、矩阵与赛马",
  status=UNVERIFIED, note="传闻：矩阵号「赛马」是运营比喻，不是平台机制。")
T("theory-rumor-8s", "注意力 8 秒（传闻）", "layer-seen",
  "「人的注意力只有 8 秒」被广泛引用，找不到可靠出处。可确认的只有「短视频前 3 秒决定去留」这一定性判断。",
  "无出处", "methodology/L1-心理补充.md", "5. 观众心理",
  status=UNVERIFIED, note="传闻：不要拿 8 秒当设计依据。")
M("m-rumor-completion30", "完播率 30% 合格线（传闻）", "layer-seen",
  "「完播率过 30% 就算合格」在行业里广泛流传，平台没有公布过任何合格线，也无法验证样本口径。",
  "methodology/L1-完播口径.md", "二、不要用的口径",
  status=UNVERIFIED, note="传闻：不同时长、不同赛道不可比，只能跟自己比。")

# ---- 心理补充 ----
T("theory-asch", "从众（Asch）", "layer-trusted",
  "不确定时人用他人行为判断正确行为；公开的多数意见会压制个人判断（约 1/3 被试跟随明显错误的答案）。效应在跨文化重复中存在，但效应量随情境差异很大。",
  "Asch, 1951；Cialdini, 1984", "methodology/L1-心理补充.md", "2. 从众与社会认同")
T("theory-foot-in-door", "门槛效应", "layer-closed",
  "先答应小请求的人更容易答应后续大请求（自我形象一致性）。效应稳健但效应量中等，两次请求间隔不能太长。",
  "Freedman & Fraser, JPSP, 1966", "methodology/L1-心理补充.md", "3. 门槛效应")
T("theory-bystander", "旁观者效应", "layer-closed",
  "在场人越多，个体越不行动，责任被分散。后续元分析显示效应弱于原研究，危险情境更强，网络情境适用性有限。",
  "Darley & Latané, 1968；Fischer et al., 2011", "methodology/L1-心理补充.md", "4. 旁观者效应")
T("theory-peak-end", "峰值-终值规则", "layer-seen",
  "人对一段经历的评价取决于峰值与结尾，不是平均。原研究是疼痛/体验实验，外推到 30 秒视频属于类比，不是验证。",
  "Kahneman et al., 1993", "methodology/L1-心理补充.md", "5. 观众心理")
A("a-name-single-exit", "点名 + 单一出口 + 私信前 20 个互动者", "layer-closed",
  "泛问「你们怎么看」会触发旁观者效应；改成点名（「如果你也在做 XX，回我一句」）、只留一个动作、主动私信前 20 个互动者，把公共场合变成一对一。",
  "methodology/L1-心理补充.md", "4. 旁观者效应·动作")
A("a-peak-ending", "一条只设一个峰值，结尾给判断句", "layer-seen",
  "峰值放在反常那一刻；结尾必须是判断句，不能是「就这样」；不用平淡收尾音乐。",
  "methodology/L1-心理补充.md", "5. 观众心理·动作")

# ---- 矩阵与投放 ----
T("theory-dou-plus", "DOU+ / 千川机制", "layer-closed",
  "DOU+ 给单条买曝光、按曝光计费；千川按转化目标出价（oCPM）。功能与计费方式有官方文档，起投门槛、成本区间、涨粉成本全部未获取。",
  "巨量引擎文档【官方】；价格为【经验帖】或未获取", "methodology/L1-矩阵与投放.md", "二、DOU+ 与千川")
T("theory-republish", "判重与搬运边界", None,
  "平台有重复内容/搬运处罚条款，但相似度阈值不公开。可观测信号：同素材、同封面、同文案、批量发。同一素材多号发，重拍比重剪安全。",
  "《社区自律公约》【官方】+ 经验【经验帖】", "methodology/L1-矩阵与投放.md", "一、矩阵与赛马")
A("a-matrix-backup", "1 主号 + 1 备份号", "layer-found",
  "一个人只维护主号 + 备份号，不做 3 个以上；备份号发同题材不同案例，不发同一条内容；一机一号。",
  "methodology/L1-矩阵与投放.md", "一、几个号合适")

# ---- 完播口径 ----
T("theory-completion-baseline", "完播率可比口径", "layer-seen",
  "完播率只在「同账号、同时长、同类型」内可比。行业没有合格线，也不该用别人的数字当基准；正确做法是建自己的历史中位数。",
  "本项目方法（平台未公布口径）", "methodology/L1-完播口径.md", "全文",
  note="口径本身是推断：平台未公布完播率计算方式，只能确认「看的是完整播放比例」。")
A("a-own-baseline", "建自己的历史表", "layer-seen",
  "按「类型 × 时长」记 5 秒完播与完播率，取历史中位数，新条只跟自己的中位数比；连续 3 条低于中位数 30% 才判这条不行。",
  "methodology/L1-完播口径.md", "三、怎么用")

# ============================ 边 ============================
# 驱动：理论 -> 动作
DRIVES = [
    ("theory-recall-ranking", "a-same-topic-first5", "题材不清则召回阶段没你；三个词连续 5 条不换"),
    ("theory-explore-exploit", "a-one-variable", "每条只改一个变量，系统和你才分辨得出哪版有效"),
    ("theory-cold-start", "a-same-topic-first5", "初始人群依赖内容标签"),
    ("theory-cold-start", "a-two-day-cadence", "同质内容高频发布可能被判低质/重复"),
    ("theory-curiosity-gap", "a-anomaly-first3s", "开头 = 一个具体事实 + 一个反常"),
    ("theory-curiosity-gap", "a-one-gap", "开两个缺口 = 一个都记不住"),
    ("theory-high-arousal", "a-anomaly-first3s", "只用「敬畏/意外」，落点是它有自己的边界"),
    ("theory-rec-flow", "a-two-titles", "推荐版标题写反常"),
    ("theory-search-flow", "a-two-titles", "搜索版标题写问题词，晚 3–7 天发"),
    ("theory-free-traffic-three", "a-share-to-peers", "社交一腿靠同行群，不靠抖音"),
    ("theory-peripheral-route", "a-peripheral-first3s", "前 3 秒看信源与气氛，中段再上论据"),
    ("theory-positioning", "a-bio-identity", "占一个空位，不抢「AI 博主」"),
    ("theory-positioning", "a-bio-three-lines", "身份、事实、入口三行写死，30 天不动"),
    ("theory-usp", "a-number-each", "每条结尾一句可验证的话"),
    ("theory-cbbe", "a-assoc-words", "单一维度反复强化才形成强联想"),
    ("theory-cbbe", "a-bio-three-lines", "简介里只放这三个词"),
    ("theory-availability", "a-assoc-words", "反复同一场景，让「想起你」先于「比较你」"),
    ("theory-slogan", "a-main-slogan", "短、可复读、指向一个利益"),
    ("theory-mere-exposure", "a-fixed-intro", "形式重复，内容不重复"),
    ("theory-mere-exposure", "a-two-day-cadence", "间隔太密会提前进入倒 U 的下降段"),
    ("theory-meme", "a-fixed-phrase", "固定句式是唯一能带来 UGC 的结构"),
    ("theory-parasocial", "a-face-to-camera", "对镜头说话 = 打破第四面墙"),
    ("theory-parasocial", "a-admit-failure", "私人细节让关系从内容转向人"),
    ("theory-parasocial", "a-fixed-intro", "固定开场让「又是他」发生在 1 秒内"),
    ("theory-narrative-transport", "a-story-first", "故事在前、道理在后，降低反驳"),
    ("theory-narrative-transport", "a-first-person-now", "第一人称现在时，传输更强"),
    ("theory-central-route", "a-number-each", "B 端高卷入，看论据"),
    ("theory-central-route", "a-refutable-claim", "可反驳的判断才是论据"),
    ("theory-social-proof", "a-real-review", "真实评价是最强证据"),
    ("theory-social-proof", "a-review-to-pin", "评价进置顶，成为后来者的证据"),
    ("theory-prestige-status", "a-not-expert-intro", "展示我能干，不宣告我厉害"),
    ("theory-prestige-status", "a-no-peer-bashing", "贬低是支配型动作"),
    ("theory-carnegie", "a-client-situation", "谈对方的利益，不谈自己的成就"),
    ("theory-carnegie", "a-reply-restate", "让对方觉得被听见"),
    ("theory-attention-commodity", "a-dm-only-asset", "把一次性注意力转成可联系的人"),
    ("theory-attention-commodity", "a-own-contact-list", "客户名单必须自己攥"),
    ("theory-attention-commodity", "a-no-irrelevant-ads", "卖错一次，人设变成恰饭号"),
    ("theory-two-step-flow", "a-share-to-peers", "B 端信息经同行中转"),
    ("theory-private-domain", "a-minimal-private", "公域获客、私域承接，不做社群运营"),
    ("theory-anchoring", "a-anchor-quote", "先出现的数字影响后续判断"),
    ("theory-anchoring", "a-quote-onepager", "把范围与付款节点写死，减少来回议价"),
    ("theory-loss-frame", "a-loss-frame", "同一事实换说法，选择会变"),
    ("theory-dual-system", "a-no-number-opening", "开头不激活慢系统"),
    ("theory-fcb", "a-info-emotion-73", "高卷入理性，信息为主"),
    ("theory-social-exchange", "a-dm-first-scene", "把互动成本降到最低"),
    ("theory-social-exchange", "a-binary-comment", "二选一比开放题成本低"),
    ("theory-social-exchange", "a-one-cta", "同时要四个动作等于成本翻四倍"),
    ("theory-social-exchange", "a-promise-reply", "把回报变得确定"),
    ("theory-reciprocal-altruism", "a-first3-no-cta", "先给三次再提要求"),
    ("theory-reciprocal-altruism", "a-low-cost-gift", "给完还留一个动作"),
    ("theory-reciprocal-altruism", "a-judgment-only", "步骤留下，才有私信的理由"),
    ("theory-performance-ad", "a-no-ads-first15", "没有转化回传，oCPM 学不到人群"),
    ("theory-interest-ecommerce", "a-no-cart", "高客单 B 端不在小黄车成交"),
    ("theory-north-star", "a-dm-log", "每周记有效私信数"),
    ("theory-nps-referral", "a-ask-review", "客户数 <50，改要一句可公开评价"),
    ("theory-nps-referral", "a-no-referral-gift", "K 因子无统计意义，返佣会伤关系"),
    ("theory-rfm", "a-dm-log", "替代方案：手工私信表，不上系统"),
    ("theory-ab-test", "a-no-ab", "几百播放无统计功效，延后"),
    ("model-public-boundary", "a-judgment-only", "公开内容只交付判断"),
    ("model-public-boundary", "a-dm-only-asset", "步骤留作私域交换物"),
    ("model-compliance", "a-compliance-4q", "发布前四问"),
    ("model-compliance", "a-blur-client", "客户信息比搬运更危险"),
    ("model-compliance", "a-no-effect-promise", "效果承诺属虚假宣传"),
    ("model-monetization-forms", "a-service-only", "前 6 个月只做接服务"),
    ("model-monetization-forms", "a-quote-onepager", "报价口径统一写进一页纸"),
    ("model-monetization-forms", "a-no-equity", "不接股权换服务"),
    ("model-six-layers", "a-same-topic-first5", "第 1 层不成立，后面全黑"),
    ("model-six-layers", "a-bio-three-lines", "第 4 层断了，信任停在关注"),
    ("model-review-8col", "a-review-8col", "8 列就够，列多了变成看数据"),
    ("model-review-8col", "a-review-order", "判定顺序固定，先开头后观点"),
    ("model-review-8col", "a-topic-twice", "同一选题最多试两次"),
    # 第三批：补篇带来的驱动关系
    ("theory-homepage-packaging", "a-avatar-set", "主页五件套，验收标准是 3 秒能说出你是谁"),
    ("theory-homepage-packaging", "a-bio-three-lines", "三行写死：身份 / 做过什么 / 入口"),
    ("theory-homepage-packaging", "a-pin-case", "置顶三条：案例、判断力、服务说明"),
    ("theory-homepage-packaging", "a-no-contact-public", "五件套里不包含联系方式"),
    ("theory-diversion-boundary", "a-no-contact-public", "公开区只引发对话，联系方式进私信"),
    ("theory-diversion-boundary", "a-ladder", "四个入口各自能做什么，按阶梯走"),
    ("theory-funnel-six", "a-weekly-focus", "每周只盯损耗最大的一段"),
    ("theory-funnel-six", "a-reply-2h", "第 5 段的动作最便宜，先做"),
    ("theory-platform-structure", "a-platform-priority", "抖音要量、视频号要人"),
    ("theory-platform-structure", "a-xhs-graphic", "小红书靠搜索，标题即搜索词"),
    ("theory-goffman", "a-face-to-camera", "前台只演判断与现场，不演能力"),
    ("theory-ip-lifecycle", "a-main-slogan", "识别期只做固定句式与固定题材"),
    ("theory-ip-lifecycle", "a-same-topic-first5", "0–1 万粉阶段不做多题材"),
    ("theory-ip-lifecycle", "a-same-agent-limit4", "纵深也要有边界，超过 4 条换案例"),
    ("theory-assetization", "a-asset-four", "每条至少沉淀四样之一"),
    ("theory-crisis-pr", "a-crisis-four-step", "四步处置，三条禁忌"),
    ("theory-stp", "a-positioning-statement", "定位陈述写进简介第一行"),
    ("theory-stp", "a-boss-three-questions", "老板只问三件事：多少钱、像不像、谁在用"),
    ("theory-stp", "a-payment-willingness-3q", "先判断他已经在为什么付钱"),
    ("theory-competitive-map", "a-deep-onsite-only", "只占「深 + 到场」一格"),
    ("theory-competitive-map", "a-positioning-statement", "空位描述就是定位语"),
    ("theory-three-choices", "a-platform-priority", "三个选择互相耦合，先定平台"),
    ("theory-pricing-methods", "a-cost-first-pricing", "先算底线，再报价值价"),
    ("theory-pricing-methods", "a-log-hours", "没有工时就没有成本底线"),
    ("theory-negotiation", "a-scope-not-price", "降范围不降价"),
    ("theory-negotiation", "a-refuse-five", "五条拒单标准"),
    ("theory-negotiation", "a-negotiation-anchor", "锚在客户省了多少"),
    ("theory-productization", "a-scope-io", "按输入-输出划范围"),
    ("theory-productization", "a-revision-cap", "两轮修改上限写进合同"),
    ("theory-risk-hedge", "a-risk-hedge", "四类风险各自对冲"),
    ("theory-risk-hedge", "a-client-concentration", "单客户占比 ≤40%"),
    ("theory-cross-platform-rewrite", "a-xhs-graphic", "同一判断句改成图文，占搜索位"),
    ("theory-dou-plus", "a-no-ads-first15", "没有转化回传，投了只是买播放"),
    ("theory-republish", "a-matrix-backup", "重拍比重剪安全；备份号不发同一条"),
    ("theory-completion-baseline", "a-own-baseline", "只跟自己同类同时长的中位数比"),
    ("theory-asch", "a-real-review", "公开的多数意见压制个人判断，但要真实"),
    ("theory-asch", "a-pinned-self-comment", "先自己回一条有信息量的，定调"),
    ("theory-foot-in-door", "a-ladder", "小请求先行，不跳级"),
    ("theory-bystander", "a-name-single-exit", "点名 + 单一出口，责任不分散"),
    ("theory-peak-end", "a-peak-ending", "峰值 + 判断句结尾"),
    ("theory-cold-start", "a-material-audit-15", "少于 15 个反常就不开工"),
    ("theory-recall-ranking", "a-topic-tags", "话题参与召回，但要垂类清楚"),
    ("model-compliance", "a-publish-sop", "发布前四问写在 SOP 第一步"),
    ("theory-explore-exploit", "a-weekly-rhythm", "每周一条测试条，只改一个变量"),
    ("model-review-8col", "a-weekly-review", "周一 30 分钟五步复盘"),
    ("model-review-8col", "a-trigger-adjust", "按阈值触发，不按心情"),
    ("model-review-8col", "a-fixed-slot", "时段固定，复盘才排得掉时间因素"),
    ("theory-social-exchange", "a-comment-templates", "降低回复成本，提高回报确定性"),
    ("theory-carnegie", "a-comment-templates", "让对方保住面子"),
    ("theory-parasocial", "a-reply-2h", "回复是关系的维护动作"),
    ("theory-anchoring", "a-negotiation-anchor", "先给一个可核对的大数字"),
    ("model-monetization-forms", "a-takeorder-sop", "接单八步固定下来"),
    ("model-monetization-forms", "a-cashflow-rules", "预付 50% 才开工"),
    ("theory-central-route", "a-quote-two-materials", "给论据：报价单 + 最像的案例"),
    ("theory-interest-recommend", "a-same-topic-first5", "标签决定初始人群"),
    ("theory-traffic-pool", "a-same-topic-first5", "层级口径不可信，只按「标签准」执行"),
    ("theory-aida", "a-story-first", "只借「四件事都要有」，不借顺序"),
    ("theory-aarrr", "a-weekly-focus", "只保留获取与收入两段"),
    ("theory-k-factor", "a-no-referral-gift", "客户数 <50，K 因子不成立"),
    ("model-sampling-bounds", "a-weekly-review", "四问答不上来就只写「样本内观察」"),
    ("model-direction-switch", "a-trigger-adjust", "四个判据触发切换，不按心情"),
    ("model-anomaly-types", "a-material-audit-15", "六型各存 2–3 个真实案例"),
    ("theory-three-choices", "a-deep-onsite-only", "选了「深 + 到场」就不能接不到场的活"),
    ("theory-rumor-coldstart", "a-same-topic-first5", "传闻不执行，只做同题材标签"),
    ("theory-rumor-saima", "a-matrix-backup", "矩阵不是赛马，备份号只防封"),
    ("theory-rumor-8s", "a-anomaly-first3s", "不按 8 秒设计，只按前 3 秒定性"),
]

# 度量：动作 -> 指标
MEASURES = [
    ("a-same-topic-first5", "m-plays", "标签准 → 分发规模"),
    ("a-same-topic-first5", "m-same-audience", "只追同类人看完，不追进池"),
    ("a-anomaly-first3s", "m-5s-completion", "钩子成立与否"),
    ("a-anomaly-first3s", "m-2s-bounce", "第一帧/第一句是否成立"),
    ("a-anomaly-first3s", "m-3s-retention", "算法推不推的第一判据"),
    ("a-one-gap", "m-completion", "缺口不合上，中段就掉"),
    ("a-cut-rhythm", "m-completion", "画面静止是掉完播的主要原因"),
    ("a-cut-rhythm", "m-avg-watch", "掉点位置对应切点"),
    ("a-speech-pace", "m-5s-completion", "语速与断句影响前 5 秒"),
    ("a-audio-floor", "m-avg-watch", "糊音/看不清会让人提前划走"),
    ("a-one-variable", "m-completion", "变量可控才谈得上归因"),
    ("a-peripheral-first3s", "m-5s-completion", "前 3 秒建立可信，人才留着"),
    ("a-no-number-opening", "m-2s-bounce", "数字堆叠抬高跳出"),
    ("a-bio-identity", "m-profile-visits", "简介第一行决定要不要点进主页"),
    ("a-main-slogan", "m-brand-search", "口号重复多了才会有人搜"),
    ("a-assoc-words", "m-profile-visits", "联想集中 → 主页访问上升"),
    ("a-fixed-phrase", "m-comments", "句式可套用 → 评论接话"),
    ("a-fixed-phrase", "m-identity-recall", "有人用你的句式接话"),
    ("a-fixed-intro", "m-profile-visits", "识别成本降低 → 认人"),
    ("a-two-day-cadence", "m-completion", "频率过高会进曝光下降段"),
    ("a-number-each", "m-demand-signal", "论据足够才有人问方法/问价"),
    ("a-refutable-claim", "m-comments", "有观点才有评论"),
    ("a-admit-failure", "m-demand-signal", "可信度来自不完美"),
    ("a-face-to-camera", "m-profile-visits", "露脸才有人点主页认人"),
    ("a-reply-restate", "m-comments", "被听见 → 继续互动"),
    ("a-judgment-only", "m-demand-signal", "判断招来「我也遇到过」，步骤招来「求源码」"),
    ("a-judgment-only", "m-favorites", "信息型内容收藏 > 点赞"),
    ("a-real-review", "m-effective-dm", "真实评价降低询价门槛"),
    ("a-not-expert-intro", "m-profile-visits", "声望型展示 → 愿意点进来看你是谁"),
    ("a-story-first", "m-completion", "故事撑住中段"),
    ("a-first-person-now", "m-demand-signal", "传输带来的是对你的记忆"),
    ("a-bio-three-lines", "m-profile-to-dm", "入口写清楚 → 访问转私信"),
    ("a-pin-case", "m-effective-dm", "案例替代自我介绍"),
    ("a-two-titles", "m-search-dm", "搜索版标题命中问题词"),
    ("a-share-to-peers", "m-effective-dm", "同行转群带来的私信更意向明确"),
    ("a-dm-only-asset", "m-effective-dm", "留了私信理由"),
    ("a-dm-only-asset", "m-contact-list", "一次性注意力转成可联系人"),
    ("a-own-contact-list", "m-contact-list", "名单条数"),
    ("a-minimal-private", "m-dm-to-wechat", "承接结构越简单，加微率越高"),
    ("a-anchor-quote", "m-close-rate", "锚点让人在快系统里选"),
    ("a-anchor-quote", "m-order-value", "锚点决定客单价落点"),
    ("a-loss-frame", "m-2s-bounce", "损失框架降低跳出"),
    ("a-info-emotion-73", "m-demand-signal", "信息占比够，才有人问价"),
    ("a-dm-first-scene", "m-dm-to-wechat", "第一轮门槛低，愿意继续聊"),
    ("a-first3-no-cta", "m-effective-dm", "先给三次，私信质量更高"),
    ("a-low-cost-gift", "m-effective-dm", "给完留动作"),
    ("a-one-cta", "m-comments", "只提一个动作，执行率才高"),
    ("a-one-cta", "m-effective-dm", "入口唯一，私信不漏"),
    ("a-binary-comment", "m-comments", "二选一降低评论成本"),
    ("a-binary-comment", "m-demand-signal", "选择题能筛出真实场景"),
    ("a-promise-reply", "m-comments", "承诺有回音 → 继续评论"),
    ("a-no-ads-first15", "m-effective-dm", "自然流量先跑出问价样本"),
    ("a-quote-onepager", "m-close-rate", "范围写死，减少议价流失"),
    ("a-service-only", "m-close-rate", "只做能交付的形态"),
    ("a-dm-log", "m-price-dm", "每周记问价条数"),
    ("a-dm-log", "m-effective-dm", "北极星可手工统计"),
    ("a-ask-review", "m-public-reviews", "交付当天索要"),
    ("a-review-to-pin", "m-effective-dm", "证据前置，询价更直接"),
    ("a-quarterly-touch", "m-referrals", "不问单的触达带来主动推荐"),
    ("a-compliance-4q", "m-5s-completion", "违规内容会被限流，直接归零"),
    ("a-blur-client", "m-completion", "客户信息暴露会引发举报/下架"),
    ("a-review-8col", "m-completion", "复盘表的核心列"),
    ("a-review-8col", "m-5s-completion", "复盘表的核心列"),
    ("a-review-8col", "m-comments", "复盘表的核心列"),
    ("a-review-8col", "m-effective-dm", "唯一的商业指标单列"),
    ("a-review-order", "m-profile-visits", "第三顺位才看人设"),
    ("a-topic-twice", "m-plays", "两次不成即弃，避免无效重拍"),
    ("a-avatar-set", "m-profile-visits", "头像可辨 → 点进主页"),
    ("a-bio-three-lines", "m-homepage-3s", "三行决定 3 秒识别"),
    ("a-no-contact-public", "m-plays", "公开区写联系方式会触发限流"),
    ("a-weekly-focus", "m-funnel-rates", "每周只测一段的转化率"),
    ("a-xhs-graphic", "m-search-dm", "图文占搜索位，带来搜索私信"),
    ("a-asset-four", "m-demand-signal", "资产里有客户问题，才会有人接话"),
    ("a-positioning-statement", "m-identity-recall", "定位语被复述"),
    ("a-boss-three-questions", "m-demand-signal", "回答了老板三问，评论才会具体"),
    ("a-payment-willingness-3q", "m-close-rate", "支付意愿判断准，成交率上升"),
    ("a-deep-onsite-only", "m-close-rate", "只接能交付的活"),
    ("a-cashflow-rules", "m-payment-cycle", "预付 + 尾款 7 天"),
    ("a-cost-first-pricing", "m-gross-margin", "成本底线决定毛利下限"),
    ("a-log-hours", "m-gross-margin", "真实工时校正毛利"),
    ("a-weekly-rhythm", "m-completion", "精品条撑完播，测试条找开头"),
    ("a-same-agent-limit4", "m-completion", "超过 4 条开始审美疲劳"),
    ("a-comment-templates", "m-comments", "回复质量影响继续评论"),
    ("a-pinned-self-comment", "m-comments", "置顶自评定调"),
    ("a-ladder", "m-effective-dm", "不跳级，私信质量更高"),
    ("a-scope-not-price", "m-close-rate", "不降价保住价值锚"),
    ("a-refuse-five", "m-close-rate", "拒掉不该接的，成交质量上升"),
    ("a-material-audit-15", "m-completion", "素材够，前 10 条不断更"),
    ("a-publish-sop", "m-5s-completion", "标题/封面/话题决定前 5 秒"),
    ("a-topic-tags", "m-plays", "垂类话题帮助召回"),
    ("a-reply-2h", "m-comments", "2 小时内回复率 100%"),
    ("a-weekly-review", "m-completion", "每周只改一个变量"),
    ("a-trigger-adjust", "m-effective-dm", "阈值触发投流与停更"),
    ("a-takeorder-sop", "m-close-rate", "首响与报价节奏固定"),
    ("a-quote-two-materials", "m-close-rate", "两样材料降低决策成本"),
    ("a-scope-io", "m-close-rate", "范围写死，议价空间小"),
    ("a-revision-cap", "m-gross-margin", "无限修改是亏损第一来源"),
    ("a-negotiation-anchor", "m-order-value", "锚定客单价落点"),
    ("a-risk-hedge", "m-contact-list", "落地页与联系人表，平台之外也有名单"),
    ("a-client-concentration", "m-client-share", "单客户占比表"),
    ("a-dm-log", "m-quote-ratio", "问价比例可手工统计"),
    ("a-own-baseline", "m-3s-retention", "跟自己历史中位数比"),
    ("a-peak-ending", "m-completion", "结尾给判断句，减少中途划走"),
    ("a-name-single-exit", "m-comments", "点名比泛问更容易得到回应"),
    ("a-matrix-backup", "m-plays", "备份号不同案例，避免判重"),
]

# 引用：文档之间的显式引用（节点承载）
REFERENCES = [
    ("theory-reciprocal-altruism", "model-public-boundary", "互惠利他原文：这正是内容模型里「教程是私域转化物」的理论依据"),
    ("model-monetization-forms", "model-public-boundary", "经营篇原文：呼应内容模型——教程是私域转化物"),
    ("model-anomaly-types", "model-public-boundary", "选题库填表要求：判断里不能出现操作步骤"),
    ("model-six-layers", "model-compliance", "总纲把违规红线列为横切约束：不属于任何一层，但每层都受它限制"),
    ("model-six-layers", "model-review-8col", "总纲把复盘方法列为横切的测量工具"),
    ("model-review-8col", "theory-ab-test", "复盘方法原文：播放几百时差异全在噪声里，见增长篇"),
    ("theory-positioning", "a-positioning-statement", "定位把「能把 AI 讲成人话」当作身份核心，落成一句话陈述"),
    ("model-public-boundary", "model-monetization-forms", "公开内容边界的关联节指向变现判断"),
    ("theory-homepage-packaging", "theory-diversion-boundary", "主页包装篇把联系方式单独拆成转化路径一节"),
    ("theory-funnel-six", "model-six-layers", "漏斗六段与六层主干一一对应，见总纲"),
    ("theory-platform-structure", "theory-cross-platform-rewrite", "七大平台对照的结论直接推到跨平台改写"),
    ("model-compliance", "theory-republish", "判重与搬运边界同属社区公约条款"),
    ("model-six-layers", "gap-publish-frequency", "总纲第 1 层要求两天一更，但最优频次无独立篇"),
]

# 依赖：层与层（source = 前层，target = 后层；语义为「后层依赖前层」）
DEPENDS = [
    ("layer-seen", "layer-remembered", "5 秒完播成立 + 固定识别元素，否则没人看到结尾"),
    ("layer-remembered", "layer-trusted", "记住之后还愿意看第二条，否则信任从零开始"),
    ("layer-trusted", "layer-found", "有信任 + 有入口，否则信任停在「关注」"),
    ("layer-found", "layer-closed", "找到的是人 + 有案例，否则主页空，掉回零"),
    ("layer-closed", "layer-referred", "交付完成 + 主动索要评价，否则无事实可转述"),
]
