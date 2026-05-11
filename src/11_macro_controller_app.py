#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
宏控制桌面应用 V6 - 双设备并行控制 + 共享制造流程

V6 相对 V5 的变化：
- 配置文件新版（11_macro.json）把 "制造武器 / 制造子弹 / 制造药品 / 制造防具"
  这类制造流程抽到顶层的 crafting_options[].actions 中，所有账号共用一份。
- 双击步骤编辑制造步骤时，修改会直接写回顶层模板 —— 改一次，所有账号同步生效。
- 兼容读取旧格式：若打开的 JSON 里账号还带 crafting_sections，则优先使用账号内的。

其它功能与 V5 一致：
- 两个独立设备面板，左右并排同时显示，互不干扰。
- 各自独立的串口（默认 COM8 / COM9）。
- 各自独立的账号勾选、制造功能勾选、播放线程、进度显示。
- 步骤列表双击编辑、保存到原文件、手动控制。
- 点击「开始/继续播放」时自动关闭未关闭的手动控制窗口。
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

DEFAULT_MACRO_PATH = os.path.join(_script_dir, "macros", "11_macro.json")

from touch_board_base import TouchBoardBase

# 串口枚举依赖 pyserial（已经被 TouchBoardBase 间接依赖）。
# 这里做一次"软导入"，缺失也不影响其它功能。
try:
    from serial.tools import list_ports as _serial_list_ports
except Exception:  # pragma: no cover - 仅在缺少 pyserial 时触发
    _serial_list_ports = None


# ---------- 共用工具函数 ----------


def list_serial_ports():
    """
    枚举当前系统所有可用串口。
    返回 [(device, description), ...]，按设备名升序。
    若 pyserial 未安装则返回空列表。
    """
    if _serial_list_ports is None:
        return []
    ports = []
    try:
        for p in _serial_list_ports.comports():
            ports.append((p.device, p.description or ""))
    except Exception:
        return []
    ports.sort(key=lambda x: x[0])
    return ports

def load_macro_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def split_account_name(name: str, device_index: int) -> str:
    """
    账号 name 中允许使用 '&' 区分左右两个设备显示的名字。
    例: "小白&臭屁股大号" -> 左(0)="小白"，右(1)="臭屁股大号"
    若没有 '&'，两侧显示相同；若只有一侧为空，则用原始整体名兜底。
    """
    if not name:
        return name
    if "&" not in name:
        return name
    parts = name.split("&", 1)
    side = parts[device_index] if 0 <= device_index < len(parts) else parts[0]
    side = side.strip()
    return side or name


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
        device_index: int,
        device_name: str,
        default_port: str,
        header_color: str = "#1565c0",
    ):
        self.frame = parent_frame
        self.root = root
        # 0 = 左侧设备，对应账号名 "&" 之前；1 = 右侧设备，对应 "&" 之后
        self.device_index = device_index
        self.device_name = device_name
        self._header_color = header_color

        self.config = None
        self.config_path = None
        self.actions = []
        self.macro_thread = None
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()
        self.skip_event = threading.Event()   # 用于「立即下一步」
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
        self._manual_ctrl: "KeyboardControllerGUI | None" = None  # 当前手动控制窗口

        # 等待状态信息（由 worker 线程更新，由 UI 轮询读取）
        self._wait_info: dict = {"active": False, "remaining": 0.0}

        # 程序内部修改 port_var 时不应被视为"用户修改"
        self._suppress_port_trace = False

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
        # 串口被用户修改时：标题刷新 + 标记为 dirty 以便保存到 JSON
        self.port_var.trace_add("write", lambda *_: self._on_port_changed())
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
            self.frame, text="制造功能（所有账号共享同一套流程，勾选即执行，默认全选）", padding=6
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
        self.btn_scan_ports = ttk.Button(
            btn_frame, text="扫描串口", command=self._open_port_scan_dialog
        )
        self.btn_scan_ports.pack(side=tk.LEFT, padx=2)
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

    def _get_crafting_actions(self, craft_id: str, account: dict):
        """
        取得某个制造流程的 actions。
        新格式：直接从顶层 crafting_options[craft_id].actions 获取（所有账号共用）。
        旧格式兼容：若账号里仍有 crafting_sections，则优先使用账号内的。
        返回 (actions_list, source_tuple_prefix):
          - ("craft_shared", craft_id) 表示共享模板（来自顶层 crafting_options）
          - ("craft_account", acc_idx, craft_id) 表示账号内独有（旧格式）
        """
        # 兼容：账号内的 crafting_sections 优先（用于加载旧文件）
        for sect in account.get("crafting_sections", []) or []:
            if sect.get("id") == craft_id:
                return sect.get("actions", []), ("craft_account", craft_id)

        for opt in self.crafting_options:
            if opt.get("id") == craft_id:
                return opt.get("actions", []), ("craft_shared", craft_id)
        return [], ("craft_shared", craft_id)

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

        # 从配置中应用本设备对应的设备名/串口
        self._apply_device_settings_from_config()

        if self.accounts:
            for acc in self.accounts:
                vid = acc.get("id", len(self.account_vars) + 1)
                var = tk.BooleanVar(value=True)
                self.account_vars[vid] = var
                display_name = split_account_name(
                    acc.get("name", f"账号{vid}"), self.device_index
                )
                ttk.Checkbutton(
                    self.account_cb_frame,
                    text=display_name,
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

    def _apply_device_settings_from_config(self):
        """
        从 config['devices'][device_index] 读取本设备的 name 与 port，
        同步到 UI（标题、串口输入框）。若配置缺失，则保持当前值。
        """
        if not self.config:
            return
        devices = self.config.get("devices") or []
        if 0 <= self.device_index < len(devices):
            dev = devices[self.device_index] or {}
            name = dev.get("name")
            port = dev.get("port")
            if name:
                self.device_name = str(name)
            if port:
                # 屏蔽追踪写回，避免 set 时把面板置为 dirty
                self._suppress_port_trace = True
                try:
                    self.port_var.set(str(port))
                finally:
                    self._suppress_port_trace = False

    def _on_port_changed(self):
        """串口输入框变化时的回调（用户改动 / 程序回写）。"""
        if self._suppress_port_trace:
            self._update_header()
            return
        self._update_header()
        if self.config_path and self.config:
            self._set_dirty(True)

    def _sync_device_settings_to_config(self):
        """把当前 UI 上的串口/设备名写回 config['devices'][device_index]。"""
        if not self.config:
            return
        devices = self.config.setdefault("devices", [])
        while len(devices) <= self.device_index:
            devices.append({"id": len(devices) + 1})
        dev = devices[self.device_index]
        if not isinstance(dev, dict):
            dev = {}
            devices[self.device_index] = dev
        dev["id"] = dev.get("id", self.device_index + 1)
        dev["name"] = self.device_name
        dev["port"] = self.port_var.get().strip()

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

            # 按 crafting_options 的顺序执行被勾选的制造流程（共享模板）
            for opt in self.crafting_options:
                cid = opt.get("id")
                if cid not in selected_craft_ids:
                    continue
                craft_actions, src_prefix = self._get_crafting_actions(cid, acc)
                for step_idx, a in enumerate(craft_actions):
                    self.actions.append(a)
                    if src_prefix[0] == "craft_shared":
                        # 共享模板编辑时会写回顶层 crafting_options
                        self._flat_source_map.append(("craft_shared", cid, step_idx))
                    else:
                        # 旧格式账号内独有，编辑时仍写回该账号
                        self._flat_source_map.append(("craft_account", acc_idx, cid, step_idx))

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
    # 面板标题更新（反映运行状态）
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

    def _source_desc(self, flat_index: int) -> str:
        """返回步骤来源的可读描述，用于编辑对话框提示。"""
        if flat_index >= len(self._flat_source_map):
            return ""
        src = self._flat_source_map[flat_index]
        if src[0] == "global":
            return "来源：全局动作"
        if src[0] == "pre":
            acc_idx = src[1]
            name = self.accounts[acc_idx].get("name", f"账号{acc_idx + 1}") if acc_idx < len(self.accounts) else "?"
            return f"来源：账号「{name}」的 pre_actions"
        if src[0] == "craft_shared":
            cid = src[1]
            opt_name = next((o.get("name", cid) for o in self.crafting_options if o.get("id") == cid), cid)
            return f"来源：共享制造流程「{opt_name}」（修改将对所有账号生效）"
        if src[0] == "craft_account":
            acc_idx, cid = src[1], src[2]
            name = self.accounts[acc_idx].get("name", f"账号{acc_idx + 1}") if acc_idx < len(self.accounts) else "?"
            return f"来源：账号「{name}」独有的制造流程「{cid}」（旧格式）"
        if src[0] == "post":
            acc_idx = src[1]
            name = self.accounts[acc_idx].get("name", f"账号{acc_idx + 1}") if acc_idx < len(self.accounts) else "?"
            return f"来源：账号「{name}」的 post_actions"
        return ""

    def _open_edit_dialog(self, index: int, event=None):
        action = self.actions[index].copy()
        dlg = tk.Toplevel(self.root)
        dlg.title(f"[{self.device_name}] 编辑第 {index + 1} 步")
        dlg.geometry("420x220")
        if event is not None:
            self._place_near_click(dlg, 420, 220, event.x_root, event.y_root)
        dlg.transient(self.root)
        dlg.grab_set()

        desc = self._source_desc(index)
        if desc:
            desc_lbl = tk.Label(dlg, text=desc, fg="#555", anchor=tk.W, justify=tk.LEFT, wraplength=400)
            desc_lbl.pack(fill=tk.X, padx=10, pady=(8, 2))

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

            self._sync_edit_to_config(index, new_action)
            # 修改共享模板会影响列表里所有账号下的同一条，重建后再刷新显示
            self._rebuild_actions_from_selection()
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
            elif src[0] == "craft_shared":
                _, cid, step_idx = src
                for opt in self.config.get("crafting_options", []):
                    if opt.get("id") == cid:
                        opt.setdefault("actions", [])[step_idx] = new_action
                        break
            elif src[0] == "craft_account":
                _, acc_idx, cid, step_idx = src
                for sect in self.config["accounts"][acc_idx].get("crafting_sections", []) or []:
                    if sect.get("id") == cid:
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
            self._sync_device_settings_to_config()
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
            initialfile="11_macro.json",
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
                    self.root.after(100, self._open_manual_control)
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
        # 自动关闭未关闭的手动控制窗口
        self._close_manual_ctrl()
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
        # 若已有手动控制窗口，先关闭再重新打开
        self._close_manual_ctrl()
        ctrl = KeyboardControllerGUI(self.root, port)
        self._manual_ctrl = ctrl
        # 用户手动关闭窗口时清除引用
        def _on_user_close():
            ctrl._on_close()
            self._manual_ctrl = None
        ctrl.win.protocol("WM_DELETE_WINDOW", _on_user_close)

    def _close_manual_ctrl(self):
        """关闭当前手动控制窗口（若存在）。"""
        if self._manual_ctrl is not None:
            try:
                if self._manual_ctrl.win.winfo_exists():
                    self._manual_ctrl._on_close()
            except Exception:
                pass
            self._manual_ctrl = None

    # ------------------------------------------------------------------
    # 串口扫描弹窗
    # ------------------------------------------------------------------

    def _open_port_scan_dialog(self):
        """弹出串口扫描窗口：列出系统当前所有串口，可应用到本设备。"""
        if _serial_list_ports is None:
            messagebox.showerror(
                "缺少依赖",
                "未检测到 pyserial（serial.tools.list_ports）。\n"
                "请安装：pip install pyserial",
            )
            return

        dlg = tk.Toplevel(self.root)
        dlg.title(f"扫描串口 - {self.device_name}")
        dlg.geometry("520x320")
        dlg.transient(self.root)
        try:
            self.root.update_idletasks()
            x = self.root.winfo_x() + 80
            y = self.root.winfo_y() + 80
            dlg.geometry(f"520x320+{x}+{y}")
        except Exception:
            pass

        tip = ttk.Label(
            dlg,
            text=(
                f"当前 {self.device_name} 的串口为："
                f"{self.port_var.get().strip() or '(空)'}\n"
                "双击列表中的串口、或选中后点「应用到本设备」即可替换。\n"
                "替换后请点主界面的「保存到原文件」写入 11_macro.json。"
            ),
            justify=tk.LEFT,
            anchor=tk.W,
            foreground="#555",
        )
        tip.pack(fill=tk.X, padx=10, pady=(10, 6))

        list_frame = ttk.Frame(dlg, padding=(10, 0))
        list_frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(
            list_frame,
            columns=("device", "desc"),
            show="headings",
            selectmode="browse",
            height=8,
        )
        tree.heading("device", text="串口")
        tree.heading("desc", text="描述")
        tree.column("device", width=110, anchor=tk.W)
        tree.column("desc", width=370, anchor=tk.W)
        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        status_var = tk.StringVar(value="")
        status_lbl = ttk.Label(dlg, textvariable=status_var, foreground="#1565c0")
        status_lbl.pack(anchor=tk.W, padx=10, pady=(2, 0))

        def refresh():
            for item in tree.get_children():
                tree.delete(item)
            ports = list_serial_ports()
            if not ports:
                status_var.set("未发现任何串口（请确认设备已连接、驱动已安装）")
                return
            current = self.port_var.get().strip()
            selected_iid = None
            for device, desc in ports:
                iid = tree.insert("", tk.END, values=(device, desc))
                if device == current:
                    selected_iid = iid
            if selected_iid:
                tree.selection_set(selected_iid)
                tree.see(selected_iid)
            status_var.set(f"共发现 {len(ports)} 个串口")

        def apply_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("提示", "请先在列表中选择一个串口", parent=dlg)
                return
            values = tree.item(sel[0], "values")
            if not values:
                return
            new_port = str(values[0])
            old_port = self.port_var.get().strip()
            if new_port == old_port:
                status_var.set(f"已是当前串口：{new_port}")
                return
            self.port_var.set(new_port)
            status_var.set(f"已将 {self.device_name} 的串口设为 {new_port}（记得点「保存到原文件」）")

        btn_frame = ttk.Frame(dlg, padding=10)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="刷新", command=refresh).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            btn_frame, text="应用到本设备", command=apply_selected
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="关闭", command=dlg.destroy).pack(side=tk.RIGHT, padx=2)

        tree.bind("<Double-1>", lambda _e: apply_selected())
        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)
        refresh()


# ---------- 双设备主应用 ----------

class MultiDeviceApp:
    # 当配置文件不可用时的兜底默认值
    _FALLBACK_DEVICES = [
        {"name": "设备1", "port": "COM8"},
        {"name": "设备2", "port": "COM9"},
    ]

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("宏控制 V6 - 双设备并行控制（共享制造流程）")
        self.root.minsize(900, 600)
        self.root.geometry("1500x860")

        # 启动前先读取一次配置，决定两个面板的初始 name/port
        devices = self._read_initial_devices(DEFAULT_MACRO_PATH)

        # 左右可拖动分割面板
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        left = ttk.Frame(paned)
        right = ttk.Frame(paned)
        paned.add(left, weight=1)
        paned.add(right, weight=1)

        self.panel1 = DevicePanel(
            left, self.root,
            device_index=0,
            device_name=devices[0]["name"],
            default_port=devices[0]["port"],
            header_color="#1565c0",
        )
        self.panel2 = DevicePanel(
            right, self.root,
            device_index=1,
            device_name=devices[1]["name"],
            default_port=devices[1]["port"],
            header_color="#2e7d32",
        )

    def _read_initial_devices(self, path: str):
        """从配置文件读取 devices 字段，缺失则用兜底默认值。返回长度为 2 的 list。"""
        result = [dict(d) for d in self._FALLBACK_DEVICES]
        if not os.path.isfile(path):
            return result
        try:
            cfg = load_macro_config(path)
        except Exception:
            return result
        devices = cfg.get("devices") or []
        for i in range(2):
            if i < len(devices) and isinstance(devices[i], dict):
                name = devices[i].get("name")
                port = devices[i].get("port")
                if name:
                    result[i]["name"] = str(name)
                if port:
                    result[i]["port"] = str(port)
        return result

    def run(self):
        self.root.mainloop()


def main():
    app = MultiDeviceApp()
    app.run()


if __name__ == "__main__":
    main()
