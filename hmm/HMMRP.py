'''
RowProcess that interfaces with HMMs
'''

from osc_utils import *
from music21 import converter
import music21
import ghmm
from RowProcessor import RowProcessor
from itertools import combinations
import random

class HMMRP(RowProcessor):
    
    def __init__(self, num_drum_pads, hmm):
        RowProcessor.__init__(self, num_drum_pads)
        self.hmm = hmm
        
        self.num_drums = 0
        for hmm_label in self.hmm.hmms:
            self.num_drums = max(self.num_drums, len(hmm_label))
        
        if self.num_drums > self.num_drum_pads:
            self.num_drums = self.num_drum_pads
            
    def process_set_rows(self, set_row):
        hidden = [set_row]
        visible = []
        for i, row in enumerate(self.set_rows):
            if row == [0]*self.beats_per_line:
                hidden.append(i)
            elif i != set_row:
                visible.append(i)
        print hidden
        print visible

        # model_label = ''
        # visible_rows = []
        # # get model label and collect visible rows in proper order
        # # drums in hmm is in reverse order of incoming rows
        # for i in range(self.num_drum_pads-1, self.num_drum_pads-self.num_drums-1, -1):
        #     if i in hidden:
        #         model_label = model_label + '0'
        #     else:
        #         model_label = model_label + '1'
        #         visible_rows.append(self.set_rows[i])

        set_row_states = [0]*self.beats_per_line
        
        all_combos = []
        for i in range(len(visible)-1, -1, -1):
            for combo in combinations(visible, i):
                all_combos.append(list(combo))
        random.shuffle(all_combos)
        
        all_combos = [visible] + all_combos
        
        for vis_ind in all_combos:
            print 'TRY VISIBLE:', vis_ind 
            model_label = ''
            this_hidden = []
            visible_rows = []
            # get model label and collect visible rows in proper order
            # drums in hmm is in reverse order of incoming rows
            for j in range(self.num_drum_pads-1, self.num_drum_pads-self.num_drums-1, -1):
                if j in vis_ind:
                    model_label = model_label + '1'
                    visible_rows.append(self.set_rows[j])
                else:
                    model_label = model_label + '0'
                    this_hidden.append(j)
                    
            
            
            print model_label
            print visible_rows
            hidden_states = self.hmm.get_hidden(model_label, visible_rows)
            print 'state_sequence: ', hidden_states

            this_hidden.sort(reverse=True)
            num_note = this_hidden.index(set_row)
            set_row_states = [(hidden_states[i] >> num_note) & 1 for i in range(len(hidden_states))]

            if set_row_states != [0]*self.beats_per_line:
                print 'SENDING ROWS'
                print set_row_states
                sendOSCMsg('/set_row', [set_row] + set_row_states)
                self.clear_set_rows()
                return
        
        print 'ALL ZEROS, no row sent'
        self.clear_set_rows()

    def process_save_rows(self):
        # do a reverse instead of the horrible backwardsness of 
        # process_set_rows().  change the other method after testing
        self.save_rows.reverse()

        face = True
        for hmm_label in self.hmm.hmms:  
            hidden_rows = []
            visible_rows = []

            for i in range(self.num_drum_pads):
                if hmm_label[i] == '0':
                    hidden_rows.append(self.save_rows[i])
                elif hmm_label[i] == '1':
                    visible_rows.append(self.save_rows[i])

            emissions = self.hmm.build_states_from_rows(visible_rows)
            self.hmm.train_hmm(hmm_label, emissions)

        # remove data from rows
        self.save_rows = [None for i in range(self.num_drum_pads)]

    def save_row(self, row_num, row_data):
        self.save_rows[row_num] = row_data

        incompletes = []
        for i in range(self.num_drum_pads):
            if self.save_rows[i] == None:
                incompletes.append(i)

        if len(incompletes) == 0:
            self.process_save_rows()