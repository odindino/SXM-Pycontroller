### -*- coding: UTF-8 -*-
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

"""
--    Bias (Gap Voltage) Control  --

Set/read bias voltage
Set/read preamp bias voltage range
Enable/disable modulation voltage

"""

import SXMRemote
import time

print("SXM remote control")

MySXM= SXMRemote.DDEClient("SXM","Remote");


#Set/read bias voltage [mV]
Bias=20
MySXM.SendWait("FeedPara('Bias', "+str(Bias)+");") 
NewBias=MySXM.GetFeedbackPara('Bias')
print("Bias", str(NewBias))

#Set/read preamp bias voltage range
'''
BiasDiv = 0 --> 10V
BiasDiv = 1 --> 1V
BiasDiv = 2 --> 100mV
'''
BiasDiv=2
MySXM.SendWait("FeedPara('BiasDiv', "+str(BiasDiv)+");") 
NewBiasDiv=MySXM.GetFeedbackPara('BiasDiv')
if NewBiasDiv == 0:
    print("Range [10V]")
elif NewBiasDiv == 1:
    print("Range [1V]")
elif NewBiasDiv == 2:
    print("Range [100mV]")

#Enable/disable modulation voltage
#Multi Channel Lockins LIA1 to LIA3 [mV]
Drive=0.4
MySXM.SendWait("MLockin('LIA1Drive', "+str(Drive)+");") 
