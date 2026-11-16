# 05 · RAG 基线与差异核验

- 生成时间：2026-11-16 10:20（CST）
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
| `ANSWER_MIN_COVERAGE` | **0.50** | **0.40**（参数表） | 0.4（`eval/report.md`） | **待确认（代码 0.50 / 文档 0.40 冲突）** | `rag.py` 第 70 行；README；eval 报告 |
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
| Top-K 展示条数 | 由调用方 `k` 决定 | 默认 5/10 | 5/10 | **待确认（未在配置中冻结）** | `rag.py` 命令参数 |
| 重排模型 | 无实现 | 未提 | 未提 | **N/A（仓库无重排）** | 代码无 rerank 模块 |

**冻结结论**：当前只可冻结「代码默认值 + 库哈希」这一事实基线；`ANSWER_MIN_COVERAGE` 因代码 0.50 与 README 0.40 冲突，**不得自行统一**，标为待确认。`knowledge-v2/README.md` 称「代码默认 `SIM_FLOOR=0.60`」与 HEAD 实测 0.66 不符，标为过期文档。

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
