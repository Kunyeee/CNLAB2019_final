import socket
import threading
import time
import sys
sys.path.append('./client_puzzle/')
from client_puzzle import *
    
class CP_agent():
    def __init__(self, my_ip, idx, outdir, exec_once=False):
        self.A = Client_puzzle(puzzle_file="./puzzle" + idx + ".json", 
                 server_file=outdir + "./server_pk.json",ans_dump="./solved_ans" + idx + ".json")
        self.A.load_server_pk()
        self.my_ip = my_ip
        self.idx = idx
        self.exec_once = exec_once
        threading.Thread(target=self.recver).start()
    def solver(self):
        print "start solving puzzle"
        while True:
            if self.A.load_client_puzzle():
                self.A.random_solve()
                #self.A.dump_ans_file()
                #print "dump file:", 'solved_ans' + self.idx + '.json'
                print "solved"
                break
            else:
                time.sleep(1)

    def recver(self):
        #my_ip = os.popen('ifconfig').read().split('inet addr:')[1].split(' ')[0]
        print "my_ip =", self.my_ip
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('', 8888))


        rcv_cnt = 0
        while True:
            print "rcv_cnt =", rcv_cnt
            rcv_cnt += 1
            buf = {}
            packet_num = None
            cnt = 0
            while True:
                data, addr = s.recvfrom(1024)
                if data:
                    tmp = data.split('$')
                    num = int(tmp[0])
                    print "recv data", num, len(tmp[1])
                    if tmp[1] == '':
                        packet_num = num
                        print "num, cnt =", num, cnt
                    else:
                        buf[num] = tmp[1]
                    cnt += 1
                else:
                    print "socket error"
                    break
                if cnt - 1== packet_num:
                    break
            dd = ''
            for i in range(packet_num):
                dd += buf[i]
            outfile = 'puzzle' + self.my_ip.split('.')[-1].rjust(3, '0') + '.json'
            f = open(outfile, 'w')
            f.write(dd)
            f.close()
            print "Write", outfile, "done"
            print "exec solver now"
            t1 = threading.Thread(target=self.solver)
            t1.start()
            if self.exec_once:
                t1.join()
                print "exec_once, exit"
                break
    def get_puzzle(self, hostname):
        #hostname format: ex, 10.0.0.2:6666
        f = open('sv2id', 'r')
        idx = '-1'
        for lines in f:
            s = lines.strip().split(',')
            if s[0] == hostname:
                idx = s[1]
                break
        f.close()
        print "in get puzzle, idx=", idx
        if int(idx) < 0:
            return "host didn't register"
        while True:
            #self.A.load_ans_file()
            res, pl = self.A.get_append_bytes(idx)
            if res:
                return str(pl[0][0]) + ',' + str(pl[0][1]) + ',' + str(pl[1][0]) + ',' + str(pl[1][1])
            else:
                time.sleep(1)

