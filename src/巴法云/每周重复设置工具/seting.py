import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import json
from datetime import datetime
import os

class BemfaTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("巴法云定时消息设置工具")
        self.root.geometry("800x600")
        
        # 存储定时任务
        self.tasks = []
        
        # 创建界面
        self.create_widgets()
        self.load_config()

    def load_config(self):
        """程序启动时，从配置文件加载用户信息"""
        config_file = "bemfa_config.json"
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 将加载出的配置填充到输入框中
                self.openid_entry.insert(0, config.get('openID', ''))
                self.topicid_entry.insert(0, config.get('topicID', ''))
                self.log("已加载上次保存的用户配置。")
            else:
                self.topicid_entry.insert(0, 'fengmm521')
        except Exception as e:
            self.log(f"加载配置文件时出错: {e}")
    
    def save_config(self):
        """将当前的用户信息保存到配置文件"""
        config_file = "bemfa_config.json"
        try:
            config = {
                'openID': self.openid_entry.get().strip(),
                'topicID': self.topicid_entry.get().strip()
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            self.log("用户配置已保存。")
        except Exception as e:
            self.log(f"保存配置文件时出错: {e}")
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 用户信息区域
        user_frame = ttk.LabelFrame(main_frame, text="用户信息", padding="5")
        user_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        user_frame.columnconfigure(1, weight=1)
        
        ttk.Label(user_frame, text="巴法云私钥:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.openid_entry = ttk.Entry(user_frame, width=40)
        self.openid_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(user_frame, text="主题:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.topicid_entry = ttk.Entry(user_frame, width=40)
        self.topicid_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 定时设置区域
        timer_frame = ttk.LabelFrame(main_frame, text="定时设置", padding="5")
        timer_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        timer_frame.columnconfigure(1, weight=1)
        
        # 时间设置
        time_frame = ttk.Frame(timer_frame)
        time_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(time_frame, text="发送时间:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.hour_var = tk.StringVar(value="00")
        self.minute_var = tk.StringVar(value="00")
        self.second_var = tk.StringVar(value="00")
        
        hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, width=3, textvariable=self.hour_var, format="%02.0f")
        hour_spinbox.grid(row=0, column=1, padx=(0, 2))
        ttk.Label(time_frame, text="时").grid(row=0, column=2, padx=(0, 5))
        
        minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, width=3, textvariable=self.minute_var, format="%02.0f")
        minute_spinbox.grid(row=0, column=3, padx=(0, 2))
        ttk.Label(time_frame, text="分").grid(row=0, column=4, padx=(0, 5))
        
        second_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, width=3, textvariable=self.second_var, format="%02.0f")
        second_spinbox.grid(row=0, column=5, padx=(0, 2))
        ttk.Label(time_frame, text="秒").grid(row=0, column=6, padx=(0, 10))
        
        # 消息内容
        ttk.Label(timer_frame, text="消息内容:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.message_entry = ttk.Entry(timer_frame, width=30)
        self.message_entry.insert(0, "e")  # 默认消息为"e"
        self.message_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(5, 0), padx=(5, 10))
        
        # 设备类型固定为TCP
        ttk.Label(timer_frame, text="设备类型:").grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        ttk.Label(timer_frame, text="TCP设备 (固定)").grid(row=1, column=3, sticky=tk.W, pady=(5, 0))
        
        # 星期选择区域
        week_frame = ttk.LabelFrame(timer_frame, text="重复星期", padding="5")
        week_frame.grid(row=2, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.week_vars = []
        week_days = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
        for i, day in enumerate(week_days):
            var = tk.BooleanVar(value=True)  # 默认全选
            self.week_vars.append(var)
            cb = ttk.Checkbutton(week_frame, text=day, variable=var)
            cb.grid(row=0, column=i, padx=10)
        
        # 按钮区域
        button_frame = ttk.Frame(timer_frame)
        button_frame.grid(row=3, column=0, columnspan=5, pady=(10, 0))
        
        self.add_button = ttk.Button(button_frame, text="设置定时任务", command=self.set_timer_task)
        self.add_button.grid(row=0, column=0, padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, text="清空任务列表", command=self.clear_all_tasks)
        self.clear_button.grid(row=0, column=1, padx=(0, 10))
        
        # 任务列表区域
        list_frame = ttk.LabelFrame(main_frame, text="已设置的定时任务", padding="5")
        list_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 创建树形视图显示任务
        columns = ("设置时间", "发送时间", "消息", "重复星期", "API状态")
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        # 设置列标题
        for col in columns:
            self.task_tree.heading(col, text=col)
            if col == "重复星期":
                self.task_tree.column(col, width=150)
            else:
                self.task_tree.column(col, width=120)
        
        self.task_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        # 删除选中任务按钮
        self.delete_button = ttk.Button(list_frame, text="删除选中任务", command=self.delete_selected_task)
        self.delete_button.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="API调用日志", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=10)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置主框架的行权重
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(3, weight=1)
    
    def set_timer_task(self):
        """设置定时任务到巴法云平台"""
        # 获取用户输入
        openid = self.openid_entry.get().strip()
        topicid = self.topicid_entry.get().strip()
        message = self.message_entry.get().strip()
        
        if not openid or not topicid:
            messagebox.showerror("错误", "请填写OpenID和TopicID")
            return
        
        if not message:
            messagebox.showerror("错误", "请填写消息内容")
            return
        
        # 构建时间字符串
        time_str = f"{self.hour_var.get():>02}:{self.minute_var.get():>02}:{self.second_var.get():>02}"
        
        # 获取选中的星期
        selected_weeks = []
        for i, var in enumerate(self.week_vars):
            if var.get():
                # 接口要求：0表示周日，1-6表示周一到周六
                selected_weeks.append(i)
        
        if not selected_weeks:
            messagebox.showerror("错误", "请至少选择一个星期")
            return
        
        # 创建任务数据
        task_data = {
            "openID": openid,
            "topicID": topicid,
            "time": time_str,
            "type": 3,  # 固定为TCP设备
            "msg": message,
            "week": selected_weeks
        }
        
        # 调用API设置定时任务
        success = self.send_to_bemfa_api(task_data)
        
        # 添加到任务列表
        if success:
            task_data["added_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            task_data["api_status"] = "成功"
            self.tasks.append(task_data)
            self.update_task_tree()
        else:
            task_data["added_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            task_data["api_status"] = "失败"
            self.tasks.append(task_data)
            self.update_task_tree()
        if success:
            self.save_config()  # <-- 添加这一行
    
    def send_to_bemfa_api(self, task_data):
        """发送定时任务到巴法云API"""
        try:
            self.log(f"正在设置定时任务: 时间 {task_data['time']}, 消息 '{task_data['msg']}'")
            
            # 发送POST请求
            response = requests.post(
                "https://apis.bemfa.com/vb/delay/v1/addTime",
                json=task_data,
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=10
            )
            
            result = response.json()
            
            if result.get("code") == 0:
                self.log(f"✓ 定时任务设置成功: 时间 {task_data['time']}, 消息 '{task_data['msg']}'")
                return True
            else:
                error_msg = result.get('msg', '未知错误')
                self.log(f"✗ 定时任务设置失败: {error_msg}")
                messagebox.showerror("API错误", f"设置定时任务失败: {error_msg}")
                return False
                
        except Exception as e:
            error_msg = str(e)
            self.log(f"✗ API请求出错: {error_msg}")
            messagebox.showerror("请求错误", f"API请求出错: {error_msg}")
            return False
    
    def delete_selected_task(self):
        """删除选中的任务（仅从本地列表删除）"""
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个任务")
            return
        
        # 获取选中项的索引
        for item in selection:
            index = self.task_tree.index(item)
            if 0 <= index < len(self.tasks):
                removed_task = self.tasks.pop(index)
                self.log(f"从本地列表删除任务: 时间 {removed_task['time']}, 消息 '{removed_task['msg']}'")
        
        self.update_task_tree()
    
    def clear_all_tasks(self):
        """清空所有任务（仅从本地列表删除）"""
        if not self.tasks:
            messagebox.showinfo("提示", "没有任务可清空")
            return
        
        if messagebox.askyesno("确认", "确定要清空所有定时任务吗？(注意：这只是从本地列表删除，不会取消已设置的定时任务)"):
            task_count = len(self.tasks)
            self.tasks.clear()
            self.update_task_tree()
            self.log(f"已从本地列表清空所有 {task_count} 个定时任务")
    
    def update_task_tree(self):
        """更新任务树形视图"""
        # 清空现有项目
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # 添加所有任务
        for task in self.tasks:
            # 格式化星期显示
            week_display = ", ".join([["日", "一", "二", "三", "四", "五", "六"][i] for i in task["week"]])
            
            self.task_tree.insert("", tk.END, values=(
                task["added_time"],
                task["time"],
                task["msg"],
                week_display,
                task.get("api_status", "未知")
            ))
    
    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)

def main():
    root = tk.Tk()
    app = BemfaTimerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()