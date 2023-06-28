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
--    Coarse Movement  --

Move tip n steps backward
Move tip n steps forward
Move tip n steps +X
Move tip n steps –X
Move tip n steps +Y
Move tip n steps –Y
Initiate auto approach operation
Trigger callback when auto approach operation finishes

"""

import SXMRemote
import time

print("SXM remote control")

MySXM= SXMRemote.DDEClient("SXM","Remote");

#Coarse Move
#Move tip n steps closer to sample(down) or backward (up)
#Steps = -1000000 .. 1000000 // >0 =>up
Steps=100 
MySXM.SendWait("MOVE('CZ', "+str(Steps)+");") 

#Move tip n steps in X direction
Steps=100 
MySXM.SendWait("MOVE('CX', "+str(Steps)+");") 

#Move tip n steps in Y direction
Steps=100 
MySXM.SendWait("MOVE('CY', "+str(Steps)+");") 


#Initiate retract operation
'''
mode 0=Piezo
mode 1=OneStep
(from ScanParameter PoupMenu)
'''
mode=1 
MySXM.SendWait("MOVE('Retract', "+str(mode)+");") 

time.sleep(0.5)

#Initiate auto approach operation
#Mode 0=Piezo
#     1=OneStep
#     2=AutoApproach
#     3=fastAutoApproach
Mode=1
MySXM.SendWait("MOVE('Approach', "+str(Mode)+");")

#Trigger callback when auto approach operation finishes
#States from FeedbackReal.MicState
#      Approached = -1
#      Unknown = 0
#      FineRetracted = 1
#      CoarseRetracted = 2
#      PoweredDown = 4
#      Approaching = 5

def MyMicState (State) :
    if (State.startswith(b'-1')):
        print ('My Approached')
    else:    
        print ('My MicState' + str(State) )

MySXM.MicState = MyMicState


