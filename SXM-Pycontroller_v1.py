"""
In this file, we use python function to simplify and replace the code of examples.
We can make SXM become a class, and the function are the actions of SXM.
"""

import SXMRemote
import time

import win32file
import win32con
import struct
import time
import math
import datetime
import win32event
import matplotlib.pyplot as plt
import numpy as np
import os


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
MySXM= SXMRemote.DDEClient("SXM","Remote");


################################################################
#  Write by Zi-Liang Yang
################################################################
# ramp on channel1
# 10us each iteration
# w_bias_Channel = 33        # 33=Bias, 34=X
# r_bias_Channel = -1        # -1 Bias

# various scale factors
Topo_SF = -8.92967E-7
bias_SF = 9.397E-6
IttoPC_SF = 8.47371E-18

## setting and reading from channel
# set bias
def setBias(bias): # bias in mV
    w_bias_Channel = 33
    bias_raw = int(bias/bias_SF)
    setChannel(w_bias_Channel, bias_raw)

# read bias
def getBias():
    r_bias_Channel = -1
    bias_raw = getChannel(r_bias_Channel) # should give back data
    bias = bias_raw * bias_SF
    return bias

# read It_to_PC
def getIttoPC():
    r_IttoPC_Channel = 12
    IttoPC_raw = getChannel(r_IttoPC_Channel)
    IttoPC = IttoPC_raw*IttoPC_SF
    return IttoPC

# read Topo
def getTopo():
    r_Topo_Channel = 0
    Topo_raw = getChannel(r_Topo_Channel)
    Topo = Topo_raw*Topo_SF
    return Topo

# general setting
def enableFb(sign=0):
    MySXM.SendWait("FeedPara('Enable', " + str(sign) + ");")
    FbOn = MySXM.GetFeedbackPara('Enable')
    print (FbOn)
    #0=On 1=off
    if (FbOn==0) : #on
        print("Feedback on")
    else:
        print("Feedback off")

# measurement functions
def STSmeasurement(Vstart, Vend, Tacquire, Tdelay, Npoint):
    Tdelay = Tdelay/1000 # convert to ms
    # get current bias
    current_bias = getBias()

    # Vstart, Vend in mV
    # Tacquire, Tdelay in ms
    # Npoint is int
    # First calculate the bias list, close the feedback
    # set the bias according to the bias_list
    # Then read It_to_PC in the time of Tacquire, append the read It_to_PC to the It_single_point_list
    # After Tacquire, calculate the average of It_single_point_list, append the average to the It_to_PC_list
    # Then delay for Tdelay, repeat the above steps for Npoint times

    # set bias list for measurement
    bias_list = np.linspace(Vstart, Vend, Npoint)
    It_to_PC_list = []
    bias_get_list = []
    # close feedback
    enableFb(1)
    # set bias
    for bias in bias_list:
        setBias(bias)
        bias_get_list.append(getBias())
        It_single_point_list = []
        # set the delay of each It measurement to 100us
        for _ in range(0, int(Tacquire)):
            It_single_point_list.append(getIttoPC())
            time.sleep(0.001) # 100us
        It_to_PC_list.append(np.mean(It_single_point_list))
        time.sleep(Tdelay)
    # set back to the original bias
    setBias(current_bias)
    enableFb(0)
    It_to_PC_list = np.array(It_to_PC_list)

    return bias_get_list, It_to_PC_list

# file management
def saveSTSdata(bias_get_list, It_to_PC_list):
    # write the file type become .dat
    # the first column is bias, the second column is It_to_PC
    # the file name is the current time
    # the file is saved in the current directory
    
    # get current time
    now = datetime.datetime.now()
    # get current directory
    current_dir = os.getcwd()
    # set file name
    file_name = str(now.year) + str(now.month) + str(now.day) + str(now.hour) + str(now.minute) + str(now.second) + ".dat"
    # set file path
    file_path = os.path.join(current_dir, file_name)
    # save data
    # np.savetxt(file_path, np.transpose([bias_get_list, It_to_PC_list]), delimiter='\t', header='Bias(mV)\tIt_to_PC(A)')
    # print("Data saved in " + file_path)
    with open(file_name, 'w') as f:
        for i in range(len(bias_get_list)):
            f.write(str(bias_get_list[i]) + ',' + str(It_to_PC_list[i]) + '\n')
    f.close()
    
# bias_get_list, It_to_PC_list = STSmeasurement(400, -400, 3, 3, 201)
# saveSTSdata(bias_get_list, It_to_PC_list)
# enableFb(0)