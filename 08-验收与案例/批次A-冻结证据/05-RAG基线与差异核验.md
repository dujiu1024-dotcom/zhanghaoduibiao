# 05 · RAG 基线与差异核验

- 生成时间：2026-11-16 10:20（CST）；修订：2026-11-16 10:40（CST，A-04 落档 U5/U11，未重新采集）
- 采集方式：只读。未执行 `ingest`、`rebuild`、`eval`、`retag`、数据库迁移或索引重建；对 `kbase.db` 仅使用 `sqlite3 "file:...?mode=ro"` 与只读 `sqlite_vec` 连接执行 `select/count`。
- 关联快照：`02-环境配置快照.json` 的 `rag` 区块；`03-Run-Manifest.json` 的 `environment.rag_*`。

## 1. 代码基线

| 项目 | 实测值 | 证据 |
|---|---|---|
| 路径 | `04-知识底座/rag/rag.py` | 文件存在 |
| Git 归属 | 已跟踪，无修改，属 HEAD `88a31efa7deac7a53d8d646471e0e2adc7e4b753` | `git status --porcelain` 无该文件 |
| 大小 / 行数 | 78,374 字节 / 1,798 行 | `ls -l`、`wc -l` |
| SHA256 | `48a3890875143cb209114c3c0cbe5fae3b7b7bfb2c3615fe4dcb330140c8c051` | `shasum -a 256` |

## 2. 参数对照表

| 参数 | rag.py 默认值 | README 值 | 评测使用值 | 最终冻结值 | 证据 |
|---|---:|---:|---:|---|---|
| `SIM_FLOOR` | 0.66 | 0.66（`rag/README.md` 参数表） | 0.66（`eval/report.md`） | **0.66（待用户确认）** | `rag.py` 第 57 行；README；eval 报告 |
| `ANSWER_MIN_COVERAGE` | **0.50** | **0.40**（参数表，历史口径） | 0.4（`eval/report.md`，历史口径） | **按运行分支冻结（U5，见 2.5）：`SHORT_RELAX=0` → 0.50；`SHORT_RELAX=1` → 动态 0.22–0.40；`RAG_ANSWER_MIN_COVERAGE` 可覆盖** | `rag.py` 第 70、94–115 行；README；eval 报告 |
| `COVERAGE_FLOOR` | 0.32 | 0.32 | 0.32 | 0.32（待用户确认） | `rag.py` 第 64 行；README；eval 报告 |
| `OOV_FLOOR` | 0.50 | 0.50 | 0.5 | 0.50（待用户确认） | `rag.py` 第 113 行；README；eval 报告 |
| `CROSS_PENALTY` | 0.9 | 未列 | 未列 | 0.9（代码唯一来源） | `rag.py` 第 60 行 |
| `POOL_MIN` | 50 | 未列 | 未列 | 50（代码唯一来源） | `rag.py` 第 63 行 |
| `STRICT_ANSWER` | 0（关） | 未列 | 未列 | 0（关） | `rag.py` 第 72 行 |
| `SHORT_RELAX` | 0（关） | 未列 | 未列 | 0（关） | `rag.py` 第 74 行 |
| `ENTITY_GATE` | 0（关） | 未列 | 未列 | 0（关） | `rag.py` 第 77 行 |
| `EMBED_MODEL` | bge-m3 | bge-m3 | bge-m3 | bge-m3 | `rag.py` 第 39 行；Ollama |
| `EMBED_DIM` | 1024 | 1024 | 1024 | 1024 | `rag.py` 第 40 行；Ollama 返回 1024 维 |
| `EMBED_BATCH` | 32 | 未列 | 未列 | 32 | `rag.py` 第 41 行 |
| Top-K 展示条数 | 由调用方 `k` 决定（API 默认 5） | 默认 5/10 | 5/10 | **按入口冻结（5 / 10 / 50，见 2.2、2.5）；不适用全局唯一值** | `rag.py` 命令参数；2.2 调用链表 |
| 重排模型 | 无实现 | 未提 | 未提 | **N/A（仓库无重排）** | 代码无 rerank 模块 |

**冻结结论**：以「代码默认值 + 库哈希」为事实基线。`ANSWER_MIN_COVERAGE` 已按运行分支冻结（U5：`SHORT_RELAX=0` 时 0.50；`SHORT_RELAX=1` 时走 `dynamic_cover_floor()` 动态 0.22–0.40；`RAG_ANSWER_MIN_COVERAGE` 可覆盖；README/eval 的 0.40 为历史文档口径），**不再裁决为 0.50 与 0.40 二选一**。Top-K 已按入口冻结（U11，见 2.5），不要求全局唯一值。`knowledge-v2/README.md` 称「代码默认 `SIM_FLOOR=0.60`」与 HEAD 实测 0.66 不符，标为过期文档。第 2.1–2.5 节为 A-03/A-04 静态调用链与裁决落档：第 2 节表格中的数值均为**源码默认值**，运行时覆盖值与可确定有效值分列于各表。

### 2.1 `ANSWER_MIN_COVERAGE` 静态调用链核验（A-03，只读）

读取位置（全部）：`rag.py` L70 在模块导入时读取环境变量；L102 `dynamic_cover_floor()` 返回该值；L1171/L1173/L1184 在 `search()` 内用于成答判定与 `meta`。**无其他读取点，无 CLI 参数、无函数参数覆盖。**

| 调用入口 | 参数来源 | 源码默认值 | 是否覆盖 | 可确定的有效值 | 证据 |
|---|---|---:|---|---|---|
| `rag.py search`（CLI） | `os.environ["RAG_ANSWER_MIN_COVERAGE"]` | 0.50 | 否（argparse 无该参数） | **0.50**（当前 shell 无 `RAG_*`）；其他父环境 unknown | `rag.py` L70；CLI 参数仅 `-k/--quality/--mode/--sim-floor/--json/--source/--no-xling`（L1761–1773） |
| `rag.py eval`（CLI） | 同上 | 0.50 | 否（仅 `--questions/--out/-k`） | **0.50**（同上）；`eval/report.md` 的 0.4 不能反推当前默认值 | `rag.py` L1787–1791；`eval/report.md` L11 |
| `验收/check_recall.py`（subprocess 调 `rag.py search`） | 继承父进程环境；脚本只传 `-k` | 0.50 | 否 | **0.50**（前提父环境无覆盖）；父环境 unknown | `check_recall.py` L161–162、L181 |
| `catalog/work/audit_a.py`（subprocess 调 `rag.py search`，不传 `-k`） | 继承父进程环境 | 0.50 | 否 | **0.50**（前提同上） | `audit_a.py` L30 |
| `catalog/check_gate.py`（同进程 `rag.search()`） | 模块级常量 | 0.50 | 否 | **0.50**（前提同上） | `check_gate.py` L48、L226 |
| `work/gap-detail-20261115/retrieval_diag.py`（同进程） | 模块级常量 | 0.50 | 否 | **0.50** | `retrieval_diag.py` L33、L41 |
| `catalog/work/batch6_failed_list.py`、`batch6_rank_diag.py`（同进程） | 模块级常量 | 0.50 | 否 | **0.50** | `batch6_failed_list.py` L51；`batch6_rank_diag.py` L48 |
| `work/gap-detail-20261115/gap_detail.py` | 仅 `rag.connect()`，不调用检索 | 0.50（已初始化未使用） | N/A | N/A | `gap_detail.py` L21 |
| `work/monitor/watch.py` | 只监控 `rag/rag.py ingest` | — | N/A | N/A（非检索入口） | `watch.py` L53 |

**结论**：
- HEAD 可确定值 = **0.50**；所有入口共用同一模块常量，未发现入口间不同值。
- 「不同值」只发生在配置层：`SHORT_RELAX=1` 时 `dynamic_cover_floor()` 不返回 `ANSWER_MIN_COVERAGE`，改用 0.22 / 0.30 / 0.36 / 0.40（`rag.py` L94–115）；`RAG_ANSWER_MIN_COVERAGE` 可覆盖默认值。当前 shell 无 `RAG_*`，但无法证明这些入口历史上未在带覆盖的 shell 中运行 → **非当前环境的运行时有效值 unknown**。
- 文档差异保留：`rag/README.md` L132 记 0.40，`eval/report.md` L11 记 0.4；`work/backups/rename-20261115/04-知识底座__rag__rag.py` L60 默认 0.40，说明 README 口径来自旧版代码，但**不能证明** README 对应哪次运行。不修改代码与文档。

### 2.2 Top-K 静态调用链核验（A-03，只读）

| 调用入口 | 传值 | 有效 Top-K | 证据 |
|---|---|---:|---|
| `rag.py search`（CLI） | `-k`，默认 5 | 5（未显式传参时） | `rag.py` L1763；`cmd_search` 使用 `args.k`（L1408、L1413、L1416、L1423、L1426、L1473） |
| `rag.py eval`（CLI） | `-k`，默认 5 | 5 | `rag.py` L1790、L1582、L1644 |
| Python API `search(conn, query, k=5, …)` | 函数默认 5 | 5 | `rag.py` L1159 |
| Python API `fuse(..., k=5)` | 函数默认 5 | 5 | `rag.py` L979 |
| Python API `legacy_search(query, k=5)` | 函数默认 5 | 5 | `rag.py` L1550 |
| `cmd_search` 内部二次查询 | `args.k * 2`，结果截断回 `args.k` | 跟随入口 | `rag.py` L1413、L1416、L1426 |
| `验收/check_recall.py` 常规 | `-k 10` | **10** | `check_recall.py` L161–162、L181 |
| `验收/check_recall.py` 深诊断 | `-k 50`（`--kdiag` 默认 50） | **50** | `check_recall.py` L282、L296、L311、L848 |
| `catalog/work/audit_a.py` | 不传 `-k` | 5 | `audit_a.py` L30 |
| `catalog/check_gate.py` | `k=5` | 5 | `check_gate.py` L226 |
| `work/gap-detail-20261115/retrieval_diag.py` | `k=5` 与 `k=50` | 5 / 50 | `retrieval_diag.py` L33、L41 |
| `catalog/work/batch6_failed_list.py` | `k=5` | 5 | `batch6_failed_list.py` L51 |
| `catalog/work/batch6_rank_diag.py` | `k=10` | 10 | `batch6_rank_diag.py` L48 |

**结论**：**不存在全局唯一 Top-K，也不应强行定义**。已冻结的是分入口口径：生产检索与审计默认 5、验收 Recall 10、深诊断候选上界 50（`check_recall.py` L285–286 说明 sqlite-vec KNN LIMIT 4096 使 k 最大约 51）。U11 已裁决：Top-K 为入口级配置，按入口冻结，不要求全局唯一值；不修改任何调用入口。

### 2.3 其他参数：源码默认 / 运行时覆盖 / 实际有效值（A-03，只读）

| 参数 | 源码默认值 | 运行时覆盖方式 | 当前可确定有效值 | 证据 |
|---|---:|---|---|---|
| `SIM_FLOOR` | 0.66 | 环境变量 `RAG_SIM_FLOOR`；`search` 子命令 `--sim-floor`（`eval` 无此参数） | **0.66**（当前 shell）；其他 unknown | `rag.py` L57、L1766–1767、L1182 |
| `COVERAGE_FLOOR` | 0.32 | 仅 `RAG_COVERAGE_FLOOR` | **0.32** | `rag.py` L64、L806、L1183 |
| `SHORT_RELAX` | 0（关） | 仅 `RAG_SHORT_RELAX=1` | **0（关）** | `rag.py` L74、L100–115 |
| `ENTITY_GATE` | 0（关） | 仅 `RAG_ENTITY_GATE=1` | **0（关）** | `rag.py` L77、L1429 |
| `OOV_FLOOR` | 0.50 | 仅 `RAG_OOV_FLOOR` | **0.50** | `rag.py` L113、L1173 |
| `POOL_MIN` | 50 | 仅 `RAG_POOL` | **50** | `rag.py` L63、L1162 |
| `CROSS_PENALTY` | 0.9 | 仅 `RAG_CROSS_PENALTY` | **0.9** | `rag.py` L60 |
| `STRICT_ANSWER` | 0（关） | 仅 `RAG_STRICT=1` | **0（关）** | `rag.py` L72 |
| `EMBED_MODEL` | bge-m3 | 环境变量 `EMBED_MODEL` | **bge-m3**（Ollama 实际模型 `bge-m3:latest`，digest `790764…bab`） | `rag.py` L39；`/api/tags` |
| `EMBED_DIM` | 1024 | 无覆盖（硬编码） | **1024** | `rag.py` L40 |
| `EMBED_BATCH` | 32 | 无覆盖（硬编码） | **32** | `rag.py` L41 |

**结论**：「当前可确定有效值」都以「源码默认值 + 当前 shell 无 `RAG_*`」为前提；在外部 shell 或服务中注入环境变量的运行值，静态分析**无法确定**，继续标 unknown。

### 2.4 核验边界（A-03）

只读静态核验：未执行 `search`、`eval`、`ingest`、`rebuild`、`retag`、数据库迁移或索引重建；未修改 `rag.py`、`rag/README.md`、`eval/report.md` 或任何配置；未设置任何 `RAG_*` 环境变量。

### 2.5 A-04 用户裁决落档（U5 / U11）

**U5 `ANSWER_MIN_COVERAGE` 按运行分支冻结**（不把 0.50 与 0.40 裁决为二选一）：

| 条件 | 阈值行为 | 冻结说明 |
|---|---|---|
| `SHORT_RELAX=0`（源码默认，当前 shell 可观测） | `ANSWER_MIN_COVERAGE = 0.50` | 当前源码默认行为 |
| `SHORT_RELAX=1` | 动态阈值 0.22 / 0.30 / 0.36 / 0.40 | 以 `dynamic_cover_floor()` 实际逻辑为准（`rag.py` L94–115） |
| `RAG_ANSWER_MIN_COVERAGE` 环境变量 | 覆盖默认值 | 记录运行时环境覆盖；未观测到的外部环境不得猜测 |
| `rag/README.md` L132 / `eval/report.md` L11 的 0.40 | 历史文档口径 | 不冒充当前源码默认值 |

- 源码默认值：**0.50**。当前 shell 可观测值：**0.50**（无 `RAG_*` 变量）。外部运行环境未知值：**unknown**（不得猜测）。
- 后续实际执行（如批次 B/C 跑 eval）必须把当时环境变量、`SHORT_RELAX` 状态与最终有效阈值写入 Run Manifest。
- 未修改 `rag.py`、`rag/README.md`、`eval/report.md` 或任何参数。

**U11 Top-K 按入口冻结**（入口级配置，不是全局单值）：

| 入口 | Top-K |
|---|---:|
| CLI `search` 默认 | 5 |
| CLI `eval` 默认 | 5 |
| Python API `search()` / `fuse()` / `legacy_search()` 默认 | 5 |
| `check_recall.py` 常规 | 10 |
| `check_recall.py` 深诊断 | 50 |
| `retrieval_diag.py` | 5 / 50 |
| `batch6_rank_diag.py` | 10 |
| `audit_a.py` / `check_gate.py` / `batch6_failed_list.py` | 5 |

- 10 与 50 属验收/诊断脚本口径，**不得冒充生产检索默认值**；生产检索与审计默认 5。
- 未修改任何调用入口，不统一参数，不定义全局唯一 Top-K。

## 3. 评测与题集

| 项目 | 路径 | 数量 | SHA256 | 版本 |
|---|---|---:|---|---|
| 有答案评测题 | `04-知识底座/rag/eval/questions.jsonl` | 20 | `b295d2254389269cb91598f9710d58104eb576265b618c44c7bcf42298a249c8` | 无版本号 |
| 无答案评测题 | `04-知识底座/rag/eval/questions_negative.jsonl` | 12 | `1ee2c2adf90198cffd75d0b08b511bfe09f8c96c8853bf048e80c5880bcef833` | 无版本号 |
| 评测报告 | `04-知识底座/rag/eval/report.md` | — | `e42da380ed70920f6417faeb0eecd4febd37186a7adae1ebed1bc70a8ebf9f99` | 无版本号 |
| **240 题正式题库** | `04-知识底座/验收/题库/01…12-*.csv` | **240（12×20）** | 清单哈希 `161f9f55237975c74431d64d634d9e26792b519ea8f37be9a88996f2c95e4f7b` | 无版本号 |
| **60 条负集** | `04-知识底座/验收/负集.csv` | **60** | `7ac104a6fe078c6afa6410f0268cba31c0af3bb551ea97287eabe8f4fc9906f0` | 无版本号 |

**240 题集存在性证据**：`04-知识底座/验收/题库/` 下 12 个 CSV，每个 20 行数据（表头外），逐文件 `wc -l` 实测合计 240。A-01 报告「仓库内未发现 240 题」与 `knowledge-v2/RAG治理与评测方案.md`「未定位到原始题集」**均与实测不符**，以本表为准。

## 4. 数据库与运行态

| 项目 | 实测值 |
|---|---|
| 路径 / 大小 | `04-知识底座/rag/kbase.db` / 4,040,204,288 字节（3.76 GiB） |
| SHA256 | `40744a5fefedad80a1a4b78f4672345d7df3493fd7d4cad9b6b3a613cd6d7923` |
| 最后写入 | 2026-11-15 22:02:35（`docs.ingested_at` 最大值同） |
| WAL / SHM | WAL 0 字节；SHM 32KB |
| docs | 807 |
| segments | 536,707 |
| vectors（`seg_vec`） | 536,707 |
| terms | 89,210,727 |
| tags | 1,860 |
| graph nodes / edges | 217 / 318 |
| docs 质量分布 | 可引用 233 / 仅参考 550 / 不可引用 23 / 历史文本\|已废止 1 |
| Ollama | 进程运行中（pid 5645），`/api/tags` 正常返回 5 个模型 |
| bge-m3 | `bge-m3:latest`，digest `790764642607…2146bab`，1024 维，F16，可用；当前无常驻加载 |

## 5. 不可复现风险

1. 当前库 `docs` 表 CHECK 约束含 `不可引用`，HEAD `rag.py` 的 `SCHEMA` 为 `('可引用','仅参考','仅参考·可转述','历史文本|已废止')`；HEAD 的 `normalize_quality()`（第 605–613 行）会把未知档位归一为 `仅参考`。故**用 HEAD 代码 rebuild 无法重建当前库的质量分布**。
2. `docs` 807 条 > `metadata.csv` 776 条，差额来自目录扫描类入库；仅凭 metadata.csv 不能完整重建 docs 集合。
3. 历史成绩存在多套口径：`rag/README.md` 记 20 题 18/20、0/20、2/12；`eval/report.md` 记 15/20、3/20、5/12；240 题负集硬答在代码注释为 47/60、验收文档为 44/60。**均不得直接引用为当前基线**，需同代码指纹重跑后才能比较。

## 6. 本批次未执行项（明确声明）

未执行 `ingest`、`rebuild`、`eval`、`retag`、数据库迁移、索引重建；未修改 `rag.py`、README、评测文件或数据库；未统一任何参数或文档口径。
