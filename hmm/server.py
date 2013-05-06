'''
author: Daniel Ryan
date: 21 mar 2013

listens for OSC messages from the sequencer patch.
uses HMMs to create a drum input to the sequencer patch.
drum input is sent back to sequencer patch via OSC
'''

from osc_utils import *
import time

NUM_DRUMS = 8

def main():
    
    # init osc communication with MAX
    initOSCServer(port=6901)
    startOSCServer()
    
    setOSCHandler()
    reportOSCHandlers()
    
    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()