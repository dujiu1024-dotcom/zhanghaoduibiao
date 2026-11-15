#!/usr/bin/env python3
"""许可抽取：从 PDF 版权页/许可页取整句，抽不到就判「未找到许可」。

原则（写死，不许改）：抽不到许可句子 → 「未找到许可」→ 不可引用；禁止按出版社、DOI、
书系推断。所有判断只用 PDF 内文字。
"""
import re

STARTERS = (
    "open access",
    "this work is licensed",
    "this book is licensed",
    "licensed under",
    "is licensed under",
    "veröffentlicht",
    "dieses buch",
)

LICENSE_HINT = re.compile(
    r"creative commons|namensnennung|cc[ -]by|all rights reserved|alle rechte vorbehalten",
    re.I,
)


def sentences(text):
    """按句切分；不在 `4.0.` 这类数字点后切断（要求句点前是小写字母或右括号）。"""
    flat = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[a-z\)\]”\"'])\.\s+", flat)
    return [p.strip() for p in parts if p.strip()]


def extract(text):
    """返回 (许可整句, 依据)。依据 ∈ {'starter+keyword','keyword-only','none'}"""
    ss = sentences(text)
    # 1) 以许可类开场白开头、且含许可关键词的句子，向后并 1–2 句以补齐 "To view a copy..." 之类
    for i, s in enumerate(ss):
        low = s.lower()
        if any(k in low for k in STARTERS) and LICENSE_HINT.search(s):
            out = s
            for j in (i + 1, i + 2):
                if j < len(ss) and LICENSE_HINT.search(ss[j]) and len(out) < 260:
                    out = out + ". " + ss[j]
            return out.strip(), "starter+keyword"
    # 2) 只含许可关键词的句子（无标准开场白）
    for s in ss:
        if LICENSE_HINT.search(s):
            return s, "keyword-only"
    return "", "none"


def kind(sentence):
    if not sentence:
        return "未找到许可"
    l = sentence.lower()
    n = re.sub(r"[^a-z0-9]", "", l)  # 去标点/连字符后再判，避免 NonCommercial-NoDerivatives 这类写法漏判
    if "allerechtevorbehalten" in n or "allrightsreserved" in n:
        return "保留所有权利"
    if "noncommercialnoderivatives" in n or "ncnd" in n:
        return "CC BY-NC-ND"
    if "noncommercial" in n:
        return "CC BY-NC"
    if "sharealike" in n:
        return "CC BY-SA"
    if "creativecommons" in n or "namensnennung" in n or "ccby" in n:
        return "CC BY"
    return "其他"


QUOTA = {
    "CC BY": "可引用",
    "CC BY-SA": "可引用",
    "CC BY-NC": "仅内部判断，对外只可转述观点＋注出处",
    "CC BY-NC-ND": "仅内部判断，对外只可转述观点＋注出处，不得成段搬用",
    "保留所有权利": "不可引用",
    "其他": "许可不明，不可引用",
    "未找到许可": "未找到许可，不可引用",
}
