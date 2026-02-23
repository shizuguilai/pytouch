#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
键盘控制器 - 基于 TouchBoardBase 的键盘控制点击器
支持通过输入数字 1-16 来控制对应引脚的点击动作
"""

import sys
import os

from touch_board_base import TouchBoardBase


class KeyboardController:
    """键盘控制器类"""

    def __init__(self, serial_port: str = "COM5"):
        """
        初始化控制器

        Args:
            serial_port: 串口号，默认为 COM5
        """
        self.running = True
        self.serial_port = serial_port
        self.board = TouchBoardBase(port=self.serial_port)
        self.setup_serial()

    def setup_serial(self):
        """初始化串口连接"""
        try:
            self.board.open()
            print(f"已连接到串口: {self.serial_port}")
        except Exception as e:
            print(f"串口连接失败: {e}")
            print(f"请检查串口号是否正确: {self.serial_port}")
            print("提示: Windows 下常见串口号为 COM1, COM3, COM5 等")
            sys.exit(1)

    def process_direct_input(self, input_str: str):
        """处理用户直接输入的命令"""
        # 优先处理退出命令
        if input_str.lower() in ["q", "quit", "exit"]:
            self.stop()
            return

        # 发送 '@' 控制指令
        if input_str == "@":
            print("发送 '@'，进入/保持工作模式")
            self.board.send_and_read("@")
            return

        # 直接数字 -> 对应触摸引脚一次
        try:
            pin = int(input_str)
            if 1 <= pin <= 16:
                print(f"控制引脚: {pin}")
                self.board.touchpin(pin)
            else:
                print(f"错误: 引脚编号超出范围 (1-16): {pin}")
        except ValueError:
            # 其它任意字符串，直接作为底层串口指令发送
            print(f"直接发送自定义串口指令: {input_str!r}")
            self.board.send_and_read(input_str)

    def start_listening(self):
        """开始监听用户输入（无限循环，回车后发送控制指令）"""
        print("=" * 50)
        print("键盘控制器已启动")
        print("=" * 50)
        print("使用说明:")
        print("  - 输入数字选择引脚 (1-16)，按回车后点击一次对应点")
        print("  - 输入 '@' -> 发送进入工作模式指令")
        print("  - 输入任意其它字符串 -> 作为原始串口指令发送")
        print("  - 输入 'q' / 'quit' / 'exit' -> 退出程序")
        print("=" * 50)

        try:
            while self.running:
                user_input = input("请输入控制命令: ").strip()
                if not user_input:
                    # 只按回车，不发送任何指令
                    continue
                self.process_direct_input(user_input)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """停止控制器"""
        self.running = False
        self.board.close()
        print(f"已断开串口连接: {self.serial_port}")
        print("程序已退出")
        sys.exit(0)


if __name__ == "__main__":
    # 确保能找到同目录下的模块
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # 获取串口号（支持命令行参数）
    if len(sys.argv) > 1:
        serial_port = sys.argv[1]
    else:
        serial_port = "COM5"  # 默认串口号

    controller = KeyboardController(serial_port)
    controller.start_listening()
