#!/usr/bin/env python3
"""跑完后统一复核 manifest：逐本重新抽页数、文字层、许可整句，重写 CSV。

许可抽取优先级：含 Creative Commons / Namensnennung / CC-BY 的整句 → 保留所有权利类 → 未核到。
"""
import csv
import os
import re
import subprocess

MAN = "oapen/manifest_oapen.csv"


def flat_text(path):
    txt = subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True).stdout
    return txt, re.sub(r"\s+", " ", txt)


def pages_of(path):
    info = subprocess.run(["pdfinfo", path], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", info)
    return int(m.group(1)) if m else 0


def license_of(flat):
    # 优先：带 CC 字样的整句（允许句中出现 CC 4.0 这种点号，故用较长窗口）
    for pat in [
        r"[^.]{0,200}(?:Creative Commons|Namensnennung)[^.]{0,400}(?:4\.0|3\.0|International|Lizenz|License)[^.]{0,120}\.",
        r"[^.]{0,200}(?:Creative Commons|Namensnennung[^.]{0,200})[^.]{0,300}\.",
        r"[^.]{0,120}(?:CC-BY|CC BY)[^.]{0,200}\.",
    ]:
        m = re.search(pat, flat, re.I)
        if m:
            return m.group(0).strip(" .")[:500]
    for pat in [r"Alle Rechte vorbehalten", r"All rights reserved", r"©[^.]{0,200}\."]:
        m = re.search(pat, flat, re.I)
        if m:
            return m.group(0).strip()[:300]
    return ""


def norm(lic):
    l = lic.lower()
    if not lic:
        return "未核到"
    if "alle rechte vorbehalten" in l or "all rights reserved" in l:
        return "保留所有权利"
    if "noncommercial-no-derivatives" in l or "non-commercial-no-derivatives" in l or "nc-nd" in l:
        return "CC BY-NC-ND"
    if "noncommercial" in l or "non-commercial" in l:
        return "CC BY-NC"
    if "sharealike" in l or "share-alike" in l:
        return "CC BY-SA"
    if "creative commons" in l or "cc-by" in l or "namensnennung" in l:
        return "CC BY"
    return "其他"


QUOTA = {
    "CC BY": "可引用",
    "CC BY-SA": "可引用",
    "CC BY-NC": "仅内部判断，对外只可转述观点＋注出处",
    "CC BY-NC-ND": "仅内部判断，对外只可转述观点＋注出处，不得成段搬用",
    "保留所有权利": "不可引用",
    "其他": "许可不明，不可引用",
    "未核到": "未核到许可，不可引用",
}


def main():
    rows = list(csv.DictReader(open(MAN, encoding="utf-8-sig")))
    fixed = 0
    for r in rows:
        fn = (r.get("文件") or "").strip()
        if not fn or not os.path.exists(fn):
            continue
        txt, flat = flat_text(fn)
        lic = license_of(flat)
        lt = norm(lic)
        new = {
            "页数": str(pages_of(fn)),
            "有无文字层": "有" if len(txt) > 3000 else "无（疑似扫描件）",
            "内页许可原文全文": lic,
            "许可类型": lt,
            "引用口径": QUOTA.get(lt, "未核到许可，不可引用"),
        }
        changed = any(r.get(k, "") != v for k, v in new.items())
        r.update(new)
        if changed:
            fixed += 1
    cols = ["编号", "书名", "出版社", "原始URL", "页数", "有无文字层", "内页许可原文全文",
            "许可类型", "命中格", "下载状态", "引用口径", "文件", "备注"]
    rows.sort(key=lambda x: (x.get("编号") or "999"))
    with open(MAN, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print("复核", len(rows), "行，改动", fixed, "行")
    print("许可分布：", Counter(r["许可类型"] for r in rows).most_common())
    print("状态分布：", Counter(r["下载状态"] for r in rows).most_common())


if __name__ == "__main__":
    main()
