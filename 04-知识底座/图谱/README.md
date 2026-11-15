# 知识图谱 · FDE 抖音账号

把 `knowledge/` 里的概念抽成节点、关系抽成边，标出证据等级和缺口，生成一张可以离线打开的单页图。

- 看图：`index.html`（双击即开，不联网、不构建）
- 数据：`graph.json`
- 决策记录：`决策使用记录.md`
- 重跑：`python3 work/extract.py`

当前规模：65 篇文档、217 个节点、318 条边。其中缺口 2 个、主动判不适用 1 个。

## 目录

```
图谱/
├── README.md                 # 本文件
├── graph.json                # 机器可读：节点、边、层级统计、元信息
├── index.html                # 单文件网页：图谱数据已内嵌
├── 决策使用记录.md            # 用图谱做决定的记录（六类决策、三档判定）
└── work/
    ├── curated_nodes.py      # 人工复核过的节点与边（唯一事实来源）
    ├── expected.py           # 六层「应有清单」，用来发现空缺
    ├── evidence_map.py       # 证据分级：哪些能对外引用
    ├── template.html         # 网页模板，构建时填入数据
    ├── extract.py            # 构建脚本
    ├── proposals.json        # 每次构建的差异报告（新增/消失/待复核/候选）
    └── reviewed.json         # 已复核文档的指纹（跑 --ack 后生成）
```

`graph.json` / `index.html` 是产物，可以随时删掉重建；要改内容，改 `work/` 下的三份清单。

## 重跑步骤

知识库有新增或修改后：

```bash
cd 04-知识底座/图谱/work

# 1. 先看差异，不写文件
python3 extract.py --check

# 2. 按报告补节点/边/证据分级（见下一节）

# 3. 正式生成 graph.json 与 index.html
python3 extract.py

# 4. 复核完变更后，把当前文档指纹记为已复核
python3 extract.py --ack
```

`--check` 会打印：

- **新增节点 / 消失节点**：和上一次 `graph.json` 比，哪些 id 新出现、哪些没了。
- **文档改过、节点待复核**：文档内容指纹（sha1）变了，但节点还没跟着改。复核后跑 `--ack` 消除提醒。
- **有文档但没有节点**：`methodology/`、`topics/`、`monetization/` 下没有任何节点引用的文档。
- **未匹配的小节**：节点数少于 3 的文档里，标题没有对上任何节点标签的段落，写进 `proposals.json`，当作补节点的候选。

构建失败（例如边端点不存在、status 非法）时不会写文件，直接报错退出。

## 新文档进来后怎么补

### 1. 登记文档路径

在 `work/curated_nodes.py` 顶部加一个常量，路径相对 `knowledge/`：

```python
DNEW = "methodology/L2-新文档.md"
```

构建时会自动读取它的最后修改时间和内容指纹，写进每个引用它的节点。文档不存在会直接报错。

### 2. 加节点

三类节点各一个 helper，签名一致：`id, label, layer, definition, ...`。

```python
# 理论 / 模型：必须尽量给出处
T("theory-new", "新理论", "layer-trusted",
  "一句话定义，写清它解释什么、不解释什么。",
  "作者, 年份", DNEW, "对应小节标题")

# 动作：doc/section 指向具体做法所在处
A("a-new", "新动作", "layer-trusted",
  "具体做什么，做到什么程度。", DNEW, "对应小节标题")

# 指标：写清口径，拿不到就标 status=MENTIONED 或 UNVERIFIED
M("m-new", "新指标", "layer-closed",
  "这个数怎么算、从哪看。", DNEW, "对应小节标题")
```

字段说明：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `id` | 是 | 全局唯一，前缀用 `theory-` / `a-` / `m-` / `gap-` |
| `label` | 是 | 图上与搜索里显示的名字 |
| `type` | 自动 | 由 helper 决定：theory / action / metric |
| `layer` | 是 | 六层 id：`layer-seen`、`layer-remembered`、`layer-trusted`、`layer-found`、`layer-closed`、`layer-referred`；横切节点写 `None` |
| `definition` | 是 | 面板里的定义 |
| `citation` | 理论必填 | 文献 / 官方 / 实测；没有就留空并标 `UNVERIFIED` |
| `doc` / `section` | 是 | 来源文档与小节，面板里可点回原文 |
| `status` | 否 | 默认 `SUPPORTED`，见下表 |
| `note` | 否 | 面板里单独显示的备注，例如「出处待确认」 |

状态词表：

| 值 | 图上 | 含义 |
| --- | --- | --- |
| `SUPPORTED` | 实心 | 已有文档支撑，可直接用 |
| `MENTIONED` | 赭色虚线 | 文档只提了一句，没有展开 |
| `MISSING` | 赭色虚线 | 应该有的内容，文档里没有 |
| `UNVERIFIED` | 实心 + 点状外圈 | 拿不准、出处待确认 |
| `EXPECTED` | 灰色虚线 | 由 `expected.py` 自动生成的占位，不由人手写 |
| `na` | 灰色空心 + 斜线 | 主动判定不适用，不是缺 |

「缺」的统计口径是 `MISSING + MENTIONED + EXPECTED`；`UNVERIFIED` 单独计，不算缺；`na` 也不计入缺。

### 3. 加边

只允许五种，写在 `curated_nodes.py` 底部的四个列表里（`belongs` 由理论节点的 `layer` 自动生成）：

```python
DRIVES = [
    ("theory-new", "a-new", "为什么这个理论支持这个动作"),
]
MEASURES = [
    ("a-new", "m-new", "这个动作影响哪个指标"),
]
REFERENCES = [
    ("theory-new", "theory-old", "文档里的显式引用关系"),
]
DEPENDS = [
    ("layer-seen", "layer-closed", "后层依赖前层：没人看见就没有成交"),
]
```

边类型：

| type | 图中的含义 | 方向 |
| --- | --- | --- |
| `belongs` | 理论归属某一层 | 理论 → 层级（自动） |
| `drives` | 理论驱动动作 | 理论 → 动作 |
| `measures` | 动作影响指标 | 动作 → 指标 |
| `depends` | 后层依赖前层 | 前层 → 后层 |
| `cites` | 文档之间的引用 | 承载概念的两端 |

端点不存在、id 重复都会让构建失败；不要为了「连上」硬造关系，拿不准的节点留 `UNVERIFIED` 并不加边。

### 4. 标证据分级

在 `work/evidence_map.py` 的 `OVERRIDES` 里按节点 id 覆盖默认值：

```python
OVERRIDES = {
    "m-new": ("none", "后台数据，公开页拿不到。"),
}
```

五类与《L1-无数据支撑清单.md》的对应：

| 值 | 图上标签 | 对应清单 | 能不能对外引用 |
| --- | --- | --- | --- |
| `sourced` | 有出处 | — | 可以 |
| `boundary` | 需注意边界 | 需注意边界 | 可以，但必须带限制条件 |
| `inferred` | 经验推断 | 经验推断 | 不能说成「数据表明」 |
| `none` | 未获取 | 未获取 | 不引用 |
| `rumor` | 传闻 | 传闻 | 不作为依据 |

默认值按类型给：理论 `sourced`、动作 `inferred`、指标 `sourced`。清单里的一条可能对应多个节点，所以图上计数会大于清单条数（当前：有出处 53、需注意边界 11、经验推断 133、未获取 15、传闻 5）。

面板里每个节点都会显示它的证据类别和一句解释；图上右上角的小标记表示非 `sourced` 的类别，缩放大于 85% 才画。

### 5. 补「应有清单」

`work/expected.py` 里每一层有若干槽位，一个槽位是一个概念位置，不是一篇文档：

```python
dict(id="x3-proof", layer="layer-trusted", type="action",
     label="信任证据", why="凭什么信你做过。",
     covered_by=["a-case", "a-numbers"]),
```

- `covered_by` 里只要有一个节点存在，这个槽位就算有着落；
- 全部为空时，构建会自动生成 `ph-<slot-id>` 占位节点（`status=expected`，灰色虚线），画在对应层里；
- 想把某个槽位重新变成「空缺」，把 `covered_by` 清空即可。

当前三个缺口没有走占位机制，而是显式写成节点，便于记录「为什么缺」：

| 节点 | 层 | 状态 |
| --- | --- | --- |
| `gap-publish-frequency` 发布频次与最优间隔 | 被看见 | mentioned（缺） |
| `gap-capacity` 产能上限与外包 | 被成交 | missing（缺） |
| `theory-community-na` 社群运营 | 被找到 | na（不适用） |

### 6. 知识维度

节点属于 L1 知识 / L2 战略 / L3 战术 / L4 方法论 / L5 工具，默认按来源文档的路径前缀判断：

- `methodology/L1-*` → L1；`L2-*` → L2；`L3-*` → L3；`L4-*` → L4
- `methodology/01-*`、`02-*`、`03-*`、`制作-01` → L1
- `methodology/制作-02`、`抽样与归因` → L4
- `methodology/理论到操盘` → L5
- `methodology/00-*`、`经营-*`、`topics/方向备选`、`monetization/` → L2
- `methodology/公开内容边界`、`topics/选题库` → L3

个别节点不跟随文档，在 `extract.py` 的 `DIM_OVERRIDE` 里按 id 指定（例如复盘八列、发布 SOP、报价单）。

## 网页怎么用

- **左栏两个独立筛选维度**：六层链路（点一层看这层的理论/动作/指标/缺口数），和 L1–L5 知识维度；两个可以同时叠加。节点类型、证据分级也能叠。
- **看缺口**：勾「只看缺口 / 仅参考·可转述」，剩下的就是 `missing / mentioned / expected` 或证据为 `none / rumor` 的节点。
- **点层级**：右侧面板显示这层的统计（理论、动作、指标、缺、不适用）、证据构成、问题/成功判据/死法，以及该层全部节点。再点一次同一层回到六层全显。
- **点节点**：显示定义、状态、证据类别及解释、出处、文档路径、最后修改时间、小节、关联动作/指标。
- **搜索**：按 `/` 聚焦，回车或点结果跳转。
- **深链**：`index.html#layer-closed` 打开即定位到第 5 层；`index.html#theory-curiosity-gap` 定位到具体节点。
- **缩放/平移**：滚轮缩放（以光标为中心）、拖拽平移；「适应窗口」「回到总览」在右下。

## 决策使用记录

`决策使用记录.md` 是图谱的使用台账，不是图谱本身。每次用它做决定，按固定结构追加一条：

- 日期、决策类别（整体规划 / 方向选择 / 选题 / 脚本审查 / 报价边界 / 复盘归因）
- 这次要定什么
- 查了图谱哪几块
- 查到的结论：逐句/逐个数字给三档判定（有源可对外断言 / 无源但可实测 / 无源且不可验证），并指到节点或写明缺什么源
- 有没有改变原决定

`evidence=inferred` 的节点正在审计，记录里遇到时标「待审计确认」，暂不当依据用。

## graph.json 结构

```jsonc
{
  "meta": { "generated_at": "...", "docs_scanned": 64, "node_count": 217, "edge_count": 318,
            "evidence_counts": {...}, "dim_counts": {...}, "missing_total": 2, "na_total": 1,
            "status_labels": {...}, "evidence_labels": {...}, "dim_labels": {...} },
  "layers": [ { "id": "layer-seen", "order": 1, "name": "被看见",
                "problem": "...", "success": "...", "death": "...", "if_broken": "...",
                "stats": { "theory": 13, "action": 18, "metric": 10,
                           "missing": 1, "na": 0, "unverified": 0,
                           "evidence": { "sourced": 9, "boundary": 3, ... } } } ],
  "nodes": [ { "id": "theory-curiosity-gap", "label": "好奇心缺口", "type": "theory",
               "layer": "layer-seen", "status": "supported",
               "definition": "...", "citation": "...", "doc": "methodology/...",
               "section": "...", "doc_mtime": "2026-11-14T...", "doc_sha1": "…",
               "evidence": "sourced", "evidence_note": "", "dim": "k1",
               "review_state": "已确认" } ],
  "edges": [ { "id": "e1", "source": "...", "target": "...",
               "type": "drives", "note": "..." } ]
}
```

## 已知边界

- 节点是**人工复核**的结果，`extract.py` 不会自动从正文里抽概念；`proposals.json` 只提供候选小节，是否成节点要人判断。这样做是为了避免把同一概念抽成多个节点、或把一句话当成理论。
- `accounts/` 下的对标账号样本没有被建模成节点，只作为证据来源出现在部分节点的出处里。
- `methodology/00-知识覆盖矩阵.md` 是知识库自己的进度表，可能与更新后的文档不完全同步；图谱的缺口语义以 `curated_nodes.py` 和 `expected.py` 为准，两者不一致时应先改清单再重跑。
- `--ack` 只把 `curated_nodes.py` 里被引用到的文档指纹记为已复核；新增但还没建节点的文档不会进 `reviewed.json`。
- 网页里的文档链接是相对路径 `../knowledge/...`，从 `index.html` 点开可回到原文；把 `index.html` 单独拷走时链接会失效，但图本身仍可离线查看。
