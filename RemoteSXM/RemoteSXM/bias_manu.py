### -*- coding: UTF-8 -*-

import SXMRemote
import time
import matplotlib.pyplot as plt
import ctypes
import warnings
import matplotlib.cbook

# supress warning from matplotlib
warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)


MySXM= SXMRemote.DDEClient("SXM","Remote");

sec = 10

Start=-0.5
Stop=-50
x=(Stop-Start)/(sec)
print(x)
for i in range(sec+1):
    Bias=Start+i*x

    MySXM.SendWait("FeedPara('Bias', "+str(Bias)+");") 
    NewBias=MySXM.GetChannel(-1)            # -> float
    NewBias2=MySXM.GetFeedbackPara('Bias')  # -> integer

    print("SendBias", str(Bias))
    print("GetChannel", str(NewBias))
    print("GetFeedback", str(NewBias2))
    time.sleep(1) # seconds

       
