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


def clearAllPinStates():
    tobj.clearAllTouch()
allUntouch = 0b1111111111111111    #所有点击头抬起
danshu     = 0b1010101010101010    #单数按下
shuanshu   = 0b0101010101010101    #双数按下


def delayt():
    dtmp = randint(80,100)      #取随机数50-100之间
    time.sleep_ms(dtmp)         #按下时间随机在50-100毫秒间
#单数
def touch1():
    setAllPinStates(danshu)     #单数按下
    delayt()
    setAllPinStates(allUntouch) #单数按下抬起，完成一次点击
    delayt()
    setAllPinStates(danshu)     #单数按下
    delayt()
    setAllPinStates(allUntouch) #单数按下抬起，完成一次点击
    delayt()

#双数
def touch2():
    setAllPinStates(shuanshu) #双数按下
    delayt()
    setAllPinStates(allUntouch) #双数按下抬起，完成一次点击
    delayt()


def delayRandom(tmin,t2max):
    dtmp = randint(tmin,t2max)      #取随机数1200-1500之间
    print(dtmp)
    time.sleep_ms(dtmp)  #延时等会上边随机数的毫秒时间  

#主函数,点击器程序从这里开始运行
def main():
    setAllPinStates(allUntouch)
    isrun = False                     #按键状态，是否启动
    while True:  #无限循环
        tkey = tobj.key.value()
        if not tkey:
            isrun = not isrun
            time.sleep_ms(100)
            if not isrun:
                time.sleep_ms(5000)
        if isrun:
            touch1()                     #单数点击一次
            delayRandom(1400,1500)         #随机等待
            touch2()                     #双数点击一次
            delayRandom(300,350)         #一次循环完成，等300-350毫秒进行下次循环      
        else:
            time.sleep_ms(100)

if __name__ == '__main__':  
    main()
    