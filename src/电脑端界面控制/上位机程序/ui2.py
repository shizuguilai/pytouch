import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
from datetime import datetime
import json

type2Pins = {1:['0','1'],2:['2','3'],3:['4','5'],4:['6','7'],5:['8','9'],6:['a','b'],7:['c','d'],8:['e','f'],9:['g','h'],10:['i','j'],11:['k','l'],12:['m','n'],13:['o','p'],14:['q','r'],15:['s','t'],16:['u','v']}

class ButtonGridApp:
    def __init__(self, root):
        self.root = root
        self.root.title("32按钮串口控制界面")
        self.root.geometry("800x650")  # 增加窗口尺寸以容纳更多按钮
        
        # 串口相关变量
        self.serial_port1 = None  # 第一个串口
        self.serial_port2 = None  # 第二个串口
        self.serial_connected1 = False
        self.serial_connected2 = False

        self.moveDict = {}

        self.upPort = 1
        self.downPort = 1
        self.leftPort = 1
        self.rightPort = 1
        self.upPins = '1,2,3,4'
        self.downPins = '4,3,2,1'
        self.leftPins = '13,14,15,16'
        self.rightPins = '16,15,14,13'
        self.initMoveDict()
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重，使界面可调整大小
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # 添加第一个串口控制区域
        serial_frame1 = ttk.LabelFrame(main_frame, text="串口1设置", padding="5")
        serial_frame1.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 串口选择下拉菜单
        ttk.Label(serial_frame1, text="选择串口:").grid(row=0, column=0, padx=(0, 5))
        self.port_combobox1 = ttk.Combobox(serial_frame1, state="readonly", width=15)
        self.port_combobox1.grid(row=0, column=1, padx=(0, 10))
        
        # 波特率选择
        ttk.Label(serial_frame1, text="波特率:").grid(row=0, column=2, padx=(0, 5))
        self.baud_combobox1 = ttk.Combobox(serial_frame1, values=["9600", "115200", "57600", "38400", "19200", "4800"], 
                                         state="readonly", width=10)
        self.baud_combobox1.grid(row=0, column=3, padx=(0, 10))
        self.baud_combobox1.set("115200")  # 默认波特率
        
        # 连接/断开按钮
        self.connect_button1 = ttk.Button(serial_frame1, text="连接", command=lambda: self.toggle_serial_connection(1))
        self.connect_button1.grid(row=0, column=4, padx=(0, 5))
        
        # 串口状态显示
        self.serial_status1 = ttk.Label(serial_frame1, text="未连接", foreground="red")
        self.serial_status1.grid(row=0, column=5, padx=(10, 0))
        
        # 添加第二个串口控制区域
        serial_frame2 = ttk.LabelFrame(main_frame, text="串口2设置", padding="5")
        serial_frame2.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 串口选择下拉菜单
        ttk.Label(serial_frame2, text="选择串口:").grid(row=0, column=0, padx=(0, 5))
        self.port_combobox2 = ttk.Combobox(serial_frame2, state="readonly", width=15)
        self.port_combobox2.grid(row=0, column=1, padx=(0, 10))
        
        # 波特率选择
        ttk.Label(serial_frame2, text="波特率:").grid(row=0, column=2, padx=(0, 5))
        self.baud_combobox2 = ttk.Combobox(serial_frame2, values=["9600", "115200", "57600", "38400", "19200", "4800"], 
                                         state="readonly", width=10)
        self.baud_combobox2.grid(row=0, column=3, padx=(0, 10))
        self.baud_combobox2.set("115200")  # 默认波特率
        
        # 连接/断开按钮
        self.connect_button2 = ttk.Button(serial_frame2, text="连接", command=lambda: self.toggle_serial_connection(2))
        self.connect_button2.grid(row=0, column=4, padx=(0, 5))
        
        # 串口状态显示
        self.serial_status2 = ttk.Label(serial_frame2, text="未连接", foreground="red")
        self.serial_status2.grid(row=0, column=5, padx=(10, 0))
        
        # 刷新串口按钮（共用）
        refresh_button = ttk.Button(serial_frame2, text="刷新串口", command=self.refresh_serial_ports)
        refresh_button.grid(row=0, column=6, padx=(20, 0))
        
        # 添加标题
        title_label = ttk.Label(main_frame, text="32按钮控制面板", font=("Arial", 16, "bold"))
        title_label.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # 创建按钮容器框架
        buttons_container = ttk.Frame(main_frame)
        buttons_container.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建第一个串口的按钮框架
        button_frame1 = ttk.LabelFrame(buttons_container, text="串口1按钮", padding="5")
        button_frame1.grid(row=0, column=0, padx=(0, 10), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建第二个串口的按钮框架
        button_frame2 = ttk.LabelFrame(buttons_container, text="串口2按钮", padding="5")
        button_frame2.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置按钮容器框架的网格
        buttons_container.columnconfigure(0, weight=1)
        buttons_container.columnconfigure(1, weight=1)
        buttons_container.rowconfigure(0, weight=1)
        
        # 配置两个按钮框架的网格
        for i in range(4):
            button_frame1.columnconfigure(i, weight=1)
            button_frame1.rowconfigure(i, weight=1)
            button_frame2.columnconfigure(i, weight=1)
            button_frame2.rowconfigure(i, weight=1)
        
        # 创建第一个串口的16个按钮
        self.buttons1 = []
        for i in range(16):
            row = i // 4
            col = i % 4
            
            button = ttk.Button(
                button_frame1, 
                text=f"串口1-按钮 {i+1}"
            )
            
            # 绑定按下和释放事件
            button.bind("<ButtonPress>", lambda event, btn_id=i+1: self.button_action(btn_id, 0, event, 1))
            button.bind("<ButtonRelease>", lambda event, btn_id=i+1: self.button_action(btn_id, 1, event, 1))
            
            button.grid(row=row, column=col, padx=3, pady=3, sticky=(tk.W, tk.E, tk.N, tk.S))
            self.buttons1.append(button)
        
        # 创建第二个串口的16个按钮
        self.buttons2 = []
        for i in range(16):
            row = i // 4
            col = i % 4
            
            button = ttk.Button(
                button_frame2, 
                text=f"串口2-按钮 {i+1}"
            )
            
            # 绑定按下和释放事件
            button.bind("<ButtonPress>", lambda event, btn_id=i+1: self.button_action(btn_id, 0, event, 2))
            button.bind("<ButtonRelease>", lambda event, btn_id=i+1: self.button_action(btn_id, 1, event, 2))
            
            button.grid(row=row, column=col, padx=3, pady=3, sticky=(tk.W, tk.E, tk.N, tk.S))
            self.buttons2.append(button)
        
        # 添加上滑和下滑按钮框架
        scroll_frame = ttk.Frame(main_frame)
        scroll_frame.grid(row=4, column=0, columnspan=2, pady=(10, 5), sticky=(tk.W, tk.E))
        
        # 配置滚动按钮框架的网格
        for i in range(4):
            scroll_frame.columnconfigure(i, weight=1)
        
        # 添加上滑按钮
        self.up_button = ttk.Button(
            scroll_frame, 
            text="上滑", 
            command=lambda: self.scroll_button_action("上滑", self.upPort)
        )
        self.up_button.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # 添加下滑按钮
        self.down_button = ttk.Button(
            scroll_frame, 
            text="下滑", 
            command=lambda: self.scroll_button_action("下滑", self.downPort)
        )
        self.down_button.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # 添加左滑按钮
        self.left_button = ttk.Button(
            scroll_frame, 
            text="左滑", 
            command=lambda: self.scroll_button_action("左滑", self.leftPort)
        )
        self.left_button.grid(row=0, column=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # 添加右滑按钮
        self.right_button = ttk.Button(
            scroll_frame, 
            text="右滑", 
            command=lambda: self.scroll_button_action("右滑", self.rightPort)
        )
        self.right_button.grid(row=0, column=3, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # 添加状态显示标签
        self.status_label = ttk.Label(main_frame, text="就绪", relief=tk.SUNKEN, padding=(5, 2))
        self.status_label.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(15, 0))
        
        # 添加事件日志文本框
        log_label = ttk.Label(main_frame, text="事件日志:")
        log_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(15, 5))
        
        self.log_text = tk.Text(main_frame, height=10, width=70)
        self.log_text.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=7, column=2, sticky=(tk.N, tk.S), pady=(0, 10))
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # 配置主框架的行权重，使日志区域可以扩展
        main_frame.rowconfigure(7, weight=1)
        
        # 初始化时刷新串口列表
        self.refresh_serial_ports()
    def array_to_string(self,arr):
        """
        将数组转换为逗号分隔的字符串
        
        参数:
        arr -- 要转换的数组（列表）
        
        返回:
        逗号分隔的字符串
        """
        return ':'.join(str(x) for x in arr)
    def initMoveDict(self):
        with open('move.json','r') as f:
            self.moveDict = json.load(f)
        self.upPort = self.moveDict['up'][0]
        self.downPort = self.moveDict['down'][0]
        self.leftPort = self.moveDict['left'][0]
        self.rightPort = self.moveDict['right'][0]
        self.upPins = self.array_to_string(self.moveDict['up'][1])
        self.downPins = self.array_to_string(self.moveDict['down'][1])
        self.leftPins = self.array_to_string(self.moveDict['left'][1])
        self.rightPins = self.array_to_string(self.moveDict['right'][1])
        print(self.moveDict)
    def refresh_serial_ports(self):
        """刷新可用的串口列表"""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_combobox1['values'] = port_list
        self.port_combobox2['values'] = port_list
        if port_list:
            self.port_combobox1.set(port_list[0])
            if len(port_list) > 1:
                self.port_combobox2.set(port_list[1])
            else:
                self.port_combobox2.set(port_list[0])
        else:
            self.port_combobox1.set('')
            self.port_combobox2.set('')
    
    def toggle_serial_connection(self, port_num):
        """连接或断开串口"""
        if port_num == 1:
            if not self.serial_connected1:
                # 尝试连接串口1
                port = self.port_combobox1.get()
                baud = self.baud_combobox1.get()
                
                if not port:
                    self.log_message("错误: 请选择串口1")
                    return
                
                try:
                    self.serial_port1 = serial.Serial(port, int(baud), timeout=1)
                    self.serial_connected1 = True
                    self.connect_button1.config(text="断开")
                    self.serial_status1.config(text="已连接", foreground="green")
                    self.log_message(f"串口1连接成功: {port} 波特率: {baud}")
                except Exception as e:
                    self.log_message(f"串口1连接失败: {str(e)}")
            else:
                # 断开串口1连接
                if self.serial_port1 and self.serial_port1.is_open:
                    self.serial_port1.close()
                self.serial_connected1 = False
                self.connect_button1.config(text="连接")
                self.serial_status1.config(text="未连接", foreground="red")
                self.log_message("串口1已断开")
        
        elif port_num == 2:
            if not self.serial_connected2:
                # 尝试连接串口2
                port = self.port_combobox2.get()
                baud = self.baud_combobox2.get()
                
                if not port:
                    self.log_message("错误: 请选择串口2")
                    return
                
                try:
                    self.serial_port2 = serial.Serial(port, int(baud), timeout=1)
                    self.serial_connected2 = True
                    self.connect_button2.config(text="断开")
                    self.serial_status2.config(text="已连接", foreground="green")
                    self.log_message(f"串口2连接成功: {port} 波特率: {baud}")
                except Exception as e:
                    self.log_message(f"串口2连接失败: {str(e)}")
            else:
                # 断开串口2连接
                if self.serial_port2 and self.serial_port2.is_open:
                    self.serial_port2.close()
                self.serial_connected2 = False
                self.connect_button2.config(text="连接")
                self.serial_status2.config(text="未连接", foreground="red")
                self.log_message("串口2已断开")
    
    def send_serial_data(self, button_id, action, port_num):
        """通过串口发送数据"""
        if port_num == 1:
            if self.serial_connected1 and self.serial_port1 and self.serial_port1.is_open:
                try:
                    data = f"{button_id},{action}\n"
                    print(f"串口1发送: {data.strip()}")
                    self.serial_port1.write(data.encode())
                    self.serial_port1.flush()
                    self.log_message(f"串口1发送: {data.strip()}")
                except Exception as e:
                    self.log_message(f"串口1发送失败: {str(e)}")
                    # 发送失败时尝试重新连接
                    self.serial_connected1 = False
                    self.connect_button1.config(text="连接")
                    self.serial_status1.config(text="未连接", foreground="red")
        elif port_num == 2:
            if self.serial_connected2 and self.serial_port2 and self.serial_port2.is_open:
                try:
                    data = f"{button_id},{action}\n"
                    print(f"串口2发送: {data.strip()}")
                    self.serial_port2.write(data.encode())
                    self.serial_port2.flush()
                    self.log_message(f"串口2发送: {data.strip()}")
                except Exception as e:
                    self.log_message(f"串口2发送失败: {str(e)}")
                    # 发送失败时尝试重新连接
                    self.serial_connected2 = False
                    self.connect_button2.config(text="连接")
                    self.serial_status2.config(text="未连接", foreground="red")
    
    def send_scroll_command(self, command, port_num):
        """发送滑动命令到串口"""
        if port_num == 1:
            if self.serial_connected1 and self.serial_port1 and self.serial_port1.is_open:
                try:
                    # 根据命令发送不同的字符
                    if command == "上滑":
                        data = "x,"+ self.upPins + "\n"
                    elif command == "下滑":
                        data = "y,"+ self.downPins + "\n"
                    elif command == "左滑":
                        data = "l,"+ self.leftPins + "\n"
                    elif command == "右滑":
                        data = "r,"+ self.rightPins + "\n"
                    else:
                        return
                    self.serial_port1.write(data.encode())
                    self.serial_port1.flush()
                    self.log_message(f"串口1发送滑动命令: {command} -> {data.strip()}")
                except Exception as e:
                    self.log_message(f"串口1发送失败: {str(e)}")
                    # 发送失败时尝试重新连接
                    self.serial_connected1 = False
                    self.connect_button1.config(text="连接")
                    self.serial_status1.config(text="未连接", foreground="red")
        elif port_num == 2:
            if self.serial_connected2 and self.serial_port2 and self.serial_port2.is_open:
                try:
                    # 根据命令发送不同的字符
                    if command == "上滑":
                        data = "x,"+ self.upPins + "\n"
                    elif command == "下滑":
                        data = "y,"+ self.downPins + "\n"
                    elif command == "左滑":
                        data = "l,"+ self.leftPins + "\n"
                    elif command == "右滑":
                        data = "r,"+ self.rightPins + "\n"
                    else:
                        return
                    self.serial_port2.write(data.encode())
                    self.serial_port2.flush()
                    self.log_message(f"串口2发送滑动命令: {command} -> {data.strip()}")
                except Exception as e:
                    self.log_message(f"串口2发送失败: {str(e)}")
                    # 发送失败时尝试重新连接
                    self.serial_connected2 = False
                    self.connect_button2.config(text="连接")
                    self.serial_status2.config(text="未连接", foreground="red")
    
    def button_action(self, button_id, action, event, port_num):
        """统一的按钮事件处理函数
        
        参数:
            button_id: 按钮编号 (1-16)
            action: 动作类型 (0表示按下, 1表示抬起)
            event: 事件对象，包含事件详细信息
            port_num: 串口号 (1或2)
        """
        # 更新状态标签
        action_text = "按下" if action == 0 else "抬起"
        port_text = f"串口{port_num}"
        self.status_label.config(text=f"{port_text} 按钮 {button_id} {action_text}")
        
        # 获取事件详细信息
        event_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # 记录到日志
        log_entry = f"时间: {event_time} - {port_text} - 按钮: {button_id} - 动作: {action_text}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)  # 自动滚动到底部
        
        # 通过串口发送数据
        self.send_serial_data(button_id, action, port_num)
        
        # 根据按钮ID和动作执行不同的操作
        self.handle_button_event(button_id, action, event, port_num)
    
    def scroll_button_action(self, command, port_num):
        """处理滑动按钮点击事件"""
        # 更新状态标签
        port_text = f"串口{port_num}"
        self.status_label.config(text=f"{port_text} 执行{command}操作")
        
        # 获取当前时间
        event_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # 记录到日志
        log_entry = f"时间: {event_time} - {port_text} - 执行: {command}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)  # 自动滚动到底部
        
        # 通过串口发送滑动命令
        self.send_scroll_command(command, port_num)
    
    def handle_button_event(self, button_id, action, event, port_num):
        """处理按钮事件的具体逻辑
        
        你可以在这里根据按钮ID和动作类型添加具体的功能代码
        """
        # 示例：根据不同的按钮和动作执行不同的操作
        port_text = f"串口{port_num}"
        
        if action == 0:
            # 按钮按下时的操作
            print(f"{port_text} 按钮 {button_id} 被按下")
        elif action == 1:
            # 按钮抬起时的操作
            print(f"{port_text} 按钮 {button_id} 被抬起")
    
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