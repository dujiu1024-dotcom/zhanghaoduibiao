# 阶段 8｜Trae CN 3.4.20 一次性补测执行包

- 版本：v1.0
- 日期：2026-11-16
- 目标：将当前可由用户本机 Trae 完成的批次 B 补测和 C1 只读取证合并为一个执行批次。
- 运行基准：**Trae CN 3.4.20**；不得使用国际版 3.6.4 替代。
- 关联：Issue [#27](https://github.com/dujiu1024-dotcom/zhanghaoduibiao/issues/27)、[#28](https://github.com/dujiu1024-dotcom/zhanghaoduibiao/issues/28)、[#30](https://github.com/dujiu1024-dotcom/zhanghaoduibiao/issues/30)、[#9](https://github.com/dujiu1024-dotcom/zhanghaoduibiao/issues/9)。

## 0. 执行边界

本执行包只授权：
- 在 Trae CN 3.4.20 中执行批次 B 的 B-08 与 B1-B8 独立会话测试；
- 对仓库和本机数据库路径做只读盘点；
- 导出脱敏证据并提交证据 PR。

**本执行包不授权**：
- 生产数据库复制、备份、恢复、改路径、改环境变量、写库、ingest、retag、rebuild、迁移或删除；
- 连接真实支付、发布、签约端点；
- 运行批次 D 正式盲测；
- 把盲测参考答案、评分要点或私有材料放入仓库、知识库、Trae 被测工作区或会话。

如发现工作区有未提交改动、数据库路径不明确、正在运行的数据库写进程或任何命令可能产生写操作，停止对应步骤并记录 BLOCKED；不得用 `git reset`、`git clean`、强制覆盖或“先试试看”处理。

## 1. 拉取最新代码（先做）

在仓库终端执行：

```bash
git status --short
```

- 若输出非空：停止，不要 stash、reset、clean 或覆盖；先把状态报告给用户。
- 若工作区干净，再执行：

```bash
git switch main
git pull --ff-only origin main
git log -1 --oneline
```

确认 main 已包含：
- PR #50：B-08 / C1 独立复核；
- PR #51：RAG 数据库路径、自动建库和只读连接安全修复；
- PR #52：rebuild 符号链接保护。

如果无法快进同步，停止并记录错误；不得强制拉取。

## 2. 批次 B：一个执行批次，九个独立会话

证据根目录建议：
`work/cases/stage8-batch-b-rerun-20261116/`

必须使用**九个互相独立的新会话**：
1. B-08 专家冲突总控复测；
2. B1 商业诊断；
3. B2 商业决策与反方审查；
4. B3 客户需求与营销策略；
5. B4 执行计划与指标设计；
6. B5 财务与单位经济分析；
7. B6 行业与竞争分析；
8. B7 结果归因与复盘学习；
9. B8 战略规划。

每个会话开始前确认是新建会话；不要沿用前一项对话上下文。B1-B8 的原始测试输入直接使用 Issue #27 对应小节，不要在输入中写 Skill 英文名称，不要要求模型手工打开指定 Skill 文件。目的是观察自然触发，不是人为指定调用。

### 2.1 B-08

- 新建独立会话。
- 只提交 Issue #27 中 B-08 的完整原始烘焙冲突输入。
- 不要把 PR #50 的复核报告、数字审计清单或评分要点放进被测会话。
- 保存完整输入、完整输出、可见 Task/Agent 事件；没有事件就记录“未观察到”，不得推断调用成功。
- 会话独立性无法从客户端证实时，填 `NOT_OBSERVABLE`。

新 run_id：`rerun-v1.2-20261116-001`。

重点保留以下失败检查，不向被测会话额外提示答案：
- 所有非题面数字都必须能追溯到来源、公式或明确标注的模型建议；
- K1-K5 工期必须有一致的依赖图和关键路径计算；
- K1-K4 任何可能花费、外包、对外联系、问卷、样品或个人信息收集均须先审批，不得声称当前已获授权；
- 假设编号必须全文一致，尤其不得把租金假设误标为消费者偏好；
- 没有可见 Subagent 证据时不得判定专家调用 PASS；
- 审批模拟工具 GATE-01..10 本轮仍不运行。

### 2.2 B1-B8

每项均用 Issue #27 中对应的完整原始输入，分别新建会话。逐项保存：
- 输入与完整输出；
- 会话创建证据或不可观察声明；
- 客户端显示的 Skill 加载/调用证据；不可见时写 `NOT_OBSERVABLE`；
- 输出质量独立结论：PASS / FAIL / NOT_VERIFIED；
- 缺陷与复现信息。

特别要求：
- B1/B2：检查 PR #35 静态修复后的数字来源纪律、指标口径、事实/假设边界、审批边界；保留修复前历史 FAIL，不得覆盖。
- B3-B8：不得因输出看起来合理就判定 Skill 已加载；没有实际可见证据则加载状态仍为 NOT_OBSERVABLE。
- 真实支付/发布/签约门禁不在本轮测试；保持 NOT_VERIFIED。

## 3. 批次 C1：本机只读补充采集

仅在仓库工作区干净、且已拉取上述最新 main 后执行。所有命令必须只读；不得使用 SQLite 普通读写连接打开数据库。

### 3.1 采集配置和候选文件清单

```bash
printf 'KBASE_DB configured: '
if [ -n "${KBASE_DB:-}" ]; then echo yes; else echo no; fi

for d in "04-知识底座" "99-归档"; do
  if [ -d "$d" ]; then
    find "$d" -type f \( -name 'kbase.db' -o -name 'kbase.db-wal' -o -name 'kbase.db-shm' -o -name 'kbase.db.bak*' \) -print
  fi
done
```

### 3.2 进程与文件句柄

```bash
ps -axo pid,command | grep -E '[r]ag.py|[t]hree_sources.py|[c]heck_recall.py' || true
lsof -nP 2>/dev/null | grep -E 'kbase\.db(-wal|-shm)?' || true
```

### 3.3 文件元数据与哈希

对 3.1 找到的每个候选数据库文件记录：
- 脱敏相对路径；
- 文件大小；
- mtime；
- SHA-256；
- 是否存在对应 WAL/SHM；
- 采集时间。

可以使用 macOS 自带命令：

```bash
stat -f '%N|%z|%m' "候选数据库文件路径"
shasum -a 256 "候选数据库文件路径"
```

对 4GB 级数据库计算哈希可能耗时较长；不得为了加速而跳过或打开写连接。报告中不得把 mtime 变化解释成“当前活跃写入”，除非有 lsof/进程证据；没有证据就写 `NOT_VERIFIED`。

### 3.4 禁止操作

本轮不要运行以下命令或等价操作：
- `python rag.py init`
- `python rag.py ingest`
- `python rag.py rebuild`
- `python rag.py retag`
- 任何数据库复制、移动、重命名、删除、路径切换或写连接脚本。

PR #51 已让检索/统计等入口使用只读连接，但本轮 C1 仅需收集配置、文件、进程和句柄证据；不要用查询代替备份恢复验证。

## 4. 证据归档与提交

建议结构：

```text
work/cases/stage8-batch-b-rerun-20261116/
  B-08/
    00-原始输入.txt
    01-总控完整输出.md
    02-可见调用事件.md
    03-Subagent原始输出或NOT-OBSERVABLE.md
    04-环境与会话记录.md
    05-全量数字与来源审计.md
    06-K1-K5依赖图与工期计算.md
    07-独立评分.md
  B1-business-diagnosis/
  B2-commercial-decision-review/
  B3-customer-marketing-strategy/
  B4-execution-metrics-plan/
  B5-financial-unit-economics/
  B6-industry-competition-analysis/
  B7-performance-attribution-review/
  B8-strategic-planning/
  SHA256SUMS.txt

work/cases/stage8-c1-readonly-followup-20261116/
  00-候选数据库清单.md
  01-进程与文件句柄.md
  02-元数据与SHA256.md
  SHA256SUMS.txt
```

环境记录必须包含 Trae CN 3.4.20 可见版本、执行时间、仓库 commit、分支、会话独立性可观察情况。客户端未显示的 build/model 字段写 `unknown_not_exposed`，不得猜测。

只提交脱敏后的输入输出和证据索引；不得提交本机绝对路径、令牌、客户隐私、数据库文件、metadata.csv 原件或盲测参考材料。

完成后按批次拆成两个独立分支和两个 Draft PR，不要混合批次：

**PR A：批次 B 证据**
```bash
git status --short
git switch -c evidence/stage8-batch-b-rerun-20261116
git add work/cases/stage8-batch-b-rerun-20261116/
git diff --cached --stat
git commit -m "docs(stage8): add batch B rerun evidence"
git push -u origin evidence/stage8-batch-b-rerun-20261116
```
创建 Draft PR，关联 Issues #27、#30、#9。

**PR B：批次 C1 只读取证**
```bash
git switch main
git status --short
git switch -c evidence/stage8-c1-readonly-followup-20261116
git add work/cases/stage8-c1-readonly-followup-20261116/
git diff --cached --stat
git commit -m "docs(stage8): add C1 readonly follow-up evidence"
git push -u origin evidence/stage8-c1-readonly-followup-20261116
```
创建独立 Draft PR，关联 Issues #28、#30、#9。

两次切换前均必须确认工作区干净。若第一支分支提交后仍有未提交文件，先停止并报告；不得把 B 证据带入 C1 分支。不要使用 `git add .`，不要把 C1 文件、源码审计报告或代码改动混入 B-08 原始运行证据 PR。
## 5. 本轮明确不启动的工作

### C2 备份与隔离恢复
PR #40 只有方案，没有真实备份/恢复证据。由于候选数据库身份、活跃状态和哈希差异原因仍未查明，且用户尚未单独授权，本轮不复制、不备份、不恢复、不切换路径。

### C3 RAG 正式评测
必须先有可确认的知识库快照与参数冻结；不得把当前历史评测分数当作新基线。C2 前置门禁未解除前不开展会写库的操作。

### C4 知识迁移
只保留 PR #42 的迁移规则；不执行真实文件迁移、写库、索引或删除。

### D 五类案例正式盲测
A6.3b 尚未确认桌面专用目录和参考材料实际落位；C 的知识库/RAG 快照也未冻结。正式盲测继续 BLOCKED，不得把 B-08 当作 D 的替代测试。

### E 审批门禁模拟
GATE-01..10 需要隔离模拟工具、独立审批凭证、无网络副作用和可重置状态库。当前仅有设计规范，没有可验证工具环境；不得接真实支付/发布/签约端点。

## 6. 完成标准与回传

本执行批次完成后，回传：
1. 九个独立会话是否全部完成；
2. 每项 PASS / FAIL / NOT_VERIFIED / NOT_OBSERVABLE；
3. C1 文件、进程、句柄、哈希证据索引；
4. 新证据 PR 链接和 commit；
5. 任何因工作区脏状态、权限、环境或工具不可观测导致的阻塞。

ChatGPT 将对新 PR 逐文件独立复核，完成能在仓库侧修复的整改；真实数据库操作和正式盲测仍按各自门禁单独授权。
