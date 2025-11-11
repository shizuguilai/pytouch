#power by fengmm521.taobao.com
#wechat:woodmage
import tDriver as t
import machine
import time
from machine import Timer

#实始化一个点击器控制实例对象
tobj = t.TouchObj()

key1 = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)
key2 = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP)
key3 = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_UP)



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
AllTouch = 0                       #所有点击头按下状态

isKey1 = False
isKey2 = False
isKey3 = False

def onTimerEnd(tim):
    global isKey1,isKey2,isKey3
    if isKey1:
        isKey1 = False
    if isKey2:
        isKey2 = False
    if isKey3:
        isKey3 = False
    
def touchAllOnce(k,tim):
    global isKey1,isKey2,isKey3
    print('k=%d'%(k))
    if k == 1:
        isKey1 = True
    elif k == 2:
        isKey2 = True
    elif k == 3:
        isKey3 = True
    if isKey1 or isKey2 or isKey3:
        for i in range(1):
            setAllPinStates(AllTouch)
            time.sleep_ms(120)
            setAllPinStates(allUntouch)
            time.sleep_ms(120)
        tim.init(period=5000,mode=Timer.ONE_SHOT ,callback=onTimerEnd)   #5秒内按键只触发一次
        

#主函数,点击器程序从这里开始运行
def main():
    global isKey1,isKey2,isKey3
    setAllPinStates(allUntouch)      #初始化所有点击头为抬起状态
    timobj = Timer(-1)
    while True:
        tkey = key1.value()      #检测物理按键是否被按下,当按键按下时tkey为0,否则为1
        if not tkey:
            if not isKey1:
                touchAllOnce(1,timobj)
        tkey = key2.value()      #检测物理按键是否被按下,当按键按下时tkey为0,否则为1
        if not tkey:
            if not isKey2:
                touchAllOnce(2,timobj)
        tkey = key3.value()      #检测物理按键是否被按下,当按键按下时tkey为0,否则为1
        if not tkey:
            if not isKey3:
                touchAllOnce(3,timobj)
        time.sleep_ms(100)              #延时100毫秒
if __name__ == '__main__':  
    main()
