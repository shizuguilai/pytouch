import serial
import keyboard
import time
import sys

class SerialKeyboardController:
    def __init__(self, port, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        
    def connect_serial(self):
        """连接串口"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"已连接到串口 {self.port}, 波特率 {self.baudrate}")
            return True
        except serial.SerialException as e:
            print(f"无法打开串口 {self.port}: {e}")
            return False
    
    def send_character(self, char):
        """通过串口发送字符"""
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(char.encode('utf-8'))
                print(f"已发送: {char}")
            except Exception as e:
                print(f"发送失败: {e}")
    
    def setup_keyboard_listeners(self):
        """设置键盘监听器"""
        # 定义F1-F12按键对应的发送字符
        function_key_mapping = {
            'f1': 'A',
            'f2': 'B', 
            'f3': 'C',
            'f4': 'D',
            'f5': 'E',
            'f6': 'F',
            'f7': 'G',
            'f8': 'H',
            'f9': 'I',
            'f10': 'J',
            'f11': 'K',
            'f12': 'L'
        }
        
        # 监听F1-F12功能键
        for key_name, send_char in function_key_mapping.items():
            keyboard.on_press_key(key_name, lambda e, char=send_char: self.send_character(char+'\n'))
        
        # 监听ESC键用于退出程序
        keyboard.on_press_key('esc', lambda e: self.stop())
        
        print("键盘监听器已启动")
        print("F1-F12功能键对应发送字符:")
        for i, (key, char) in enumerate(function_key_mapping.items(), 1):
            print(f"  {key.upper()} -> '{char}'")
        print("按ESC键退出程序")
    
    def stop(self):
        """停止程序"""
        if self.ser and self.ser.is_open:
            self.ser.close()
        print("程序已退出")
        sys.exit(0)
    
    def run(self):
        """运行主程序"""
        if not self.connect_serial():
            return
        
        self.setup_keyboard_listeners()
        
        try:
            # 保持程序运行
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()

if __name__ == "__main__":
    # 请根据实际情况修改串口号
    # Windows: 'COM3', Linux: '/dev/ttyUSB0', macOS: '/dev/tty.usbserial-*'
    serial_port = 'COM3'  # 修改为你的串口号
    
    controller = SerialKeyboardController(serial_port, 115200)
    controller.run()