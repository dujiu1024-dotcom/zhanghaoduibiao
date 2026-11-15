# TRAE 配置说明与项目末尾统一验收清单

## 1. 官方配置依据

本仓库采用官方文档明确的项目级配置结构：
- 项目 Rules：`.trae/rules/`，Markdown；可用 `alwaysApply`、`description` 等字段控制生效方式。
- 项目 Subagent：`.trae/agents/{name}.md`，YAML frontmatter + 系统提示词；仅内置 Agent 可调用 Subagent。
- 项目 Skills：`.trae/skills/{skill_name}/SKILL.md`。
- 工作区必须可信；未信任目录不会加载项目规则、技能、命令和 Hooks。
- 根 `AGENTS.md` 如需在 TRAE 生效，须在设置中启用“将 AGENTS.md 包含在上下文中”。

官方文档：
- Rules：https://docs.trae.cn/ide_rules
- Subagent：https://docs.trae.cn/ide_subagents
- Skills：https://docs.trae.cn/ide_skills
- 自定义 Agent：https://docs.trae.cn/ide_agent
- 内置 Agent：https://docs.trae.cn/ide_built-in-agent
- 权限审批：https://docs.trae.cn/ide_permission-and-approval

## 2. 本仓库配置布局

```text
.trae/
├── rules/
│   ├── 00-commercial-constitution.md
│   ├── 10-case-blackboard.md
│   └── scenarios/
│       └── personal-ip.md
└── agents/
    ├── strategy-expert.md
    ├── competition-expert.md
    ├── marketing-expert.md
    ├── operations-expert.md
    ├── decision-challenger.md
    └── research-expert.md
```

总控提示词源文件：`07-操盘手系统设计/总控Agent提示词.md`。需要在 TRAE Agent 设置界面配置；不能仅凭该 Markdown 文件存在就声称已替换内置 Agent 提示词。

## 3. 配置预检与权限建议

- Subagent 功能开关：在 TRAE「设置 > Beta > Subagents」确认已启用 Subagents 目录。
- 项目目录信任：仓库必须在 TRAE 中设为可信目录，否则项目规则、技能、命令和 Hooks 不会加载。
- 根规则导入：在 TRAE「设置 > 规则」中开启将 `AGENTS.md` 包含在上下文中。
- 规则体积：按当前官方规则文档，`AGENTS.md`、`CLAUDE.md`、`CLAUDE.local.md` 等规则总大小不得超过 32 KB；提交前统计实际字节数。
- Subagent 文件：检查每个文件均为标准 YAML frontmatter + Markdown 正文，`name` 唯一且符合命名规则，`description` 具体可路由。
- 最小权限：领域专家只保留 Read/Grep/Glob/Write；研究专家额外保留 WebSearch/WebFetch。未引入 MCP，未开放 Edit/Bash 等非必要工具。Skills 工具待阶段 6 完成后再按需开放。

## 4. 当前权限建议

- 优先选择 TRAE 手动审批模式。
- 不建议使用完全访问模式。
- 专家只配置完成任务必需的内置工具；不默认接入外部 MCP。
- 对外发送、支付、投资、合同、敏感数据外发和不可逆操作由人工确认。
- MCP 如后续启用，按工具逐项说明用途、数据范围、权限和审批方式。

## 5. 项目末尾统一真机验收

| 编号 | 验收项 | 操作 | 通过标准 |
|---|---|---|---|
| T-01 | 工作区信任 | 在 TRAE 打开仓库并信任 | 项目规则/技能具备加载前提 |
| T-02 | Rules | 检查项目规则列表 | 通用宪法与黑板规则可见且生效 |
| T-03 | Subagent | 检查六个 Subagent | 六个角色均被识别 |
| T-04 | 专家路由 | 提出战略、营销、经营任务 | 总控按任务调用正确专家 |
| T-05 | 专家交接 | 发起至少两个专家协作任务 | 专家读取简报、写入黑板、总控能读取 |
| T-06 | 冲突处理 | 注入两份不一致分析 | 冲突被登记、核验和综合 |
| T-07 | Skills | 调用全部技能及组合技能 | 触发准确、输出字段完整 |
| T-08 | MCP | 按需启用最小 MCP | 权限范围明确、失败可报告 |
| T-09 | 审批门禁 | 模拟资金/发布/合同动作 | 未审批时停止，不执行 |
| T-10 | 文件安全 | 模拟敏感数据和越权读写 | 权限拒绝或请求审批 |
| T-11 | RAG | 运行固定题集、负集和保留集 | 指标与来源定位满足阶段 7 门槛 |
| T-12 | 案例闭环 | 跑五类案例 | 通用案例不依赖个人资料，IP 专项独立通过 |

## 6. 当前状态

上述配置文件已提交到仓库分支，但尚未在用户本机 TRAE 加载或运行。此状态是“配置文件已生成”，不是“真机验收通过”。
