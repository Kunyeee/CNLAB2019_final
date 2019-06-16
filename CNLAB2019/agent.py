#author:sean
# -*- coding: UTF-8 -*-

from scapy.config import conf
conf.ipv6_enabled = False
from scapy.all import *
import socket, logging
import select, errno
import random
import sys, os, subprocess
import time

logger = logging.getLogger("agent")
server = {}
server_id = {}
Max_server_num = 9
fd2addr = {}
'''
def my_send(data, ip):
    act, param = check(data, ip)
    print "recv data:", data, "action:", act
    if act < 0:
        data = "Wrong format"
        print data
    elif act > 0:
        packet = IP(dst="10.0.0.2")/TCP(options = [(254, param)])
        send(packet)
    return data
'''
def release_server(hostname):
    for i in range(1, 1 + Max_server_num):
        if server_id[i] == hostname:
            server_id[i] = None
            return True
    return False
def get_server_id(hostname):
    for i in range(1, 1 + Max_server_num):
        if server_id[i] == None:
            server_id[i] = hostname
            return i
    return -1
def server_exit(addr):
    check('exit', addr[0])
    param = 'df,' + addr[0] + ',' + str(addr[1]) + ',10.0.0.1,6666'
    packet = IP(dst="10.0.0.2")/TCP(sport=9999, dport=9999, options = [(254, param)])
    send(packet)
def check(data, ip):
    fail = (-1, "Wrong format")
    Nop = (0, None)
    t = data.find('register')
    if data == 'register':
        if ip in server:
            return fail
        server[ip] = set()
        return Nop
    if data.startswith('open port:'):
        try:
            s = data[10:].split(',')
            a = int(s[0])
            b = int(s[1])
        except:
            return fail
        if len(s) == 2 and ip in server:
            idx = get_server_id((ip, a))
            if idx < 0:
                return (-1, "Server queue is full")
            server[ip].add(a)
            return 1, 'o,' + ip + ',' + data[10:] + ',' + str(idx)
        else:
            return fail
    if data.startswith('close port:'):
        try:
            a = int(data[11:])
            d = server[ip]
        except:
            return fail
        if a in d and release_server((ip, a)):
            server[ip].remove(a)
            return 2, 'c,' + ip + ',' + data[11:]
        else:
            return fail
    if data == 'exit':
        try:
            d = server[ip]
        except:
            return fail
        for port in d:
            packet = IP(dst="10.0.0.2")/TCP(sport=9999, dport=9999, options = [(254, 'c,' + ip + ',' + str(port))])
            send(packet)
            #my_send('close port: ' + str(port), ip)
        del server[ip]
        return 4, None
    if data.startswith('df,'):
        try:
            s = data.split(',')
            a = int(s[2])
            b = int(s[3])
            d = server[ip]
        except:
            return fail
        if len(s) == 4 and b in d:
            return 3, 'df,' + s[1] + ',' + s[2] + ',' + ip + ',' + s[3]
        else:
            return fail
    return fail

def InitLog():
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler("agent.log")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)


if __name__ == "__main__":
    InitLog()
    for i in range(1, 1 + Max_server_num):
        server_id[i] = None
    if os.fork() == 0:
        outdir = './client_puzzle/'
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('10.0.0.1', 8888))
        #subprocess.call(['python', outdir + 'generate_server_key.py', '-i', outdir, '-o', outdir])
        while True:
            #call function
            subprocess.call(['python', outdir + 'generate_puzzle.py', '-i', outdir, '-o', outdir, '-s', '1', '-l', '5'])
            f = open(outdir + 'puzzle.json')
            cnt = 0
            while True:
                data = f.read(1024-6)
                if not data:
                    #packet = Ether(dst="ff:ff:ff:ff:ff:ff")/IP()/UDP(sport=8888, dport=8888)/(str(cnt) + '$')
                    #packet = IP(dst='10.0.0.0/30')/UDP(sport=8888, dport=8888)/(str(cnt) + '$')
                    packet = Ether()/IP(dst='10.255.255.255')/UDP(sport=8888, dport=8888)/(str(cnt) + '$')
                    print "send", cnt
                    sendp(packet)
                    break
                #packet = Ether(dst="ff:ff:ff:ff:ff:ff")/IP()/UDP(sport=8888, dport=8888)/(str(cnt).rjust(5,'0') + '$' + data)
                packet = Ether()/IP(dst='10.255.255.255')/UDP(sport=8888, dport=8888)/(str(cnt).rjust(5,'0') + '$' + data)
                sendp(packet)
                cnt += 1
                print "send"
            time.sleep(60)

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
        listen_fd.bind(('10.0.0.1', 6666))
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
    except select.error as  msg:
        logger.error(msg)

    connections = {}
    addresses = {}
    datalist = {}
    while True:
        # epoll 進行 fd 掃描的地方 -- 未指定超時時間則為阻塞等待
        epoll_list = epoll_fd.poll(1)
        for fd, events in epoll_list:
            # 若為監聽 fd 被激活
            if fd == listen_fd.fileno():
                # 進行 accept -- 獲得連接上來 client 的 ip 和 port，以及 socket 句柄
                conn, addr = listen_fd.accept()
                logger.debug("accept connection from %s, %d, fd = %d" % (addr[0], addr[1], conn.fileno()))
                fd2addr[conn.fileno()] = addr
                # 將連接 socket 設置為 非阻塞
                conn.setblocking(0)
                # 向 epoll 句柄中註冊 連接 socket 的 可讀 事件
                epoll_fd.register(conn.fileno(), select.EPOLLIN | select.EPOLLET)
                # 將 conn 和 addr 信息分別保存起來
                connections[conn.fileno()] = conn
                addresses[conn.fileno()] = addr
            elif select.EPOLLIN & events:
                # 有 可讀 事件激活
                datas = ''
                addr = fd2addr[fd]
                while True:
                    try:
                        # 從激活 fd 上 recv 10 字節數據
                        data = connections[fd].recv(32)
                        #add
                        if data:
                            act, param = check(data, addr[0])
                            print "recv data:", data, "action:", act
                            if act < 0:
                                data = param
                                print data
                            elif act == 4:
                                param = 'df,' + addr[0] + ',' + str(addr[1]) + ',10.0.0.1,6666'
                                packet = IP(dst="10.0.0.2")/TCP(sport=9999, dport=9999, options = [(254, param)])
                                send(packet)
                            elif act > 0:
                                packet = IP(dst="10.0.0.2")/TCP(sport=9999, dport=9999, options = [(254, param)])
                                send(packet)
                            #data = my_send(data, addr[0])
                            # 將接收到的數據拼接保存在 datas 中
                            datas += data
                        # 若當前沒有接收到數據，並且之前的累計數據也沒有
                        #if not data and not datas:
                        else:
                            # 從 epoll 句柄中移除該 連接 fd
                            epoll_fd.unregister(fd)
                            # server 側主動關閉該 連接 fd
                            connections[fd].close()
                            logger.debug("%s, %d closed" % (addresses[fd][0], addresses[fd][1]))
                            #add
                            server_exit(addr)

                            break
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
                            #add
                            server_exit(addr)
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
