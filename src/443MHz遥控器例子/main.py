#power by fengmm521.taobao.com
#wechat:woodmage
import tDriver as t
import time
import rfUtil

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
    tobj.move([1,2,3,4],5)  #按J1,J2,J3,J4顺序滑动,第二个参数5是滑动时间,单位是毫秒
#向下滑动操作,正好和向上相反
def moveDown():
    tobj.move([4,3,2,1],5) #按J4,J3,J2,J1顺序滑动,第二个参数5是滑动时间,单位是毫秒

#使用16位的按键状态数一次控制所有点击头状态
def setAllPinStates(state):
    tobj.set16Pins(state)
    tobj.updateData()

allUntouch = 0b1111111111111111    #所有点击头抬起状态
danshu     = 0b1010101010101010    #单数按下状态
shuanshu   = 0b0101010101010101    #双数按下状态

isRUN = False                      #定义程序运行控制全局变量


#实始化一个点击器控制实例对象
tobj = t.TouchObj()

tSTATE  = [1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1] #定义一个16位按键状态数组,用于存储每个按键的当前状态
RFKVDict = {1:1,2:3,3:5,4:4,5:2,6:6,7:7,8:8,9:9,10:10,11:11,12:12,13:13,14:14,15:15,0:16,16:17,64:18} #定义一个按键编号和点击头编号的对应关系
def checkRF():
    dat = rfUtil.rfRecive()
    if dat:
        print(dat) #[1705, 827, 1],说明:[两次按键间隔,遥控器地址,按键编号,1~18]
        ktmp = RFKVDict[dat[2]]
        if ktmp == 17:
            setAllPinStates(0xFFFF) #所有点击头抬起,或者继电器动作
            for i in range(16):
                tSTATE[i] = 0
        elif ktmp == 18:
            setAllPinStates(0x0000) #所有点击头按下,或者继电器停止
            for i in range(16):
                tSTATE[i] = 1
        else:
            if tSTATE[ktmp-1] == 0:
                tSTATE[ktmp-1] = 1
                touchPin(ktmp)
            else:
                tSTATE[ktmp-1] = 0
                unTouchPin(ktmp)
        rfUtil.next()

#主函数,点击器程序从这里开始运行
def main():
    global isRUN                     #引用全局变量isRUN
    setAllPinStates(allUntouch)      #初始化所有点击头为抬起状态
    while True:
        tkey = tobj.key.value()      #检测板子上按键是否被按下,当按键按下时tkey为0,否则为1
        if not tkey:
            isRUN = not isRUN        #程序运行状态取反
            if isRUN:
                rfUtil.init()            #启动遥控器检测
            else:
                rfUtil.end()             #关闭遥控器
            print('isRUN:', isRUN)
            time.sleep(1)            #按键被按下,按键消抖延时1秒
        if isRUN:
            checkRF()                #处理遥控器按键数据
        time.sleep_ms(100)  # 主循环继续运行

if __name__ == '__main__':  
    main()
