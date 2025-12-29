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
if not isExists('wifi.json'):
    import webconfig
    webconfig.WebConfig().run() #开始web配网,配网成功后自动保存wifi.json,然后重新启动
else:
    with open('wifi.json', 'r') as f:
        config = ujson.load(f)
        SSID = config.get('ssid')
        PASSWORD = config.get('password')
        print('wifi config:',SSID,PASSWORD)

from machine import RTC
import time
import ntptime



#这个工具,当设备连上网络后,可以获取网络时间,并设置到RTC
rtc = RTC() 
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

    #获取北京时间
    def getBjTimeStamp(self):
        # 获取当前时间([年, 月, 日, 时, 分, 秒, 毫秒, 微秒])，数组形式
        utc_now = rtc.datetime()
        # 转成时间戳
        utc_time = time.mktime((utc_now[0], utc_now[1], utc_now[2], utc_now[4], utc_now[5], utc_now[6], 0, 0))
        return utc_time + 8 * 3600

    #获取时间戳-格式 2025-02-18T22:00:00
    def isNowAfterTime(self, time_str):
        
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

        print("time_tag:",time_str)
        print('time_now:',self.getBjTime())
        
        return time.mktime(time_tuple) < self.getBjTimeStamp()

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

def test():
    socketUtil.connect_wifi(SSID,PASSWORD)  #让板子连接wifi
    tobj = LibTime()
    tobj.syncRemote() #同步网络时间,同时打印北京时间
    dftime = tobj.getTime() #获取默认UTC时间
    print("dftime:",dftime)
    bjtime = tobj.getBjTime() #获取北京时间
    print("bjtime:",bjtime)
    #这样获取到时间后,就可以结合出厂程序里的控制点击头的逻辑来用程序控制和时间有关的定时点击操作了
if __name__ == '__main__':
    test()