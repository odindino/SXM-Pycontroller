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

FileName = b"C:\\Users\\Data\\170215_XY\\32P_2_20168.dat"

def PlotFile(FileName):
    # load file, skip header line(s)
    headerlines = 1
    # with open(b"yourfile.txt") as f:
    with open(FileName) as f:
        file = f.readlines()
        header = file[:headerlines]
        data = file[headerlines:]
        #print(header)
        #print(data) 

    # seperate columns '\t' is TAB key as seperator
    col1 = 0; col2 = 1; col3 = 2; col4 = 3; col5 = 4;
    
    xCol = col1
    yCol = col4
    
    #read header to describe the labels
    xLabel = [row.split('\t')[xCol] for row in header]
    yLabel = [row.split('\t')[yCol] for row in header]
    
    #read data
    x = [row.split('\t')[xCol] for row in data]
    y = [row.split('\t')[yCol] for row in data]


    fig = plt.figure()
    sub = fig.add_subplot(111)

    #label
    sub.set_title("Spectroscopy")
    sub.set_xlabel(xLabel)
    sub.set_ylabel(yLabel)

    # plot
    sub.plot(x, y, c='r', label='the data')
    plt.draw()
    plt.pause(0.01) # time to draw

