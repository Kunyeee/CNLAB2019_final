import json
class Server_list():
    def __init__(self, server_file="./server_sk.json", check_json=False):
        self.server_file=server_file
        self.check_json=check_json
        self.SER=None
        return
    def load_server_sk(self):
        try:
            with open(self.server_file, "r") as f:
                tmp_str=f.read()
                if self.check_json==True:
                    if self.check_file_integrality(tmp_str)==True:
                        tmp_str=tmp_str[:-1]
                    else:
                        return False
                self.SER=json.loads(tmp_str)
        except:
            return False
            #self.SER=json.load(f)
        return

    def check_file_integrality(self, check_str):
        if check_str[-1]=='&':
            return True
        else:
            return False

    ## return None if not found, else return sk
    def name_to_sk(self, server_name):
        if server_name not in self.SER.keys():
            return None
        return self.SER[server_name]


class Server_puzzle():
    def __init__(self, puzzle_file="./puzzle.json", check_json=False ):
        self.puzzle_file=puzzle_file
        self.PUZ=None
        self.check_json=check_json
        self.defend_server={} ## server_name:{sk:???, ...}
        
        self.available_ans={"now":{}, "prev":{}}
        self.NOW_T=None
        return

    def check_file_integrality(self, check_str):
        if check_str[-1]=='&':
            return True
        else:
            return False

    ## return False if not new puzzle, True else
    def load_client_puzzle(self):
        try:
            with open(self.puzzle_file, "r") as f:
                tmp_str=f.read()
                if self.check_json==True:
                    if self.check_file_integrality(tmp_str)==True:
                        tmp_str=tmp_str[:-1]
                    else:
                        return False
                self.PUZ=json.loads(tmp_str)
        except:
            return False
            #self.PUZ=json.load(f)
        if self.NOW_T==self.PUZ['time']:
            return False

        self.NOW_T=self.PUZ['time']
        
        tmp_dict=self.available_ans["prev"]
        self.available_ans["prev"]=self.available_ans["now"]
        self.available_ans["now"]=tmp_dict
        self.available_ans["now"]['time']=self.PUZ['time']
        self.available_ans["now"]['ans']={}
        print "load complete"
        return True

    ## True if add, False if has exist
    def add_defend(self, server_name, server_sk):
        if server_name not in self.defend_server.keys():
            self.defend_server[server_name]={'sk': server_sk}
            return True
        return False

    def remove_defend(self, server_name):
        if server_name in self.defend_server.keys():
            del self.defend_server[server_name]
            return True
        return False

    def update_ans(self, mode="all", spec_server=None):
        p=self.PUZ['prime']
        update_attr=None
        for (key, items) in self.available_ans.items():
            #print key, items
            if items.get('time')!=None and items['time']==self.PUZ['time']:
                update_attr=items['ans']
        if update_attr==None:
            print("something wrong")
            return False
        
        if mode=="all":
            for server in self.defend_server.keys():
                server_sk=self.defend_server[server]['sk']
                update_attr[server]={}
                for (channel, puzzle) in self.PUZ['puzzle'].items():
                    tmp=self._exp_and_sqr(puzzle["g"], server_sk, p)  
                    update_attr[server][str(channel)]=self._first_n_bits(tmp,48)
        else:
            server_sk=self.defend_server[spec_server]['sk']
            update_attr[spec_server]={}
            for (channel, puzzle) in self.PUZ['puzzle'].items():
                tmp=self._exp_and_sqr(puzzle["g"], server_sk, p)
                update_attr[spec_server][str(channel)]=self._first_n_bits(tmp,48)
        
        return True

    def _exp_and_sqr(self, m, sk, mod_N):
        r=1
        bits="{0:b}".format(sk)
        for i, bit in enumerate(bits):
            if bit=='1':
                r = (((r**2)* m ) % mod_N)
            else:
                r = ((r**2) % mod_N)
        return r % mod_N
    
    def _first_n_bits(self, x, n):
        binary_str=bin(x)[2:]
        #print binary_str,"\n", binary_str[:n]
        return int(binary_str[:n],2)

    def check_ans(self, server_name, channel_ans_list):
        if server_name not in self.defend_server.keys():
            return True, [ tmp_tuple[0] for tmp_tuple in channel_ans_list ]
        check=False
        valid_channel=[]
        for (channel, ans) in channel_ans_list:
            #if check==True:
                #break
            for (time, tmp_dict) in self.available_ans.items():
                #print time, tmp_dict
                if tmp_dict.get('ans')==None:
                    continue               
                if server_name not in tmp_dict['ans'].keys():
                    continue
                correct_ans=tmp_dict['ans'][server_name].get(channel)

                print correct_ans
                if correct_ans==None:
                    continue
                else:
                    if correct_ans==ans:
                        check=True
                        valid_channel.append(channel)
                        break
        
        return check, valid_channel
    
if __name__=='__main__':
    ## below is only for test ##
    C=Server_list()
    C.load_server_sk()
    server2_sk=C.name_to_sk(str(2))
    #print server2_sk

    B=Server_puzzle()
    B.load_client_puzzle()
    #print B.PUZ
    B.add_defend(str(2), server2_sk)
    #print B.defend_server
    B.update_ans()
    print B.available_ans
    #print B.check_ans(str(2),[('0', 0), ('2', 152698141292545)])

    #B.remove_defend(str(2))
    #print B.defend_server
    #print B.check_ans(str(2),[('0', 0), ('0',0)])
    import time
    for i in range(5):
        print "================="
        time.sleep(10)
        print B.load_client_puzzle()
        B.update_ans()
        print B.available_ans
