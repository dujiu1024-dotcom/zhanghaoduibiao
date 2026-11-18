#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地检索底座：SQLite + sqlite-vec + 中文二元字组倒排 + 人工概念标签。

三个检索通道：
  literal  中文二元字组倒排（BM25 近似打分，OR 语义）
  tag      人工概念标签（segment_tags，只由原文出现过的说法归并）
  vector   bge-m3 向量（ollama 本地）

所有命中必须同时带 路径 / 段号(或法条号/页码) / 质量档，缺一不输出。
"""
import argparse
import csv
import hashlib
import json
import math
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import sqlite_vec

HERE = Path(__file__).resolve().parent
BASE = HERE.parent                    # 04-知识底座
PROJECT = BASE.parent                 # 账号对标
KNOW = BASE / "knowledge"
SOURCES = KNOW / "sources"
DB_PATH = HERE / "kbase.db"
GRAPH_JSON = BASE / "图谱" / "graph.json"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "bge-m3")
EMBED_DIM = 1024
EMBED_BATCH = 32

QUALITY_ORDER = {"可引用": 3, "仅参考": 2, "不可引用": 1, "历史文本|已废止": 0}

# 来源不明的扫描件/摘编件：只作索引，不摘原句、不构成答案，排序排在可引用之后
INDEX_ONLY = set()
INDEX_ONLY_MARK = "来源不明"
# 二手读书笔记：只作索引，不摘原句、不计入门槛，排序永远排在可引原文之后
SECONDHAND = set()
SECONDHAND_MARK = "读书笔记（二手）"

# 相关性下限（可调）：向量相似度 = 1 - cosine 距离；字面覆盖率 = 命中字组 IDF 占查询总 IDF 的比例
SIM_FLOOR = float(os.environ.get("RAG_SIM_FLOOR", "0.66"))
COVERAGE_FLOOR = float(os.environ.get("RAG_COVERAGE_FLOOR", "0.32"))
# 跨语言通道：中文问句打外文原文（公版书）时，相似度整体低一档，沿用 0.66 会把整库外文判成「库里没有」。
# 只对「文档级」放行：同一文档至少 2 段过 XLING_NEAR 且前两段均值 ≥ XLING_FLOOR，单段擦边不算。
# 实测：5 条中文问句→英文公版书 4 条过；12 条无答案问句 0 条过（见 rag/eval/report.md）。
XLING_FLOOR = float(os.environ.get("RAG_XLING_FLOOR", "0.58"))
XLING_NEAR = float(os.environ.get("RAG_XLING_NEAR", "0.56"))
# 回答闸门：字面路单独成答，要求覆盖率更高、且问句里未登录字组的 IDF 占比不能过高
ANSWER_MIN_COVERAGE = float(os.environ.get("RAG_ANSWER_MIN_COVERAGE", "0.40"))
OOV_FLOOR = float(os.environ.get("RAG_OOV_FLOOR", "0.50"))

# 人工概念层：只收录语料中实际出现过的说法（掉播、踩坑在语料中 0 次，已剔除）
TOPIC_LEXICON = {
    "完播": ["完播", "完播率", "留人", "划走", "三秒", "3秒", "5秒", "掉点", "平均播放时长"],
    "报价": ["报价", "定价", "多少钱", "收费", "砍价", "压价", "价格"],
    "可引用": ["可引用", "出处", "依据", "未获取", "传闻", "经验推断"],
    "私信": ["私信", "咨询", "加微信", "私域"],
    "翻车": ["翻车", "失败", "报错"],
    "选题": ["选题", "题材", "方向", "话题"],
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS docs(
  id INTEGER PRIMARY KEY,
  source_path TEXT UNIQUE NOT NULL,
  text_path TEXT,
  title TEXT NOT NULL,
  quality TEXT NOT NULL CHECK(quality IN ('可引用','仅参考','不可引用','历史文本|已废止')),
  kind TEXT NOT NULL,
  sha1 TEXT NOT NULL,
  char_count INTEGER NOT NULL,
  meta_json TEXT,
  updated_at TEXT NOT NULL,
  ingested_at TEXT
);
CREATE TABLE IF NOT EXISTS segments(
  id INTEGER PRIMARY KEY,
  doc_id INTEGER NOT NULL REFERENCES docs(id) ON DELETE CASCADE,
  ordinal INTEGER NOT NULL,
  section TEXT NOT NULL,
  locator TEXT NOT NULL,
  quality TEXT NOT NULL,
  text TEXT NOT NULL,
  embed_text TEXT NOT NULL,
  char_len INTEGER NOT NULL,
  UNIQUE(doc_id, ordinal)
);
CREATE INDEX IF NOT EXISTS idx_seg_doc ON segments(doc_id);
CREATE INDEX IF NOT EXISTS idx_seg_quality ON segments(quality);
CREATE TABLE IF NOT EXISTS terms(
  gram TEXT NOT NULL,
  seg_id INTEGER NOT NULL,
  PRIMARY KEY(gram, seg_id)
) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS segment_tags(
  seg_id INTEGER NOT NULL,
  topic TEXT NOT NULL,
  synonym TEXT NOT NULL,
  PRIMARY KEY(seg_id, topic, synonym)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_tag_topic ON segment_tags(topic, seg_id);
CREATE TABLE IF NOT EXISTS graph_nodes(
  id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  type TEXT,
  layer TEXT,
  status TEXT,
  evidence TEXT,
  doc TEXT,
  payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS graph_edges(
  id INTEGER PRIMARY KEY,
  source TEXT NOT NULL,
  target TEXT NOT NULL,
  type TEXT,
  note TEXT
);
CREATE INDEX IF NOT EXISTS idx_edge_src ON graph_edges(source);
CREATE INDEX IF NOT EXISTS idx_edge_dst ON graph_edges(target);
"""


# ---------------------------------------------------------------- 基础工具

def connect(path: Path = DB_PATH, create: bool = True) -> sqlite3.Connection:
    if not create and not path.exists():
        sys.exit(f"数据库不存在：{path}，先跑 `python rag.py rebuild`")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    if create:
        conn.executescript(SCHEMA)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(docs)")]
        if "ingested_at" not in cols:      # 旧库迁移：入库时间列
            conn.execute("ALTER TABLE docs ADD COLUMN ingested_at TEXT")
        conn.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS seg_vec USING vec0(embedding float[{EMBED_DIM}] distance_metric=cosine)")
        conn.commit()
    return conn


def norm_space(s: str) -> str:
    return re.sub(r"\s+", "", s)


def grams(s: str) -> set:
    t = norm_space(s)
    return {t[i:i + 2] for i in range(len(t) - 1)}


def sha1_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def rel(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(PROJECT))
    except ValueError:
        return str(p)


def load_metadata() -> dict:
    path = SOURCES / "metadata.csv"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return {r["本地路径"]: r for r in csv.DictReader(f)}


# ---------------------------------------------------------------- 切段

MD_HEAD = re.compile(r"^(#{1,6})\s+(.*)$")
LAW_ART = re.compile(r"^第([一二三四五六七八九十百千零〇两\d]+)条")
LAW_CHAP = re.compile(r"^第([一二三四五六七八九十百千零〇两\d]+)(编|章|节)")
FENCE = re.compile(r"^(```|~~~)")


def clean_block(lines) -> str:
    text = "\n".join(l.rstrip() for l in lines).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def chunk_block(block: str, limit: int = 1200):
    if len(block) <= limit:
        return [block]
    lines = block.split("\n")
    if lines[0].lstrip().startswith("|"):
        header = lines[:2] if len(lines) > 2 else lines[:1]
        chunks, cur = [], list(header)
        for row in lines[len(header):]:
            if len("\n".join(cur)) + len(row) > limit and len(cur) > len(header):
                chunks.append("\n".join(cur))
                cur = list(header)
            cur.append(row)
        if len(cur) > len(header):
            chunks.append("\n".join(cur))
        return chunks
    sents = re.split(r"(?<=[。！？；!?;])", block)
    chunks, cur = [], ""
    for s in sents:
        if cur and len(cur) + len(s) > limit:
            chunks.append(cur)
            cur = ""
        cur += s
    if cur.strip():
        chunks.append(cur)
    # 无句读的长段（如英文原文）硬切，避免整篇只有一个向量
    out = []
    for c in chunks:
        if len(c) <= limit:
            out.append(c)
        else:
            out.extend(c[i:i + limit] for i in range(0, len(c), limit))
    return out


def split_markdown(text: str):
    """按标题分节、按空行分段；返回 [(section, locator, 段落)]。"""
    text = text.replace("\r\n", "\n")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    section, sec_stack = "开头", {}
    out, buf = [], []
    in_fence = False

    def flush():
        if not buf:
            return
        block = clean_block(buf)
        buf.clear()
        if not block or re.fullmatch(r"[-*_=\s]{3,}", block):
            return
        for i, piece in enumerate(chunk_block(block)):
            out.append((section, piece, i))

    for line in text.split("\n"):
        s = line.strip()
        if FENCE.match(s):
            in_fence = not in_fence
            buf.append(line)
            continue
        m = None if in_fence else MD_HEAD.match(s)
        if m:
            flush()
            level = len(m.group(1))
            sec_stack = {k: v for k, v in sec_stack.items() if k < level}
            sec_stack[level] = m.group(2).strip()
            section = " / ".join(sec_stack[k] for k in sorted(sec_stack)) or m.group(2).strip()
            continue
        if not s and not in_fence:
            flush()
            continue
        buf.append(line)
    flush()

    out2, n = [], 0
    for section, piece, part in out:
        if len(norm_space(piece)) < 6:
            continue
        n += 1
        loc = f"§{n}" if part == 0 else f"§{n}.{part + 1}"
        out2.append((section, loc, piece))
    return out2


def split_law(text: str):
    """法条按“第X条”切；章节标题作为 section。"""
    section = "正文"
    out, buf, art = [], [], None

    def flush():
        if not buf:
            return
        block = clean_block(buf)
        buf.clear()
        if not block:
            return
        if art:
            loc = f"第{art}条"
        else:
            loc = f"§{len(out) + 1}"
        for i, piece in enumerate(chunk_block(block)):
            out.append((section, loc if i == 0 else f"{loc}-{i + 1}", piece))

    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        mch = LAW_CHAP.match(s)
        if mch and len(s) < 40:
            flush()
            section = s[:40]
            art = None
            continue
        mart = LAW_ART.match(s)
        if mart:
            flush()
            art = mart.group(1)
            buf.append(s)
            continue
        buf.append(line)
    flush()
    return [x for x in out if len(norm_space(x[2])) >= 6]


PLAIN_HEAD = re.compile(r"^(BOOK\s+[IVXLC]+|Part\s+\d+|CHAPTER\s+[IVXLCDM\d]+)$", re.I)
PLAIN_CN_HEAD = re.compile(r"^(第[一二三四五六七八九十]+[章节]|[一二三四五六七八九十]+、.{0,20}|【[^】]{2,14}】|总则|附则|前言)$")


def split_plain(text: str):
    """纯文本：按空行分段；BOOK/Part/Chapter 与中文“一、/第X章/【...】/总则”行作为章节。"""
    blocks, buf, book = [], [], "正文"
    section = "正文"

    def flush():
        if not buf:
            return
        block = " ".join(l.strip() for l in buf if l.strip())
        buf.clear()
        block = re.sub(r"\s{2,}", " ", block).strip()
        if len(norm_space(block)) >= 6:
            blocks.append((section, block))

    for line in text.replace("\r\n", "\n").split("\n"):
        s = line.strip()
        if not s or re.fullmatch(r"[-=]{3,}", s):
            flush()
            continue
        if PLAIN_HEAD.match(s) and len(s) < 40:
            flush()
            if s.upper().startswith("BOOK"):
                book = s
                section = s
            else:
                section = f"{book} / {s}"
            continue
        if PLAIN_CN_HEAD.match(s) and len(s) <= 26 and not s.endswith(("。", "；", "，", "：", "、")):
            flush()
            section = s if book == "正文" else f"{book} / {s}"
            continue
        buf.append(line)
    flush()

    out = []
    for sec, block in blocks:
        for i, piece in enumerate(chunk_block(block)):
            out.append((sec, f"§{len(out) + 1}" + (f".{i + 1}" if i else ""), piece))
    return out


def split_doc(kind: str, text: str):
    if kind == "law":
        return split_law(text)
    if kind == "plain":
        return split_plain(text)
    return split_markdown(text)


def tag_segments(text: str, section: str):
    """只对原文里字面出现的说法打标签，不推断。"""
    hay = norm_space(text + "\n" + section)
    hits = []
    for topic, syns in TOPIC_LEXICON.items():
        for syn in syns:
            if norm_space(syn) in hay:
                hits.append((topic, syn))
    return hits


# ---------------------------------------------------------------- 文档清单

def md_sources():
    meta = load_metadata()
    by_path = {}
    for row in meta.values():
        by_path[row.get("来源URL", "")] = row
    out = []
    for md in sorted(KNOW.rglob("*.md")):
        if "sources" in md.relative_to(KNOW).parts[:1]:
            continue
        text = md.read_text(encoding="utf-8", errors="ignore")
        key = rel(md)
        row = by_path.get(key, {})
        title = row.get("题名") or next(
            (l.lstrip("# ").strip() for l in text.splitlines() if l.startswith("# ")), md.stem)
        out.append({
            "source_path": key,
            "text_path": key,
            "title": title,
            "quality": row.get("质量分级", "仅参考"),
            "kind": "md",
            "text": text,
            "meta": row,
        })
    return out


def fulltext_sources():
    meta = load_metadata()
    out = []
    # metadata.csv 的「文本形态」历史写法不统一（Markdown/Markdown(原生)、PDF原生/原生PDF/PDF、
    # OCR/扫描OCR、原生HTML/浏览器渲染HTML），全部纳入白名单；按本地文件存在性兜底。
    TEXT_FORMS = {
        "原生HTML", "浏览器渲染HTML", "PDF原生", "原生PDF", "PDF",
        "Markdown(原生)", "Markdown", "原生文本", "扫描OCR", "OCR",
    }
    # 被打回的自写笔记（口径第五格）：是替换对象不是依据，永不入库
    BANNED_DIR = "fulltext/knowledge/"
    for row in meta.values():
        if row.get("文本形态") not in TEXT_FORMS:
            continue
        local = row.get("本地路径") or ""
        if BANNED_DIR in local:
            continue
        p = SOURCES / row["本地路径"]
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        name = p.stem
        if "law" in p.parts:
            kind = "law"
        elif p.suffix.lower() == ".md":
            kind = "md"
        else:
            kind = "plain"
        out.append({
            "source_path": rel(p),
            "text_path": rel(p),
            "title": row.get("题名") or name,
            "quality": row.get("质量分级", "仅参考"),
            "kind": kind,
            "text": text,
            "meta": row,
        })
    return out


def all_sources():
    return md_sources() + fulltext_sources()


def load_paths(paths):
    """显式指定文件：md/txt，未知的按 plain 处理。"""
    meta = load_metadata()
    rows = []
    for raw in paths:
        p = Path(raw)
        if not p.is_absolute():
            cand = [PROJECT / p, BASE / p, KNOW / p]
            p = next((c for c in cand if c.exists()), p)
        if not p.exists():
            print(f"[skip] 不存在：{raw}")
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        suffix = p.suffix.lower()
        kind = "md" if suffix == ".md" else ("law" if "law" in p.parts else "plain")
        title = next((l.lstrip("# ").strip() for l in text.splitlines() if l.startswith("# ")), p.stem)
        quality = "仅参考"
        row_meta = {}
        for row in meta.values():
            if row.get("本地路径") and (SOURCES / row["本地路径"]).resolve() == p.resolve():
                title, quality = row.get("题名", title), row.get("质量分级", quality)
                row_meta = row
        rows.append({"source_path": rel(p), "text_path": rel(p), "title": title,
                     "quality": quality, "kind": kind, "text": text, "meta": row_meta})
    return rows


# ---------------------------------------------------------------- 向量

def embed_texts(texts, workers: int = 4):
    """调本地 ollama /api/embed，失败时给出可执行的替代方案后退出。"""
    if not texts:
        return []
    batches = [texts[i:i + EMBED_BATCH] for i in range(0, len(texts), EMBED_BATCH)]

    def one(batch):
        payload = json.dumps({"model": EMBED_MODEL, "input": batch}).encode()
        req = urllib.request.Request(OLLAMA_URL + "/api/embed", data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.load(r)
        embs = data.get("embeddings")
        if not embs or len(embs) != len(batch):
            raise RuntimeError(f"embedding 返回异常：{len(embs or [])}/{len(batch)}")
        return embs

    out = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for embs in ex.map(one, batches):
            out.extend(embs)
    return out


def check_embedder():
    try:
        v = embed_texts(["连接测试"])
        if len(v[0]) != EMBED_DIM:
            sys.exit(f"模型 {EMBED_MODEL} 维度 {len(v[0])}，与表结构 {EMBED_DIM} 不符；"
                     f"改 EMBED_DIM 后需重建索引。")
        print(f"[embed] {EMBED_MODEL} @ {OLLAMA_URL} 可用，维度 {EMBED_DIM}")
        return True
    except (urllib.error.URLError, ConnectionError, TimeoutError, RuntimeError) as e:
        sys.exit(f"""[embed] 不可用：{e}
可行选项（不自动安装）：
  1) 启动 ollama 并拉模型：ollama serve；ollama pull bge-m3   （本机已装 ollama，最省事）
  2) 换嵌入模型：EMBED_MODEL=<已下载模型> 并同步改 EMBED_DIM 后重建
  3) 用远端 embedding：需提供 API key 与 endpoint（当前环境未检测到可用 key）
""")


# ---------------------------------------------------------------- 入库

def embed_text_of(title: str, section: str, text: str) -> str:
    return f"{title} > {section}\n{text}"


def delete_doc(conn, doc_id):
    ids = [r[0] for r in conn.execute("SELECT id FROM segments WHERE doc_id=?", (doc_id,))]
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        q = ",".join("?" * len(chunk))
        conn.execute(f"DELETE FROM seg_vec WHERE rowid IN ({q})", chunk)
        conn.execute(f"DELETE FROM terms WHERE seg_id IN ({q})", chunk)
        conn.execute(f"DELETE FROM segment_tags WHERE seg_id IN ({q})", chunk)
    conn.execute("DELETE FROM segments WHERE doc_id=?", (doc_id,))
    conn.execute("DELETE FROM docs WHERE id=?", (doc_id,))



ALLOWED_QUALITY = ("可引用", "仅参考", "不可引用", "历史文本|已废止")


def normalize_quality(q):
    """metadata 里的细分质量档（如「仅参考·与官方口径冲突」）入库时归一，避免 CHECK 失败。"""
    q = (q or "").strip()
    if q in ALLOWED_QUALITY:
        return q
    for base in ("不可引用", "仅参考", "可引用"):
        if base in q:
            return base
    return "仅参考"


def ingest_docs(conn, docs, skip_unchanged=True):
    stats = {"new": 0, "updated": 0, "skipped": 0, "segments": 0}
    for doc in docs:
        sha = sha1_text(doc["text"])
        row = conn.execute("SELECT id, sha1 FROM docs WHERE source_path=?", (doc["source_path"],)).fetchone()
        if row and row["sha1"] == sha and skip_unchanged:
            stats["skipped"] += 1
            continue
        if row:
            delete_doc(conn, row["id"])
            stats["updated"] += 1
        else:
            stats["new"] += 1
        cur = conn.execute(
            "INSERT INTO docs(source_path,text_path,title,quality,kind,sha1,char_count,meta_json,updated_at,ingested_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?)",
            (doc["source_path"], doc["text_path"], doc["title"], normalize_quality(doc["quality"]), doc["kind"],
             sha, len(doc["text"]), json.dumps(doc["meta"], ensure_ascii=False),
             time.strftime("%Y-%m-%d %H:%M:%S"), time.strftime("%Y-%m-%d %H:%M:%S")))
        doc_id = cur.lastrowid

        segs = split_doc(doc["kind"], doc["text"])
        if not segs:
            continue
        emb_inputs = [embed_text_of(doc["title"], sec, txt) for sec, _, txt in segs]
        vectors = embed_texts(emb_inputs)

        rows_term, rows_tag, seg_ids = [], [], []
        tag_count = 0
        for ordinal, ((section, locator, txt), vec) in enumerate(zip(segs, vectors), start=1):
            et = embed_text_of(doc["title"], section, txt)
            cur = conn.execute(
                "INSERT INTO segments(doc_id,ordinal,section,locator,quality,text,embed_text,char_len)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (doc_id, ordinal, section[:200], locator, doc["quality"], txt, et, len(norm_space(txt))))
            sid = cur.lastrowid
            conn.execute("INSERT INTO seg_vec(rowid,embedding) VALUES(?,?)",
                         (sid, sqlite_vec.serialize_float32(vec)))
            seg_ids.append(sid)
            for g in grams(f"{doc['title']} {section} {txt}"):
                rows_term.append((g, sid))
            for topic, syn in tag_segments(txt, section):
                rows_tag.append((sid, topic, syn))
                tag_count += 1
            stats["segments"] += 1
        conn.executemany("INSERT OR IGNORE INTO terms(gram,seg_id) VALUES(?,?)", rows_term)
        conn.executemany("INSERT OR IGNORE INTO segment_tags(seg_id,topic,synonym) VALUES(?,?,?)", rows_tag)
        conn.commit()
        print(f"  [{stats['new'] + stats['updated']:>3}] {doc['source_path']}  "
              f"segs={len(seg_ids)} tags={tag_count}")
    return stats


def cmd_init(args):
    conn = connect()
    n = import_graph(conn)
    conn.close()
    print(f"[ok] schema ready: {DB_PATH}  （图谱节点 {n}）")


def cmd_ingest(args):
    check_embedder()
    conn = connect()
    docs = load_paths(args.paths) if args.paths else all_sources()
    t0 = time.time()
    st = ingest_docs(conn, docs, skip_unchanged=not args.force)
    print(f"[done] new={st['new']} updated={st['updated']} skipped={st['skipped']} "
          f"segments={st['segments']} 用时 {time.time() - t0:.1f}s")
    conn.close()


def cmd_retag(args):
    """只重打概念标签，不重算向量（改 TOPIC_LEXICON 后用）。"""
    conn = connect(create=False)
    conn.execute("DELETE FROM segment_tags")
    n = 0
    for doc in conn.execute("SELECT id FROM docs").fetchall():
        for s in conn.execute("SELECT id,section,text FROM segments WHERE doc_id=?", (doc["id"],)):
            for topic, syn in tag_segments(s["text"], s["section"]):
                conn.execute("INSERT OR IGNORE INTO segment_tags(seg_id,topic,synonym) VALUES(?,?,?)",
                             (s["id"], topic, syn))
                n += 1
    conn.commit()
    print(f"[retag] tags={n}")
    conn.close()


def cmd_rebuild(args):
    check_embedder()
    if DB_PATH.exists():
        DB_PATH.unlink()
    for suffix in ("-wal", "-shm"):
        p = Path(str(DB_PATH) + suffix)
        if p.exists():
            p.unlink()
    conn = connect()
    docs = all_sources()
    st = ingest_docs(conn, docs)
    n = import_graph(conn)
    print(f"[rebuild] docs={st['new']} segments={st['segments']} graph_nodes={n}")
    conn.close()


# ---------------------------------------------------------------- 检索

def quality_clause(arg):
    if not arg:
        return "", []
    # 质量档本身可能含竖线（历史文本|已废止），只按逗号分多选
    vals = [v.strip() for v in re.split(r"[,，]", arg) if v.strip()]
    bad = [v for v in vals if v not in QUALITY_ORDER]
    if bad:
        sys.exit(f"未知质量档：{bad}，可选 {list(QUALITY_ORDER)}")
    if len(vals) == 1:
        return " AND s.quality = ?", vals
    return f" AND s.quality IN ({','.join('?' * len(vals))})", vals


def literal_search(conn, query, limit, quality_arg=""):
    N = conn.execute("SELECT COUNT(*) FROM segments").fetchone()[0]
    qg = grams(query)
    if not qg or not N:
        return []
    qmarks = ",".join("?" * len(qg))
    df = {r[0]: r[1] for r in conn.execute(
        f"SELECT gram, COUNT(*) FROM terms WHERE gram IN ({qmarks}) GROUP BY gram", tuple(qg))}
    usable = {g: d for g, d in df.items() if d <= max(3, int(N * 0.6))} or df
    if not usable:
        return []
    idf = {g: math.log(1 + (N - d + 0.5) / (d + 0.5)) for g, d in usable.items()}
    q2 = ",".join("?" * len(usable))
    scores = {}
    for g, sid in conn.execute(f"SELECT gram, seg_id FROM terms WHERE gram IN ({q2})", tuple(usable)):
        scores[sid] = scores.get(sid, 0.0) + idf[g]
    if not scores:
        return []
    # 带质量档过滤时扩大候选池，避免过滤后为空
    pool = limit * 100 if quality_arg else limit * 20
    cand = sorted(scores.items(), key=lambda kv: -kv[1])[:pool]
    clause, params = quality_clause(quality_arg)
    ids = [c[0] for c in cand]
    rows = {}
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        q = ",".join("?" * len(chunk))
        for r in conn.execute(
                f"SELECT s.id,s.locator,s.section,s.quality,s.text,s.char_len,d.source_path,d.title "
                f"FROM segments s JOIN docs d ON d.id=s.doc_id WHERE s.id IN ({q}){clause}",
                (*chunk, *params)):
            rows[r["id"]] = r
    out = []
    for sid, sc in cand:
        r = rows.get(sid)
        if not r:
            continue
        coverage = sc / sum(idf.values())
        out.append({
            "seg_id": sid, "path": r["source_path"], "title": r["title"], "locator": r["locator"],
            "section": r["section"], "quality": r["quality"], "text": r["text"],
            "score": sc * (0.4 + coverage), "coverage": coverage,
        })
    out.sort(key=lambda x: -x["score"])
    # 只靠一两个高频字组命中的段落不算有效字面命中（查询覆盖率门槛）
    kept = [x for x in out if x["coverage"] >= COVERAGE_FLOOR]
    return (kept or out[:3])[:max(limit * 4, 20)]


def query_topics(query):
    q = norm_space(query)
    hits = []
    for topic, syns in TOPIC_LEXICON.items():
        for syn in syns:
            if norm_space(syn) in q:
                hits.append((topic, syn))
    return hits


def oov_idf_ratio(conn, query):
    """问句里"库里没有的字组"占多大 IDF 权重。越高越说明本库缺这个词。"""
    qg = grams(query)
    if not qg:
        return 1.0
    N = conn.execute("SELECT COUNT(*) FROM segments").fetchone()[0]
    df = {r[0]: r[1] for r in conn.execute(
        f"SELECT gram, COUNT(*) FROM terms WHERE gram IN ({','.join('?' * len(qg))}) GROUP BY gram",
        tuple(qg))}
    zero = math.log(1 + (N + 0.5) / 1.5)
    total = miss = 0.0
    for g in qg:
        d = df.get(g, 0)
        w = math.log(1 + (N - d + 0.5) / (d + 0.5)) if d else zero
        total += w
        if not d:
            miss += w
    return miss / total if total else 1.0


def tag_search(conn, query, limit, quality_arg=""):
    qhits = query_topics(query)
    if not qhits:
        return [], []
    topics = sorted({t for t, _ in qhits})
    clause, params = quality_clause(quality_arg)
    q = ",".join("?" * len(topics))
    rows = conn.execute(
        f"SELECT tg.seg_id, tg.topic, tg.synonym,"
        f" s.locator, s.section, s.quality, s.text, s.char_len, d.source_path, d.title"
        f" FROM segment_tags tg"
        f" JOIN segments s ON s.id=tg.seg_id JOIN docs d ON d.id=s.doc_id"
        f" WHERE tg.topic IN ({q}){clause}", (*topics, *params)).fetchall()
    by_seg = {}
    for r in rows:
        rec = by_seg.setdefault(r["seg_id"], {
            "seg_id": r["seg_id"], "path": r["source_path"], "title": r["title"],
            "locator": r["locator"], "section": r["section"], "quality": r["quality"],
            "text": r["text"], "tags": [], "char_len": r["char_len"],
        })
        rec["tags"].append((r["topic"], r["synonym"]))
    out = list(by_seg.values())
    for r in out:
        # 同主题标签命中越多越强；过短的段（如单条法条）证据力弱，轻微降权
        r["score"] = len({t for t, _ in r["tags"]}) * 2 + len(r["tags"]) * 0.2 \
            + min(r["char_len"], 500) / 500 * 0.8
    out.sort(key=lambda x: (-len({t for t, _ in x["tags"]}), -x["score"]))
    # 同一文档最多留 2 段，避免一个文档把标签通道占满
    capped, per_doc = [], {}
    for r in out:
        if per_doc.get(r["path"], 0) >= 2:
            continue
        per_doc[r["path"]] = per_doc.get(r["path"], 0) + 1
        capped.append(r)
    return capped[:max(limit * 6, 40)], qhits


_QCACHE = {}


def embed_query(text):
    if text not in _QCACHE:
        _QCACHE[text] = embed_texts([text])[0]
    return _QCACHE[text]


def cjk_ratio(s: str) -> float:
    """汉字占非空白字符的比例，用来判断查询/段落属于哪种语言。"""
    body = re.sub(r"\s+", "", s or "")
    if not body:
        return 0.0
    return len(re.findall(r"[\u4e00-\u9fff]", body)) / len(body)


def vector_search(conn, query, limit, quality_arg="", sim_floor=None):
    """向量路：相似度低于 sim_floor 的候选直接丢弃，不进入融合。"""
    floor = SIM_FLOOR if sim_floor is None else sim_floor
    try:
        vec = embed_query(query)
    except Exception as e:  # 向量不可用不应打死整条查询
        print(f"[warn] 向量路失败：{e}", file=sys.stderr)
        return []
    clause, params = quality_clause(quality_arg)
    rows = conn.execute(
        f"SELECT s.id,s.locator,s.section,s.quality,s.text,d.source_path,d.title,v.distance"
        f" FROM (SELECT rowid, distance FROM seg_vec WHERE embedding MATCH ? ORDER BY distance LIMIT ?) v"
        f" JOIN segments s ON s.id=v.rowid JOIN docs d ON d.id=s.doc_id"
        f" WHERE 1=1{clause} ORDER BY v.distance",
        (sqlite_vec.serialize_float32(vec), limit * (60 if quality_arg else 8), *params)).fetchall()
    query_zh = cjk_ratio(query) >= 0.3
    out, cross = [], []
    for r in rows:
        sim = 1.0 - r["distance"]
        rec = {
            "seg_id": r["id"], "path": r["source_path"], "title": r["title"], "locator": r["locator"],
            "section": r["section"], "quality": r["quality"], "text": r["text"],
            "score": sim, "sim": sim, "distance": r["distance"],
        }
        if query_zh and cjk_ratio(r["text"]) < 0.1:
            cross.append(rec)            # 中文问句 → 外文段落，走文档级准入
        elif floor <= 0 or sim >= floor:
            out.append(rec)
    if cross and XLING_FLOOR > 0:
        by_doc = {}
        for rec in cross:
            by_doc.setdefault(rec["path"], []).append(rec)
        for recs in by_doc.values():
            recs.sort(key=lambda x: -x["sim"])
            top = [x["sim"] for x in recs[:2]]
            if len(top) >= 2 and min(top) >= XLING_NEAR and sum(top) / 2 >= XLING_FLOOR:
                out.extend(recs[:2])
    out.sort(key=lambda x: -x["score"])
    return out


def fuse(literal, tags, vectors, k=5):
    """RRF 融合；同时命中的段落标记为“原文命中”，仅标签路命中标记为“标签命中”。

    来源不明（仅索引）的文档一律排在可引用/仅参考之后，且不作为答案来源摘原句。
    """
    merged = {}

    def add(rec, channel, rank, weight):
        key = rec["seg_id"]
        m = merged.setdefault(key, {**rec, "channels": {}})
        m["channels"][channel] = rank
        m["rrf"] = m.get("rrf", 0.0) + weight / (60 + rank)

    for i, r in enumerate(literal, 1):
        add(r, "literal", i, 0.8)
    for i, r in enumerate(vectors, 1):
        add(r, "vector", i, 1.0)
    for i, r in enumerate(tags, 1):
        add(r, "tag", i, 1.1)
    for rec in merged.values():
        rec["hit_type"] = "原文" if rec["channels"].get("literal") or rec["channels"].get("vector") else "标签"
    out = sorted(merged.values(), key=lambda x: (2 if x["path"] in INDEX_ONLY else
                                                 1 if x["path"] in SECONDHAND else 0,
                                                 -x["rrf"], -QUALITY_ORDER.get(x["quality"], 0),
                                                 x["seg_id"]))
    # 同一文档最多 2 段，避免单一文档淹没其它出处
    final, per_doc = [], {}
    for rec in out:
        if per_doc.get(rec["path"], 0) >= 2:
            continue
        per_doc[rec["path"]] = per_doc.get(rec["path"], 0) + 1
        final.append(rec)
        if len(final) >= k:
            break
    return final


def validate_hits(hits):
    for h in hits:
        if not (h.get("path") and h.get("locator") and h.get("quality")):
            raise RuntimeError(f"命中缺字段，拒绝输出：{h}")
    return hits


LICENSE_NOTE = {}   # source_path -> 授权限制（NC/ND 等）
TRANSLATE_ONLY = set()   # 第 2 档：授权未知，可转述、不吐原句


def load_license_note():
    """从 metadata.csv 读「授权限制」列；非「无限制」的，命中时提示对外仅可转述。
    授权未核的书标「未核许可·可转述」，进 TRANSLATE_ONLY，检索时不输出原文。"""
    global LICENSE_NOTE, TRANSLATE_ONLY
    LICENSE_NOTE = {}
    TRANSLATE_ONLY = set()
    for relp, row in load_metadata().items():
        v = (row.get("授权限制") or "").strip()
        if v and v != "无限制":
            p = SOURCES / relp
            if p.exists():
                k = rel(p)
                LICENSE_NOTE[k] = v
                if "可转述" in v:
                    TRANSLATE_ONLY.add(k)


def load_index_only(conn):
    """标了「来源不明」或「读书笔记（二手）」的文档，只作索引，不摘原句。"""
    global INDEX_ONLY, SECONDHAND
    try:
        INDEX_ONLY = {r[0] for r in conn.execute(
            "SELECT source_path FROM docs WHERE meta_json LIKE ?", (f"%{INDEX_ONLY_MARK}%",))}
        SECONDHAND = {r[0] for r in conn.execute(
            "SELECT source_path FROM docs WHERE meta_json LIKE ?", (f"%{SECONDHAND_MARK}%",))}
    except sqlite3.Error:
        INDEX_ONLY, SECONDHAND = set(), set()


def search(conn, query, k=5, quality="", mode="hybrid", sim_floor=None):
    """返回 (hits, meta)。三路都没过相关性下限时 hits 为空，meta['answered']=False。"""
    load_index_only(conn)
    lit = literal_search(conn, query, k, quality) if mode in ("literal", "literal+tag", "hybrid") else []
    tags, qtopics = ([], [])
    if mode in ("tag", "literal+tag", "hybrid"):
        tags, qtopics = tag_search(conn, query, k, quality)
    vecs = vector_search(conn, query, k, quality, sim_floor) if mode == "hybrid" else []
    best_cov = max((l["coverage"] for l in lit), default=None)
    oov = oov_idf_ratio(conn, query)
    # 字面单独成答要求：覆盖率高 + 问句里没有大量"库里不存在的词"
    literal_ok = best_cov is not None and best_cov >= ANSWER_MIN_COVERAGE and oov <= OOV_FLOOR
    answered = bool(vecs) or literal_ok   # 标签只作定位线索，单独命中不构成答案
    meta = {
        "mode": mode, "answered": answered, "qtopics": qtopics,
        "best_sim": max((v["sim"] for v in vecs), default=None),
        "best_coverage": best_cov,
        "oov_idf": oov,
        "tag_only": 0 if answered else len(tags),
        "floor": SIM_FLOOR if sim_floor is None else sim_floor,
        "coverage_floor": COVERAGE_FLOOR,
        "answer_min_coverage": ANSWER_MIN_COVERAGE,
        "oov_floor": OOV_FLOOR,
    }
    hits = validate_hits(fuse(lit, tags, vecs, k)) if answered else []
    return hits, meta


def relax_search(conn, query, k, quality, mode, sim_floor=None):
    """无答案时试探：先放宽质量档，再降一档阈值。返回仅作线索，不是答案。"""
    floor = SIM_FLOOR if sim_floor is None else sim_floor
    out = []
    if quality:
        h, _ = search(conn, query, k, "", mode, floor)
        if h:
            out.append(("放宽质量档", "", h))
    low = max(0.30, round(floor - 0.10, 2))
    h2, _ = search(conn, query, k, quality, mode, low)
    if h2:
        out.append((f"阈值降到 {low:.2f}", quality, h2))
    return out


def print_no_answer(conn, query, meta, k, quality, mode, sim_floor):
    print(f"\nQUERY: {query}   mode={mode}   【库内无相关内容】")
    sim = "无" if meta["best_sim"] is None else f"{meta['best_sim']:.3f}"
    cov = "无" if meta["best_coverage"] is None else f"{meta['best_coverage']:.2f}"
    print(f"判定：向量最高相似度 {sim}（成答下限 {meta['floor']:.2f}）；字面最高覆盖率 {cov}"
          f"（候选召回 {meta['coverage_floor']:.2f}，单独成答需 {meta['answer_min_coverage']:.2f}"
          f" 且问句未登录词占比 ≤ {meta['oov_floor']:.2f}，当前 {meta['oov_idf']:.2f}）。")
    if meta["tag_only"]:
        print(f"标签层另有 {meta['tag_only']} 段同主题，但标签不代表原文回答了该问题，不返回。")
    print("未返回任何段落。建议：")
    leads = relax_search(conn, query, k, quality, mode, sim_floor)
    for label, q, hits in leads:
        print(f"  - {label}后有 {len(hits)} 条线索（标注：放宽了{'质量档' if label == '放宽质量档' else '阈值'}才有命中，不构成答案）：")
        for h in hits[:3]:
            print(f"      {h['path']} · {h['locator']} · {h['quality']}")
    if not leads:
        print("  - 换关键词：用本库会用的说法（平台黑话换全称、把问题拆成单个概念）")
        print("  - 补源：该问题的出处本库没有登记，需要先找可核来源再入库")
    else:
        print("  - 若线索方向不对，再换关键词；仍无结果则说明本库缺这个来源")


def print_hits(query, hits, qtopics, mode):
    print(f"\nQUERY: {query}   mode={mode}   hits={len(hits)}")
    if qtopics:
        print(f"标签识别: " + ", ".join(f"{t}←{s}" for t, s in qtopics))
    for i, h in enumerate(hits, 1):
        if h["path"] in SECONDHAND:
            print(f"\n{i}. [二手·待核] {h['path']}  {h['locator']}  仅参考·读书笔记（二手）")
            print(f"   {h['title']} / {h['section']}")
            print("   二手读书笔记：只说明「这本书在这个问题上怎么说过」，不摘原句、不作判断依据；"
                  "写入内容前须回到原书或可引用出处核实。")
            continue
        if h["path"] in INDEX_ONLY:
            print(f"\n{i}. [索引命中·来源不明] {h['path']}  {h['locator']}  仅参考·来源不明")
            print(f"   {h['title']} / {h['section']}")
            print("   仅作定位线索：不摘原句，不构成答案。要写进内容，须回到公版书或开放论文找到可引用出处。")
            continue
        if h["path"] in TRANSLATE_ONLY:
            print(f"\n{i}. [可转述·不吐原句] {h['path']}  {h['locator']}  {h['quality']}")
            print(f"   {h['title']} / {h['section']}")
            print("   此段属「可转述」档（授权未知／未核／保留所有权利）：可入库、可作判断依据、"
                  "可对外表达同一意思并注出处，但不搬运原句。请按意思重写，不得成段搬用。")
            continue
        if h["quality"] == "不可引用":
            print(f"\n{i}. [不可引用·仅线索] {h['path']}  {h['locator']}  不可引用")
            print(f"   {h['title']} / {h['section']}")
            print("   该书授权未标且未进两档登记：只作定位线索，不摘原句、不进对外产出；"
                  "补登 metadata 授权限制后可升为可转述。")
            continue
        if h["hit_type"] == "原文":
            channel = " ".join(f"{c}#{r}" for c, r in h["channels"].items())
            print(f"\n{i}. [原文命中] {h['path']}  {h['locator']}  {h['quality']}  ({channel})")
            print(f"   {h['title']} / {h['section']}")
            print("   " + h["text"].replace("\n", " ")[:220])
        else:
            tagstr = " ".join(f"{t}←“{s}”" for t, s in h.get("tags", [])[:4])
            print(f"\n{i}. [标签命中] {h['path']}  {h['locator']}  {h['quality']}  ({tagstr})")
            print(f"   {h['title']} / {h['section']}")
            print("   原文： " + h["text"].replace("\n", " ")[:220])
            print("   注：标签只说明主题相同，不能当原文引用；引用需回到原文核实。")
        lic = LICENSE_NOTE.get(h["path"])
        if lic:
            if lic.startswith("无限制"):
                print(f"   授权提示：{lic}——可引用，对外引用须注明出处。")
            else:
                print(f"   授权提示：{lic}——对外产出（视频/文章/报价单）只可转述观点＋注明出处，不得成段搬用原文。")


def cmd_search(args):
    conn = connect(create=False)
    load_license_note()
    hits, meta = search(conn, args.query, args.k, args.quality, args.mode, args.sim_floor)
    if args.json:
        if meta["answered"]:
            safe = []
            for h in hits:
                if h["path"] in INDEX_ONLY or h["path"] in SECONDHAND:
                    note = ("来源不明·仅索引；不摘原句，须另找可引用出处"
                            if h["path"] in INDEX_ONLY else
                            "二手读书笔记；不摘原句、不作判断依据，须回原书核实")
                    safe.append({**h, "text": "", "index_only": h["path"] in INDEX_ONLY,
                                 "secondhand": h["path"] in SECONDHAND, "note": note})
                elif h["quality"] == "不可引用":
                    safe.append({**h, "text": "", "unquotable": True,
                                 "license": LICENSE_NOTE.get(h["path"], "不可引用"),
                                 "note": "不可引用（保留所有权利/未找到许可）：不摘原句，只作定位线索"})
                else:
                    safe.append({**h, "license": LICENSE_NOTE.get(h["path"], "无限制")})
            print(json.dumps({"status": "ok", "hits": safe}, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"status": "no_answer", "query": args.query,
                              "best_sim": meta["best_sim"], "floor": meta["floor"],
                              "best_coverage": meta["best_coverage"],
                              "coverage_floor": meta["coverage_floor"],
                              "answer_min_coverage": meta["answer_min_coverage"],
                              "oov_idf": meta["oov_idf"], "oov_floor": meta["oov_floor"],
                              "tag_only": meta["tag_only"]}, ensure_ascii=False, indent=2))
    elif meta["answered"]:
        print_hits(args.query, hits, meta["qtopics"], args.mode)
    else:
        print_no_answer(conn, args.query, meta, args.k, args.quality, args.mode, args.sim_floor)
    conn.close()


# ---------------------------------------------------------------- 图谱

def import_graph(conn):
    if not GRAPH_JSON.exists():
        print(f"[skip] 找不到图谱：{GRAPH_JSON}")
        return 0
    g = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM graph_edges")
    conn.execute("DELETE FROM graph_nodes")
    for n in g.get("nodes", []):
        conn.execute(
            "INSERT OR REPLACE INTO graph_nodes(id,label,type,layer,status,evidence,doc,payload)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (n["id"], n.get("label", n["id"]), n.get("type"), n.get("layer"), n.get("status"),
             n.get("evidence"), n.get("doc"), json.dumps(n, ensure_ascii=False)))
    for i, e in enumerate(g.get("edges", []), 1):
        conn.execute("INSERT INTO graph_edges(id,source,target,type,note) VALUES(?,?,?,?,?)",
                     (i, e["source"], e["target"], e.get("type"), e.get("note")))
    conn.commit()
    return len(g.get("nodes", []))


def cmd_graph(args):
    conn = connect(create=False)
    if args.import_:
        n = import_graph(conn)
        print(f"[graph] nodes={n} edges={conn.execute('SELECT COUNT(*) FROM graph_edges').fetchone()[0]}")
        return
    if args.search:
        rows = conn.execute("SELECT id,label,type,layer,doc FROM graph_nodes WHERE label LIKE ? OR payload LIKE ?"
                            " LIMIT 20", (f"%{args.search}%", f"%{args.search}%")).fetchall()
        for r in rows:
            print(f"{r['id']}  {r['label']}  [{r['type']}/{r['layer']}]  {r['doc'] or ''}")
        return
    if args.neighbors:
        center = conn.execute("SELECT * FROM graph_nodes WHERE id=?", (args.neighbors,)).fetchone()
        if not center:
            sys.exit(f"节点不存在：{args.neighbors}")
        print(f"# {center['label']} ({center['id']}) type={center['type']} layer={center['layer']}")
        print(f"doc: {center['doc']}")
        for e in conn.execute("SELECT * FROM graph_edges WHERE source=? OR target=?",
                              (args.neighbors, args.neighbors)):
            other = e["target"] if e["source"] == args.neighbors else e["source"]
            row = conn.execute("SELECT label FROM graph_nodes WHERE id=?", (other,)).fetchone()
            arrow = "->" if e["source"] == args.neighbors else "<-"
            print(f"  {arrow} [{e['type']}] {row['label'] if row else other}  ({other})  {e['note'] or ''}")
        conn.close()
        return
    print("用法：graph --import | --neighbors <id> | --search <关键词>")
    conn.close()


# ---------------------------------------------------------------- 统计

def cmd_stats(args):
    conn = connect(create=False)
    q = conn.execute
    print(f"DB: {DB_PATH}  ({DB_PATH.stat().st_size / 1e6:.1f} MB)")
    print(f"docs={q('SELECT COUNT(*) FROM docs').fetchone()[0]}  "
          f"segments={q('SELECT COUNT(*) FROM segments').fetchone()[0]}  "
          f"terms={q('SELECT COUNT(*) FROM terms').fetchone()[0]}  "
          f"vectors={q('SELECT COUNT(*) FROM seg_vec').fetchone()[0]}  "
          f"tags={q('SELECT COUNT(*) FROM segment_tags').fetchone()[0]}  "
          f"graph_nodes={q('SELECT COUNT(*) FROM graph_nodes').fetchone()[0]}")
    for r in q("SELECT quality, COUNT(*) FROM segments GROUP BY quality"):
        print(f"  quality {r[0]}: {r[1]}")
    for r in q("SELECT topic, COUNT(DISTINCT seg_id) FROM segment_tags GROUP BY topic ORDER BY 2 DESC"):
        print(f"  tag {r[0]}: {r[1]} 段")
    conn.close()


# ---------------------------------------------------------------- 评估

def legacy_search(query, k=5):
    """直接调用旧索引的检索函数，保证对照真实而非重写。"""
    sys.path.insert(0, str(SOURCES / "pipeline"))
    import build_index  # noqa: E402
    try:
        rows = build_index.search(query, limit=k)
    except Exception:
        return []
    out = []
    for r in rows:
        f = r["file"]
        if f.startswith("fulltext/knowledge/"):
            inner = f[len("fulltext/knowledge/"):-4].replace("__", "/")
            path = "04-知识底座/knowledge/" + inner + ".md"
        else:
            path = "04-知识底座/knowledge/sources/" + f
        out.append({"path": path, "locator": r["section"], "quality": r["quality"],
                    "title": r["book"], "text": r["para"], "hit_type": "原文", "channels": {}})
    return out


def cmd_eval(args):
    def load(name):
        p = HERE / name
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

    pos = load("eval/questions.jsonl")
    neg = load("eval/questions_negative.jsonl")
    conn = connect(create=False)
    modes = [("纯字面", "literal"), ("字面+标签", "literal+tag"), ("字面+标签+向量", "hybrid")]

    def run(q, mode, floor=None):
        return search(conn, q, args.k, "", mode, floor)

    pos_rows, neg_rows = [], []
    for item in pos:
        row = {"id": item["id"], "q": item["q"], "expect": item["expect"], "answers": {}, "metas": {}}
        row["answers"]["旧索引"] = legacy_search(item["q"], args.k)
        for label, mode in modes:
            hits, meta = run(item["q"], mode)
            row["answers"][label], row["metas"][label] = hits, meta
        pos_rows.append(row)
    for item in neg:
        row = {"id": item["id"], "q": item["q"], "answers": {}, "metas": {}}
        row["answers"]["旧索引"] = legacy_search(item["q"], args.k)
        for label, mode in modes:
            hits, meta = run(item["q"], mode)
            row["answers"][label], row["metas"][label] = hits, meta
        neg_rows.append(row)

    def hit(hits, expect):
        return any(any(e in h["path"] for e in expect) for h in hits)

    labels = ["旧索引"] + [m[0] for m in modes]
    summary = {}
    for name in labels:
        h = sum(1 for r in pos_rows if hit(r["answers"][name], r["expect"]))
        refused = sum(1 for r in pos_rows if not r["answers"][name])
        false = sum(1 for r in neg_rows if r["answers"][name])
        summary[name] = {"hit": h, "refused": refused, "false": false,
                         "n_pos": len(pos_rows), "n_neg": len(neg_rows)}

    # 分布与阈值扫描：用于说明当前取值的依据
    pos_sim = [max([v["sim"] for v in vector_search(conn, r["q"], args.k, "", 0)], default=0.0) for r in pos_rows]
    neg_sim = [max([v["sim"] for v in vector_search(conn, r["q"], args.k, "", 0)], default=0.0) for r in neg_rows]
    pos_oov = [oov_idf_ratio(conn, r["q"]) for r in pos_rows]
    neg_oov = [oov_idf_ratio(conn, r["q"]) for r in neg_rows]

    def med(xs):
        xs = sorted(xs)
        return xs[len(xs) // 2] if xs else 0.0

    floors = [0.50, 0.55, 0.60, 0.62, 0.64, 0.66, 0.68, 0.70]
    sweep = []
    for fl in floors:
        ph = pr = nf = 0
        for r in pos_rows:
            hits, _ = run(r["q"], "hybrid", fl)
            ph += hit(hits, r["expect"])
            pr += (not hits)
        for r in neg_rows:
            hits, _ = run(r["q"], "hybrid", fl)
            nf += bool(hits)
        sweep.append((fl, ph, pr, nf))

    def fmt(v):
        return "无" if v is None else f"{v:.2f}"

    refused_ids = [r["id"] for r in pos_rows if not r["answers"]["字面+标签+向量"]]
    false_ids = [r["id"] for r in neg_rows if r["answers"]["字面+标签+向量"]]

    L = ["# 检索底座评估报告", "",
         f"- 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
         f"- 评估集：有答案 {len(pos_rows)} 条（questions.jsonl）+ 无答案 {len(neg_rows)} 条（questions_negative.jsonl）",
         f"- 判定：前 {args.k} 条里是否出现预期出处（路径级）；无答案集只看是否返回了任何段落",
         f"- 向量模型：{EMBED_MODEL}（ollama 本地）；字面路为中文二元字组倒排", "",
         "## 当前阈值", "",
         f"- 向量相似度下限 `SIM_FLOOR = {SIM_FLOOR}`（`--sim-floor` 或 `RAG_SIM_FLOOR` 可改）",
         f"- 字面单独成答的覆盖率下限 `ANSWER_MIN_COVERAGE = {ANSWER_MIN_COVERAGE}`，"
         f"未登录字组 IDF 占比上限 `OOV_FLOOR = {OOV_FLOOR}`（`RAG_ANSWER_MIN_COVERAGE` / `RAG_OOV_FLOOR`）",
         f"- 字面候选召回下限 `COVERAGE_FLOOR = {COVERAGE_FLOOR}`（低于它不进融合，但不是答案）",
         "- 成答条件：向量最高相似度 ≥ 下限，**或** 字面覆盖率 ≥ 上限且问句未登录词不超标；"
         "标签单独命中不算答案。三路都不过线 → 返回「库内无相关内容」，不返回段落。", "",
         "## 两组核心指标", "",
         "| 方案 | 有答案集命中率 | 漏答率（被拒答） | 无答案集硬答率 |",
         "| --- | --- | --- | --- |"]
    for name in labels:
        s = summary[name]
        L.append(f"| {name} | {s['hit']}/{s['n_pos']}（{s['hit'] / s['n_pos']:.0%}） | "
                 f"{s['refused']}/{s['n_pos']}（{s['refused'] / s['n_pos']:.0%}） | "
                 f"{s['false']}/{s['n_neg']}（{s['false'] / s['n_neg']:.0%}） |")

    L += ["", "## 阈值依据", "",
          f"- 有答案集向量最高相似度：min {min(pos_sim):.3f} / 中位 {med(pos_sim):.3f} / max {max(pos_sim):.3f}；"
          f"未登录 IDF 占比：中位 {med(pos_oov):.2f} / max {max(pos_oov):.2f}",
          f"- 无答案集向量最高相似度：min {min(neg_sim):.3f} / 中位 {med(neg_sim):.3f} / max {max(neg_sim):.3f}；"
          f"未登录 IDF 占比：中位 {med(neg_oov):.2f} / min {min(neg_oov):.2f}",
          "- 两个分布有重叠（无答案集最高相似度可到 "
          f"{max(neg_sim):.3f}，有答案集最低只有 {min(pos_sim):.3f}），所以不能只靠向量下限分开，"
          "字面路必须再加「高覆盖率 + 问句词在库内」两道闸，否则长句里只要含「抖音」「怎么」就会被硬答。",
          "", "### 扫描（hybrid，固定字面闸门，只动向量下限）", "",
          "| 向量下限 | 有答案命中 | 漏答 | 无答案硬答 |", "| --- | --- | --- | --- |"]
    for fl, ph, pr, nf in sweep:
        mark = " ←当前" if abs(fl - SIM_FLOOR) < 1e-9 else ""
        L.append(f"| {fl:.2f}{mark} | {ph}/{len(pos_rows)} | {pr}/{len(pos_rows)} | {nf}/{len(neg_rows)} |")
    L += ["", f"- 取 {SIM_FLOOR:.2f} 的实测依据：0.60 时硬答 4/12、命中 20/20；0.62–0.64 时硬答 3/12；"
          f"{SIM_FLOOR:.2f} 时硬答 2/12、0 漏答；0.68 起开始出现漏答（2/20）。"
          "也就是说，0.66 是「不漏答」前提下硬答最少的一档，代价是比 0.60 少 2 条命中"
          "（q12、q13 的预期出处被挤出前五）。这是用 32 条样本换来的分区，不是普适常数。", "",
          f"- 当前仍有漏答：{('、'.join(refused_ids) if refused_ids else '无')}；"
          f"仍有硬答：{('、'.join(false_ids) if false_ids else '无')}。",
          ""]

    L += ["## 逐条明细（有答案集）", ""]
    for r in pos_rows:
        L.append(f"### {r['id']}. {r['q']}")
        L.append(f"预期出处：{' / '.join(r['expect'])}")
        for name in labels:
            hits = r["answers"][name]
            mark = "✅" if hit(hits, r["expect"]) else "❌"
            if not hits:
                extra = ""
                if name != "旧索引":
                    m = r["metas"][name]
                    extra = (f"（拒答：sim {fmt(m['best_sim'])} < {m['floor']:.2f}；"
                             f"cov {fmt(m['best_coverage'])} < {m['answer_min_coverage']:.2f}"
                             f" 或 oov {m['oov_idf']:.2f} > {m['oov_floor']:.2f}）")
                L.append(f"- {mark} **{name}**：0 条{extra}")
                continue
            L.append(f"- {mark} **{name}**：")
            for i, h in enumerate(hits, 1):
                tag = "" if name == "旧索引" else (" 〔标签〕" if h["hit_type"] == "标签" else "")
                L.append(f"  {i}. `{h['path']}` · {h['locator']} · {h['quality']}{tag}")
        L.append("")

    L += ["## 逐条明细（无答案集）", ""]
    for r in neg_rows:
        L.append(f"### {r['id']}. {r['q']}")
        for name in labels:
            hits = r["answers"][name]
            if not hits:
                L.append(f"- ✅ **{name}**：正确拒答")
            else:
                L.append(f"- ❌ **{name}**：硬答 {len(hits)} 条")
                for i, h in enumerate(hits[:3], 1):
                    tag = "" if name == "旧索引" else (" 〔标签〕" if h["hit_type"] == "标签" else "")
                    L.append(f"  {i}. `{h['path']}` · {h['locator']} · {h['quality']}{tag}")
        L.append("")

    L += ["## 口径与偏差（先看这段再引用数字）", "",
          "1. **旧索引 0 命中不是实现 bug**：旧检索要求查询的全部二元字组同时命中且整句子串出现，自然问句必然 0；"
          "它对关键词查询有效（查「完播率」「报价」各返回 5 条）。",
          "2. **命中是路径级判定**：前 5 条里出现预期文件即记命中，不保证那一段就是最佳段；"
          "段级正确性看 locator，人工回原文核对。",
          "3. **两个评估集都不是盲测**：二十条有答案问题是在读过语料后写的；十二条无答案问题是按「本库不该有」挑的。"
          "阈值是在这两组上选的，存在过拟合风险，换一批问题要重新校准。",
          "4. **无答案集的判定偏严**：只要返回任何段落就记硬答，哪怕那一段确实是本库对相关话题的真实记载"
          "（例如库里有一段小红书平台对比，但它答不了「封面文案怎么写」）。",
          "5. **标签命中的含义**：标〔标签〕的条目只说明命中了人工同义词表，原文未必回答问题，不能当引用依据。",
          "6. **q08 语料本身没有直接答案**（翻车素材复用），它留在有答案集里是为了看会不会拒答，不是标准答案题。",
          ""]

    out = Path(args.out)
    if not out.is_absolute():
        out = HERE / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8")
    for name in labels:
        s = summary[name]
        print(f"{name}: 命中 {s['hit']}/{s['n_pos']}  漏答 {s['refused']}/{s['n_pos']}  硬答 {s['false']}/{s['n_neg']}")
    print(f"[report] {out}")
    conn.close()


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description="本地检索底座（SQLite + sqlite-vec + 二元字组 + 概念标签）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="建库建表")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("ingest", help="增量入库：切段、打标签、算向量")
    p.add_argument("paths", nargs="*", help="指定文件；不填则扫描 knowledge/")
    p.add_argument("--force", action="store_true", help="忽略 sha1，强制重建这些文档")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("rebuild", help="删库重建（含全量向量）")
    p.set_defaults(func=cmd_rebuild)

    p = sub.add_parser("search", help="检索")
    p.add_argument("query")
    p.add_argument("-k", type=int, default=5)
    p.add_argument("--quality", default="", help="质量档过滤：可引用 / 仅参考 / 不可引用，可逗号多选")
    p.add_argument("--mode", default="hybrid", choices=["literal", "tag", "literal+tag", "hybrid", "vector"])
    p.add_argument("--sim-floor", type=float, default=None,
                   help=f"向量相似度下限（默认 {SIM_FLOOR}，也可用环境变量 RAG_SIM_FLOOR）")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("stats", help="看库规模与标签覆盖")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("retag", help="只重打概念标签（改同义词表后）")
    p.set_defaults(func=cmd_retag)

    p = sub.add_parser("graph", help="图谱：导入 / 查邻居 / 搜节点")
    p.add_argument("--import", dest="import_", action="store_true")
    p.add_argument("--neighbors")
    p.add_argument("--search")
    p.set_defaults(func=cmd_graph)

    p = sub.add_parser("eval", help="跑 20 条评估集，输出对照报告")
    p.add_argument("--questions", default="eval/questions.jsonl")
    p.add_argument("--out", default="eval/report.md")
    p.add_argument("-k", type=int, default=5)
    p.set_defaults(func=cmd_eval)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
