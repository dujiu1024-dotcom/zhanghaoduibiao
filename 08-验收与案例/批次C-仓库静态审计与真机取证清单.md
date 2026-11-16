# 阶段 8 批次 C｜仓库静态审计与真机取证清单

审计日期：2026-11-16  
范围：Git 仓库中可见的知识治理文档、RAG 源码、评测资产与历史清点记录。  
性质：只读静态审计；**不代表已访问用户本机数据库，不代表完成备份恢复或真实 RAG 评测。**

## 1. 已核验的仓库资产

| 资产 | 仓库可见状态 | 证据与边界 |
|---|---|---|
| A-E 知识分层 | 已定义 | `04-知识底座/knowledge-v2/README.md` |
| 元数据规范 | 已定义 | `知识元数据规范.md`，含来源、定位、授权、核验、时效、敏感级别等字段 |
| 知识卡片模板 | 已定义 | `知识卡片模板.md`，schema_version v2.1 |
| 领域覆盖矩阵 | 已定义 | `领域覆盖矩阵.md`，14 个一级领域，C0-C5 成熟度 |
| 旧资产迁移映射 | 已定义，未证明迁移完成 | `旧资产迁移映射.md` 明确原件保留、逐篇审计、分批迁移 |
| RAG 评测规范 | 已定义 | `RAG治理与评测方案.md` |
| 评测模板 | 仅格式示例 | `evaluation/question-template.jsonl` 只有 2 条 template_only 示例 |
| 正向/负向历史题集 | 仓库可见 | `rag/eval/questions.jsonl` 20 条；`questions_negative.jsonl` 12 条；不是独立保留集 |
| 本机 RAG 引擎 | 仓库可见 | `04-知识底座/rag/rag.py`；运行依赖 SQLite、sqlite-vec、Ollama/bge-m3 |
| 本机数据库 | 仓库说明指向本地文件 | `04-知识底座/rag/kbase.db`；本次未读取该文件 |

## 2. 当前已知的仓库侧风险与不一致

### 2.1 RAG 参数文档与代码不同步

静态读取 `rag.py` 可见默认值（环境变量未覆盖时）：

- `SIM_FLOOR = 0.66`
- `ANSWER_MIN_COVERAGE = 0.50`
- `OOV_FLOOR = 0.50`
- `COVERAGE_FLOOR = 0.32`
- `SHORT_RELAX` 默认关闭
- `ENTITY_GATE` 默认关闭
- `STRICT_ANSWER` 默认关闭

但 `knowledge-v2/README.md` 的阶段 7 静态复核段仍称 `SIM_FLOOR` 默认值为 0.60；`RAG治理与评测方案.md` 对答案覆盖率的历史描述仍有 0.40 口径。旧 `rag/README.md` 还保留历史阈值扫描与 20+12 题结果。

**处理要求：** 真机取证时记录环境变量覆盖后的实际生效值；先确认当前运行参数，再统一文档。不得只按文档推断运行值。

### 2.2 历史成绩不可作为当前基线

仓库同时出现 20 条正向 + 12 条负向历史题集，以及源码注释中的 240/60 历史评测口径。它们的题集、标注和运行版本并未在当前仓库中形成可直接比较的统一基线。旧 README 自述 20+12 集是在读过语料后编写，且阈值在这两组上选择，存在过拟合风险。

因此：
- 历史分数只作历史记录，不得记为本批次 C 的 PASS；
- 20+12 题集不能冒充独立保留集；
- 当前正式评测前必须冻结题集版本、知识库快照、代码提交、模型与参数；
- 独立保留集不得参与调参、索引调试或整改反馈。

### 2.3 仓库侧知识清点只是历史快照

`catalog/2026-11-15-藏量清点.md` 记录了 2026-11-15 约 03:00 的只读快照：474 docs、131,793 segments、431 条 metadata、64 个无 metadata 文档、42 组重复文档。该文件自身说明这是当时的清点结果，不代表 2026-11-16 当前数据库状态。

### 2.4 元数据与索引质量风险

历史清点报告记录 11 篇资料存在 metadata 质量档与库内档位不一致；同时 93 份自撰转文本副本与 65 份自撰件重复。它们是待复核风险，不授权本轮直接修改或去重。

## 3. C1-C4 当前判定

| 子项 | 当前结论 | 原因 |
|---|---|---|
| C1 仓库静态治理设计审计 | 已完成（仅仓库可见范围） | A-E、元数据、覆盖矩阵、迁移映射、RAG 方案均已读取 |
| C1 本机知识资产/权限/索引现状 | NOT_VERIFIED | 未访问用户本机文件系统、数据库和 Trae 环境 |
| C2 备份与隔离恢复 | BLOCKED / NOT_VERIFIED | 未取得当前数据库快照、备份校验与隔离恢复证据 |
| C3 当前 RAG 真实评测 | NOT_VERIFIED | 历史题集不是独立保留集；本轮未运行本机 RAG |
| C4 抽样迁移 | 仅有计划，未执行 | 不得在未备份、未恢复验证、未获用户授权前写库或迁移 |

## 4. Trae CN 3.4.20 只读取证任务

以下任务仅采集状态，不执行 ingest、rebuild、retag、迁移、删除、覆盖或参数变更。运行前确认终端位于项目仓库根目录。

### C1-A：环境与工作区快照

```bash
pwd
git rev-parse HEAD
git status --short
python3 --version
```

记录 Trae 客户端版本页面；若界面没有暴露版本，原样记录 `unknown_not_exposed`，不要推测。

### C1-B：RAG 只读统计与参数

先记录实际生效配置（值可能被环境变量覆盖）：

```bash
cd "04-知识底座/rag"
python3 - <<'PY'
import os
for k, default in {
    "RAG_SIM_FLOOR": "0.66",
    "RAG_ANSWER_MIN_COVERAGE": "0.50",
    "RAG_OOV_FLOOR": "0.50",
    "RAG_COVERAGE_FLOOR": "0.32",
    "RAG_SHORT_RELAX": "0",
    "RAG_ENTITY_GATE": "0",
    "RAG_STRICT": "0",
    "RAG_CROSS_PENALTY": "0.9",
    "RAG_POOL": "50",
    "OLLAMA_URL": "http://127.0.0.1:11434",
    "EMBED_MODEL": "bge-m3",
}.items():
    print(f"{k}={os.environ.get(k, default)}")
PY
```

数据库统计采用 SQLite 只读模式；该脚本不创建表、不写入数据库：

```bash
python3 - <<'PY'
import sqlite3
from pathlib import Path
p = Path("kbase.db").resolve()
print("db_exists=", p.exists())
if not p.exists():
    raise SystemExit("kbase.db 不存在；停止，不要自动 rebuild")
uri = p.as_uri() + "?mode=ro"
con = sqlite3.connect(uri, uri=True)
con.execute("PRAGMA query_only=ON")
for table in ("docs", "segments", "terms", "segment_tags", "graph_nodes", "graph_edges", "seg_vec"):
    try:
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}_count={n}")
    except Exception as e:
        print(f"{table}_error={type(e).__name__}: {e}")
print("docs_columns=", [r[1] for r in con.execute("PRAGMA table_info(docs)")])
print("segments_columns=", [r[1] for r in con.execute("PRAGMA table_info(segments)")])
con.close()
PY
```

同时记录数据库文件大小、修改时间、SHA-256，以及同目录 `kbase.db-wal`、`kbase.db-shm` 是否存在。只记录，不删除、不移动、不复制活动数据库文件。

### C1-C：元数据与重复项抽样

只读检查 metadata 行数、字段完整率、质量档差异、缺少 metadata 的文档、重复 SHA-1 分组。抽样至少覆盖 A/B/C/D/E 候选层，并记录每条样本的原路径、来源、权限/授权证据、时效、质量档、核验状态。不要把个人/客户内容复制进仓库报告；只提交脱敏统计和不可识别的样本编号。

### C2：备份与恢复准备（本轮不执行）

先提交备份方案，明确数据库、WAL/SHM、metadata、原始知识文件、索引配置、模型依赖和环境变量的范围；确定一致性备份方法、SHA-256 校验、隔离恢复目录、恢复前后统计对照与回滚步骤。**未经用户明确授权，不创建备份副本、不执行恢复、不触碰生产库。**

### C3：评测准备（本轮不启动正式评测）

先核实当前题集版本、gold 来源/定位、脚本版本、模型、参数与数据库快照。将现有 20+12 题标为历史开发集候选；不得将其称为 holdout。另行建立由非调参流程保管的独立保留集，冻结后才可执行正式评测。评测至少包含正向召回、负向拒答、相似干扰/过期/冲突对抗、引用准确性和权限隔离；逐题保存原始召回、引用、输出与人工评分。

## 5. 明确禁止的命令

在用户授权和 C2 门禁通过前，不运行：

- `rag.py ingest`
- `rag.py rebuild`
- `rag.py retag`
- 任何数据库写入 SQL、批量删除、覆盖或迁移脚本
- 任何改变生产检索参数、索引或知识库配置的操作

## 6. 回传材料

请回传脱敏后的：
1. C1-A 环境快照；
2. C1-B 实际生效参数、只读数据库统计、文件指纹；
3. C1-C 分层抽样和元数据异常汇总；
4. C2 备份/恢复方案（不含私密内容）；
5. 当前题集与模型/参数/代码版本盘点。

**本文件只完成仓库静态审计与执行协议准备。C1 本机审计、C2 备份恢复、C3 当前真实评测和 C4 迁移均不得据此宣称完成。**
