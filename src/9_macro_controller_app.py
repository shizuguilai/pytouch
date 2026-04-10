#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
宏控制桌面应用 V5 - 快速停止 & 立即下一步

升级内容（相对于 V4）：
- 停止响应：改用可中断式等待（每 0.1s 检查一次），点击「停止」后约 0.1s 内退出
- 新增「立即下一步」按钮：跳过当前剩余等待时间，立即触发下一个引脚操作
- 状态栏实时倒计时（等待中，剩余 Xs）
- 默认宏文件切换为 9_macro.json
"""

import json
import os
import sys
import threading
import time
import random
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

DEFAULT_MACRO_PATH = os.path.join(_script_dir, "macros", "9_macro.json")

from touch_board_base import TouchBoardBase


# ---------- 共用工具函数 ----------

def load_macro_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def step_label(action: dict, index: int) -> str:
    if "说明" in action:
        return f"步骤 {index + 1}: 说明 - {action.get('说明', '')}"
    if "pin" in action:
        return f"步骤 {index + 1}: pin {action.get('pin', '?')}, interval {action.get('interval', 0):.2f}s"
    return f"步骤 {index + 1}: (未知)"


def interruptible_sleep(
    seconds: float,
    stop_event: threading.Event,
    skip_event: threading.Event,
    chunk: float = 0.1,
    wait_info: dict = None,
) -> bool:
    """
    可中断式等待。每 chunk 秒检查一次 stop_event / skip_event。
    返回 True 表示被中断（stop 或 skip），False 表示正常等待完毕。
    wait_info: 可选 dict {"active": bool, "remaining": float}，由本函数线程安全更新。
    """
    if seconds <= 0:
        return False
    deadline = time.monotonic() + seconds
    if wait_info is not None:
        wait_info["active"] = True
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            if stop_event.is_set() or skip_event.is_set():
                return True
            if wait_info is not None:
                wait_info["remaining"] = remaining
            time.sleep(min(chunk, remaining))
    finally:
        if wait_info is not None:
            wait_info["active"] = False
            wait_info["remaining"] = 0.0


def play_macro_worker(
    config: dict,
    port: str,
    start_index: int,
    pause_event: threading.Event,
    stop_event: threading.Event,
    skip_event: threading.Event,
    step_callback,
    wait_info: dict = None,
):
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
    except Exception:
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

            # ---- 执行前等待（interval）——可中断 ----
            interval = float(action.get("interval", 0.0))
            if interval > 0:
                interruptible_sleep(interval, stop_event, skip_event, wait_info=wait_info)
                skip_event.clear()  # 消耗本次 skip，防止连续跳过

            if stop_event.is_set():
                step_callback(idx, total_done, "stopped")
                break

            # ---- 执行引脚操作 ----
            board.touchpin(pin)

            # ---- 执行后固定 + 随机延迟——可中断 ----
            extra = fixed_delay + random.uniform(0.0, max(0.0, random_delay_max))
            if extra > 0:
                interruptible_sleep(extra, stop_event, skip_event, wait_info=wait_info)
                skip_event.clear()  # 消耗本次 skip

            total_done += 1
            step_callback(idx, total_done, "running")

            # ---- 暂停处理 ----
            while pause_event.is_set() and not stop_event.is_set():
                close_board()
                step_callback(idx, total_done, "paused")
                time.sleep(0.3)
            if stop_event.is_set():
                step_callback(idx, total_done, "stopped")
                break
            try:
                open_board()
            except Exception:
                step_callback(idx, total_done, "error")
                return
        else:
            step_callback(len(actions) - 1, total_done, "finished")
    finally:
        close_board()


# ---------- 键盘控制器弹窗 ----------

class KeyboardControllerGUI:
    def __init__(self, parent_win: tk.Misc, serial_port: str):
        self.serial_port = serial_port
        self.board = None
        self.win = tk.Toplevel(parent_win)
        self.win.title(f"手动控制 [{serial_port}]")
        self.win.geometry("480x320")
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        try:
            parent_win.update_idletasks()
            px, py = parent_win.winfo_x(), parent_win.winfo_y()
            pw = parent_win.winfo_width()
            sw = self.win.winfo_screenwidth()
            x = px + pw + 25
            if x + 480 > sw:
                x = max(0, px - 480 - 25)
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


# ---------- 单设备控制面板 ----------

class DevicePanel:
    """
    一个完整的设备控制面板，嵌入到 parent_frame 内。
    root 是主 Tk 窗口，用于 after() 调度和 Toplevel 弹窗。
    """

    def __init__(
        self,
        parent_frame: ttk.Frame,
        root: tk.Tk,
        device_name: str,
        default_port: str,
        header_color: str = "#1565c0",
    ):
        self.frame = parent_frame
        self.root = root
        self.device_name = device_name
        self._header_color = header_color

        self.config = None
        self.config_path = None
        self.actions = []
        self.macro_thread = None
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()
        self.skip_event = threading.Event()   # 新增：用于「立即下一步」
        self.current_step_index = -1
        self.total_done_count = 0
        self.worker_status = "idle"
        self.dirty = False

        self.global_actions = []
        self.accounts = []
        self.account_vars = {}

        self.crafting_options = []
        self.crafting_vars = {}

        self._flat_source_map = []
        self._step_queue = []

        # 等待状态信息（由 worker 线程更新，由 UI 轮询读取）
        self._wait_info: dict = {"active": False, "remaining": 0.0}

        self._build_ui(default_port)
        self._process_step_updates()
        self._poll_wait_status()  # 启动倒计时轮询
        if os.path.isfile(DEFAULT_MACRO_PATH):
            self._load_macro_by_path(DEFAULT_MACRO_PATH)

    # ------------------------------------------------------------------
    # UI 构建（parent 均为 self.frame）
    # ------------------------------------------------------------------

    def _build_ui(self, default_port: str):
        # 设备标题栏
        self.header_var = tk.StringVar(value=self.device_name)
        header = tk.Label(
            self.frame,
            textvariable=self.header_var,
            font=("", 13, "bold"),
            bg=self._header_color, fg="white",
            anchor=tk.W, padx=12, pady=6,
        )
        header.pack(fill=tk.X)

        top = ttk.Frame(self.frame, padding=8)
        top.pack(fill=tk.X)

        ttk.Button(top, text="打开宏文件", command=self._open_macro).pack(side=tk.LEFT, padx=2)
        ttk.Label(top, text="串口:").pack(side=tk.LEFT, padx=(10, 0))
        self.port_var = tk.StringVar(value=default_port)
        ttk.Entry(top, textvariable=self.port_var, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Label(top, text="从第").pack(side=tk.LEFT, padx=(10, 0))
        self.start_step_var = tk.StringVar(value="1")
        self.start_spin = ttk.Spinbox(
            top, from_=1, to=9999, width=6, textvariable=self.start_step_var
        )
        self.start_spin.pack(side=tk.LEFT, padx=2)
        ttk.Label(top, text="步开始").pack(side=tk.LEFT, padx=2)

        self.account_cb_frame = ttk.LabelFrame(
            self.frame, text="执行账号（勾选即参与播放，默认全选）", padding=6
        )
        self.account_cb_frame.pack(fill=tk.X, padx=8, pady=(4, 2))

        self.crafting_cb_frame = ttk.LabelFrame(
            self.frame, text="制造功能（勾选即执行，默认全选）", padding=6
        )
        self.crafting_cb_frame.pack(fill=tk.X, padx=8, pady=(2, 4))

        btn_frame = ttk.Frame(self.frame, padding=4)
        btn_frame.pack(fill=tk.X)
        self.btn_start = ttk.Button(btn_frame, text="开始 / 继续播放", command=self._start_or_resume)
        self.btn_start.pack(side=tk.LEFT, padx=2)
        self.btn_pause = ttk.Button(btn_frame, text="暂停", command=self._pause, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, padx=2)
        self.btn_stop = ttk.Button(btn_frame, text="停止", command=self._stop, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=2)
        self.btn_skip = ttk.Button(
            btn_frame, text="立即下一步", command=self._skip_step, state=tk.DISABLED
        )
        self.btn_skip.pack(side=tk.LEFT, padx=2)
        self.btn_manual = ttk.Button(btn_frame, text="手动控制", command=self._open_manual_control)
        self.btn_manual.pack(side=tk.LEFT, padx=2)
        self.btn_save = ttk.Button(
            btn_frame, text="保存到原文件", command=self._save_macro, state=tk.DISABLED
        )
        self.btn_save.pack(side=tk.LEFT, padx=2)

        current_frame = ttk.Frame(self.frame, padding=6)
        current_frame.pack(fill=tk.X)
        ttk.Label(current_frame, text="当前执行到：", font=("", 10)).pack(side=tk.LEFT, padx=(8, 4))
        self.current_step_display_var = tk.StringVar(value="—")
        ttk.Label(
            current_frame,
            textvariable=self.current_step_display_var,
            font=("", 12, "bold"),
        ).pack(side=tk.LEFT, padx=2)
        ttk.Label(current_frame, text="步", font=("", 10)).pack(side=tk.LEFT)

        ttk.Label(
            self.frame,
            text="步骤列表（已执行=绿，当前=黄，待执行=灰；双击可编辑，编辑后点「保存到原文件」）:",
        ).pack(anchor=tk.W, padx=8, pady=2)

        tree_frame = ttk.Frame(self.frame, padding=4)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(
            tree_frame, columns=("content",), show="tree headings", height=14, selectmode="browse"
        )
        self.tree.heading("#0", text="步骤")
        self.tree.column("#0", width=80)
        self.tree.heading("content", text="内容")
        self.tree.column("content", width=440)
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
        ttk.Label(self.frame, textvariable=self.status_var).pack(anchor=tk.W, padx=8, pady=4)
        self.progress_var = tk.StringVar(value="")
        ttk.Label(self.frame, textvariable=self.progress_var).pack(anchor=tk.W, padx=8, pady=0)

    # ------------------------------------------------------------------
    # 加载宏文件
    # ------------------------------------------------------------------

    def _load_macro_by_path(self, path: str):
        try:
            self.config = load_macro_config(path)
            self.config_path = path
        except Exception as e:
            messagebox.showerror("错误", f"[{self.device_name}] 加载宏文件失败: {e}")
            return

        for w in self.account_cb_frame.winfo_children():
            w.destroy()
        self.account_vars.clear()

        for w in self.crafting_cb_frame.winfo_children():
            w.destroy()
        self.crafting_vars.clear()

        self.global_actions = list(self.config.get("global_actions", []))
        self.accounts = self.config.get("accounts", [])
        self.crafting_options = self.config.get("crafting_options", [])

        if self.accounts:
            for acc in self.accounts:
                vid = acc.get("id", len(self.account_vars) + 1)
                var = tk.BooleanVar(value=True)
                self.account_vars[vid] = var
                ttk.Checkbutton(
                    self.account_cb_frame,
                    text=acc.get("name", f"账号{vid}"),
                    variable=var,
                    command=self._on_selection_changed,
                ).pack(side=tk.LEFT, padx=12, pady=2)
            self.account_cb_frame.pack(fill=tk.X, padx=8, pady=(4, 2))
        else:
            self.account_cb_frame.pack_forget()

        if self.crafting_options:
            for opt in self.crafting_options:
                cid = opt.get("id")
                var = tk.BooleanVar(value=True)
                self.crafting_vars[cid] = var
                ttk.Checkbutton(
                    self.crafting_cb_frame,
                    text=opt.get("name", cid),
                    variable=var,
                    command=self._on_selection_changed,
                ).pack(side=tk.LEFT, padx=16, pady=2)
            self.crafting_cb_frame.pack(fill=tk.X, padx=8, pady=(2, 4))
        else:
            self.crafting_cb_frame.pack_forget()

        self._rebuild_actions_from_selection()
        self.progress_var.set("")
        self._set_dirty(False)
        self._update_header()

    # ------------------------------------------------------------------
    # 重建扁平步骤列表
    # ------------------------------------------------------------------

    def _rebuild_actions_from_selection(self):
        self.actions = []
        self._flat_source_map = []

        selected_craft_ids = {
            cid for cid, var in self.crafting_vars.items() if var.get()
        }

        for g_idx, a in enumerate(self.global_actions):
            self.actions.append(a)
            self._flat_source_map.append(("global", g_idx))

        for acc_idx, acc in enumerate(self.accounts):
            vid = acc.get("id", acc_idx + 1)
            if not self.account_vars.get(vid, tk.BooleanVar(value=True)).get():
                continue

            for step_idx, a in enumerate(acc.get("pre_actions", [])):
                self.actions.append(a)
                self._flat_source_map.append(("pre", acc_idx, step_idx))

            for section in acc.get("crafting_sections", []):
                sect_id = section.get("id")
                if sect_id not in selected_craft_ids:
                    continue
                for step_idx, a in enumerate(section.get("actions", [])):
                    self.actions.append(a)
                    self._flat_source_map.append(("craft", acc_idx, sect_id, step_idx))

            for step_idx, a in enumerate(acc.get("post_actions", [])):
                self.actions.append(a)
                self._flat_source_map.append(("post", acc_idx, step_idx))

        self._refresh_step_list()
        n = len(self.actions)
        self.start_spin.configure(to=max(1, n))
        self.start_step_var.set("1")
        self.current_step_index = -1
        self.total_done_count = 0

        n_accs = sum(1 for v in self.account_vars.values() if v.get())
        selected_craft_names = [
            opt["name"] for opt in self.crafting_options if opt["id"] in selected_craft_ids
        ]
        craft_str = "、".join(selected_craft_names) if selected_craft_names else "（无）"
        self.current_step_display_var.set(f"— （共 {n} 步）")
        self.status_var.set(f"已选 {n} 步 | {n_accs} 个账号 | 制造功能: {craft_str}")

    def _on_selection_changed(self):
        self._rebuild_actions_from_selection()

    # ------------------------------------------------------------------
    # 面板标题更新
    # ------------------------------------------------------------------

    def _update_header(self, extra: str = ""):
        port = self.port_var.get().strip() or "?"
        text = f"{self.device_name}  ({port})"
        if extra:
            text += f"  ▶ {extra}"
        self.header_var.set(text)

    # ------------------------------------------------------------------
    # 步骤列表与编辑
    # ------------------------------------------------------------------

    def _refresh_step_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, action in enumerate(self.actions):
            self.tree.insert(
                "", tk.END, iid=str(i), text=f"#{i + 1}",
                values=(step_label(action, i),), tags=("pending",)
            )

    def _on_step_double_click(self, event):
        sel = self.tree.selection()
        if not sel or not self.actions:
            return
        try:
            index = int(sel[0])
        except (ValueError, TypeError):
            return
        if 0 <= index < len(self.actions):
            self._open_edit_dialog(index, event)

    def _place_near_click(self, win, w, h, x_root, y_root, offset=15):
        x, y = x_root + offset, y_root + offset
        try:
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            x = max(0, min(x, sw - w))
            y = max(0, min(y, sh - h))
        except Exception:
            pass
        win.geometry(f"{w}x{h}+{x}+{y}")

    def _open_edit_dialog(self, index: int, event=None):
        action = self.actions[index].copy()
        dlg = tk.Toplevel(self.root)
        dlg.title(f"[{self.device_name}] 编辑第 {index + 1} 步")
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
                new_action = {"说明": note_var.get().strip()} if note_var.get().strip() else {}
            else:
                try:
                    pin = int(pin_var.get())
                    if not (1 <= pin <= 16):
                        messagebox.showerror("错误", "引脚必须在 1-16 之间", parent=dlg)
                        return
                    interval = float(interval_var.get())
                except ValueError:
                    messagebox.showerror("错误", "请输入有效的数字", parent=dlg)
                    return
                new_action = {"pin": pin, "interval": interval}

            self.actions[index] = new_action
            self._sync_edit_to_config(index, new_action)
            self._refresh_step_list()
            self._set_dirty(True)
            dlg.destroy()

        btn_frame = ttk.Frame(dlg, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="取消", command=dlg.destroy).pack(side=tk.LEFT, padx=4)
        if is_note:
            note_entry.focus_set()
        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)

    def _sync_edit_to_config(self, flat_index: int, new_action: dict):
        if not self.config or flat_index >= len(self._flat_source_map):
            return
        src = self._flat_source_map[flat_index]
        try:
            if src[0] == "global":
                self.config["global_actions"][src[1]] = new_action
            elif src[0] == "pre":
                self.config["accounts"][src[1]]["pre_actions"][src[2]] = new_action
            elif src[0] == "craft":
                _, acc_idx, sect_id, step_idx = src
                for sect in self.config["accounts"][acc_idx]["crafting_sections"]:
                    if sect["id"] == sect_id:
                        sect["actions"][step_idx] = new_action
                        break
            elif src[0] == "post":
                self.config["accounts"][src[1]]["post_actions"][src[2]] = new_action
        except (IndexError, KeyError, TypeError):
            pass

    # ------------------------------------------------------------------
    # 保存 / 打开
    # ------------------------------------------------------------------

    def _set_dirty(self, dirty: bool):
        self.dirty = dirty
        self.btn_save.config(state=tk.NORMAL if (dirty and self.config_path) else tk.DISABLED)

    def _save_macro(self):
        if not self.config_path or not self.config:
            return
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self._set_dirty(False)
            self.status_var.set(f"已保存到 {os.path.basename(self.config_path)}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")

    def _open_macro(self):
        path = filedialog.askopenfilename(
            title="选择宏 JSON 文件",
            initialdir=os.path.join(_script_dir, "macros"),
            initialfile="9_macro.json",
            filetypes=[("JSON", "*.json"), ("所有文件", "*.*")],
        )
        if path:
            self._load_macro_by_path(path)

    # ------------------------------------------------------------------
    # 播放控制
    # ------------------------------------------------------------------

    def _update_step_states(self, current_index: int, total_done: int, from_callback: bool = True):
        total = len(self.actions)
        for item in self.tree.get_children():
            i = int(item)
            if from_callback:
                tag = "done" if i <= current_index else ("current" if i == current_index + 1 else "pending")
            else:
                tag = "done" if i < current_index else ("current" if i == current_index else "pending")
            self.tree.item(item, tags=(tag,))

        next_1based = (
            (current_index + 2 if current_index + 1 < total else current_index + 1)
            if from_callback
            else current_index + 1
        )
        self.current_step_index = current_index
        self.total_done_count = total_done
        self.current_step_display_var.set(f"第 {next_1based} / {total}")
        self.progress_var.set(f"已执行 {total_done} 步，当前第 {next_1based} / {total} 步")
        self.start_step_var.set(str(next_1based))
        try:
            row = current_index + 1 if (from_callback and current_index + 1 < total) else current_index
            self.tree.see(str(row))
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
                self.btn_skip.config(state=tk.NORMAL)
                self.btn_manual.config(state=tk.DISABLED)
                self._update_header("运行中")

            elif status == "paused":
                self.btn_start.config(state=tk.NORMAL)
                self.btn_pause.config(state=tk.DISABLED)
                self.btn_stop.config(state=tk.NORMAL)
                self.btn_skip.config(state=tk.DISABLED)
                self.btn_manual.config(state=tk.NORMAL)
                self.start_step_var.set(str(current_index + 2))
                self.current_step_display_var.set(
                    f"第 {current_index + 1} / {len(self.actions)}（已暂停，继续将从第 {current_index + 2} 步开始）"
                )
                self.status_var.set("已暂停，可点击「手动控制」或「开始/继续播放」")
                self._update_header("已暂停")

            elif status in ("finished", "stopped", "error"):
                self.btn_start.config(state=tk.NORMAL)
                self.btn_pause.config(state=tk.DISABLED)
                self.btn_stop.config(state=tk.DISABLED)
                self.btn_skip.config(state=tk.DISABLED)
                self.btn_manual.config(state=tk.NORMAL)
                total = len(self.actions)
                if status == "finished":
                    self.current_step_display_var.set(f"已完成（共 {total} 步）")
                    self.status_var.set("宏播放完毕")
                    self._update_header("已完成")
                elif status == "stopped":
                    self.current_step_display_var.set(f"第 {current_index + 1} / {total}（已停止）")
                    self.status_var.set("已停止")
                    self._update_header("已停止")
                else:
                    self.current_step_display_var.set("—")
                    self.status_var.set("发生错误，请检查串口")
                    self._update_header("错误")

    def _poll_wait_status(self):
        """每 200ms 轮询一次等待状态，更新倒计时显示。"""
        try:
            if self.worker_status == "running":
                info = self._wait_info
                if info["active"]:
                    rem = info["remaining"]
                    self.status_var.set(
                        f"等待中，剩余 {rem:.1f}s —— 点「立即下一步」可跳过"
                    )
                else:
                    self.status_var.set("正在播放...")
            self.root.after(200, self._poll_wait_status)
        except tk.TclError:
            pass  # 窗口已销毁，停止轮询

    def _get_start_index(self) -> int:
        try:
            v = int(self.start_step_var.get())
            return max(0, min(v - 1, len(self.actions) - 1))
        except (ValueError, TypeError):
            return 0

    def _start_or_resume(self):
        if not self.actions:
            messagebox.showwarning("提示", f"[{self.device_name}] 请先打开宏文件，且至少勾选一个账号和一个制造功能")
            return
        start_index = self._get_start_index()
        port = self.port_var.get().strip() or "COM5"
        self.pause_event.clear()
        self.stop_event.clear()
        self.skip_event.clear()
        self.status_var.set("正在播放...")
        self._update_step_states(start_index, self.total_done_count, from_callback=False)

        run_config = {
            "fixed_delay": self.config.get("fixed_delay", 0.2) if self.config else 0.2,
            "random_delay": self.config.get("random_delay", 5.0) if self.config else 5.0,
            "actions": self.actions,
        }

        wait_info = self._wait_info
        wait_info["active"] = False
        wait_info["remaining"] = 0.0

        def run():
            play_macro_worker(
                run_config, port, start_index,
                self.pause_event, self.stop_event, self.skip_event,
                self._step_callback, wait_info=wait_info,
            )

        self.macro_thread = threading.Thread(target=run, daemon=True)
        self.macro_thread.start()
        self.btn_start.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL)
        self.btn_skip.config(state=tk.NORMAL)
        self.btn_manual.config(state=tk.DISABLED)

    def _pause(self):
        self.pause_event.set()
        self.status_var.set("正在暂停…（当前步执行完后暂停）")

    def _stop(self):
        self.stop_event.set()
        self.pause_event.set()
        self.status_var.set("正在停止…（约 0.1s 内响应）")

    def _skip_step(self):
        """跳过当前等待，立即执行下一个引脚操作。"""
        self.skip_event.set()

    def _open_manual_control(self):
        if self.worker_status == "running":
            messagebox.showinfo("提示", "请先点击「暂停」，等当前步执行完后再使用手动控制")
            return
        port = self.port_var.get().strip() or "COM5"
        KeyboardControllerGUI(self.root, port)


# ---------- 双设备主应用 ----------

class MultiDeviceApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("宏控制 V5 - 快速停止 & 立即下一步")
        self.root.minsize(900, 600)
        self.root.geometry("1500x860")

        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        left = ttk.Frame(paned)
        right = ttk.Frame(paned)
        paned.add(left, weight=1)
        paned.add(right, weight=1)

        self.panel1 = DevicePanel(left,  self.root, "设备1", "COM8", header_color="#1565c0")
        self.panel2 = DevicePanel(right, self.root, "设备2", "COM9", header_color="#2e7d32")

    def run(self):
        self.root.mainloop()


def main():
    app = MultiDeviceApp()
    app.run()


if __name__ == "__main__":
    main()
