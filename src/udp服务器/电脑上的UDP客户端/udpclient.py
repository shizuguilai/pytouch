import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading

class UDPClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("UDP客户端 - ESP8266连接工具")
        
        self.sock = None
        self.esp_ip = "255.255.255.255"  # 默认广播IP
        self.esp_port = 8888
        self.is_broadcast = False  # 广播模式标志
        
        # 初始化UDP socket
        self.init_socket()
        self.setup_ui()
        
        # 默认启用广播模式
        self.broadcast_var.set(True)
        self.toggle_broadcast()
        
    def init_socket(self):
        """初始化UDP socket"""
        try:
            if self.sock:
                self.sock.close()
                
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 设置广播选项
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # 设置超时时间
            self.sock.settimeout(3.0)
            
        except Exception as e:
            messagebox.showerror("Socket错误", f"初始化Socket失败: {e}")
        
    def setup_ui(self):
        # 连接设置框架
        connection_frame = tk.Frame(self.root)
        connection_frame.pack(padx=10, pady=5, fill=tk.X)
        
        tk.Label(connection_frame, text="目标IP:").grid(row=0, column=0, sticky=tk.W)
        self.ip_entry = tk.Entry(connection_frame, width=15)
        self.ip_entry.insert(0, self.esp_ip)
        self.ip_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(connection_frame, text="端口:").grid(row=0, column=2, padx=(20,0))
        self.port_entry = tk.Entry(connection_frame, width=8)
        self.port_entry.insert(0, str(self.esp_port))
        self.port_entry.grid(row=0, column=3, padx=5)
        
        # 广播模式复选框
        self.broadcast_var = tk.BooleanVar()
        self.broadcast_check = tk.Checkbutton(connection_frame, text="广播模式", 
                                            variable=self.broadcast_var,
                                            command=self.toggle_broadcast)
        self.broadcast_check.grid(row=0, column=4, padx=10)
        
        # 重新初始化Socket按钮
        self.reinit_btn = tk.Button(connection_frame, text="重新初始化Socket", command=self.init_socket)
        self.reinit_btn.grid(row=0, column=5, padx=10)
        
        # 消息显示区域
        self.text_area = scrolledtext.ScrolledText(self.root, width=60, height=20)
        self.text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # 消息发送区域
        send_frame = tk.Frame(self.root)
        send_frame.pack(padx=10, pady=5, fill=tk.X)
        
        tk.Label(send_frame, text="消息:").pack(side=tk.LEFT)
        self.message_entry = tk.Entry(send_frame, width=40)
        self.message_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        
        self.send_btn = tk.Button(send_frame, text="发送", command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT)
        
        self.log("UDP客户端已启动，可以发送消息")
        self.log("提示: UDP是无连接协议，无需建立连接即可发送消息")
        
    def toggle_broadcast(self):
        """切换广播模式"""
        if self.broadcast_var.get():
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, "255.255.255.255")
            self.ip_entry.config(state='disabled')
            self.is_broadcast = True
            self.log("已切换到广播模式")
        else:
            self.ip_entry.config(state='normal')
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, "192.168.1.255")  # 默认局域网广播地址
            self.is_broadcast = False
            self.log("已切换到单播模式")
        
    def send_message(self):
        if not self.sock:
            messagebox.showwarning("警告", "Socket未初始化，请重新初始化")
            return
            
        message = self.message_entry.get().strip()
        if not message:
            return
            
        try:
            self.esp_ip = self.ip_entry.get()
            self.esp_port = int(self.port_entry.get())
            
            target_ip = self.esp_ip
            
            if self.is_broadcast:
                self.log(f"广播发送到端口 {self.esp_port}: {message}")
            else:
                self.log(f"发送到 {target_ip}:{self.esp_port}: {message}")
                
            self.sock.sendto(message.encode('utf-8'), (target_ip, self.esp_port))
            
            # 在新线程中等待回复
            threading.Thread(target=self.receive_response, daemon=True).start()
            
            self.message_entry.delete(0, tk.END)
            
        except ValueError:
            self.log("错误: 端口号必须是数字")
        except Exception as e:
            self.log(f"发送错误: {e}")
            
    def receive_response(self):
        try:
            if self.is_broadcast:
                # 广播模式下尝试接收多个回复
                self.log("等待广播回复...")
                responses_received = 0
                while True:
                    try:
                        data, addr = self.sock.recvfrom(1024)
                        response = data.decode('utf-8')
                        self.log(f"来自 {addr[0]}:{addr[1]} 的回复: {response}")
                        responses_received += 1
                    except socket.timeout:
                        if responses_received == 0:
                            self.log("广播: 未收到任何回复")
                        else:
                            self.log(f"广播: 共收到 {responses_received} 个回复")
                        break
            else:
                # 单播模式接收单个回复
                data, addr = self.sock.recvfrom(1024)
                response = data.decode('utf-8')
                self.log(f"来自 {addr[0]}:{addr[1]} 的回复: {response}")
                
        except socket.timeout:
            if not self.is_broadcast:  # 单播模式才报超时
                self.log("错误: 接收超时")
        except Exception as e:
            self.log(f"接收错误: {e}")
            
    def log(self, message):
        self.text_area.insert(tk.END, f"{message}\n")
        self.text_area.see(tk.END)
        
    def __del__(self):
        if self.sock:
            self.sock.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = UDPClientGUI(root)
    root.mainloop()