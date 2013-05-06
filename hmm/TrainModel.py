'''
author: Daniel Ryan
date: 28 mar 2013
TrainModel is a subclass of BeatModel
It takes a list of music21 midi elements, builds an hmm,
and provides methods and data access on the inputs and model
'''
from BeatModel import BeatModel

class TrainModel(BeatModel):

    def __init__(self, hidden_notes, visible_notes, sub=0.25):
        BeatModel.__init__(self, sub)
        
        self.hidden_notes = hidden_notes
        self.visible_notes = visible_notes
        self.sub = sub
        
        # build a dictionary with midi-note as key, powers of 2 index as value
        self.state_dict = {self.hidden_notes[i] : 
                                2**i for i in range(len(self.hidden_notes))}
        self.emission_dict = {self.visible_notes[i] : 
                                2**i for i in range(len(self.visible_notes))}
                
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

    @property
    def num_visible_states(self):
        return 2**len(self.visible_notes)


def main(args, sub):
    # first just do it by splitting the note set in half
    # add the for loop at does all the combinations after
    elements = TrainModel.elements(args.input_name)
    midi_notes = list(BeatModel.midi_note_set(elements))
    
    # hack to run a sample distribution of hidden/visible
    # full feature auto-test script to come
    hidden_notes = midi_notes[:len(midi_notes)/2]
    print 'hidden', hidden_notes
    visible_notes = midi_notes[len(midi_notes)/2:]
    print 'visible', visible_notes
    
    bm = BeatModel(hidden_notes, visible_notes)
    bm.add_midi_file(args.input_name)
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
