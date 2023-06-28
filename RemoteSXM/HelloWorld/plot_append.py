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
 * shows about 15 FPS
* Processor: Intel(R) Core (TM) i7-4771 CPU @3.50GHz
 * shows about 27 FPS
 *
 * Feel free to use it.
 *
 
'''

import pylab
import time
import random
import matplotlib.pyplot as plt
import ctypes
import math
import numpy as np
import warnings
import matplotlib.cbook
warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)

data=[]
fig = plt.figure()
sub = fig.add_subplot(111)
line, = sub.plot(data)

# fix axis-scale
sub.set_xlim([0,4000])  
sub.set_ylim([-120,120])

#plt.ion() # interactive mode on

# timer
tstart = time.time()
num_plots = 0                
while time.time()-tstart < 1:   # 1 second
  for index in range (100):     # y size
    y=round(100*math.sin(index/100*2*3.141)+15*np.random.random())
    data.append(y)   #add data  
    line.set_ydata(data)
    line.set_xdata(range(len(data)))
    #plt.draw() # anti flicker? but slows down
    #data=[] # erases the data --> screen clear
  plt.pause(0.001)
  num_plots += 1
print(str(num_plots)+' loops in one second')

   


