import json
#import os
from Crypto.Random import random
from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument("-s", "--server", default='10', dest= "s", help= "Assign server_number")

parser.add_argument("-i", "--input_folder", default='./', dest= "i", help= "bastion parameter folder")

parser.add_argument("-o", "--out_folder", default="./" , dest= "o", help= "output key dir")

args =parser.parse_args()

SERVER_NUM=int(args.s)
print SERVER_NUM
BASTION_FILE=args.i+'bastion_pg.json'
print BASTION_FILE

def exp_and_sqr(m, sk, mod_N):
    r=1
    bits="{0:b}".format(sk)
    for i, bit in enumerate(bits):
        if bit=='1':
            r = (((r**2)*m) % mod_N)
        else:
            r = ((r**2) % mod_N)
    return r % mod_N
"""
f=open("bastion_pg.txt", "r")
tmp=f.readline().strip()
p=int(tmp.split('=')[1])
print 'p= ',p
tmp=f.readline().strip()
g=int(tmp.split('=')[1])
print 'g= ',g
f.close()
"""
f=open(BASTION_FILE, "r")
bastion_para=json.load(f)
p=int(bastion_para['p'])
print 'p= ',p
g=int(bastion_para['g'])
print 'g= ',g

server_pk={}
server_sk={}
for i in range(SERVER_NUM):
    new_sk=random.StrongRandom().randint(0,p-1)
    new_pk=exp_and_sqr(g, new_sk, p)
    server_pk[str(i)]=new_pk
    server_sk[str(i)]=new_sk

with open(args.o+"server_sk.json","w") as f:
    json.dump(server_sk,f)

with open(args.o+"server_pk.json","w") as f:
    json.dump(server_pk,f)


