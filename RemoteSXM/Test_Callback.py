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


import SXMRemote
import time

print("SXM remote control")

MySXM= SXMRemote.DDEClient("SXM","Remote");

# string="FeedPara('Bias',-10);"
# MySXM.execute(string, 5000);

def MyScanIsOn():
    print('myScan is on');
    
def MyScanIsOff():
    print('myScan is off');    

MySXM.ScanOnCallBack = MyScanIsOn
MySXM.ScanOffCallBack = MyScanIsOff

# GoXYStr="Goxy(0.2,0.7);"
# MySXM.execute(GoXYStr, 5000);
MySXM.callback(b"ScanOn")

