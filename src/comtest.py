#!/usr/bin/env python
# -*- coding: utf-8 -*-
#本代码来自所出售产品的淘宝店店主编写
#未经受权不得复制转发
#淘宝店：https://fengmm521.taobao.com/
#再次感谢你购买本店产品
import os,sys
import serial
import time
import json

try:
    import ch340usb
except Exception as e:
    print("error! ", e)

from sys import version_info  

isTest = False

SERIALOBJ = None

#'@'工作模式字典
type2Pins = {1:['0','1'],2:['2','3'],3:['4','5'],4:['6','7'],5:['8','9'],6:['a','b'],7:['c','d'],8:['e','f'],9:['g','h'],10:['i','j'],11:['k','l'],12:['m','n'],13:['o','p'],14:['q','r'],15:['s','t'],16:['u','v']}

# type2Pins[1]   # ['0','1']
# type2Pins[1][0] # '0'
#获取当前python版本
def pythonVersion():
    return version_info.major


def readcom(t):
    n = t.inWaiting()
    while n<=0:
        time.sleep(0.01)
        n = t.inWaiting()
    pstr = t.read(n)
    if pythonVersion() > 2:
        print('板子日志(python3):', pstr.decode())
    else:
        print('板子日志(python2):', pstr)
    

def sendcmd(t,cmd):
    sendstr = cmd
    # if cmd[-1] != '\r':
    #     sendstr += '\r'
    print('发送数据:', sendstr)
    if pythonVersion() > 2:
        s = t.write(sendstr.encode())
    else:
        s = t.write(sendstr.encode())
    t.flush()

def sendAndread(t,v):
    if isTest:
        f = open('test.txt','a')
        f.write(v + '\n')
        f.close()
    else:
        sendcmd(t,v)
        time.sleep(0.05)
        readcom(t)


def getSerialConfig():
    f = open('config.json','r')
    dat = f.read()
    f.close()
    tmpdict = json.loads(dat)
    return tmpdict

def getPinDat(p):
    return type2Pins[p]

def readconfig():
    f= open('config.json','r')
    jstr = f.read()
    f.close()
    devdic = json.loads(jstr)
    return devdic['port']

def touch(p):
    global SERIALOBJ
    pstr = type2Pins[p][0]
    sendAndread(SERIALOBJ, pstr)

def untouch(p):
    global SERIALOBJ
    pstr = type2Pins[p][1]
    sendAndread(SERIALOBJ, pstr)


def touchpin(n):
    if n == 0:
        n = 10
    touch(n)
    time.sleep(0.03)
    untouch(n)
    # time.sleep(10)
def main():
    global SERIALOBJ
    # try:
    #     dev = ch340usb.getUSB()
    # except Exception as e:
    #     dev = None
    
    # if not dev:
    #     print('自动获取串口错误,串口不存在或者有多个ch340')
    #     print('使用config.json配置文件中的串口设置')
    #     dev = readconfig()
    # btv = 115200                        #得到波特率
    # if dev:
    #     print('port:' + dev)
    #     print('btv:' + str(btv))
    # else:
    #     print('com init erro')
    #     return  
    # 终端输入下面这一行打印串口信息
    # python -c "import serial.tools.list_ports; ports = serial.tools.list_ports.comports(); [print(f'串口: {port.device} - {port.description}') for port in ports]"
    t = serial.Serial('com5',115200,timeout=1)
    SERIALOBJ = t
    if t:
        print('串口名:', t.name)
        print('串口号:', t.port)
        print('波特率:', t.baudrate)
        print('字节大小:', t.bytesize)
        print('校验位(N-无校验，E-偶校验，O-奇校验):', t.parity)
        print('停止位:', t.stopbits)
        print('读超时设置:', t.timeout)
        print('写超时:', t.writeTimeout)
        print('软件流控:', t.xonxoff)
        print('硬件流控(rtscts):', t.rtscts)
        print('硬件流控(dsrdtr):', t.dsrdtr)
        print('字符间隔超时:', t.interCharTimeout)
        print('-'*10)
        time.sleep(1)
        # readcom(t)
        sendAndread(t, '@')
        for i in range(1):
            # 启动三角洲
            # touchpin(1)
            # time.sleep(40)

            # # 开始游戏
            # touchpin(2)
            # time.sleep(2)

            # 关闭活动叉叉
            # touchpin(3)
            # time.sleep(2)

            # 打开特勤处
            # touchpin(4)
            # time.sleep(3)

            # 领取枪
            # touchpin(5)
            # time.sleep(3)
            # touchpin(5)
            # time.sleep(3)

            # 领取子弹
            # touchpin(6)
            # time.sleep(3)
            # touchpin(6)
            # time.sleep(3)

            # 领取药品
            # touchpin(7)
            # time.sleep(3)
            # touchpin(7)
            # time.sleep(3)

            # 领取防具
            # touchpin(8)
            # time.sleep(3)
            # touchpin(8)
            # time.sleep(3)

            ## 制作枪械
            # 进入枪械工作台
            # touchpin(5)
            # time.sleep(3)
            # # 选取枪械
            # touchpin(5)
            # time.sleep(3)
            # # 一键补齐材料
            # touchpin(2)
            # time.sleep(5)
            # # 购买材料
            # touchpin(9)
            # time.sleep(5)
            # # 点击制作
            # touchpin(2)
            # time.sleep(5)
            # # 点击返回
            # touchpin(10)
            # time.sleep(2)

            # 制作子弹
            # 进入子弹工作台
            # touchpin(6)
            # time.sleep(3)
            # # 选取子弹
            # touchpin(5)
            # time.sleep(3)
            # # 一键补齐材料
            # touchpin(2)
            # time.sleep(5)
            # # 购买材料
            # touchpin(9)
            # time.sleep(5)
            # # 点击制作
            # touchpin(2)
            # time.sleep(5)
            # # 点击返回
            # touchpin(10)
            # time.sleep(2)


            # 制作药品
            # 进入子弹工作台
            # touchpin(7)
            # time.sleep(3)
            # # 选取药品
            # touchpin(5)
            # time.sleep(3)
            # # 一键补齐材料
            # touchpin(2)
            # time.sleep(5)
            # # 购买材料
            # touchpin(9)
            # time.sleep(5)
            # # 点击制作
            # touchpin(2)
            # time.sleep(5)
            # # 点击返回
            # touchpin(10)
            # time.sleep(2)


            # 制作盔甲
            # 进入子弹工作台
            # touchpin(8)
            # time.sleep(3)
            # # 选取盔甲
            # touchpin(5)
            # time.sleep(3)
            # # 一键补齐材料
            # touchpin(2)
            # time.sleep(5)
            # # 购买材料
            # touchpin(9)
            # time.sleep(5)
            # # 点击制作
            # touchpin(2)
            # time.sleep(5)
            # # 点击返回
            # touchpin(10)
            # time.sleep(2)



            

          

            

        t.close()
    else:
        print('串口不存在')



if __name__ == '__main__':
    args = sys.argv
    fpth = ''
    if len(args) == 2 :
        pass
    else:
        main()