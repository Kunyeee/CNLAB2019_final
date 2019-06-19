from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import argparse
import random
import socket
import time

from scapy.all import *
from scapy.config import conf
conf.ipv6_enabled = False

from CP_agent import CP_agent


def main(args):
    
    host_idx = args.ip.split('.')[-1].rjust(3, '0')
    puzzle_dir = 'client_puzzle/'
    puzzle_agent = CP_agent(args.ip, host_idx, puzzle_dir, False)

    n_connection = 0
    while True:
        try:
            num_msg = random.randint(1, 20)
            interval = random.uniform(0.01, 3)
            client_port = random.randint(1000, 65535)
            n_connection += 1

            solved_puzzle = puzzle_agent.get_puzzle('{}:{}'.format(args.server_ip, args.server_port))
            packet = IP(
                dst = args.server_ip, 
                src = args.ip
            ) / TCP(
                sport = client_port, 
                dport = args.server_port, 
                seq = 1, 
                options = [(254, solved_puzzle)]
            )
            send(packet)

            time.sleep(1)

            s = socket.socket()
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((args.ip, client_port))
            s.connect((args.server_ip, args.server_port))

            for i in range(num_msg):
                msg = 'Connection #{}, Msg #{}'.format(n_connection, i+1)
                s.send(msg)
                print(s.recv(len(msg)))
                
                time.sleep(interval)

        except socket.error:
            print('!!! CONNECTION ERROR !!!')
            print('Wait 10 seconds and retry ...')
            time.sleep(10)



def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, required=True, dest='ip', help='source ip')
    parser.add_argument('--server-ip', type=str, required=True, dest='server_ip', help='server ip')
    parser.add_argument('--server-port', type=int, default=6666, dest='server_port', help='server port')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    try:
        main(args)
    except KeyboardInterrupt:
        pass