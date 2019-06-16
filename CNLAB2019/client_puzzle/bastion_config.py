from Crypto import Random
from Crypto.PublicKey import ElGamal as El
import time
import json
from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument("-k", "--key", default='2048', dest= "k", help= "Assign prime length")
parser.add_argument("-o", "--out_folder", default='./', dest= "o", help= "bastion parameter output dir")
args =parser.parse_args()
print int(args.k)

def exp_and_sqr(m, sk, mod_N):
    r=1
    bits="{0:b}".format(sk)
    for i, bit in enumerate(bits):
        if bit=='1':
            r = (((r**2)*m) % mod_N)
        else:
            r = ((r**2) % mod_N)
    return r % mod_N

key=El.generate(int(args.k), Random.new().read)
#key=El.generate(2048, Random.new().read)
print "p is: ", int(key.p)
print "g is: ", int(key.g)
#print "sk is: ", int(key.x)
#print "pk is: ", int(key.y)

#print "============"
#print exp_and_sqr(int(key.g), int(key.x), int(key.p))
p=int(key.p)
g=int(key.g)
sk=int(key.x)
pk=int(key.y)
bastion={}
bastion['p']=p
bastion['g']=g
bastion['sk']=sk
bastion['pk']=pk
"""
fp=open("bastion_pg.txt", "w")
fp.write("p=%d\ng=%d\n"%(p,g))
fp.write("sk=%d\npk=%d\n"%(sk,pk))
"""
fp=open(args.o+'bastion_pg.json', "w")
json.dump(bastion,fp)
fp.close()

