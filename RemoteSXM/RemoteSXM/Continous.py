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
--    Continous   --


"""

import SXMRemote
import time

print("SXM remote control")

MySXM= SXMRemote.DDEClient("SXM","Remote");

# Set Mode of Spectroscopy
# 0=X(z)
# 1= X(U,z) number may vary! by configuration of SXM

for i in range(100):
    x=MySXM.GetChannel(-2)
    print(x)


"""
dz=1
MySXM.SendWait("SpectPara(5, "+str(dz)+");")
U1=100  #
MySXM.SendWait("SpectPara(7, "+str(U1)+");")
U2=-100  #
MySXM.SendWait("SpectPara(8, "+str(U2)+");")
"""
