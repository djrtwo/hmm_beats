'''
author: Daniel Ryan
date: 11 mar 2013
Script takes a directory path as input.  All .mid files in the path
are then used to build and test all combinations of BeatModels.

Each .mid file is assumed to be composed of the same midi note structure.
'''

import glob
import os
import argparse
import shutil
from itertools import combinations

import utils
from BeatModel import BeatModel

verboseprint = None

def setup_directories(data_dir, output_dir):
    os.chdir(data_dir)
    
    try:
        os.mkdir(output_dir)
        os.mkdir('%s/models' % output_dir)
        os.mkdir('%s/eval' % output_dir)
    except OSError:
        print 'output directory already exists...'
        if (utils.query_yes_no('Wipe data and continue?')):
            shutil.rmtree(output_dir)
            os.mkdir(output_dir)
            os.mkdir('%s/models' % output_dir)
            os.mkdir('%s/eval' % output_dir)
        else:
            return False
    
    os.chmod(output_dir, 0766)
    os.chmod('%s/models' % output_dir, 0766)
    os.chmod('%s/eval' % output_dir, 0766)
    return True
    

def main(args):
    verboseprint = utils.verbose_printing(args.verbose)
    
    data_dir = '%s' % args.input_name
    output_dir = args.output_name if args.output_name else 'out'
    if (not setup_directories(data_dir, output_dir)):
        return
    
    midi_files = glob.glob("*.mid")
    print midi_files
    all_notes = BeatModel.all_notes_in_files(midi_files)
    print all_notes
    
    # evaluate and write to file
    with open('%s/eval/train.txt' % output_dir, 'w') as f:
    
        # run test for all combinations of hidden notes
        for i in range(len(all_notes)):
            for combo in combinations(all_notes, i):
                hidden_notes = list(combo)
                hidden_notes.sort()
                visible_notes = list(all_notes - set(hidden_notes))
                visible_notes.sort()
                
                bm = BeatModel(hidden_notes, visible_notes, args.sub)
        
                states_emissions = []
                for midi_file in midi_files:
                    states_emissions.append(bm.add_midi_file(midi_file, all_pi=args.all_pi))
        
                bm.build_hmm()
                bm.hmm_pi_nonzero(args.min_pi)
                bm.hmm_trans_nonzero(args.min_trans)
                bm.hmm_emissions_nonzero(args.min_emission)
            
                name = ''
                for note in all_notes:
                    if note in visible_notes:
                        name = name + '1'
                    else:
                        name = name + '0'
                
                # write hmm to file
                hidden_string = ''.join('%s-' % note for note in hidden_notes)[:-1]
                visible_string = ''.join('%s-' % note for note in visible_notes)[:-1]
                #             hidden_visible_string = '%s_%s' % (hidden_string, visible_string)
                bm.hmm.write('%s/models/%s.xml' % (output_dir, name))
                verboseprint(bm.hmm)
        
                # test hmm and write results to file
                hidden_string = ''.join('%s, ' % note for note in hidden_notes)[:-2] if hidden_notes else None
                visible_string = ''.join('%s, ' % note for note in visible_notes)[:-2]
                f.write('%s\n' % name)
                
                verboseprint('HIDDEN_NOTES:\t%s' % hidden_string)
                verboseprint('VISIBLE_NOTES:\t%s' % visible_string)
                verboseprint('FILE\t\tACCURACY')
            
                for j, midi_file in enumerate(midi_files):
                    accuracy = bm.test_hmm(states_emissions[j][0], states_emissions[j][1])
                    note_accuracy = bm.test_each_hidden(states_emissions[j][0], states_emissions[j][1])
                    f.write('%s\t%s\n' % (midi_file, accuracy))
                    
                    f.write('%s\t' % midi_file)
                    if len(note_accuracy) == 0:
                        f.write('None')
                    for accur in note_accuracy:
                        f.write('%s ' % accur)
                    f.write('\n')

                    verboseprint('%s\t%s' % (midi_file, accuracy))
                    verboseprint('%s\t%s' % (midi_file, note_accuracy))
            
                f.write('\n')    
                verboseprint('')
                verboseprint('-----------------------------------------')
                verboseprint('')
            
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build and test hmms via ghmm.')
    parser.add_argument('-i', dest='input_name', help="midi input folder name", type=str)
    parser.add_argument('-o', dest='output_name', help="output folder file", type=str, default=None)
    parser.add_argument('--sub', dest='sub', help="smallest subdivision", type=float, default=0.25)
    parser.add_argument('-v', dest='verbose', help="turn on verbose printing", action='store_true', default=False)
    parser.add_argument('--all_pi', dest='all_pi', help='enable every state seen as start state', action='store_true', default=False)
    parser.add_argument('--min_pi', dest='min_pi', help='minimum start state (before renormalizing). defaults to 0.01', type=float, default=0.01)
    parser.add_argument('--min_trans', dest='min_trans', help='minimum transition probability (before renormalizing). defaults to 0.01', type=float, default=0.01)
    parser.add_argument('--min_emission', dest='min_emission', help='minimum emission probability (before renormalizing). defaults to 0.01', type=float, default=0.01)
    args = parser.parse_args()
    main(args)