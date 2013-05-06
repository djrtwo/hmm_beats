import matplotlib.pyplot as plt
import numpy as np
import random
import math

def main():
    freq = 0.2
    x0 = np.linspace(0,.5,25)
    y0 = np.sqrt(x0*freq)
    
    x1 = np.linspace(0.5, 1.0, 25)
    y1 = 1.0 - np.sqrt((1.0-x1)*(1.0-freq))
    
    # plt.axis((0.0, 1.0, 0.0, 1.0))
    # plt.plot(x0, y0)
    # plt.plot(x1, y1)
    
    test_len = 1000
    num_buckets = 17
    buckets = [0]*num_buckets
    for i in range(test_len):
        u = random.random()
        if u <= freq:
            bucket = int(math.sqrt(u*freq) * num_buckets)
            buckets[bucket] = buckets[bucket] + 1
        else:
            bucket =  int((1.0 - math.sqrt((1.0-u)*(1.0-freq))) * num_buckets)
            buckets[bucket] = buckets[bucket] + 1
    
    x2 = range(num_buckets)
    y2 = [bucket for bucket in buckets]
    
    
    fig = plt.figure()
    ax = plt.subplot(111)
    ax.bar(x2, y2, align='center')
    
    ax.set_xticks(range(num_buckets))
    plt.xlabel('Number of beats returned')
    plt.ylabel('Number of experiments')
    # plt.plot(x2, y2)
    plt.show()
    

if __name__ == '__main__':
    main()