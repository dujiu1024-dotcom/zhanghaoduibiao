#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""四道闸 + 检索验收的统一入口，出 PASS/FAIL、写 json 快照、与上一份快照比数字。

跑什么（顺序固定）：
  1. gate   04-知识底座/catalog/check_gate.py --soft      （门槛自检；--soft 只卡结构错误）
  2. data   04-知识底座/catalog/check_data.py             （catalog/metadata 一致性）
  3. e0     04-知识底座/experience/check_e0.py            （E0 是否被四类判断引用）
  4. copy   01-执行包/check_copy.py --selftest            （合规检查器自测）
  5. recall 04-知识底座/验收/check_recall.py --no-report   （240 题召回跑分）

退出码：
  0 = 全绿
  1 = 有回归（任一计数变差）、或有检查崩溃/超时
  2 = 有检查未达标，但与上次持平（回归由 diff 判定，见下）
  --strict 时「未达标」也算 1。

为什么不直接把「未达标」当失败：gate 现在 75/77、data 有 45 处重复，天天红等于没信号。
回路要抓的是「比上次更差」，所以 diff 里的变差才阻断。

快照：01-执行包/checks/<时间戳>.json，同时覆盖 latest.json。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
OUT = HERE / "checks"
PY = sys.executable
RAG_PY = str(PROJ / "04-知识底座" / "rag" / ".venv" / "bin" / "python")
if not Path(RAG_PY).exists():
    RAG_PY = PY  # fallback：无专用 venv 时用系统 Python

# counts: (键名, 正则, 方向)  方向 up=越大越好 / down=越小越好 / none=只记录
CHECKS = [
    {
        "name": "gate",
        "cmd": [str(RAG_PY), str(PROJ / "04-知识底座/catalog/check_gate.py"), "--soft"],
        "counts": [
            ("细类数", r"细类共 (\d+) 个", "up"),
            ("0条细类", r"硬底线 0 条：(\d+) 个", "down"),
            ("硬底线", r"硬底线（每类 ≥1，仅参考可计）：(\d+)/(\d+) 过", "up"),
            ("合格线", r"合格线（可用 ≥3 且其中可引用 ≥2）：(\d+)/(\d+) 过", "up"),
            ("重点线", r"重点线（12 个代表细类，每类可用 ≥6）：(\d+)/(\d+) 过", "up"),
            ("经验门槛", r"经验门槛[^：]*：(\d+)/(\d+) 类过", "up"),
        ],
    },
    {
        "name": "data",
        "cmd": [str(PY), str(PROJ / "04-知识底座/catalog/check_data.py")],
        "counts": [
            ("重复组", r"\[重复\] 组 (\d+)", "down"),
            ("重复副本", r"\[重复\] 组 \d+｜多余副本 (\d+)", "down"),
            ("metadata缺必填", r"\[metadata\] 行 \d+｜缺必填 (\d+)", "down"),
            ("档位不一致", r"\[档位\] 文档 \d+｜与 metadata 不一致 (\d+)", "down"),
            ("档位无meta行", r"\[档位\] 文档 \d+｜与 metadata 不一致 \d+｜无 metadata 行 (\d+)", "down"),
            ("编号重复", r"\[编号\] catalog \d+ 条｜重复编号 (\d+)", "down"),
            ("文件缺失", r"\[文件\] metadata 指向但不存在的文件 (\d+)", "down"),
            ("结论", r"结论：(有需处理项|无问题)", "none"),
        ],
    },
    {
        "name": "e0",
        "cmd": [str(PY), str(PROJ / "04-知识底座/experience/check_e0.py")],
        "counts": [
            ("E0违规命中", r"命中 (\d+) 处", "down", r"(0 处)"),
            ("E0条数", r"0 处：(\d+) 条 E0", "none"),
        ],
    },
    {
        "name": "copy",
        "cmd": [str(PY), str(PROJ / "01-执行包/check_copy.py"), "--selftest"],
        "counts": [
            ("自测", r"(自测通过|自测未通过)", "none"),
        ],
    },
    {
        "name": "recall",
        "cmd": [str(PY), str(PROJ / "04-知识底座/验收/check_recall.py"), "--no-report"],
        "counts": [("结论", r"验收结论：(通过|不通过)", "none")],
        "totals": True,   # 另行解析「总计」那行的列
    },
]

TOTALS_KEYS = ["题数", "R@5", "R@10", "MRR", "原文率", "gold原文占比", "无料", "拒答"]


def extract(stdout, counts, totals=False):
    out = {}
    for spec in counts:
        key, pat = spec[0], spec[1]
        m = re.search(pat, stdout, re.M)
        if not m and len(spec) > 3:
            m = re.search(spec[3], stdout, re.M)
        if not m:
            out[key] = "未获取"
            continue
        val = m.group(1) if m.lastindex == 1 else "/".join(g for g in m.groups() if g)
        out[key] = "0" if val == "0 处" else val
    if totals:
        for line in stdout.splitlines():
            if line.strip().startswith("总计"):
                toks = line.split()
                for i, k in enumerate(TOTALS_KEYS, start=1):
                    if i < len(toks):
                        out[k] = toks[i]
                break
    return out


def as_number(v):
    v = str(v)
    if "/" in v:
        v = v.split("/")[0]
    v = v.strip().rstrip("%")
    try:
        return float(v)
    except ValueError:
        return None


def diff_snapshots(prev, cur):
    """只报变化的数字与退出码变化。返回 (变化行, 回归行)。"""
    changes, regress = [], []
    if not prev:
        return changes, regress
    prev_items = {i["name"]: i for i in prev.get("items", [])}
    for it in cur["items"]:
        p = prev_items.get(it["name"])
        if not p:
            changes.append(f"{it['name']}：新增检查")
            continue
        if p.get("exit") != it.get("exit"):
            changes.append(f"{it['name']} 退出码 {p.get('exit')} → {it['exit']}")
        for key, val in it["counts"].items():
            old = p.get("counts", {}).get(key)
            if old is None or old == val or val == "未获取":
                continue
            direction = it["_dir"].get(key, "none")
            line = f"{it['name']} {key} {old} → {val}"
            changes.append(line)
            if direction == "none":
                continue
            a, b = as_number(old), as_number(val)
            if a is None or b is None:
                continue
            worse = (b < a) if direction == "up" else (b > a)
            if worse:
                regress.append(line)
    return changes, regress


def run_one(spec, timeout):
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(spec["cmd"], cwd=str(PROJ), capture_output=True, text=True,
                              timeout=timeout)
        code, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        code, out, err = 124, "", f"超时（>{timeout}s）"
    except FileNotFoundError as e:
        code, out, err = 127, "", str(e)
    secs = time.perf_counter() - t0
    counts = extract(out, spec["counts"], spec.get("totals", False))
    return {
        "name": spec["name"],
        "exit": code,
        "seconds": round(secs, 1),
        "counts": counts,
        "cmd": " ".join(spec["cmd"]),
        "output_tail": (out or err)[-800:],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="只跑指定检查，逗号分隔：gate,data,e0,copy,recall")
    ap.add_argument("--fast", action="store_true", help="跳过 recall（约 6 分钟）")
    ap.add_argument("--strict", action="store_true", help="未达标也算失败")
    ap.add_argument("--timeout", type=int, default=1800, help="单项超时秒数，默认 1800")
    args = ap.parse_args()

    want = {s.strip() for s in args.only.split(",") if s.strip()}
    specs = [c for c in CHECKS if (not want or c["name"] in want)
             and not (args.fast and c["name"] == "recall")]
    if not specs:
        sys.exit("没有匹配的检查")

    OUT.mkdir(parents=True, exist_ok=True)
    latest = OUT / "latest.json"
    prev = json.loads(latest.read_text(encoding="utf-8")) if latest.exists() else None

    print(f"检查 {len(specs)} 项｜项目 {PROJ}")
    items = []
    for i, spec in enumerate(specs, 1):
        it = run_one(spec, args.timeout)
        if os.environ.get("SIMULATE_FAIL") in (it["name"], "all"):
            it["exit"] = 1
            it["simulated"] = True
        for spec_c in spec["counts"]:
            it.setdefault("_dir", {})
            it["_dir"][spec_c[0]] = spec_c[2]
        items.append(it)
        shown = "  ".join(f"{k}={v}" for k, v in it["counts"].items() if k != "结论")
        if it["counts"].get("结论"):
            shown += f"  结论={it['counts']['结论']}"
        sim = "（模拟）" if it.get("simulated") else ""
        print(f"[{i}/{len(specs)}] {it['name']:<7} exit={it['exit']}{sim}  {it['seconds']:>6.1f}s  {shown}")

    crash = [i["name"] for i in items if i["exit"] not in (0, 1)]
    failing = [i["name"] for i in items if i["exit"] != 0]
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    cur = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "duration_s": round(sum(i["seconds"] for i in items), 1),
        "items": items,
    }
    changes, regress = diff_snapshots(prev, cur)
    if crash or regress:
        overall = 1
    elif failing and args.strict:
        overall = 1
    elif failing:
        overall = 2
    else:
        overall = 0
    cur["overall_exit"] = overall
    cur["changes"] = changes
    cur["regressions"] = regress

    snap = OUT / f"{ts}.json"
    n = 2
    while snap.exists():
        snap = OUT / f"{ts}-{n}.json"
        n += 1
    serial = {**cur, "items": [{k: v for k, v in it.items() if k != "_dir"} for it in items]}
    text = json.dumps(serial, ensure_ascii=False, indent=2)
    snap.write_text(text, encoding="utf-8")
    # latest.json 按检查名合并：只跑子集时不把没跑的项抹掉，否则下次全跑会全报「新增检查」
    merged = {}
    if prev:
        for it in prev.get("items", []):
            merged[it["name"]] = it
    for it in serial["items"]:
        merged[it["name"]] = it
    order = [c["name"] for c in CHECKS]
    latest.write_text(json.dumps(
        {**serial, "items": [merged[n] for n in order if n in merged]},
        ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"快照：{snap.relative_to(PROJ)}")
    print(f"基线：{prev['ts'] if prev else '无（首次运行）'}")
    if changes:
        shown = changes[:12]
        print(f"变化 {len(changes)} 项：")
        for line in shown:
            print(f"  {'!! ' if line in regress else '   '}{line}")
        if len(changes) > len(shown):
            print(f"   …另 {len(changes) - len(shown)} 项见 json")
    else:
        print("变化：无（所有计数与上次一致）")
    why = []
    if crash:
        why.append("崩溃/超时 " + ",".join(crash))
    if regress:
        why.append("回归 " + ",".join(regress[:3]))
    if failing:
        why.append("未达标 " + ",".join(failing))
    print(f"结论：{'；'.join(why) if why else '全绿'} → exit {overall}")
    return overall


if __name__ == "__main__":
    sys.exit(main())
