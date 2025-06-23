#power by fengmm521.taobao.com
#wechat:woodmage
import tDriver as t
import time
import uartUtil
import machine

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

allUntouch = 0b1111111111111111    #所有点击头抬起状态
danshu     = 0b1010101010101010    #单数按下状态
shuanshu   = 0b0101010101010101    #双数按下状态

isRUN = False                      #定义程序运行控制全局变量

#串口接收数据,指令,会为@模型和!模式,
#@模式把按下和抬起拆分成两步,中间按下时间由发送端控制,!模式是按下和抬起一起发送,中间按下时间在当前程序中控制
uartMODE = '@' #串口模式,默认是@模式
reciveMode = 0 #接收模式,0:接收单字节指令,1:配网接收数据,{wifi名,wifi密码}通过socket控制点击器,2:同时控制所有点击头状态数据,3:巴法云设置,[wifi名,wifi密码,巴法云UID]
reciveBuff = ''
SSID = None
PASSWORD = None
BUID = None
serverIP = None
serverPORT = 0

def onSocketRecive(socket,data):
    runCmd(data)

def onClientConnected(client):
    print('client connected',client)

def connectWifi():
    import socketUtil
    global serverIP,serverPORT
    tmps = reciveBuff.split(',')
    ssid = tmps[0]
    password = tmps[1]
    if len(tmps) == 4: #使用客户端模式
        serverIP = tmps[2]
        serverPORT = int(tmps[3])
        socketUtil.connect_wifi(ssid,password)
        socketUtil.startClient(serverIP,serverPORT,onSocketRecive)
    else:
        socketUtil.startServer(onSocketRecive,onClientConnected,23)
        socketUtil.connect_wifi(ssid,password)

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

def cleanConfig():
    f = open('config.txt','w')
    f.write('')
    f.close()

def saveConfig(ssid,password,uid = '',sSer = '',sPort= ''):
    out = ssid + ',' + password + ',' + uid + ',' + sSer + ',' + str(sPort)+ ',' + uartMODE
    f = open('config.txt','w')
    f.write(out)
    f.close()

def readConfig():
    global SSID,PASSWORD,BUID,serverIP,serverPORT,uartMODE
    try:
        f = open('config.txt','r')
        s = f.read()
        f.close()
        tmps = s.split(',')
        if tmps[0] and tmps[0] != '':
            SSID = tmps[0]
        if tmps[1] and tmps[1] != '':
            PASSWORD = tmps[1]
        if tmps[2] and tmps[2] != '':
            BUID = tmps[2]
        if tmps[3] and tmps[3] != '':
            serverIP = tmps[3]
        if tmps[4] and tmps[4] != '':
            serverPORT = int(tmps[4])
        if tmps[5] and tmps[5] != '':
            uartMODE = tmps[5]
    except:
        print('默认出厂设置')

#单字节指令处理
def runCmd(dat):
    global uartMODE
    if dat == '@' or dat == '!':
        uartMODE = dat
    elif dat == '$':
        cleanConfig()
        machine.reset()
    else:
        if uartMODE == '!':
            touchOncePin(tMode1[dat])
        elif uartMODE == '@':
            tmp = tDMode[dat]
            if tmp[1]:
                touchPin(tmp[0])
            else:
                unTouchPin(tmp[0])
#一次控制16个点击头状态
def touch16Pins():
    integer = int(reciveBuff, 16)
    setAllPinStates(integer)


#判断dat是否为整数字符串
def is_int(dat):
    try:
        int(dat)
        return True
    except:
        return False

#慢速双击p号按键后点亮屏幕的操作
def doubleTouch(p):
    touchOncePin(p)
    time.sleep(0.3)
    touchOncePin(p)
#快速双击
def doubleTouchFast(p):
    touchOncePin(p)
    touchOncePin(p)

#长按屏幕,默认是3秒
def longTouch(p,t = 3000):
    touchPin(p)
    time.sleep_ms(t)
    unTouchPin(p)


#巴法云回调函数,收到巴法云发来的消息后会被调用
def bfCallback(dat):
    print(dat)
    intdat = -1
    if is_int(dat): #收到按钮1~按钮16的点击指令,对应点击头点击一次
        intdat = int(dat)
    if dat == 'h':                      #所有点击头击一次
        setAllPinStates(0)              #16个点击头都按下
        time.sleep_ms(80)               #按下时间80毫秒
        setAllPinStates(allUntouch)     #16个点击头都抬起
    elif intdat >=1 and intdat <= 16:   #对次编号的点击头点击一次
        touchOncePin(intdat)
    elif dat == 'a':           #向上滑动,j1,j2,j3,j4
        moveUP()
    elif dat == 'b':           #向下滑动,j1,j2,j3,j4
        moveDown()
    elif dat == 'c':           #快速双击
        doubleTouchFast(4)      #快速双击J4
    elif dat == 'd':           #长按
        longTouch(4)            #快速双击J4
    elif dat == 'e':           #慢速双击,用来点亮屏幕
        doubleTouch(4)         #慢速双击J4
    else:
        print('unknow command:%s'%(dat)) #你们发的命令,自行解析吧
def runBafaMode():
    import BFUtil
    tmps = reciveBuff.split(',')
    ssid  = tmps[0]
    password = tmps[1]
    uid = tmps[2]
    BFUtil.connect_wifi(ssid,password)        #连接wifi,wifi只能是纯2.4G的,
    BFUtil.start(uid,bfCallback)              #设置巴法云的uid,并设置接收消息回调函数,同时启动巴法云

def reciveOneByte(dat):
    global reciveMode,reciveBuff
    try:
        dat = dat.decode()
        print(dat)
        if dat == '{':  #表示使用串口配网的开始标识
            reciveMode = 1
        elif dat == '}': #配网wifi参数设置完成
            reciveMode = 0
            connectWifi()
            reciveBuff = ''
        elif dat == '<': #表示使用串口同时控制所有点击头状态数据开始标识
            reciveMode = 2
        elif dat == '>': #表示使用串口同时控制所有点击头状态数据结束标识
            reciveMode = 0
            touch16Pins()
            reciveBuff = ''
        elif dat == '[]': #表示使用串口巴法云设置开始标识
            reciveMode = 3
        elif dat == ']': #表示使用串口巴法云设置结束标识
            reciveMode = 0
            runBafaMode()
            reciveBuff = ''
        elif reciveMode != 0: #接收wifi参数
            reciveBuff += dat
        else:
            runCmd(dat)
    except:
        print('recive uart data error')

def uartCheck():
    dat = uartUtil.reciveDat(isRead=True) #True表示每次只接收一个字节数据,只要有数据就一直接收,默认是False,接收一行数据,只有以换行符结束才会返回
    if dat: #接收到数据,dat将不为None
        #为了和最早的arduino固件功能统一,这里把默认固件做只接收一个字节的数据,并按字节处理
        print('recive uart data:')
        if len(dat) == 1:
            reciveOneByte(dat)
        else:
            for i,v in enumerate(dat):
                reciveOneByte(v)
#主函数,点击器程序从这里开始运行
def main():
    global isRUN,reciveBuff                     #引用全局变量isRUN
    setAllPinStates(allUntouch)      #初始化所有点击头为抬起状态
    tkey = tobj.key.value()      #检测物理按键是否被按下,开机时按键被按下,恢复出厂设置
    if not tkey:
        cleanConfig()           #恢复出厂设置
    else:
        readConfig()            #读取配置文件
    if BUID and BUID != '' and SSID and PASSWORD:
        reciveBuff = SSID + ',' + PASSWORD + ',' + BUID
        runBafaMode() #进入巴法云模式
    elif SSID and PASSWORD and serverIP and serverIP != '' and serverPORT:#使用客户端模式
        reciveBuff = SSID + ',' + PASSWORD + ',' + serverIP + ',' + serverPORT
        connectWifi() #进入客户端模式
    elif SSID != '' and PASSWORD != '': #使用socket服务器模式
        reciveBuff = SSID + ',' + PASSWORD 
        connectWifi() #进入客户端模式
    while True:
        tkey = tobj.key.value()      #检测物理按键是否被按下,当按键按下时tkey为0,否则为1
        if not tkey:
            isRUN = not isRUN        #程序运行状态取反
            time.sleep(1)            #按键被按下,按键消抖延时1秒
        if isRUN:
            touchOncePin(1)          #j1点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(2)          #j2点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(3)          #j3点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(4)          #j4点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(5)          #j5点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(6)          #j6点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(7)          #j7点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(8)          #j8点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(9)          #j9点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(10)         #j10点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(11)         #j11点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(12)         #j12点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(13)         #j13点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(14)         #j14点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(15)         #j15点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(16)         #j16点击一次
            isRUN = False            #停止,等待下一次按键按下启动
        uartCheck()                  #检查串口是否有数据输入,在这个函数中进行接收

if __name__ == '__main__':  
    main()
