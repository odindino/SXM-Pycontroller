
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

2024/11/24 Zi-Liang Yang:
Trying to figure out the problem of auto_move_scan_area.
The problem is it cannot operate continueously. Finally, I found that since I change the scan_on into is_scanning in the "perform_scan_sequence" function.
After add "self.scan_on" before "if not self.is_scanning()", the problem is solved.

2024/11/28 Zi-Liang Yang:
Testing the CITS function.
Found that problem is, when SXM is scanning, it can not listen to other command. But Python would keep sending the rest of command and end the program (function, script).

2024/12/05 Zi-Liang Yang:
About two weeks past, the program almost fits what I want. But there are still some things need to be done.

1. Auto detect the scan direction.
2. Fix local CITS function in java script.
3. Local CITS scripts
4. Transform the front end to Vue structure.
5. Loading the last image from the SXM data folder.
