'''
Section.py contains the class Section that contains the details of the results 
of one section (1, 2, or 3) from the user study
'''

class Section(object):
    
    def __init__(self, number, section_data, learn_first):
        self.number = number
        self.learn_first = learn_first
        self.learn = {}
        self.random = {}
        self.q0 = None
        self.q1 = None
        self.q2 = None
        
        self._add_section_data(section_data)
     
    def _add_data_to_result(self, data, result):
        result['coherence'] = int(data[0])
        descrip = data[1].split()
        result['musical'] = int(descrip[0])
        result['interesting'] = int(descrip[1])
        result['complexity'] = int(descrip[2])
        result['structured'] = int(descrip[3])
        result['surprising'] = int(descrip[4])
        result['satisfying'] = int(descrip[5])
        
    def _add_section_data(self, section_data):
        results = [self.learn, self.random] if self.learn_first else [self.random, self.learn]
        
        data = section_data.split('\n')
        self._add_data_to_result(data[0:2], results[0])
        self._add_data_to_result(data[2:4], results[1])

        questions = data[-1].split()
        self.q0 = questions[0]
        self.q1 = questions[1]
        if self.number != 3:
            self.q2 = questions[2]
