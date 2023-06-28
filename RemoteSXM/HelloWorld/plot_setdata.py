'''
 * (C) Copyright 02/2017 
 *
 * Anfatec Instruments AG 
 * Melanchthonstr. 28 
 * 08606 Oelsnitz/i.V.
 * Germany
 * http://www.anfatec.de/
 *
 * Processor: AMD A6-3650 APU with Radeon(tm) HD Graphics 2.60 GHz
 * shows about 25 FPS
 * Processor: Intel(R) Core (TM) i7-4771 CPU @3.50GHz
 * shows about 60 FPS
 *
 * Feel free to use it.
 *
 
'''

import matplotlib.pyplot as plt
import numpy as np
import time
import math
import ctypes
import warnings
import matplotlib.cbook
warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)

# create arry of longint 
y=(ctypes.c_long*200)()    

fig = plt.figure()
sub = fig.add_subplot(111)
line, = sub.plot(y)

# fix axis-scale
sub.set_xlim([0,200])        
sub.set_ylim([-120,120])

# timer
tstart = time.time()
num_plots = 0              
while time.time()-tstart < 1: # 1 second
    for index in range(len(y)):
        y[index]=round(100*math.sin(index/20)+15*np.random.random())
    line.set_ydata(y)
    plt.pause(0.0001)
    num_plots += 1
print(str(num_plots)+' loops in one second')

