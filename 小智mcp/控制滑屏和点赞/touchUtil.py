#!/usr/bin/env python
# -*- coding: utf-8 -*-
#本代码来自所出售产品的淘宝店店主编写
#未经受权不得复制转发
#淘宝店：https://fengmm521.taobao.com/
#再次感谢你购买本店产品
import os,sys
import serial
import time

SERIALOBJ = None
serialPORT = 'com10'
#'@'工作模式字典
type2Pins = {1:['0','1'],2:['2','3'],3:['4','5'],4:['6','7'],5:['8','9'],6:['a','b'],7:['c','d'],8:['e','f'],9:['g','h'],10:['i','j'],11:['k','l'],12:['m','n'],13:['o','p'],14:['q','r'],15:['s','t'],16:['u','v']}

def readcom(timeout=0.5):
    if SERIALOBJ == None:
        print("串口未打开")
        return
    n = SERIALOBJ.inWaiting()
    while n<=0:
        time.sleep(0.01)
        n = SERIALOBJ.inWaiting()
        timeout = timeout - 0.01
        if timeout<=0:
            return
    pstr = SERIALOBJ.read(n)
    print(pstr.decode())

def sendcmd(cmd):
    if SERIALOBJ == None:
        print("串口未打开")
        return
    sendstr = str(cmd) + '\n'
    print(sendstr)
    s = SERIALOBJ.write(sendstr.encode())
    SERIALOBJ.flush()
    return 'ok'

def sendAndread(v):
    sendcmd(v)
    time.sleep(0.05)
    readcom()


def getPinDat(p):
    return type2Pins[p]

def touch(p):
    pstr = type2Pins[p][0]
    sendAndread(pstr)

def untouch(p):
    pstr = type2Pins[p][1]
    sendAndread(pstr)

def touchpin(n):
    touch(n)
    time.sleep(0.03)
    untouch(n)
    time.sleep(0.03)

def openSerial():
    global SERIALOBJ
    SERIALOBJ = serial.Serial(serialPORT,115200,timeout=1)
    time.sleep(1)
    sendAndread('@')

def closeSerial():
    global SERIALOBJ
    SERIALOBJ.close()

def test():
    global SERIALOBJ
    btv = 115200
    t = serial.Serial(serialPORT,btv,timeout=1)
    SERIALOBJ = t
    if t:
        print(t.name)               #串口名
        print(t.port)               #串口号
        print(t.baudrate)           #波特率
        print(t.bytesize)           #字节大小
        print(t.parity)             #校验位N－无校验，E－偶校验，O－奇校验
        print(t.stopbits)           #停止位
        print(t.timeout)            #读超时设置
        print(t.writeTimeout)       #写超时
        print(t.xonxoff)            #软件流控
        print(t.rtscts)             #硬件流控
        print(t.dsrdtr)             #硬件流控
        print(t.interCharTimeout)   #字符间隔超时
        print('-'*10)
        time.sleep(1)
        # readcom(t)
        sendAndread(t, '@')
        for i in range(1):
            touchpin(1)
            touchpin(0)
            touchpin(0)
            touchpin(8)
            touchpin(6)
        t.close()
    else:
        print('串口不存在')

if __name__ == '__main__':
    args = sys.argv
    fpth = ''
    # if len(args) == 2 :
    #     pass
    # else:
    test()