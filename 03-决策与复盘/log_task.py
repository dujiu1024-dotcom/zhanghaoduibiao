#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按七张表作业：写日志、改状态、看卡在哪、跑门禁自检。

用法：
  python3 03-决策与复盘/log_task.py start --row S1 --what "法规采集第4批" --by 采集会话
  python3 03-决策与复盘/log_task.py finish --id L0007 --result 完成 --outputs "catalog.csv 新增3条" --next S1 --minutes 42
  python3 03-决策与复盘/log_task.py status
  python3 03-决策与复盘/log_task.py check

表 ID 全部读 03-决策与复盘/sop_tables.json，脚本里不写死。
"""
import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONF = HERE / "sop_tables.json"

HINT = {
    1254302: "没有这张表的编辑权限，找表主开权限",
    800010701: "字段类型不对，或值不在选项里（先看选项拼写）",
    1254005: "记录不存在，编号可能写错",
    131013: "token 无效，检查配置里的 base/table id",
}


def conf():
    if not CONF.exists():
        sys.exit(f"缺配置文件：{CONF}")
    d = json.loads(CONF.read_text(encoding="utf-8"))
    # 作废表：登记保留，但不参与任何推进与自检（不删数据，留档可查）
    voided = d.get("voided") or {}
    for key in list(voided):
        d.pop(key, None)
    d["_voided"] = voided
    return d


def cli(args):
    r = subprocess.run(["lark-cli"] + args, capture_output=True, text=True)
    try:
        out = json.loads(r.stdout)
    except json.JSONDecodeError:
        sys.exit(f"lark-cli 没有返回 JSON：\n{r.stdout[:300]}\n{r.stderr[:300]}")
    if not out.get("ok"):
        err = out.get("error", {})
        code = err.get("code")
        msg = err.get("message", "")
        why = HINT.get(code, err.get("hint", "原因不明"))
        sys.exit(f"写表失败：{msg}\n说明：{why}")
    return out.get("data", {})


def list_records(c, table):
    d = cli(["base", "+record-list", "--base-token", c["base"], "--table-id", table,
             "--page-size", "200", "--format", "json"])
    return d.get("record_id_list", []), d.get("fields", []), d.get("data", [])


def rows(c, table):
    ids, fields, data = list_records(c, table)
    return [dict(zip(fields, r), _id=i) for i, r in zip(ids, data)]


def now_ms():
    return int(datetime.datetime.now().timestamp() * 1000)


def find_step(c, sid):
    """常跑项 C1–C5 不在表一，返回 None；阶段项 S1–S9 必须存在。"""
    for r in rows(c, c["t1"]):
        if r.get("编号") == sid:
            return r
    if re.fullmatch(r"C[1-5]", str(sid or "")):
        return None
    sys.exit(f"表一里没有 {sid}，编号要写 S1–S9（或常跑项 C1–C5）")


def next_no(c):
    nums = []
    for r in rows(c, c["t8"]):
        m = re.fullmatch(r"L(\d+)", str(r.get("编号") or ""))
        if m:
            nums.append(int(m.group(1)))
    return f"L{max(nums, default=0) + 1:04d}"


def do_start(c, args):
    step = find_step(c, args.row)
    no = next_no(c)
    rec = {
        "编号": no,
        "时间": now_ms(),
        "按哪行干": [step["_id"]] if step else [],
        "干了什么": args.what,
        "结论": [],
        "状态": ["在做"],
    }
    if args.by:
        rec["下一行交给谁"] = args.by
    d = cli(["base", "+record-batch-create", "--base-token", c["base"],
             "--table-id", c["t8"], "--json", json.dumps({"create_records": [rec]}, ensure_ascii=False),
             "--format", "json"])
    print(f"已写日志 {no}（{args.row}）：{args.what}")
    print(f"记录 ID：{d['record_id_list'][0]}")


def do_finish(c, args):
    target = None
    for r in rows(c, c["t8"]):
        if r.get("编号") == args.id:
            target = r
            break
    if not target:
        sys.exit(f"表八里没有 {args.id}，编号要写 L0001 这种")
    patch = {"结论": [args.result]}
    if args.result in ("完成", "作废", "卡住"):
        patch["状态"] = {"完成": "已完成", "作废": "作废", "卡住": "卡住"}[args.result]
    if args.outputs:
        patch["交出什么"] = args.outputs
    if args.next:
        patch["下一行交给谁"] = args.next
    if args.minutes is not None:
        patch["耗时"] = args.minutes
    patch["采集条数"] = args.collected
    patch["入库条数"] = args.ingested
    cli(["base", "+record-batch-update", "--base-token", c["base"], "--table-id", c["t8"],
         "--json", json.dumps({"update_records": {target["_id"]: patch}}, ensure_ascii=False),
         "--format", "json"])
    print(f"已回填 {args.id}：{args.result}")
    if args.result == "完成":
        sid = args.next or target.get("下一行交给谁")
        step = None
        for r in rows(c, c["t1"]):
            if r.get("编号") == sid:
                step = r
                break
        if step:
            cli(["base", "+record-batch-update", "--base-token", c["base"], "--table-id", c["t1"],
                 "--json", json.dumps({"update_records": {step["_id"]: {
                     "状态": ["已完成"], "实际完成时间": now_ms()}}}, ensure_ascii=False),
                 "--format", "json"])
            print(f"表一 {sid} 已置「已完成」并写入完成时间")
        else:
            print("注意：没找到对应阶段行，表一未改")


def do_status(c):
    print("表一当前状态：")
    for r in sorted(rows(c, c["t1"]), key=lambda x: str(x.get("编号"))):
        st = r.get("状态") or ["未开始"]
        st = st[0] if isinstance(st, list) and st else "未开始"
        t = r.get("实际完成时间")
        if isinstance(t, (int, float)):
            t = datetime.datetime.fromtimestamp(t / 1000).strftime("%Y-%m-%d %H:%M")
        print(f"  {r.get('编号')} {r.get('阶段')}：{st}｜完成时间 {t or '—'}｜卡住原因 {(r.get('卡住怎么办') or '—')[:30]}")


def do_check(c):
    bad1, bad2, bad3, wait = [], [], [], []
    for key, name in [("t1", "表一"), ("t3", "表三"), ("t5", "表五"), ("t6", "表六")]:
        for r in rows(c, c[key]):
            st = r.get("状态") or []
            st = st[0] if isinstance(st, list) and st else None
            label = r.get("编号") or r.get("关卡编号") or r.get("事项") or r.get("素材/案例") or r["_id"]
            if st == "已完成" and not r.get("实际完成时间"):
                bad1.append(f"{name} {label}")
            if st == "卡住":
                reason = r.get("卡住怎么办") or r.get("卡在哪") or r.get("限制条件")
                if not reason:
                    bad2.append(f"{name} {label}")
            if st == "待你确认":
                wait.append(f"{name} {label}")
    for r in rows(c, c["t8"]):
        res = r.get("结论") or []
        res = res[0] if isinstance(res, list) and res else None
        if res == "完成" and not r.get("下一行交给谁"):
            bad3.append(r.get("编号"))
    print(f"① 已完成但无时间：{len(bad1)} 行" + ("（" + "、".join(bad1) + "）" if bad1 else ""))
    print(f"② 卡住但没写原因：{len(bad2)} 行" + ("（" + "、".join(bad2) + "）" if bad2 else ""))
    print(f"③ 完成但没写下一行：{len(bad3)} 行" + ("（" + "、".join(bad3) + "）" if bad3 else ""))
    print(f"④ 等你确认：{len(wait)} 行" + ("（" + "、".join(wait) + "）" if wait else ""))
    print("（④ 只能给条数：七张表都没有「进入待确认时间」字段，算不了几天）")

    # ⑤ S1 入库堵塞
    t9 = sorted(rows(c, c["t9"]), key=lambda x: str(x.get("批次号")))
    if len(t9) < 2:
        print(f"⑤ 入库堵塞：台账不足两批（现有 {len(t9)} 批），判不了")
    else:
        a, b = t9[-2].get("待入库条数"), t9[-1].get("待入库条数")
        if a is not None and b is not None and b > 0 and b >= a:
            print(f"⑤ 入库堵塞：是（上批待入库 {a} → 本批 {b}，连续两批不下降）")
        else:
            print(f"⑤ 入库堵塞：否（上批待入库 {a} → 本批 {b}）")

    # S1 最近进度
    logs = [r for r in rows(c, c["t8"]) if str(r.get("编号") or "").startswith("L")]
    logs = [r for r in logs if (r.get("采集条数") or 0) > 0]
    logs.sort(key=lambda r: str(r.get("时间") or ""))
    if logs:
        r = logs[-1]
        print(f"S1 最近进度：入库 {r.get('入库条数')}/{r.get('采集条数')}（待入库 {r['采集条数'] - r['入库条数']}，记录于 {r.get('时间')}）")
    else:
        print("S1 最近进度：暂无带采集/入库数的日志")


LAYERS = [
    ("A库", ("A库", "打底", "审库")),
    ("判断", ("判断",)),
    ("道", ("道", "定方向")),
    ("法", ("法", "选路")),
    ("术", ("术", "定做法", "备料")),
    ("执行物", ("执行物", "出片", "记数归因", "回写改方向")),
]


def layer_of(phase):
    p = str(phase or "")
    for i, (_, keys) in enumerate(LAYERS):
        for k in keys:
            if p.startswith(k) or k in p:
                return i
    return None


def do_next(c):
    """按层推进：A库→判断→道→法→术→执行物；同层内按超时天数降序。
    上游层未完成却出现下游行在做/已完成，直接报错，不静默排序。"""
    steps = rows(c, c["t1"])
    last = {}
    for r in rows(c, c["t8"]):
        st = r.get("状态") or []
        st = st[0] if isinstance(st, list) and st else None
        res = r.get("结论") or []
        res = res[0] if isinstance(res, list) and res else None
        if st == "作废" or res == "作废":
            continue
        for link in r.get("按哪行干") or []:
            rid = link.get("id") if isinstance(link, dict) else link
            t = r.get("时间") or 0
            if isinstance(t, str):
                try:
                    t = int(datetime.datetime.fromisoformat(t).timestamp() * 1000)
                except ValueError:
                    t = 0
            if t:
                last[rid] = max(last.get(rid, 0), t)
    now = now_ms()

    items = []
    for r in steps:
        st = r.get("状态") or []
        st = st[0] if isinstance(st, list) and st else "未开始"
        li = layer_of(r.get("阶段"))
        if li is None:
            continue
        gate = str(r.get("编号") or "").startswith("L") and str(r.get("阶段")) == LAYERS[li][0]
        items.append({"r": r, "st": st, "layer": li, "gate": gate, "t": last.get(r["_id"], 0), "no": str(r.get("编号"))})

    # 当前层：第一个闸门行尚未完成的层
    current = len(LAYERS)
    for i, (name, _) in enumerate(LAYERS):
        gates = [x for x in items if x["layer"] == i and x["gate"]]
        if gates and all(g["st"] == "已完成" for g in gates):
            continue
        if not gates:                       # 没有闸门行，按层内是否全完成判断
            same = [x for x in items if x["layer"] == i]
            if same and all(x["st"] == "已完成" for x in same):
                continue
        current = i
        break

    # 越层检查：下游层已开工/已完成 → 报错
    bad = [x for x in items if x["layer"] > current and x["st"] in ("在做", "已完成")]
    if bad:
        print("错误：上游未完成，下游已开工——不推进，先修表")
        for x in bad:
            print(f"  {x['no']} {x['r'].get('阶段')}｜{x['st']}｜所在层 {LAYERS[x['layer']][0]} 晚于当前层 {LAYERS[current][0]}")
        return False

    cand = [x for x in items if x["layer"] == current and x["st"] in ("未开始", "在做")]
    cand.sort(key=lambda x: (-(now - x["t"]) if x["t"] else 0, x["no"]))
    print(f"当前层：{LAYERS[current][0]}｜可推进行 {len(cand)} 条")
    for x in cand:
        if x["t"]:
            print(f"  {x['no']} {x['r'].get('阶段')}｜{x['st']}｜{int((now - x['t']) / 3600000)} 小时未动")
        else:
            print(f"  {x['no']} {x['r'].get('阶段')}｜{x['st']}｜未计时")
    if not cand:
        from collections import Counter
        cnt = Counter(x["st"] for x in items if x["layer"] == current)
        print("③ 该层没有「未开始／在做」的行——不是脚本失效，是卡在缺事实")
        for k, v in cnt.most_common():
            print(f"  {k}：{v} 条")
        if LAYERS[current][0] == "道":
            print("  道层待实测／待拍板明细见道法术器 base 的「01 道」表（42 行）")
    return True


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("--row", required=True)
    s.add_argument("--what", required=True)
    s.add_argument("--by", default="")
    f = sub.add_parser("finish")
    f.add_argument("--id", required=True)
    f.add_argument("--result", required=True, choices=["完成", "部分完成", "卡住", "作废"])
    f.add_argument("--outputs", default="")
    f.add_argument("--next", default="")
    f.add_argument("--minutes", type=int, default=None)
    f.add_argument("--collected", type=int, required=True)
    f.add_argument("--ingested", type=int, required=True)
    sub.add_parser("status")
    sub.add_parser("check")
    sub.add_parser("next")
    args = ap.parse_args()
    c = conf()
    if args.cmd == "start":
        do_start(c, args)
    elif args.cmd == "finish":
        do_finish(c, args)
    elif args.cmd == "status":
        do_status(c)
    elif args.cmd == "next":
        do_next(c)
    else:
        do_check(c)


if __name__ == "__main__":
    main()
