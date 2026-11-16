# Issue #28 · C1 Trae CN 3.4.20 本机只读采集命令

> 目的：补齐仓库静态审计无法读取的本机知识库、元数据、SQLite 和目录分层证据。
>
> **安全级别：只读。** 本命令不执行 ingest、rebuild、retag、eval、迁移、备份、复制、删除、移动、重命名或配置修改。只读取文件元数据/哈希/CSV字段统计/SQLite统计。请在 Trae CN 3.4.20 当前项目终端运行。
>
> **执行前提：** 将终端当前目录切换到仓库根目录。不要把知识正文、metadata.csv 全文、数据库、个人/客户内容或任何密钥上传到 GitHub。只回传本命令生成的汇总文本。

## 1. 确认仓库和文件状态

```bash
cd "/你的项目仓库根目录"
printf '\n=== REPO ===\n'
pwd
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short

printf '\n=== IGNORE STATUS ===\n'
git check-ignore -v "04-知识底座/knowledge" "04-知识底座/knowledge/sources/metadata.csv" "04-知识底座/rag/kbase.db" 2>/dev/null || true
```

## 2. 知识正文、A-E 目录和元数据只读盘点

复制执行：

```bash
python3 - <<'PY'
import os, csv, json, hashlib
from collections import Counter

root = "04-知识底座"
knowledge = os.path.join(root, "knowledge")
base = os.path.abspath(".")

summary = {
    "knowledge_dir_exists": os.path.isdir(knowledge),
    "knowledge_file_count": 0,
    "knowledge_total_bytes": 0,
    "knowledge_manifest_sha256": None,
    "top_level_file_counts": {},
    "layer_dirs": {},
    "metadata": {"exists": False}
}

if os.path.isdir(knowledge):
    rows = []
    top = Counter()
    for current, dirs, files in os.walk(knowledge):
        dirs.sort()
        files.sort()
        rel_dir = os.path.relpath(current, base)
        for name in files:
            path = os.path.join(current, name)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            rel = os.path.relpath(path, base).replace(os.sep, "/")
            size = os.path.getsize(path)
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            rows.append((rel, size, h.hexdigest()))
            summary["knowledge_file_count"] += 1
            summary["knowledge_total_bytes"] += size
            parts = os.path.relpath(path, knowledge).split(os.sep)
            top[parts[0]] += 1
    manifest = hashlib.sha256()
    for rel, size, digest in sorted(rows):
        manifest.update(f"{rel}\t{size}\t{digest}\n".encode("utf-8"))
    summary["knowledge_manifest_sha256"] = manifest.hexdigest()
    summary["top_level_file_counts"] = dict(sorted(top.items()))

for layer in ["A-通用商业认知", "B-行业与市场情报", "C-专业领域知识", "D-业务项目知识", "E-个人专属知识"]:
    path = os.path.join(root, "knowledge-v2", layer)
    summary["layer_dirs"][layer] = {"exists": os.path.isdir(path),
        "files": sum(len(fs) for _, _, fs in os.walk(path)) if os.path.isdir(path) else 0}

meta = os.path.join(knowledge, "sources", "metadata.csv")
if os.path.isfile(meta):
    summary["metadata"]["exists"] = True
    summary["metadata"]["size_bytes"] = os.path.getsize(meta)
    summary["metadata"]["sha256"] = hashlib.sha256(open(meta, "rb").read()).hexdigest()
    required = ["knowledge_id","layer","source_uri","locator","rights_status",
                "rights_evidence","quality_level","verification_status",
                "sensitivity","owner","status","sha256"]
    counts = Counter()
    layers, statuses, verification = Counter(), Counter(), Counter()
    ids = Counter()
    with open(meta, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        summary["metadata"]["headers"] = headers
        missing_columns = [x for x in required if x not in headers]
        summary["metadata"]["missing_required_columns"] = missing_columns
        n = 0
        for row in reader:
            n += 1
            for col in required:
                if col in headers and not (row.get(col) or "").strip():
                    counts[col] += 1
            if row.get("knowledge_id"):
                ids[row["knowledge_id"].strip()] += 1
            layers[(row.get("layer") or "EMPTY").strip()] += 1
            statuses[(row.get("status") or "EMPTY").strip()] += 1
            verification[(row.get("verification_status") or "EMPTY").strip()] += 1
    summary["metadata"].update({
        "row_count": n,
        "missing_value_counts": dict(counts),
        "duplicate_knowledge_id_count": sum(1 for k,v in ids.items() if v > 1),
        "layer_distribution": dict(layers),
        "status_distribution": dict(statuses),
        "verification_distribution": dict(verification)
    })
else:
    summary["metadata"]["note"] = "metadata.csv not found at expected path"

print(json.dumps(summary, ensure_ascii=False, indent=2))
PY
```

## 3. SQLite 数据库位置与只读完整性检查

先只列出候选数据库和 sidecar，不打开数据库：

```bash
find "04-知识底座" -maxdepth 4 \( -name "kbase.db" -o -name "*.db-wal" -o -name "*.db-shm" -o -name "kbase.db-wal" -o -name "kbase.db-shm" \) -type f -print
```

如找到数据库，逐个执行下面 Python 只读统计（自动尝试常见路径；仅输出表名和行数，不输出记录内容）：

```bash
python3 - <<'PY'
import os, sqlite3, json
candidates = [
 "04-知识底座/kbase.db",
 "04-知识底座/knowledge/kbase.db",
 "04-知识底座/rag/kbase.db",
]
out = []
for path in candidates:
    if not os.path.isfile(path):
        continue
    item = {"path": path, "size_bytes": os.path.getsize(path)}
    for suffix in ["-wal","-shm"]:
        p = path + suffix
        item[suffix[1:] + "_exists"] = os.path.exists(p)
        item[suffix[1:] + "_size_bytes"] = os.path.getsize(p) if os.path.exists(p) else 0
    try:
        uri = "file:" + os.path.abspath(path) + "?mode=ro"
        con = sqlite3.connect(uri, uri=True, timeout=10)
        con.execute("PRAGMA query_only=ON")
        item["quick_check"] = con.execute("PRAGMA quick_check").fetchone()[0]
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )]
        item["tables"] = tables
        item["row_counts"] = {}
        for table in ["docs","segments","terms","segment_tags","seg_vec","graph_nodes","graph_edges"]:
            if table in tables:
                safe = '"' + table.replace('"','""') + '"'
                try:
                    item["row_counts"][table] = con.execute(f"SELECT COUNT(*) FROM {safe}").fetchone()[0]
                except Exception as e:
                    item["row_counts"][table] = "COUNT_ERROR:" + type(e).__name__
        con.close()
    except Exception as e:
        item["read_only_open_error"] = type(e).__name__ + ": " + str(e)[:240]
    out.append(item)
print(json.dumps(out, ensure_ascii=False, indent=2))
PY
```

若数据库不在上述三个路径，不要自行移动或改名；只回报 `find` 找到的路径。若 SQLite 打开失败，保留错误，不要尝试修复或重建。

## 4. 本次回传格式

只把以下信息回传给 ChatGPT：
- 仓库 HEAD、分支、工作区是否干净；
- 知识正文文件数、总字节、manifest SHA256、一级目录分布；
- A-E 目录是否存在及文件数；
- metadata.csv 行数、SHA256、缺失必填字段计数、重复 knowledge_id 数、layer/status/verification_status 分布；
- SQLite 数据库实际路径、文件大小、WAL/SHM 状态、quick_check、表行数；
- 执行失败或无法观测项。

不要回传知识正文、CSV 原始行、客户/个人名称、文件内容、数据库记录、Token、Cookie、绝对用户目录或盲测参考答案。

## 5. 明确禁止

本次不得执行以下任何命令或操作：
- `rag.py ingest`、`rag.py rebuild`、`rag.py retag`、`rag.py eval`；
- 任何数据库写入、迁移、VACUUM、REINDEX、UPDATE、DELETE、ALTER、DROP；
- 任何文件复制/移动/删除/重命名或批量格式转换；
- 修改 `.gitignore`、RAG 参数、索引配置或知识元数据；
- 上传知识正文、metadata.csv、数据库或个人/客户数据。

本采集只完成 C1 的本机事实核验，不代表 C2 备份恢复、C3 RAG 正式评测或 C4 迁移通过。
