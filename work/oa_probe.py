# -*- coding: utf-8 -*-
"""用 OpenAlex 批量查论文的开放获取状态，只产出事实（是否 OA + 直链），不做判断。"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request

SRC = "/Users/longyi/project/账号对标/04-知识底座/catalog/catalog.csv"
SCOPE = ("二、传播与内容", "三、判断与思维", "六、平台与增长")

rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
out = []
for r in rows:
    if r["类"] not in SCOPE:
        continue
    if "论文" not in r["类型"] and "专利" not in r["类型"]:
        continue
    title = r["资料名称"].split("/")[0].strip()
    q = title[:120]
    url = ("https://api.openalex.org/works?filter=title.search:"
           + urllib.parse.quote(q) + "&per_page=3&select=title,publication_year,open_access,best_oa_location,doi")
    try:
        with urllib.request.urlopen(url, timeout=15) as f:
            d = json.load(f)
        res = d.get("results", [])
        hit = res[0] if res else {}
        oa = hit.get("open_access", {})
        loc = hit.get("best_oa_location") or {}
        out.append([r["编号"], r["资料名称"][:60], r["类型"],
                    str(hit.get("publication_year", "")),
                    "OA" if oa.get("is_oa") else ("CLOSED" if hit else "NOTFOUND"),
                    loc.get("pdf_url") or loc.get("landing_page_url") or oa.get("oa_url") or "",
                    hit.get("doi") or ""])
    except Exception as e:
        out.append([r["编号"], r["资料名称"][:60], r["类型"], "", "ERR", str(e)[:40], ""])
    time.sleep(0.15)

with open("/Users/longyi/project/账号对标/work/oa.tsv", "w", encoding="utf-8") as f:
    for o in out:
        f.write("\t".join(str(x) for x in o) + "\n")

from collections import Counter
print("rows", len(out), Counter(o[4] for o in out))
