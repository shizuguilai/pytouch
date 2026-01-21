#power by fengmm521.taobao.com
#wechat:woodmage
import machine
import ujson
import os
import socketUtil

#文件是否存在
def isExists(pth):
    try:
        f = open(pth,'rb')
        f.close()
        return True
    except Exception:
        return False

SSID = None
PASSWORD = None

if SSID is None or PASSWORD is None:
    if not isExists('wifi.json'):
        import webconfig
        webconfig.WebConfig().run() #开始web配网,配网成功后自动保存wifi.json,然后重新启动
    else:
        with open('wifi.json', 'r') as f:
            config = ujson.load(f)
            SSID = config.get('ssid')
            PASSWORD = config.get('password')
            print('wifi config:',SSID,PASSWORD)

import machine
import time
import ntptime
import tDriver as t


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
    time.sleep_ms(60)   #按下时间为60毫秒,这个时间可以根据需要修改,建议30~100之间
    unTouchPin(pNumber) #对应点击头抬起
    time.sleep_ms(60)   #抬起后再等60毫秒

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


isNoDaKa = False

def DaKa(tim = None):
    # 在这里写打卡逻辑
    if isNoDaKa:
        print("今天不用打卡")
        return
    print("开始打卡")
    

#这个工具,当设备连上网络后,可以获取网络时间,并设置到RTC
rtc = machine.RTC() 
#lib_time
class LibTime:
    # def __init__(self): 
    #远程同步时间
    def syncRemote(self, trycount=5):
        while trycount > 0:
            try:
                # 自动同步时间
                ntptime.settime()  #从服务器远程同步时间
                print('now_time:',self.getBjTime())
                break
            except:
                pass
            finally:
                trycount -= 1
    #获取默认时间
    def getTime(self):
        utc_now = rtc.datetime()
        # 格式化输出时间
        formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            utc_now[0],  # 年
            utc_now[1],  # 月
            utc_now[2],  # 日
            utc_now[4],  # 时
            utc_now[5],  # 分
            utc_now[6]   # 秒
        )
        return formatted_time

    #获取北京时间
    def getBjTime(self):
        # 获取当前时间([年, 月, 日, 时, 分, 秒, 毫秒, 微秒])，数组形式
        utc_now = rtc.datetime()
        # 转成时间戳
        utc_time = time.mktime((utc_now[0], utc_now[1], utc_now[2], utc_now[4], utc_now[5], utc_now[6], 0, 0))
        bj_time = utc_time + 8 * 3600
        # 转成数组
        bj_datetime = time.localtime(bj_time)
        formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            bj_datetime[0],  # 年
            bj_datetime[1],  # 月
            bj_datetime[2],  # 日
            bj_datetime[3],  # 时
            bj_datetime[4],  # 分
            bj_datetime[5]   # 秒
        )
        return formatted_time
    #获取北京时间,返回数组形式[年,月,日,时,分,秒,星期几],星期几（数字，0-6，0代表星期一，6代表星期日）
    def getBjTimeList(self):
        # 获取当前时间([年, 月, 日, 时, 分, 秒, 毫秒, 微秒])，数组形式
        utc_now = rtc.datetime()
        # 转成时间戳
        utc_time = time.mktime((utc_now[0], utc_now[1], utc_now[2], utc_now[4], utc_now[5], utc_now[6], 0, 0))
        bj_time = utc_time + 8 * 3600
        # 转成数组
        bj_datetime = time.localtime(bj_time)
        #年,月,日,时,分,秒,星期
        return bj_datetime[0], bj_datetime[1], bj_datetime[2], bj_datetime[3], bj_datetime[4], bj_datetime[5], bj_datetime[6]
    #获取北京时间戳
    def getBjTimeStamp(self):
        # 获取当前时间([年, 月, 日, 时, 分, 秒, 毫秒, 微秒])，数组形式
        utc_now = rtc.datetime()
        # 转成时间戳
        utc_time = time.mktime((utc_now[0], utc_now[1], utc_now[2], utc_now[4], utc_now[5], utc_now[6], 0, 0))
        return utc_time + 8 * 3600
    #获取时间戳-格式 2025-02-18T22:00:00
    def strTimeToStamp(self,time_str,isBJ = True):
        tmps = time_str.split("T")
        ytmp = tmps[0].split("-")
        year = int(ytmp[0])
        month = int(ytmp[1])
        day = int(ytmp[2])
        htmps = tmps[1].split(":")
        if len(htmps) == 2:
            hour = int(htmps[0])
            minute = int(htmps[1])
            second = 0
        elif len(htmps) == 3:
            hour = int(htmps[0])
            minute = int(htmps[1])
            second = int(htmps[2])
        else:
            return False
        # 构造时间元组并转换 
        time_tuple = (year, month, day, hour, minute, second, 0, 0)
        outtime = time.mktime(time_tuple)
        if isBJ:
            outtime += 8 * 3600
        return outtime
    #获取时间戳-格式 2025-02-18T22:00:00
    def isNowAfterTime(self, time_str,isBJ = True):
        utctime = self.strTimeToStamp(time_str,isBJ)
        return utctime < self.getBjTimeStamp()

    # 当前线程睡眠
    def sleep(self, s):
        time.sleep(s)

    # 当前线程睡眠
    def sleep_ms(self, ms):
        time.sleep_ms(ms)

## 清除wifi配置,下次上电后,需要重新配置wifi
def cleanWifiConfig():
    os.remove('wifi.json')
    time.sleep_ms(100)
    machine.reset()

def runDAKA():
    print("打卡时间到,开始打卡")
    touchOncePin(1)      #J1点击一次,打开app
    time.sleep(10)       #延时10秒
    touchOncePin(2)      #J2点击一次,打卡
    time.sleep(10)       #延时10秒
    touchOncePin(3)      #J3点击一次,返回桌面
    time.sleep(5)       #延时5秒

def main():
    wlan = socketUtil.connect_wifi(SSID,PASSWORD)  #让板子连接wifi
    print("\nWiFi connected:", wlan.ifconfig())
    timobj = LibTime()
    timobj.syncRemote() #同步网络时间,同时打印北京时间
    #打卡时间
    dklist = ["08:00:00","12:00:00","18:00:00"]
    dkdown = -1 #打卡最后一次打卡下标
    weekdays = [0,1,2,3,4,5,6] #要打卡的星期,(数字，0-6，0代表星期一，6代表星期日),默认为全部
    randomtime = 5*60    #随机时间,提前5分钟内打卡,单位秒
    wificount = 3600     #wifi时间每小时检查校准一次
    while True:
        year,month,day,hour,minute,second,week = timobj.getBjTimeList()
        if week in weekdays:
            for i,dktime in enumerate(dklist):
                if dkdown != i:
                    dts = dktime.split(":")
                    dkh = int(dts[0])   #打卡小时
                    dkm = int(dts[1])   #打卡分钟
                    dks = int(dts[2])   #打卡秒
                    dt = randint(0,randomtime)             #打卡在要求的时间提前随机5分钟内
                    nowtime = hour*3600+minute*60+second
                    dktime = dkh*3600+dkm*60+dks - dt
                    if dktime <= nowtime:
                        runDAKA()
                        dkdown = i #当前时间设置为已经打卡了
        time.sleep(1) #每秒钟检查一次
        wificount -= 1  #每小时从服务器获取一次时间
        if wificount <= 0:
            wificount = 3600
            if wlan.isconnected(): #wifi连接是否连接
                timobj.syncRemote() #同步网络时间,同时打印北京时间
            else:
                time.sleep_ms(100) #等待100毫秒
                machine.reset() #wifi连接断开,重启设备

    #这样获取到时间后,就可以结合出厂程序里的控制点击头的逻辑来用程序控制和时间有关的定时点击操作了
if __name__ == '__main__':
    main()