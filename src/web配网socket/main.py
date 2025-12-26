#power by fengmm521.taobao.com
#wechat:woodmage
import machine
import ujson
#文件是否存在
def isExists(pth):
    try:
        f = open(pth,'rb')
        f.close()
        return True
    except Exception:
        return False
SSID = None
PASSWORD = None
if not isExists('wifi.json'):
    import webconfig
    webconfig.WebConfig().run() #开始web配网,配网成功后自动保存wifi.json,然后重新启动
else:
    with open('wifi.json', 'r') as f:
        config = ujson.load(f)
        SSID = config.get('ssid')
        PASSWORD = config.get('password')
        print('wifi config:',SSID,PASSWORD)
import tDriver as t
import time
import uartUtil
import os

#实始化一个点击器控制实例对象
tobj = t.TouchObj()

delayTouchTime = 50
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
    time.sleep_ms(delayTouchTime)   #按下时间为80毫秒,这个时间可以根据需要修改,建议30~100之间
    unTouchPin(pNumber) #对应点击头抬起
    time.sleep_ms(delayTouchTime)   #抬起后再等80毫秒

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

allUntouch = 0b1111111111111111    #所有点击头抬起状态
danshu     = 0b1010101010101010    #单数按下状态
shuanshu   = 0b0101010101010101    #双数按下状态

isRUN = False                      #定义程序运行控制全局变量

#串口接收数据,指令,会为@模型和!模式,
#@模式把按下和抬起拆分成两步,中间按下时间由发送端控制,!模式是按下和抬起一起发送,中间按下时间在当前程序中控制
uartMODE = '@' #串口模式,默认是@模式
reciveMode = 0 #接收模式,0:接收单字节指令,1:配网接收数据,{wifi名,wifi密码}通过socket控制点击器,2:同时控制所有点击头状态数据,3:巴法云设置,[wifi名,wifi密码,巴法云UID]
reciveBuff = ''



def onSocketRecive(socket,data):
    runCmd(data)

def onClientConnected(client):
    print('client connected',client)

def connectWifi():
    import socketUtil
    socketUtil.connect_wifi(SSID,PASSWORD)
    socketUtil.startServer(onSocketRecive,onClientConnected,23)
        
tMode1 = {'1':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'a':10,'b':11,'c':12,'d':13,'e':14,'f':15,'g':16}
tDMode = {'0':[1,0],
          '1':[1,1],
          '2':[2,0],
          '3':[2,1],
          '4':[3,0],
          '5':[3,1],
          '6':[4,0],
          '7':[4,1],
          '8':[5,0],
          '9':[5,1],
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
          'v':[16,1]}

def cleanWifiConfig():
    os.remove('wifi.json')
    time.sleep_(100)
    machine.reset()
#单字节指令处理
def runCmd(dat):
    global uartMODE
    if dat == '@' or dat == '!':
        uartMODE = dat
    elif dat == '$':  #清除wifi配置,恢复初始设置
        cleanWifiConfig()
    elif dat == 'x':  #重启
        setAllPinStates(0)
    elif dat == 'y':  #关闭所有灯
        setAllPinStates(allUntouch)
    else:
        if uartMODE == '!':
            touchOncePin(tMode1[dat])
        elif uartMODE == '@':
            tmp = tDMode[dat]
            if tmp[1] == 0:
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
def setDelayTime():
    global delayTouchTime
    delayTouchTime = int(reciveBuff)

def reciveOneByte(dat):
    global reciveMode,reciveBuff
    try:
        dat = dat.decode()
        print(dat)
        if dat == '<': #表示使用串口同时控制所有点击头状态数据开始标识
            reciveMode = 2
        elif dat == '>': #表示使用串口同时控制所有点击头状态数据结束标识
            reciveMode = 0
            touch16Pins()
            reciveBuff = ''
        elif dat == '[': #表示设置!模式的延时
            reciveMode = 3
        elif dat == ']': #表示使用串口巴法云设置结束标识
            reciveMode = 0
            setDelayTime()
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
        cleanWifiConfig()           #恢复出厂设置
    else:
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
