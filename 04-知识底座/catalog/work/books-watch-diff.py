#!/usr/bin/env python3
"""比对飞书书籍采集清单当前数据与快照，输出差异行。"""
import json
import sys

WORK = "/Users/longyi/project/账号对标/04-知识底座/catalog/work"
SNAP = f"{WORK}/books-watch-snapshot.json"
CUR = f"{WORK}/books-watch-current.ndjson"

# 参与比对的业务字段
FIELDS = ["书籍名称", "作者", "入库时间", "是否采集到", "最后更新时间", "编号", "路径", "遇到问题", "采集人", "采集时间"]


def norm(v):
    if v is None:
        return None
    if isinstance(v, list):
        return json.dumps([x if not isinstance(x, dict) else json.dumps(x, sort_keys=True, ensure_ascii=False) for x in v], ensure_ascii=False, sort_keys=True)
    if isinstance(v, dict):
        return json.dumps(v, sort_keys=True, ensure_ascii=False)
    return str(v)


def main():
    with open(SNAP, encoding="utf-8") as f:
        snap = json.load(f)
    snap_recs = snap["records"]

    cur_recs = {}
    with open(CUR, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            rid = rec.get("record_id") or rec.get("recordId")
            cur_recs[rid] = rec

    snap_ids = set(snap_recs)
    cur_ids = set(cur_recs)
    added = cur_ids - snap_ids
    removed = snap_ids - cur_ids
    changed = []
    for rid in sorted(cur_ids & snap_ids):
        diffs = []
        for fld in FIELDS:
            a = norm(snap_recs[rid].get(fld))
            b = norm(cur_recs[rid].get(fld))
            if a != b:
                diffs.append((fld, snap_recs[rid].get(fld), cur_recs[rid].get(fld)))
        if diffs:
            changed.append((rid, diffs))

    print(f"快照行数: {len(snap_ids)}  当前行数: {len(cur_ids)}")
    print(f"新增行: {len(added)}  删除行: {len(removed)}  变更行: {len(changed)}")
    for rid in sorted(added):
        r = cur_recs[rid]
        print(f"  [新增] {rid} 编号={r.get('编号')} {r.get('书籍名称')} 状态={r.get('是否采集到')}")
    for rid in sorted(removed):
        print(f"  [删除] {rid} {snap_recs[rid].get('书籍名称')}")
    for rid, diffs in changed:
        r = cur_recs[rid]
        print(f"  [变更] {rid} 编号={r.get('编号')} {r.get('书籍名称')}")
        for fld, old, new in diffs:
            print(f"      {fld}: {json.dumps(old, ensure_ascii=False)} -> {json.dumps(new, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
