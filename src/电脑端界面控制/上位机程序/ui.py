import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
from datetime import datetime

type2Pins = {1:['0','1'],2:['2','3'],3:['4','5'],4:['6','7'],5:['8','9'],6:['a','b'],7:['c','d'],8:['e','f'],9:['g','h'],10:['i','j'],11:['k','l'],12:['m','n'],13:['o','p'],14:['q','r'],15:['s','t'],16:['u','v']}


class ButtonGridApp:
    def __init__(self, root):
        self.root = root
        self.root.title("16按钮串口控制界面")
        self.root.geometry("600x550")  # 增加高度以容纳新按钮
        
        # 串口相关变量
        self.serial_port = None
        self.serial_connected = False
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重，使界面可调整大小
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 添加串口控制区域
        serial_frame = ttk.LabelFrame(main_frame, text="串口设置", padding="5")
        serial_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 串口选择下拉菜单
        ttk.Label(serial_frame, text="选择串口:").grid(row=0, column=0, padx=(0, 5))
        self.port_combobox = ttk.Combobox(serial_frame, state="readonly", width=15)
        self.port_combobox.grid(row=0, column=1, padx=(0, 10))
        
        # 波特率选择
        ttk.Label(serial_frame, text="波特率:").grid(row=0, column=2, padx=(0, 5))
        self.baud_combobox = ttk.Combobox(serial_frame, values=["9600", "115200", "57600", "38400", "19200", "4800"], 
                                         state="readonly", width=10)
        self.baud_combobox.grid(row=0, column=3, padx=(0, 10))
        self.baud_combobox.set("115200")  # 默认波特率
        
        # 连接/断开按钮
        self.connect_button = ttk.Button(serial_frame, text="连接", command=self.toggle_serial_connection)
        self.connect_button.grid(row=0, column=4, padx=(0, 5))
        
        # 刷新串口按钮
        refresh_button = ttk.Button(serial_frame, text="刷新", command=self.refresh_serial_ports)
        refresh_button.grid(row=0, column=5)
        
        # 串口状态显示
        self.serial_status = ttk.Label(serial_frame, text="未连接", foreground="red")
        self.serial_status.grid(row=0, column=6, padx=(10, 0))
        
        # 添加标题
        title_label = ttk.Label(main_frame, text="16按钮控制面板", font=("Arial", 16, "bold"))
        title_label.grid(row=1, column=0, columnspan=2, pady=(0, 15))
        
        # 创建按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置按钮框架的网格
        for i in range(4):
            button_frame.columnconfigure(i, weight=1)
            button_frame.rowconfigure(i, weight=1)
        
        # 创建16个按钮
        self.buttons = []
        for i in range(16):
            row = i // 4
            col = i % 4
            
            button = ttk.Button(
                button_frame, 
                text=f"按钮 {i+1}"
            )
            
            # 绑定按下和释放事件
            button.bind("<ButtonPress>", lambda event, btn_id=i+1: self.button_action(btn_id, 0, event))
            button.bind("<ButtonRelease>", lambda event, btn_id=i+1: self.button_action(btn_id, 1, event))
            
            button.grid(row=row, column=col, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
            self.buttons.append(button)
        
        # 添加上滑和下滑按钮框架
        scroll_frame = ttk.Frame(main_frame)
        scroll_frame.grid(row=3, column=0, columnspan=2, pady=(10, 5), sticky=(tk.W, tk.E))
        
        # 配置滚动按钮框架的网格
        scroll_frame.columnconfigure(0, weight=1)
        scroll_frame.columnconfigure(1, weight=1)
        
        # 添加上滑按钮
        self.up_button = ttk.Button(
            scroll_frame, 
            text="上滑", 
            command=lambda: self.scroll_button_action("上滑")
        )
        self.up_button.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # 添加下滑按钮
        self.down_button = ttk.Button(
            scroll_frame, 
            text="下滑", 
            command=lambda: self.scroll_button_action("下滑")
        )
        self.down_button.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # 添加状态显示标签
        self.status_label = ttk.Label(main_frame, text="就绪", relief=tk.SUNKEN, padding=(5, 2))
        self.status_label.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(15, 0))
        
        # 添加事件日志文本框
        log_label = ttk.Label(main_frame, text="事件日志:")
        log_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(15, 5))
        
        self.log_text = tk.Text(main_frame, height=10, width=70)
        self.log_text.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=6, column=2, sticky=(tk.N, tk.S), pady=(0, 10))
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # 配置主框架的行权重，使日志区域可以扩展
        main_frame.rowconfigure(6, weight=1)
        
        # 初始化时刷新串口列表
        self.refresh_serial_ports()
    
    def refresh_serial_ports(self):
        """刷新可用的串口列表"""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_combobox['values'] = port_list
        if port_list:
            self.port_combobox.set(port_list[0])
        else:
            self.port_combobox.set('')
    
    def toggle_serial_connection(self):
        """连接或断开串口"""
        if not self.serial_connected:
            # 尝试连接串口
            port = self.port_combobox.get()
            baud = self.baud_combobox.get()
            
            if not port:
                self.log_message("错误: 请选择串口")
                return
            
            try:
                self.serial_port = serial.Serial(port, int(baud), timeout=1)
                self.serial_connected = True
                self.connect_button.config(text="断开")
                self.serial_status.config(text="已连接", foreground="green")

                self.log_message(f"串口连接成功: {port} 波特率: {baud}")
                # self.serial_port.write('@'.encode('utf-8'))
            except Exception as e:
                self.log_message(f"串口连接失败: {str(e)}")
        else:
            # 断开串口连接
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.serial_connected = False
            self.connect_button.config(text="连接")
            self.serial_status.config(text="未连接", foreground="red")
            self.log_message("串口已断开")
    
    def send_serial_data(self, button_id, action):
        """通过串口发送数据"""
        if self.serial_connected and self.serial_port and self.serial_port.is_open:
            try:
                # 构建发送的数据格式: "按钮ID:动作"
                data = f"{button_id},{action}\n"  # 例如: "B01:按下" 或 "B01:抬起"
                # data = type2Pins[button_id][action]
                print(data)
                self.serial_port.write(data.encode())
                self.serial_port.flush()
                self.log_message(f"串口发送: {data.strip()}")
            except Exception as e:
                self.log_message(f"串口发送失败: {str(e)}")
                # 发送失败时尝试重新连接
                self.serial_connected = False
                self.connect_button.config(text="连接")
                self.serial_status.config(text="未连接", foreground="red")
    
    def send_scroll_command(self, command):
        """发送滑动命令到串口"""
        if self.serial_connected and self.serial_port and self.serial_port.is_open:
            try:
                # 根据命令发送不同的字符
                if command == "上滑":
                    data = "x,0\n"
                elif command == "下滑":
                    data = "y,0\n"
                else:
                    return
                self.serial_port.write(data.encode())
                self.serial_port.flush()
                self.log_message(f"串口发送滑动命令: {command} -> {data}")
            except Exception as e:
                self.log_message(f"串口发送失败: {str(e)}")
                # 发送失败时尝试重新连接
                self.serial_connected = False
                self.connect_button.config(text="连接")
                self.serial_status.config(text="未连接", foreground="red")
    
    def button_action(self, button_id, action, event):
        """统一的按钮事件处理函数
        
        参数:
            button_id: 按钮编号 (1-16)
            action: 动作类型 (0表示按下, 1表示抬起)
            event: 事件对象，包含事件详细信息
        """
        # 更新状态标签
        action_text = "按下" if action == 0 else "抬起"
        self.status_label.config(text=f"按钮 {button_id} {action_text}")
        
        # 获取事件详细信息
        event_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # 记录到日志
        log_entry = f"时间: {event_time} - 按钮: {button_id} - 动作: {action_text}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)  # 自动滚动到底部
        
        # 通过串口发送数据
        self.send_serial_data(button_id, action)
        
        # 根据按钮ID和动作执行不同的操作
        self.handle_button_event(button_id, action, event)
    
    def scroll_button_action(self, command):
        """处理滑动按钮点击事件"""
        # 更新状态标签
        self.status_label.config(text=f"执行{command}操作")
        
        # 获取当前时间
        event_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # 记录到日志
        log_entry = f"时间: {event_time} - 执行: {command}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)  # 自动滚动到底部
        
        # 通过串口发送滑动命令
        self.send_scroll_command(command)
    
    def handle_button_event(self, button_id, action, event):
        """处理按钮事件的具体逻辑
        
        你可以在这里根据按钮ID和动作类型添加具体的功能代码
        """
        # 示例：根据不同的按钮和动作执行不同的操作
        if action == 0:
            # 按钮按下时的操作
            if button_id == 1:
                print(f"按钮 {button_id} 被按下 - 执行功能 A")
                # 在这里添加按钮1按下时的功能代码
            elif button_id == 2:
                print(f"按钮 {button_id} 被按下 - 执行功能 B")
                # 在这里添加按钮2按下时的功能代码
            # 可以继续为其他按钮添加按下时的功能...
            else:
                print(f"按钮 {button_id} 被按下")
        
        elif action == 1:
            # 按钮抬起时的操作
            if button_id == 1:
                print(f"按钮 {button_id} 被抬起 - 停止功能 A")
                # 在这里添加按钮1抬起时的功能代码
            elif button_id == 2:
                print(f"按钮 {button_id} 被抬起 - 停止功能 B")
                # 在这里添加按钮2抬起时的功能代码
            # 可以继续为其他按钮添加抬起时的功能...
            else:
                print(f"按钮 {button_id} 被抬起")
    
    def log_message(self, message):
        """添加消息到日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)  # 自动滚动到底部

if __name__ == "__main__":
    root = tk.Tk()
    app = ButtonGridApp(root)
    root.mainloop()