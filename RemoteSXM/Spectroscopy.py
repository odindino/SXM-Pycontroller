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
--    Spectroscopy   --

Set start/end value of (Z)-spectroscopy ramp
Set number of points for (Z)-spectroscopy ramp
Set sample time per spectroscopy point for (Z)
Trigger callback when new data is available
Read acquired spectroscopy data

Set start/end value of (V)-spectroscopy ramp
Set number of points for (V)-spectroscopy ramp
Set sample time per spectroscopy point for (V)

"""

import SXMRemote
import time

print("SXM remote control")

MySXM= SXMRemote.DDEClient("SXM","Remote");

# MySXM.SendWait("SpectPara(xx, "+str(Mode)+");")
# xx is number of User Input Feld in Spectroscopy Form
# 0 is combobox for Mode selection
# meaning is Spectroscopy Mode dependend
# so select Spec mode 1st and then parameter for this mode


# Set Mode of Spectroscopy
# number may vary! by configuration of SXM
# X(z) = 0                      X(t) U-step = 5
# X(U,z) = 1                    X(t) U-step CL = 6
# X(U) CL = 2                   cmAFM X(U) = 7
# X(t) z-step = 3               X(t) noise = 8
# X(t) z-step CL = 4            X(x,y) = 9
Mode=0
#Delay
MySXM.SendWait("SpectPara(0, "+str(Mode)+");") 
delay1=0.040  #dalay after tip is arrived on position
MySXM.SendWait("SpectPara(3, "+str(delay1)+");") 
delay2=0.060  #time for one data point
MySXM.SendWait("SpectPara(4, "+str(delay2)+");")

# Spectroscopy Options --> Acquire
# 16, 32, 64, 128, 256, 512, 1024
DataPoints=32
MySXM.SendWait("SpectPara('Points', "+str(DataPoints)+");")
#AutoSave=On
MySXM.SendWait("SpectPara('AUTOSAVE', 1);")
#AutoRepeat=Off
MySXM.SendWait("SpectPara('Repeat', 0);")

dz1=2  
MySXM.SendWait("SpectPara(5, "+str(dz1)+");")
dz2=-3
MySXM.SendWait("SpectPara(6, "+str(dz2)+");")


#Start Spectroscopy
MySXM.SendWait("SpectStart;")


#Trigger callback when new data is available
def MySpectSave(FileName): # new callback function
    print("My Spect File Is Written "+str(FileName))

MySXM.SpectSave=MySpectSave # use it

#not in every mode
U1=100  
MySXM.SendWait("SpectPara(7, "+str(U1)+");")
U2=-100  
MySXM.SendWait("SpectPara(8, "+str(U2)+");")


