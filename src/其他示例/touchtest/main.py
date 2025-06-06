# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import touchDriver as t
import time
from machine import Timer
#实始化一个点击器控制实例对象
tobj = t.TouchObj()
#pNumber按键按下,pNumber从0~15
def touchPin(pNumber):
    tobj.setPin(pNumber,False)
    tobj.updateData()
#pNumber按键抬起,pNumber从0~15
def unTouchPin(pNumber):
    tobj.setPin(pNumber,True)
    tobj.updateData()
#按下并抬起,即点按一次
def touchOncePin(pNumber):
    touchPin(pNumber)
    time.sleep_ms(100)  #按下时间为50毫秒
    unTouchPin(pNumber)
    time.sleep_ms(100)  #抬起后再等50毫秒

#使用16位的按键状态数一次控制所有点击头状态
def setAllPinStates(state):
    tobj.set16Pins(state)
    tobj.updateData()


#主函数,点击器程序从这里开始运行
def main():
    global TIMEOBJ
    setAllPinStates(0b1111111111111111)
    #按键检测循环
    isRun = False
    while True:
        tkey = tobj.key.value()
        if not tkey:
            isRun = not isRun
            if not isRun:
                time.sleep(5)
        if isRun:
            # touchPin(0)
            setAllPinStates(0b0000000000000000)
            time.sleep_ms(100)
            # unTouchPin(0)
            setAllPinStates(0b1111111111111111)
            time.sleep_ms(5000)
        else:
            time.sleep_ms(40)

    
if __name__ == '__main__':  
    main()
    