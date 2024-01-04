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

# -*- coding: UTF-8 -*-

"""
Trigger callback when new data file has been written
Read name and path of data file written

Trigger callback when scan starts/stops
Start/stop scanning
Check if scan is in progress
"""


import SXMRemote
import time
print("SXM remote control")
# Connect to remote controll
MySXM = SXMRemote.DDEClient("SXM", "Remote")


# callback when new data file has been written
# Read name and path of data file written
def MyNewFileIsWritten(FileName):  # new callback function
    # get used ini-filename and read from it
    Path = MySXM.GetIniEntry('Save', 'Path')
    print('MyNewFileIsWritten ' + Path + str(FileName))


MySXM.SaveIsDone = MyNewFileIsWritten  # use it
'''
#callback for Start and stop scan
def MyScanIsOn():
    print('MyScanIsOn');
def MyScanIsOff():
    print('MyScanIsOff');    

MySXM.ScanOnCallBack = MyScanIsOn   # use it
MySXM.ScanOffCallBack = MyScanIsOff # use it
'''

# Start/stop scanning
MySXM.SendWait("ScanPara('Scan',1);")  # <>0 = start
time.sleep(1)  # in second
MySXM.SendWait("ScanPara('Scan',0);")  # =0 = stop
time.sleep(1)  # in second

# Check if scan is in progress
print(MySXM.GetScanPara('Scan'))  # 1.0=on
