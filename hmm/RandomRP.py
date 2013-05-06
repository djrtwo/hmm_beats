'''
Child of RowProcessor
Fills rows with random beats
'''

from osc_utils import *
from RowProcessor import RowProcessor
import random
import math
import copy

class RandomRP(RowProcessor):
    
    def __init__(self, num_drum_pads, freq_path=None):
        RowProcessor.__init__(self, num_drum_pads)

        self.drum_freq = []
        if freq_path:
            with open(freq_path) as f:
                freqs = f.read().split()
                for freq in freqs:
                    self.drum_freq.append(float(freq))
            # reverse to match incoming signals
            self.drum_freq.reverse()
            
        self.last_request = None
        self.last_reply = None
        self.last_set_rows = None
    
    @classmethod
    def triangular(cls, freq=0.5):
        """Return a random float in the range (0, 1) inclusive
        with a triangular histogram, and the peak at mode.
        """
        u = random.random()
        if u <= freq:
            return math.sqrt(u*freq)
        else:
            return 1.0 - math.sqrt((1.0-u)*(1.0-freq))
        
    def row_from_freq(self, freq):
        adjusted = self.triangular(freq)
        num_on = int(adjusted * self.beats_per_line)
        print adjusted, num_on
        beats_on = random.sample([i for i in range(self.beats_per_line)], num_on)
        
        return [1 if i in beats_on else 0 for i in range(self.beats_per_line)]
        
    def process_set_rows(self, set_row):
        if self.last_set_rows == self.set_rows:
            if self.last_request == set_row:
                set_row_states = self.last_reply
        else:
            if self.drum_freq:
                set_row_states = self.row_from_freq(self.drum_freq[set_row])
            else:
                set_row_states = [random.randint(0, 1) for i in range(self.beats_per_line)]
         
        print set_row_states
        sendOSCMsg('/set_row', [set_row] + set_row_states)
        
        self.last_request = set_row
        self.last_set_rows = copy.deepcopy(self.set_rows)
        self.last_reply = set_row_states
        self.clear_set_rows()