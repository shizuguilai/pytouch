#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
键盘宏录制器（类似 keyboard_controller，但带“录制 + 导出配置”功能）

功能：
- 像原来的 keyboard_controller 一样，通过键盘输入数字 1-16 控制触摸点点击
- 可以开始/停止录制，记录：
  - 每次点击的引脚编号（pin）
  - 与上一键之间的时间间隔（interval）
- 随时把当前已录制的内容导出为 JSON 配置文件，
  配置结构与 macro_player.py 使用的格式一致。
"""

import sys
import os
import time
import json
import datetime
from typing import List, Dict, Optional

from touch_board_base import TouchBoardBase


class KeyboardMacroRecorder:
    """键盘宏录制器"""

    def __init__(
        self,
        serial_port: str = "COM5",
        fixed_delay: float = 0.2,
        random_delay: float = 5.0,
    ):
        """
        Args:
            serial_port: 串口号，默认为 COM5
            fixed_delay: 每次动作后固定延迟（秒）
            random_delay: 每次动作后随机延迟的最大值（0 ~ random_delay）
        """
        self.serial_port = serial_port
        self.fixed_delay = fixed_delay
        self.random_delay = random_delay

        self.board = TouchBoardBase(port=self.serial_port)
        self.running = True

        # 录制相关状态
        self.recording: bool = False
        self.actions: List[Dict] = []
        self.last_action_time: Optional[float] = None

        self._setup_serial()

    def _setup_serial(self):
        """初始化串口连接"""
        try:
            self.board.open()
            print(f"已连接到串口: {self.serial_port}")
        except Exception as e:
            print(f"串口连接失败: {e}")
            print(f"请检查串口号是否正确: {self.serial_port}")
            sys.exit(1)

    # ---------------- 录制控制 ----------------
    def start_recording(self):
        self.recording = True
        self.actions.clear()
        self.last_action_time = time.time()
        print("开始录制宏（已清空之前的录制）。")

    def stop_recording(self):
        self.recording = False
        self.last_action_time = None
        print(f"停止录制。当前共录制 {len(self.actions)} 个动作。")

    def save_recording(self, filename: Optional[str] = None):
        if not self.actions:
            print("当前没有任何录制动作，无法保存。")
            return

        if not filename:
            # 默认保存到 ./macros/ 目录，文件名带日期时间，避免覆盖
            macros_dir = os.path.join(os.getcwd(), "macros")
            os.makedirs(macros_dir, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(macros_dir, f"macro_{ts}.json")

        config = {
            "fixed_delay": self.fixed_delay,
            "random_delay": self.random_delay,
            "actions": self.actions,
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(f"已保存宏配置到文件: {filename}")

    # ---------------- 输入处理 ----------------
    def _record_action(self, pin: int):
        """在录制模式下，记录一次动作及与上一动作的时间间隔。"""
        now = time.time()
        if self.last_action_time is None:
            interval = 0.0
        else:
            interval = now - self.last_action_time
        self.last_action_time = now

        action = {"pin": pin, "interval": interval}
        self.actions.append(action)
        print(f"已录制动作: {action}")

    def process_input(self, input_str: str):
        """处理一行用户输入"""
        s = input_str.strip()

        # 控制命令（以冒号开头）
        if s.startswith(":"):
            cmd_parts = s[1:].split()
            if not cmd_parts:
                return

            cmd = cmd_parts[0].lower()
            args = cmd_parts[1:]

            if cmd in ("q", "quit", "exit"):
                self.stop()
            elif cmd in ("start", "record"):
                self.start_recording()
            elif cmd in ("stop",):
                self.stop_recording()
            elif cmd in ("save",):
                filename = args[0] if args else None
                self.save_recording(filename)
            elif cmd in ("show",):
                print(f"当前录制动作数量: {len(self.actions)}")
                if self.actions:
                    print("最后一个动作:", self.actions[-1])
            else:
                print(f"未知命令: {s}")
            return

        # 退出命令（不加冒号也支持）
        if s.lower() in ["q", "quit", "exit"]:
            self.stop()
            return

        # 数字 -> 点击对应引脚
        try:
            pin = int(s)
            if 1 <= pin <= 16:
                print(f"点击引脚: {pin}")
                self.board.touchpin(pin)
                if self.recording:
                    self._record_action(pin)
            else:
                print(f"错误: 引脚编号超出范围 (1-16): {pin}")
        except ValueError:
            # 其它字符串暂时不做处理，可以扩展为直接发送原始串口指令
            print(f"无效输入: {s}")

    # ---------------- 主循环 ----------------
    def start_loop(self):
        print("=" * 50)
        print("键盘宏录制器已启动")
        print("=" * 50)
        print("基本用法：")
        print("  - 直接输入数字 1-16 并回车 -> 点击对应引脚（touchpin）")
        print("  - 支持录制/停止/保存等控制命令：")
        print("      :start         或 :record   -> 开始新一轮录制（会清空已录制动作）")
        print("      :stop                      -> 停止录制")
        print("      :save [文件名]            -> 保存当前录制为 JSON，文件名可选")
        print("      :show                      -> 查看当前录制数量及最后一个动作")
        print("      :q / :quit / :exit         -> 退出程序")
        print("  - 不加冒号的 q/quit/exit 也可以直接退出")
        print("=" * 50)

        try:
            while self.running:
                line = input("请输入指令（数字1-16，或 :命令）: ")
                if not line:
                    continue
                self.process_input(line)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.running = False
        self.board.close()
        print(f"已断开串口连接: {self.serial_port}")
        print("程序已退出")
        sys.exit(0)


def main():
    """
    命令行用法示例：

    python src/keyboard_macro_recorder.py COM5 0.2 0.3

    参数：
      1) 串口号（如 COM5），可省略，默认 COM5
      2) 每次动作后固定延迟 fixed_delay（秒），可省略，默认 0.2
      3) 每次动作后随机延迟最大值 random_delay（秒），可省略，默认 0.3
    """
    # 确保同目录能找到模块
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # 解析命令行参数
    args = sys.argv[1:]
    serial_port = args[0] if len(args) >= 1 else "COM5"
    fixed_delay = float(args[1]) if len(args) >= 2 else 0.2
    random_delay = float(args[2]) if len(args) >= 3 else 0.3

    recorder = KeyboardMacroRecorder(
        serial_port=serial_port,
        fixed_delay=fixed_delay,
        random_delay=random_delay,
    )
    recorder.start_loop()


if __name__ == "__main__":
    main()

