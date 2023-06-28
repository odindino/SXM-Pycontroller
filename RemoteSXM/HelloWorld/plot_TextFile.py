'''
 * (C) Copyright 02/2017 
 *
 * Anfatec Instruments AG 
 * Melanchthonstr. 28 
 * 08606 Oelsnitz/i.V.
 * Germany
 * http://www.anfatec.de/
 *
 * Feel free to use it.
 *
 
'''

import matplotlib.pyplot as plt
import warnings
import matplotlib.cbook
warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)

# load file
headerlines = 2
# with open(b"yourfile.txt") as f:
with open(b".\osc.dat") as f:
    data = f.readlines()[headerlines:]
#print(data)

# seperate columns '\t' is TAB key as seperator
col1 = 0; col2 = 1; col3 = 2; col4 = 3; col5 = 4;
x = [row.split('\t')[col1] for row in data]
y = [row.split('\t')[col3] for row in data]

fig = plt.figure()
sub = fig.add_subplot(111)

# label
sub.set_title("Plot title...")    
sub.set_xlabel('your x label..')
sub.set_ylabel('your y label...')

# plot
sub.plot(x, y, c='r', label='the data')
plt.draw()
plt.pause(0.01) # time to draw
