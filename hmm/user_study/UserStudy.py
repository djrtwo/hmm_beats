'''
Container object to store a user study
'''

from Section import Section
from us_util import *

class User(object):
    
    def __init__(self):
        self.age = None
        self.student = None
        self.musician = None
        self.cs = None

        self.performance = None
        self.composition = None
        self.drumming = None
        self.electronic_music = None
        self.controllers = None
        self.sequencers = None

class General(object):
    
    def __init__(self):
        self.intelligent = None
        self.use = None
        self.pref = None
        self.composition = None
        self.performance = None
        self.ext = None
        self.agent = None
        self.names = None
        
    def __str__(self):
        return '''
More Intelligent:\t%s
Likely to Use:\t%s
Pref Descript:\t%s
Useful in Comp:\t%s
\t\t%s
Useful in Perf:\t%s
\t\t%s
How to extend:\t%s
Thoughts on agent:\t%s
Potential Names:\t%s        
''' % (self.intelligent, self.use, self.pref, self.composition[0], self.composition[1], self.performance[0], self.performance[1], self.ext, self.agent, self.names)

class UserStudy(object):

    LEARN = 'LEARN'
    RANDOM = 'RANDOM'
    
    def __init__(self, data_file):
        with open(data_file, 'r') as df:
            data = df.read()
        
        data = data.split('\n\n')
        
        user_info = data[0].split('\n')
        self.user = User()
        for i, user_line in enumerate(user_info):
            user_line = user_line.split()
            if i == 0:
                self.id = user_line[0]
                self.learn_first = True if user_line[1] == 'LEARN' else False
            elif i == 1:
                self.user.age = user_line[0]
                self.user.student = self.eval_YN(user_line[1])
                self.user.musician = self.eval_YN(user_line[2])
                self.user.cs = self.eval_YN(user_line[3])
            elif i == 2:
                self.user.performance = int(user_line[0])
                self.user.composition = int(user_line[1])
                self.user.drumming = int(user_line[2])
                self.user.electronic_music = int(user_line[3])
                self.user.controllers = int(user_line[4])
                self.user.sequencers = int(user_line[5])
        
        self.sections = [Section(i, data[i], self.learn_first) for i in range(1, 4)]
        
        general_data = data[4].split('\n')
        self.gen = General()
        self.gen.intelligent = self.convert_AB(general_data[0], self.learn_first)
        self.gen.use = self.convert_AB(general_data[1], self.learn_first)
        self.gen.pref = general_data[2]
        self.gen.composition = (self.eval_YN(general_data[3].split()), ' '.join(general_data[3].split()[1:]))
        self.gen.performance = (self.eval_YN(general_data[4].split()), ' '.join(general_data[4].split()[1:]))
        self.gen.ext = general_data[5]
        self.gen.agent = general_data[6]
        self.gen.names = general_data[7].split()
        
    def __str__(self):
        return str(self.id)
        

    @classmethod
    def eval_YN(cls, yn):
        return True if yn == 'Y' else False
        
    @classmethod
    def convert_AB(cls, ab, learn_first):
        '''
        convert A/B to 1 (LEARN) or 2 (RANDOM) depending on if learn_first is True or False
        '''
        if ab == 'A':
            if learn_first:
                return cls.LEARN
            else:
                return cls.RANDOM
        elif ab == 'B':
            if learn_first:
                return cls.RANDOM
            else:
                return cls.LEARN
        return None

    @classmethod
    def import_range(cls, start=2, stop=12, path='forms/'):
        us = []
        for i in range(start, stop+1):
            file_name = path + 'user%s' % i
            us.append(cls(file_name))
        
        return us
                
    def is_musician(self, min_perf=5, min_comp=5):
        if self.user.musician:
            if self.user.performance >= min_perf:
                if self.user.composition >= min_comp:
                    return True
        return False

    def has_electronic(self, min_elect=5):
        return self.user.electronic_music >= min_elect

    def is_electronic_musician(self, min_elect=5, min_perf=5, min_comp=5):
        return self.has_electronic(min_elect) and self.is_musician(min_perf, min_comp)

                
def main():
    studies = UserStudy.import_range()
    show_intel_use(studies, UserStudy.is_musician, 'MUSICIAN')
    print
    print '-'*60
    print
    show_intel_use(studies, UserStudy.has_electronic, 'ELECTRONIC')
    print
    print '-'*60
    print
    show_intel_use(studies, UserStudy.is_electronic_musician, 'ELECT_MUSICIAN')

    musicians = []
    for study in studies:
        if study.is_musician():
            musicians.append(study)

    print
    print '-'*60
    print

    show_averages(musicians)

if __name__ == '__main__':
    main()
        
        
        
        
        