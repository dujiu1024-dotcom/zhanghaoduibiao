#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A 库可用性审查：8 个真问题 + 2 组关键词对照，全部实调 rag.py search。"""
import re
import subprocess
import time

BASE = "/Users/longyi/project/账号对标/04-知识底座"
PY = f"{BASE}/rag/.venv/bin/rag/../.venv/bin/python"
PY = f"{BASE}/rag/.venv/bin/python"

QS = [
    ("Q1 199元诊断卖给谁", "定价 客户分层 目标客户 画像 谁该买"),
    ("Q2 凭什么值199", "价值证明 定价依据 差异化 为什么值这个价"),
    ("Q3 太贵了怎么答", "价格异议 砍价 嫌贵 价值锚定"),
    ("Q4 首个询盘第一句", "首次接触 开场白 询盘 第一句话"),
    ("Q5 抖音合规红线", "广告法 虚假宣传 极限词 禁止 处罚"),
    ("Q6 前三秒抓什么", "钩子 前三秒 开头 注意力 留存"),
    ("Q7 标准件交付验收", "交付清单 验收标准 交付物 里程碑"),
    ("Q8 合同资质账期", "合同 资质 账期 回款 风险 该不该接"),
    ("Q3b 太贵了(对照)", "客户说贵 便宜点 议价 折扣"),
    ("Q6b 前三秒(对照)", "视频开头 完播率 黄金三秒 抓眼球"),
]

HIT = re.compile(r"^(\d+)\.\s+\[([^\]]+)\]\s+(\S+)\s+(\S+)\s+(\S+)\s*$")


def run(q):
    t0 = time.time()
    p = subprocess.run([PY, "rag/rag.py", "search", q], cwd=BASE,
                       capture_output=True, text=True, timeout=900)
    out = p.stdout
    hits = []
    for line in out.splitlines():
        m = HIT.match(line.strip())
        if m:
            hits.append({"n": m.group(1), "tag": m.group(2), "path": m.group(3),
                         "loc": m.group(4), "quality": m.group(5)})
    # 兜底：从 [xx] 标记统计
    tags = re.findall(r"\[([^\]]+)\]", out)
    from collections import Counter
    return {"q": q, "sec": round(time.time() - t0, 1), "n_out": len(out),
            "hits": hits, "tags": Counter(tags), "raw": out}


def main():
    lines = []
    for name, q in QS:
        r = run(q)
        lines.append(f"\n{'='*70}\n## {name}\n命令: cd {BASE} && rag/.venv/bin/python rag/rag.py search \"{q}\"")
        lines.append(f"耗时 {r['sec']}s  输出 {r['n_out']} 字符  结构化命中 {len(r['hits'])} 条")
        lines.append(f"标记分布: {dict(r['tags'])}")
        for h in r["hits"][:3]:
            lines.append(f"  - [{h['tag']}] {h['path']}  {h['loc']}  {h['quality']}")
        if not r["hits"]:
            lines.append("  （无结构化命中，原始输出前 6 行）")
            for l in r["raw"].splitlines()[:6]:
                lines.append("   | " + l[:110])
        lines.append(f"原始输出前 12 行:\n" + "\n".join("   | " + l[:120] for l in r["raw"].splitlines()[:12]))
    open("/tmp/audit_a.txt", "w").write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
