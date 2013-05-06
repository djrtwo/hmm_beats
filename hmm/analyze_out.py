'''
author: Daniel Ryan
date: 6 apr 2013
Script takes a test_data.py test output file as input.  
Script provides a series of functions to analyze the output.
 
'''

import argparse
import copy
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

class AccSet(object):
    
    def __init__(self, acc_list):
        self.acc_list = acc_list
    
    @property
    def num_drums(self):
        return len(self.acc_list[0].model_label)
        
    def plot_num_drums_vs_total_acc(self):
        name_dict = {}       
        names = self.acc_list[0].file_names
        for name in names:
            name_dict[name] = [[] for i in range(2)]
        
        for acc in self.acc_list:
            for i, total in enumerate(acc.total_accs):
                name_dict[acc.file_names[i]][0].append(acc.num_hidden)
                name_dict[acc.file_names[i]][1].append(total)
                
        f = plt.figure()
        f.canvas.set_window_title("Total Accuracy for Each Model")
        plt.xlabel('Hidden Drums per Model')
        plt.ylabel('Accuracy')
        plt.axis((0, self.num_drums, 0.0, 1.0))
        ax = f.add_subplot(111)
        for name in name_dict:
            ax.plot(name_dict[name][0], name_dict[name][1], marker='o', markersize=10, label=name)
        
        plt.legend(loc='lower left')
        plt.xticks([i for i in range(0, self.num_drums)])
        plt.yticks([i/10.0 for i in range(0, 11)])
        # plt.scatter(num_accur[0], num_accur[1], figure=f)
        
    def plot_num_drums_vs_avg_total_acc(self):
        num_accur = [[] for i in range(2)]
        freqs = [[] for i in range(self.num_drums+1)]
        for acc in self.acc_list:
            num_visible = sum([int(digit) for digit in acc.model_label])
            num_hidden = len(acc.model_label) - num_visible
            
            num_accur[0].append(num_hidden)
            num_accur[1].append(acc.avg_total_acc)
            
            freqs[num_hidden].append(max(acc.state_freq))
        
        averages = [sum(freqs[i])/len(freqs[i]) for i in range(self.num_drums+1)]
        
        print averages
        
        f = plt.figure()
        f.canvas.set_window_title("Average Total State Accuracy") 
        plt.xlabel('Hidden Drums per Model')
        plt.ylabel('Accuracy')
        plt.axis((0, self.num_drums, 0.0, 1.0))
        plt.xticks([i for i in range(0, self.num_drums)])
        plt.yticks([i/10.0 for i in range(0, 11)])
        plt.scatter(num_accur[0], num_accur[1], figure=f)
        plt.scatter(range(self.num_drums+1), averages)
        plt.grid()
        
    def plot_num_drums_vs_avg_avg_drum_acc(self):
        num_accur = [[] for i in range(2)]
        # which_drum = [num_accur[:] for i in range(self.num_drums)]
        
        for acc in self.acc_list:
            num_visible = sum([int(digit) for digit in acc.model_label])
            num_hidden = len(acc.model_label) - num_visible
            
            if num_hidden > 0:
                num_accur[0].append(num_hidden)
                num_accur[1].append(acc.avg_avg_drum_acc)
        
        f = plt.figure()
        f.canvas.set_window_title("Average Average Drum Accuracy")
        plt.xlabel('Hidden Drums per Model')
        plt.ylabel('Accuracy')
        plt.axis((0, self.num_drums, 0.0, 1.0))
        plt.xticks([i for i in range(0, self.num_drums)])
        plt.yticks([i/10.0 for i in range(0, 11)])
        plt.scatter(num_accur[0], num_accur[1], figure=f)
        plt.grid()
        
    def plot_num_drums_vs_avg_drum_acc(self, bad_drums=[], bad_color='k'):
        num_accur = [[] for i in range(2)]
        which_drum = [copy.deepcopy(num_accur) for i in range(self.num_drums)]
        finish = copy.deepcopy(which_drum)
        
        for acc in self.acc_list:
            num_visible = sum([int(digit) for digit in acc.model_label])
            num_hidden = len(acc.model_label) - num_visible
                              
            if num_hidden > 0:
                for i, index in enumerate(acc.hidden_index):
                    total = 0.0
                    for drum_acc in acc.drum_accs:
                        total = total + drum_acc[i]
                    
                    which_drum[index][0].append(num_hidden)
                    which_drum[index][1].append(total / len(acc.drum_accs))
                    
        for z, drum in enumerate(which_drum):
            for i in range(self.num_drums):
                if i in drum[0]:
                    total = sum([accur for j, accur in enumerate(drum[1]) if drum[0][j] == i])
                    occurences = sum([1 for j in drum[0] if j == i])
                    finish[z][0].append(i)
                    finish[z][1].append(total / occurences)
            
        cm = plt.get_cmap('gist_rainbow')
        f = plt.figure()    
        f.canvas.set_window_title("Individual Drum Accuracy")   
        NUM_COLORS = len(finish)
        ax = f.add_subplot(111)
        ax.set_color_cycle([cm(1.*i/NUM_COLORS) for i in range(NUM_COLORS)])
        # for i in range(NUM_COLORS):
        #     color = cm(1.*i/NUM_COLORS)  # color will now be an RGBA tuple
        #     ax.plot(np.arange(10)*(i+1))
        
        
        
        plt.xlabel('Hidden Drums per Model')
        plt.ylabel('Accuracy')
        plt.axis((1, self.num_drums, 0.0, 1.0)) 
        for i, drum in enumerate(finish):    
            if i in bad_drums:
                ax.plot(drum[0], drum[1], label='Drum%s' % i, marker='x', markersize=9, color=bad_color)
            else:
                ax.plot(drum[0], drum[1], label='Drum%s' % i, marker='x', markersize=9)
                
        plt.xticks([i for i in range(0, self.num_drums)])
        plt.yticks([i/10.0 for i in range(0, 11)])
        plt.legend(loc='lower left')
        plt.grid()
            
    def find_common_hidden_below(self, accuracy):
        common = set([i for i in range(self.num_drums)])
        
        for acc in self.acc_list:
            for total_accuracy in acc.total_accs:
                if total_accuracy < accuracy:
                    hidden = set([i for i, digit in enumerate(acc.model_label) if digit == '0'])
                    common = common.intersection(hidden)
        
        return common
    
    def plot_bad_drums(self, accuracy, bad_color='k'):
        bad_drums = self.find_common_hidden_below(accuracy)
        self.plot_num_drums_vs_avg_drum_acc(bad_drums=bad_drums, bad_color=bad_color)
        
        
    def plot_individual_highlight_specific(self, ind_index, highlight_index, color='r'):
        num_accur = [[] for i in range(2)]
        high_num_accur = [[] for i in range(2)]
        
        for acc in self.acc_list:
            if acc.model_label[ind_index] == '0':
                if acc.model_label[highlight_index] == '1':
                    high_num_accur[0].append(acc.num_hidden)
                    high_num_accur[1].append(acc.avg_specific_drum(acc.hidden_index[ind_index]))
                else:
                    num_accur[0].append(acc.num_hidden)
                    num_accur[1].append(acc.avg_specific_drum(acc.hidden_index[ind_index]))
                    
        f = plt.figure()
        f.canvas.set_window_title("Drum%s Accuracy with models with visible Drum%s highlighed" % (ind_index, highlight_index))
        plt.xlabel('Hidden Drums per Model')
        plt.ylabel('Accuracy')
    
    
        plt.scatter(num_accur[0], num_accur[1], color='k', marker='x', label='Drum%s not visible' % highlight_index)
        plt.scatter(high_num_accur[0], high_num_accur[1], color=color, marker='o', label='Drum%s visible' % highlight_index)
    
        # ax = f.add_subplot(111)
        # ax.plot(num_accur[0], num_accur[1], color='k')
        # ax.plot(high_num_accur[0], high_num_accur[1], color=color)
    
        plt.axis((0, self.num_drums, 0.0, 1.0))
        plt.xticks([i for i in range(0, self.num_drums)])

        plt.yticks([i/10.0 for i in range(0, 11)])
        plt.legend(loc='lower left')
        plt.grid()
        
        

class Acc(object):
    
    def __init__(self, model_label, file_names, total_accs, drum_accs, state_freq):
        self.model_label = model_label
        self.file_names = file_names
        self.total_accs = total_accs
        self.drum_accs = drum_accs
        self.state_freq = state_freq
        
    def __str__(self):
        return '''
model_label:\t\t %s
file_names:\t\t %s
total_accuracies:\t %s
avg total_acc:\t\t %s
avg drum_accs:\t\t %s
avg total_drum_acc:\t %s
drum_accuracies:\t %s''' % (self.model_label, self.file_names, self.total_accs, self.avg_total_acc, self.avg_drum_accs, self.avg_avg_drum_acc, self.drum_accs)

    @property
    def avg_total_acc(self):
        return sum(self.total_accs) / len(self.total_accs)
    
    @property
    def avg_drum_accs(self):
        return [sum(drum_acc) / len(drum_acc) for drum_acc in self.drum_accs]
    
    def avg_specific_drum(self, index):
        return sum([drum_acc[index] for drum_acc in self.drum_accs]) / len(self.drum_accs)
    
    @property    
    def avg_avg_drum_acc(self):
        if self.avg_drum_accs:
            return sum(self.avg_drum_accs) / len(self.avg_drum_accs)
        else:
            return None
         
    @property
    def num_visible(self):
        return sum([int(digit) for digit in self.model_label])
        
    @property
    def num_hidden(self):
        return len(self.model_label) - self.num_visible
            
    @property
    def hidden_index(self):
        '''
        a list of the indexes of the model_label that are hidden
        useful for accertaining which drum in the drum accuracies list is which
        ''' 
        return [i for i, digit in enumerate(self.model_label) if digit == '0']
        
def parse_input(input_lines):
    acc_list = []
    
    model_label = None
    file_names = []
    total_accs = []
    drum_accs = []
    state_freq= []
    for line in input_lines:
        split_line = line.split()
        if not model_label:
            if split_line:
                model_label = split_line[0]
                state_freq = [float(spl) for spl in split_line[1:]]
                
            total_line = True
            file_names = []
            total_accs = []
            drum_accs = []
        elif len(split_line) > 0:
            if total_line == True:
                total_accs.append(float(split_line[-1]))
                file_names.append(split_line[0])
            else:
                if split_line[-1] != 'None':
                    drum_acc = [float(split_line[i]) for i in range(1, len(split_line))]
                    drum_accs.append(drum_acc)
            
            total_line = not total_line
        else:
            acc_list.append(Acc(model_label, file_names, total_accs, drum_accs, state_freq))
            model_label = None
        
    return acc_list

def main(args):

    with open(args.input_name, 'r') as to_analyze:
        file_lines = to_analyze.read().split('\n')

        acc_list = parse_input(file_lines)
        acc_set = AccSet(acc_list)

        # for acc in acc_set.acc_list:
        #     print acc
        # 
        # print acc_set.find_common_hidden_below(0.2)
        #         
        acc_set.plot_num_drums_vs_avg_total_acc()
        acc_set.plot_num_drums_vs_avg_avg_drum_acc()
        acc_set.plot_num_drums_vs_avg_drum_acc()
        acc_set.plot_num_drums_vs_total_acc()
        # 
        # acc_set.plot_bad_drums(0.2)
        
        # for i in range(4):
        #     if i != 1:
        #         acc_set.plot_individual_highlight_specific(1, i)
        # 
        plt.show()
        # for acc in acc_list:
        #     print acc
        # 
        # print 
        # print 'avg_total_acc std_dev:\t %s' % np.std([acc.avg_total_acc for acc in acc_list])
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build and test hmms via ghmm.')
    parser.add_argument('-i', dest='input_name', help="test_data.py output file to analyze", type=str)
    parser.add_argument('-v', dest='verbose', help="turn on verbose printing", action='store_true', default=False)
    args = parser.parse_args()
    main(args)

