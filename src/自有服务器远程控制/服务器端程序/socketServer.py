#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 创建SocketServer TCP服务器：

import socketserver
import os
import socket
import json


host = "0.0.0.0"
port = 9527
addr = (host, port)

clients = {}
PCSOCKET = None

# 请求设备数
# 接口:
# 1:发送点击指令,点击指令为1个十六进制数的hex编码,指令格式
# {"cmd":1,"ctype":1,"dat":"ff","mac":"mac地址"} 
# 0:点击器返回操作结果指令,返回数据格式如下
# {"cmd":0,"ctype":0,"dat":"ff","mac":"mac地址"}


def getTouchData(s, dat, mac):
    global clients
    print('touch:', dat, mac)
    if mac in clients:
        clients[mac]['dat'] = dat
    else:
        clients[mac] = {'socket': s, 'dat': dat}


def getPCData(s, dat, mac):
    global clients
    print('PC:', dat, mac)
    if mac in clients:
        clients[mac]['socket'].send(dat.encode())
    else:
        outdic = {'cmd': 0, 'erro': 1}  # 点击器不存在
        jstr = json.dumps(outdic)
        s.send(jstr.encode())


def getDataFromClient(s, dat):
    global PCSOCKET
    try:
        dat = dat.decode()
        datdic = json.loads(dat)
    except Exception as e:
        print('JSON decode error:', e)
        return

    print(datdic)

    if datdic['ctype'] == 0:  # 点击器指令
        getTouchData(s, datdic['dat'], datdic['mac'])
        if PCSOCKET:
            datdic['erro'] = 0
            jstr = json.dumps(datdic)
            PCSOCKET.send(jstr.encode())
    elif datdic['ctype'] == 1:  # 控制端指令
        getPCData(s, datdic['dat'], datdic['mac'])
        PCSOCKET = s  # 注册PC控制端


class Servers(socketserver.StreamRequestHandler):
    def handle(self):
        print('got connection from', self.client_address)
        while True:
            try:
                data = self.request.recv(1024)
                if not data:
                    break
                print('data len:', len(data))
                print("RECV from", self.client_address)
                print(data)

                getDataFromClient(self.request, data)

            except (EOFError, ConnectionResetError) as e:
                print('接收客户端错误，客户端已断开连接:', e)
                break
            except Exception as e:
                print('未知错误:', e)
                break


def startServer():
    server = socketserver.ThreadingTCPServer(addr, Servers, bind_and_activate=False)
    server.allow_reuse_address = True
    server.server_bind()
    server.server_activate()
    print('server started:')
    print(addr)
    server.serve_forever()


if __name__ == '__main__':
    startServer()
