'''
author: Daniel Ryan
date: 10 mar 2013
BeatModel object takes a list of music21 midi elements, builds an hmm,
and provides methods and data access on the inputs and model
'''

import argparse
from music21 import converter
import music21
import ghmm

class BeatModel(object):
    
    def __init__(self, hidden_notes, visible_notes, sub=0.25):
        self.hidden_notes = hidden_notes
        self.visible_notes = visible_notes
        self.sub = sub
        
        # MxM matrix, M == number of hidden states
        self.trans_sum = [[0]*self.num_hidden_states for i in range(self.num_hidden_states)]
        self.trans = [[0]*self.num_hidden_states for i in range(self.num_hidden_states)]

        # MxN matrix, N == number of visible states
        self.emission_sum = [[0]*self.num_visible_states for i in range(self.num_hidden_states)]
        self.emission = [[0]*self.num_visible_states for i in range(self.num_hidden_states)]
        
        # 1xM matrix, probility of start state
        self.pi_sum = [0 for i in range(self.num_hidden_states)]
        self.pi = [0 for i in range(self.num_hidden_states)]
        
        # build a dictionary with midi-note as key, powers of 2 index as value
        self.state_dict = {self.hidden_notes[i] : 
                                2**i for i in range(len(self.hidden_notes))}
        self.emission_dict = {self.visible_notes[i] : 
                                2**i for i in range(len(self.visible_notes))}
        
        self.note_count = {self.visible_notes[i] : 0 for i in range(len(self.visible_notes))}
        self.beat_count = 0
        
        self.hidden_state_count = [0] * self.num_hidden_states
        
        self.midi_files = []
        
        self.emission_domain = None
        self.dist = None
        self.hmm = None
    
    @classmethod
    def all_notes_in_files(cls, midi_files):
        '''
        return a set() of all midi notes contained in list of midi_files
        '''
        all_notes = set()
        for midi_file in midi_files:
            all_notes = all_notes.union(cls.midi_note_set(cls.elements(midi_file)))
            print all_notes
            
        return all_notes
        
    @classmethod
    def midi_note_set(cls, elements):
        '''
        return a set() of all the midi notes in the score
        '''
        midi_note_set = set()
        for e in elements:
            if type(e) == music21.note.Note:
                midi_note_set.add(e.midi)
            elif type(e) == music21.chord.Chord:
                for p in e.pitches:
                    midi_note_set.add(p.midi)

        return midi_note_set    
    
    @classmethod
    def elements(cls, midi_file):
        '''
        Get the individual elements (notes, rests, etc) from the score
        '''
        # print midi_file
        
        try:
            score = converter.parseFile(midi_file)
        except:
            return False
            
        assert len(score.elements) == 1, 'midi not in expected format: multiple Parts'
                
        part = score[0]
        assert type(part) == music21.stream.Part, 'midi not in expected format: score not composed of parts'

        # for v in part[3]:
        #     print v
        
        # return part[2].elements    
        
        part.flattenUnnecessaryVoices(force=True)
            
        return part.elements
    
    @property
    def num_visible_states(self):
        return 2**len(self.visible_notes)
        
    @property
    def num_hidden_states(self):
        return 2**len(self.hidden_notes)

    def state_from_list(self, note_list):
        return sum([self.state_dict[note] for note in note_list])
    
    def emission_from_list(self, note_list):
        return sum([self.emission_dict[note] for note in note_list])    
        
    def blist_from_state(self, state):
        return [(state >> i) & 1 for i in range(len(self.hidden_notes))]
        
    def blist_from_emission(self, emission):
        return [(emission >> i) & 1 for i in range(len(self.visible_notes))]
        
    def get_states_and_emissions(self, elements):
        states = []
        emissions = []
        notes = []
        offset = 0
        state = 0
        emission = 0
        for e in elements:
            # time passed if offset changed ==> update transitions
            if e.offset != offset:
                # some beats are skipped ==> state == 0
                num_beats = int((e.offset-offset) / self.sub)
                
                # sum up what the state will be by 2**position (see paper)
                note_set = set(notes)         
                for note in note_set:
                    if note in self.hidden_notes:
                        state = state + self.state_dict[note]
                    if note in self.visible_notes:
                        emission = emission + self.emission_dict[note]
                        self.note_count[note] = self.note_count[note] + 1
                
                if num_beats > 0:
                    for i in range(num_beats):
                        states.append(state)
                        emissions.append(emission)
                        notes = []
                        state = 0
                        emission = 0
                        self.beat_count = self.beat_count + 1
                    offset = e.offset
                    
                # do not count notes on fraction other than multiples of sub    
                else:
                    notes = []
                    state = 0
                    emission = 0

            # get all notes in this element
            if type(e) == music21.note.Note:
                notes.append(e.midi)
            elif type(e) == music21.chord.Chord:
                for p in e.pitches:
                    notes.append(p.midi)    

        # update last timestep
        states.append(state)
        emissions.append(emission)

        return states, emissions
        
    def add_midi_data(self, midi_file):
        '''
        add a midi file data to the transition probabilities, emission probabilities,
        and initial probabilities for the BeatModel
        '''
        elements = self.elements(midi_file)
        states, emissions = self.get_states_and_emissions(elements)
        
        # update sums
        last_state = -1
        for i, state in enumerate(states):
            if i == 0:
                self.pi_sum[state] = self.pi_sum[state] + 1
            else:
                self.trans_sum[last_state][state] = self.trans_sum[last_state][state] + 1
            self.emission_sum[state][emissions[i]] = self.emission_sum[state][emissions[i]] + 1
            
            last_state = state
        
        # update probabilities
        for i in range(self.num_hidden_states):        
            self.trans[i] = [self.trans_sum[i][j] / float(sum(self.trans_sum[i])) if sum(self.trans_sum[i]) > 0 else 0.0 for j in range(self.num_hidden_states)]
            self.emission[i] = [self.emission_sum[i][j] / float(sum(self.emission_sum[i])) if sum(self.emission_sum[i]) > 0 else 0.0 for j in range(self.num_visible_states)]
            self.pi[i] = self.pi_sum[i] / float(sum(self.pi_sum))

        # track that this file was added
        self.midi_files.append(midi_file)
        
        return states, emissions
    
    def add_elements(self, elements=None, states=None, emissions=None):
        '''
        add a midi file data to the transition probabilities, emission probabilities,
        and initial probabilities for the BeatModel
        '''
        if not states and not emissions:
            states, emissions = self.get_states_and_emissions(elements)
        
        # update sums
        last_state = -1
        for i, state in enumerate(states):
            self.hidden_state_count[state] = self.hidden_state_count[state] + 1
            if i == 0:
                self.pi_sum[state] = self.pi_sum[state] + 1
            else:
                self.trans_sum[last_state][state] = self.trans_sum[last_state][state] + 1
            self.emission_sum[state][emissions[i]] = self.emission_sum[state][emissions[i]] + 1
            
            last_state = state
        
        return states, emissions
    
    def update_probabilities(self):
        for i in range(self.num_hidden_states):        
            self.trans[i] = [self.trans_sum[i][j] / float(sum(self.trans_sum[i])) if sum(self.trans_sum[i]) > 0 else 0.0 for j in range(self.num_hidden_states)]
            self.emission[i] = [self.emission_sum[i][j] / float(sum(self.emission_sum[i])) if sum(self.emission_sum[i]) > 0 else 0.0 for j in range(self.num_visible_states)]
            self.pi[i] = self.pi_sum[i] / float(sum(self.pi_sum))      
        
    def add_elements_wrap(self, elements):
        '''
        wrapping the data like this does not affect anything but the intial start probabilities
        in that case, should we just add every beat as a start state?
        '''
        
        states, emissions = self.get_states_and_emissions(elements)
        
        beats_per_bar = 1.0 / self.sub
        num_wraps = int(len(states) / beats_per_bar)
        
        for i in range(num_wraps):
            offset = int(i * beats_per_bar)
            states_wrap = states[offset:] + states[:offset]
            emissions_wrap = emissions[offset:] + emissions[:offset]
            self.add_elements(states=states_wrap, emissions=emissions_wrap)
        
        return states, emissions
    
    def add_all_pi(self, elements, but_start=False):
        # states, emissions = self.get_states_and_emissions(elements)
        # 
        # for i, state in enumerate(states):
        #     if i != 0 or not but_start:
        #         self.pi_sum[state] = self.pi_sum[state] + 1
        
        for state in range(self.num_hidden_states):
            self.pi_sum[state] = self.pi_sum[state] + 1
        
    def add_midi_file(self, midi_file, wrap=False, all_pi=False, require_all_notes=False):
        elements = self.elements(midi_file)
        if not elements:
            return False
        
        note_set = self.midi_note_set(elements)
        
        if require_all_notes:
            if not note_set.issuperset(set(self.hidden_notes + self.visible_notes)):
                return False
        
        # track that this file was added
        self.midi_files.append(midi_file)    
        
        if all_pi:
            self.add_all_pi(elements, but_start=True)
        
        if wrap:
            return self.add_elements_wrap(elements)

        return self.add_elements(elements)
             
    def build_hmm(self):
        self.update_probabilities()

        self.emission_domain = ghmm.IntegerRange(0, self.num_visible_states)
        self.dist = ghmm.DiscreteDistribution(self.emission_domain)
        self.hmm = ghmm.HMMFromMatrices(self.emission_domain, self.dist, self.trans, self.emission, self.pi)

    def hmm_pi_nonzero(self, min_pi=0.01):
        if not self.hmm:
            raise Exception('hmm_pi_nonzero can only be called after build_hmm has successfully built an hmm for BeatModel')
            
        for i in range(self.num_hidden_states):
            pi = self.hmm.getInitial(i)
            if pi < min_pi:
                self.hmm.setInitial(i, min_pi)
                
        self.hmm.normalize() 
   
    def hmm_trans_nonzero(self, min_trans=0.01):
        if not self.hmm:
            raise Exception('hmm_trans_nonzero can only be called after build_hmm has successfully built an hmm for BeatModel')

        for i in range(self.num_hidden_states):
            for j in range(self.num_hidden_states):
                trans = self.hmm.getTransition(i,j)
                if trans < min_trans:
                    self.hmm.setTransition(i, j, min_trans)

        self.hmm.normalize()   
       
    def hmm_emissions_nonzero(self, min_emission=0.01):
        if not self.hmm:
            raise Exception('hmm_emissions_nonzero can only be called after build_hmm has successfully built an hmm for BeatModel')
            
        for i in range(self.num_hidden_states):
            emissions = self.hmm.getEmission(i)
            emissions = [emission if emission > min_emission else min_emission for emission in emissions]
            self.hmm.setEmission(i, emissions)
            
        self.hmm.normalize()
    
    def reduce_state_by(self, prob=0.5, state=0):
        if not self.hmm:
            raise Exception('reduce_zero_by can only be called after build_hmm has successfully built an hmm for BeatModel')
            
        for i in range(self.num_hidden_states):
            self.hmm.setTransition(i, state, self.hmm.getTransition(i, state) * prob)
        
        self.hmm.normalize()
        
    def test_hmm(self, states, emissions):
        most_likely = self.hmm.viterbi(ghmm.EmissionSequence(self.emission_domain, emissions))[0]
        
        correct = 0
        for i in range(len(most_likely)):
            if most_likely[i] == states[i]:
                correct = correct + 1
        
        accuracy = correct / float(len(most_likely))
        return accuracy
        
    def test_each_hidden(self, states, emissions):
        most_likely = self.hmm.viterbi(ghmm.EmissionSequence(self.emission_domain, emissions))[0]
        
    
        correct = [0 for i in range(len(self.hidden_notes))]
        for i in range(len(most_likely)):
            state_blist = self.blist_from_state(states[i])
            likely_blist = self.blist_from_state(most_likely[i])
            
            for j in range(len(state_blist)):
                if state_blist[j] == likely_blist[j]:
                    correct[j] = correct[j] + 1
        
        beat_len = len(most_likely)    
        accuracy = [correct[i] / float(beat_len) for i in range(len(correct))]
        
        return accuracy    

def main(args, sub):
    # first just do it by splitting the note set in half
    # add the for loop at does all the combinations after
    elements = BeatModel.elements(args.input_name)
    midi_notes = list(BeatModel.midi_note_set(elements))
    
    # hack to run a sample distribution of hidden/visible
    # full feature auto-test script to come
    hidden_notes = midi_notes[:len(midi_notes)/2]
    print 'hidden', hidden_notes
    visible_notes = midi_notes[len(midi_notes)/2:]
    print 'visible', visible_notes
    
    bm = BeatModel(hidden_notes, visible_notes)
    bm.add_midi_file(args.input_name, all_pi=True)
    bm.build_hmm()
    print bm.hmm
    
    # bm_wrap = BeatModel(hidden_notes, visible_notes)
    # bm_wrap.add_midi_file(args.input_name, wrap=True)
    # bm_wrap.build_hmm()
    # print bm_wrap.hmm
    
    # states, emissions = bm.get_states_and_emissions(elements)
    # 
    # print 'hidden notes binary per state'
    # for state in states:
    #     print bm.blist_from_state(state)
    # 
    # print 'visible notes binary per state'
    # for emission in emissions:
    #     print bm.blist_from_emission(emission)
    # 
    # print 'state accuracy =\t %s' % bm.test_hmm(states, emissions)    
    # print 'note accuracy  =\t %s' % bm.test_each_hidden(states, emissions)
    # 
    # most_likely = bm.hmm.viterbi(ghmm.EmissionSequence(bm.emission_domain, emissions))[0]
    # print 'States\tOut'
    # for i in range(len(most_likely)):
    #     print '%d\t%d' % (states[i], most_likely[i])
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build and test hmms via ghmm.')
    parser.add_argument('-i', dest='input_name', help="midi input file name", type=str)
    parser.add_argument('-o', dest='output_name', help="output tests to file", type=str)
    args = parser.parse_args()
    main(args, 0.25)
        