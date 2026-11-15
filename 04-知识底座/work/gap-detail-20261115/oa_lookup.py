#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 Semantic Scholar API 批量查论文 OA PDF。只读查询，输出候选清单。"""
import csv
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent

# 待查论文：编号 → 检索词
PAPERS = {
    "01-03": "Prospect Theory An Analysis of Decision under Risk Kahneman Tversky",
    "01-13": "Studies of Independence and Conformity A Minority of One Asch",
    "01-14": "Normative and Informational Social Influences upon Individual Judgment Deutsch Gerard",
    "01-18": "Compliance without Pressure The Foot-in-the-Door Technique Freedman Fraser",
    "01-23": "The Norm of Reciprocity A Preliminary Statement Gouldner",
    "01-40": "Possible Selves Markus Nurius",
    "02-04": "Encoding Decoding Stuart Hall",
    "02-08": "The Agenda-Setting Function of Mass Media McCombs Shaw",
    "02-61": "Watching Subtitled Television Automatic Reading Behavior d'Ydewalle",
    "03-21": "Convergent and Discriminant Validation by the Multitrait-Multimethod Matrix Campbell Fiske",
    "03-24": "Failing to Learn and Learning to Fail Intelligently How Great Organizations Put Failure to Work Edmondson",
    "04-08": "Marketing Malpractice The Cause and the Cure Christensen",
    "04-16": "Product Differentiation and Market Segmentation as Alternative Marketing Strategies Smith",
    "04-35": "The Consumer Decision Journey Court Elting",
    "05-17": "The Good-Better-Best Approach to Pricing",
    "05-32": "The One Number You Need to Grow Reichheld",
    "06-04": "The YouTube Video Recommendation System Davidson",
    "06-18": "How T.V. Advertising Works A Meta-Analysis of 389 Real World Split Cable T.V. Advertising Experiments",
    "09-14": "How Large Are Software Cost Overruns A Review of the 1994 CHAOS Report",
    "X-09": "On the Nature of Reactance and Its Role in Persuasive Health Communication Quick",
    "X-10": "Adolescent Reactance and Anti-Smoking Campaigns A Theoretical Approach",
}

out = []
for no, q in PAPERS.items():
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={q}&limit=3&fields=title,year,externalIds,openAccessPdf,venue"
    r = subprocess.run(["curl", "-sL", "--max-time", "20", url], capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        out.append({"编号": no, "状态": "API错误", "PDF": "", "题名": "", "年份": "", "venue": ""})
        time.sleep(2)
        continue
    best = None
    for p in d.get("data", []):
        if p.get("openAccessPdf") and p["openAccessPdf"].get("url"):
            best = p
            break
    if best:
        out.append({"编号": no, "状态": "有OA", "PDF": best["openAccessPdf"]["url"],
                    "题名": best.get("title", "")[:80], "年份": str(best.get("year", "")),
                    "venue": best.get("venue", "")[:40]})
    else:
        first = (d.get("data") or [{}])[0]
        out.append({"编号": no, "状态": "无OA", "PDF": "",
                    "题名": (first.get("title") or "")[:80], "年份": str(first.get("year", "")),
                    "venue": first.get("venue", "")[:40]})
    time.sleep(1.5)

with open(HERE / "oa_lookup.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["编号", "状态", "PDF", "题名", "年份", "venue"])
    w.writeheader()
    w.writerows(out)

for r in out:
    print(f"{r['编号']} {r['状态']:5} {r['年份']:6} {r['题名'][:55]}")
    if r["PDF"]:
        print(f"        {r['PDF'][:100]}")
