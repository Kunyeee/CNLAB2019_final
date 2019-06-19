import os, sys
import argparse
import functools
import subprocess

sys.path.insert(0, os.path.join(os.path.expanduser("~"), 'mininet'))

import mininet as mn
from mininet.topo import Topo 
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController


class MyTopo(Topo):
    
    def __init__(self,  num_hosts, host_dir_prefix=''):
        Topo.__init__(self)

        switch = self.addSwitch('s1')

        self.hosts_ = [ f"h{i+1}" for i in range(num_hosts) ]

        for hostname in self.hosts_:
            host = self.addHost(hostname)
            self.addLink(host, switch)


def parse_cmd(line, available_hosts):
    """
    line: command
    available_hosts: all available hosts' name (set)

    Commands:
        agent host [host...]
        server host [host...]
        client host server
        attacker host_start host_end target_server
        stop host_start [host_end]
        stopall 'agent' | 'server' | 'client' | 'attacker'
        cli
        exit
    """

    try:

        tokens = line.split()
        if len(tokens) == 0:
            return None

        cmd = tokens[0]
        if cmd == 'cli' or cmd == 'exit':
            if len(tokens) == 1:
                return cmd, None
            else:
                return None
        
        if cmd == 'attacker':
            if len(tokens) != 4:
                return None
        
            host_start = int(tokens[1][1:])
            host_end = int(tokens[2][1:])
            hosts = [ f"h{i}" for i in range(host_start, host_end+1) ]

            for host in hosts:
                if host not in available_hosts:
                    return None

            if tokens[3] not in available_hosts:
                return None

            return cmd, (hosts, tokens[3])

        if cmd == 'stop':
            if len(tokens) == 2:
                hosts = [ tokens[1] ]
            elif len(tokens) == 3:
                host_start = int(tokens[1][1:])
                host_end = int(tokens[2][1:])
                hosts = [ f"h{i}" for i in range(host_start, host_end+1) ]
            else:
                return None

            for host in hosts:
                if host not in available_hosts:
                    return None

            return cmd, hosts

        if cmd == 'stopall':
            if len(tokens) != 2 or tokens[1] not in [ 'agent', 'server', 'client', 'attacker' ]:
                return None

            return cmd, tokens[1]

        if cmd == 'client':
            if len(tokens) != 3:
                return None

            if tokens[1] in available_hosts and tokens[2] in available_hosts:
                return cmd, tokens[1:]
            else:
                return None
        
        if cmd == 'agent' or cmd == 'server':
            if len(tokens) < 2:
                return None
            
            for host in tokens[1:]:
                if host not in available_hosts:
                    return None

            return cmd, tokens[1:]

        return None

    except ValueError:
        return None


def main(args):
    mn.log.setLogLevel('info')
    
    topo = MyTopo(num_hosts = args.num_hosts)

    net = Mininet(
        topo = topo,
        switch = functools.partial(OVSKernelSwitch, protocols='OpenFlow13'),
        controller = functools.partial(RemoteController),
        autoSetMacs = True
    )

    if not os.path.isdir(args.output_dump_dir):
        os.mkdir(args.output_dump_dir)

    dump_file = lambda host: os.path.join(args.output_dump_dir, f"{host}.out")
    
    try:
        net.start()

        available_hosts = set(topo.hosts_)

        agents = {}
        servers = {}
        clients = {}
        attackers = {}
        host_to_role_dict = {}
        role_to_dict = {
            'agent': agents,
            'server': servers,
            'client': clients,
            'attacker': attackers 
        }

        while True:
            parsed_cmd = parse_cmd(input('> '), available_hosts)
            if parsed_cmd is None:
                print('!!! Invalid command !!!')

            else:
                cmd, params = parsed_cmd

                if cmd == 'cli':
                    mn.cli.CLI(net)

                elif cmd == 'exit':
                    for host, role_dict in host_to_role_dict.items():
                        role_dict[host].kill()

                    sys.exit(0)

                elif cmd == 'agent':
                    hosts = params
                    for h in hosts:
                        agents[h] = net[h].popen(
                            f"stdbuf -oL python agent.py",
                            stdout = open(dump_file(h), 'w'),
                            stderr = subprocess.STDOUT
                        )
                        host_to_role_dict[h] = agents

                elif cmd == 'server':
                    hosts = params
                    for h in hosts:
                        servers[h] = net[h].popen(
                            f"stdbuf -oL python server.py -ip {net[h].IP()}",
                            stdout = open(dump_file(h), 'w'),
                            stderr = subprocess.STDOUT
                        )
                        host_to_role_dict[h] = servers

                elif cmd == 'client':
                    host, server = params
                    clients[host] = net[host].popen(
                        f"stdbuf -oL python client_auto.py --ip {net[host].IP()} --server-ip {net[server].IP()}",
                        stdout = open(dump_file(host), 'w'),
                        stderr = subprocess.STDOUT
                    )
                    host_to_role_dict[host] = clients

                elif cmd == 'attacker':
                    hosts, target = params
                    for h in hosts:
                        attackers[h] = net[h].popen(
                            f"stdbuf -oL python attacker.py --ip {net[h].IP()} --target-ip {net[target].IP()}",
                            stdout = open(dump_file(h), 'w'),
                            stderr = subprocess.STDOUT
                        )
                        host_to_role_dict[h] = attackers

                elif cmd == 'stop':
                    hosts = params
                    for h in hosts:
                        role_dict = host_to_role_dict[h]
                        proc = role_dict[h]
                        proc.kill()
                        del role_dict[h]
                        del host_to_role_dict[h]

                elif cmd == 'stopall':
                    for host, proc in role_to_dict[params].items():
                        proc.kill()
                        del host_to_role_dict[host]

                    role_to_dict[params].clear()

    finally:
        net.stop()


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', type=int, required=True, dest='num_hosts', help='number of hosts')
    parser.add_argument('-o', type=str, required=True, dest='output_dump_dir', help='output dump directory')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    try:
        main(args)
    except KeyboardInterrupt:
        pass