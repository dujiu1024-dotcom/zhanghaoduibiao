# 商业操盘 Skills 索引与调用关系

## 技能列表

| Skill | 触发场景 | 主要产物 |
|---|---|---|
| business-intake | 新商业任务、问题不清 | 任务简报与风险分级 |
| business-diagnosis | 经营异常、增长/利润问题 | 诊断报告与根因假设 |
| strategic-planning | 战略方向、资源配置 | 战略方案与取舍 |
| industry-competition-analysis | 行业、竞品、替代 | 竞争分析 |
| customer-marketing-strategy | 客户、产品、营销增长 | 营销策略与实验 |
| business-model-analysis | 商业模式、交易与变现 | 商业模式图与验证计划 |
| financial-unit-economics | 财务、现金、单位经济 | 财务分析与敏感性 |
| commercial-decision-review | 重大决策、反方审查 | 决策挑战与风险 |
| execution-metrics-plan | 决策获批后推进执行 | 执行计划与指标 |
| performance-attribution-review | 执行后复盘 | 复盘报告与知识候选 |

## 调用关系

```mermaid
flowchart TD
 A[商业任务] --> B[business-intake]
 B --> C{任务类型}
 C --> D[business-diagnosis]
 C --> E[strategic-planning]
 C --> F[industry-competition-analysis]
 C --> G[customer-marketing-strategy]
 C --> H[business-model-analysis]
 C --> I[financial-unit-economics]
 D --> J[commercial-decision-review]
 E --> J
 F --> J
 G --> J
 H --> J
 I --> J
 J --> K{批准/决策确定}
 K --> L[execution-metrics-plan]
 L --> M[performance-attribution-review]
 M --> N[知识回写候选]
```

此图是逻辑调用关系，不要求所有任务经过全部 Skill。简单任务可以跳过 intake 或审查；高风险任务必须执行决策审查和审批门禁。

## 组合建议

- 战略进入新市场：business-intake → industry-competition-analysis → strategic-planning → financial-unit-economics → commercial-decision-review → execution-metrics-plan。
- 新产品上市：business-intake → customer-marketing-strategy → business-model-analysis → financial-unit-economics → commercial-decision-review → execution-metrics-plan。
- 经营恶化：business-intake → business-diagnosis → financial-unit-economics → commercial-decision-review → execution-metrics-plan。
- 试点结束：performance-attribution-review；必要时回到诊断或战略 Skill。

## 通用质量约束

- Skill 只描述“如何完成”，不重复总控宪法和专家职责。
- 所有关键数据、证据和结论可追溯。
- 资料不足时标记未知，不编造。
- 外部影响动作须人工审批。
- 知识回写是候选，不自动入库。


## TRAE 技能加载规范与本项目静态检查

- 项目技能目录：`.trae/skills/<skill-name>/SKILL.md`。
- 每个技能以 YAML frontmatter 提供 `name` 与 `description`；目录名与 `name` 保持一致。
- TRAE 按需加载技能：先读取技能描述，判断与任务相关后再加载完整 `SKILL.md`，不应把十项技能内容一次性塞进总控规则。
- Skill 负责说明任务如何完成；Subagent 负责专业角色与独立分析；MCP Server 提供外部工具能力，三者不可混为一谈。
- 项目技能仅在当前项目使用；项目目录必须在 TRAE 中设为可信，才能加载项目技能。
- 技能命名遵循小写字母、数字和连字符，名称唯一；description 明确功能与触发场景，避免泛化词造成误触发。

### 静态验收记录

| 检查项 | 本次结果 |
|---|---|
| Skill 数量 | 10 个 |
| 目录名与 frontmatter name 一致 | 待 PR 静态脚本逐项复核 |
| name / description 字段 | 待 PR 静态脚本逐项复核 |
| 必需章节与输出契约 | 按 Issue #7 标准逐项复核 |
| TRAE 本机识别与自动触发 | 未测试，留待项目末尾统一真机验收 |
