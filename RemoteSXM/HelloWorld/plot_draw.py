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
 * shows about 7 FPS
* Processor: Intel(R) Core (TM) i7-4771 CPU @3.50GHz
 * shows about 16 FPS
 *
 * Feel free to use it.
 *
 
'''

import matplotlib.pyplot as plt
import time
import random
import numpy as np
import math
import ctypes
import warnings
import matplotlib.cbook
warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)

# create array of long
y=(ctypes.c_long*100)()      

fig = plt.figure()
sub = fig.add_subplot(111)    

# Turn interactive mode on
plt.ion()                 

# timer
tstart = time.time()
num_plots = 0         
while time.time()-tstart < 1:        # 1 second
  for index in range(len(y)):
    #generate sinus data with noise 
    y[index]=round(150*math.sin(index/10)+30*np.random.random())
  sub.cla()   #clear axis, slow
  sub.plot(y)
  plt.pause(0.001)
  num_plots += 1
print(str(num_plots)+' loops in one second')



  

