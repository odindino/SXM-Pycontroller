
2024/11/23 Zi-Liang Yang:

Recovers some functions like GetScanPara, SetScanPara and so on. Now, the basic functions are available.

change the structure of the project into
SXM-Pycontroller/
├── modules/
│   ├── __init__.py
│   ├── SXMRemote.py
│   ├── SXMPyBase.py
│   ├── SXMPyEvent.py
│   ├── SXMPyScan.py
│   ├── SXMPySpectro.py
│   └── SXMPyCITS.py
├── utils/
│   ├── __init__.py
│   ├── SXMPyCalc.py
│   └── SXMPyLogger.py
├── config/
│   ├── __init__.py
│   └── SXMParameters.py
├── SXMPycontroller.py
└── SXMPycon_entry.py

Note that Pixels is one of the problem today, since pixel is set according to the order of list in the SXM program, for example, ScanPara('Pixel', 2); → 3th entry in drop down list => 128. If you do something like ScanPara('Pixel', 128), it will be the 129th entry in the list, which is not what you want. So, I need to change the way to set the pixel in the SXM program if we want to do things like setting pixel to 500.

