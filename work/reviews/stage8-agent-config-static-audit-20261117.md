# 商业操盘手 Agent 配置与 CI 门禁静态复核（2026-11-17）

## 1. 范围与限制

检查范围：
- 根目录 `AGENTS.md`；
- `.trae/rules/` 下通用宪法、案例黑板、个人 IP 场景规则；
- `.trae/agents/` 六个专家定义；
- `.trae/skills/` 十个 Skill；
- `待配置Agent/商业操盘手/` 六份配置材料；
- 当前 main 分支 GitHub Actions workflow 与相关 manifest 校验脚本。

本次是仓库静态复核。没有用户的 Trae CN 3.4.20 客户端界面、实际加载事件、Agent 调用事件或权限弹窗，因此**不能对 CN 3.4.20 运行兼容性给出 PASS**。

## 2. 静态一致性结果

| 检查项 | 结果 | 依据 |
|---|---|---|
| 专家定义数量 | 6 个 | `.trae/agents/` 中 6 个 Markdown Agent 定义 |
| 配置对照表映射 | PASS | 六个名称与对应文件路径一致 |
| 专家职责边界 | PASS（静态） | 各 Agent 均定义职责、步骤、输出与不负责事项 |
| 工具范围 | PASS（静态） | 无 Bash/Edit/任意命令执行工具；研究专家额外具有 WebSearch/WebFetch |
| Skill 数量 | 10 个 | 10 个目录各有 `SKILL.md` |
| Skill 元数据 | PASS（静态） | 每个 Skill 均声明 name 与 description，名称与目录对应 |
| 通用/场景规则隔离 | PASS（静态） | 宪法 alwaysApply=true；黑板与 personal-ip alwaysApply=false；个人 IP 明确按需启用 |
| 关键文档引用 | PASS | AGENTS.md 引用的专家交付契约、黑板协议、总控提示词和 Trae 验收清单均存在 |
| 权限审批文档 | PASS（文档层） | 明确提示词约束不能替代 Trae 平台权限 |
| CN 3.4.20 Rules/Agent/Skill 实际加载 | NOT TESTED | 需要用户本机界面与事件证据 |
| 总控实际调用六类 Subagent | NOT TESTED | 静态文件不证明运行时调用 |
| 审批负向测试与子 Agent 绕过测试 | NOT TESTED | 需要本机工具权限与审批弹窗证据 |

## 3. 发现与建议

### F-01：角色工具权限仍需在 CN 3.4.20 界面逐个确认

六个 Agent 文件声明的工具如下：
- strategy / competition / marketing / operations / decision-challenger：Read、Grep、Glob、Write；
- research：Read、Grep、Glob、WebSearch、WebFetch、Write。

未发现 Bash 或 Edit 权限声明。当前 Write 是为了让专家将独立产物写入案例黑板；这并不代表 Trae 平台一定能将 Write 限制在 `work/cases/<case_id>/`。

**真机验收要求：** 确认 Write 是否可限制到项目工作区/案例目录；若平台不能做路径级限制，则使用逐项审批或人工交接，不得宣称已实现路径沙箱。Research 的 WebSearch/WebFetch 也需验证实际外部访问权限与审批策略。

### F-02：总控配置包与项目原生规则是两层资产

`待配置Agent/商业操盘手/` 是供用户复制到 Trae 配置界面的总控提示词和验收材料；`.trae/agents/`、`.trae/rules/`、`.trae/skills/` 是仓库中的项目配置资产。文件存在不能证明 Trae CN 3.4.20 已识别它们，也不能证明自定义总控能够调用 Subagent。

README 对此边界已有明确说明，本次未发现应当擅自修改的身份或专家映射。

### F-03：现有 RAG 安全测试 Workflow 未显式收紧 GITHUB_TOKEN 权限

`.github/workflows/test-rag-db-safety.yml` 未声明 workflow/job 级 `permissions`。建议明确设置 `contents: read`，使该测试任务只需读取仓库，不继承不必要的写权限。本 PR 对此作最小修正。

### F-04：Trae CN 3.4.20 兼容性必须保留为真机阻塞

目前没有可靠的仓库证据可以证明 CN 3.4.20 的 Agent/Rules/Skills/Subagent 功能入口、frontmatter 解析和权限粒度与文件预期完全一致。不得以国际版或其他版本代替。按 `05-真机配置验收清单.md` 执行并保留原始输入、完整输出、可见事件和权限提示。

## 4. 建议的最小权限验收矩阵

| 角色 | 预期工具 | 必须验证 |
|---|---|---|
| strategy / competition / marketing / operations | Read/Grep/Glob/Write | Write 仅用于约定案例产物；无 Shell/外发能力 |
| decision-challenger | Read/Grep/Glob/Write | 只提交挑战意见，不执行被审查动作 |
| research | Read/Grep/Glob/WebSearch/WebFetch/Write | 外部检索范围、敏感数据不外发、来源记录 |
| controller | 按任务配置 | 付款/发布/合同/敏感数据外发均需平台级人工确认 |

若平台不能提供某项限制，记录为 NOT OBSERVABLE 或 BLOCKED，采用人工替代流程，不把提示词当作技术强制门禁。

## 5. 本 PR 变更

- 新增本静态审查报告；
- 将 RAG 安全测试 workflow 的 token 权限明确限制为 `contents: read`。

不更改 Agent 身份、路由、Skills、Rules，不声称 CN 3.4.20 真机兼容通过。
