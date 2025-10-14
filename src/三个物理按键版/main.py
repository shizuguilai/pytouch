#power by fengmm521.taobao.com
#wechat:woodmage
import tDriver as t
import machine
import time

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
touch1     = 0b1110110110110110    #单数按下状态 
touch2     = 0b1101101101101101    #双数按下状态
touch3     = 0b1011011011011011    #双数按下状态

Touch_ST = allUntouch


def touchKey(k):
    global Touch_ST
    if k == 1:
        Touch_ST = touch1&Touch_ST
    elif k == 2:
        Touch_ST = touch2&Touch_ST
    elif k == 3:
        Touch_ST = touch3&Touch_ST
    setAllPinStates(Touch_ST)

def untouchKey(k):
    global Touch_ST
    if k == 1:
        Touch_ST = Touch_ST | (~touch1)
    elif k == 2:
        Touch_ST = Touch_ST | (~touch2)
    elif k == 3:
        Touch_ST = Touch_ST | (~touch3)
    setAllPinStates(Touch_ST)



#主函数,点击器程序从这里开始运行
def main():
    global isRun1,isRun2,isRun3                     #引用全局变量isRUN
    setAllPinStates(allUntouch)      #初始化所有点击头为抬起状态
    
    while True:
        tkey = key1.value()      #检测物理按键是否被按下,当按键按下时tkey为0,否则为1
        if tkey:
            untouchKey(1)
        else:
            touchKey(1)
        tkey = key2.value()      #检测物理按键是否被按下,当按键按下时tkey为0,否则为1
        if tkey:
            untouchKey(2)
        else:
            touchKey(2)
        tkey = key3.value()      #检测物理按键是否被按下,当按键按下时tkey为0,否则为1
        if tkey:
            untouchKey(3)
        else:
            touchKey(3)
        time.sleep_ms(50)              #延时50毫秒
if __name__ == '__main__':  
    main()
