#!/usr/bin/env python3
"""OAPEN 已下 PDF → knowledge/sources/books/<格>/<编号>-<slug>.md，并写出入库清单。

只读 PDF 与 manifest，不联网、不改 manifest 已有行。
用法：python3 ingest_oapen.py [--force]
产物：
  work/book-scout-4/oapen-ingest-plan.json   本批清单（含许可档位、字符数、落盘采集时间）
  knowledge/sources/books/<格>/*.md          分页 Markdown（[[p.N]]＝PDF 页序）
  knowledge/sources/metadata.csv             追加 6 列完整登记行
"""
import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

W4 = Path(__file__).resolve().parent                     # work/book-scout-4
BASE = W4.parents[1]                                     # 04-知识底座
SOURCES = BASE / "knowledge" / "sources"
METADATA = SOURCES / "metadata.csv"
MANIFEST = W4 / "oapen" / "manifest_oapen.csv"
PLAN = W4 / "oapen-ingest-plan.json"
PDFTOTEXT = "/opt/homebrew/bin/pdftotext"

# 细类（命中格）→ books 下目录（11–14 为第二批新开）
CELL_DIR = {
    "定价与报价": "07-商业与经营",
    "销售与谈判": "05-客户运营与转化",
    "一人公司的协作与招人": "07-商业与经营",
    "B2B采购决策链": "04-用户与市场",
    "定位与差异化": "11-定位与差异化",
    "交付与验收": "12-交付与验收",
    "行业方案库": "13-行业方案库",
    "行业场景知识": "14-行业场景知识",
    "商业模式设计": "07-商业与经营",
    "个体老板与小额采购": "07-商业与经营",
}

# 许可类型 → 库内质量档（库只认三档；引用口径写进「授权限制」与「备注」）
QUALITY = {
    "CC BY": "可引用",
    "CC BY-SA": "可引用",
    "CC BY-NC": "仅参考",
    "CC BY-NC-ND": "仅参考",
    "保留所有权利": "不可引用",
    "未找到许可": "不可引用",
    "": "不可引用",
}
LICENSE_TERM = {
    "CC BY": "无限制（CC BY 4.0，manifest 内页许可句已核；对外引用须注出处）",
    "CC BY-SA": "无限制（CC BY-SA，manifest 内页许可句已核；对外引用须注出处并以同许可共享）",
    "CC BY-NC": "CC BY-NC（仅内部判断；对外只可转述观点＋注出处，不得成段搬用原文）",
    "CC BY-NC-ND": "CC BY-NC-ND（仅内部判断；对外只可转述观点＋注出处；ND：不得成段搬用、不得改编）",
    "保留所有权利": "保留所有权利（不可引用；对外不得摘原句，只可转述观点并注出处）",
    "未找到许可": "未找到许可（按不可引用处理；对外不得摘原句）",
    "": "未找到许可（按不可引用处理；对外不得摘原句）",
}


def clean_page(s: str) -> str:
    s = s.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    s = "".join(ch for ch in s if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip("\n")


def pdf_pages(pdf: Path):
    r = subprocess.run([PDFTOTEXT, "-layout", str(pdf), "-"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"pdftotext rc={r.returncode} {r.stderr.strip()[:120]}")
    if not r.stdout.strip():
        raise RuntimeError("pdftotext 抽出 0 字符（疑似无文字层）")
    pages = r.stdout.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return [clean_page(p) for p in pages]


def author_year_index():
    """从本地 harvest 候选池补作者与年份；不联网，查不到就写未获取。"""
    idx = {}
    p = W4 / "raw" / "candidates_raw.json"
    if not p.exists():
        return idx
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return idx
    for cell, recs in data.items():
        for r in recs or []:
            t = (r.get("title") or "").strip()
            if not t:
                continue
            authors = r.get("authors") or []
            year = (r.get("published") or "")[:4]
            idx.setdefault(t.lower(), (authors, year))
    return idx


def resolve_pdf(rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else (W4 / p)


def main():
    argv = sys.argv[1:]
    force = "--force" in argv
    plan_out = PLAN
    exclude = set()
    if "--plan-out" in argv:
        plan_out = Path(argv[argv.index("--plan-out") + 1])
    if "--exclude-plan" in argv:
        prev = Path(argv[argv.index("--exclude-plan") + 1])
        if prev.exists():
            exclude = {i["编号"] for i in json.loads(prev.read_text(encoding="utf-8"))["items"]}
    rows = [r for r in csv.DictReader(MANIFEST.open(encoding="utf-8-sig"))
            if (r.get("下载状态") or "").strip() == "OK" and r["编号"].strip() not in exclude]
    meta_rows = list(csv.DictReader(METADATA.open(encoding="utf-8-sig")))
    have = {(r.get("本地路径") or "").strip() for r in meta_rows}
    ay = author_year_index()

    plan, fails = [], []
    for r in rows:
        num = r["编号"].strip()
        rel = (r.get("文件") or "").strip()
        if not rel:
            fails.append({"编号": num, "书名": r["书名"], "原因": "manifest 无文件路径"})
            continue
        pdf = resolve_pdf(rel)
        if not pdf.exists():
            fails.append({"编号": num, "书名": r["书名"], "原因": f"文件不存在：{pdf}"})
            continue
        cell = (r.get("命中格") or "").split("；")[0].strip()
        sub = CELL_DIR.get(cell)
        if not sub:
            fails.append({"编号": num, "书名": r["书名"], "原因": f"命中格无对应目录：{cell}"})
            continue
        out_dir = SOURCES / "books" / sub
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / (pdf.stem + ".md")
        rel_out = out.relative_to(SOURCES).as_posix()
        lic = (r.get("许可类型") or "").strip()
        quality = QUALITY.get(lic, "不可引用")
        lic_sentence = re.sub(r"\s+", " ", (r.get("内页许可原文全文") or "").strip())[:160]
        authors, year = ay.get((r.get("书名") or "").strip().lower(), ([], ""))
        author = "；".join(authors) if authors else "未获取"
        year = year or "未获取"
        st = pdf.stat()
        collect_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))

        if out.exists() and rel_out in have and not force:
            plan.append({"编号": num, "书名": r["书名"], "格": cell, "目录": sub,
                         "本地路径": rel_out, "许可类型": lic, "质量分级": quality,
                         "字符数": out.stat().st_size, "采集时间": collect_time,
                         "状态": "已存在（跳过转换）"})
            continue
        try:
            pages = pdf_pages(pdf)
        except Exception as e:
            fails.append({"编号": num, "书名": r["书名"], "原因": str(e)})
            print(f"[FAIL] {num} {r['书名'][:40]} :: {e}", flush=True)
            continue

        head = (f"# {r['书名']}\n> {author}｜{year}｜{r.get('出版社','')}｜"
                f"许可：{lic or '未找到许可'}（{lic_sentence}…）｜OAPEN {r.get('原始URL','')}\n")
        body = [head]
        for i, pg in enumerate(pages, 1):
            if not pg:
                continue
            body.append(f"\n## p.{i}\n\n[[p.{i}]]\n\n{pg}\n")
        text = "".join(body)
        out.write_text(text, encoding="utf-8")

        note = (f"OAPEN 编号 {num}｜格 {cell}｜许可类型 {lic or '未找到许可'}｜"
                f"内页许可句：{lic_sentence[:80]}｜引用口径：{LICENSE_TERM.get(lic, '')}｜"
                f"PDF：{rel}")
        row = {
            "题名": r["书名"], "作者": author, "年份": year, "来源URL": r.get("原始URL", ""),
            "获取日期": time.strftime("%Y-%m-%d", time.localtime(st.st_mtime)),
            "文本形态": "PDF 原生文字层（分页 Markdown）", "质量分级": quality,
            "授权限制": LICENSE_TERM.get(lic, LICENSE_TERM[""]),
            "页码映射": "有（[[p.N]]＝PDF 页序）", "本地路径": rel_out,
            "字符数": str(len(text)), "备注": note, "采集时间": collect_time, "入库时间": "",
        }
        plan.append({"编号": num, "书名": r["书名"], "格": cell, "目录": sub,
                     "本地路径": rel_out, "许可类型": lic, "质量分级": quality,
                     "页数": len(pages), "字符数": len(text), "采集时间": collect_time,
                     "状态": "已转换", "_meta": row})
        print(f"[ok] {num} {len(pages):>4}p {len(text):>9}c {quality} {out.name}", flush=True)

    # 追加 metadata（按表头顺序，跳过已登记路径）
    with METADATA.open(encoding="utf-8-sig", newline="") as f:
        header = next(csv.reader(f))
    new_rows = [p["_meta"] for p in plan if p.get("_meta") and p["本地路径"] not in have]
    if new_rows:
        with METADATA.open("a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header)
            for row in new_rows:
                w.writerow(row)
    for p in plan:
        p.pop("_meta", None)

    plan_out.write_text(json.dumps({"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "manifest_ok_rows": len(rows), "converted": len(plan),
                                    "failed": len(fails), "items": plan, "fails": fails},
                                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[done] manifest OK={len(rows)} converted={len(plan)} failed={len(fails)} "
          f"metadata_appended={len(new_rows)}")
    for f_ in fails:
        print(f"  FAIL {f_['编号']} {f_['书名'][:50]} :: {f_['原因']}")


if __name__ == "__main__":
    main()
