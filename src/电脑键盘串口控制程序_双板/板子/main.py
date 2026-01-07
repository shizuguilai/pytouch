#power by fengmm521.taobao.com
#wechat:woodmage
import tDriver as t
import time
import uartUtil
from machine import Timer

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

atouch = 0b1111111111110000    #所有点击头抬起状态
btouch = 0b1111111100001111    #所有点击头抬起状态
ctouch = 0b1111000011111111    #所有点击头抬起状态
dtouch = 0b0000111111111111    #所有点击头抬起状态

isRUN = False                      #定义程序运行控制全局变量

TOBJ = Timer(-99)
touchST = -1

def runTimer(tim):
    global touchST
    if touchST == 1:
        setAllPinStates(atouch)
        time.sleep_ms(80)
        setAllPinStates(allUntouch)
        tim.init(period=250,mode=Timer.ONE_SHOT ,callback=runTimer)
    else:
        setAllPinStates(allUntouch)
        tim.deinit() 

def func_A():
    global touchST,isRUN
    if isRUN:
        print('isRUN A')
        if touchST != 1:
            TOBJ.deinit() 
            touchST = 1
            TOBJ.init(period=150,mode=Timer.ONE_SHOT ,callback=runTimer)
        else:
            touchST = -1
            TOBJ.deinit()
    else:
        print('isRUN false A')

TOBJ_B = Timer(-81)
BLIST = [5,6,7,8]
BIndex = 0
def runTimerBup(tim):
    global BIndex
    unTouchPin(BLIST[BIndex])
    BIndex += 1
    if BIndex >= 4:
        BIndex = 0
    else:
        tim.init(period=300,mode=Timer.ONE_SHOT ,callback=runTimerBDown)
def runTimerBDown(tim):
    touchPin(BLIST[BIndex])
    tim.init(period=80,mode=Timer.ONE_SHOT ,callback=runTimerBup)

def func_B():
    global isRUN,BIndex
    if isRUN:
        print('isRUN B')
        BIndex = 0
        for i,v in enumerate(BLIST):
            unTouchPin(v)
        TOBJ_B.deinit()
        TOBJ_B.init(period=1,mode=Timer.ONE_SHOT ,callback=runTimerBDown)
    else:
        print('isRUN false B')

TOBJ_C = Timer(-82)
CLIST = [9,10,11,12]
CIndex = 0
def runTimerCup(tim):
    global CIndex
    unTouchPin(CLIST[CIndex])
    CIndex += 1
    if CIndex >= 4:
        CIndex = 0
    else:
        tim.init(period=300,mode=Timer.ONE_SHOT ,callback=runTimerCDown)
def runTimerCDown(tim):
    touchPin(CLIST[CIndex])
    tim.init(period=80,mode=Timer.ONE_SHOT ,callback=runTimerCup)

def func_C():
    global isRUN,CIndex
    if isRUN:
        print('isRUN C')
        CIndex = 0
        for i,v in enumerate(CLIST):
            unTouchPin(v)
        TOBJ_C.deinit()
        TOBJ_C.init(period=1,mode=Timer.ONE_SHOT ,callback=runTimerCDown)
    else:
        print('isRUN false C')

TOBJ_D = Timer(-83)
DLIST = [13,14,15,16]
DIndex = 0
def runTimerDup(tim):
    global DIndex
    unTouchPin(DLIST[DIndex])
    DIndex += 1
    if DIndex >= 4:
        DIndex = 0
    else:
        tim.init(period=300,mode=Timer.ONE_SHOT ,callback=runTimerDDown)
def runTimerDDown(tim):
    touchPin(DLIST[DIndex])
    tim.init(period=80,mode=Timer.ONE_SHOT ,callback=runTimerDup)

def func_D():
    global isRUN,DIndex
    if isRUN:
        print('isRUN D')
        DIndex = 0
        for i,v in enumerate(DLIST):
            unTouchPin(v)
        TOBJ_D.deinit()
        TOBJ_D.init(period=1,mode=Timer.ONE_SHOT ,callback=runTimerDDown)
    else:
        print('isRUN false C')

def uartCheck():
    dat = uartUtil.reciveDat() #True表示每次只接收一个字节数据,只要有数据就一直接收,默认是False,接收一行数据,只有以换行符结束才会返回
    if dat: #接收到数据,dat将不为None
        print('recive uart data:%s'%(dat.decode())) #decode是把字节流数据转成字符串格式
        dat = dat.decode().strip() #strip()是去掉字符串两边的空格
        print(len(dat),dat)
        if dat == 'A':#f1
            # print('touch pin 1')
            # touchOncePin(1)
            func_A()
        elif dat == 'B':#f2
            # touchOncePin(2)
            func_B()
        elif dat == 'C':#f3
            func_C()
        elif dat == 'D':#F4
            func_D()
        elif dat == 'E':#f5
            pass
        elif dat == 'F':#f6
            touchOncePin(6)
        elif dat == 'G':#f7
            touchOncePin(7)
        elif dat == 'H':#f8
            touchOncePin(8)
        elif dat == 'I':#f9
            touchOncePin(9)
        elif dat == 'J':#f10
            touchOncePin(10)
        elif dat == 'K':#f11
            touchOncePin(11)
        elif dat == 'L':#f12
            touchOncePin(12)


#主函数,点击器程序从这里开始运行
def main():
    global isRUN                     #引用全局变量isRUN
    isRUN = True
    setAllPinStates(allUntouch)      #初始化所有点击头为抬起状态
    while True:
        tkey = tobj.key.value()      #检测物理按键是否被按下,当按键按下时tkey为0,否则为1
        if not tkey:
            isRUN = not isRUN        #程序运行状态取反
            time.sleep(1)            #按键被按下,按键消抖延时1秒
        uartCheck()                  #检查串口是否有数据输入,在这个函数中进行接收

if __name__ == '__main__':  
    main()
