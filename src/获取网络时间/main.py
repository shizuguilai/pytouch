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


import time
import rtcUtil #需要20260121版本以上固件

## 清除wifi配置,下次上电后,需要重新配置wifi
def cleanWifiConfig():
    os.remove('wifi.json')
    time.sleep_ms(100)
    machine.reset()

def test():
    socketUtil.connect_wifi(SSID,PASSWORD)  #让板子连接wifi
    tobj = rtcUtil.RTCUtil()
    tobj.syncRemote() #同步网络时间,同时打印北京时间
    dftime = tobj.getTime() #获取默认UTC时间
    print("dftime:",dftime)
    bjtime = tobj.getBjTime() #获取北京时间
    print("bjtime:",bjtime)
    #这样获取到时间后,就可以结合出厂程序里的控制点击头的逻辑来用程序控制和时间有关的定时点击操作了
if __name__ == '__main__':
    test()