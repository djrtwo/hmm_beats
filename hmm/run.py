'''
author: Daniel Ryan
date: 21 mar 2013

listens for OSC messages from the sequencer patch.
uses HMMs to create a drum input to the sequencer patch.
drum input is sent back to sequencer patch via OSC
'''

from osc_utils import *
from BeatModel import BeatModel
from HMM_set import HMM_set
from HMMRP import HMMRP
from RandomRP import RandomRP
import argparse
import time

NUM_DRUM_PADS = 4
        
def set_row(addr, tags, data, source):
    print "---"
    print "received new osc msg from %s" % getUrlStr(source)
    print "with addr : %s" % addr
    print "typetags :%s" % tags
    print "the actual data is : %s" % data
    print "---"
    
    row = int(addr[-1])
    RP.set_row(row, data)
    
def save_row(addr, tags, data, source):
    print "---"
    print "received new osc msg from %s" % getUrlStr(source)
    print "with addr : %s" % addr
    print "typetags :%s" % tags
    print "the actual data is : %s" % data
    print "---"
    
    row = int(addr[-1])
    RP.save_row(row, data)

def main(args):    
    # init osc communication with MAX
    initOSCClient(port=6900)
    initOSCServer(port=6901)
    startOSCServer()
    
    global RP
    if args.random:
        RP = RandomRP(NUM_DRUM_PADS, args.freq_path)
    else:
        hmm = HMM_set(args.input_name)
        print hmm.hmms
        RP = HMMRP(NUM_DRUM_PADS, hmm)
        
    for i in range(NUM_DRUM_PADS):
        setOSCHandler('/set_row%d' % i, set_row)
        setOSCHandler('/save_row%d' % i, save_row)
   
    while True:
        time.sleep(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build and test hmms via ghmm.')
    parser.add_argument('-i', dest='input_name', help="midi input folder name", type=str)
    parser.add_argument('-o', dest='output_name', help="output folder file", type=str, default=None)
    parser.add_argument('-v', dest='verbose', help="turn on verbose printing", action='store_true', default=False)
    parser.add_argument('-r', dest='random', help='enable random row processing', action='store_true', default=False)
    parser.add_argument('-f', dest='freq_path', help='file containing average drum frequencies', type=str, default=None)    
    args = parser.parse_args()
    main(args)