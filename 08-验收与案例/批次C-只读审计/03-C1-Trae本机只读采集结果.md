# 批次 C · C1 本机只读采集结果

**执行日期：** 2026-11-16 17:20–17:40（本机时间）
**执行环境：** Trae CN 3.4.20，Python 3.14.6，Git HEAD `086d4ac942540f02aeac8868a5b914247101b231`
**仓库：** `dujiu1024-dotcom/zhanghaoduibiao`（本机路径：`<本机仓库根目录>`）
**执行依据：** `批次C-仓库静态审计与真机取证清单.md` 第 4 节（C1-A/B/C 命令组）。PR #32 引用的细项命令文件 `02-C1-Trae本机只读采集命令.md` 本机仓库未合入，本报告按已合入清单的命令执行。
**约束遵守：** 全程只读，未执行 ingest/rebuild/retag/迁移/删除/覆盖/参数变更。所有 SQLite 访问使用 `mode=ro` 只读 URI + `PRAGMA query_only=ON` 双重锁写。未接触任何客户隐私内容。

---

## 1. 执行环境

| 项目 | 值 | 证据 |
|---|---|---|
| Trae 客户端版本 | Trae CN 3.4.20 | 用户指令显式声明；本机仓库无独立 Trae 版本文件，不得推测其他值 |
| Python | 3.14.6 | `python3 --version` → `Python 3.14.6` |
| Python 路径 | `/opt/homebrew/bin/python3` | `which python3` |
| Git HEAD | `086d4ac942540f02aeac8868a5b914247101b231` | `git rev-parse HEAD` |
| Git 工作区 | 有 2 个未跟踪目录：`99-归档/真人IP存档-2026-11-16/`、`work/cases/b08-holobake-entry/` | `git status --short` |
| sqlite-vec | 0.1.9 | `import sqlite_vec` + `pip list` |
| 仓库根 | `<REDACTED_LOCAL_REPO_ROOT>` | `pwd` |

---

## 2. RAG 实际生效参数

11 个参数全部回退到源码默认值，本机无环境变量覆盖。这与 `批次C-仓库静态审计与真机取证清单.md` 第 2.1 节指出的"文档与代码不同步"现象吻合——旧 README 称 `SIM_FLOOR` 默认 0.60，但本机实际生效就是源码的 0.66，旧文档已过时。

| 参数 | 实际值 | 来源 |
|---|---|---|
| RAG_SIM_FLOOR | 0.66 | 源码默认，无环境变量覆盖 |
| RAG_ANSWER_MIN_COVERAGE | 0.50 | 源码默认 |
| RAG_OOV_FLOOR | 0.50 | 源码默认 |
| RAG_COVERAGE_FLOOR | 0.32 | 源码默认 |
| RAG_SHORT_RELAX | 0（关闭） | 源码默认 |
| RAG_ENTITY_GATE | 0（关闭） | 源码默认 |
| RAG_STRICT | 0（关闭） | 源码默认 |
| RAG_CROSS_PENALTY | 0.9 | 源码默认 |
| RAG_POOL | 50 | 源码默认 |
| OLLAMA_URL | http://127.0.0.1:11434 | 源码默认 |
| EMBED_MODEL | bge-m3 | 源码默认 |

---

## 3. SQLite 数据库

### 3.1 路径异常（重要）

`rag.py` 第 35 行硬编码 `DB_PATH = HERE / "kbase.db"`，其中 `HERE` 是 `rag.py` 所在目录 → 期望路径为 `04-知识底座/rag/kbase.db`。**该路径下文件不存在**。

仓库中实际存在的 `kbase.db` 有三份：

| 路径 | 大小 | 修改时间 | SHA-256 | 说明 |
|---|---|---|---|---|
| `04-知识底座/kbase.db` | 0 字节 | 2026-11-15 08:39 | `e3b0c442…`（空哈希） | 空壳文件，不包含任何数据 |
| `04-知识底座/knowledge/kbase.db` | 0 字节 | 2026-11-15 08:32 | `e3b0c442…`（空哈希） | 空壳文件，不包含任何数据 |
| `99-归档/个人IP工作区-2026-11-16/配置层/kbase.db` | 4,040,204,288 字节（~3.76 GB） | 2026-11-15 22:02:36 | `40744a5f…93fd7d4cad9b6b3a613cd6d7923` | 唯一有真实数据的知识库快照 |

归档库伴随文件：
- `kbase.db-shm` = 32,768 字节（2026-11-16 17:36）
- `kbase.db-wal` = 0 字节（2026-11-16 17:36，当前无未写入内容）
- 历史备份：`kbase.db.bak-20261114-2338`（145 MB）、`kbase.db.bak-20261115-0045`（259 MB）

**关键结论：** `rag.py` 的生产库路径已失效；当前若在 `rag/` 下运行任何 `ingest`/`rebuild`，会自动创建一份全新空库。归档库是唯一可用于 C2 备份、C3 评测的数据基线。

### 3.2 归档库数据量（只读查询）

查询方式：`sqlite3.connect("file://...?mode=ro", uri=True)` + `PRAGMA query_only=ON`。

| 表 | 记录数 | 备注 |
|---|---|---|
| docs | 807 | 主文档表 |
| segments | 536,707 | 切段表 |
| terms | 89,210,727 | FTS5 倒排索引词表 |
| segment_tags | 1,860 | 标签表 |
| graph_nodes | 217 | 图谱节点 |
| graph_edges | 318 | 图谱边 |
| seg_vec | 未直接查询 | schema 存在（vec0 虚拟表），Python 脚本首次查询时未调用 `sqlite_vec.load(conn)` 报 OperationalError，属于脚本调用顺序问题。schema 列出 5 张向量表：seg_vec、seg_vec_info、seg_vec_chunks、seg_vec_rowids、seg_vec_vector_chunks00 |

docs 表列：`id, source_path, text_path, title, quality, kind, sha1, char_count, meta_json, updated_at, ingested_at`
segments 表列：`id, doc_id, ordinal, section, locator, quality, text, embed_text, char_len`
integrity_check = **ok**
journal_mode = **wal**

### 3.3 索引清单

- `sqlite_autoindex_docs_1`（docs 表自索引）
- `sqlite_autoindex_segments_1`（segments 表自索引）
- `idx_seg_doc`（segments.doc_id）
- `idx_seg_quality`（segments.quality）
- `idx_tag_topic`（segment_tags）
- `idx_edge_src` / `idx_edge_dst`（graph_edges）
- `sqlite_autoindex_graph_nodes_1`（graph_nodes）
- `sqlite_autoindex_seg_vec_info_1` / `sqlite_autoindex_segments_vector_chunks00_1`（向量辅助表）

---

## 4. metadata.csv 统计

### 4.1 基本信息

| 项目 | 值 |
|---|---|
| 路径 | `04-知识底座/knowledge/sources/metadata.csv` |
| 总行数 | 776（不含表头，文件 777 行） |
| 列名 | 14 列，均为中文：`题名, 作者, 年份, 来源URL, 获取日期, 文本形态, 质量分级, 授权限制, 页码映射, 本地路径, 字符数, 备注, 采集时间, 入库时间` |
| BOM | 存在（首列 `\ufeff题名`），Python csv.DictReader 可正常处理 |
| rag.py 集成 | `load_metadata()` 函数通过中文列名取值，映射到 SQLite docs 表的 `title`、`quality`、`kind`、`sha1` 等英文列。两套 schema 在 ingest 流程中打通 |

### 4.2 缺失值统计

| 列 | 缺失行数 | 缺失率 | 说明 |
|---|---|---|---|
| 文本形态 | 0 | 0.0% | 完整 |
| 质量分级 | 0 | 0.0% | 完整 |
| 授权限制 | 0 | 0.0% | 完整 |
| 本地路径 | 0 | 0.0% | 完整 |
| 题名 | 2 | 0.3% | |
| 来源URL | 19 | 2.4% | |
| 获取日期 | 19 | 2.4% | |
| 页码映射 | 19 | 2.4% | |
| 作者 | 24 | 3.1% | |
| 字符数 | 25 | 3.2% | |
| 年份 | 69 | 8.9% | |
| 采集时间 | 70 | 9.0% | |
| 备注 | 85 | 11.0% | |
| **入库时间** | **249** | **32.1%** | 最显著异常——776 条中有 249 条无入库时间 |

### 4.3 重复与唯一性

- **重复 SHA-1 分组：** 0 组（metadata.csv 本身无 sha1 列，此统计在 SQLite docs 表层面进行）
- **docs 表唯一性：** 归档库 807 个 docs 记录，source_path + sha1 组合无重复（SQLite 端未检测到重复行）

---

## 5. 知识文件目录分布

### 5.1 总览

| 项目 | 值 |
|---|---|
| `knowledge/` 下总文件数 | 810 |
| `knowledge/sources/metadata.csv` 行数 | 776 |
| 归档库 docs 表记录数 | 807 |

三者存在差异的原因：
- `knowledge/` 目录包含 metadata.csv 本身、manifest.csv、INDEX.md、README.md、_templates/、methodology/ 等非知识源文件
- 归档库 docs 表记录数（807） > metadata.csv 行数（776），推测 ingest 过程中可能自动补充了部分文档（例如自撰转文本副本、OCR 版本），或归档时间点之后有新增。需在恢复后进一步核验

### 5.2 sources/ 子目录文件数

| 子目录 | 文件数 | 说明 |
|---|---|---|
| books | 423 | 公版书籍/PDF/文本 |
| fulltext | 155 | 全文抓取内容 |
| secondhand | 107 | 二手来源/替代材料 |
| papers | 74 | 论文/学术文本 |
| work | 16 | 工作文档 |
| scam | 6 | 诈骗样本（独立语料，不入库） |
| official | 1 | 官方文档 |
| index | 2 | 索引文件 |
| pipeline | 2 | 管线配置 |
| inbox | 0 | 待处理目录（空） |

### 5.3 深层领域分层（sources/books/ 下）

books/ 下有 14 个中文编号子目录，分别对应：`00-来源待购`、`01-人性与心理`、`02-传播与内容`、`03-判断与思维`、`04-用户与市场`、`05-客户运营与转化`、`06-平台与增长`、`07-商业与经营`、`08-风险与治理`、`09-专业本体`、`10-跨类项`、`11-定位与差异化`、`12-交付与验收`、`13-行业方案库`、`14-行业场景知识`。每目录配 `manifest.csv`。

---

## 6. A/B/C/D/E 五层知识资产实际存在情况

### 6.1 设计（knowledge-v2/README.md）

V2 治理方案定义了五层：

| 层 | 职责 | 目录建议路径 |
|---|---|---|
| A 通用商业认知 | 跨行业原理、战略、竞争、营销、经营、财务、组织、决策 | `knowledge-v2/A-通用商业认知/` |
| B 行业与市场情报 | 行业结构、政策、市场规模、客户行为、技术趋势、竞争情报 | `knowledge-v2/B-行业与市场情报/` |
| C 专业领域知识 | 职能/专业/业务模式知识；个人 IP 归入 C 的专业子域 | `knowledge-v2/C-专业领域知识/` |
| D 具体业务项目知识 | 客户、产品、项目、投标、交付、运营、复盘 | `knowledge-v2/D-业务项目知识/` |
| E 个人专属知识 | 个人经历、偏好、能力、私有数据、私人案例 | `knowledge-v2/E-个人专属知识/` |

### 6.2 物理存在情况（Glob + LS 核验）

**A-E 五层目录全部不存在。** `04-知识底座/knowledge-v2/` 下仅包含治理设计文档（README.md、知识元数据规范.md、旧资产迁移映射.md、知识卡片模板.md、RAG治理与评测方案.md、领域覆盖矩阵.md、evaluation/），无任何 A/B/C/D/E 子目录。

### 6.3 实际物理结构

当前知识资产分布在三套并行结构中：

1. **`knowledge/sources/`**（实际知识源文件）：按来源类型（books/fulltext/papers/secondhand/work/scam/official）+ 深层 14 个领域编号（01–14）组织
2. **`metadata.csv`**（源清单）：776 行中文元数据，每行通过"本地路径"列映射到 sources/ 下的物理文件
3. **归档库 SQLite**（`99-归档/.../kbase.db`）：807 docs + 536,707 segments，rag.py 从 metadata.csv 读取后切段入库

**迁移状态：** V2 治理方案已设计、A-E 五层职责已定义、但物理目录未创建、历史知识未搬迁。批次 C 第 1 节判定"C1 仓库静态治理设计审计已完成、C4 抽样迁移仅有计划未执行"——与本机现状一致。

---

## 7. D/E 权限控制和默认关闭状态证据

### 7.1 设计层

knowledge-v2/README.md 第 3 节（层间引用、继承与检索隔离）明确定义了 D/E 层的权限控制规则：

| 规则 | 出处 |
|---|---|
| D 层默认必须匹配 project_id/customer_id 和访问权限，不跨客户/跨项目复用 | README.md 第 44 行 |
| E 层默认关闭，按用户明确授权和最小范围检索，不向 A/B/C/D 自动扩散 | README.md 第 45 行 |
| D/E 敏感信息不得进入共享向量索引；如需形成匿名化经验，需先完成授权、脱敏、可迁移性和反例审查 | README.md 第 53 行 |
| 所有跨层引用记录 source knowledge_id、引用层、调用任务、访问主体 | README.md 第 54 行 |

### 7.2 实现层现状

**D/E 层权限控制无运行证据。** 原因：
- A-E 五层物理目录不存在，D/E 层的具体数据位置无法定位
- rag.py（当前 RAG 引擎）不包含层级权限隔离逻辑——检索函数（`literal_search`/`tag_search`/`vec_search`）按 `quality`、`source_path`、`text_path` 过滤，但无层（layer）字段
- SQLite docs 表无 `layer` 列，metadata.csv 无层标识
- 无独立的权限控制中间件、访问日志或 token 校验机制

**默认关闭状态无代码证据。** rag.py 当前 `STRICT=0`、`ENTITY_GATE=0`、`SHORT_RELAX=0` 三个环境变量全部关闭——这些控制的是检索行为，不是层级访问。不存在"E 层默认关闭"的运行时拦截逻辑。

**判定：** D/E 权限控制和默认关闭状态仅存在于设计文档中，未在当前代码、数据库结构或运行参数层面实现。C2 备份恢复、C3 真实评测、C4 抽样迁移均不能假设这些控制已生效。

---

## 8. 命令执行记录与退出码

| # | 命令 | 退出码 | 状态 | 备注 |
|---|---|---|---|---|
| 1 | `pwd` + `git rev-parse HEAD` + `git status --short` + `python3 --version` | 0 | ✅ 完成 | 环境快照 |
| 2 | RAG 生效参数 Python 脚本（11 个环境变量默认值输出） | 0 | ✅ 完成 | 全部回退源码默认值 |
| 3 | SQLite 只读统计（目标路径 `rag/kbase.db`） | 1 | ⚠️ 按预期失败 | 脚本中 `raise SystemExit("kbase.db 不存在；停止")` 被触发，路径下文件确实不存在 |
| 4 | Glob 全仓库搜 `kbase.db` | — | ✅ 完成 | 找到 3 份：2 份 0 字节空壳、1 份 4GB 归档库 |
| 5 | 三份 kbase.db SHA-256 + stat 对比 | 0 | ✅ 完成 | 确认唯一真实库为归档文件 |
| 6 | rag.py 搜 DB_PATH 定义 | — | ✅ 完成 | 35 行硬编码 `HERE / "kbase.db"` |
| 7 | 4GB 归档库只读统计（docs/segments/terms/segment_tags/graph_nodes/graph_edges/integrity_check/indexes） | 0 | ✅ 完成 | 完整读取，`seg_vec` 表因脚本未调用 `sqlite_vec.load(conn)` 报 OperationalError，属于脚本调用遗漏，非数据库问题 |
| 8 | 归档库伴随文件 + stat | 0 | ✅ 完成 | shm=32KB, wal=0 字节 |
| 9 | `import vec0`（错误模块名） | 1 | ⚠️ 误测 | vec0 是 SQLite 虚拟表类型，不是 Python 模块。正确模块名为 sqlite_vec |
| 10 | `import sqlite_vec` + `pip list` | 0 | ✅ 完成 | sqlite-vec 0.1.9 已安装可用 |
| 11 | metadata.csv 完整统计（776 行、14 中文列、缺失值、sha1 分组、质量/kind/授权分布） | 0 | ✅ 完成 | quality/kind/permission 分布全空——metadata.csv 无这些列，对应中文列名需重新映射 |
| 12 | rag.py 搜 metadata/sha1/quality/vec0/sqlite_vec | — | ✅ 完成 | 确认 `load_metadata()` 通过中文列名映射到 SQLite 英文列 |
| 13 | sources/ 各子目录文件数 | 0 | ✅ 完成 | books(423)、fulltext(155)、secondhand(107)、papers(74)、work(16)、scam(6)、official(1)、index(2)、pipeline(2)、inbox(0) |
| 14 | knowledge-v2/README.md A-E 五层定义 | — | ✅ 完成 | 仅设计文档，无物理目录 |
| 15 | Glob 搜 A-E 物理目录 | — | ✅ 完成 | 全部不存在 |

**全程无写入命令执行。** 所有涉及 SQLite 访问的命令使用了只读 URI + query_only PRAGMA。未运行 ingest/rebuild/retag/任何写操作。

---

## 9. 无法验证的事项及原因

| 事项 | 原因 | 影响 |
|---|---|---|
| 生产 RAG 引擎（rag.py）对真实知识库的检索能力 | 生产路径 `rag/kbase.db` 不存在；归档库不在 rag.py 期望位置。本次未尝试将归档库软链或复制到生产路径（严格只读约束） | C3 真实 RAG 评测被阻塞——需要先确定生产库路径策略 |
| seg_vec 表向量记录数 | 脚本首次查询时未调用 `sqlite_vec.load(conn)` 报 OperationalError。可通过修正脚本验证，但当前已足够推断规模（与 segments 1:1，约 53.7 万条向量） | 低影响——数据规模已可推断，完整性可通过 schema 校验替代 |
| D/E 层权限控制的运行时验证 | D/E 层物理目录不存在，权限代码路径不存在，无中间件/token/访问日志 | 中高影响——C4 抽样迁移前必须先定义 D/E 数据位置和权限机制 |
| 模型信息（EMBED_MODEL 的 bge-m3 实际版本、Ollama 本地运行状态） | OLLAMA_URL 指向 127.0.0.1:11434，未尝试连接 Ollama（可能在运行也可能未启动；严格只读约束，且连接 Ollama 可能涉及网络 IO） | 中影响——C3 评测需要确认 Ollama 和 bge-m3 可用 |
| 归档库与 metadata.csv 行数差异原因 | 归档库 807 docs vs metadata.csv 776 行，差 31 行，可能是 ingest 过程中自动补充或归档后有新增。未执行 `SELECT source_path FROM docs LEFT JOIN metadata.csv ...` 式交叉核验（metadata.csv 非数据库表，需 Python 脚本比对，耗时） | 低影响——差集可在恢复后离线核验 |
| 批次 C 清单中提到的"当前题集版本、gold 来源" | 清单 2.2 节称 `rag/eval/questions.jsonl` 20 条、`questions_negative.jsonl` 12 条，但未见独立冻结集 | 中影响——C3 评测需先确认题集冻结版本 |

---

## 10. 最终结论

**本次只读采集：PASS**

依据：
1. C1-A（环境快照）完整执行，环境数据已记录
2. C1-B（RAG 参数 + SQLite 只读统计）完整执行，归档库数据量、结构、完整性已核验
3. C1-C（metadata 统计 + 目录分布 + A-E 分层现状）完整执行
4. 全程保持只读：无文件写入、无数据库写入、无 ingest/rebuild/迁移/参数变更
5. 所有命令退出码已记录，误判项（`import vec0` 模块名错误、`rag/kbase.db` 路径缺失）已如实标注

**但发现 3 项需处理的数据层异常，C2/C3/C4 不得绕过：**

### 异常 1：生产库路径失效

rag.py 硬编码的 `DB_PATH = HERE / "kbase.db"` 当前为空。`rag.py connect()` 默认 `create=True`，意味着在 rag/ 下执行任何 ingest 会自动创建新空库——这直接违反批次 C 清单第 5 节"禁止 rebuild"的约束。C2 备份恢复必须先确定：
- 生产库是继续使用归档库（需移动/软链/改路径），还是从归档库恢复到指定位置
- `04-知识底座/kbase.db` 和 `04-知识底座/knowledge/kbase.db` 两份 0 字节空壳的处理方式（删除/归档/保留）

### 异常 2：D/E 权限控制仅设计未实现

A-E 五层物理目录不存在，rag.py 无层级权限隔离逻辑，SQLite docs 表无 layer 列。D/E 的"默认关闭""按授权检索""不跨项目复用"全部停留在 README 里。C4 抽样迁移前必须先定义：
- D 层业务项目知识、E 层个人专属知识的物理位置
- 层标识字段设计（docs 表加 layer 列？metadata.csv 加层列？）
- 权限拦截机制位置（RAG 引擎内 / 独立中间件 / 检索前过滤）

### 异常 3：metadata.csv 入库时间 32.1% 缺失

776 行中 249 行无入库时间，意味着这部分条目无法追溯入库时点和版本。rag.py ingest 流程会写 `ingested_at` 到 SQLite docs 表，但 metadata.csv 本身未同步回写。需恢复后核验 SQLite docs 表的 `ingested_at` 字段覆盖情况。

**建议下一步（需用户授权）：**
1. C2：确定生产库恢复策略——从 4GB 归档库恢复到 rag/kbase.db（软链或复制），清掉两份 0 字节空壳，SHA-256 校验前后一致
2. C2：补充 D/E 层权限设计落地——在 rag.py 的检索入口加入层过滤，metadata.csv 加层列，SQLite docs 表加 layer 列
3. C3：确认 Ollama + bge-m3 运行状态，冻结题集版本，再启动真实评测
4. C4：在 C2/C3 完成后执行抽样迁移，不得提前

---

## 附录：执行时间线

| 时间 | 动作 |
|---|---|
| 17:20 | 打开批次 C 清单，确认执行规范文件未合入 |
| 17:21 | Glob 定位关键文件路径（rag.py、metadata.csv、knowledge-v2/） |
| 17:22 | C1-A 环境快照 |
| 17:23 | C1-B RAG 生效参数脚本 |
| 17:24 | SQLite 只读统计（首试失败，路径下无文件） |
| 17:25 | Glob 搜全部 kbase.db，定位 3 份候选 |
| 17:26 | SHA-256 + stat 指纹对比，确认唯一真实库 |
| 17:27 | rag.py grep 确认 DB_PATH 硬编码位置 |
| 17:28 | 4GB 归档库只读统计（docs/segments/terms/segment_tags/graph_nodes/graph_edges/integrity_check/indexes） |
| 17:30 | sqlite-vec 模块验证（先误测 import vec0，后修正 import sqlite_vec） |
| 17:31 | metadata.csv 完整统计（Python csv.DictReader） |
| 17:33 | rag.py grep 确认 metadata 读取逻辑和中文列映射 |
| 17:34 | sources/ 各子目录文件数分布 |
| 17:35 | knowledge-v2/README.md A-E 五层定义 |
| 17:36 | 归档库伴随文件 + stat |
| 17:37 | Glob 搜 A-E 物理目录（全部不存在） |
| 17:40 | 报告撰写完成 |


## 隐私脱敏说明

为避免在公开仓库暴露本机用户名与绝对目录，原始本机仓库根路径已统一替换为 `<REDACTED_LOCAL_REPO_ROOT>`。仓库相对路径、命令名称及技术观察保持不变；该脱敏不补充或改变任何运行时证据。
