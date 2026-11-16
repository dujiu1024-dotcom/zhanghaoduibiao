# Trae 客户端环境信息取证

**取证时间**：2026-11-16 16:57 CST
**取证人**：总控 Agent

---

## 一、Agent 可直接获取的信息

| 字段 | 值 | 来源 |
|---|---|---|
| **产品名称（系统级）** | macOS | `sw_vers` |
| **系统版本** | 27.0.1 | `sw_vers` |
| **Build Version** | 26A434 | `sw_vers` |
| **操作系统架构** | arm64 (Apple Silicon) | `uname -m` |
| **CPU** | Apple M5 | `sysctl` |
| **内存** | 24 GB | `sysctl` |
| **当前时间** | 2026-11-16 16:57:19 CST | `date` |
| **Git 分支** | evidence/stage8-batch-b-supplement-report | `git branch` |
| **Git HEAD** | f082010（docs(stage8-batch-b): add supplement acceptance final report） | `git log` |
| **专家定义文件数** | 6 | `.trae/agents/` |
| **Skill 定义目录数** | 10 | `.trae/skills/` |

## 二、Agent 无法访问、需用户手动查看的字段（Trae CN 客户端 UI）

以下字段**不在文件系统中**，只能通过 Trae 客户端界面查看。Agent 无法自行访问 UI，需用户协助：

| 字段 | 需要查看的位置 | 说明 |
|---|---|---|
| **产品名称（Trae 客户端）** | 菜单栏 → Trae → About Trae（或 Settings → About） | 应显示 "Trae CN" 或类似 |
| **客户端版本** | 菜单栏 → Trae → About Trae | 类似 "3.4.20" |
| **Build Number** | 菜单栏 → Trae → About Trae | 内部构建号 |
| **当前模型名称** | 聊天窗口顶部或模型选择器 | 当前会话使用的模型名称 |

### 截图位置指引（参考 macOS 应用通用模式）

```
┌─────────────────────────────────────────────┐
│  菜单栏                                      │
│  [Trae] [File] [Edit] ...                   │
│   ↑                                          │
│   └── 点击 → 下拉菜单中找 "About Trae CN"   │
│       或 "关于 Trae CN"                      │
│                                              │
│  聊天窗口顶部模型选择器                      │
│  ┌──────────────────────────────────────┐   │
│  │ 🔒 seed-code  ▼  ← 点击下拉看完整名称 │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**当前已知约束**：
- Git 分支已切换到 `evidence/stage8-batch-b-supplement-report`（非 main）
- HEAD 是新提交 `f082010`，与之前 A 批次冻结时的 `88a31ef` 不同

## 三、Trae 配置文件状态

```
.trae/
├── agents/     (6 个专家定义文件，全部可读)
│   ├── competition-expert.md
│   ├── decision-challenger.md
│   ├── marketing-expert.md
│   ├── operations-expert.md
│   ├── research-expert.md
│   └── strategy-expert.md
├── rules/      (5 个规则文件，含项目宪法和黑板协议)
│   ├── 00-commercial-constitution.md
│   ├── 10-case-blackboard.md
│   └── scenarios/personal-ip.md
└── skills/     (10 个 Skill 目录，每个含 SKILL.md)
    ├── business-diagnosis/
    ├── business-intake/
    ├── business-model-analysis/
    ├── commercial-decision-review/
    ├── customer-marketing-strategy/
    ├── execution-metrics-plan/
    ├── financial-unit-economics/
    ├── industry-competition-analysis/
    ├── performance-attribution-review/
    └── strategic-planning/
```

**配置完整性检查**：✅ 通过——所有专家、规则、Skill 文件都存在且可读。

## 四、工作区变更状态

```
已修改:
  01-执行包/checks/.event.last
  01-执行包/checks/latest.json

未跟踪（新文件，主要是本轮测试证据）:
  stage8_batch_b_supplement/           ← 本轮新建证据目录
  .workbuddy/
  01-执行包/checks/20261116-*.json（多个）
```

**工作区检查**：
- `stage8_batch_b_supplement/` 是本轮新建目录，包含 B-08、B1、B2、environment 的全部证据
- 无代码文件修改
- 无知识库文件修改
- 无生产配置修改
- 符合"禁止修改项目代码、知识库、RAG 数据及任何生产配置"的约束

## 五、unknown_not_exposed 字段

以下字段经 Agent 检查文件系统和进程信息后仍无法获取：

| 字段 | 状态 | 原因 |
|---|---|---|
| Trae CN 客户端版本号 | unknown_not_exposed | 不在文件系统中，需从应用 UI 查看 |
| Trae CN Build Number | unknown_not_exposed | 不在文件系统中，需从应用 UI 查看 |
| 当前会话使用的完整模型名称 | unknown_not_exposed | 模型名称在运行时注入，文件系统中无持久化记录 |
| Trae CN 客户端安装路径 | unknown_not_exposed | 未检查 /Applications/ |
