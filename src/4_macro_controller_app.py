#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
宏控制桌面应用 - 整合宏播放与键盘控制器

功能：
- 加载宏 JSON，可视化显示所有步骤及执行进度
- 支持从指定步骤开始播放
- 支持暂停后切入手动控制（键盘控制器），再恢复播放
"""

import json
import os
import sys
import threading
import time
import random
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# 确保能找到同目录模块
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

# 默认宏文件（启动时自动加载，无需每次选择）
DEFAULT_MACRO_PATH = os.path.join(_script_dir, "macros", "macro_final.json")

from touch_board_base import TouchBoardBase


# ---------- 宏配置与播放逻辑 ----------

def load_macro_config(path: str) -> dict:
    """加载宏配置文件。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def step_label(action: dict, index: int) -> str:
    """生成单步显示文本。"""
    if "说明" in action:
        return f"步骤 {index + 1}: 说明 - {action.get('说明', '')}"
    if "pin" in action:
        pin = action.get("pin", "?")
        interval = action.get("interval", 0)
        return f"步骤 {index + 1}: pin {pin}, interval {interval:.2f}s"
    return f"步骤 {index + 1}: (未知)"


def is_executable_step(action: dict) -> bool:
    """是否为可执行步骤（有 pin 的项）。"""
    if "pin" not in action:
        return False
    try:
        int(action.get("pin"))
        return True
    except (TypeError, ValueError):
        return False


def play_macro_worker(
    config: dict,
    port: str,
    start_index: int,
    pause_event: threading.Event,
    stop_event: threading.Event,
    step_callback,
):
    """
    在后台线程中执行宏。
    - start_index: 从第几步开始（0-based，即 actions[start_index]）
    - pause_event: 置位时暂停（在本步结束后暂停并关闭串口）
    - stop_event: 置位时终止
    - step_callback(current_index, total_done, status): 每步后回调，status in ('running','paused','finished','stopped')
    """
    fixed_delay = float(config.get("fixed_delay", 0.2))
    random_delay_max = float(config.get("random_delay", 5.0))
    actions = config.get("actions", [])

    if not actions or start_index >= len(actions):
        step_callback(start_index, 0, "finished")
        return

    board = None
    total_done = 0

    def open_board():
        nonlocal board
        if board is None or not (getattr(board, "serial_obj", None) and board.serial_obj.is_open):
            board = TouchBoardBase(port=port)
            board.open()

    def close_board():
        nonlocal board
        if board is not None:
            try:
                board.close()
            except Exception:
                pass
            board = None

    try:
        open_board()
    except Exception as e:
        step_callback(start_index, 0, "error")
        return

    try:
        for idx in range(start_index, len(actions)):
            if stop_event.is_set():
                step_callback(idx, total_done, "stopped")
                break

            action = actions[idx]
            if "pin" not in action:
                step_callback(idx, total_done, "running")
                continue
            try:
                pin = int(action.get("pin"))
            except (TypeError, ValueError):
                step_callback(idx, total_done, "running")
                continue

            interval = float(action.get("interval", 0.0))
            if interval > 0:
                time.sleep(interval)
            if stop_event.is_set():
                step_callback(idx, total_done, "stopped")
                break

            board.touchpin(pin)
            extra = fixed_delay + random.uniform(0.0, max(0.0, random_delay_max))
            if extra > 0:
                time.sleep(extra)

            total_done += 1
            step_callback(idx, total_done, "running")

            # 暂停检查：暂停时关闭串口，便于手动控制使用
            while pause_event.is_set() and not stop_event.is_set():
                close_board()
                step_callback(idx, total_done, "paused")
                time.sleep(0.3)
            if stop_event.is_set():
                step_callback(idx, total_done, "stopped")
                break
            try:
                open_board()
            except Exception as e:
                step_callback(idx, total_done, "error")
                return

        else:
            step_callback(len(actions) - 1, total_done, "finished")
    finally:
        close_board()


# ---------- 键盘控制器（GUI 版）----------

class KeyboardControllerGUI:
    """在独立窗口中提供键盘控制器功能（输入框 + 发送）。"""

    def __init__(self, parent, serial_port: str):
        self.serial_port = serial_port
        self.board = None
        self.win = tk.Toplevel(parent)
        self.win.title("手动控制 - 键盘控制器")
        self.win.geometry("480x320")
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        # 定位到主窗口右侧，避免离得太远
        parent.update_idletasks()
        try:
            px, py = parent.winfo_x(), parent.winfo_y()
            pw = parent.winfo_width()
            screen_w = self.win.winfo_screenwidth()
            x = px + pw + 25
            if x + 480 > screen_w:
                x = max(0, px - 480 - 25)  # 放不下则贴主窗口左侧
            self.win.geometry(f"480x320+{x}+{py}")
        except Exception:
            pass

        ttk.Label(self.win, text="输入数字 1-16 点击对应引脚，或 '@' / 其它串口指令，回车发送。").pack(pady=5)
        self.entry = ttk.Entry(self.win, width=50)
        self.entry.pack(pady=5, padx=10, fill=tk.X)
        self.entry.bind("<Return>", lambda e: self._send())
        ttk.Button(self.win, text="发送", command=self._send).pack(pady=5)
        ttk.Button(self.win, text="关闭", command=self._on_close).pack(pady=5)

        self.log = scrolledtext.ScrolledText(self.win, height=10, width=60, state=tk.DISABLED)
        self.log.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self._open_board()
        self.entry.focus_set()

    def _log(self, msg: str):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def _open_board(self):
        try:
            self.board = TouchBoardBase(port=self.serial_port)
            self.board.open()
            self._log(f"已连接串口: {self.serial_port}")
        except Exception as e:
            self._log(f"串口连接失败: {e}")

    def _send(self):
        if self.board is None:
            self._log("串口未连接，无法发送")
            return
        text = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if not text:
            return
        if text.lower() in ("q", "quit", "exit"):
            self._log("请使用「关闭」按钮退出手动控制")
            return
        if text == "@":
            self._log("发送 '@'，进入/保持工作模式")
            self.board.send_and_read("@")
            return
        try:
            pin = int(text)
            if 1 <= pin <= 16:
                self._log(f"控制引脚: {pin}")
                self.board.touchpin(pin)
            else:
                self._log(f"引脚应在 1-16 之间: {pin}")
        except ValueError:
            self._log(f"发送自定义指令: {text!r}")
            self.board.send_and_read(text)

    def _on_close(self):
        if self.board is not None:
            try:
                self.board.close()
            except Exception:
                pass
            self.board = None
        self.win.destroy()


# ---------- 主应用 ----------

class MacroControllerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("宏控制 - 播放 / 暂停 / 手动控制")
        self.root.minsize(520, 420)
        self.root.geometry("640x520")

        self.config = None
        self.config_path = None
        self.actions = []
        self.macro_thread = None
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()
        self.current_step_index = -1
        self.total_done_count = 0
        self.worker_status = "idle"  # idle | running | paused | finished | stopped | error
        self.dirty = False  # 是否有未保存的编辑

        self._build_ui()
        self._step_queue = []
        self._process_step_updates()
        # 自动加载默认宏文件，无需每次手动选择
        if os.path.isfile(DEFAULT_MACRO_PATH):
            self._load_macro_by_path(DEFAULT_MACRO_PATH)

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)

        ttk.Button(top, text="打开宏文件", command=self._open_macro).pack(side=tk.LEFT, padx=2)
        ttk.Label(top, text="串口:").pack(side=tk.LEFT, padx=(10, 0))
        self.port_var = tk.StringVar(value="COM5")
        ttk.Entry(top, textvariable=self.port_var, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Label(top, text="从第").pack(side=tk.LEFT, padx=(10, 0))
        self.start_step_var = tk.StringVar(value="1")
        self.start_spin = ttk.Spinbox(top, from_=1, to=9999, width=6, textvariable=self.start_step_var)
        self.start_spin.pack(side=tk.LEFT, padx=2)
        ttk.Label(top, text="步开始").pack(side=tk.LEFT, padx=2)

        btn_frame = ttk.Frame(self.root, padding=4)
        btn_frame.pack(fill=tk.X)
        self.btn_start = ttk.Button(btn_frame, text="开始 / 继续播放", command=self._start_or_resume)
        self.btn_start.pack(side=tk.LEFT, padx=2)
        self.btn_pause = ttk.Button(btn_frame, text="暂停", command=self._pause, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, padx=2)
        self.btn_stop = ttk.Button(btn_frame, text="停止", command=self._stop, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=2)
        self.btn_manual = ttk.Button(btn_frame, text="手动控制", command=self._open_manual_control)
        self.btn_manual.pack(side=tk.LEFT, padx=2)
        self.btn_save = ttk.Button(btn_frame, text="保存到原文件", command=self._save_macro, state=tk.DISABLED)
        self.btn_save.pack(side=tk.LEFT, padx=2)

        # 醒目显示：当前执行到第几步（不用数，一眼可见）
        current_frame = ttk.Frame(self.root, padding=6)
        current_frame.pack(fill=tk.X)
        ttk.Label(current_frame, text="当前执行到：", font=("", 10)).pack(side=tk.LEFT, padx=(8, 4))
        self.current_step_display_var = tk.StringVar(value="—")
        self.current_step_label = ttk.Label(
            current_frame, textvariable=self.current_step_display_var, font=("", 12, "bold")
        )
        self.current_step_label.pack(side=tk.LEFT, padx=2)
        ttk.Label(current_frame, text="步", font=("", 10)).pack(side=tk.LEFT, padx=0)

        ttk.Label(self.root, text="步骤列表（已执行=绿，当前=黄，待执行=灰；双击可编辑，编辑后点「保存到原文件」）:").pack(anchor=tk.W, padx=8, pady=2)
        tree_frame = ttk.Frame(self.root, padding=4)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(tree_frame, columns=("content",), show="tree headings", height=18, selectmode="browse")
        self.tree.heading("#0", text="步骤")
        self.tree.column("#0", width=80)
        self.tree.heading("content", text="内容")
        self.tree.column("content", width=400)
        scroll = ttk.Scrollbar(tree_frame)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.configure(command=self.tree.yview)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.tag_configure("done", background="#c8e6c9")
        self.tree.tag_configure("current", background="#fff9c4")
        self.tree.tag_configure("pending", background="#f5f5f5")
        self.tree.bind("<Double-1>", self._on_step_double_click)

        self.status_var = tk.StringVar(value="请先打开宏文件")
        ttk.Label(self.root, textvariable=self.status_var).pack(anchor=tk.W, padx=8, pady=4)
        self.progress_var = tk.StringVar(value="")
        ttk.Label(self.root, textvariable=self.progress_var).pack(anchor=tk.W, padx=8, pady=0)

    def _on_step_double_click(self, event):
        """双击步骤：打开编辑对话框，修改该步内容。"""
        sel = self.tree.selection()
        if not sel or not self.actions:
            return
        item = sel[0]
        try:
            index = int(item)
        except (ValueError, TypeError):
            return
        if index < 0 or index >= len(self.actions):
            return
        self._open_edit_dialog(index, event)

    def _place_near_click(self, win: tk.Toplevel, w: int, h: int, x_root: int, y_root: int, offset: int = 15):
        """将窗口定位到点击位置附近，并保证不超出屏幕。"""
        x = x_root + offset
        y = y_root + offset
        try:
            screen_w = win.winfo_screenwidth()
            screen_h = win.winfo_screenheight()
            if x + w > screen_w:
                x = max(0, screen_w - w)
            if y + h > screen_h:
                y = max(0, screen_h - h)
            if x < 0:
                x = 0
            if y < 0:
                y = 0
        except Exception:
            pass
        win.geometry(f"{w}x{h}+{x}+{y}")

    def _open_edit_dialog(self, index: int, event=None):
        """打开编辑当前步骤的对话框。"""
        action = self.actions[index].copy()
        dlg = tk.Toplevel(self.root)
        dlg.title(f"编辑第 {index + 1} 步")
        dlg.geometry("360x180")
        if event is not None:
            self._place_near_click(dlg, 360, 180, event.x_root, event.y_root)
        dlg.transient(self.root)
        dlg.grab_set()

        is_note = "说明" in action
        if is_note:
            ttk.Label(dlg, text="说明（注释）:").pack(anchor=tk.W, padx=10, pady=(10, 2))
            note_var = tk.StringVar(value=action.get("说明", ""))
            note_entry = ttk.Entry(dlg, textvariable=note_var, width=48)
            note_entry.pack(fill=tk.X, padx=10, pady=2)
        else:
            ttk.Label(dlg, text="引脚 (1-16):").pack(anchor=tk.W, padx=10, pady=(10, 2))
            pin_var = tk.StringVar(value=str(action.get("pin", "")))
            ttk.Entry(dlg, textvariable=pin_var, width=10).pack(anchor=tk.W, padx=10, pady=2)
            ttk.Label(dlg, text="间隔 interval (秒):").pack(anchor=tk.W, padx=10, pady=(8, 2))
            interval_var = tk.StringVar(value=str(action.get("interval", 0)))
            ttk.Entry(dlg, textvariable=interval_var, width=16).pack(anchor=tk.W, padx=10, pady=2)

        def on_ok():
            if is_note:
                new_note = note_var.get().strip()
                self.actions[index] = {"说明": new_note} if new_note else {}
            else:
                try:
                    pin = int(pin_var.get())
                    if not (1 <= pin <= 16):
                        messagebox.showerror("错误", "引脚必须在 1-16 之间", parent=dlg)
                        return
                    interval = float(interval_var.get())
                except ValueError as e:
                    messagebox.showerror("错误", "请输入有效的数字", parent=dlg)
                    return
                self.actions[index] = {"pin": pin, "interval": interval}
            self._refresh_step_list()
            self._set_dirty(True)
            dlg.destroy()

        def on_cancel():
            dlg.destroy()

        btn_frame = ttk.Frame(dlg, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="取消", command=on_cancel).pack(side=tk.LEFT, padx=4)
        if is_note:
            note_entry.focus_set()
        dlg.protocol("WM_DELETE_WINDOW", on_cancel)

    def _set_dirty(self, dirty: bool):
        self.dirty = dirty
        if self.btn_save.winfo_exists():
            self.btn_save.config(state=tk.NORMAL if (dirty and self.config_path) else tk.DISABLED)
        if dirty and self.config_path:
            self.root.title("宏控制 - 播放 / 暂停 / 手动控制 *未保存*")
        else:
            self.root.title("宏控制 - 播放 / 暂停 / 手动控制")

    def _save_macro(self):
        """将当前宏（含编辑后的步骤）保存到原文件。"""
        if not self.config_path or not self.config:
            return
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self._set_dirty(False)
            self.status_var.set(f"已保存到 {os.path.basename(self.config_path)}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")

    def _load_macro_by_path(self, path: str):
        """按路径加载宏文件（供自动加载或打开文件对话框后调用）。"""
        try:
            self.config = load_macro_config(path)
            self.config_path = path
            self.actions = self.config.get("actions", [])
        except Exception as e:
            messagebox.showerror("错误", f"加载宏文件失败: {e}")
            return
        self._refresh_step_list()
        n = len(self.actions)
        self.start_spin.configure(to=max(1, n))
        self.start_step_var.set("1")
        self.status_var.set(f"已加载: {os.path.basename(path)}，共 {n} 步")
        self.progress_var.set("")
        self.current_step_display_var.set("— （共 " + str(n) + " 步）")
        self.current_step_index = -1
        self.total_done_count = 0
        self._set_dirty(False)

    def _open_macro(self):
        path = filedialog.askopenfilename(
            title="选择宏 JSON 文件",
            initialdir=os.path.join(_script_dir, "macros"),
            initialfile="macro_final.json",
            filetypes=[("JSON", "*.json"), ("所有文件", "*.*")],
        )
        if not path:
            return
        self._load_macro_by_path(path)

    def _refresh_step_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, action in enumerate(self.actions):
            label = step_label(action, i)
            self.tree.insert("", tk.END, iid=str(i), text=f"#{i + 1}", values=(label,), tags=("pending",))

    def _update_step_states(self, current_index: int, total_done: int):
        for item in self.tree.get_children():
            i = int(item)
            if i < current_index:
                self.tree.item(item, tags=("done",))
            elif i == current_index:
                self.tree.item(item, tags=("current",))
            else:
                self.tree.item(item, tags=("pending",))
        self.current_step_index = current_index
        self.total_done_count = total_done
        total = len(self.actions)
        step_one = current_index + 1
        self.current_step_display_var.set(f"第 {step_one} / {total}")
        self.progress_var.set(f"已执行 {total_done} 步，当前第 {step_one} / {total} 步")
        # 滚动列表使当前行可见
        try:
            self.tree.see(str(current_index))
        except Exception:
            pass

    def _step_callback(self, current_index: int, total_done: int, status: str):
        self._step_queue.append((current_index, total_done, status))
        self.root.after(0, self._process_step_updates)

    def _process_step_updates(self):
        while self._step_queue:
            current_index, total_done, status = self._step_queue.pop(0)
            self.worker_status = status
            self._update_step_states(current_index, total_done)
            if status == "running":
                self.btn_start.config(state=tk.DISABLED)
                self.btn_pause.config(state=tk.NORMAL)
                self.btn_stop.config(state=tk.NORMAL)
                self.btn_manual.config(state=tk.DISABLED)
            elif status == "paused":
                self.btn_start.config(state=tk.NORMAL)
                self.btn_pause.config(state=tk.DISABLED)
                self.btn_stop.config(state=tk.NORMAL)
                self.btn_manual.config(state=tk.NORMAL)
                self.start_step_var.set(str(current_index + 2))  # 默认从下一步继续
                self.current_step_display_var.set(f"第 {current_index + 1} / {len(self.actions)}（已暂停，继续将从第 {current_index + 2} 步开始）")
                self.status_var.set("已暂停，可点击「手动控制」或「开始/继续播放」")
            elif status in ("finished", "stopped", "error"):
                self.btn_start.config(state=tk.NORMAL)
                self.btn_pause.config(state=tk.DISABLED)
                self.btn_stop.config(state=tk.DISABLED)
                self.btn_manual.config(state=tk.NORMAL)
                if status == "finished":
                    total = len(self.actions)
                    self.current_step_display_var.set(f"已完成（共 {total} 步）")
                    self.status_var.set("宏播放完毕")
                elif status == "stopped":
                    self.current_step_display_var.set(f"第 {current_index + 1} / {len(self.actions)}（已停止）")
                    self.status_var.set("已停止")
                else:
                    self.current_step_display_var.set("—")
                    self.status_var.set("发生错误，请检查串口")

    def _get_start_index(self) -> int:
        try:
            v = int(self.start_step_var.get())
            return max(0, min(v - 1, len(self.actions) - 1))
        except (ValueError, TypeError):
            return 0

    def _start_or_resume(self):
        if not self.actions:
            messagebox.showwarning("提示", "请先打开宏文件")
            return
        start_index = self._get_start_index()
        port = self.port_var.get().strip() or "COM5"
        self.pause_event.clear()
        self.stop_event.clear()
        self.status_var.set("正在播放...")
        self._update_step_states(start_index, self.total_done_count)

        def run():
            play_macro_worker(
                self.config,
                port,
                start_index,
                self.pause_event,
                self.stop_event,
                self._step_callback,
            )

        self.macro_thread = threading.Thread(target=run, daemon=True)
        self.macro_thread.start()
        self.btn_start.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL)
        self.btn_manual.config(state=tk.DISABLED)

    def _pause(self):
        self.pause_event.set()
        self.status_var.set("正在暂停…（当前步执行完后暂停）")

    def _stop(self):
        self.stop_event.set()
        self.pause_event.set()
        self.status_var.set("正在停止…")

    def _open_manual_control(self):
        if self.worker_status == "running":
            messagebox.showinfo("提示", "请先点击「暂停」，等当前步执行完后再使用手动控制")
            return
        port = self.port_var.get().strip() or "COM5"
        KeyboardControllerGUI(self.root, port)

    def run(self):
        self.root.mainloop()


def main():
    app = MacroControllerApp()
    app.run()


if __name__ == "__main__":
    main()
