'''
 * (C) Copyright 04/2023
 *
 * Anfatec Instruments AG 
 * Melanchthonstr. 28 
 * 08606 Oelsnitz/i.V.
 * Germany
 * http://www.anfatec.de/
 * mailbox@anfatec.de
 *
 * Feel free to use it.
 *
 
'''


import win32file
import win32con
import struct
import time
import math
import datetime
import win32event
import matplotlib.pyplot as plt


##############################################################

FILE_DEVICE_UNKNOWN = 0x00000022
METHOD_BUFFERED = 0
FILE_ANY_ACCESS = 0x0000

def CTL_CODE(DeviceType, Access, Function_code, Method):
  Result = (DeviceType << 16 ) | (Access << 14) | (Function_code << 2) | (Method);
  return Result


IOCTL_GO_XY = CTL_CODE(FILE_DEVICE_UNKNOWN,
                           METHOD_BUFFERED,
                           0xF17,
                           FILE_ANY_ACCESS);
IOCTL_SET_CHANNEL = CTL_CODE(FILE_DEVICE_UNKNOWN,
                           METHOD_BUFFERED,
                           0xF18,
                           FILE_ANY_ACCESS);
IOCTL_GET_KANAL = CTL_CODE(FILE_DEVICE_UNKNOWN,
                           METHOD_BUFFERED,
                           0xF0D,
                           FILE_ANY_ACCESS);
IOCTL_SET_OSZI = CTL_CODE(FILE_DEVICE_UNKNOWN,
                          METHOD_BUFFERED,
                          0xF10,
                          FILE_ANY_ACCESS);


###############################################################



def init():
    hDriver = win32file.CreateFile('\\\.\\SXM',     # fileName
                   win32con.GENERIC_WRITE,          # desiredAccess (0,GENERIC_READ,GENERIC_WRITE)
                   0,                               # shareMode (FILE_SHARE_DELETE,FILE_SHARE_READ,FILE_SHARE_WRITE)
                   None,                            # security attributes 
                   win32con.OPEN_EXISTING,          # CreationDisposition (CREATE_NEW,CREATE_ALWAYS,OPEN_EXISTING,OPEN_ALWAYS,TRUNCATE_EXISTING) 
                   win32con.FILE_ATTRIBUTE_NORMAL,  # flagsAndAttributes
                   0);
    GOXY_Event = win32event.CreateEvent(None,       # EventAttributes
                               1,                   # bManualReset
                               0,                   # bInitialState
                               'Global\GOXYWAIT\0') # object name    
    return hDriver


# z, bias, x, y, ..     32, 33, 34,..
def setChannel(Channel, Data):
    D = struct.pack("ll", Channel, Data)
    win32file.DeviceIoControl(hDriver,          # handle device
                          IOCTL_SET_CHANNEL,    # io control code
                          D,                    # in buffer
                          0,                    # out buffer size
                          None)                 # overlapped

# z, bias, x, y, ..     0, -1, -2 , -3, ..
def getChannel(Channel):
    D = struct.pack("l", Channel)               
    result = win32file.DeviceIoControl(hDriver, # handle device
                          IOCTL_GET_KANAL,      # io control code
                          D,                    # in buffer
                          4,                    # out buffer size 
                          None)                 # overlapped
    D2 = struct.unpack_from("l", result)[0]
    return D2


def StopScan():
    DataArray = [0]*39  # init empty array
    DataArray[4] = -1   # Steps -> -1=stop scan
    inbuf = struct.pack('l'*39, *DataArray)    # pack array to buffer
    succ = win32file.DeviceIoControl(hDriver,  # handle device
                          IOCTL_GO_XY,         # io control code
                          inbuf,               # in buffer
                          32*4,                # out buffer (or size)
                          None)
   

def getCurrentPos():
    global xPos   # make it global, otherwise in GoToPos xPos=0
    global yPos   # make it global
    xPos = getChannel(-2)   
    yPos = getChannel(-3)
    print("xPos=",xPos,"yPos =", yPos)


# x/y range: -1e9 ... 1e9
def GoToPos(new_xPos, new_yPos):
    totaltime = 10        # in seconds
    
    getCurrentPos()       # current Pos in xPos / yPos
    dx = new_xPos - xPos  # total way to go in x
    dy = new_yPos - yPos  # total way to go in y
    datapoints = 1000     # nr of datapoints
    StepsPerPoint = (int) (39000 * totaltime / datapoints)  # nr of steps per datapoint
    DataArray = [0]*39    # init array with zeros
    for i in range (7,39):
        DataArray[i] = -2  # -1 bias 8=fasttb ... Nr like at GetChannel
    DataArray[0] = 0       # xPos not used here
    DataArray[1] = 0       # yPos not used here
    DataArray[2] = (int)(dx/datapoints/StepsPerPoint)  # xStepSize
    DataArray[3] = (int)(dy/datapoints/StepsPerPoint)  # yStepSize
    DataArray[4] = StepsPerPoint   # Steps
    DataArray[5] = 50     # NrPixelInLine
    DataArray[6] = 1      # AquChannelListCount

    plotdata = []       # init empty array to fill it with data points in the loop
    inbuf = struct.pack('l'*39, *DataArray)      # convert Array to IN buffer      
    outbuf = win32file.AllocateReadBuffer(32*4)  # Allocate OUT Buffer
    for i in range (1, datapoints):             # loop over datapoints
        succ = win32file.DeviceIoControl(hDriver,   # handle device
                          IOCTL_GO_XY,          # io control code
                          inbuf,                # in buffer
                          outbuf,               # out buffer (or size)
                          None)                 # overlapped
        D2 = struct.unpack_from("l"*32, outbuf) # convert outbuffer to array of longint
        plotdata.append(D2[0])  # add aquired channel value to array (to draw later)
    getCurrentPos()    # print current pos to check 
    plt.plot(plotdata) # plotting by columns
    plt.show()         # open plot window


################################################################
#SXM has to be running
#tested in python 3.4.2
#connect to driver
hDriver = init()

GoToPos(-1e8,-1e8)
#GoToPos(0,0)
#GoToPos(4000000,4000000)



