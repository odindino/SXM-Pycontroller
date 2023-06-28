'''
 * (C) Copyright 02/2020
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

import SXMRemote
import threading
#import win32file
from win32 import win32file #manu
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
import random
import numpy as np
import math
import ctypes
from ctypes import POINTER, byref, c_ulong
from ctypes.wintypes import BOOL, HWND, MSG, UINT

class MyDataClass():

    def __init__(self):
        self.XData = (ctypes.c_long*100)()
        self.YData=(ctypes.c_long*100)()

class MyPlotClass():
    
    def __init__(self, dataClass):
        self._dataClass = dataClass
        self.hLine, = plt.plot(0, 0)
        self.ani = FuncAnimation(plt.gcf(), self.run, interval = 100, repeat=True)


    def run(self, i):  
        self.hLine.set_data(self._dataClass.XData, self._dataClass.YData)
        self.hLine.axes.relim()
        self.hLine.axes.autoscale_view()



class MyDataFetchClass(threading.Thread):

    def __init__(self, dataClass):
        threading.Thread.__init__(self)
        self._dataClass = dataClass
        self._period = 0.1
        self._nextCall = time.time()

        fname=r"\\.\SXM"
        self.h = win32file.CreateFile(
            fname,                           #  CTSTR lpFileName,
            win32file.GENERIC_READ,          #  DWORD dwDesiredAccess,
            win32file.FILE_SHARE_READ,       #  DWORD dwShareMode,
            None,                            #  LPSECURITY_ATTRIBUTES lpSecurityAttributes,
            win32file.OPEN_EXISTING,         #  DWORD dwCreationDisposition,
            win32file.FILE_ATTRIBUTE_NORMAL, #  DWORD dwFlagsAndAttributes,
            0,                               #  HANDLE hTemplateFile
        )


    def run(self):

        while True:
            (Status, s) = win32file.ReadFile(self.h, 4200*16*4 , None) #None = not overlapped
            if (Status!=0):
                print( "Readfile returned %d" % Status)

            if (len(s)>100) :
                # cast C array of long -> python   
                ptr=ctypes.cast(s, ctypes.POINTER(ctypes.c_long))
                for i in range(100):
                    # add data to data class
                    self._dataClass.XData[i] = i
                    self._dataClass.YData[i] = ptr[i]

            # sleep until next execution
            self._nextCall = self._nextCall + self._period;
            time.sleep(self._nextCall - time.time())


        
                
MySXM= SXMRemote.DDEClient("SXM","Remote");

# Set Collect Frequency in Hz
Freq=10000
MySXM.SendWait("Collect('Freq', "+str(Freq)+");")

# Set Channels to collect
# 0 = IN A
# 1 = LIAY                   
# 2 = LIAX
# 3 = SyncRadius
# 4 = IN_B
# 5 = SyncAngle
# 6 = Lia2X
# 7 = Lia2Y
# 8 = Lia3X
# 9 = Lia3Y
# 10 = Lia4X
# 11 = Lia4Y
# 12 = zSlowData
# 13 = Frame/Line Sync
# 14 = zFastData
# 15 = WaveCounte
# 16 = LIA1R
# 17 = LIA1Phi
# max. 14 Channels/ Nr. of Channels * freq shoud <1MHz (depends on speed of PC)
# for 1 channel:
Channel = 3
MySXM.SendWait("Collect('ChList', " + str(Channel) + ");")
# for 2 data channels :MySXM.SendWait("Collect('ChList', 0, 1);")
#MySXM.SendWait("Collect('ChList', 0, 2);")

#enable disable
#Switch on/off
On=1 #  0=false=Off else e.g.=1=true=On
MySXM.SendWait("Collect('On', "+str(On)+");")

data = MyDataClass()
plotter = MyPlotClass(data)
fetcher = MyDataFetchClass(data)

fetcher.start()
plt.show()
