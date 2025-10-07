#power by fengmm521.taobao.com
#wechat:woodmage
import tDriver as t
import time
import uartUtil

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


def uartCheck():
    dat = uartUtil.reciveDat() #True表示每次只接收一个字节数据,只要有数据就一直接收,默认是False,接收一行数据,只有以换行符结束才会返回
    if dat: #接收到数据,dat将不为None
        print('recive uart data:%s'%(dat.decode())) #decode是把字节流数据转成字符串格式
        dat = dat.decode().strip() #strip()是去掉字符串两边的空格
        print(len(dat),dat)
        if dat == 'x': #收到字符'x'时,向上滑动
            moveUP()
        elif dat == 'y': #收到字符'y'时,向下滑动
            moveDown()
        elif dat == 'z':     #收到字符'z'时,按下1号双击
            touchOncePin(1)
            touchOncePin(1)
        elif dat == '1':        #收到字符'1'时,按下16号点击头
            touchOncePin(16)
        elif dat == '2':        #收到字符'2'时,按下15号点击头
            touchOncePin(15)

#主函数,点击器程序从这里开始运行
def main():
    global isRUN                     #引用全局变量isRUN
    setAllPinStates(allUntouch)      #初始化所有点击头为抬起状态
    while True:
        tkey = tobj.key.value()      #检测物理按键是否被按下,当按键按下时tkey为0,否则为1
        if not tkey:
            isRUN = not isRUN        #程序运行状态取反
            time.sleep(1)            #按键被按下,按键消抖延时1秒
        if isRUN:
            touchOncePin(1)          #j1点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(2)          #j2点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(3)          #j3点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(4)          #j4点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(5)          #j5点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(6)          #j6点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(7)          #j7点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(8)          #j8点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(9)          #j9点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(10)         #j10点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(11)         #j11点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(12)         #j12点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(13)         #j13点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(14)         #j14点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(15)         #j15点击一次
            time.sleep_ms(10)       #延时等待10毫秒,1000毫秒=1秒
            touchOncePin(16)         #j16点击一次
            isRUN = False            #停止,等待下一次按键按下启动
        uartCheck()                  #检查串口是否有数据输入,在这个函数中进行接收

if __name__ == '__main__':  
    main()
