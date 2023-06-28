'''
 * (C) Copyright 10/2021 
 *
 * Anfatec Instruments AG 
 * Melanchthonstr. 28 
 * 08606 Oelsnitz/i.V.
 * Germany
 * http://www.anfatec.de/
 *
 * Terms and Condition look to licenses
 * 
'''

import win32file
import win32con
import struct

##############################################################

FILE_DEVICE_UNKNOWN = 0x00000022
METHOD_BUFFERED = 0
FILE_ANY_ACCESS = 0x0000

def CTL_CODE(DeviceType, Access, Function_code, Method):
  Result = (DeviceType << 16 ) | (Access << 14) | (Function_code << 2) | (Method);
  return Result

IOCTL_SET_CHANNEL = CTL_CODE(FILE_DEVICE_UNKNOWN,
                           METHOD_BUFFERED,
                           0xF18,
                           FILE_ANY_ACCESS);
IOCTL_GET_KANAL = CTL_CODE(FILE_DEVICE_UNKNOWN,
                           METHOD_BUFFERED,
                           0xF0D,
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

################################################################
#SXM has to be running
#tested in python 3.4.2
#connect to driver
hDriver = init()


# ramp on channel
# 10us each iteration
wChannel = 34        # 33=Bias, 34=X
for i in range (1, 1000):
    Data = i*1000000
    setChannel(wChannel, Data)



# Set Bias and read back    
wChannel = 33        # 33=Bias, 34=X
rChannel = -1        # -1 Bias
Data = 1000000000 # ~8V
setChannel(wChannel, Data)
print(getChannel(rChannel)) # should give back data
