import machine
import time

SCLPIN = machine.Pin(4, machine.Pin.OUT)
SDAPIN = machine.Pin(5, machine.Pin.OUT)

SCLPIN.value(1)
SDAPIN.value(1)

#主板向从板发送数据,一次只发一个字节
#发送数据格式:gpio4作为时钟,gpio5作为数据线
#启始:gpio4输出高电平,gpio5从高向低变化
#结速:gpio4输出高电平,gpio5从低向高变化
#发送一个位,gpio4上升沿时,从机可读取gpio5的电平
#主机准备数据,gpio4为低电平时,设置gpio5的电平,为从机读取数据做准备
def startFlog():
    time.sleep_ms(1)
    SCLPIN.value(1)
    time.sleep_ms(1)
    SDAPIN.value(1)
    time.sleep_ms(1)
    SDAPIN.value(0)
    time.sleep_ms(1)
    SCLPIN.value(0)
    time.sleep_ms(1)
def endFlog():
    SDAPIN.value(0)
    time.sleep_ms(1)
    SCLPIN.value(1)
    time.sleep_ms(1)
    SDAPIN.value(1)
    time.sleep_ms(1)

def sendByte(dat):
    for i in range(8):
        if dat & 0x80:
            SDAPIN.value(1)
        else:
            SDAPIN.value(0)
        dat <<= 1
        time.sleep_ms(1)
        SCLPIN.value(1)
        time.sleep_ms(1)
        SCLPIN.value(0)
        time.sleep_ms(1)
def sendBytes(datas):
    print('send datas:',datas)
    startFlog()
    print('send len',len(datas))
    sendByte(len(datas))
    for dat in datas:
        sendByte(dat)
    endFlog()
