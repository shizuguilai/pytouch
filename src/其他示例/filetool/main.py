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


keynum = 0

runlist = []
            #0001001001001001
keyzus = {1:[1,4,7,10,13],2:[2,5,8,11,14],3:[3,6,9,12,15]}

def readCmdFromFile():
    global runlist
    f = open('f.txt','r')
    fstr = f.read()
    f.close()
    fstrs = fstr.split('\n')
    for i,v in enumerate(fstrs):
        if len(v) > 2:
            tmpv = v.replace('\r','')
            runlist.append(tmpv)

    print(str(runlist))
runtimes = 160

TIMEOBJ = None

def stopAll():
    global TIMEOBJ
    global runtimes
    global keynum
    global nowTouchState
    TIMEOBJ.deinit()          #循环次数到了，程序结束
    keynum = 0
    nowTouchState = 0
    runtimes = 160
    setAllPinStates(0b1111111111111111)

#定时器时间达到后的回调函数
def onTimerEnd(tim):
    global keynum
    global runtimes
    global nowTouchState
    print(keynum,len(runlist))
    datstr = runlist[keynum].split(',')
    k = int(datstr[0])
    t = int(datstr[1])
    s = int(datstr[2])
    if s == 0:
        for i,v in enumerate(keyzus[k]):
            touchPin(v)
    else:
        for i,v in enumerate(keyzus[k]):
            unTouchPin(v)
    keynum +=1
    if(keynum >= len(runlist)):
        keynum = 0
        runtimes -= 1
        print('run times:%d'%(runtimes))
    if runtimes < 0:
        #循环次数到了，程序结束
        stopAll()
        return
    tim.init(period=t,mode=Timer.ONE_SHOT ,callback=onTimerEnd)
    

nowTouchState = 0 #0:当前停止状态,1:当关前运行状态,2:当前为暂停状态,3:当前为复位重启状态
#短按函数
def shotDown(tim):
    global nowTouchState
    global keynum
    if nowTouchState == 0:      #在停止状态下按了按键 
        keynum = 0              #设置当前运行从头开始
        nowTouchState = 1       #设置当前状态为运行状态
        onTimerEnd(tim)           #启动工作延时定时器  
    elif nowTouchState == 1:    #当前工作状态为正常运行,则状态要改为暂停运行
        stopAll()

#主函数,点击器程序从这里开始运行
def main():
    global TIMEOBJ
    setAllPinStates(0b1111111111111111)
    readCmdFromFile()
    tim = Timer(-1)  #新建一个虚拟定时器
    TIMEOBJ = tim
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
                shotDown(tim)
        else:
            time.sleep_ms(10)

    
if __name__ == '__main__':  
    main()
    