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
import ConfigParser
import copy
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

def val(val):
    return None if val == 'None' else val

def to_bool(val):
    return False if (val == 'False' or val == 'off') else True

class Build_Set(object):
    
    def __init__(self, path, midi, sub):
        self.path = path
        self.midi_notes = set(midi)
        self.sub = sub
        self.midi_files = glob.glob("%s/*.mid" % self.path)
        self.beat_models = {}
        self.st_em = {}
    
    def build(self, all_pi, require_all):
        first_run = True
        for i in range(len(self.midi_notes)+1):
            for combo in combinations(self.midi_notes, i):
                hidden_notes = list(combo)
                hidden_notes.sort()
                visible_notes = list(self.midi_notes - set(hidden_notes))
                visible_notes.sort()

                bm = BeatModel(hidden_notes, visible_notes, self.sub)

                states_emissions = []
                added_files = []
                added = 0
                for midi_file in self.midi_files:
                    st_em = bm.add_midi_file(midi_file, all_pi=all_pi, require_all_notes=require_all)
                    if st_em:
                        self.st_em[midi_file] = st_em
                        added_files.append(midi_file)
                        if first_run:
                            print('ADDED: %s' % midi_file)


                # remove files not added so that process time is less
                # next time around
                if first_run:
                    cp_midi_files = copy.copy(self.midi_files)
                    for midi_file in cp_midi_files:
                        if midi_file not in added_files:
                            self.midi_files.remove(midi_file)
                            print('MIDI FILE REMOVED: %s' % midi_file)
                first_run = False

                # get name and store beatmodel
                name = ''
                for note in self.midi_notes:
                    if note in visible_notes:
                        name = name + '1'
                    else:
                        name = name + '0'
                
                self.beat_models[name] = bm  

class HMM_Builder(object):
    
    def __init__(self, title, require_all, all_pi, min_pi, min_trans, min_emission, reduce_zero, num_sets, build_sets):
        self.title = title
        self.require_all = require_all
        self.all_pi = all_pi
        self.min_pi = min_pi
        self.min_trans = min_trans
        self.min_emission = min_emission
        self.reduce_zero = reduce_zero
        self.num_sets = num_sets
        self.build_sets = build_sets
        self.beat_models = {}
    
    def __str__(self):
        return self.title
    
    @classmethod
    def from_config_path(cls, config_path):
        config = ConfigParser.ConfigParser()
        with open(config_path) as cfg:
            config.readfp(cfg)
        
        title = config.get('Config', 'title')
        require_all = to_bool(config.get('Config', 'require_all'))
        all_pi = to_bool(config.get('Config', 'all_pi'))
        min_pi = float(config.get('Config', 'min_pi'))
        min_trans = float(config.get('Config', 'min_trans'))
        min_emission = float(config.get('Config', 'min_emission'))
        reduce_zero = val(config.get('Config', 'reduce_zero'))
        reduce_zero = float(reduce_zero) if reduce_zero else None
        num_sets = int(config.get('Config', 'num_sets'))
        
        build_sets = []
        for i in range(num_sets):
            path = config.get('Set%s' % i, 'path')
            midi_s = config.get('Set%s' % i, 'midi')
            midi = [int(note) for note in midi_s.split()]
            sub = float(config.get('Set%s' % i, 'sub'))
            
            build_sets.append(Build_Set(path, midi, sub))
        
        return HMM_Builder(title, require_all, all_pi, min_pi, min_trans, min_emission, reduce_zero, num_sets, build_sets)   
    
    @property
    def output_dir(self):
        return  'output/%s' % self.title
        
    @property
    def eval_dir(self):
        return '%s/eval' % self.output_dir
    
    @property
    def model_dir(self):
        return '%s/models' % self.output_dir
        
    def setup_output_path(self):
        try:
            os.mkdir(self.output_dir)
            os.mkdir(self.model_dir)
            os.mkdir(self.eval_dir)
        except OSError:
            print 'output directory already exists...'
            if (utils.query_yes_no('Wipe data and continue?')):
                shutil.rmtree(self.output_dir)
                os.mkdir(self.output_dir)
                os.mkdir(self.model_dir)
                os.mkdir(self.eval_dir)
            else:
                return False

        os.chmod(self.output_dir, 0766)
        os.chmod(self.model_dir, 0766)
        os.chmod(self.eval_dir, 0766)
        return True
        
    def build_all(self):
        for build_set in self.build_sets:
            print build_set.build(self.all_pi, self.require_all)
        
        for label in self.build_sets[0].beat_models:
            # create a meta_bm. notes are pass simply to populate proper size in arrays
            fake_hidden = self.build_sets[0].beat_models[label].hidden_notes
            fake_visible = self.build_sets[0].beat_models[label].visible_notes
            fake_sub = self.build_sets[0].beat_models[label].sub
            meta_bm = BeatModel(fake_hidden, fake_visible, fake_sub)

            # sum the trans, emission, pi
            for build_set in self.build_sets:
                bm = build_set.beat_models[label]
                
                # for all transitions
                for i in range(meta_bm.num_hidden_states):
                    for j in range(meta_bm.num_hidden_states):
                        meta_bm.trans_sum[i][j] = meta_bm.trans_sum[i][j] + bm.trans_sum[i][j]
                        
                # for all emissions
                for i in range(meta_bm.num_hidden_states):
                    for j in range(meta_bm.num_visible_states):
                        meta_bm.emission_sum[i][j] = meta_bm.emission_sum[i][j] + bm.emission_sum[i][j]
                    
                # for all pi
                for i in range(meta_bm.num_hidden_states):
                    meta_bm.pi_sum[i] = meta_bm.pi_sum[i] + bm.pi_sum[i]
                    meta_bm.hidden_state_count[i] = meta_bm.hidden_state_count[i] + bm.hidden_state_count[i]
                    
            # update probabilities of meta_bm
            meta_bm.update_probabilities()
            
            meta_bm.build_hmm()
            meta_bm.hmm_pi_nonzero(self.min_pi)
            meta_bm.hmm_trans_nonzero(self.min_trans)
            meta_bm.hmm_emissions_nonzero(self.min_emission)
            if self.reduce_zero:
                meta_bm.reduce_state_by(prob=self.reduce_zero)
            
            self.beat_models[label] = meta_bm
            print "%s :::: %s" % (label, meta_bm)

    def test_models(self):
        with open('%s/results.txt' % self.eval_dir, 'w') as f:
            for label in self.beat_models:
                
                f.write('%s ' % label)
                for num in self.beat_models[label].hidden_state_count:
                    freq = float(num) / sum(self.beat_models[label].hidden_state_count)
                    f.write('%f ' % freq)
                bm = self.beat_models[label]
                f.write('\n')
                
                # test each midi file in each build_set
                for build_set in self.build_sets:
                    for midi_file in build_set.midi_files:
                        states = build_set.st_em[midi_file][0]
                        emissions = build_set.st_em[midi_file][1]
                        accuracy = bm.test_hmm(states, emissions)
                        note_accuracy = bm.test_each_hidden(states, emissions)
                        
                        f.write('%s\t%s\n' % (midi_file, accuracy))

                        f.write('%s\t' % midi_file)
                        if len(note_accuracy) == 0:
                            f.write('None')
                        for accur in note_accuracy:
                            f.write('%s ' % accur)
                        f.write('\n')

                f.write('\n')

    def save_models(self):
        for label in self.beat_models:
            self.beat_models[label].hmm.write('%s/%s.xml' % (self.model_dir, label))
    
    def output_drum_freq(self):
        '''
        NOTE FOR NOW ASSUMES ALL SETS HAVE SAME NUMBER OF NOTES
        '''
        
        num_notes = len(self.build_sets[0].midi_notes)
        visible_label = '1' * num_notes
        note_freq = {i : 0 for i in range(num_notes)}
        total_beats = 0
        
        for build_set in self.build_sets:
            midi_notes = list(build_set.midi_notes)
            midi_notes.sort()
            
            visible_bm = build_set.beat_models[visible_label]
            for i, midi_note in enumerate(midi_notes):
                note_freq[i] = note_freq[i] + visible_bm.note_count[midi_note]
            total_beats = total_beats + visible_bm.beat_count
        
        with open('%s/note_freq.txt' % self.output_dir, 'w') as f:
            for i in range(num_notes):
                frequency = note_freq[i] / float(total_beats)
                print frequency
                f.write('%s ' % frequency)
            f.write('\n')
            
                

def main(args):
    hmm_builder= HMM_Builder.from_config_path(args.config_path)
    verboseprint = utils.verbose_printing(args.verbose)
    
    if not hmm_builder.setup_output_path():
        return
    
    hmm_builder.build_all()
    hmm_builder.test_models()
    hmm_builder.save_models()    
    hmm_builder.output_drum_freq()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build and test hmms via ghmm.')
    parser.add_argument('-i', dest='config_path', help="configuration file", type=str)
    parser.add_argument('-v', dest='verbose', help="turn on verbose printing", action='store_true', default=False)
    
    args = parser.parse_args()
    main(args)