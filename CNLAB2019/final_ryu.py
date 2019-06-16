from ryu.lib.packet import *
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib import hub

import sys
import subprocess
sys.path.append('./client_puzzle/')
from server_puzzle import *

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.switch = []
        #self.server = set()
        self.channel_num = 10
        self.channel = {} #the number of channel in use
        self.cn2ch = {} #connection to channel number
        self.server = {}#(ip, port) : (idx, connection_number) 
        #self.server.add(('10.0.0.1', 6666))
        outdir = './client_puzzle/'
        
        subprocess.call(['sudo', 'python', outdir + 'generate_server_key.py', '-i', outdir, '-o', outdir])
        print "server_key available"
        self.C=Server_list(server_file = outdir + 'server_sk.json')
        self.C.load_server_sk()
        #self.server2_sk = self.C.name_to_sk('0')
        self.B=Server_puzzle(puzzle_file = outdir + 'puzzle.json')
        self.add_server(('10.0.0.1', 6666), 0, 50)
        #self.B.add_defend(0, self.C.name_to_sk('0'))
        #f.write('10.0.0.1:6666,0')
        self.monitor_thread = hub.spawn(self.cp_server)
    def del_server(self, hostname):
        idx = self.server[hostname][0]
        del self.server[hostname]
        self.B.remove_defend(idx)
        f = open('sv2id', 'w')
        for (host, v) in self.server.items():
            f.write(host[0] + ':' + str(host[1]) + ',' + str(v[0]) + '\n')
        f.close()
        del self.channel[hostname]

    def add_server(self, hostname, idx, conn_num):
        self.server[hostname] = (idx, conn_num)
        self.B.add_defend(idx, self.C.name_to_sk(str(idx)))
        f = open('sv2id', 'w')
        for (host, v) in self.server.items():
            f.write(host[0] + ':' + str(host[1]) + ',' + str(v[0]) + '\n')
        f.close()
        self.channel[hostname] = {}
        for i in range(10):
            self.channel[hostname][str(i)] = 0
        print "self.server:", self.server
    
    def cp_server(self):
        while True:
            if self.B.load_client_puzzle():
                self.B.update_ans()
                print self.B.available_ans
                hub.sleep(10)
            else:
                hub.sleep(1)

    def check(self, data, idx):
        print "in check"
        try:
            s = data[0].value.split(',')
            a = [(s[0], int(s[1])), (s[2], int(s[3]))]
            #a = [int(i) for i in data[0].value.split(',')]
        except:
            return False
        return self.B.check_ans(str(idx), a)[1]

    def bastion_handler(self, cmd):
        s = cmd.split(',')
        if s[0] == 'o' or s[0] == 'c':
            ip = s[1]
            port = int(s[2])
            for d in self.switch:
                match = d.ofproto_parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, 
                ip_proto=in_proto.IPPROTO_TCP, ipv4_dst=ip, tcp_dst=port)
                actions = [d.ofproto_parser.OFPActionOutput(d.ofproto.OFPP_CONTROLLER, d.ofproto.OFPCML_NO_BUFFER)]
                if s[0] == 'o':
                    self.add_server((ip, port), int(s[4]), int(s[3]))
                    self.add_flow(d, 2, match, actions)
                else:
                    self.del_server((ip, port))
                    self.del_flow(d, 2, match)
                    self.del_flow(d, 3, match)
        elif s[0] == 'df':
            src = (s[1], int(s[2]))
            dst = (s[3], int(s[4]))
            print "delet flow", src, "->", dst
            try:
                c = self.cn2ch[(src, dst)]
                del self.cn2ch[(src, dst)]
            except:
                return 
            self.channel[dst][c] -= 1
            for d in self.switch:
                match = d.ofproto_parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, 
                ip_proto=in_proto.IPPROTO_TCP, ipv4_src=s[1], tcp_src=int(s[2]), ipv4_dst=s[3], tcp_dst=int(s[4]))
                self.del_flow(d, 3, match)

            
        #if s[0] == 'd':
        #    self.server.remove((ip, port))

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        #add
        self.switch.append(datapath)

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.
        match1 = parser.OFPMatch()
        #add
        match2 = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ip_proto=in_proto.IPPROTO_TCP, in_port=1, ipv4_src='10.0.0.1', tcp_src=9999, tcp_dst=9999)
        match3 = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ip_proto=in_proto.IPPROTO_UDP, udp_dst=8888)
        match4 = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ip_proto=in_proto.IPPROTO_UDP, in_port=1, udp_dst=8888)
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match1, actions)
        self.add_flow(datapath, 100, match2, actions)
        self.add_flow(datapath, 97, match3, [])
        self.add_flow(datapath, 98, match4, actions)
        #add
        for ip, port in self.server:
            match2 = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ip_proto=in_proto.IPPROTO_TCP, ipv4_dst=ip, tcp_dst=port)
            self.add_flow(datapath, 2, match2, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)
    def del_flow(self, datapath, priority, match):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        mod = parser.OFPFlowMod(datapath=datapath, command=ofproto.OFPFC_DELETE, priority=priority,
                                match=match, out_port=ofproto.OFPP_ANY,out_group=ofproto.OFPG_ANY)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        

        pkt = packet.Packet(data=msg.data)
        #eth = pkt.get_protocols(ethernet.ethernet)[0]
        eth = pkt.get_protocol(ethernet.ethernet)
        
        #add
        print ""
        #for p in pkt.protocols:
        #    print "p =", p
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        pkt_tcp = pkt.get_protocol(tcp.tcp)
        pkt_udp = pkt.get_protocol(udp.udp)

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        #add
        valid = True
        if pkt_tcp and pkt_ipv4:
            print "{}:{} -> {}:{}".format(pkt_ipv4.src, pkt_tcp.src_port, pkt_ipv4.dst, pkt_tcp.dst_port)
            if pkt_ipv4.src == '10.0.0.1' and pkt_tcp.src_port == 9999 and pkt_tcp.dst_port == 9999:
                t = pkt_tcp.option[0].value
                print "bastion send to controller", t
                self.bastion_handler(t)
                valid = False
        elif pkt_ipv4:
            print "{} -> {}".format(pkt_ipv4.src, pkt_ipv4.dst)
        if pkt_tcp and (pkt_ipv4.dst, pkt_tcp.dst_port) in self.server:
            t = pkt_tcp.option
            dst = (pkt_ipv4.dst, pkt_tcp.dst_port)
            src = (pkt_ipv4.src, pkt_tcp.src_port)
            print "option", t
            channel = self.check(t, self.server[dst][0])
            if channel:
                for c in channel:
                    if self.channel[dst][c] < self.server[dst][1] / self.channel_num:
                        self.channel[dst][c] += 1
                        self.cn2ch[(src, dst)] = c
                        valid = True
                        break
        if pkt_udp and pkt_ipv4:
            print "{}:{} -> {}:{}".format(pkt_ipv4.src, pkt_udp.src_port, pkt_ipv4.dst, pkt_udp.dst_port)

        print "valid =", valid
        print "channel", self.channel

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        #if out_port != ofproto.OFPP_FLOOD:
        #modify
        if out_port != ofproto.OFPP_FLOOD:
            if pkt_tcp and valid:
            #match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_type=ether_types.ETH_TYPE_IP, ipv4_src=pkt_ipv4.src)
                match1 = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_type=ether_types.ETH_TYPE_IP, ip_proto=in_proto.IPPROTO_TCP, ipv4_src=pkt_ipv4.src, ipv4_dst=pkt_ipv4.dst ,tcp_src=pkt_tcp.src_port, tcp_dst=pkt_tcp.dst_port)
                print "add_flow1"
                self.add_flow(datapath, 3, match1, actions)
            elif valid:
                print "add_flow2"
                match1 = parser.OFPMatch(in_port=in_port, eth_dst=dst)
                match2 = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ip_proto=in_proto.IPPROTO_UDP, in_port = 1, udp_dst=8888)
                self.add_flow(datapath, 1, match1, actions)
                self.add_flow(datapath, 99, match2, actions)


        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        #datapath.send_msg(out)
        #mod
        if valid:
            datapath.send_msg(out)
