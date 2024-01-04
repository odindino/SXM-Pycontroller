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

"""
--    Tip conditioning --    

Set conditioning Mode
Set gap voltage during conditioning
Set dive dz during conditioning
Set time for conditioning
Do it

"""

import SXMRemote
import time

print("SXM remote control")

MySXM= SXMRemote.DDEClient("SXM","Remote");

#Set tip conditioning mode
#Mode
#0=BiasPulse
#1=Tip Dive
#2=Tip Dive with Bias
#3=z-Pulse with Bias
Mode=0
MySXM.SendWait("TipCond('Mode', "+str(Mode)+");")
if Mode == 0:
    print("Mode [BiasPulse]")
elif Mode == 1:
    print("Mode [Tip Dive]")
elif Mode == 2:
    print("Mode [Tip Dive with Bias]")
elif Mode == 3:
    print("Mode [z-Pulse with Bias]")

#Change gap voltage during tip conditioning, Bias
GapVoltage=300  # in Units from SXM e.g. mV
MySXM.SendWait("TipCond('Bias', "+str(GapVoltage)+");")

#Set time for conditioning [ms], Time
DiveTime=400
MySXM.SendWait("TipCond('Time', "+str(DiveTime)+");") 

#dive dz during conditioning (Topo) [nm]
dz=4
MySXM.SendWait("TipCond('Dive', "+str(dz)+");") 

#Do it, run
MySXM.SendWait("TipCond('Do', 1);") 
print ("running")

