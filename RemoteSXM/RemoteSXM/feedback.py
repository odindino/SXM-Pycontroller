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
--    Feedback Loop  --

Enable/disable feedback loop
Check state of feedback loop 

Set/read feedback loop setpoint 

Set/read Ist part of loop gain 
Set/read 2nd part of loop gain 
   
Set/read preamp tunnelling current range

Set feedback mode
Set ratio between AFM and STM feedback mode

Apply a relative Z-offset
Set slew rate for Z-offset changes
Read the absolute Z-position
"""

import SXMRemote
import time

print("SXM remote control")

#MySXM= SXMRemote.DDEClient("Sigma","Remote");
MySXM= SXMRemote.DDEClient("SXM","Remote");

#Check state of feedback loop
#in SXM->zControl->Feedback Off
FbOn=MySXM.GetFeedbackPara('Enable')
print (FbOn)
#0=On 1=off
if (FbOn==0) : #on
    print("Feedback on")
else:
    print("Feedback off")


#Enable/disable feedback loop
MySXM.SendWait("FeedPara('Enable', 0);")    #feedback on
#MySXM.SendWait("FeedPara('Enable', 1);")   #feedback off

#Set feedback mode (Parameter --> Feedback)
#0 = off
#1 = STM general
#2 = STM abs()
#3 = STM log(abs())
#4 = AFM contact mode
#5 = Amplitude R
#6 = Amplitude X
#7 = PLL AFM
#8 = STM+AFM
MySXM.SendWait("FeedPara('Mode', 8);") 


#Set ratio between AFM and STM feedback mode --> bar
#0-100
MySXM.SendWait("FeedPara('Ratio', 100);") #100 AFM

#Set/read preamp tunnelling current range
#GainIndex=MySXM.GetFeedbackPara('PreAmp')
#set gain index:
#1 = 10mA 500kHz
#2 = 1mA 500kHz
#3 = 100µA 400kHz
#4 = 10µA 200kHz
#5 = 1µA 50kHz
#6 = 100nA 7kHz
#7 = 10nA 1kHz
#8 = 1nA 7kHz
#9 = 100pA 1kHz
GainIndex=7
#print (GainIndex)

if GainIndex<10 :
    GainIndex=GainIndex-1
MySXM.SendWait("FeedPara('PreAmp', "+str(GainIndex)+");")
#MySXM.SendWait("FeedPara('PreAmp', 1);")

#Set/read feedback loop setpoint
#read
Ref=MySXM.GetFeedbackPara('Ref')   #e.g. STM
Ref2=MySXM.GetFeedbackPara('Ref2') #AFM if in dual mode
print("Ref", Ref)
print("AFM Ref", Ref2)
#set
Ref=0.79E-9      
Ref2=15      # Hz   AFM
MySXM.SendWait("FeedPara('ref', "+str(Ref)+");")
MySXM.SendWait("FeedPara('Ref2', "+str(Ref2)+");")
print("Ref", Ref)
print("AFM Ref", Ref2)

#Set/read 1st and prim. part of loop gain 
ki=MySXM.GetFeedbackPara('Ki')
kp=MySXM.GetFeedbackPara('Kp')
print ('ki/kp = '+str(ki)+'/'+str(kp))
#do anything
kp=12
ki=11
#double gain
#kp=kp*2
#ki=ki*2
#set feedback loop 
MySXM.SendWait("FeedPara('Ki', "+str(ki)+");")
MySXM.SendWait("FeedPara('Kp', "+str(kp)+");")

#Settings in STM & AFM (dual) mode 
ki2=MySXM.GetFeedbackPara('Ki2')
kp2=MySXM.GetFeedbackPara('Kp2')
print ('2nd loop gains ki/kp = '+str(ki2)+'/'+str(kp2))
ki2=12
kp2=4
#double gain
#ki2=ki2*2
#kp2=kp2*2
#set gain for 2nd loop (if enabled)
MySXM.SendWait("FeedPara('Ki2', "+str(ki2)+");")
MySXM.SendWait("FeedPara('Kp2', "+str(kp2)+");")

#Apply a relative Z-offset
dz=-1
MySXM.SendWait("FeedPara('ZOffset', "+str(dz)+");") #zControl
#Set slew rate for Z-offset changes
#zControl
SlewRate = 2
MySXM.SendWait("FeedPara('ZOffsetSlew', "+str(SlewRate)+");")
MySXM.SendWait("FeedPara('Enable', 1);") #off
time.sleep(1)
MySXM.SendWait("FeedPara('Enable', 0);") #on

#Read the absolute Z-position
print("Z position: ", MySXM.GetChannel(0))
      
      
