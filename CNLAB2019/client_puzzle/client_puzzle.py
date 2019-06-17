import json
from Crypto.Random import random


class Client_puzzle():
    def __init__(self, puzzle_file="./puzzle.json", server_file="./server_pk.json", check_json=False ,enable_cheat=False, cheat_file=None, ans_dump="./solved_ans.json"):
        self.puzzle_file=puzzle_file
        self.server_file=server_file
        self.check_json=check_json
        self.ans_dump=ans_dump
        self.PUZ=None
        self.SER=None
        self.available_ans={"now":{}, "prev":{}}
        self.NOW_T=None
        if enable_cheat:
            self.cheat=True
            self.cheat_file=cheat_file
            self.SOL=None
        else:
            self.cheat=False
            self.cheat_file=None
            self.SOL=None
        return
    
    def load_ans_file(self):
        try:
            with open(self.ans_dump, "r") as f:
                tmp_str=f.read()
                '''
                if self.check_json==True:
                    if self.check_file_integrality(tmp_str)==True:
                        tmp_str=tmp_str[:-1]
                    else:
                        return False
                '''
                self.available_ans=json.loads(tmp_str)
        except:
            return False

                #self.available_ans=json.load(f)
        return True

    def dump_ans_file(self):
        with open(self.ans_dump, "w") as f:
            tmp_str=json.dumps(self.available_ans)
            '''
            if self.check_json==True:
                tmp_str+='&'
            '''
            f.write(tmp_str)
            #json.dump(self.available_ans, f)
        return True

    def load_cheat_file(self):
        if not self.cheat:
            return False
        try:
            with open(self.cheat_file, "r") as f:
                tmp_str=f.read()
                '''
                if self.check_json==True:
                    if self.check_file_integrality(tmp_str)==True:
                        tmp_str=tmp_str[:-1]
                    else:
                        return False
                '''
                self.SOL=json.loads(tmp_str)
        except:
            return False
            #self.SOL=json.load(f)
        return True
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
        if self.NOW_T==self.PUZ['time']:
            return False

        self.NOW_T=self.PUZ['time']
        tmp_dict=self.available_ans["prev"]
        self.available_ans["prev"]=self.available_ans["now"]
        #print "??",self.available_ans["prev"]
        self.available_ans["now"]=tmp_dict
        self.available_ans["now"]['p']=self.PUZ['prime']
        self.available_ans["now"]['g']=self.PUZ['generater']
        self.available_ans["now"]['l']=self.PUZ['l']
        self.available_ans["now"]['c_num']=self.PUZ['channel_num']
        self.available_ans["now"]['time']=self.PUZ['time']
        self.available_ans["now"]['ans']={}
        #print "**",self.available_ans["prev"]
        print "load complete"
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

    def get_channel_num(self, spec_time="now"):
        if spec_time not in self.available_ans.keys() or self.available_ans[spec_time].get('c_num')==None:
            print "not valid spec time!!!"
            return None
        return self.available_ans[spec_time]['c_num']

    def load_server_pk(self):
        try:
            with open(self.server_file, "r") as f:
                tmp_str=f.read()
                '''
                if self.check_json==True:
                    if self.check_file_integrality(tmp_str)==True:
                        tmp_str=tmp_str[:-1]
                    else:
                        return False
                '''
                self.SER=json.loads(tmp_str)
        except:
            return False
            #self.SER=json.load(f)
        return True

    def cheat_solve(self, channel):
        if self.cheat==False:
            return False
        ans=self.SOL['sol'][str(channel)]

        for (key, items) in self.available_ans.items():
            #print key, items
            if items.get('time')!=None and items['time']==self.SOL['time']:
                items['ans'][str(channel)]=ans
                return True
        print "solution file out-of-date!!"
        return False
    ## False if error
    def solve(self, channel):
        r_c=self.PUZ['puzzle'][str(channel)]['r']
        g_c=self.PUZ['puzzle'][str(channel)]['g']
        p=self.PUZ['prime']
        g=self.PUZ['generater']
        l=self.PUZ['l']
        ans=None
        i=0
        while i <= l:
            test_number=(r_c+i) % p
            if self._exp_and_sqr(g, test_number, p)==g_c:
                ans=test_number
                break
            i+=1
        if ans==None:
            print("client puzzle crashed!!!")
            return False
        for (key, items) in self.available_ans.items():
            #print key, items
            if items.get('time')!=None and items['time']==self.PUZ['time']:
                # print "solve",key,"client puzzle, channel=",channel
                items['ans'][str(channel)]=ans
                return True
        return False
    def remove_channel_ans(self, channel, spec_time="now"):
        if spec_time not in self.available_ans.keys() or self.available_ans[spec_time].get('ans')==None:
            print "not valid spec time!!!"
            return None

        channel_str=str(channel)
        if channel_str in self.available_ans[spec_time]['ans'].keys():
            del self.available_ans[spec_time]['ans'][channel_str]
            return True
        return False

    ## random select an unsolve channel to call solve
    def random_solve(self):
        channel_num= self.PUZ['channel_num']
        tmp_int=random.StrongRandom().randint(0,channel_num-1)
        while self.available_ans["now"].get('ans')!=None and str(tmp_int) in self.available_ans["now"]["ans"].keys():
            tmp_int=random.StrongRandom().randint(0,channel_num-1)

        return self.solve(tmp_int)
    
    #return False if no ans to send
    def _first_n_bits(self, x, n):
        binary_str=bin(x)[2:]
        #print binary_str,"\n", binary_str[:n]
        return int(binary_str[:n],2)
    
    def _cacu_ans(self, puzzle_attr, server_pk):
        if puzzle_attr.get('ans')!=None and len(puzzle_attr["ans"].keys())>0:
            channel , tmp_ans =random.StrongRandom().choice( list(puzzle_attr["ans"].items()) )
            ans=self._exp_and_sqr(server_pk, tmp_ans, puzzle_attr['p'])
            ans=self._first_n_bits(ans, 48)
            return True, (channel, ans)
        else:
            return False, ('0',0)

    ## return True/False + ans
    def get_append_bytes(self, server_name):
        server_pk=self.SER[server_name]
        #print server_pk
        
        have_ans=False
        ans_list=[]

        ## do prev first
        
        puzzle_attr=self.available_ans["prev"]
        (outcome, ans_tuple) =self._cacu_ans(puzzle_attr, server_pk)
        if outcome:
            have_ans=True
        ans_list.append(ans_tuple)

        ## then do now
        puzzle_attr=self.available_ans["now"]
        (outcome, ans_tuple) =self._cacu_ans(puzzle_attr, server_pk)
        if outcome:
            have_ans=True
        ans_list.append(ans_tuple)

        if have_ans:
            return True, ans_list
        else:
            return False, None

if __name__=='__main__':
    ## below is test ##
    
    ## generate Client_puzzle instance
    A=Client_puzzle()
    #A=Client_puzzle(enable_cheat=True, cheat_file='./solution.json')

    ## load client puzzle, discard out-of-date puzzle and its solution
    print A.load_client_puzzle()

    ## load server_public key
    A.load_server_pk()
    #print A.SER

    ## solve now client puzzle spec channel solution
    A.solve(2)
    print [items['ans'] for (key,items) in A.available_ans.items() if items.get('ans')!=None]
    #print A.dump_ans_file()
    #print A.load_ans_file()
    ## generate client puzzle solution to spec server name(random pick valid channel from above)
    ## return True/False + two (channel, ans) set
    print A.get_append_bytes(str(2))

    ## remove a spec channel's solution (can spec "now"/"prev")
    print A.get_channel_num(spec_time="now")
    #print A.remove_channel_ans(2)
    #print A.remove_channel_ans(2, spec_time="now")
    #print [items['ans'] for (key,items) in A.available_ans.items() if items.get('ans')!=None]
    import time
    for i in range(5):
        print "========================="
        time.sleep(10)
        print A.load_client_puzzle()
        A.random_solve()
        print [items['ans'] for (key,items) in A.available_ans.items() if items.get('ans')!=None]
    '''
    ## below is cheat file if you have client puzzle's solution
    ## only load cheat file , not matching (may be out-of-date)
    print A.load_cheat_file()

    ## solve spec channel's solution use solution file , return False if error or puzzle solution out-of-date
    print A.cheat_solve(2)
    print [items['ans'] for (key,items) in A.available_ans.items() if items.get('ans')!=None]
    '''

