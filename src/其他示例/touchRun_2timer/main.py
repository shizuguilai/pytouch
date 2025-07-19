# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import tDriver as t
import time
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

#1234,5678
touchlist1 = {1:[1,5],2:[2,6],3:[3,7],4:[4,8]}
touchps1 = [1,2,3,2,4]
touchdelay1 = [1.0,2.0,1.0,2.0,2.0]
tindex1 = 0
isTimerRun1 = False


touchlist2 = {1:[9],2:[10],3:[11],4:[12],5:[13],6:[14]}
touchps2 = [1,2,3,4,5,3,6]
touchdelay2 = [0.7,0.7,2.0,0.7,0.7,2.0,2.0]
tindex2 = 0
isTimerRun2 = False


TIMEOBJ1 = None

TIMEOBJ2 = None

def stopAll():
    global isTimerRun1,isTimerRun2,tindex1,tindex2
    global nowTouchState
    if isTimerRun1:
        TIMEOBJ1.deinit()          #循环次数到了，程序结束
        isTimerRun1 = False
    if isTimerRun2:
        TIMEOBJ2.deinit()          #循环次数到了，程序结束
        isTimerRun2 = False
    tindex1 = 0
    tindex2 = 0
    nowTouchState = 0
    setAllPinStates(0b1111111111111111)
    print('stop work!')

#定时器时间达到后的回调函数
def onTimerEnd1(tim1):
    global nowTouchState,isTimerRun1,tindex1
    isTimerRun1 = False
    if tindex1 >= len(touchps1):
        tindex1 = 0
    tps = touchlist1[touchps1[tindex1]]
    print('on 1touch pins',tps)
    for i,v in enumerate(tps):
        touchPin(v)
    time.sleep_ms(100)
    for i,v in enumerate(tps):
        unTouchPin(v)
    time.sleep_ms(100)
    dt = int(touchdelay1[tindex1]*1000)
    tindex1 += 1
    isTimerRun1 = True
    tim1.init(period=dt,mode=Timer.ONE_SHOT ,callback=onTimerEnd1)

def onTimerEnd2(tim2):
    global nowTouchState,isTimerRun2,tindex2
    isTimerRun2 = False
    if tindex2 >= len(touchps2):
        tindex2 = 0
    # print(tindex2)
    # print(touchps2[tindex2])
    tps = touchlist2[touchps2[tindex2]]
    print('on 2touch pins',tps)
    for i,v in enumerate(tps):
        touchPin(v)
    time.sleep_ms(100)
    for i,v in enumerate(tps):
        unTouchPin(v)
    time.sleep_ms(100)
    dt = int(1000*touchdelay2[tindex2])
    tindex2 += 1
    isTimerRun2 = True
    tim2.init(period=dt,mode=Timer.ONE_SHOT ,callback=onTimerEnd2)
    

nowTouchState = 0 #0:当前停止状态,1:当关前运行状态
#短按按键函数
def shotDown(tim1,tim2):
    global nowTouchState
    global isTimerRun1,isTimerRun2
    print('button push!')
    if nowTouchState == 0:      #在停止状态下按了按键 
        nowTouchState = 1       #设置当前状态为运行状态
        if not isTimerRun1 and not isTimerRun2:
            print('start work:')
            onTimerEnd1(tim1)           #启动工作延时定时器
            onTimerEnd2(tim2)           #启动工作延时定时器
    elif nowTouchState == 1:    #当前工作状态为正常运行,则状态要改为暂停运行
        stopAll()


#主函数,点击器程序从这里开始运行
def main():
    global TIMEOBJ1,TIMEOBJ2
    setAllPinStates(0b1111111111111111)
    tim1 = Timer(-1)    #新建一个虚拟定时器1
    TIMEOBJ1 = tim1
    tim2 = Timer(-2)   #新建一个虚拟定时器2
    TIMEOBJ2 = tim2
    keydowntime = 0
    keyuptime = 0
    #按键检测循环
    while True:
        tkey = tobj.key.value()
        if not tkey:
            keydowntime = time.time()
        else:
            keyuptime = time.time()
        if keydowntime and keyuptime and keyuptime > keydowntime:
            dtime = keyuptime - keydowntime
            if dtime > 0:
                keydowntime = 0
                shotDown(tim1,tim2)
        else:
            time.sleep_ms(10)

    
if __name__ == '__main__':  
    main()
    