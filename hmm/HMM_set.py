'''
author: Daniel Ryan
date: 22 mar 2013
HMM_set object is a container for all of the HMMs associated with a midi dataset.
This object is loaded by run.py to provide information to the sequencer max patch

if there are no models in models/ then the test_data.py will run to build the models.
'''

import ghmm
import glob
import os
import argparse
from itertools import combinations

class HMM_set(object):
    
    def __init__(self, input_dir=None, num_drums=4):
        self.hmms = {}
        self.num_drums = num_drums
        
        # load hmms from dir
        if input_dir:
            os.chdir(input_dir)
            hmm_files = glob.glob('*.xml')
            for hmm_file in hmm_files:
                hmm = ghmm.HMMOpen(hmm_file)
                self.hmms[hmm_file.split('.')[0]] = hmm
                
        # build neutral hmms
        else:
            for i in range(self.num_drums):
                for combo in combinations(range(self.num_drums), i):
                    if combo == ():
                        pass
                    else:
                        hidden_drums = list(combo)
                        visible_drums = list(set(range(self.num_drums)) - set(combo))
                        
                        self.add_neutral_hmm(hidden_drums)

    def add_neutral_hmm(self, hidden_drums):
        hmm_label = ''
        for i in range(self.num_drums):
            hmm_label = hmm_label + '0' if i in hidden_drums else hmm_label + '1'
            
        num_hidden = self.num_states(len(hidden_drums))
        num_visible = self.num_states(self.num_drums - len(hidden_drums))
        trans = [[1.0/num_hidden]*num_hidden for i in range(num_hidden)]
        emission = [[1.0/num_visible]*num_visible for i in range(num_hidden)]
        
        pi = [1.0/num_hidden for i in range(num_hidden)]
        
        emission_domain = ghmm.IntegerRange(0, num_visible)
        dist = ghmm.DiscreteDistribution(emission_domain)
        
        hmm = ghmm.HMMFromMatrices(emission_domain, dist, trans, emission, pi)
        
        self.hmms[hmm_label] = hmm

    @classmethod
    def num_states(cls, num_drums):
        return 2**num_drums

    def train_hmm(self, hmm_label, emissions):
        num_vis_drums = sum(int(hmm_label[i]) for i in range(len(hmm_label)))
        emission_domain = ghmm.IntegerRange(0, self.num_states(num_vis_drums))
        
        train_seq = ghmm.EmissionSequence(emission_domain, emissions)
        self.hmms[hmm_label].baumWelch(train_seq)

    def build_states_from_rows(self, row_list):
        if not row_list:
            states = [0 for i in range(64/self.num_drums)]
        else:
            states = []
            for i in range(len(row_list[0])):
                state = 0
                for j in range(len(row_list)):
                    state = state + row_list[j][i] * (2**j)
                states.append(state)
       
        return states
    
    def get_hidden(self, hmm_label, row_list):
        emissions = self.build_states_from_rows(row_list)
        print 'emissions: %s' % emissions
        emission_domain = ghmm.IntegerRange(0, 2**len(row_list))
        print 'emission_domain: %s' % emission_domain
        
        return self.hmms[hmm_label].viterbi(ghmm.EmissionSequence(emission_domain, emissions))[0]

def main(args):
    input_dir = args.input_name
    hmm = HMM_set(input_dir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build and test hmms via ghmm.')
    parser.add_argument('-i', dest='input_name', help="midi input folder name", type=str)
    parser.add_argument('-o', dest='output_name', help="output folder file", type=str, default=None)
    parser.add_argument('-v', dest='verbose', help="turn on verbose printing", action='store_true', default=False)
    args = parser.parse_args()
    main(args)
