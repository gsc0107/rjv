#!/usr/bin/python

'''
split fasta into chunks based on record counting
'''

import os,sys
if os.uname()[1] != 'mocedades':
    sys.path.append('/ibers/ernie/home/rov/python_lib')
    
from rjv.fasta import *

usage=\
'''
usage: splitfasta.py <fastafile> <chunks>

eg splitfasta.py mycontigs.fa 10
gives mycontigs-000.fa,... mycontigs-009.fa
'''

if len(sys.argv) != 3:
    print usage
    exit()
    
inpname = sys.argv[1]
chunks = int(sys.argv[2])
base = os.path.basename(inpname)
base = ''.join(base.split('.')[:-1]) + '-%03d.fa'

f = [open(base%i,'wb') for i in xrange(chunks)]

for i,fa in enumerate(next_fasta(inpname)):
    write_fasta(fa,f[i%chunks])

for x in f: x.close()
