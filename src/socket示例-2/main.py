#power by fengmm521.taobao.com
#wechat:woodmage
import tDriver as t
import time
import uartUtil
import machine
import socketUtil

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
SSID = 'XY108771'
PASSWORD = '12345678'
serverIP = '106.14.238.240'
serverPORT = 9527

def sendMsgToServer(msg):
    socketUtil.sendMsgToServer(msg)

def onSocketRecive(socket,data):
    print('recive:',data)
    if data == 'pong':
        return
    runCmd(data)
    sendMsgToServer('{"ctype":0,"cmd":"ok"}')

def connectWifi():
    socketUtil.connect_wifi(SSID,PASSWORD)
    socketUtil.concectServer(serverIP,serverPORT)
    sendMsgToServer('ping')

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
#单字节指令处理
def runCmd(dat):
    global uartMODE
    if dat == '@' or dat == '!':
        uartMODE = dat
    elif dat == '$':
        machine.reset()
    elif dat == 'x':
        setAllPinStates(0)
    elif dat == 'y':
        setAllPinStates(0xffff)
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
def touch16Pins(reciveBuff):
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

#主函数,点击器程序从这里开始运行
def main():
    global isRUN                     #引用全局变量isRUN
    setAllPinStates(allUntouch)      #初始化所有点击头为抬起状态
    tkey = tobj.key.value()      #检测物理按键是否被按下,开机时按键被按下,恢复出厂设置
    connectWifi() #进入客户端模式
    heartstart = time.time()
    while True:
        # tkey = tobj.key.value()      #检测物理按键是否被按下,当按键按下时tkey为0,否则为1
        # if not tkey:
        #     isRUN = not isRUN        #程序运行状态取反
        #     time.sleep(1)            #按键被按下,按键消抖延时1秒
        # if isRUN:
        #     isRUN = False            #停止,等待下一次按键按下启动
        time.sleep_ms(100)
        socketUtil.reciveData(onSocketRecive)  #100ms检查一次是否有数据
        if time.ticks_diff(time.time(), heartstart) > 10: #10s发送一次心跳包
            heartstart = time.time()
            sendMsgToServer('ping')
        time.sleep_ms(100)

if __name__ == '__main__':  
    main()
