#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 _映射表.csv 重算 md 内部相对链接（第一版解析基于绝对路径，已作废）。"""
import csv
import os
import re
import sys
from pathlib import Path

ROOT = Path("/Users/longyi/project/账号对标")
sys.path.insert(0, str(ROOT / "work"))
import reorg  # noqa: E402

FILE_MAP = {}
NEW2OLD = {}
with open(ROOT / "_映射表.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        old, new = row["原路径"], row["新路径"]
        if new.startswith("（"):
            continue
        FILE_MAP[old] = new
        NEW2OLD[new] = old


def old_dir_of(new_rel: str) -> str:
    return os.path.dirname(NEW2OLD[new_rel])


def resolve(old_abs_rel: str):
    if old_abs_rel in FILE_MAP:
        return FILE_MAP[old_abs_rel]
    key = old_abs_rel.rstrip("/") + "/"
    mapped = reorg.map_path(key)
    if mapped:
        return mapped.rstrip("/")
    return None


LINK = re.compile(r"(\[[^\]]*\]\()([^)\s]+)(\))")


def main():
    changed, unresolved = [], []
    for new_rel in sorted(FILE_MAP.values()):
        if not new_rel.endswith(".md"):
            continue
        path = ROOT / new_rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        orig = text
        base_old = old_dir_of(new_rel)

        def sub(m):
            before, tgt, after = m.group(1), m.group(2), m.group(3)
            if tgt.startswith(("http://", "https://", "mailto:", "#", "tel:")):
                return m.group(0)
            core, anchor = tgt, ""
            if "#" in core:
                core, anchor = core.split("#", 1)
                anchor = "#" + anchor
            if not core:
                return m.group(0)
            trail = "/" if core.endswith("/") else ""
            old_abs = os.path.normpath(os.path.join(base_old, core))
            new_abs = resolve(old_abs)
            if new_abs is None:
                unresolved.append((new_rel, tgt))
                return m.group(0)
            rel = os.path.relpath(str(ROOT / new_abs), str(path.parent))
            return before + rel + trail + anchor + after

        text = LINK.sub(sub, text)
        if text != orig:
            path.write_text(text, encoding="utf-8")
            changed.append(new_rel)

    print("changed:", len(changed))
    for c in changed:
        print("  ", c)
    print("unresolved:", len(unresolved))
    seen = set()
    for f, t in unresolved:
        k = (f, t)
        if k in seen:
            continue
        seen.add(k)
        print("  ", f, "->", t)


if __name__ == "__main__":
    main()
