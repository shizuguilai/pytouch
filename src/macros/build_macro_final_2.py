#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从 macro_final.json 按账号拆分并生成 macro_final_2.json（仅运行一次）。"""
import json
import os

_dir = os.path.dirname(os.path.abspath(__file__))
path_in = os.path.join(_dir, "macro_final.json")
path_out = os.path.join(_dir, "macro_final_2.json")

with open(path_in, "r", encoding="utf-8") as f:
    data = json.load(f)

actions = data.get("actions", [])
# 按“说明”里的关键词找各账号起始 index
idx2 = idx3 = idx4 = idx5 = None
for i, a in enumerate(actions):
    s = (a.get("说明") or "")
    if "开始登陆第二个账号" in s:
        idx2 = i
    elif "开始登陆新的账号" in s:
        idx3 = i
    elif "开始登陆第四个" in s:
        idx4 = i
    elif "开始登陆第五个账号" in s:
        idx5 = i

# 边界
b = [0, idx2 or 0, idx3 or 0, idx4 or 0, idx5 or 0, len(actions)]
# 确保单调
for j in range(1, len(b)):
    if b[j] < b[j - 1]:
        b[j] = b[j - 1]
if idx5 is None:
    b[5] = len(actions)

ranges = [(b[k], b[k + 1]) for k in range(5)]
print("Account ranges (start, end):", ranges)

accounts = []
for k, (start, end) in enumerate(ranges):
    if start >= end:
        continue
    accounts.append({
        "id": k + 1,
        "name": f"账号{k + 1}",
        "actions": actions[start:end],
    })

out = {
    "fixed_delay": data.get("fixed_delay", 2),
    "random_delay": data.get("random_delay", 3),
    "accounts": accounts,
}
with open(path_out, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print("Written:", path_out)
