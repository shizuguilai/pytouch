#power by fengmm521.taobao.com
#wechat:woodmage
import tDriver as t
import time
import uartUtil
import socketUtil
import config
import touchTimer
import json
from machine import Pin

reciveBuff = ''
isRUN = False                      #定义程序运行控制全局变量

redata = None
sendDats = None

def sendMsgToServer(msg):
    socketUtil.sendMsgToServer(msg)

def onSocketRecive(socket,data):
    print(data)
    global redata,sendDats
    try:
        if not redata:
            redata = data
        else:
            redata += data
        datstr = str(redata, 'utf8')
        print(datstr,len(datstr))
        if datstr[0] != '{' and datstr.find('#') != -1:
            redata = None
            return
        datdic = json.loads(datstr)
        #{"p":1,"t1":50,"t2":50,"c":1}
        print(datdic)
        back = touchTimer.runTouchCmd(datdic)
        if back:
            sendMsgToServer('2:{"p":"%s","st":0,"id":"%s"}'%(datdic['p'],config.cfgDict['id']))
            # sendDats.append('2:{"p":"%s","st":0,"id":"%s"}'%(datdic['p'],espid))
            # cs.write('2:{"p":"%s","st":0,"id":"%s"}'%(datdic['p'],espid))
        else:
            sendMsgToServer('2:{"p":"%s","st":-1,"id":"%s"}'%(datdic['p'],config.cfgDict['id']))
            # sendDats.append('2:{"p":"%s","st":-1,"id":"%s"}'%(datdic['p'],espid))
        redata = None
    except Exception as e:
        print('callback data erro')
        return

def connectWifi():
    
    socketUtil.connect_wifi(config.cfgDict['ssid'],config.cfgDict['pwd'])
    socketUtil.concectServer(config.cfgDict['sAddr'],config.cfgDict['sPort'])
    socketUtil.reciveData(onSocketRecive)

def uartCheck():
    dat = uartUtil.reciveDat(isRead=True) #True表示每次只接收一个字节数据,只要有数据就一直接收,默认是False,接收一行数据,只有以换行符结束才会返回
    if dat: #接收到数据,dat将不为None
        #为了和最早的arduino固件功能统一,这里把默认固件做只接收一个字节的数据,并按字节处理
        print('recive uart data:')
        if len(dat) == 1:
            config.reciveOneByte(dat)
        else:
            for i,v in enumerate(dat):
                config.reciveOneByte(v)

def openLED():
    led = Pin(2,Pin.OUT)
    led.off()

def closeLED():
    led = Pin(2,Pin.OUT)
    led.on()

#主函数,点击器程序从这里开始运行
def main():
    global isRUN                            #引用全局变量isRUN
    touchTimer.setAllPinStates(0xffff)      #初始化所有点击头为抬起状态
    openLED()
    config.readConfig()
    if config.checkConfig():
        while True:
            connectWifi()
            time.sleep_ms(100)
            if socketUtil.isConnected():
                closeLED()
                touchTimer.startHeart(sendMsgToServer)
                break
            else:
                openLED()
        heartstart = time.time()
        while True:
            time.sleep_ms(100)
            socketUtil.reciveData(onSocketRecive)  #100ms检查一次是否有数据
            if time.ticks_diff(time.time(), heartstart) > 10: #10s发送一次心跳包
                heartstart = time.time()
                touchTimer.sendHeart()   #发送心跳包
    else:
        closeLED()
        uartCheck() #检查串口是否有数据输入,在这个函数中进行接收
        openLED()

if __name__ == '__main__':  
    main()
