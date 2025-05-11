## 产品介绍

产品使用micropython固件,可以直接开发板上使用python编程,支持大多数python库.板子默认固件中代有相关点击头驱动的py库,默认原厂main.py文件为按键按下J1到J16这十六个点击头以次点击.最单的使用方式就是修改这个main.py文件.

板子默认上传py文件的工具只支持windows系统.如果你要在mac os或者linux系统下使用,可以使用ampy这个命令行工具进行上传.具体ampy如何使用,你可以问deepseek或者在网上搜索使用方法,ampy可以使用python包管理工具pip进行安装.

硬件购买地址:
https://item.taobao.com/item.htm?ft=t&id=906190081877

B站:
https://space.bilibili.com/166287840

微信:
woodmage

## 项目目录结构
```
|---src---|--板子初始程序(这里何存板子出厂main.py程序文件)
|         |
|         |--跑密码程序(这里放有一个跑6位密码的程序)
|
|---固件(这里放有micropython固件)
|
|---上传工具(这里放有windwos系统下给板子上传py文件的工具)
|
|---python安装包(这里只放了python3.8的安装包,因为win7只支持到python3.8,如果你是更新的win系统,可以自行下载安装更高版本的安装包)
|
|---LICENSE(可以不用关心)
|
|---readme.md(当前查看的说明文件)
```

## 电脑端python开发环境搭建

我们这里使用当前最流行的开源IED开发工具vs code

vs code下载地址:

官方下载地址:
https://code.visualstudio.com/

### API介绍

micropython固件编译相关库:

点击头驱动库:tDriver

使用方法
``` python
#导入tDriver库重命名为t,可以不用重命名
import tDriver as t
updateData():
#把驱动中缓存当前状态更新到点击头上
set16Pins(states):
#设置当前内部16个点击器的工作状态,是按下还是抬起
clearAllTouch():
#让所有点击头为抬起状态
setAllTouch():
#让所有点击头为按下状态
touchPin(pNumber):
#让pNumber这个点击头按下
unTouchPin(pNumber):
#让pNumber这个点击头抬起
move(pins,dt = 5):
#滑动动作,让pins这个数组列表中的点击头依次按下来模拟滑动动作,dt为滑动按键状态改变间隔时间,默认为5毫秒
#比如使用J1,J2,J3,J4为作为滑动头,那个pins就是[1,2,3,4]

#实始化一个点击器控制实例对象
tobj = t.TouchObj()
#然后直接使用对象方法调用上边对应的函数即可,例如滑动动作
tobj.move([1,2,3,4])
```

串口输入接收数据库:uartUtil
``` python
#导入串口接收数据库:
import uartUtil
#读取串口的数据
reciveDat(isRead = False,timeout = 0.005):
#这个函数用来读取串口发送给板子的数据,
#isRead:是否按字节方式读取任意接收到的字节数据,当这个值为True时,直接读取字节流,这个值为False时数据是按行读取,只有接收到\n换行符时才会返回数据
#timeout:读数据超时时间,如果超时没有数据就返回None结果

#使用例子如下
data1 = uartUtil.reciveDat()
#这里的data1是一个以\n结束的字符串
data2 = uartUtil.reciveDat(True)
#这里读取到是的第一个字节流,只要有数据就会返回,不看是否有\n这样的换行符

#另外这个uarUtil中还有几个别的功能函数定义,
initUART2(tx_pin = 26,rx_pin = 25,btv = 9600):
#这是初始化创建另一个uart串口的接口
writeUART2(dat):
#这创建的新串口发送数据
readUART2():
#从新创建的串口读取字节流数据

#关于引脚外部中断函数也是在这个库里
addExtIntPin(callfunc,ex_pin = 33,trigst = 0)
#其中
#callfunc:外部引脚中断后的回调函数
#ex_pin:用于作外部硬件中断的引脚编号
#trigst:外部中断触发方式,0:下降沿触发中断函数,1:上升沿触发中断函数,其他状态为状态改变触发
```
巴法云相关处理逻辑库:BFUtil
``` python
start(uid,cFunc):
#启动巴法云,并尝试连接巴法云服务器
#uid:巴法云给的用户ID
#cfunc:接受服务器数据回调函数,当收到服务器数据时会调用这个回调函数
stop():
#停止巴法云服务器,并断开连接
```

目前这个板加了这三个功能,如果需要别的功能可以联系我

micropython相关教程:
http://micropython.com.cn/en/latet/esp8266/quickref.html


我的网盘下载地址:
链接: https://pan.baidu.com/s/1NR2oT3o-vGjov8Ztjhno4Q?pwd=1234 提取码: 1234