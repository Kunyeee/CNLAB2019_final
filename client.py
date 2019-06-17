from scapy.config import conf
conf.ipv6_enabled = False
from scapy.all import *
import socket
import random
import sys
import os
from argparse import ArgumentParser
from CP_agent import *

my_ip = os.popen('ifconfig').read().split('inet addr:')[1].split(' ')[0]
idx = my_ip.split('.')[-1].rjust(3, '0')
outdir = './client_puzzle/'
T = CP_agent(my_ip, idx, outdir, False)
print my_ip

_ip_src = my_ip
_ip_dst = '10.0.0.2'
_port_dst = 6666
_seq = random.randint(0, 10000000)
_port = random.randint(5000, 20000)

parser = ArgumentParser(usage= '[-h] [-sp SP] [-dp DP] [-dip DIP] [-dt DT]')
parser.add_argument("-sp", default=str(random.randint(5000, 20000)), dest= "sp", help= "src port")
parser.add_argument("-dp", default='6666', dest= "dp", help= "dst port")
parser.add_argument("-dip", default='10.0.0.2', dest= "dip", help= "dst ip")
parser.add_argument("-dt", default='default', dest= "dt", help= "default using correct client_puzzle data")

while True:
    parser.print_help()
    while True:
        try:
            cmd = raw_input().strip().split(' ')
            if len(cmd) == 1 and cmd[0] == '':
                cmd = []
            args =parser.parse_args(cmd)
            break
        except:
            a = 1

    _port = int(args.sp)
    dp = int(args.dp)
    _ip_dst = args.dip
    dt = args.dt
    print '({}, {}) -> ({}, {})'.format(my_ip, _port, _ip_dst, dp)

    print "Press any key after server is ready."
    raw_input()
    if dt == 'default':
        data = T.get_puzzle(_ip_dst + ':' + str(dp))
    else:
        data = dt
    packet = IP(dst=_ip_dst, src=_ip_src)/TCP(sport=_port, dport=dp, seq=_seq, options = [(254, data)])
    send(packet)
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    s.bind((_ip_src, _port))
    s.connect((_ip_dst, dp))
    while True:
        t = raw_input()
        if t == 'exit':
            s.close()
            break
        else:
            s.send(t)
            print s.recv(len(t))

