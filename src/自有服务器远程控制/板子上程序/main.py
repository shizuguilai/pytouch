# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import os,sys
import socket
import select
import tDriver as t
import time
import json
from machine import Timer
from machine import UART
from machine import Pin
import network


cs = None
socketTimer = Timer(-17)
#实始化一个点击器控制实例对象
tobj = t.TouchObj()

#使用16位的按键状态数一次控制所有点击头状态
def setAllPinStates(state):
    tobj.set16Pins(state)
    tobj.updateData()

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
def touchOncePin(pNumber):
    #判断输入的点击头编号是否在1~16范围内,不在时程序直接返回,并报错
    if pNumber < 1 or pNumber > 16: 
        print('pin number erro:%d'%(pNumber)) 
        return
    touchPin(pNumber)   #对应点击头按下
    time.sleep_ms(80)   #按下时间为80毫秒,这个时间可以根据需要修改,建议30~100之间
    unTouchPin(pNumber) #对应点击头抬起
    time.sleep_ms(80)   #抬起后再等80毫秒

#使用四个点击头组成一列进行向上滑动操作, 从下向上依次是J1,J2,J3,J4的方式排列
def moveUP():
    tobj.move([1,2,3,4],5)  #按J1,J2,J3,J4顺序滑动,第二个参数5是滑动时间,单位是毫秒
#向下滑动操作,正好和向上相反
def moveDown():
    tobj.move([4,3,2,1],5) #按J4,J3,J2,J1顺序滑动,第二个参数5是滑动时间,单位是毫秒

#使用16位的按键状态数一次控制所有点击头状态
def setAllPinStates(state):
    tobj.set16Pins(state)
    tobj.updateData()

m_tST = 0xffff
#字符串转为hex十六进制数
# hex_string = "0xFF"

# an_integer = int(hex_string, 16)

# hex_value = hex(an_integer)
# print(hex_value)

#使用两个字节码控制多个点击头按下
def touchCMD(cmd):
    global m_tST
    an_integer = int(cmd, 16)
    m_tST = m_tST & an_integer
    setAllPinStates(m_tST)
    # hex_value = hex(an_integer)
    # print(hex_value)

#使用字节码控制多个点击头抬起
def unTouchCMD(cmd):
    global m_tST
    an_integer = int(cmd, 16)
    notInt = ~(an_integer)
    m_tST = m_tST | notInt
    setAllPinStates(m_tST)

def getMacAddr():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    s = sta_if.config('mac')
    mymac = ('%02x%02x%02x%02x%02x%02x') %(s[0],s[1],s[2],s[3],s[4],s[5])
    return mymac

#根据指令按下一个按钮
def touchWithCmd(cmd):
    pass



def isHeaveFile(fpth):
    try:
        f = open(fpth,'r')
        f.close()
        return True
    except Exception as e:
        return False
    

# time.sleep(1)           # sleep for 1 second
# time.sleep_ms(500)      # sleep for 500 milliseconds
# time.sleep_us(10)       # sleep for 10 microseconds
# start = time.ticks_ms() # get millisecond counter
# delta = time.ticks_diff(time.ticks_ms(), start) # compute time difference

espid = None
espidPTH = 'espid.txt'

def saveESPID(tid):
    global espid
    espid = tid
    f = open(espidPTH,'w')
    f.write(tid)
    f.close()

def readESPID():
    global espid
    if not isHeaveFile(espidPTH):
        return
    f = open(espidPTH,'r')
    espid = f.read()
    f.close()

#清除设置编号,不连socket
def cleanESPID():
    global espid
    espid = None
    os.remove(espidPTH)

ssid = None
pwd = None

wifiPTH = 'wifi.txt'

def saveWIFI(pid,ppwd):
    global ssid,pwd
    ssid = pid
    pwd = ppwd
    jstr = ssid + ',' + pwd
    f = open(wifiPTH,'w')
    f.write(jstr)
    f.close()


def readWIFI():
    global ssid,pwd
    if not isHeaveFile(wifiPTH):
        return
    f = open(wifiPTH,'r')
    tmp = f.read()
    f.close()
    tmps = tmp.split(',')
    ssid = tmps[0]
    pwd = tmps[1]

def cleanWIFI():
    global ssid,pwd
    ssid = None
    pwd = None
    os.remove(wifiPTH)

ifconfig = None

def do_connect():
    global ifconfig
    sta_if = network.WLAN(network.STA_IF)  # 配置wifi模式为station
    if not sta_if.isconnected():   # 判断有无连接
        print('connecting wifi rout...')
        sta_if.active(True)        # 激活wifi接口
        sta_if.connect(ssid,pwd)  # 连接现有wifi网络，需要替换为已知的热点名称和密码
        while not sta_if.isconnected():
            time.sleep_ms(1)   # 未连接上就等待一下，直到连接成功
    print('network config:', sta_if.ifconfig())  # 输出当前wifi网络给自己分配的网络参数
    # ('192.168.1.100', '255.255.255.0', '192.168.1.1', '8.8.8.8')
    ifconfig = sta_if.ifconfig()

SERIAL_UART = None  #UART串口

sAddr = None    
sPort = None

serverPTH = 'server.txt'

def saveServer(ser,port):
    global sAddr,sPort
    sAddr = ser
    sPort = port
    jstr = ser + ',' + port
    f = open(serverPTH,'w')
    f.write(jstr)
    f.close()

def readServer():
    global sAddr,sPort
    if not isHeaveFile(serverPTH):
        return
    f = open(serverPTH,'r')
    tmp = f.read()
    f.close()
    tmps = tmp.split(',')
    sAddr = tmps[0]
    sPort = tmps[1]

def cleanServer():
    global sAddr,sPort
    sAddr = None
    sPort = None
    os.remove(serverPTH)

def readConfig():
    readESPID()
    readWIFI()
    readServer()

#当是串口是<>符号时,就是一次设置所有参数
#<espid,ssid,pwd,sAddr,sPort>
def saveAllConfig(dstr):
    tmps = dstr.split(',')
    saveESPID(tmps[0])
    saveWIFI(tmps[1],tmps[2])
    saveServer(tmps[3],tmps[4])

def checkConfig():
    notsets = []
    if espid:
        print('device ID:%s\n'%(espid))
    else:
        notsets.append(2)
    if sAddr:
        print('server,addr:%s,port:%s\n'%(sAddr,sPort))
    else:
        notsets.append(3)
    if ssid:
        print('wifi:ssid:%s,pwd:%s\n'%(ssid,pwd))
    else:
        notsets.append(1)
    for i,v in enumerate(notsets):
        if v == 1:
            print('please set wifi with:{ssid,password}\n')
        if v == 2:
            print('please set deviceID with:[id]\n')
        if v == 3:
            print('please set server with:(serverAddr,port)\n')
def UARTRecive():
    outstr = ''
    checkConfig()
    while True:
        time.sleep_ms(3)
        c = sys.stdin.read(1) 
        if c == '{':
            outstr = ''
            continue
        elif c == '}': #保存wifi
            tmps = outstr.split(',')
            saveWIFI(tmps[0],tmps[1])
            print(outstr)
            return
        elif c == '[':
            outstr = ''
            continue
        elif c == ']': #保存设备ID
            saveESPID(outstr)
            print(outstr)
            return
        elif c == '(':
            outstr = ''
            continue
        elif c == ')':  #保存服务器地址和端口
            tmps = outstr.split(',')
            saveServer(tmps[0],tmps[1])
            print(outstr)
            return
        elif c == '<':
            outstr = ''
            continue
        elif c == '>': #保存所有参数,<espid,ssid,pwd,sAddr,sPort>
            saveAllConfig(outstr)
            print(outstr)
            return
        elif not c:
            continue
        else:
            outstr += c

#坐串口读取配置信息
def uartConfig():
    while not (espid and ssid and pwd and sAddr and sPort):
        UARTRecive()

def resetESP():
    import machine
    sta = network.WLAN(network.STA_IF)  # Or network.AP_IF
    sta.active(True)
    sta.disconnect()   # For ESP8266
    socketTimer.deinit()
    machine.reset()

def openLED():
    led = Pin(2,Pin.OUT)
    led.off()

def closeLED():
    led = Pin(2,Pin.OUT)
    led.on()


#定义16个手机点击头的16个定时器,将会分步进行启动运行
timerDict = {}
usedT = []          #已经使用的Timer
unUsedTs = []       #未使用的Timer

def initAllTimer():
    global timerDict
    for i in range(16):
        tp = i+1
        ttmp = Timer(-(tp))
        timerDict[tp] = ttmp
        unUsedTs.append(tp)
def getTimer():
    global timerDict
    if unUsedTs:
        tmp = unUsedTs.pop(0)
        usedT.append(tmp)
        return tmp
    else:
        return None

cmdDict = {}

#点击任务完成,释放定时器使用权
def releaseTimer(tim):
    cmd = cmdDict[str(tim)]
    tid = cmd['tid']
    global timerDict
    index = 0
    for i,v in enumerate(usedT):
        if v  == tid:
            index = i
            break
    usedT.pop(index)
    unUsedTs.append(tid)

def tU(tim):
    global cs
    cmd = cmdDict[str(tim)]
    cmdDict[str(tim)]['c'] -= 1
    unTouchCMD(cmd['p'])
    if cmd['c'] <= 0:
        tim.deinit()
        releaseTimer(tim)
        cs.write('3:{"p":"%s","st":1,"id":"%s"}'%(cmd['p'],espid))
    else:
        if cmd['t2'] >= 30:
            tim.init(period=cmd['t2'],mode=Timer.ONE_SHOT ,callback=tD)
        else:
            tim.init(period=cmd['t1'],mode=Timer.ONE_SHOT ,callback=tD)
def tD(tim):
    cmd = cmdDict[str(tim)]
    touchCMD(cmd['p'])
    tim.init(period=cmd['t1'],mode=Timer.ONE_SHOT ,callback=tU)
def runTouchCmd(cmd):
    global cmdDict
    #{"p":1,"t1":50,"t2":50,"c":1}
    tid = getTimer()
    if not tid:
        return False
    t = timerDict[tid]
    cmd['tid'] = tid
    cmdDict[str(t)] = cmd
    touchCMD(cmd['p'])
    t.init(period=cmd['t1'],mode=Timer.ONE_SHOT ,callback=tU)
    return True

inputs = []
sendDats = []

def sendToServer(data):
    global sendDats
    sendDats.append(data)

def heartSocket(tim):
    global cs
    try:
        if inputs:
            # cs.write('1:w1#%s'%(espid))
            print('send heart')
            sendToServer('1:w1#%s'%(espid))
            tim.init(period=10000,mode=Timer.ONE_SHOT ,callback=heartSocket)
        else:
            tim.deinit()
    except Exception as e:
        print('server disconnected!')
        tim.deinit()

def connectServer():
    global cs,socketTimer,inputs
    print('connect server:(%s,%s)'%(sAddr,sPort))
    addr_info = socket.getaddrinfo(sAddr,int(sPort))
    addr = addr_info[0][-1]
    cs = socket.socket()
    cs.settimeout(10.0)
    while True:
        try:
            cs.connect(addr)
            closeLED()
            break
        except Exception as e:
            print('connect server erro,delay 1s retry...')
            time.sleep(3)
            cs.close()
            cs = None
            openLED()
            return
    print('send heart')
    sendToServer('1:w1#%s'%(espid))
    socketTimer.init(period=10000,mode=Timer.ONE_SHOT ,callback=heartSocket)

redata = None

def callback(pdata):
    global redata,sendDats
    try:
        if not redata:
            redata = pdata
        else:
            redata += pdata
        datstr = str(redata, 'utf8')
        print(datstr,len(datstr))
        if datstr[0] != '{':
            redata = None
            return
        datdic = json.loads(datstr)
        #{"p":1,"t1":50,"t2":50,"c":1}
        print(datdic)
        back = runTouchCmd(datdic)
        if back:
            sendToServer('2:{"p":"%s","st":0,"id":"%s"}'%(datdic['p'],espid))
            # sendDats.append('2:{"p":"%s","st":0,"id":"%s"}'%(datdic['p'],espid))
            # cs.write('2:{"p":"%s","st":0,"id":"%s"}'%(datdic['p'],espid))
        else:
            sendToServer('2:{"p":"%s","st":-1,"id":"%s"}'%(datdic['p'],espid))
            # sendDats.append('2:{"p":"%s","st":-1,"id":"%s"}'%(datdic['p'],espid))
        redata = None
    except Exception as e:
        print('callback data erro')
        return

def selectSocket():
    global inputs,cs
    if cs:
        inputs.append(cs)
    else:
        inputs = []
        return
    # 创建一个列表来存储我们要监视的套接字
    # 定义回调函数
    while True:
        # 使用 select 监视套接字，等待数据可读或可写
        readable, writable, exceptional = select.select(inputs, inputs, inputs)
        # 处理可读的套接字
        for s in readable:
            if s is cs:
                # 从服务器接收数据
                data = s.recv(1024)
                if data:
                    # 调用回调函数处理收到的数据
                    callback(data)
                else:
                    # 服务器关闭连接
                    print('server closed!')
                    openLED()
                    cs.close()
                    inputs.remove(cs)
                    cs = None
                    break

        # 处理可写的套接字
        for s in writable:
            if s is cs:
                # 向服务器发送数据
                while sendDats:
                    msg = sendDats.pop(0)
                    s.write(msg)
                    time.sleep_ms(10)
        # 处理异常的套接字
        for s in exceptional:
            print('socket erro')
            openLED()
            cs.close()
            inputs.remove(cs)
            cs = None
            break
        if not inputs:
            time.sleep(3)
            break

#主函数,点击器程序从这里开始运行
def main():
    setAllPinStates(0b1111111111111111)
    time.sleep_ms(10)
    print('think you for used this deivce,get more deivce please to our shop:\nhttps://fengmm521.taobao.com/\n')
    time.sleep_ms(10)
    print('when power on,the key down the deivce will clean wifi config.when set config,must set wifi at last\nwhen all config set,device can connect server!\n')
    openLED()
    readConfig()
    #按键检测循环
    if espid and ssid and pwd and sAddr and sPort:
        print('espid:',espid)
        print('wifi:',ssid,pwd)
        print('server:',sAddr,sPort)
        checkConfig()
        initAllTimer()
        do_connect()
        time.sleep(1)
    else:
        time.sleep_ms(100)
        uartConfig()
        time.sleep_ms(100)
        resetESP()
    while True:
        time.sleep_ms(300)
        selectSocket()
        time.sleep_ms(300)
        connectServer()

if __name__ == '__main__':  
    main()
    