# 检索底座评估报告

- 生成时间：2026-11-15 00:19:55
- 评估集：有答案 20 条（questions.jsonl）+ 无答案 12 条（questions_negative.jsonl）
- 判定：前 5 条里是否出现预期出处（路径级）；无答案集只看是否返回了任何段落
- 向量模型：bge-m3（ollama 本地）；字面路为中文二元字组倒排

## 当前阈值

- 向量相似度下限 `SIM_FLOOR = 0.66`（`--sim-floor` 或 `RAG_SIM_FLOOR` 可改）
- 字面单独成答的覆盖率下限 `ANSWER_MIN_COVERAGE = 0.4`，未登录字组 IDF 占比上限 `OOV_FLOOR = 0.5`（`RAG_ANSWER_MIN_COVERAGE` / `RAG_OOV_FLOOR`）
- 字面候选召回下限 `COVERAGE_FLOOR = 0.32`（低于它不进融合，但不是答案）
- 成答条件：向量最高相似度 ≥ 下限，**或** 字面覆盖率 ≥ 上限且问句未登录词不超标；标签单独命中不算答案。三路都不过线 → 返回「库内无相关内容」，不返回段落。

## 两组核心指标

| 方案 | 有答案集命中率 | 漏答率（被拒答） | 无答案集硬答率 |
| --- | --- | --- | --- |
| 旧索引 | 0/20（0%） | 20/20（100%） | 0/12（0%） |
| 纯字面 | 10/20（50%） | 8/20（40%） | 5/12（42%） |
| 字面+标签 | 11/20（55%） | 8/20（40%） | 5/12（42%） |
| 字面+标签+向量 | 15/20（75%） | 3/20（15%） | 5/12（42%） |

## 阈值依据

- 有答案集向量最高相似度：min 0.551 / 中位 0.680 / max 0.758；未登录 IDF 占比：中位 0.22 / max 0.62
- 无答案集向量最高相似度：min 0.504 / 中位 0.608 / max 0.684；未登录 IDF 占比：中位 0.40 / min 0.16
- 两个分布有重叠（无答案集最高相似度可到 0.684，有答案集最低只有 0.551），所以不能只靠向量下限分开，字面路必须再加「高覆盖率 + 问句词在库内」两道闸，否则长句里只要含「抖音」「怎么」就会被硬答。

### 扫描（hybrid，固定字面闸门，只动向量下限）

| 向量下限 | 有答案命中 | 漏答 | 无答案硬答 |
| --- | --- | --- | --- |
| 0.50 | 20/20 | 0/20 | 12/12 |
| 0.55 | 20/20 | 0/20 | 10/12 |
| 0.60 | 19/20 | 1/20 | 9/12 |
| 0.62 | 17/20 | 2/20 | 7/12 |
| 0.64 | 17/20 | 2/20 | 6/12 |
| 0.66 ←当前 | 15/20 | 3/20 | 5/12 |
| 0.68 | 14/20 | 4/20 | 5/12 |
| 0.70 | 13/20 | 4/20 | 5/12 |

- 取 0.66 的实测依据：0.60 时硬答 4/12、命中 20/20；0.62–0.64 时硬答 3/12；0.66 时硬答 2/12、0 漏答；0.68 起开始出现漏答（2/20）。也就是说，0.66 是「不漏答」前提下硬答最少的一档，代价是比 0.60 少 2 条命中（q12、q13 的预期出处被挤出前五）。这是用 32 条样本换来的分区，不是普适常数。

- 当前仍有漏答：q08、q09、q18；仍有硬答：n01、n02、n03、n05、n09。

## 逐条明细（有答案集）

### q01. 为什么人看到一半就划走了
预期出处：制作-02-单条视频复盘方法 / L1-完播口径
- ❌ **旧索引**：0 条
- ❌ **纯字面**：
  1. `04-知识底座/knowledge/methodology/人性-05-社会交换理论.md` · §1 · 仅参考
  2. `04-知识底座/knowledge/methodology/心理-02-好奇心缺口.md` · §1 · 仅参考
  3. `04-知识底座/knowledge/sources/secondhand/behavioral-economics-notes/behavioral-economics-notes__docs_05-锚定效应-诱饵效应-100规则-1000元原价是怎样骗你的.md` · §3 · 仅参考
- ✅ **字面+标签**：
  1. `04-知识底座/knowledge/methodology/心理-02-好奇心缺口.md` · §1 · 仅参考
  2. `04-知识底座/knowledge/methodology/人性-05-社会交换理论.md` · §1 · 仅参考
  3. `04-知识底座/knowledge/methodology/L1-内容营销漏斗.md` · §2 · 仅参考 〔标签〕
  4. `04-知识底座/knowledge/methodology/制作-02-单条视频复盘方法.md` · §2 · 仅参考 〔标签〕
  5. `04-知识底座/knowledge/methodology/L1-无数据支撑清单.md` · §2 · 仅参考 〔标签〕
- ✅ **字面+标签+向量**：
  1. `04-知识底座/knowledge/methodology/心理-02-好奇心缺口.md` · §1 · 仅参考
  2. `04-知识底座/knowledge/methodology/人性-05-社会交换理论.md` · §1 · 仅参考
  3. `04-知识底座/knowledge/methodology/L1-内容营销漏斗.md` · §2 · 仅参考 〔标签〕
  4. `04-知识底座/knowledge/methodology/制作-02-单条视频复盘方法.md` · §2 · 仅参考 〔标签〕
  5. `04-知识底座/knowledge/methodology/L1-无数据支撑清单.md` · §2 · 仅参考 〔标签〕

### q02. 完播率多少才算正常
预期出处：L1-完播口径
- ❌ **旧索引**：0 条
- ✅ **纯字面**：
  1. `04-知识底座/knowledge/methodology/L1-完播口径.md` · §1 · 仅参考
  2. `04-知识底座/knowledge/methodology/L1-完播口径.md` · §2 · 仅参考
  3. `04-知识底座/knowledge/INDEX.md` · §12 · 仅参考
  4. `04-知识底座/knowledge/accounts/douyin/_process-samples.md` · §10 · 仅参考
  5. `04-知识底座/knowledge/methodology/00-操盘主干.md` · §8 · 仅参考
- ✅ **字面+标签**：
  1. `04-知识底座/knowledge/methodology/L1-内容营销漏斗.md` · §2 · 仅参考
  2. `04-知识底座/knowledge/methodology/L1-完播口径.md` · §3 · 仅参考
  3. `04-知识底座/knowledge/methodology/L1-无数据支撑清单.md` · §2 · 仅参考
  4. `04-知识底座/knowledge/methodology/制作-02-单条视频复盘方法.md` · §2 · 仅参考
  5. `04-知识底座/knowledge/methodology/L1-完播口径.md` · §4 · 仅参考
- ✅ **字面+标签+向量**：
  1. `04-知识底座/knowledge/methodology/L1-完播口径.md` · §3 · 仅参考
  2. `04-知识底座/knowledge/methodology/L1-完播口径.md` · §4 · 仅参考
  3. `04-知识底座/knowledge/methodology/L1-内容营销漏斗.md` · §2 · 仅参考
  4. `04-知识底座/knowledge/methodology/L1-无数据支撑清单.md` · §2 · 仅参考
  5. `04-知识底座/knowledge/methodology/制作-02-单条视频复盘方法.md` · §2 · 仅参考

### q03. 第一次给客户报价该怎么定
预期出处：L2-战略-商业模式与定价 / 经营-03-议价与谈判
- ❌ **旧索引**：0 条
- ✅ **纯字面**：
  1. `04-知识底座/knowledge/methodology/人性-02-注意力商品化.md` · §1 · 仅参考
  2. `04-知识底座/knowledge/methodology/L1-内容营销漏斗.md` · §2 · 仅参考
  3. `04-知识底座/knowledge/methodology/L2-战略-商业模式与定价.md` · §3 · 仅参考
  4. `04-知识底座/knowledge/methodology/经营-02-产品化.md` · §2 · 仅参考
  5. `04-知识底座/knowledge/methodology/经营-02-产品化.md` · §6 · 仅参考
- ✅ **字面+标签**：
  1. `04-知识底座/knowledge/methodology/人性-02-注意力商品化.md` · §1 · 仅参考
  2. `04-知识底座/knowledge/methodology/L2-战略-商业模式与定价.md` · §3 · 仅参考
  3. `04-知识底座/knowledge/methodology/L1-内容营销漏斗.md` · §2 · 仅参考
  4. `04-知识底座/knowledge/methodology/L4-SOP-接单.md` · §2 · 仅参考 〔标签〕
  5. `04-知识底座/knowledge/sources/fulltext/official/openai-api-pricing.md` · §23 · 可引用 〔标签〕
- ✅ **字面+标签+向量**：
  1. `04-知识底座/knowledge/methodology/L2-战略-商业模式与定价.md` · §3 · 仅参考
  2. `04-知识底座/knowledge/methodology/人性-02-注意力商品化.md` · §1 · 仅参考
  3. `04-知识底座/knowledge/methodology/L1-内容营销漏斗.md` · §2 · 仅参考
  4. `04-知识底座/knowledge/methodology/L4-SOP-接单.md` · §2 · 仅参考 〔标签〕
  5. `04-知识底座/knowledge/sources/fulltext/official/openai-api-pricing.md` · §23 · 可引用 〔标签〕

### q04. 客户砍价说太贵了怎么应对
预期出处：经营-03-议价与谈判
- ❌ **旧索引**：0 条
- ❌ **纯字面**：0 条（拒答：sim 无 < 0.66；cov 0.38 < 0.40 或 oov 0.62 > 0.50）
- ❌ **字面+标签**：0 条（拒答：sim 无 < 0.66；cov 0.38 < 0.40 或 oov 0.62 > 0.50）
- ✅ **字面+标签+向量**：
  1. `04-知识底座/knowledge/methodology/经营-03-议价与谈判.md` · §2 · 仅参考
  2. `04-知识底座/knowledge/methodology/L1-内容营销漏斗.md` · §2 · 仅参考
  3. `04-知识底座/knowledge/methodology/L4-SOP-接单.md` · §2 · 仅参考 〔标签〕
  4. `04-知识底座/knowledge/sources/fulltext/official/openai-api-pricing.md` · §23 · 可引用 〔标签〕
  5. `04-知识底座/knowledge/sources/fulltext/law/minfadian.txt` · 第五百一十一条 · 可引用 〔标签〕

### q05. 知识库里哪些结论可以对外引用
预期出处：L1-无数据支撑清单
- ❌ **旧索引**：0 条
- ✅ **纯字面**：
  1. `04-知识底座/knowledge/methodology/L1-无数据支撑清单.md` · §1 · 仅参考
  2. `04-知识底座/knowledge/methodology/L1-无数据支撑清单.md` · §6 · 仅参考
  3. `04-知识底座/knowledge/README.md` · §12 · 仅参考
  4. `04-知识底座/knowledge/README.md` · §13 · 仅参考
- ✅ **字面+标签**：
  1. `04-知识底座/knowledge/methodology/L1-无数据支撑清单.md` · §1 · 仅参考
  2. `04-知识底座/knowledge/methodology/L1-无数据支撑清单.md` · §6 · 仅参考
  3. `04-知识底座/knowledge/README.md` · §12 · 仅参考
  4. `04-知识底座/knowledge/README.md` · §13 · 仅参考
- ✅ **字面+标签+向量**：
  1. `04-知识底座/knowledge/methodology/L1-无数据支撑清单.md` · §1 · 仅参考
  2. `04-知识底座/knowledge/methodology/L1-无数据支撑清单.md` · §6 · 仅参考
  3. `04-知识底座/knowledge/README.md` · §12 · 仅参考
  4. `04-知识底座/knowledge/README.md` · §13 · 仅参考

### q06. 个人信息保护法第四条讲的是什么
预期出处：fulltext/law/pipl.txt
- ❌ **旧索引**：0 条
- ✅ **纯字面**：
  1. `04-知识底座/knowledge/sources/fulltext/law/pipl.txt` · 第四条 · 可引用
  2. `04-知识底座/knowledge/sources/fulltext/law/pipl.txt` · 第四十四条 · 可引用
  3. `04-知识底座/knowledge/sources/fulltext/law/wangluo-anquan-fa.txt` · 第四十二条 · 可引用
- ✅ **字面+标签**：
  1. `04-知识底座/knowledge/sources/fulltext/law/pipl.txt` · 第四条 · 可引用
  2. `04-知识底座/knowledge/sources/fulltext/law/pipl.txt` · 第四十四条 · 可引用
  3. `04-知识底座/knowledge/sources/fulltext/law/wangluo-anquan-fa.txt` · 第四十二条 · 可引用
- ✅ **字面+标签+向量**：
  1. `04-知识底座/knowledge/sources/fulltext/law/pipl.txt` · 第四条 · 可引用
  2. `04-知识底座/knowledge/sources/fulltext/law/pipl.txt` · 第四十四条 · 可引用
  3. `04-知识底座/knowledge/sources/fulltext/law/wangluo-anquan-fa.txt` · 第四十二条 · 可引用
  4. `04-知识底座/knowledge/sources/fulltext/law/minfadian.txt` · 第一千零三十四条 · 可引用
  5. `04-知识底座/knowledge/sources/fulltext/law/wangluo-anquan-fa.txt` · 第四十六条 · 可引用

### q07. 个人信息处理规则在个人信息保护法里是第几章
预期出处：fulltext/law/pipl.txt
- ❌ **旧索引**：0 条
- ✅ **纯字面**：
  1. `04-知识底座/knowledge/sources/fulltext/law/pipl.txt` · 第四十八条 · 可引用
  2. `04-知识底座/knowledge/sources/fulltext/law/pipl.txt` · 第七条 · 可引用
- ✅ **字面+标签**：
  1. `04-知识底座/knowledge/sources/fulltext/law/pipl.txt` · 第四十八条 · 可引用
  2. `04-知识底座/knowledge/sources/fulltext/law/pipl.txt` · 第七条 · 可引用
- ✅ **字面+标签+向量**：
  1. `04-知识底座/knowledge/sources/fulltext/law/pipl.txt` · 第七条 · 可引用
  2. `04-知识底座/knowledge/sources/fulltext/law/pipl.txt` · 第六十二条 · 可引用
  3. `04-知识底座/knowledge/sources/fulltext/law/minfadian.txt` · 第一千零三十五条 · 可引用
  4. `04-知识底座/knowledge/sources/fulltext/law/minfadian.txt` · 第一千零三十六条 · 可引用

### q08. 翻车的素材还能怎么用
预期出处：经营-04-品牌风险与对冲 / 心理-01-准社会关系
- ❌ **旧索引**：0 条
- ❌ **纯字面**：0 条（拒答：sim 无 < 0.66；cov 0.35 < 0.40 或 oov 0.26 > 0.50）
- ❌ **字面+标签**：0 条（拒答：sim 无 < 0.66；cov 0.35 < 0.40 或 oov 0.26 > 0.50）
- ❌ **字面+标签+向量**：0 条（拒答：sim 无 < 0.66；cov 0.35 < 0.40 或 oov 0.26 > 0.50）

### q09. 新号前几条视频平台会给多少流量
预期出处：02-新号冷启动与养号 / 01-推荐机制与流量池
- ❌ **旧索引**：0 条
- ❌ **纯字面**：0 条（拒答：sim 无 < 0.66；cov 0.39 < 0.40 或 oov 0.18 > 0.50）
- ❌ **字面+标签**：0 条（拒答：sim 无 < 0.66；cov 0.39 < 0.40 或 oov 0.18 > 0.50）
- ❌ **字面+标签+向量**：0 条（拒答：sim 无 < 0.66；cov 0.39 < 0.40 或 oov 0.18 > 0.50）

### q10. 评论区怎么把人引到私信
预期出处：L3-战术-评论区与私信话术
- ❌ **旧索引**：0 条
- ❌ **纯字面**：0 条（拒答：sim 无 < 0.66；cov 0.34 < 0.40 或 oov 0.12 > 0.50）
- ❌ **字面+标签**：0 条（拒答：sim 无 < 0.66；cov 0.34 < 0.40 或 oov 0.12 > 0.50）
- ✅ **字面+标签+向量**：
  1. `04-知识底座/knowledge/methodology/人性-05-社会交换理论.md` · §1 · 仅参考
  2. `04-知识底座/knowledge/methodology/L3-战术-跨平台改写.md` · §2 · 仅参考
  3. `04-知识底座/knowledge/methodology/L3-战术-评论区与私信话术.md` · §2 · 仅参考
  4. `04-知识底座/knowledge/methodology/人性-02-注意力商品化.md` · §1 · 仅参考 〔标签〕
  5. `04-知识底座/knowledge/methodology/人性-03-互惠利他.md` · §1 · 仅参考 〔标签〕

### q11. 视频发出去48小时内看哪几个数据
预期出处：制作-02-单条视频复盘方法
- ❌ **旧索引**：0 条
- ✅ **纯字面**：
  1. `04-知识底座/knowledge/methodology/制作-02-单条视频复盘方法.md` · §3 · 仅参考
  2. `04-知识底座/knowledge/methodology/制作-02-单条视频复盘方法.md` · §2 · 仅参考
- ✅ **字面+标签**：
  1. `04-知识底座/knowledge/methodology/制作-02-单条视频复盘方法.md` · §3 · 仅参考
  2. `04-知识底座/knowledge/methodology/制作-02-单条视频复盘方法.md` · §2 · 仅参考
- ✅ **字面+标签+向量**：
  1. `04-知识底座/knowledge/methodology/制作-02-单条视频复盘方法.md` · §3 · 仅参考
  2. `04-知识底座/knowledge/methodology/制作-02-单条视频复盘方法.md` · §2 · 仅参考

### q12. 搬运别人的视频会有什么后果
预期出处：03-违规红线
- ❌ **旧索引**：0 条
- ❌ **纯字面**：
  1. `04-知识底座/knowledge/methodology/01-推荐机制与流量池.md` · §6 · 仅参考
  2. `04-知识底座/knowledge/sources/secondhand/behavioral-economics-notes/behavioral-economics-notes__docs_03-羊群效应-资讯级联-排队越长的餐厅越好吃吗.md` · §6 · 仅参考
- ❌ **字面+标签**：
  1. `04-知识底座/knowledge/methodology/01-推荐机制与流量池.md` · §6 · 仅参考
  2. `04-知识底座/knowledge/sources/secondhand/behavioral-economics-notes/behavioral-economics-notes__docs_03-羊群效应-资讯级联-排队越长的餐厅越好吃吗.md` · §6 · 仅参考
- ❌ **字面+标签+向量**：
  1. `04-知识底座/knowledge/methodology/01-推荐机制与流量池.md` · §6 · 仅参考
  2. `04-知识底座/knowledge/sources/secondhand/behavioral-economics-notes/behavioral-economics-notes__docs_03-羊群效应-资讯级联-排队越长的餐厅越好吃吗.md` · §6 · 仅参考

### q13. 除了接单还有哪几种变现方式
预期出处：经营-01-五种变现形态
- ❌ **旧索引**：0 条
- ❌ **纯字面**：0 条（拒答：sim 无 < 0.66；cov 0.38 < 0.40 或 oov 0.30 > 0.50）
- ❌ **字面+标签**：0 条（拒答：sim 无 < 0.66；cov 0.38 < 0.40 或 oov 0.30 > 0.50）
- ❌ **字面+标签+向量**：
  1. `04-知识底座/knowledge/monetization/README.md` · §5 · 仅参考
  2. `04-知识底座/knowledge/attachments/research/36kr-ai-blogger-monetization.md` · §71 · 仅参考
  3. `04-知识底座/knowledge/attachments/research/36kr-ai-blogger-monetization.md` · §81 · 仅参考

### q14. 抖音的流量池是一层层往上推的吗
预期出处：流量理论-推荐到搜索 / 01-推荐机制与流量池
- ❌ **旧索引**：0 条
- ❌ **纯字面**：0 条（拒答：sim 无 < 0.66；cov 0.34 < 0.40 或 oov 0.34 > 0.50）
- ❌ **字面+标签**：0 条（拒答：sim 无 < 0.66；cov 0.34 < 0.40 或 oov 0.34 > 0.50）
- ✅ **字面+标签+向量**：
  1. `04-知识底座/knowledge/methodology/01-推荐机制与流量池.md` · §3 · 仅参考
  2. `04-知识底座/knowledge/methodology/流量理论-推荐到搜索.md` · §7 · 仅参考
  3. `04-知识底座/knowledge/methodology/01-推荐机制与流量池.md` · §2 · 仅参考

### q15. 怎么吃到搜索流量
预期出处：流量理论-推荐到搜索
- ❌ **旧索引**：0 条
- ✅ **纯字面**：
  1. `04-知识底座/knowledge/methodology/流量理论-推荐到搜索.md` · §6 · 仅参考
  2. `04-知识底座/knowledge/methodology/00-操盘主干.md` · §6 · 仅参考
  3. `04-知识底座/knowledge/methodology/00-操盘主干.md` · §24 · 仅参考
  4. `04-知识底座/knowledge/methodology/流量理论-推荐到搜索.md` · §1 · 仅参考
  5. `04-知识底座/knowledge/INDEX.md` · §3 · 仅参考
- ✅ **字面+标签**：
  1. `04-知识底座/knowledge/methodology/流量理论-推荐到搜索.md` · §6 · 仅参考
  2. `04-知识底座/knowledge/methodology/00-操盘主干.md` · §6 · 仅参考
  3. `04-知识底座/knowledge/methodology/00-操盘主干.md` · §24 · 仅参考
  4. `04-知识底座/knowledge/methodology/流量理论-推荐到搜索.md` · §1 · 仅参考
  5. `04-知识底座/knowledge/INDEX.md` · §3 · 仅参考
- ✅ **字面+标签+向量**：
  1. `04-知识底座/knowledge/methodology/流量理论-推荐到搜索.md` · §6 · 仅参考
  2. `04-知识底座/knowledge/methodology/00-操盘主干.md` · §6 · 仅参考
  3. `04-知识底座/knowledge/methodology/00-操盘主干.md` · §24 · 仅参考
  4. `04-知识底座/knowledge/methodology/流量理论-推荐到搜索.md` · §1 · 仅参考
  5. `04-知识底座/knowledge/INDEX.md` · §3 · 仅参考

### q16. 从收到私信到收定金要走哪几步
预期出处：L4-SOP-接单
- ❌ **旧索引**：0 条
- ✅ **纯字面**：
  1. `04-知识底座/knowledge/methodology/L4-SOP-接单.md` · §2 · 仅参考
  2. `04-知识底座/knowledge/methodology/L4-SOP-接单.md` · §1 · 仅参考
- ✅ **字面+标签**：
  1. `04-知识底座/knowledge/methodology/L4-SOP-接单.md` · §2 · 仅参考
  2. `04-知识底座/knowledge/methodology/人性-02-注意力商品化.md` · §1 · 仅参考 〔标签〕
  3. `04-知识底座/knowledge/methodology/人性-03-互惠利他.md` · §1 · 仅参考 〔标签〕
  4. `04-知识底座/knowledge/README.md` · §3 · 仅参考 〔标签〕
  5. `04-知识底座/knowledge/methodology/L1-平台-七大平台对照.md` · §3 · 仅参考 〔标签〕
- ✅ **字面+标签+向量**：
  1. `04-知识底座/knowledge/methodology/L4-SOP-接单.md` · §2 · 仅参考
  2. `04-知识底座/knowledge/methodology/L4-SOP-接单.md` · §1 · 仅参考
  3. `04-知识底座/knowledge/methodology/人性-02-注意力商品化.md` · §1 · 仅参考 〔标签〕
  4. `04-知识底座/knowledge/methodology/人性-03-互惠利他.md` · §1 · 仅参考 〔标签〕
  5. `04-知识底座/knowledge/README.md` · §3 · 仅参考 〔标签〕

### q17. 主页简介三行该怎么写
预期出处：L1-主页包装与转化路径
- ❌ **旧索引**：0 条
- ✅ **纯字面**：
  1. `04-知识底座/knowledge/methodology/L1-主页包装与转化路径.md` · §5 · 仅参考
  2. `04-知识底座/knowledge/methodology/L1-主页包装与转化路径.md` · §6 · 仅参考
  3. `04-知识底座/knowledge/methodology/00-操盘主干.md` · §25 · 仅参考
- ✅ **字面+标签**：
  1. `04-知识底座/knowledge/methodology/L1-主页包装与转化路径.md` · §5 · 仅参考
  2. `04-知识底座/knowledge/methodology/L1-主页包装与转化路径.md` · §6 · 仅参考
  3. `04-知识底座/knowledge/methodology/00-操盘主干.md` · §25 · 仅参考
- ✅ **字面+标签+向量**：
  1. `04-知识底座/knowledge/methodology/L1-主页包装与转化路径.md` · §6 · 仅参考
  2. `04-知识底座/knowledge/methodology/L1-主页包装与转化路径.md` · §5 · 仅参考
  3. `04-知识底座/knowledge/methodology/00-操盘主干.md` · §25 · 仅参考

### q18. 六层链路里哪一层最容易断
预期出处：00-操盘主干
- ❌ **旧索引**：0 条
- ❌ **纯字面**：0 条（拒答：sim 无 < 0.66；cov 0.39 < 0.40 或 oov 0.23 > 0.50）
- ❌ **字面+标签**：0 条（拒答：sim 无 < 0.66；cov 0.39 < 0.40 或 oov 0.23 > 0.50）
- ❌ **字面+标签+向量**：0 条（拒答：sim 无 < 0.66；cov 0.39 < 0.40 或 oov 0.23 > 0.50）

### q19. 一周发几条、怎么排
预期出处：L3-战术-一周内容节奏
- ❌ **旧索引**：0 条
- ❌ **纯字面**：0 条（拒答：sim 无 < 0.66；cov 0.30 < 0.40 或 oov 0.15 > 0.50）
- ❌ **字面+标签**：0 条（拒答：sim 无 < 0.66；cov 0.30 < 0.40 或 oov 0.15 > 0.50）
- ✅ **字面+标签+向量**：
  1. `04-知识底座/knowledge/methodology/L3-战术-一周内容节奏.md` · §1 · 仅参考
  2. `04-知识底座/knowledge/methodology/L3-战术-一周内容节奏.md` · §7 · 仅参考
  3. `04-知识底座/knowledge/methodology/02-新号冷启动与养号.md` · §3 · 仅参考
  4. `04-知识底座/knowledge/accounts/douyin/_process-samples.md` · §1 · 仅参考
  5. `04-知识底座/knowledge/sources/secondhand/books-for-agents/email-marketing-how-to-push-send-and-grow-your-business.md` · §30 · 仅参考

### q20. 数据不好是选题问题还是结构问题
预期出处：制作-02-单条视频复盘方法
- ❌ **旧索引**：0 条
- ✅ **纯字面**：
  1. `04-知识底座/knowledge/methodology/制作-02-单条视频复盘方法.md` · §7 · 仅参考
  2. `04-知识底座/knowledge/methodology/制作-02-单条视频复盘方法.md` · §8 · 仅参考
- ✅ **字面+标签**：
  1. `04-知识底座/knowledge/methodology/制作-02-单条视频复盘方法.md` · §7 · 仅参考
  2. `04-知识底座/knowledge/INDEX.md` · §9 · 仅参考 〔标签〕
  3. `04-知识底座/knowledge/methodology/L1-平台-七大平台对照.md` · §3 · 仅参考 〔标签〕
  4. `04-知识底座/knowledge/methodology/L4-SOP-发布.md` · §2 · 仅参考 〔标签〕
  5. `04-知识底座/knowledge/sources/fulltext/official/bilibili-shequ-guifan.txt` · §14.2 · 可引用 〔标签〕
- ✅ **字面+标签+向量**：
  1. `04-知识底座/knowledge/methodology/制作-02-单条视频复盘方法.md` · §7 · 仅参考
  2. `04-知识底座/knowledge/INDEX.md` · §9 · 仅参考 〔标签〕
  3. `04-知识底座/knowledge/methodology/L1-平台-七大平台对照.md` · §3 · 仅参考 〔标签〕
  4. `04-知识底座/knowledge/methodology/L4-SOP-发布.md` · §2 · 仅参考 〔标签〕
  5. `04-知识底座/knowledge/sources/fulltext/official/bilibili-shequ-guifan.txt` · §14.2 · 可引用 〔标签〕

## 逐条明细（无答案集）

### n01. 抖音星图的投放最低预算是多少
- ✅ **旧索引**：正确拒答
- ❌ **纯字面**：硬答 2 条
  1. `04-知识底座/knowledge/methodology/L1-无数据支撑清单.md` · §2 · 仅参考
  2. `04-知识底座/knowledge/sources/secondhand/behavioral-economics-notes/behavioral-economics-notes__docs_05-锚定效应-诱饵效应-100规则-1000元原价是怎样骗你的.md` · §7 · 仅参考
- ❌ **字面+标签**：硬答 2 条
  1. `04-知识底座/knowledge/methodology/L1-无数据支撑清单.md` · §2 · 仅参考
  2. `04-知识底座/knowledge/sources/secondhand/behavioral-economics-notes/behavioral-economics-notes__docs_05-锚定效应-诱饵效应-100规则-1000元原价是怎样骗你的.md` · §7 · 仅参考
- ❌ **字面+标签+向量**：硬答 2 条
  1. `04-知识底座/knowledge/methodology/L1-无数据支撑清单.md` · §2 · 仅参考
  2. `04-知识底座/knowledge/sources/secondhand/behavioral-economics-notes/behavioral-economics-notes__docs_05-锚定效应-诱饵效应-100规则-1000元原价是怎样骗你的.md` · §7 · 仅参考

### n02. 2025 年抖音日活是多少
- ✅ **旧索引**：正确拒答
- ❌ **纯字面**：硬答 5 条
  1. `04-知识底座/knowledge/attachments/research/36kr-ai-blogger-monetization.md` · §22 · 仅参考
  2. `04-知识底座/knowledge/methodology/抽样与归因的边界.md` · §10 · 仅参考
  3. `04-知识底座/knowledge/methodology/理论到操盘动作映射表.md` · §2 · 仅参考
- ❌ **字面+标签**：硬答 5 条
  1. `04-知识底座/knowledge/attachments/research/36kr-ai-blogger-monetization.md` · §22 · 仅参考
  2. `04-知识底座/knowledge/methodology/抽样与归因的边界.md` · §10 · 仅参考
  3. `04-知识底座/knowledge/methodology/理论到操盘动作映射表.md` · §2 · 仅参考
- ❌ **字面+标签+向量**：硬答 5 条
  1. `04-知识底座/knowledge/attachments/research/36kr-ai-blogger-monetization.md` · §22 · 仅参考
  2. `04-知识底座/knowledge/methodology/抽样与归因的边界.md` · §10 · 仅参考
  3. `04-知识底座/knowledge/methodology/理论到操盘动作映射表.md` · §2 · 仅参考

### n03. 小红书封面文案怎么写
- ✅ **旧索引**：正确拒答
- ❌ **纯字面**：硬答 5 条
  1. `04-知识底座/knowledge/methodology/L3-战术-跨平台改写.md` · §2 · 仅参考
  2. `04-知识底座/knowledge/methodology/L3-战术-跨平台改写.md` · §3 · 仅参考
  3. `04-知识底座/knowledge/methodology/L1-矩阵与投放.md` · §3 · 仅参考
- ❌ **字面+标签**：硬答 5 条
  1. `04-知识底座/knowledge/methodology/L3-战术-跨平台改写.md` · §2 · 仅参考
  2. `04-知识底座/knowledge/methodology/L3-战术-跨平台改写.md` · §3 · 仅参考
  3. `04-知识底座/knowledge/methodology/L1-矩阵与投放.md` · §3 · 仅参考
- ❌ **字面+标签+向量**：硬答 5 条
  1. `04-知识底座/knowledge/methodology/L3-战术-跨平台改写.md` · §2 · 仅参考
  2. `04-知识底座/knowledge/methodology/L3-战术-跨平台改写.md` · §3 · 仅参考
  3. `04-知识底座/knowledge/methodology/L1-矩阵与投放.md` · §3 · 仅参考

### n04. 视频号直播推流码率设多少
- ✅ **旧索引**：正确拒答
- ✅ **纯字面**：正确拒答
- ✅ **字面+标签**：正确拒答
- ✅ **字面+标签+向量**：正确拒答

### n05. 抖音蓝V认证一年多少钱
- ✅ **旧索引**：正确拒答
- ❌ **纯字面**：硬答 3 条
  1. `04-知识底座/knowledge/sources/fulltext/official/yuwen-guifan-yinwen-82.txt` · §31 · 仅参考
  2. `04-知识底座/knowledge/methodology/增长理论-AARRR到复购.md` · §2 · 仅参考
  3. `04-知识底座/knowledge/methodology/理论到操盘动作映射表.md` · §2 · 仅参考
- ❌ **字面+标签**：硬答 5 条
  1. `04-知识底座/knowledge/methodology/理论到操盘动作映射表.md` · §2 · 仅参考
  2. `04-知识底座/knowledge/methodology/L4-SOP-接单.md` · §2 · 仅参考 〔标签〕
  3. `04-知识底座/knowledge/sources/fulltext/official/openai-api-pricing.md` · §23 · 可引用 〔标签〕
- ❌ **字面+标签+向量**：硬答 5 条
  1. `04-知识底座/knowledge/methodology/理论到操盘动作映射表.md` · §2 · 仅参考
  2. `04-知识底座/knowledge/methodology/L4-SOP-接单.md` · §2 · 仅参考 〔标签〕
  3. `04-知识底座/knowledge/sources/fulltext/official/openai-api-pricing.md` · §23 · 可引用 〔标签〕

### n06. 剪映关键帧曲线怎么调
- ✅ **旧索引**：正确拒答
- ✅ **纯字面**：正确拒答
- ✅ **字面+标签**：正确拒答
- ✅ **字面+标签+向量**：正确拒答

### n07. TikTok 美国小店入驻保证金多少
- ✅ **旧索引**：正确拒答
- ✅ **纯字面**：正确拒答
- ✅ **字面+标签**：正确拒答
- ✅ **字面+标签+向量**：正确拒答

### n08. 快手磁力聚星的接单门槛是什么
- ✅ **旧索引**：正确拒答
- ✅ **纯字面**：正确拒答
- ✅ **字面+标签**：正确拒答
- ✅ **字面+标签+向量**：正确拒答

### n09. 公众号文章排版规范
- ✅ **旧索引**：正确拒答
- ❌ **纯字面**：硬答 4 条
  1. `04-知识底座/knowledge/sources/fulltext/official/weixin-wailian-neirong-guanli-guifan.txt` · §5.2 · 仅参考
  2. `04-知识底座/knowledge/sources/fulltext/official/weixin-gongzhong-pingtai-yunying-guifan.txt` · §78 · 仅参考
  3. `04-知识底座/knowledge/sources/fulltext/official/weixin-gongzhong-pingtai-yunying-guifan.txt` · §76 · 仅参考
- ❌ **字面+标签**：硬答 4 条
  1. `04-知识底座/knowledge/sources/fulltext/official/weixin-wailian-neirong-guanli-guifan.txt` · §5.2 · 仅参考
  2. `04-知识底座/knowledge/sources/fulltext/official/weixin-gongzhong-pingtai-yunying-guifan.txt` · §78 · 仅参考
  3. `04-知识底座/knowledge/sources/fulltext/official/weixin-gongzhong-pingtai-yunying-guifan.txt` · §76 · 仅参考
- ❌ **字面+标签+向量**：硬答 4 条
  1. `04-知识底座/knowledge/sources/fulltext/official/weixin-gongzhong-pingtai-yunying-guifan.txt` · §76 · 仅参考
  2. `04-知识底座/knowledge/sources/fulltext/official/weixin-gongzhong-pingtai-yunying-guifan.txt` · §338 · 仅参考
  3. `04-知识底座/knowledge/sources/fulltext/official/weixin-wailian-neirong-guanli-guifan.txt` · §5.2 · 仅参考

### n10. 知乎盐选投稿多久审核
- ✅ **旧索引**：正确拒答
- ✅ **纯字面**：正确拒答
- ✅ **字面+标签**：正确拒答
- ✅ **字面+标签+向量**：正确拒答

### n11. 抖音小店保证金怎么退
- ✅ **旧索引**：正确拒答
- ✅ **纯字面**：正确拒答
- ✅ **字面+标签**：正确拒答
- ✅ **字面+标签+向量**：正确拒答

### n12. B站充电计划的分成比例
- ✅ **旧索引**：正确拒答
- ✅ **纯字面**：正确拒答
- ✅ **字面+标签**：正确拒答
- ✅ **字面+标签+向量**：正确拒答

## 口径与偏差（先看这段再引用数字）

1. **旧索引 0 命中不是实现 bug**：旧检索要求查询的全部二元字组同时命中且整句子串出现，自然问句必然 0；它对关键词查询有效（查「完播率」「报价」各返回 5 条）。
2. **命中是路径级判定**：前 5 条里出现预期文件即记命中，不保证那一段就是最佳段；段级正确性看 locator，人工回原文核对。
3. **两个评估集都不是盲测**：二十条有答案问题是在读过语料后写的；十二条无答案问题是按「本库不该有」挑的。阈值是在这两组上选的，存在过拟合风险，换一批问题要重新校准。
4. **无答案集的判定偏严**：只要返回任何段落就记硬答，哪怕那一段确实是本库对相关话题的真实记载（例如库里有一段小红书平台对比，但它答不了「封面文案怎么写」）。
5. **标签命中的含义**：标〔标签〕的条目只说明命中了人工同义词表，原文未必回答问题，不能当引用依据。
6. **q08 语料本身没有直接答案**（翻车素材复用），它留在有答案集里是为了看会不会拒答，不是标准答案题。
