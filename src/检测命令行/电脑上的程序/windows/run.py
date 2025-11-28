import subprocess
import sys
import os
import time
import serial
import socket


target_count = 5           #要检测的命令行数量

SerialPort = '/dev/ttyUSB0'

isSerial = False

def broadcast_Msg(msg, port=8888):
    """
    在局域网内广播发送'find'消息
    """
    try:
        # 创建UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # 设置socket选项，允许广播
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # 广播地址和端口
        broadcast_address = ('192.168.31.206', port)  # 端口可以自定义
        
        # 要发送的消息
        message = msg
        
        # 发送广播消息
        sock.sendto(message.encode('utf-8'), broadcast_address)
        print(f"已发送广播消息: {message}")
        
        # 关闭socket
        sock.close()
        
    except Exception as e:
        print(f"发送广播时出错: {e}")


def sendMsg(msg):
    if isSerial:
        ser = serial.Serial(SerialPort, 115200)
        ser.write(msg.encode())
        ser.close()
    else:
        broadcast_Msg(msg)



def simple_gost_monitor():
    """简化的gost监控版本"""
    request_count = 0
    
    def callback():
        print(f"\n🎉 收到 {target_count} 个请求，执行回调！")
        # 在这里添加您的处理逻辑
        print("执行自定义操作...")
        sendMsg('1')
    
    try:
        # 启动gost
        process = subprocess.Popen(
            ['gost', '-L', 'http://:1235'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        print("监控gost请求中... (目标: 5个请求)")
        
        # 读取输出
        for line in process.stdout:
            print(line.strip())
            
            # 简单的请求检测
            if any(keyword in line.lower() for keyword in ['http', 'request', 'connect']):
                request_count += 1
                print(f"请求计数: {request_count}")
                
                if request_count >= target_count:
                    callback()
                    break
                    
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except FileNotFoundError:
        print("错误: 找不到 gost 命令")
    finally:
        if process:
            process.terminate()

if __name__ == "__main__":    
    sendMsg('0')
    simple_gost_monitor()