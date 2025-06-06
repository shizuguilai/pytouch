# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import tDriver as t
import time
from machine import Timer

TIMEOBJ = None
#实始化一个点击器控制实例对象
tobj = t.TouchObj()
pindict = {'1':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'0':10,'ok':11}
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


def clearAllPinStates():
    tobj.clearAllTouch()

def conventNumber2String(n):
    tmpstr = str(n)
    lth = len(tmpstr)
    tmpstr = (6-lth)*'0' + tmpstr
    return tmpstr

def sendNumber(n):
    strn = conventNumber2String(n)
    print(strn)
    for i,v in enumerate(strn):
        if not isRUN:
            return
        touchOncePin(v)
        time.sleep_ms(150)
    touchOncePin('ok')
isRUN = False
baseNum = 0
endNum = 999999
index = baseNum
def chickKey():
    global isRUN,index
    tkey = tobj.key.value()
    if not tkey:
        lastTime = time.ticks_ms()
        time.sleep_ms(100)
        while not tkey:
            tkey = tobj.key.value()
            if time.ticks_ms() - lastTime > 5000:
                isRUN = False
                index = baseNum
                print('reset and stop:',index)
                return True
            time.sleep_ms(10)
        isRUN = not isRUN
        if not isRUN:
            print('pause:',index)
            clearAllPinStates()
    return False

def resetFlog():
    for i in range(30):
        touchPin(15)
        time.sleep_ms(100)
        unTouchPin(15)
        time.sleep_ms(100)
#定时器时间达到后的回调函数
def onTimerEnd(tim):
    if chickKey():
        resetFlog()
    if isRUN:
        tim.init(period=100,mode=Timer.ONE_SHOT ,callback=onTimerEnd)

#主函数,点击器程序从这里开始运行
def main():
    global isRUN,index,TIMEOBJ
    tim = Timer(-1)  #新建一个虚拟定时器
    TIMEOBJ = tim
    print('start:',baseNum)
    print('end:',endNum)
    while True:
        tkey = tobj.key.value()
        if not tkey:
            isRUN = not isRUN
            time.sleep(1)
            if isRUN:
                 tim.init(period=100,mode=Timer.ONE_SHOT ,callback=onTimerEnd)
            print('isRUN:',isRUN)
        if isRUN:
            time.sleep_ms(600)
            sendNumber(index)
            if isRUN:
                index += 1
            if index > endNum:
                print('end',endNum)
                break
        time.sleep_ms(100)

if __name__ == '__main__':  
    main()
    