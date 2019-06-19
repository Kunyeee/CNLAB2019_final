#author:sean
# -*- coding: UTF-8 -*-

from scapy.config import conf
conf.ipv6_enabled = False
from scapy.all import *
import random
import sys
import socket, logging
import select, errno
import time
import os
import threading
from CP_agent import *
from argparse import ArgumentParser

logger = logging.getLogger("server")
STDIN = sys.stdin.fileno()
agent_server = ('10.0.0.1', 6666)
def InitLog():
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler("server.log")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)


if __name__ == "__main__":
    #if os.fork() == 0:
    #    os.execl('/usr/bin/python', 'python', './recver.py')
    parser = ArgumentParser()
    parser.add_argument("-ip", type=str, required=True, dest= "ip", help= "ip") 
    parser.add_argument("-bp", default="6666", dest= "bp", help= "port connected to client") 
    parser.add_argument("-cp", default="5555", dest= "cp", help= "port connected to agent") 
    
    args =parser.parse_args()
    bp = int(args.bp)
    cp = int(args.cp)

    #my_ip = os.popen('ifconfig').read().split('inet addr:')[1].split(' ')[0]
    my_ip = args.ip
    idx = my_ip.split('.')[-1].rjust(3, '0')
    outdir = './client_puzzle/'

    T = CP_agent(my_ip, idx, outdir, True)
    #thread.start_new_thread(recver, (my_ip, idx, A, True, ))

 
    InitLog()
    #register
    
    payload = T.get_puzzle(agent_server[0] + ':' + str(agent_server[1]))
    print "payload =", payload
    packet = IP(dst="10.0.0.1", src=my_ip)/TCP(sport=cp, dport=6666, options = [(254, payload)])
    send(packet)
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    s.bind((my_ip, cp))
    s.connect(agent_server)
    s.send('register')
    print s.recv(32)
    s.send('open port:6666, 20')
    print s.recv(32)

    try:
        # 創建TCPsocket 作為監聽 socket
        listen_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    except socket.error as  msg:
        logger.error("create socket failed")

    try:
        # 設置 SO_REUSEADDR 選項
        listen_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except socket.error as  msg:
        logger.error("setsocketopt SO_REUSEADDR failed")

    try:
        # 進行 bind -- 此處未指定 ip 地址，即 bind 了全部網卡 ip 上
        listen_fd.bind((my_ip, bp))
    except socket.error as  msg:
        logger.error("bind failed")

    try:
        # 設置 listen 的 backlog 數
        listen_fd.listen(10)
    except socket.error as  msg:
        logger.error(msg)

    try:
        # 創建 epoll 句柄
        epoll_fd = select.epoll()
        # 向 epoll 句柄中註冊 監聽 socket 的 可讀 事件
        epoll_fd.register(listen_fd.fileno(), select.EPOLLIN)
        # register stdin
        #epoll_fd.register(STDIN, select.EPOLLIN)
    except select.error as  msg:
        logger.error(msg)

    connections = {}
    addresses = {}
    datalist = {}
    while True:
        # epoll 進行 fd 掃描的地方 -- 未指定超時時間則為阻塞等待
        epoll_list = epoll_fd.poll(1)
        '''
        '''

        for fd, events in epoll_list:
            # 若為監聽 fd 被激活
            if fd == listen_fd.fileno():
                # 進行 accept -- 獲得連接上來 client 的 ip 和 port，以及 socket 句柄
                conn, addr = listen_fd.accept()
                logger.debug("accept connection from %s, %d, fd = %d" % (addr[0], addr[1], conn.fileno()))
                # 將連接 socket 設置為 非阻塞
                conn.setblocking(0)
                # 向 epoll 句柄中註冊 連接 socket 的 可讀 事件
                epoll_fd.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)
                # 將 conn 和 addr 信息分別保存起來
                connections[conn.fileno()] = conn
                addresses[conn.fileno()] = addr
            elif fd == STDIN and select.EPOLLIN & events:
                data = sys.stdin.readline().strip()
                print "data =", data
                if data == 'exit':
                    s.send('close port: 6666')
                    print s.recv(32)
                    s.send('exit')
                    #print s.recv(20)
                    s.close()
                    exit(0)
                else:
                    s.send(data)
                    print s.recv(32)
            elif select.EPOLLIN & events:
                # 有 可讀 事件激活
                datas = ''
                while True:
                    try:
                        # 從激活 fd 上 recv 10 字節數據
                        data = connections[fd].recv(32)
                        # 若當前沒有接收到數據，並且之前的累計數據也沒有
                        #if not data and not datas:
                        if not data:
                            # 從 epoll 句柄中移除該 連接 fd
                            epoll_fd.unregister(fd)
                            # server 側主動關閉該 連接 fd
                            connections[fd].close()
                            logger.debug("%s, %d closed" % (addresses[fd][0], addresses[fd][1]))
                            t = 'df,{},{},{}'.format(addresses[fd][0], addresses[fd][1], 6666)
                            print "send to bastion:", t
                            s.send(t)
                            s.recv(32)
                            break
                        else:
                            # 將接收到的數據拼接保存在 datas 中
                            datas += data
                    except socket.error as  msg:
                        # 在 非阻塞 socket 上進行 recv 需要處理 讀穿 的情況
                        # 這裏實際上是利用 讀穿 出 異常 的方式跳到這裏進行後續處理
                        if msg.errno == errno.EAGAIN:
                            logger.debug("%s receive %s" % (fd, datas))
                            # 將已接收數據保存起來
                            datalist[fd] = datas
                            # 更新 epoll 句柄中連接d 註冊事件為 可寫
                            epoll_fd.modify(fd, select.EPOLLET | select.EPOLLOUT)
                            break
                        else:
                            # 出錯處理
                            epoll_fd.unregister(fd)
                            connections[fd].close()
                            logger.error(msg)
                            t = 'df,{},{},{}'.format(addresses[fd][0], addresses[fd][1], 6666)
                            print "send to bastion:", t
                            s.send(t)
                            s.recv(32)
                            break
            elif select.EPOLLHUP & events:
                # 有 HUP 事件激活
                epoll_fd.unregister(fd)
                connections[fd].close()
                logger.debug("%s, %d closed" % (addresses[fd][0], addresses[fd][1]))
            elif select.EPOLLOUT & events:
                # 有 可寫 事件激活
                sendLen = 0
                # 通過 while 循環確保將 buf 中的數據全部發送出去
                while True:
                    # 將之前收到的數據發回 client -- 通過 sendLen 來控制發送位置
                    sendLen += connections[fd].send(datalist[fd][sendLen:])
                    # 在全部發送完畢後退出 while 循環
                    if sendLen == len(datalist[fd]):
                        break
                # 更新 epoll 句柄中連接 fd 註冊事件為 可讀
                epoll_fd.modify(fd, select.EPOLLIN | select.EPOLLET)
            else:
                # 其他 epoll 事件不進行處理
                continue

