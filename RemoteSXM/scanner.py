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
 
++++++++++++++++++++++++++++++++++++++++++++'''

### -*- coding: UTF-8 -*-

"""
Set/read scan area rotation angle
Set/read scan area width
Set/read scan area height
Set/read number of scan points per scan lines
Set/read number of scan lines
Set/read scan area offset
Set/read raster time

?Enable/disable scan line retrace
!Enable/disable up/down scan mode

Trigger callback when scan reaches end of scan line
Trigger callback when scan finishes retrace of scan line
Erigger callback when scan area has been scanned completely in “up” direction
Trigger callback when scan area has been scanned completely in “down” direction

Set/read drift compensation vector
Enable/disable drift compensation

Enable/disable plane subtraction scan mode
Set plane subtraction scan slope (X/Y)

Read the current tip position
Remember current tip position 	
    --> Used in conjunction with “Return to remembered position” below
Return to remembered position
Set new target tip position 
   --> Used in conjunction with “Move tip to new position” below
Move tip to new position
Trigger callback when tip arrives at target position
Trigger operation when tip arrives at target position 
   --> A configured operation will be automatically triggered when the tip arrives at a target position. The customer uses this to start regular single point spectroscopy and atom manipulation operations.
"""

import SXMRemote
#import time

print("SXM remote control")
MySXM= SXMRemote.DDEClient("SXM","Remote");

#Set/read scan area rotation angle
MySXM.SendWait("ScanPara('Angle',-50);");
print (MySXM.GetScanPara('Angle'));

#Set/read scan area width
MySXM.SendWait("ScanPara('Range',300);");
print (MySXM.GetScanPara('Range'));

#Set/read number of scan points per scan lines
MySXM.SendWait("ScanPara('Pixel',128);");
print (MySXM.GetScanPara('Pixel'));

#Pixel Density Ratio=Pixel Density in Line / Pixel Density in Col
MySXM.SendWait("ScanPara('PixelDensity', 1.5);");
print (MySXM.GetScanPara('PixelDensity'));


#AspectRatio=Width/height = Image Format
MySXM.SendWait("ScanPara('AspectRatio', 1.4);");
print (MySXM.GetScanPara('AspectRatio'));

#x/y-center
#Set/read scan area offset
MySXM.SendWait("ScanPara('x',113);");
MySXM.SendWait("ScanPara('Y',234);");
print (MySXM.GetScanPara('X'));
print (MySXM.GetScanPara('Y'));

#speed
#Set/read raster time
MySXM.SendWait("ScanPara('Speed',3);");
print (MySXM.GetScanPara('Speed'));

#Enable/disable up/down scan mode
#???

#Trigger callback when scan finishes retrace of scan line
#Trigger callback when scan area has been scanned completely in “up” direction
#Trigger callback when scan area has been scanned completely in “down” direction
def MyScanIsCompleted(Value):
    print('MyScanIsCompleted ' + Value)
    # 1st letter is f/b/u/d for forward/backward/up/ down finished
    # Nr. is scanline

MySXM.Scan = MyScanIsCompleted


#Set/read drift compensation vector
#disable drift compensation = set drift vector 0
# drift vector is visible in hint durimg mouse over ScanPara-Form->below tip, on sample
MySXM.SendWait("ScanPara('DriftX',-2);");
print ("driftX:", MySXM.GetScanPara('DriftX'));
MySXM.SendWait("ScanPara('DriftY',-15);");
print ("driftY:", MySXM.GetScanPara('DriftY'));

#Enable/disable plane subtraction scan mode
# in SXM ScanPara_Form tab "Level"
#0 = off
#1 = fixed
#2 = auto
Mode=1 
MySXM.SendWait("ScanPara('Slope',"+str(Mode)+");")

#Set plane subtraction scan slope (X/Y)
Slope=1.1 # in grd if scannerfile is correct
MySXM.SendWait("ScanPara('SlopeX',"+str(Slope)+");");
print(MySXM.GetScanPara('SlopeX'))
Slope=-1.1 # in grd if scannerfile is correct
MySXM.SendWait("ScanPara('SlopeY',"+str(Slope)+");");
print(MySXM.GetScanPara('SlopeY'))


# current tip position
# read x, y (scale --> DACxx (1-xx))
oldx=MySXM.GetChannel(-2)
oldy=MySXM.GetChannel(-3)
print("old x: " + str(oldx))
print("old y: " + str(oldy))

#shift tip to new position
#set x, y
newx=55
newy=56
TargetX=MySXM.SendWait("SpectPara(1, "+str(newx)+");")
TargetY=MySXM.SendWait("SpectPara(2, "+str(newy)+");")
print("new x: " + str(newx))
print("new y: " + str(newy))

#start spectroscopy to move? autosafe off
MySXM.SendWait("SpectPara('AUTOSAVE', 0);")
MySXM.SendWait("SpectStart;")

print("new x?", str(MySXM.GetChannel(-2))) #x-direction
print("new y?", str(MySXM.GetChannel(-3))) #y-direction

if (newx == MySXM.GetChannel(-2)) and (newy == MySXM.GetChannel(-3)):
    print('target position arrived');

#move tip back to remembered tip position
def BackToRememberedPosition():
    MySXM.SendWait("SpectPara(1, "+str(oldx)+");")
    MySXM.SendWait("SpectPara(2, "+str(oldy)+");")
    MySXM.SendWait("SpectStart;")

back=BackToRememberedPosition() #use it





