
import os
import json
def isHeaveFile(fpth):
    try:
        f = open(fpth,'r')
        f.close()
        return True
    except Exception as e:
        return False

espid = None
espidPTH = 'config.txt'
cfgDict = {'id':"0",'ssid':'0','pwd':'0','sAddr':'0','sPort':0}

reciveBuff = ''

def saveESPID(tid):
    cfgDict['id'] = tid
    jstr = json.dumps(cfgDict)
    with open(espidPTH,'w') as f:
        f.write(jstr)

def readConfig():
    global cfgDict
    if isHeaveFile(espidPTH):
        with open(espidPTH,'r') as f:
            jstr = f.read()
            cfgDict = json.loads(jstr)
    else:
        print('no config.txt file')

def saveWIFI(pid,ppwd):
    cfgDict['ssid'] = pid
    cfgDict['pwd'] = ppwd
    jstr = json.dumps(cfgDict)
    with open(espidPTH,'w') as f:
        f.write(jstr)

def saveServer(ser,port):
    cfgDict['sAddr'] = ser
    cfgDict['sPort'] = port
    jstr = json.dumps(cfgDict)
    with open(espidPTH,'w') as f:
        f.write(jstr)

#当是串口是<>符号时,就是一次设置所有参数
#<espid,ssid,pwd,sAddr,sPort>
def saveAllConfig(dstr):
    tmps = dstr.split(',')
    cfgDict['ssid'] = tmps[1]
    cfgDict['pwd'] = tmps[2]
    cfgDict['sAddr'] = tmps[3]
    cfgDict['sPort'] = tmps[4]
    saveESPID(tmps[0])

def checkConfig():
    notsets = []
    if cfgDict['id'] != '0':
        print('device ID:%s\n'%(cfgDict['id']))
    else:
        notsets.append(2)
    if cfgDict['sAddr'] != '0':
        print('server,addr:%s,port:%s\n'%(cfgDict['sAddr'],cfgDict['sPort']))
    else:
        notsets.append(3)
    if cfgDict['ssid'] != '0':
        print('wifi:ssid:%s,pwd:%s\n'%(cfgDict['ssid'],cfgDict['pwd']))
    else:
        notsets.append(1)
    for i,v in enumerate(notsets):
        if v == 1:
            print('please set wifi with:{ssid,password}\n')
        if v == 2:
            print('please set deviceID with:[id]\n')
        if v == 3:
            print('please set server with:(serverAddr,port)\n')
    if len(notsets) == 0:
        print('all config is set\n')
        return True
    else:
        print('some config is not set\n')
        return False

reciveMode = 0

def reciveOneByte(dat):
    global reciveMode,reciveBuff
    try:
        dat = dat.decode()
        print(dat)
        if dat == '{':  #表示使用串口配网的开始标识
            reciveMode = 1
        elif dat == '}': #配网wifi参数设置完成
            reciveMode = 0
            tmps = reciveBuff.split(',')
            saveWIFI(tmps[0],tmps[1])
            reciveBuff = ''
        elif dat == '<': #表示使用串口同时控制所有点击头状态数据开始标识
            reciveMode = 2
        elif dat == '>': #表示使用串口同时控制所有点击头状态数据结束标识
            reciveMode = 0
            saveAllConfig(reciveBuff)
            reciveBuff = ''
        elif dat == '[]': #表示使用串口巴法云设置开始标识
            reciveMode = 3
        elif dat == ']': #表示使用串口巴法云设置结束标识
            reciveMode = 0
            saveESPID(reciveBuff)
            reciveBuff = ''
        elif dat == '(':
            reciveMode = 4
        elif dat == ')':  #保存服务器地址和端口
            reciveMode = 0
            tmps = reciveBuff.split(',')
            saveServer(tmps[0],tmps[1])
            reciveBuff = ''
            return
        elif reciveMode != 0: #接收wifi参数
            reciveBuff += dat
        else:
            print(dat)
    except:
        print('recive uart data error')