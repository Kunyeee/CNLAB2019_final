import time
import json
#import os
from Crypto.Random import random
#from Crypto.PublicKey import ElGamal as El
#from Crypto.Util.number import GCD, getPrime
#from Crypto.Hash import SHA
from argparse import ArgumentParser


parser = ArgumentParser()
parser.add_argument("-c", "--channel", default='10', dest= "CHANNEL", help= "Assign channel number")

parser.add_argument("-l", "--hardness", default='10', dest= "l", help= "Assign hardness to 2**(input)")

parser.add_argument("-s", "--solution", default='0', dest= "s", help= "Decide generater puzzle solution or not")

parser.add_argument("-i", "--input_folder", default="./" , dest= "i", help= "bastion parameter location")

parser.add_argument("-o", "--out_folder", default="./" , dest= "o", help= "output puzzle dir")


args =parser.parse_args()


CHANNEL=int(args.CHANNEL)
print 'CHANNEL =',CHANNEL
l=2**int(args.l)
print 'l =',l
BASTION_FILE=args.i+'bastion_pg.json'
print 'BASTION FILE =', BASTION_FILE
#print args.o

if int(args.s)==0:
    PUZ_SOL=False
else:
    PUZ_SOL=True

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

tmp=f.readline().strip()
sk=int(tmp.split('=')[1])
print 'sk= ',sk
tmp=f.readline().strip()
pk=int(tmp.split('=')[1])
print 'pk= ',pk
"""
f=open(BASTION_FILE, "r")
bastion_para=json.load(f)
p=bastion_para['p']
#print 'p= ',p
g=bastion_para['g']
#print 'g= ',g
sk=bastion_para['sk']
#print 'sk= ',sk
pk=bastion_para['pk']
#print 'pk= ',pk

puzzle={}
puzzle['time']=int(time.time())
puzzle['prime']=p
puzzle['generater']=g
puzzle['channel_num']=CHANNEL
puzzle['l']=l
puzzle['puzzle']={}

## generate solution file(only for experiement)
if PUZ_SOL:
    puzzle_sol={}
    puzzle_sol['time']=int(time.time())
    puzzle_sol['prime']=p
    puzzle_sol['generater']=g
    puzzle_sol['channel_num']=CHANNEL
    puzzle_sol['l']=l
    puzzle_sol['sol']={}

for i in range(CHANNEL):
    r_c=random.StrongRandom().randint(0,p-1)
    #print i,r_c
    tmp=random.StrongRandom().randint(0,l)
    a_c= (r_c+tmp) % p

    ## not do random permutation
    g_c=exp_and_sqr(g, a_c, p)
    puzzle['puzzle'][str(i)]={}
    puzzle['puzzle'][str(i)]['g']=g_c
    puzzle['puzzle'][str(i)]['r']=r_c

    if PUZ_SOL:
        puzzle_sol['sol'][str(i)]=a_c

puzzle_str=json.dumps(puzzle)
fp=open(args.o+'puzzle.json', "w")
fp.write(puzzle_str)
fp.close()

if PUZ_SOL:
    with open(args.o+'solution.json', "w") as f:
        json.dump(puzzle_sol, f)

'''
## dump bastion parameter to sign
bastion=El.construct((p,g,pk,sk))
#print bastion.x

## puzzle_str -> sha256
h=SHA.new()
h.update(puzzle_str)
sha_puzzle= h.hexdigest()
print "sha puzzle is:", sha_puzzle

while True:
    tmp_int= random.StrongRandom().randint(1, p-1)
    if GCD(tmp_int, p-1)==1:
        break

print tmp_int

sig= bastion._sign(sha_puzzle, tmp_int)
fp.write("\n"+sig)
fp.close()
'''


print "finish"

