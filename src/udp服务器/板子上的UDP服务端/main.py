import socket
import network
import time
import tDriver as t
import socketUtil
# 设置Wi-Fi连接信息
SSID = "CMCC-h3gp"
PASSWORD = "pat5k9he"
# VVG1,a12345678
#实始化一个点击器控制实例对象
tobj = t.TouchObj()
#生成随机整数
def randint(min, max):
    return t.randint(min, max)
#pNumber按键按下,pNumber从1~16
def touchPin(pNumber):
    tobj.setPin(pNumber,False)
    tobj.updateData()
#pNumber按键抬起,pNumber从1~16
def unTouchPin(pNumber):
    tobj.setPin(pNumber,True)
    tobj.updateData()

#按下并抬起,即点按一次,pNumber从1~16
def touchOncePin(pNumber,misll=1):
    #判断输入的点击头编号是否在1~16范围内,不在时程序直接返回,并报错
    if pNumber < 1 or pNumber > 16: 
        print('pin number erro:%d'%(pNumber)) 
        return
    touchPin(pNumber)   #对应点击头按下
    time.sleep_ms(misll)   #按下时间为80毫秒,这个时间可以根据需要修改,建议30~100之间
    unTouchPin(pNumber) #对应点击头抬起
    time.sleep_ms(misll)   #抬起后再等80毫秒

#使用四个点击头组成一列进行向上滑动操作, 从下向上依次是J1,J2,J3,J4的方式排列
def moveUP():
    tobj.move([1,2,3,4])  #按J1,J2,J3,J4顺序滑动
#向下滑动操作,正好和向上相反
def moveDown():
    tobj.move([4,3,2,1]) #按J4,J3,J2,J1顺序滑动

#使用16位的按键状态数一次控制所有点击头状态
def setAllPinStates(state):
    tobj.set16Pins(state)
    tobj.updateData()

# 连接Wi-Fi
def connect_wifi():
    socketUtil.connect_wifi(SSID,PASSWORD)
    # wlan = network.WLAN(network.STA_IF)
    # wlan.active(True)
    
    # if not wlan.isconnected():
    #     print('正在连接Wi-Fi...')
    #     wlan.connect(SSID, PASSWORD)
        
    #     # 等待连接，最多10秒
    #     timeout = 10
    #     while not wlan.isconnected() and timeout > 0:
    #         time.sleep(1)
    #         timeout -= 1
    #         print('.', end='')
    
    # if wlan.isconnected():
    #     print('\nWi-Fi连接成功!')
    #     print('网络配置:', wlan.ifconfig())
    #     return wlan.ifconfig()
    # else:
    #     print('\nWi-Fi连接失败!')
    #     return None

def runTouch(msg):
    try:
        print(msg)
        tmps = msg.split('-')
        for i in range(int(tmps[1])):
            touchOncePin(int(tmps[0]),int(tmps[2]))          #j1点击一次

    except Exception as e:
        print('msg erro')

# 创建UDP服务器
def udp_server():
    # 获取IP地址
    network_info = connect_wifi()
    if not network_info:
        return
    
    local_ip = network_info[0]
    port = 8888  # UDP端口号
    
    # 创建UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((local_ip, port))
    
    print(f'UDP服务器启动在 {local_ip}:{port}')
    print('等待接收数据...')
    
    try:
        while True:
            # 接收数据（最大缓冲区大小：1024字节）
            data, addr = sock.recvfrom(1024)
            
            # 解码接收到的数据
            received_message = data.decode('utf-8')
            runTouch(received_message)
            print(f'收到来自 {addr} 的消息: {received_message}')
            
            # 发送回复
            response = f'已收到你的消息: {received_message}'
            sock.sendto(response.encode('utf-8'), addr)
            print(f'已发送回复给 {addr}')
            
    except KeyboardInterrupt:
        print('\n服务器关闭')
    except Exception as e:
        print(f'发生错误: {e}')
    finally:
        sock.close()

# 运行UDP服务器
if __name__ == '__main__':
    udp_server()