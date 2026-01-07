import socket
import time
import random

server_ip = '10.0.0.160'
server_port = 8888

def delayMS(t1,t2):
    dt = random.randint(t1,t2)
    dt = dt/1000.0
    time.sleep(dt)

def delayS(t1,t2):
    delayMS(t1*1000,t2*1000)
    
def send_udp_message(message):
    """
    发送UDP消息到指定的服务器
    
    参数:
        server_ip: 服务器IP地址
        server_port: 服务器端口号
        message: 要发送的消息内容
    """
    try:
        # 创建UDP套接字
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # 设置超时时间（可选，单位：秒）
        client_socket.settimeout(5)
        
        # 发送消息
        print(f"发送消息到 {server_ip}:{server_port}")
        print(f"消息内容: {message}")
        
        client_socket.sendto(message.encode(), (server_ip, server_port))
        
        # 尝试接收响应（可选）
        try:
            response, server_address = client_socket.recvfrom(1024)
            print(f"收到来自 {server_address} 的响应: {response.decode()}")
        except socket.timeout:
            print("未收到响应（超时）")
        
        # 关闭套接字
        client_socket.close()
        
    except Exception as e:
        print(f"发送失败: {e}")

def simple_example():
    """
    最简单的使用示例
    """
    # 配置
    SERVER_IP = "127.0.0.1"  # 服务器IP地址
    SERVER_PORT = 12345      # 服务器端口号
    
    # 您要发送的内容
    
    # 发送消息
    send_udp_message('1')
    delayS(5,10) 
    send_udp_message('2')
    time.sleep(1)

if __name__ == "__main__":
    print("UDP客户端示例")
    print("1. 交互式模式")
    print("2. 批量发送示例")
    print("3. 简单示例")
    
    simple_example()
