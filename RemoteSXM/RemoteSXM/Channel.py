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

MySXM= SXMRemote.DDEClient("SXM","Remote");


# Get Channel (options -> scale -> DAC):
# MySXM.GetChannel(XX)
# 1-XX
# GetChannel(0)  --> 1     = DAC1 Topo
# GetChannel(-1) --> 1-(-1)= DAC2 Bias
# GetChannel(-2) --> 1-(-2)= DAC3 x-direction
# ...
# -37

XX=1
Channel=MySXM.GetChannel(XX)
print(Channel)
