import time
from pathlib import Path
from datetime import datetime

import tkinter as tk
from PIL import ImageTk, Image
import uiautomator2 as u2


# 连接手机（如果是 USB 连接，直接用设备序列号或空着）
d = u2.connect()


def get_screen_image(save_dir=None):
    """
    同步获取当前手机屏幕内容。

    - 如果指定 save_dir，则把截图保存为 PNG 文件，返回文件路径（str）
    - 如果不指定 save_dir，则返回 PIL.Image.Image 对象（方便在 UI 中直接显示）
    """
    if save_dir:
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".png"
        filepath = save_path / filename
        # 直接保存为文件
        d.screenshot(str(filepath))
        return str(filepath)
    else:
        # 返回一个 PIL.Image.Image 对象
        img = d.screenshot()
        return img


def preview_loop(interval: float = 1.0, save_dir: str = "screenshots"):
    """
    简单的轮询预览：每隔 interval 秒截一张图保存到本地。
    这更适合“同步观察屏幕状态”，而不是高帧率视频。
    """
    device_size = d.window_size()
    print(f"已连接设备: {d.device_info.get('serial', 'unknown')}")
    print(f"屏幕尺寸: {device_size}")
    print(f"开始轮询截图，保存到: {Path(save_dir).resolve()}，间隔: {interval} 秒")

    try:
        while True:
            path = get_screen_image(save_dir)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 已保存截图: {path}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("已停止截图轮询。")


def run_tk_preview(refresh_interval_ms: int = 200):
    """
    使用 Python 内置 Tkinter 实现的简易预览 + 鼠标点击控制：
    - 窗口里显示当前手机屏幕截图
    - 左键点击窗口中的位置，会把该坐标映射到手机上执行 d.click(x, y)

    注意：这里不做缩放，按手机原分辨率显示，这样坐标一一对应。
    """
    device_size = d.window_size()
    # 某些版本的 uiautomator2 返回 (width, height) 元组，这里统一处理为宽高两个整数
    if isinstance(device_size, (tuple, list)) and len(device_size) >= 2:
        width, height = device_size[0], device_size[1]
    elif isinstance(device_size, dict):
        width, height = device_size.get("width"), device_size.get("height")
    else:
        raise RuntimeError(f"无法识别的 window_size 返回值: {device_size!r}")

    root = tk.Tk()
    root.title("ADB 手机屏幕预览（点击操作，可缩放窗口）")

    # 初始窗口大小设为手机分辨率，可以手动拖拽缩放
    root.geometry(f"{width}x{height}")

    # 允许自由缩放
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    label = tk.Label(root, bg="black")
    label.grid(row=0, column=0, sticky="nsew")

    # 记录当前缩放比例 / 偏移，用于坐标还原和拖动手势
    state = {
        "photo": None,
        "scale_x": 1.0,
        "scale_y": 1.0,
        "offset_x": 0,
        "offset_y": 0,
        "img_w": width,
        "img_h": height,
        "press_x": None,
        "press_y": None,
        "updating": False,
    }

    def _map_to_phone_coords(x, y):
        """
        将 label 内部坐标 (x, y) 映射为手机真实坐标。
        - 考虑图片在 label 中居中显示时的偏移
        - 如果点击在黑色边缘（图片外面），返回 None
        """
        # 去掉图片在 label 中的偏移
        local_x = x - state["offset_x"]
        local_y = y - state["offset_y"]

        # 超出图片区域则不处理
        if local_x < 0 or local_y < 0 or local_x >= state["img_w"] or local_y >= state["img_h"]:
            return None

        real_x = int(local_x * state["scale_x"])
        real_y = int(local_y * state["scale_y"])
        return real_x, real_y

    def update_image():
        # 避免上一次截图还没完成就开始下一次，导致卡顿
        if state.get("updating"):
            root.after(refresh_interval_ms, update_image)
            return
        state["updating"] = True

        # 当前窗口内可用的显示区域大小
        label_width = label.winfo_width() or width
        label_height = label.winfo_height() or height

        img = get_screen_image()
        if not isinstance(img, Image.Image):
            # 理论上 get_screen_image 在 save_dir=None 时返回的是 PIL.Image
            img = Image.open(img)

        # 按等比例缩放以适配窗口（保持纵横比）
        scale = min(label_width / float(width), label_height / float(height))
        new_w = max(1, int(width * scale))
        new_h = max(1, int(height * scale))
        resized = img.resize((new_w, new_h), Image.LANCZOS)

        # 记录缩放比例和偏移（用于点击映射）
        state["scale_x"] = width / float(new_w)
        state["scale_y"] = height / float(new_h)
        state["img_w"] = new_w
        state["img_h"] = new_h
        # 居中显示时，记录图片相对 label 左上角的偏移
        state["offset_x"] = (label_width - new_w) // 2
        state["offset_y"] = (label_height - new_h) // 2

        photo = ImageTk.PhotoImage(resized)
        state["photo"] = photo  # 防止被 GC
        label.config(image=photo)

        state["updating"] = False
        root.after(refresh_interval_ms, update_image)

    def on_button_press(event):
        # 记录按下时的坐标（用于区分点击和滑动）
        state["press_x"] = event.x
        state["press_y"] = event.y

    def on_button_release(event):
        if state["press_x"] is None or state["press_y"] is None:
            return

        start_x, start_y = state["press_x"], state["press_y"]
        end_x, end_y = event.x, event.y

        # 计算拖动距离（基于缩放后坐标）
        dx = end_x - start_x
        dy = end_y - start_y
        dist2 = dx * dx + dy * dy

        # 映射到手机坐标
        start_mapped = _map_to_phone_coords(start_x, start_y)
        end_mapped = _map_to_phone_coords(end_x, end_y)

        # 重置
        state["press_x"] = None
        state["press_y"] = None

        # 如果按下或抬起在图片外，就不处理
        if start_mapped is None or end_mapped is None:
            print("点击/拖动在图片外，忽略。")
            return

        # 阈值：移动距离很小就当单击
        if dist2 < 5 * 5:
            real_x, real_y = end_mapped
            print(f"单击 -> 手机坐标: ({real_x}, {real_y})")
            try:
                d.click(real_x, real_y)
            except Exception as e:
                print(f"点击失败: {e}")
        else:
            x0, y0 = start_mapped
            x1, y1 = end_mapped
            print(f"滑动 -> 手机坐标: ({x0}, {y0}) -> ({x1}, {y1})")
            try:
                d.swipe(x0, y0, x1, y1, 0.1)
            except Exception as e:
                print(f"滑动失败: {e}")

    def on_right_click(event):
        # 右键 = 返回键
        print("右键点击：发送返回键。")
        try:
            d.press("back")
        except Exception as e:
            print(f"返回键失败: {e}")

    def on_mouse_wheel(event):
        # 鼠标滚轮 -> 垂直滑动
        # event.delta 在 Windows 下一般是 ±120 的倍数
        direction = -1 if event.delta > 0 else 1  # 向上滚 = 内容向下滚
        x_center = width // 2
        # 以屏幕中间为基准做一次短滑动
        span = height // 4  # 滑动距离
        y0 = int(height // 2 + direction * span / 2)
        y1 = int(height // 2 - direction * span / 2)
        print(f"滚轮滑动：方向 {direction}, ({x_center}, {y0}) -> ({x_center}, {y1})")
        try:
            d.swipe(x_center, y0, x_center, y1, 0.1)
        except Exception as e:
            print(f"滚轮滑动失败: {e}")

    # 左键按下 / 抬起 -> 点击或滑动
    label.bind("<ButtonPress-1>", on_button_press)
    label.bind("<ButtonRelease-1>", on_button_release)
    # 右键 -> 返回键
    label.bind("<Button-3>", on_right_click)
    # 滚轮 -> 上下滑动
    label.bind("<MouseWheel>", on_mouse_wheel)

    print(f"已连接设备: {d.device_info.get('serial', 'unknown')}")
    print(f"屏幕尺寸: {device_size}")
    print("窗口中左键点击 = 手机上点击同一坐标。")

    update_image()
    root.mainloop()


if __name__ == "__main__":
    # 直接运行本文件时，打开 Tk 预览窗口并支持鼠标点击控制
    # 可自行调整 refresh_interval_ms（越小帧率越高，但 CPU/USB 压力越大）
    run_tk_preview(refresh_interval_ms=100)