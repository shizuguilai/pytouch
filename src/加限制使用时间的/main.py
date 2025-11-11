#power by fengmm521.taobao.com
#wechat:woodmage
import tDriver as t
import time
import uartUtil
from machine import Timer



BASETIME = 60*60*24   #到计时时间,第一个6是表示60秒,因为计时器是10秒运行一次,第二个60是表示60分钟,第三个24表示是24小时
BASERUN = 100           #运行次数

#实始化一个点击器控制实例对象
tobj = t.TouchObj()
#生成随机整数
def randint(min, max):
    return t.randint(min, max)

def isExists(pth):
    try:
        f = open(pth,'rb')
        f.close()
        return True
    except Exception:
        return False

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
    time.sleep_ms(35)   #按下时间为35毫秒,这个时间可以根据需要修改,建议30~100之间
    unTouchPin(pNumber) #对应点击头抬起
    time.sleep_ms(20)   #抬起后再等20毫秒

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

#定时运行相关
timecount = 60*60*24   #到计时时间,第一个6是表示60秒,因为计时器是10秒运行一次,第二个60是表示60分钟,第三个24表示是24小时
def saveTime():
    with open('tc', 'w') as f:
        s = timecount % 60
        m = (timecount // 60) % 60
        h = (timecount // 60) // 60
        f.write('%d:%d:%d'%(h,m,s))
def initTime():
    global timecount
    if isExists('rc'):
        with open('tc', 'r') as f:
            t = f.read()
            h,m,s = t.split(':')
            timecount = int(h)*60*60 + int(m)*60 + int(s)
    else:
        timecount = BASETIME
        saveTime()
tim = Timer(-1)
#10秒运行一次
def onTimerEnd(tim):
    global timecount
    timecount -= 10
    if timecount <= 0:
        timecount = 0
    saveTime()
    # tim.init(period=10000,mode=Timer.PERIODIC ,callback=onTimerEnd)   #5秒内按键只触发一次
def startTimer():
    tim.init(period=10000,mode=Timer.PERIODIC ,callback=onTimerEnd)
def stopTimer():
    tim.deinit()

#运行次数相关
runCount = 100        #运行次数
def chickRunState():
    global runCount
    runCount -= 1
    with open('rc', 'w') as f:
        f.write('%d'%runCount)
    if runCount <= 0:         #程序运行次数大于0时,可运行
        print('程序运行次数已用完')
        return True
    else:
        print('剩余运行次数:',runCount)
    if timecount <= 0:         #程序运行时间大于0时,可运行
        print('程序运行时间已用完')
        return True
    else:
        print('剩余运行时间:',timecount)
    return False
def initRunCount():
    global runCount
    if isExists('rc'):
        with open('rc', 'r') as f:
            runCount = int(f.read())
            if runCount < 0:
                runCount = -1
    else:
        with open('rc', 'w') as f:
            f.write('%d'%BASERUN)
        runCount = BASERUN

allUntouch = 0b1111111111111111    #所有点击头抬起状态
danshu     = 0b1010101010101010    #单数按下状态
shuanshu   = 0b0101010101010101    #双数按下状态

isRUN = False                      #定义程序运行控制全局变量

def uartCheck():
    dat = uartUtil.reciveDat() #True表示每次只接收一个字节数据,只要有数据就一直接收,默认是False,接收一行数据,只有以换行符结束才会返回
    if dat: #接收到数据,dat将不为None
        print('recive uart data:%s'%(dat.decode())) #decode是把字节流数据转成字符串格式
        dat = dat.decode().strip() #strip()是去掉字符串两边的空格
        print(len(dat),dat)
        if dat == '1':
            print('touch pin 1')
            touchOncePin(1)
        elif dat == '2':
            touchOncePin(2)
        elif dat == '3':
            touchOncePin(3)
        elif dat == '4':
            touchOncePin(4)
        elif dat == '5':
            touchOncePin(5)
        elif dat == '6':
            touchOncePin(6)
        elif dat == '7':
            touchOncePin(7)
        elif dat == '8':
            touchOncePin(8)
        elif dat == '9':
            touchOncePin(9)
        elif dat == 'a':
            touchOncePin(10)
        elif dat == 'b':
            touchOncePin(11)
        elif dat == 'c':
            touchOncePin(12)
        elif dat == 'd':
            touchOncePin(13)
        elif dat == 'e':
            touchOncePin(14)
        elif dat == 'f':
            touchOncePin(15)
        elif dat == 'g':
            touchOncePin(16)

#主函数,点击器程序从这里开始运行
def main():
    global isRUN,runCount                     #引用全局变量isRUN,runCount:程序运行状态,程序运行次数
    setAllPinStates(allUntouch)      #初始化所有点击头为抬起状态
    initRunCount()                     #初始化程序运行次数
    initTime()                         #初始化程序运行时间
    startTimer()                     #启动程序运行时间定时器
    while True:
        tkey = tobj.key.value()      #检测物理按键是否被按下,当按键按下时tkey为0,否则为1
        if not tkey:
            isRUN = not isRUN        #程序运行状态取反
            time.sleep(0.03)            #按键被按下,按键消抖延时1秒
        if isRUN:
            if chickRunState():             #检查运行次数或者运行时间是否到期,到期就停止程序
                isRUN = False
                continue
            touchOncePin(1)          #j1点击一次
            time.sleep_ms(31)       #延时等待31毫秒,1000毫秒=1秒，最小30
            touchOncePin(2)          #j2点击一次
            time.sleep_ms(350)       #延时等待350毫秒,1000毫秒=1秒，最小350
            touchOncePin(3)          #j3点击一次
            time.sleep_ms(110)       #延时等待110毫秒,1000毫秒=1秒，最小80
            touchOncePin(4)          #j4点击一次
            time.sleep_ms(35)       #延时等待35毫秒,1000毫秒=1秒，最小30
            touchOncePin(5)          #j5点击一次
            time.sleep_ms(32)       #延时等待29毫秒,1000毫秒=1秒，最小30
            touchOncePin(6)          #j6点击一次
            time.sleep_ms(30)       #延时等待30毫秒,1000毫秒=1秒，最小30
            touchOncePin(7)          #j7点击一次
            time.sleep_ms(145)       #延时等待140毫秒,1000毫秒=1秒
            isRUN = False            #停止,等待下一次按键按下启动
        uartCheck()                  #检查串口是否有数据输入,在这个函数中进行接收

if __name__ == '__main__':  
    main()
