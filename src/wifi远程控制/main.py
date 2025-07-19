#power by fengmm521.taobao.com
#wechat:woodmage
import tDriver as t
import time
import socketUtil

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
danshu     = 0b1010101010101010    #单数按下状态
shuanshu   = 0b0101010101010101    #双数按下状态

isRUN = False                      #定义程序运行控制全局变量

type2Pins = {1:['0','1'],2:['2','3'],3:['4','5'],4:['6','7'],5:['8','9'],6:['a','b'],7:['c','d'],8:['e','f'],9:['g','h'],10:['i','j'],11:['k','l'],12:['m','n'],13:['o','p'],14:['q','r'],15:['s','t'],16:['u','v']}

touchState = {}

def inittouchPins():
    global touchState
    for k,v in type2Pins.items():
        touchState[v[0]] = [k,0]
        touchState[v[1]] = [k,1]

def cmdrun(cmd):
    if cmd not in touchState:
        if cmd == 'x':
            moveUP()   #向上滑动
        elif cmd == 'y':
            moveDown() #向下滑动
        return
    cmdtmp = touchState[cmd]
    if cmdtmp[1] == 0:
        touchPin(cmdtmp[0])
    else:
        unTouchPin(cmdtmp[0])

#收到来自socket客户端发送的消息
def servercallback(data):
    if type(data) != str:
        data = data.decode()
    cmdrun(data)
        
#主函数,点击器程序从这里开始运行
def main():
    global isRUN                     #引用全局变量isRUN
    setAllPinStates(allUntouch)      #初始化所有点击头为抬起状态
    inittouchPins()
    socketUtil.connect_wifi('wifi名称','wifi密码') #连接wifi
    socketUtil.startServer(servercallback,host = '0.0.0.0',port = 23,maxclients = 5)        #启动socket服务器的23端口,设置最大客户端数量为5

if __name__ == '__main__':  
    main()
