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

import win32file
import ctypes

# load file:
filename=r".\osc.dat"
print('file: '+filename)

buf = win32file.AllocateReadBuffer(8192)      # buffer size ... 2^13
# Data can be read from the file and the file pointer can be moved 
wmode = win32file.GENERIC_READ                # access to a template file

# Creates or opens a file &
# returns a handle (can be used to access the object)
h = win32file.CreateFile(
            filename,                         # CTSTR lpFileName,
            wmode,                            # DWORD dwDesiredAccess,
            win32file.FILE_SHARE_READ,        # DWORD dwShareMode,
            None,                             # LPSECURITY_ATTRIBUTES lpSecurityAttributes,
            win32file.OPEN_EXISTING,          # DWORD dwCreationDisposition,
            win32file.FILE_ATTRIBUTE_NORMAL,  # DWORD dwFlagsAndAttributes,
            0,                                # HANDLE hTemplateFile
            )

# Reads a string from a file
(Status, s) = win32file.ReadFile(
            h,                                # hFile/Handle to the file
            4,                                # buffer/bufSize
            None                              # None = not overlapped
            ) 
if (Status!=0):
  print( "Readfile returned %d" % Status)

# in case it is an array of long
# s --> pointer to different ctypes data type
#ptr=ctypes.cast(s, ctypes.POINTER(ctypes.c_long))
#print (ptr[0])
#print (ptr)
#print (((109*256+32)*256+48)*256+49)

# in case it is an array of long
# s --> pointer to different ctypes data type
ptr=ctypes.cast(s, ctypes.POINTER(ctypes.c_char))

# read the first 4 letters
for i in range (0, 4):
  print(ptr[i])



