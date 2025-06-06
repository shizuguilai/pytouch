#!/usr/bin/python
# -*- coding: utf-8 -*-
#创建SocketServerTCP服务器：

from glob import glob0
import SocketServer
# from SocketServer import StreamRequestHandler

import os
import socket
import json

myname = socket.getfqdn(socket.gethostname())
myaddr = socket.gethostbyname(myname)

print('selfip:%s'%(myaddr))
host = str(myaddr)


port = 8099
addr = (host,port)

clients = {}

PCSOCKET = None

#请求设备数
#接口:
#1:发送点击指令,点击指令为1个十六进制数的hex编码,指令格式
#{"cmd":1,"ctype":1,"dat":"ff","mac":"mac地址"} 
#其中cmd为指令类型(1为电脑端控制数据,0为点击器端控制结果返回数据),ctype为客户端类型(1为电脑控制端,0为点击器端),dat为转送动作指令,mid为设备mac地址
#0:点击器返回操作结果指令,返回数据格式如下
#{"cmd":0,"ctype":0,"dat":"ff","mac":"mac地址"}
#其中dat为接收到的指令原值返回,err表示是否点击器连接出错0为成功,1为点击器出错,mid为点击器mac地址

def getTouchData(s,dat,mac):
    global clients
    print('touch:',dat,mac)
    if mac in clients:
        clients[mac]['dat'] = dat
    else:
        clients[mac] = {'socket':s,'dat':dat}

def getPCData(s,dat,mac):
    global clients
    print('PC:',dat,mac)
    if mac in clients:
        clients[mac]['socket'].send(dat)
    else:
        outdic = {'cmd':0,'erro':1} #点击器不存在
        jstr = json.dumps(outdic)
        s.send(jstr.encode())
def getDataFromClient(s,dat):
    global PCSOCKET
    datdic = json.loads(dat)
    print(datdic)
    dat = {}
    if datdic['ctype'] == 0: #点击器指令
        getTouchData(s,datdic['dat'],datdic['mac'])
        if PCSOCKET:
            datdic['erro'] = 0
            jstr = json.dumps(datdic)
            PCSOCKET.send(jstr.encode())
    elif datdic['ctype'] == 1: #控制端指令
        getPCData(s,datdic['dat'],datdic['mac'])


class Servers(SocketServer.StreamRequestHandler):
    def handle(self):
        print('got connection from ',self.client_address)
        while True:
            try:  
                data = self.request.recv(1024)
                getDataFromClient(self.request,data)
            except EOFError:  
                print('接收客户端错误，客户端已断开连接,错误码:')
                print(EOFError )
                break
            except:  
                print('接收客户端错误，客户端已断开连接')
                break
            if not data: 
                break
            print('data len:%d'%(len(data)))
            print("RECV from ", self.client_address)
            print(data)
            # self.request.send('aaa')

def startServer():
    server = SocketServer.ThreadingTCPServer(addr,Servers,bind_and_activate = False)
    server.allow_reuse_address = True   #设置IP地址和端口可以不使用客户端连接等待，并手动绑定服务器地址和端口，手动激活服务器,要不然每一次重启服务器都会出现端口占用的问题
    server.server_bind()
    server.server_activate()
    print('server started:')
    print(addr)
    server.serve_forever()
    
if __name__ == '__main__':
    startServer()