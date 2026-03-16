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

# 1. 仅把最前面的「启动游戏」+ 紧随其后的 pin 5 作为公共步骤
#    其它内容（同意协议、进入特勤处等）仍然视为和账号 1 绑定。
global_start = None
global_end = None
for i, a in enumerate(actions):
    if a.get("说明") == "启动游戏" and i + 1 < len(actions):
        next_a = actions[i + 1]
        if "pin" in next_a and next_a["pin"] == 5:
            global_start = i
            global_end = i + 2  # 包含说明 + pin5 这两步
        break

if global_start is not None and global_end is not None:
    global_actions = actions[global_start:global_end]
    rest_actions = actions[:global_start] + actions[global_end:]
else:
    # 找不到预期模式时，不拆公共步骤，全部按账号划分
    global_actions = []
    rest_actions = actions

# 2. 在剩余部分里，按“说明”里的关键词找各账号起始 index
idx2 = idx3 = idx4 = idx5 = None
for i, a in enumerate(rest_actions):
    s = (a.get("说明") or "")
    if "开始登陆第二个账号" in s:
        idx2 = i
    elif "开始登陆新的账号" in s:
        idx3 = i
    elif "开始登陆第四个" in s:
        idx4 = i
    elif "开始登陆第五个账号" in s:
        idx5 = i

# 边界（在 rest_actions 里的下标）
b = [0, idx2 or 0, idx3 or 0, idx4 or 0, idx5 or 0, len(rest_actions)]
for j in range(1, len(b)):
    if b[j] < b[j - 1]:
        b[j] = b[j - 1]
if idx5 is None:
    b[5] = len(rest_actions)

ranges = [(b[k], b[k + 1]) for k in range(5)]
print("Global range:", (0, global_end))
print("Account ranges in rest_actions (start, end):", ranges)

accounts = []
for k, (start, end) in enumerate(ranges):
    if start >= end:
        continue
    accounts.append({
        "id": k + 1,
        "name": f"账号{k + 1}",
        "actions": rest_actions[start:end],
    })

out = {
    "fixed_delay": data.get("fixed_delay", 2),
    "random_delay": data.get("random_delay", 3),
    "global_actions": global_actions,
    "accounts": accounts,
}
with open(path_out, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print("Written:", path_out)
