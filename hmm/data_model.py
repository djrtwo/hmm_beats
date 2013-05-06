'''
author: Daniel Ryan
date: 25 feb 2013
This script is a first attempt at building a transition model for ghmm.
The script assumes that the input midi file is composed of two drums.

NOTE: all lists of midi notes are assumed to be in ascending order.
'''

import sys
import argparse
from music21 import converter
import music21

def get_elements(input_name):
    '''
    Get the individual elements (notes, rests, etc) from the score
    '''
    score = converter.parseFile(input_name)
    assert len(score.elements) == 1, 'midi not in expected format: multiple Parts'
    
    part = score[0]
    assert type(part) == music21.stream.Part, 'midi not in expected format: score not composed of parts'
    
    return score[0].elements

def get_midi_note_set(elements):
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
    
    midi_note_set
    return midi_note_set

def num_states(notes):
    return 2**len(notes)

def build_trans_model(elements, hidden_notes, sub):
    '''
    Build and return the transition probabilities, emission probabilities,
    and initial probabilities
    
    (trans, emission, pi)
    '''
    print get_midi_note_set(elements)
    
    # MxM matrix, M == number of states
    num_hidden = num_states(hidden_notes)  
    trans = [[0]*num_hidden for i in range(num_hidden)]
    
    # MxN matrix, N == number of visible states
    vis_notes = list(get_midi_note_set(elements) - set(hidden_notes))
    vis_notes.sort()
    num_vis = num_states(vis_notes)
    emission = [[0]*num_vis for i in range(num_hidden)]
    
    # build a dictionary with midi-note as key, powers of 2 index as value
    state_dict = {hidden_notes[i] : 2**i for i in range(len(hidden_notes))}
    emission_dict = {vis_notes[i] : 2**i for i in range(len(vis_notes))}
    
    last_state = -1
    offset = 0
    state = 0
    cur_em = 0
    pi = None
    for e in elements:
        # time passed if offset changed ==> update transitions
        if e.offset != offset:
            # hack for generating intial probabilities!
            if pi == None:
                pi = [0.0 for i in range(num_hidden)]
                pi[state] = 1.0
            
            # some beats are skipped
            num_beats = int((e.offset-offset) / sub)
            for i in range(num_beats):
                if last_state >= 0:
                    trans[last_state][state] = trans[last_state][state] + 1
                emission[state][cur_em] = emission[state][cur_em] + 1
                    
                print 'state: %d, emission: %d' % (state, cur_em)
                                
                last_state = state
                state = 0
                cur_em = 0
                offset = e.offset
        
        # get all notes in this element
        notes = []
        if type(e) == music21.note.Note:
            notes = [e.midi]
        elif type(e) == music21.chord.Chord:
            notes = [p.midi for p in e.pitches]
        
        # sum up what the state will be by 2**position (see paper)         
        for note in notes:
            if note in hidden_notes:
                state = state + state_dict[note]
            if note in vis_notes:
                cur_em = cur_em + emission_dict[note]                
    
    # update last timestep
    trans[last_state][state] = trans[last_state][state] + 1
    emission[state][cur_em] = emission[state][cur_em] + 1
    
    print 'state: %d, emission: %d' % (state, cur_em)
    
    print trans
    for i in range(num_hidden):        
        trans[i] = [trans[i][j] / float(sum(trans[i])) for j in range(num_hidden)]
        emission[i] = [emission[i][j] / float(sum(emission[i])) for j in range(num_vis)]
    
    return trans, emission, pi

def main(args, sub):
    elements = get_elements(args.input_name)
    
    trans, emission, pi = build_trans_model(elements, [68], sub)

    print trans
    print emission
    print pi

    # zeroth element is always metronome marking
    tempo = elements[0].number
    
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build transition model used by ghmm.')
    parser.add_argument('-i', dest='input_name', help="midi input file name", type=str)
    parser.add_argument('-o', dest='output_name', help="output arrays to this file", type=str)
    args = parser.parse_args()
    main(args, 0.25)