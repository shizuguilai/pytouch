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

dtouch =  0b1111111111000000    #所有点击头抬起状态
ftouch =  0b1111111000111111    #所有点击头抬起状态
gtouch =  0b1111000111111111    #所有点击头抬起状态


isRUN = False                      #定义程序运行控制全局变量

sendST = allUntouch

def touchState(st):
    global sendST
    sendST = sendST&st
    setAllPinStates(sendST)

def untouchState(st):
    global sendST
    sendST = sendST|st
    setAllPinStates(sendST)

def func_E():
    global isRUN
    if isRUN:
        print('isRUN D')
        # setAllPinStates(dtouch)
        touchState(dtouch)
    else:
        print('isRUN false B')
def func_e():
    global isRUN
    if isRUN:
        print('isRUN D')
        # setAllPinStates(allUntouch)
        untouchState(~dtouch)
    else:
        print('isRUN false B')

def func_F():
    global isRUN
    if isRUN:
        print('isRUN F')
        # setAllPinStates(ftouch)
        touchState(ftouch)
    else:
        print('isRUN false F')
def func_f():
    global isRUN
    if isRUN:
        print('isRUN F')
        # setAllPinStates(allUntouch)
        untouchState(~ftouch)
    else:
        print('isRUN false F')

def func_G():
    global isRUN
    if isRUN:
        print('isRUN G')
        # setAllPinStates(gtouch)
        touchState(gtouch)
    else:
        print('isRUN false G')
def func_g():
    global isRUN
    if isRUN:
        print('isRUN G')
        # setAllPinStates(allUntouch)
        untouchState(~gtouch)
    else:
        print('isRUN false G')
def uartCheck():
    dat = uartUtil.reciveDat() #True表示每次只接收一个字节数据,只要有数据就一直接收,默认是False,接收一行数据,只有以换行符结束才会返回
    if dat: #接收到数据,dat将不为None
        print('recive uart data:%s'%(dat.decode())) #decode是把字节流数据转成字符串格式
        dat = dat.decode().strip() #strip()是去掉字符串两边的空格
        print(len(dat),dat)
        if dat == 'A':#f1
            # func_A()
            pass
        elif dat == 'E':#f2
            func_E()
        elif dat == 'F':#f3
            func_F()
        elif dat == 'G':#F4
            func_G()
        elif dat == 'e':#f2
            func_e()
        elif dat == 'f':#f3
            func_f()
        elif dat == 'g':#F4
            func_g()
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
