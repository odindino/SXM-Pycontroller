'''
 * (C) Copyright 02/2020
 *
 * Anfatec Instruments AG 
 * Melanchthonstr. 28 
 * 08606 Oelsnitz/i.V.
 * Germany
 * http://www.anfatec.de/
 *
 * Processor: Intel(R) Core (TM) i7-4771 CPU @3.50GHz
 * shows about 32 FPS
 *
 * Feel free to use it.
 *
 
'''

import SXMRemote

import threading
from win32 import win32file
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
import random
import numpy
import math
import ctypes
from ctypes import POINTER, byref, c_ulong
from ctypes.wintypes import BOOL, HWND, MSG, UINT


class MyDataClass():

    def __init__(self):
        self.XData = (ctypes.c_long*100)()
        self.YData1=(ctypes.c_long*100)()
        self.YData2=(ctypes.c_long*100)()


class MyPlotClass():
    
    def __init__(self, dataClass):
        self._dataClass = dataClass

        fig = plt.figure()
        self.sub = fig.add_subplot(121)
        self.sub2 = fig.add_subplot(122)
        
        #self.hLine, = plt.plot(0, 0)
        #self.hLine2, = plt.plot(0, 0)
        self.hLine, = self.sub.plot(dataClass.YData1)
        self.hLine2, = self.sub2.plot(dataClass.YData2)
        
        self.ani = FuncAnimation(plt.gcf(), self.run, interval = 100, repeat=True)


    def run(self, i):

        Max1=max(self._dataClass.YData1)
        Min1=min(self._dataClass.YData1)

        Max2=max(self._dataClass.YData2)
        Min2=min(self._dataClass.YData2)

        # axes scale
        self.sub.set_xlim([0, 100])        
        self.sub.set_ylim([Min1-32000, Max1+32000])

        self.sub2.set_xlim([0, 100])        
        self.sub2.set_ylim([Min2-32000, Max2+32000])        

        # set new data to line
        self.hLine.set_data(self._dataClass.XData, self._dataClass.YData1)
        self.hLine2.set_data(self._dataClass.XData, self._dataClass.YData2)

        # show plot
        self.hLine.axes.relim()
        self.hLine.axes.autoscale_view()
        self.hLine2.axes.relim()
        self.hLine2.axes.autoscale_view()


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
        x = 100
        while True:
            
            (Status, data) = win32file.ReadFile(self.h, 4200*16*4 , None )
            if (Status!=0):
               print( "Readfile returned %d" % Status)
            if (len(data)>x) :  
                ptr=ctypes.cast(data, ctypes.POINTER(ctypes.c_long))

            for i in range(x):
                # 2 data channels
                # 8 last bits = channel number
                channel = ptr[i]
                channel = channel & 0xff

                if (channel==0):
                    # first channel
                    self._dataClass.YData1[i] = ptr[i]
                else:
                    # second channel
                    self._dataClass.YData2[i] = ptr[i]
                self._dataClass.XData[i] = i
                
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
# MySXM.SendWait("Collect('ChList', 0);")
# for 2 data channels :MySXM.SendWait("Collect('ChList', 0, 1);")
MySXM.SendWait("Collect('ChList', 0, 3);")

#enable disable
#Switch on/off
On=1 #  0=false=Off else e.g.=1=true=On
MySXM.SendWait("Collect('On', "+str(On)+");")

data = MyDataClass()
plotter = MyPlotClass(data)
fetcher = MyDataFetchClass(data)

fetcher.start()
plt.show()
