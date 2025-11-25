import subprocess
import os
import time
import serial
import socket


OPENSH = "./open.sh"   #修改这里的检测程序路径
CMDCOUNT = 5           #要检测的命令行数量

PIPE = "/tmp/terminal_capture.pipe"
HOOK = "./hook.so"

SerialPort = '/dev/ttyUSB0'

isSerial = True

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
        broadcast_address = ('255.255.255.255', port)  # 端口可以自定义
        
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

count = 0

def reader():
    global count
    with open(PIPE, "r") as f:
        while True:
            line = f.readline()
            if line:
                print("实时输出:", line.strip())
                count += 1
                if count >= CMDCOUNT:
                    print("检测到第五行命令消息，启动程序")
                    sendMsg(msg = '<FFFF>') #向局域网内广播消息,让所有点击头抬起
                    time.sleep(1)
                    os._exit(0)

def main():
    # 建 pipe
    sendMsg(msg = '<0000>') #启动程序让所有点击头按下
    try:
        os.mkfifo(PIPE)
    except FileExistsError:
        pass

    env = os.environ.copy()
    env["LD_PRELOAD"] = HOOK

    # 启动 open.sh
    subprocess.Popen(OPENSH, env=env, shell=True)

    # 实时读取
    reader()

if __name__ == "__main__":
    main()
