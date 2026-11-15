#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Crossref 查 DOI → Unpaywall 查 OA PDF。只读查询。"""
import csv
import json
import os
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
# 联系邮箱从环境变量读取，不写死在仓库里
EMAIL = os.environ.get("CONTACT_EMAIL", "you@example.com")

PAPERS = {
    "01-03": "Prospect Theory An Analysis of Decision under Risk Kahneman Tversky 1979",
    "01-13": "Studies of Independence and Conformity A Minority of One Asch 1956",
    "01-14": "A Study of Normative and Informational Social Influences upon Individual Judgment Deutsch Gerard 1955",
    "01-18": "Compliance without Pressure The Foot-in-the-Door Technique Freedman Fraser 1966",
    "01-23": "The Norm of Reciprocity A Preliminary Statement Gouldner 1960",
    "01-40": "Possible Selves Markus Nurius 1986",
    "02-04": "Encoding Decoding Stuart Hall 1973",
    "02-08": "The Agenda-Setting Function of Mass Media McCombs Shaw 1972",
    "02-61": "Watching Subtitled Television Automatic Reading Behavior d'Ydewalle",
    "03-21": "Convergent and Discriminant Validation by the Multitrait-Multimethod Matrix Campbell Fiske 1959",
    "03-24": "Failing to Learn and Learning to Fail Intelligently How Organizations Put Failure to Work",
    "04-08": "Marketing Malpractice The Cause and the Cure Christensen 2005",
    "04-16": "Product Differentiation and Market Segmentation as Alternative Marketing Strategies Wendell Smith 1956",
    "04-35": "The Consumer Decision Journey Court Elting 2009 McKinsey",
    "05-17": "The Good-Better-Best Approach to Pricing 2018",
    "05-32": "The One Number You Need to Grow Reichheld 2003",
    "06-04": "The YouTube Video Recommendation System Davidson 2010",
    "06-18": "How T.V. Advertising Works A Meta-Analysis of 389 Real World Split Cable T.V. Advertising Experiments",
    "09-14": "How Large Are Software Cost Overruns A Review of the 1994 CHAOS Report",
    "X-09": "On the Nature of Reactance and Its Role in Persuasive Health Communication Quick 2013",
    "X-10": "Adolescent Reactance and Anti-Smoking Campaigns A Theoretical Approach Miller 1981",
}


def get(url):
    r = subprocess.run(["curl", "-sL", "--max-time", "25", url], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


out = []
for no, q in PAPERS.items():
    import urllib.parse
    qq = urllib.parse.quote(q)
    cr = get(f"https://api.crossref.org/works?query.bibliographic={qq}&rows=1&select=DOI,title,author,published")
    if not cr or not cr.get("message", {}).get("items"):
        out.append({"编号": no, "DOI": "", "OA": "查无", "PDF": "", "题名": "", "年份": ""})
        continue
    item = cr["message"]["items"][0]
    doi = item.get("DOI", "")
    title = (item.get("title") or [""])[0][:80]
    year = (item.get("published", {}).get("date-parts") or [[""]])[0][0]
    up = get(f"https://api.unpaywall.org/v2/{doi}?email={EMAIL}")
    if not up:
        out.append({"编号": no, "DOI": doi, "OA": "UP错误", "PDF": "", "题名": title, "年份": year})
    elif up.get("is_oa") and up.get("best_oa_location", {}).get("url_for_pdf"):
        out.append({"编号": no, "DOI": doi, "OA": "有OA", "PDF": up["best_oa_location"]["url_for_pdf"],
                    "题名": title, "年份": year})
    elif up.get("is_oa"):
        out.append({"编号": no, "DOI": doi, "OA": "OA无PDF", "PDF": up.get("best_oa_location", {}).get("url", ""),
                    "题名": title, "年份": year})
    else:
        out.append({"编号": no, "DOI": doi, "OA": "closed", "PDF": "", "题名": title, "年份": year})
    time.sleep(1.2)

with open(HERE / "oa_lookup2.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["编号", "DOI", "OA", "PDF", "题名", "年份"])
    w.writeheader()
    w.writerows(out)

for r in out:
    print(f"{r['编号']} {r['OA']:9} {r['年份']:4} [{r['DOI'][:30]}] {r['题名'][:50]}")
    if r["PDF"]:
        print(f"        PDF: {r['PDF'][:110]}")
