import machine
import time

SCLPIN =  machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP)
SDAPIN = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)

#主板向从板发送数据,一次只发一个字节
#发送数据格式:gpio4作为时钟,gpio5作为数据线
#启始:gpio4输出高电平,gpio5从高向低变化
#结速:gpio4输出高电平,gpio5从低向高变化
#发送一个位,gpio4上升沿时,从机可读取gpio5的电平
#主机准备数据,gpio4为低电平时,设置gpio5的电平,为从机读取数据做准备

#state:1,开始,2,结束,3,数值修改,4,数值传送,5,无效状态,为数值修改做准备,6,两个同时改变,读书状态错误
def checkstate():
    lastscl = SCLPIN.value()
    lastsda = SDAPIN.value()
    while True:
        time.sleep_us(10)
        scl = SCLPIN.value()
        sda = SDAPIN.value()
        if scl != lastscl or sda != lastsda:
            break
    if lastscl == scl and lastscl == 1:#时钟高电平,sda数据发生变化
        if sda == 0 and lastsda == 1:#数据下降沿开始标志
            return 1,0
        elif sda == 1 and lastsda == 0:#数据上升沿,结束标志
            return 2,0
    elif lastscl == scl and lastscl == 0:#数据更新,时钟高电平,sda数据发生变化
        if sda == 0 and lastsda == 1:#数据下降沿,修改数值为低
            return 3,0
        elif sda == 1 and lastsda == 0:#数据上升沿,修改数值为高
            return 3,1
    elif sda == lastsda and sda == 1: #数值发送,时钟沿变化
        if lastscl == 0 and scl == 1: #时钟上升沿,为发送数据
            return 4,1
        elif lastscl == 1 and scl == 0: #时钟下降,为修改数值做准备
            return 5,0
    elif sda == lastsda and sda == 0: #数值发送,时钟沿变化
        if lastscl == 0 and scl == 1: #时钟上升沿,为发送数据
            return 4,0
        elif lastscl == 1 and scl == 0: #时钟下降,为修改数值做准备
            return 5,0
    else:
        return 6,0
def isStart():
    st,v = checkstate()
    if st == 1:
        return True
    else:
        return False

def isEnd():
    st,v  = checkstate()
    if  st == 2:
        return True
    else:
        return False
#时钟从低变高时读取一个位数据,再等时间变低
def readBit():
    while True:
        st,v = checkstate()
        if st == 4:
            return v
        else:
            time.sleep_us(10)
            continue
    
def readByte():
    dat = 0x00
    for i in range(8):
        tmp = 0x00 | readBit()
        dat = dat | (tmp << (7-i))
    return dat
def readBytes(count):
    readbuff = []
    for i in range(count):
        dat = readByte()
        readbuff.append(dat)
    return bytearray(readbuff)

def reciveData():
    while not isStart():
        time.sleep_us(10)
    # print('start ok')
    count = readByte()
    # print('count',count)
    datas = readBytes(count)
    while not isEnd():
        time.sleep_us(10)
    return datas
