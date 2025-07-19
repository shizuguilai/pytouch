# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import tDriver as t
import time

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


def conventNumber2String(n):
    tmpstr = str(n)
    lth = len(tmpstr)
    tmpstr = (6-lth)*'0' + tmpstr
    return tmpstr

def sendNumber(n):
    strn = conventNumber2String(n)
    print(strn)
    for i,v in enumerate(strn):
        tmp = int(v)
        touchOncePin(tmp)
        time.sleep_ms(200)

isRUN = False

def wait(t):
    global isRUN
    for i in range(t):
        print(i)
        time.sleep(1)
        tkey = tobj.key.value()
        if not tkey:
            isRUN = not isRUN
            return isRUN
    return True
        

def chickKey():
    global isRUN
    tkey = tobj.key.value()
    if not tkey:
        isRUN = not isRUN

#主函数,点击器程序从这里开始运行
def main():
    global isRUN
    while True:
        tkey = tobj.key.value()
        if not tkey:
            isRUN = not isRUN
            time.sleep(1)
        if isRUN:
            for i in range(102563,1000000):
                # touchOncePin(10)
                time.sleep_ms(500)
                sendNumber(i)
                chickKey()
                # if not wait(10):
                #     return
        time.sleep_ms(100)

if __name__ == '__main__':  
    main()
    