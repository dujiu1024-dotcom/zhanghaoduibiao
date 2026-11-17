# Trae Skills 触发与路由边界

版本：1.0  
适用：仓库内十个商业 Skills 与六类 Subagent  
原则：Skill 是任务方法包，不是独立 Agent；总控是唯一入口与最终综合责任方。多个 Skill 可组合，但必须指定一个主 Skill，避免重复诊断和重复交付。

## 1. 路由优先级

按以下顺序判断，不要求每个任务走完所有阶段：

1. **先判断是否需要结构化任务**：目标/对象/决策问题尚不清楚，主 Skill 选 `business-intake`。信息已充分时跳过。
2. **再判断问题类型**：经营结果异常用 `business-diagnosis`；明确的专项问题直接进入对应专项 Skill。
3. **专项分析按问题选择**：战略、行业竞争、客户营销、商业模式、财务单位经济各自负责其专业边界。
4. **只有方向已选定或方案已获批**，才以 `execution-metrics-plan` 制定执行计划；未获批方案只能形成待审批草案。
5. **只有存在真实执行结果数据**，才用 `performance-attribution-review` 做结果归因；没有实际数据只能做预期复盘/假设审查。
6. **重大、高影响、不可逆、争议或涉及审批门禁**，追加 `commercial-decision-review`，而不是让它替代领域分析。

## 2. 十个 Skill 的主责与排除边界

| Skill | 主责（主触发） | 不应单独承担 |
|---|---|---|
| business-intake | 问题未结构化；定义目标、对象、边界、决策人、成功标准 | 专业诊断、行业研究、最终方案 |
| business-diagnosis | 增长停滞、利润下降、客户流失、经营效率或模式问题的系统诊断 | 在证据不足时直接锁定根因；替代财务专项计算 |
| strategic-planning | 战略方向、业务组合、定位、增长路径、资源取舍 | 详细行业事实采集、财务审计、批准资源 |
| industry-competition-analysis | 市场边界、竞品/替代、行业结构、竞争反应 | 客户细分与渠道转化方案的完整设计 |
| customer-marketing-strategy | 客户细分、购买行为、价值主张、定价、渠道、获客、转化、留存 | 把曝光/意向当成交；替代经营现金流分析 |
| business-model-analysis | 价值创造/交付/获取、交易结构、收入模式、合作伙伴和规模化机制 | 将商业模式画布当作盈利证明 |
| financial-unit-economics | 利润、现金、成本、预算、盈亏平衡、单位经济和投资回报测算 | 缺少数据时编造行业基准或财务事实 |
| execution-metrics-plan | 已选方向/获批方案的任务拆解、责任、依赖、指标、节奏和监控 | 替用户批准方案、预算或对外承诺 |
| performance-attribution-review | 执行结束或指标异常后的实际结果差异与经验复盘 | 无执行数据时声称已完成真实归因 |
| commercial-decision-review | 重大方案比较、反方挑战、失败预演、风险/退出条件和审批检查 | 替代领域专家分析或替决策人批准 |

## 3. 常见重叠的裁决规则

### 3.1 business-intake vs business-diagnosis
- 用户只说“帮我看看业务怎么了”，先 intake 补齐对象、期间和目标，再 diagnosis。
- 用户已给出清晰对象、问题与数据，可直接 diagnosis，不重复 intake。
- Intake 的产物是任务简报；diagnosis 的产物是诊断报告。

### 3.2 business-diagnosis vs financial-unit-economics
- Diagnosis 负责建立系统图、指标树和竞争性根因假设。
- Financial 专项负责在数据可用时复算利润桥、现金、单位经济、盈亏平衡和敏感性。
- 可并行，但 diagnosis 不得把缺少明细的财务假设写成事实。

### 3.3 strategic-planning vs business-model-analysis
- 战略规划回答“选择哪个方向、放弃什么、资源如何取舍”。
- 商业模式分析回答“价值如何创造/交付/获取、谁付款、如何回款、成本和风险如何分担”。
- 战略选择依赖交易机制判断时组合调用；两份结论分别交付，不重复写一份泛化 SWOT。

### 3.4 industry-competition-analysis vs customer-marketing-strategy
- 竞争分析回答市场边界、替代方案、对手能力与竞争结构。
- 营销策略回答目标客户、购买过程、价值主张、定价和渠道动作。
- 竞品价格/渠道数据可作为营销输入，但不得把竞品观察直接当作客户购买证据。

### 3.5 execution-metrics-plan vs performance-attribution-review
- Execution 产出未来计划、基线、指标定义、责任人和触发条件。
- Attribution 使用实际结果、对照原假设和决策日志解释偏差。
- 计划指标不是实际结果；没有实际数据时只能输出“预期复盘/待验证假设”。

### 3.6 commercial-decision-review 的追加条件
以下任一情况可追加：高影响/高不确定/不可逆；多个专家结论冲突；资源承诺明显；存在重大下行风险；需要检查审批与退出条件。普通低风险任务不为凑数调用。

## 4. Subagent 路由映射

| 问题类型 | 首选专家 | 可选协作 |
|---|---|---|
| 战略方向、业务组合、资源取舍 | strategy-expert | competition-expert、operations-expert |
| 行业、市场边界、竞品、替代 | competition-expert | research-expert、strategy-expert |
| 客户细分、价值主张、定价、渠道 | marketing-expert | competition-expert、operations-expert |
| 收入、成本、利润、现金、交付效率 | operations-expert | research-expert、marketing-expert |
| 动态事实、来源核验、资料缺口 | research-expert | 对应领域专家 |
| 重大决策、关键假设、方案冲突 | decision-challenger | 相关领域专家；总控保留综合权 |

专家选择与 Skill 选择是两层路由：Skill 决定分析方法，Subagent 决定由谁完成专业分析。不得仅因某 Skill 被触发，就推断某个 Subagent 已被实际调用。

## 5. 调用与交付门禁

- 总控为每个任务指定主 Skill、可选辅助 Skill、负责专家、输入文件、输出路径和完成条件。
- 专家派单遵循 `07-操盘手系统设计/专家交付契约.md`；协作遵循 `07-操盘手系统设计/专家协作与黑板协议.md`。
- 同一事实只维护一个证据 ID；跨 Skill 复用引用，不复制成互相矛盾的事实。
- 各 Skill 的输出按需合并，但不得抹掉专业结论的责任归属和证据边界。
- 高风险事项停在审批请求；不得把执行计划或分析建议描述为已获批准。
- 运行日志必须区分“Skill 文件存在”“Skill 被加载”“Skill 被触发”“专家被实际调用”和“产出被总控接受”。

## 6. 验收状态

本文件和静态检查通过仅证明仓库配置的名称、路由映射和必要规则存在。Trae CN 3.4.20 是否实际加载 Skill、是否按描述触发、是否按总控派单调用专家，仍须在目标客户端留存运行证据后判定。
