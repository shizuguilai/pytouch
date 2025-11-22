import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading

class UDPClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("UDP客户端 - ESP8266连接工具")
        
        self.sock = None
        self.esp_ip = "192.168.1.6"  # 默认IP
        self.esp_port = 8888
        
        self.setup_ui()
        
    def setup_ui(self):
        # 连接设置框架
        connection_frame = tk.Frame(self.root)
        connection_frame.pack(padx=10, pady=5, fill=tk.X)
        
        tk.Label(connection_frame, text="ESP8266 IP:").grid(row=0, column=0, sticky=tk.W)
        self.ip_entry = tk.Entry(connection_frame, width=15)
        self.ip_entry.insert(0, self.esp_ip)
        self.ip_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(connection_frame, text="端口:").grid(row=0, column=2, padx=(20,0))
        self.port_entry = tk.Entry(connection_frame, width=8)
        self.port_entry.insert(0, str(self.esp_port))
        self.port_entry.grid(row=0, column=3, padx=5)
        
        self.connect_btn = tk.Button(connection_frame, text="连接", command=self.connect_server)
        self.connect_btn.grid(row=0, column=4, padx=10)
        
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
        
        self.log("客户端已启动，请连接ESP8266服务器")
        
    def connect_server(self):
        try:
            self.esp_ip = self.ip_entry.get()
            self.esp_port = int(self.port_entry.get())
            
            if self.sock:
                self.sock.close()
                
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(5.0)
            
            # 测试连接
            test_msg = "connect_test"
            self.sock.sendto(test_msg.encode(), (self.esp_ip, self.esp_port))
            
            self.log(f"已连接到 {self.esp_ip}:{self.esp_port}")
            self.connect_btn.config(text="重新连接")
            
        except Exception as e:
            messagebox.showerror("连接错误", f"无法连接到服务器: {e}")
            
    def send_message(self):
        if not self.sock:
            messagebox.showwarning("警告", "请先连接服务器")
            return
            
        message = self.message_entry.get().strip()
        if not message:
            return
            
        try:
            self.log(f"发送: {message}")
            self.sock.sendto(message.encode('utf-8'), (self.esp_ip, self.esp_port))
            
            # 在新线程中等待回复
            threading.Thread(target=self.receive_response, args=(message,), daemon=True).start()
            
            self.message_entry.delete(0, tk.END)
            
        except Exception as e:
            self.log(f"发送错误: {e}")
            
    def receive_response(self, sent_message):
        try:
            data, addr = self.sock.recvfrom(1024)
            response = data.decode('utf-8')
            self.log(f"收到回复: {response}")
        except socket.timeout:
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