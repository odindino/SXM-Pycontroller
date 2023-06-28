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

### -*- coding: UTF-8 -*-


'''
Read acquired spectroscopy data
'''

import SXMRemote
import MyPlotFile
import matplotlib.pyplot as plt
import warnings
import matplotlib.cbook
warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)

#Start SXM Remote control
MySXM= SXMRemote.DDEClient("SXM","Remote");

#To read acquired spectroscopy data turn autosave on and autorepeat off
#1=on
#0=off
#AutoSave=On
MySXM.SendWait("SpectPara('AUTOSAVE', 1);")
#AutoRepeat=Off
MySXM.SendWait("SpectPara('Repeat', 0);")

#Start Spectroscopy
#MySXM.SendWait("SpectStart;")

def MySpectSave(FileName): # new callback function
    print("My Spect File Is Written "+str(FileName))
    #FileName2=b"C:\\Users\\Data\\170215_XY\\32P_2_20168.dat"
    NewFileName=FileName.decode('utf-8')[:-2]
    print(NewFileName)
    bNewFileName = bytes(NewFileName, 'utf-8')
    print(bNewFileName)
    MyPlotFile.PlotFile(bNewFileName)

MySXM.SpectSave=MySpectSave # use it
MySXM.SendWait("SpectStart;")

