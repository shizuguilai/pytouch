import serial
import keyboard
import time
import sys

class SerialKeyboardController:
    def __init__(self, port1,port2, baudrate=115200):
        self.port1 = port1
        self.port2 = port2
        self.baudrate = baudrate
        self.ser = None
        self.ser2 = None
        
    def connect_serial(self):
        """连接串口"""
        isOK = True
        try:
            self.ser = serial.Serial(self.port1, self.baudrate, timeout=1)
            print(f"已连接到串口 {self.port1}, 波特率 {self.baudrate}")
        except serial.SerialException as e:
            print(f"无法打开串口 {self.port1}: {e}")
            isOK = False
        try:
            self.ser2 = serial.Serial(self.port2, self.baudrate, timeout=1)
            print(f"已连接到串口 {self.port1}, 波特率 {self.baudrate}")
        except serial.SerialException as e:
            print(f"无法打开串口 {self.port1}: {e}")
            isOK = False
        return isOK
    
    def send_character(self, char):
        """通过串口发送字符"""
        ser1s = ['A','B','C','D','a','b','c','d']
        if (char.strip() in ser1s):
            print(char)
            if self.ser and self.ser.is_open:
                try:
                    self.ser.write(char.encode('utf-8'))
                    print(f"1已发送: {char}")
                except Exception as e:
                    print(f"1发送失败: {e}")
        ser2s = ['E','F','G','e','f','g']
        if (char.strip() in ser2s):
            if self.ser and self.ser.is_open:
                try:
                    self.ser2.write(char.encode('utf-8'))
                    print(f"2已发送: {char}")
                except Exception as e:
                    print(f"2发送失败: {e}")
    
    def setup_keyboard_listeners(self):
        """设置键盘监听器"""
        # 定义F1-F12按键对应的发送字符
        function_key_mapping = {
            'q': 'A',
            'w': 'B', 
            'e': 'C',
            'r': 'D',
            'd':'E',
            'f':'F',
            'g':'G'
        }
        function_key_release = {
            'q': 'a',
            'w': 'b', 
            'e': 'c',
            'r': 'd',
            'd':'e',
            'f':'f',
            'g':'g'
        }
        
        # 监听F1-F12功能键
        for key_name, send_char in function_key_mapping.items():
            keyboard.on_press_key(key_name, lambda e, char=send_char: self.send_character(char+'\n'))
        for key_name, send_char in function_key_release.items():
            keyboard.on_release_key(key_name, lambda e, char=send_char: self.send_character(char+'\n'))
        
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
    # Windows: 'COM4', Linux: '/dev/ttyUSB0', macOS: '/dev/tty.usbserial-*'
    serial_port1 = 'COM4'  # 修改为你的串口号
    serial_port2 = 'COM5'  # 修改为你的串口号
    controller = SerialKeyboardController(serial_port1,serial_port2, 115200)
    controller.run()