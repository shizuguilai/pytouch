from machine import Timer
import time
import tDriver as t
import config

socketTimer = Timer(-17) #心跳包定时器

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

#定义16个手机点击头的16个定时器,将会分步进行启动运行
timerDict = {}
usedT = []          #已经使用的Timer
unUsedTs = []       #未使用的Timer

def initAllTimer():
    global timerDict
    for i in range(16):
        tp = i+1
        ttmp = Timer(-(tp))
        timerDict[tp] = ttmp
        unUsedTs.append(tp)
def getTimer():
    global timerDict
    if unUsedTs:
        tmp = unUsedTs.pop(0)
        usedT.append(tmp)
        return tmp
    else:
        return None

m_tST = 0xffff
#字符串转为hex十六进制数
# hex_string = "0xFF"

# an_integer = int(hex_string, 16)

# hex_value = hex(an_integer)
# print(hex_value)

#使用两个字节码控制多个点击头按下
def touchCMD(cmd):
    global m_tST
    an_integer = int(cmd, 16)
    m_tST = m_tST & an_integer
    setAllPinStates(m_tST)
    # hex_value = hex(an_integer)
    # print(hex_value)

#使用字节码控制多个点击头抬起
def unTouchCMD(cmd):
    global m_tST
    an_integer = int(cmd, 16)
    notInt = ~(an_integer)
    m_tST = m_tST | notInt
    setAllPinStates(m_tST)

cmdDict = {}

#点击任务完成,释放定时器使用权
def releaseTimer(tim):
    cmd = cmdDict[str(tim)]
    tid = cmd['tid']
    global timerDict
    index = 0
    for i,v in enumerate(usedT):
        if v  == tid:
            index = i
            break
    usedT.pop(index)
    unUsedTs.append(tid)

serverMsgFunc = None

def tU(tim):
    cmd = cmdDict[str(tim)]
    cmdDict[str(tim)]['c'] -= 1
    unTouchCMD(cmd['p'])
    if cmd['c'] <= 0:
        tim.deinit()
        releaseTimer(tim)
        if serverMsgFunc:
            serverMsgFunc('3:{"p":"%s","st":1,"id":"%s"}'%(cmd['p'],config.cfgDict['id']))
    else:
        if cmd['t2'] >= 30:
            tim.init(period=cmd['t2'],mode=Timer.ONE_SHOT ,callback=tD)
        else:
            tim.init(period=cmd['t1'],mode=Timer.ONE_SHOT ,callback=tD)
def tD(tim):
    cmd = cmdDict[str(tim)]
    touchCMD(cmd['p'])
    tim.init(period=cmd['t1'],mode=Timer.ONE_SHOT ,callback=tU)

def heartEnd(tim):
    global serverMsgFunc
    serverMsgFunc('1:w1#%s'%(config.cfgDict['id']))

def startHeart(msgFunc):
    global serverMsgFunc
    serverMsgFunc = msgFunc
    serverMsgFunc('1:w1#%s'%(config.cfgDict['id']))
    socketTimer.init(period=10000,mode=Timer.ONE_SHOT ,callback=heartEnd)

def runTouchCmd(cmd):
    global cmdDict
    #{"p":1,"t1":50,"t2":50,"c":1}
    tid = getTimer()
    if not tid:
        return False
    t = timerDict[tid]
    cmd['tid'] = tid
    cmdDict[str(t)] = cmd
    touchCMD(cmd['p'])
    t.init(period=cmd['t1'],mode=Timer.ONE_SHOT ,callback=tU)
    return True