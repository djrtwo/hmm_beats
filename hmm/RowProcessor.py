'''
Parent class.
Child class must implement process_set_rows
'''

from music21 import converter
import music21
import ghmm

class RowProcessor(object):
    
    def __init__(self, num_drum_pads):
        self.num_drum_pads = num_drum_pads
        self.beats_per_line = 64 / num_drum_pads

        self.set_rows = [None for i in range(self.num_drum_pads)]
        self.save_rows = [None for i in range(self.num_drum_pads)]
        
        self.num_drums = num_drum_pads
        
    def process_set_rows(self, set_row):
        pass
        
    def clear_set_rows(self):
        self.set_rows = [None for i in range(self.num_drum_pads)]    
    
    def set_row(self, row_num, row_data):
        self.set_rows[row_num] = row_data
        
        incompletes = []
        for i in range(self.num_drum_pads):
            if self.set_rows[i] == None:
                incompletes.append(i)
                
        if len(incompletes) == 1:
            self.process_set_rows(incompletes[0])
    
