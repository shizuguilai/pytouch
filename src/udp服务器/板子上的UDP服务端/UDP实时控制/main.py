import socket
import network
import time
import tDriver as t
import machine

# 设置Wi-Fi连接信息
SSID = 'HUAWEI-MIX_2.4G'
PASSWORD = '123456789'

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
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('正在连接Wi-Fi...')
        wlan.connect(SSID, PASSWORD)
        
        # 等待连接，最多10秒
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print('.', end='')
    
    if wlan.isconnected():
        print('\nWi-Fi连接成功!')
        print('网络配置:', wlan.ifconfig())
        return wlan.ifconfig()
    else:
        print('\nWi-Fi连接失败!')

        return None

tMode1 = {'1':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'a':10,'b':11,'c':12,'d':13,'e':14,'f':15,'g':16}
tDMode = {'0':[1,1],
          '1':[1,0],
          '2':[2,1],
          '3':[2,0],
          '4':[3,1],
          '5':[3,0],
          '6':[4,1],
          '7':[4,0],
          '8':[5,1],
          '9':[5,0],
          'a':[6,0],
          'b':[6,1],
          'c':[7,0],
          'd':[7,1],
          'e':[8,0],
          'f':[8,1],
          'g':[9,0],
          'h':[9,1],
          'i':[10,0],
          'j':[10,1],
          'k':[11,0],
          'l':[11,1],
          'm':[12,0],
          'n':[12,1],
          'o':[13,0],
          'p':[13,1],
          'q':[14,0],
          'r':[14,1],
          's':[15,0],
          't':[15,1],
          'u':[16,0],
          'v':[16,1],
          'x':[17,0],
          'y':[17,1],}
isSplitTouch = False            #定义按下和抬起是否分开控制,默认是分开控制:@模式,一起控制是:!模式

isMutilTouch = False            #定义是否同时控制多个点击头,默认不是同时控制多个点击头,只有收到<>时才是
mutildat = ''
def touchCmd(cmd):
    if isSplitTouch:
        if tDMode[cmd][1] == 1:
            touchPin(tDMode[cmd][0])
        else:
            unTouchPin(tDMode[cmd][0])
    else:
        if cmd > '0' and cmd < 'h':
            print('touch pin:',tMode1[cmd])
            touchOncePin(tMode1[cmd])

def touchMutil(cmd):
    #串口同时控制多个点击头
    tmpd = int(cmd, 16)
    setAllPinStates(tmpd)
def runTouch(msg):
    global isSplitTouch,isMutilTouch,mutildat
    dat = msg
    for i,v in enumerate(msg):
        dat = v
        if dat: #接收到数据,dat将不为None
            # print('recive uart data:%s'%(dat.decode())) #decode是把字节流数据转成字符串格式
            # dat = dat.decode().strip() #strip()是去掉字符串两边的空格
            print(len(dat),dat)
            if dat == '@':
                isSplitTouch = True
            elif dat == '!':
                isSplitTouch = False
            elif dat == '<':
                isMutilTouch = True
            elif dat == '>':
                isMutilTouch = False
                print(mutildat)
                if len(mutildat) == 4:
                    touchMutil(mutildat)
                mutildat = ''
            elif isMutilTouch and ((dat >= '0' and dat <= '9') or (dat >= 'a' and dat <= 'f') or (dat >= 'A' and dat <= 'F')):
                mutildat += dat
            elif (not isMutilTouch) and ((dat >= '0' and dat <= '9') or (dat >= 'a' and dat <= 'z') or (dat >= 'A' and dat <= 'Z')):
                touchCmd(dat)
            else:
                print('error data:%s'%(dat))

# 创建UDP服务器
def udp_server():
    # 获取IP地址
    network_info = connect_wifi()
    if not network_info:
        print('重启整个系统')
        time.sleep_ms(10)
        machine.reset()  # 重启整个系统
        time.sleep_ms(100)
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