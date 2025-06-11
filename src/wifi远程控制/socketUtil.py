import usocket as socket
import uselect as select
import network
import time

def connect_wifi(ssid,pwd):
    """连接Wi-Fi网络"""
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("Connecting to Wi-Fi...")
        sta_if.active(True)
        sta_if.connect(ssid, pwd)
        while not sta_if.isconnected():
            time.sleep(1)
            print('.')
    print("Wi-Fi connected:", sta_if.ifconfig())


def startServer(datacallFunc,host = '0.0.0.0',port = 23,maxclients = 5):
 
    # 创建TCP套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_addr = (host, port)
    server_socket.bind(server_addr)
    server_socket.listen(maxclients)
    server_socket.setblocking(False)  # 非阻塞模式
    
    # 创建poll对象
    poller = select.poll()
    # 注册服务器套接字，关注读事件
    poller.register(server_socket, select.POLLIN)
    
    # 客户端列表 [socket对象]
    clients = []
    
    print(f"Server started on {server_addr}")
    
    try:
        while True:
            # 等待事件，超时时间500毫秒
            events = poller.poll(500)
            
            for sock, event in events:
                # 新客户端连接
                if sock == server_socket:
                    try:
                        client_socket, addr = server_socket.accept()
                        print(f"New connection from: {addr}")
                        client_socket.setblocking(False)
                        poller.register(client_socket, select.POLLIN)
                        clients.append(client_socket)
                    except Exception as e:
                        print(f"Accept error: {e}")
                
                # 客户端数据可读
                elif event & select.POLLIN:
                    try:
                        data = sock.recv(256)  # 每次接收最多256字节
                        if data:
                            # 处理数据（这里简单打印并回显）
                            print(f"Received {len(data)} bytes: {data[:20]}...")
                            datacallFunc(data)
                            try:
                                sock.sendall(b"Echo: " + data)
                            except:
                                print("Send error, closing connection")
                                sock.close()
                                clients.remove(sock)
                                poller.unregister(sock)
                        else:
                            # 空数据表示客户端断开
                            print("Client disconnected")
                            sock.close()
                            clients.remove(sock)
                            poller.unregister(sock)
                    except Exception as e:
                        print(f"Receive error: {e}")
                        try:
                            sock.close()
                            clients.remove(sock)
                            poller.unregister(sock)
                        except:
                            pass
                        
            # 这里可以添加其他后台任务
            # time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("Server shutdown")
    finally:
        # 清理所有资源
        for client in clients:
            try:
                client.close()
            except:
                pass
        server_socket.close()
        print("All connections closed")

# 启动服务器
# if __name__ == "__main__":
#     main()