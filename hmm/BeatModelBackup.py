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
        score = converter.parseFile(midi_file)
        assert len(score.elements) == 1, 'midi not in expected format: multiple Parts'

        part = score[0]
        assert type(part) == music21.stream.Part, 'midi not in expected format: score not composed of parts'

        return score[0].elements
    
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
        offset = 0
        state = 0
        emission = 0
        for e in elements:
            # time passed if offset changed ==> update transitions
            if e.offset != offset:
                # some beats are skipped ==> state == 0
                num_beats = int((e.offset-offset) / self.sub)
                
                if num_beats > 0:
                    for i in range(num_beats):
                        states.append(state)
                        emissions.append(emission)
                    
                        state = 0
                        emission = 0
                    offset = e.offset
                else:
                    state = 0
                    emission = 0

            # get all notes in this element
            notes = []
            if type(e) == music21.note.Note:
                notes = [e.midi]
            elif type(e) == music21.chord.Chord:
                notes = [p.midi for p in e.pitches]

            # sum up what the state will be by 2**position (see paper)         
            for note in notes:
                if note in self.hidden_notes:
                    state = state + self.state_dict[note]
                if note in self.visible_notes:
                    emission = emission + self.emission_dict[note]                

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
        
    def build_hmm(self):
        self.emission_domain = ghmm.IntegerRange(0, self.num_visible_states)
        self.dist = ghmm.DiscreteDistribution(self.emission_domain)
        self.hmm = ghmm.HMMFromMatrices(self.emission_domain, self.dist, self.trans, self.emission, self.pi)
        
    def test_hmm(self, states, emissions):
        most_likely = self.hmm.viterbi(ghmm.EmissionSequence(self.emission_domain, emissions))[0]
        
        correct = 0
        for i in range(len(most_likely)):
            if most_likely[i] == states[i]:
                correct = correct + 1
        
        accuracy = correct / float(len(most_likely))
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
    bm.add_midi_data(args.input_name)
    bm.build_hmm()
    print bm.hmm
    
    states, emissions = bm.get_states_and_emissions(elements)
    
    print 'hidden notes binary per state'
    for state in states:
        print bm.blist_from_state(state)

    print 'visible notes binary per state'
    for emission in emissions:
        print bm.blist_from_emission(emission)

    
    most_likely = bm.hmm.viterbi(ghmm.EmissionSequence(bm.emission_domain, emissions))[0]
    print 'States\tOut'
    for i in range(len(most_likely)):
        print '%d\t%d' % (states[i], most_likely[i])
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build and test hmms via ghmm.')
    parser.add_argument('-i', dest='input_name', help="midi input file name", type=str)
    parser.add_argument('-o', dest='output_name', help="output tests to file", type=str)
    args = parser.parse_args()
    main(args, 0.25)
