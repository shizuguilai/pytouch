#power by fengmm521.taobao.com
#wechat:woodmage
import tDriver as t
import time
import BFUtil
import machine

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




#使用16位的按键状态数一次控制所有点击头状态
def setAllPinStates(state):
    tobj.set16Pins(state)
    tobj.updateData()
#随机延时min~max毫秒
def randDelayMS(min,max):
    dt = t.randint(min,max)#随机延时min~max毫秒
    time.sleep_ms(dt)

allUntouch = 0b1111111111111111    #所有点击头抬起状态

#使用四个点击头组成一列进行向上滑动操作, 从下向上依次是J1,J2,J3,J4的方式排列
def moveUP():
    tobj.move([1,2,3,4])  #按J1,J2,J3,J4顺序滑动
#向下滑动操作,正好和向上相反
def moveDown():
    tobj.move([4,3,2,1]) #按J4,J3,J2,J1顺序滑动


#慢速双击p号按键后点亮屏幕的操作
def doubleTouch(p):
    touchOncePin(p)
    time.sleep(0.3)
    touchOncePin(p)
#快速双击
def doubleTouchFast(p):
    touchOncePin(p)
    touchOncePin(p)

#长按屏幕,默认是3秒
def longTouch(p,t = 3000):
    touchPin(p)
    time.sleep_ms(t)
    unTouchPin(p)

#判断dat是否为整数字符串
def is_int(dat):
    try:
        int(dat)
        return True
    except:
        return False

tDelayTouch = 100      #按下时间,默认毫秒

nowTouchPin = -1

#按下并抬起,即点按一次,pNumber从1~16
def touchOncePin(pNumber):
    global nowTouchPin
    #判断输入的点击头编号是否在1~16范围内,不在时程序直接返回,并报错
    if pNumber < 1 or pNumber > 16: 
        print('pin number erro:%d'%(pNumber)) 
        return
    if nowTouchPin > 0:
        print('heave touch run')
        return
    nowTouchPin = pNumber

#巴法云回调函数,收到巴法云发来的消息后会被调用
def bfCallback(dat):
    global tDelayTouch
    try:
        print(dat)
        intdat = -1
        if is_int(dat): #收到按钮1~按钮16的点击指令,对应点击头点击一次
            intdat = int(dat)
        if intdat >=1 and intdat <= 16:   #对次编号的点击头点击一次
            touchOncePin(intdat)
        elif dat == 'a':           #向上滑动,j1,j2,j3,j4
            tDelayTouch = 100
        elif dat == 'b':           #向下滑动,j1,j2,j3,j4
            tDelayTouch = 200
        elif dat == 'c':           #快速双击
            tDelayTouch = 300
        elif dat == 'd':           #长按
            tDelayTouch = 500
        elif dat == 'e':           #慢速双击,用来点亮屏幕
            tDelayTouch = 1000
        elif dat == 'f':
            tDelayTouch = 3000
        elif dat == 'g':
            tDelayTouch = 6000
        elif dat == 'h':
            tDelayTouch = 12000
        else:
            print('unknow command:%s'%(dat)) #你们发的命令,自行解析吧
    except:
        print('bfCallback error,and reset')
        time.sleep(1)
        machine.reset()
#主函数,点击器程序从这里开始运行
def main():
    global  nowTouchPin,tDelayTouch
    setAllPinStates(allUntouch)               #初始化所有点击头为抬起状态
    uid = '14712ccdbc88a59817d77c64ca2e4c33'  #巴法云uid,自行替换
    ssid = 'wifi名称'                          #wifi名称,自行替换
    password = 'wifi密码'                      #wifi密码,自行替换
    wlan = BFUtil.connect_wifi(ssid,password)        #连接wifi,wifi只能是纯2.4G的,
    BFUtil.start(uid,bfCallback)              #设置巴法云的uid,并设置接收消息回调函数,同时启动巴法云
    nowTouchPin = -1
    tDelayTouch = 100
    resetHour = 24*60*60*10                 #一天,设备重启一次,防止内存泄漏
    count = 0
    while True:
        if nowTouchPin >= 1 and nowTouchPin <= 16:
            touchPin(nowTouchPin)   #对应点击头按下
            time.sleep_ms(tDelayTouch)   #按下时间为60毫秒,这个时间可以根据需要修改,建议30~100之间
            unTouchPin(nowTouchPin) #对应点击头抬起
            time.sleep_ms(1000)   #抬起后再等60毫秒
            nowTouchPin = -1
        if not wlan.isconnected(): #wifi断线重连,直接让设备重启再重连
            time.sleep(1)
            machine.reset()
        count += 1
        if count >= resetHour:
            time.sleep(1)
            machine.reset()
        time.sleep_ms(100)                         #这里是死循环,延时1秒,可以写别的逻辑

if __name__ == '__main__':  
    main()
