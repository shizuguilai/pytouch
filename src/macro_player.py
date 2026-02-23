#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
脚本 A：宏播放脚本

功能：
- 从配置文件中读取用户录制的一串点击指令
- 按顺序依次执行：
  - 先等待“两个按键之间的原始间隔时间”
  - 再执行一次点击（touchpin）
  - 每次点击结束后，再追加一个“固定耗时 + 随机延迟”

配置文件示例（JSON）：
{
  "fixed_delay": 0.2,          # 每个动作后固定等待（秒）
  "random_delay": 0.3,         # 每个动作后额外随机等待的最大值（0 ~ random_delay）
  "actions": [
    {"pin": 5, "interval": 1.234},
    {"pin": 2, "interval": 0.876}
  ]
}
"""

import json
import sys
import os
import time
import random

from touch_board_base import TouchBoardBase


def load_macro_config(path: str) -> dict:
    """加载宏配置文件。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def play_macro(config: dict, port: str = "COM5"):
    """根据配置执行一次完整的宏。"""
    fixed_delay = float(config.get("fixed_delay", 0.2))
    # 每次动作后随机延迟最大值（秒），默认 5 秒：每次动作都会重新随机一次
    random_delay_max = float(config.get("random_delay", 5.0))
    actions = config.get("actions", [])

    if not actions:
        print("配置中没有任何 actions，什么都不会执行。")
        return

    board = TouchBoardBase(port=port)
    board.open()

    print("=" * 50)
    print(f"开始执行宏，共 {len(actions)} 个动作")
    print(f"串口: {port}")
    print(f"每次动作后固定延迟: {fixed_delay} 秒")
    print(f"每次动作后随机延迟范围: [0, {random_delay_max}] 秒")
    print("=" * 50)

    try:
        for idx, action in enumerate(actions, start=1):
            pin = int(action["pin"])
            interval = float(action.get("interval", 0.0))

            # 先还原“上一次按键到这一次按键之间”的时间间隔
            if interval > 0:
                print(f"[{idx}/{len(actions)}] 等待上一次到本次的间隔: {interval:.3f} 秒")
                time.sleep(interval)

            # 执行一次点击
            print(f"[{idx}/{len(actions)}] 点击引脚: {pin}")
            board.touchpin(pin)

            # 每次点击后增加固定 + 随机延迟
            extra = fixed_delay + random.uniform(0.0, max(0.0, random_delay_max))
            if extra > 0:
                print(f"[{idx}/{len(actions)}] 每次动作后的额外延迟: {extra:.3f} 秒")
                time.sleep(extra)

        print("宏执行完毕。")
    finally:
        board.close()
        print(f"已断开串口连接: {port}")


def main():
    """
    命令行用法：

    python -m macro_player <config_path> [serial_port]

    例如：
        python src/macro_player.py macros/my_macro.json COM5
    """
    if len(sys.argv) < 2:
        print("用法: python src/macro_player.py <config_path> [serial_port]")
        sys.exit(1)

    config_path = sys.argv[1]
    if not os.path.isfile(config_path):
        print(f"配置文件不存在: {config_path}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        port = sys.argv[2]
    else:
        port = "COM5"

    config = load_macro_config(config_path)
    play_macro(config, port=port)


if __name__ == "__main__":
    main()

