#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基于串口的触摸板基础类。
从 `comtest.py` 中抽象出的通用串口控制逻辑，方便复用。
"""

import time
import json
import serial
from sys import version_info
from typing import Optional

# '@' 工作模式字典，与原 comtest.py 保持一致
type2Pins = {
    1: ['0', '1'],
    2: ['2', '3'],
    3: ['4', '5'],
    4: ['6', '7'],
    5: ['8', '9'],
    6: ['a', 'b'],
    7: ['c', 'd'],
    8: ['e', 'f'],
    9: ['g', 'h'],
    10: ['i', 'j'],
    11: ['k', 'l'],
    12: ['m', 'n'],
    13: ['o', 'p'],
    14: ['q', 'r'],
    15: ['s', 't'],
    16: ['u', 'v'],
}


def python_version_major() -> int:
    """返回当前 Python 主版本号。"""
    return version_info.major


class TouchBoardBase:
    """
    触摸板基础控制类：
    - 负责打开/关闭串口
    - 发送指令并读取板子返回
    - 提供 touch / untouch / touchpin 等高级接口
    """

    def __init__(self, port: str = "COM5", baudrate: int = 115200, timeout: float = 1.0, is_test: bool = False):
        """
        Args:
            port: 串口号，例如 'COM5'
            baudrate: 波特率
            timeout: 读超时时间（秒）
            is_test: 如果为 True，则只把发送的指令写入 test.txt，不真正发串口
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.is_test = is_test
        self.serial_obj: Optional[serial.Serial] = None

    # ---------------- 串口相关 ----------------
    def open(self):
        """打开串口并进入 '@' 工作模式。"""
        if self.serial_obj and self.serial_obj.is_open:
            return

        self.serial_obj = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        self._print_serial_info()
        time.sleep(1)
        # 默认先发一次 '@' 进入工作模式
        self.send_and_read("@")

    def close(self):
        """关闭串口。"""
        if self.serial_obj and self.serial_obj.is_open:
            self.serial_obj.close()

    def _print_serial_info(self):
        """打印串口配置，方便调试。"""
        t = self.serial_obj
        if not t:
            return

        print("串口名:", t.name)
        print("串口号:", t.port)
        print("波特率:", t.baudrate)
        print("字节大小:", t.bytesize)
        print("校验位(N-无校验，E-偶校验，O-奇校验):", t.parity)
        print("停止位:", t.stopbits)
        print("读超时设置:", t.timeout)
        print("写超时:", t.writeTimeout)
        print("软件流控:", t.xonxoff)
        print("硬件流控(rtscts):", t.rtscts)
        print("硬件流控(dsrdtr):", t.dsrdtr)
        print("字符间隔超时:", t.interCharTimeout)
        print("-" * 10)

    # ---------------- 低层读写 ----------------
    def _read_from_board(self):
        """从板子读取返回日志并打印。"""
        if not self.serial_obj:
            return

        t = self.serial_obj
        n = t.in_waiting
        while n <= 0:
            time.sleep(0.01)
            n = t.in_waiting

        pstr = t.read(n)
        if python_version_major() > 2:
            print("板子日志(python3):", pstr.decode(errors="ignore"))
        else:
            print("板子日志(python2):", pstr)

    def send_cmd(self, cmd: str):
        """只发送指令，不主动读取返回。"""
        if not self.serial_obj:
            raise RuntimeError("串口尚未打开，请先调用 open()")

        send_str = cmd
        print("发送数据:", send_str)
        if python_version_major() > 2:
            self.serial_obj.write(send_str.encode())
        else:
            self.serial_obj.write(send_str)
        self.serial_obj.flush()

    def send_and_read(self, value: str):
        """发送指令并读取板子返回。"""
        if self.is_test:
            with open("test.txt", "a", encoding="utf-8") as f:
                f.write(value + "\n")
        else:
            self.send_cmd(value)
            time.sleep(0.05)
            self._read_from_board()

    # ---------------- 高层封装 ----------------
    @staticmethod
    def get_pin_dat(p: int):
        """获取某个点的按下/抬起编码。"""
        return type2Pins[p]

    def touch(self, p: int):
        """按下第 p 个点。"""
        press_code = type2Pins[p][0]
        self.send_and_read(press_code)

    def untouch(self, p: int):
        """抬起第 p 个点。"""
        release_code = type2Pins[p][1]
        self.send_and_read(release_code)

    def touchpin(self, n: int):
        """点击一次（按下再抬起）第 n 个点。"""
        if n == 0:
            n = 10
        self.touch(n)
        time.sleep(0.03)
        self.untouch(n)

    # ---------------- 可选：从 config.json 读取串口 ----------------
    @staticmethod
    def load_serial_config(path: str = "config.json") -> Optional[dict]:
        """读取串口配置文件，返回 dict；失败时返回 None。"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("读取串口配置失败:", e)
            return None

