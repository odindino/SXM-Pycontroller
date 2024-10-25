# This file is the to make a user-friendly module for SXM controlling
from RemoteSXM import SXMRemote
import time
import pyvisa

class SXMController:
    def __init__(self):
        self.MySXM = SXMRemote.DDEClient("SXM", "Remote")

        self.FbOn = 0
        self.tip_pos_X = None
        self.tip_pos_Y = None
        self.scan_status = None
        self.re_scan_status = None
        self.rm = pyvisa.ResourceManager()


    def addsmu(self, smu):
        self.smu = self.rm.open_resource(smu)
        self.smu_voltage_read = 0
        self.smu_current_read = 0

    # voltage in V
    def smu_set_voltage(self, voltage):
        self.smu.write(':SOURCE:VOLTAGE:LEVEL ' + str(voltage))

    # Enable output
    def smu_output_on(self):
        self.smu.write(':OUTPUT ON')

    # Read voltage, current
    def smu_read_voltage(self):
        self.smu_voltage_read = self.smu.query(':MEASURE:VOLTAGE?')
        return self.smu_voltage_read

    def smu_read_current(self):
        self.smu_current_read = self.smu.query(':MEASURE:CURRENT?')
        return self.smu_current_read

    # Disable output
    def smu_output_off(self):
        self.smu.write(':OUTPUT OFF')

    #     self.MySXM.SaveIsDone = self.MyNewFileIsWritten  # use it

    # def MyNewFileIsWritten(FileName):  # new callback function
    #     # get used ini-filename and read from it
    #     Path = self.MySXM.GetIniEntry('Save', 'Path')
    #     print('MyNewFileIsWritten ' + Path + str(FileName))

    # tip position

    def get_tip_position(self):
        x = self.MySXM.GetChannel(-2)  # get tip X-position
        y = self.MySXM.GetChannel(-3)  # get tip Y-position
        return x, y

    def update_tip_position(self):
        self.tip_pos_X, self.tip_pos_Y = self.get_tip_position()

    def show_tip_position(self):
        print("Tip position: X = " + str(self.tip_pos_X) +
              " Y = " + str(self.tip_pos_Y))

    # Feedback loop
    def get_feedback_state(self):
        if self.FbOn == self.MySXM.GetFeedbackPara('Enable'):
            print("Feedback normal")
        else:
            print("Feedback abnormal")

    def feedback_on(self):
        self.MySXM.SendWait("FeedPara('Enable', 0);")  # feedback on
        self.FbOn = 0

    def feedback_off(self):
        self.MySXM.SendWait("FeedPara('Enable', 1);")  # feedback on
        self.FbOn = 1

    # Spectrocopy
    # Move the tip
    def move_tip(self, x, y):
        self.MySXM.SendWait("SpectPara(1, " + str(x) + ");")
        self.MySXM.SendWait("SpectPara(2, " + str(y) + ");")

    def spectroscopy_on(self):
        self.MySXM.SendWait("SpectStart;")

    # Scan
    def check_scan(self):
        # self.scan_status = self.MySXM.execute(
        #     "a:=GetScanPara('Scan');\r\n" +
        #     "Writeln(a);\r\n", 5000)
        self.scan_status = self.MySXM.GetScanPara('Scan')
        # self.MySXM.ScanOffCallBack()
        # a = self.MySXM.execute("GetScanPara('angle');", 5000)
        # print(a)
        print(self.scan_status)
        return self.scan_status

    def scan_on(self):
        # self.MySXM.execute(
        #     "ScanPara('Scan', 1);\r\n", 5000)
        self.MySXM.execute(
            "ScanPara('Scan', 1);\r\n", 5000)
        # "a:=GetScanPara('Scan');\r\n" +
        # "Writeln(a);\r\n", 5000)
        # "Wait(3);\r\n" +
        # "ScanPara('Scan', 0);\r\n" +
        # "a:=GetScanPara('Scan');\r\n" +
        # "Writeln(a);", 5000)
        # self.checkscan()

    def scan_off(self):
        self.MySXM.execute(
            "ScanPara('Scan', 0);\r\n", 5000)
        # self.checkscan()

    def clear_memo(self):
        self.MySXM.execute("ClrScr;", 5000)

    def check_scanXY(self):
        # self.MySXM.execute(
        #     "a:=GetScanPara('Angle');\r\n" +
        #     "Writeln(a);\r\n", 5000)
        x = self.MySXM.GetScanPara('X')
        y = self.MySXM.GetScanPara('Y')
        print('X = ', x, 'Y = ', y)
        return

    # Mixed functions

    # Conduct a spectroscopy measurement at a given position
    # after turn off the feedback loop, conduct the command for SMU, then do STS
    # after STS, turn on the feedback loop

    def STSxSMU(self, x, y):

        # move the tip
        self.MySXM.SendWait("SpectPara(1, " + str(x) + ");")
        self.MySXM.SendWait("SpectPara(2, " + str(y) + ");")

        # turn off the feedback loop
        self.feedback_off()

        # conduct the command for SMU
        self.smu_set_voltage(0.3)
        self.smu_output_on()

        # conduct STS
        self.spectroscopy_on()

        # turn off the SMU
        self.smu_output_off()

        # turn on the feedback loop
        self.feedback_on()

        return


SXM = SXMController()

# I want to scan 3 times, after sending scan_on, I will check the scan status every 2 minutes, once the scan is done, I will send the next scan_on command, and also print the current time.
# for i in range(3):
#     SXM.scan_on()
#     SXM.check_scan()
#     print("Scan on", i)
#     time.sleep(5)
#     while SXM.scan_status == 1.0:
#         print("Scan is not done")
#         time.sleep(10)
#         SXM.check_scan()
#     print("Scan is done")
#     time.sleep(5)
#     SXM.check_scan()
#     SXM.check_scanXY()
#     print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
#     time.sleep(5)

# # # scan 3 times
# # for i in range(6):
# #     SXM.scan_on()
# #     print("Scan on", i)
# #     time.sleep(10)
# # SXMController
# SXM.check_scan()
# print("scan status", SXM.scan_status)
# SXM.scan_on()
# time.sleep(5)
# print('check scan')
# SXM.check_scan()
# print("scan status", SXM.scan_status)
# SXM.scan_off()
# time.sleep(5)
# print('check scan')
# SXM.check_scan()
# print("scan status", SXM.scan_status)
# SXM.check_scanXY()

# SXM.scan_off()
# time.sleep(5)
# # time.sleep(5)
# # SXM.clear_memo()
# # time.sleep(5)
# print('check scan')
# SXM.check_scan()
# SXM.check_scanXY()
# # SXM.scan_off()

# MySXM = SXMRemote.DDEClient("SXM", "Remote")
# print(MySXM.GetScanPara('Angle'))


# def automoveScanArea(SXM, movelist, distance, waittime, repeat=0):
#     SXM_status = SXM.GetScanPara('Scan')
#     x, y = getXYcenter(SXM)

#     # move the scan area
#     for i in range(len(movelist)):
#         print("move to " + str(i) + "th scan area")
#         if movelist[i] == 'R':
#             x += distance
#             setXYcenter(SXM, x, y)
#         elif movelist[i] == 'L':
#             x -= distance
#             setXYcenter(SXM, x, y)
#         elif movelist[i] == 'U':
#             y += distance
#             setXYcenter(SXM, x, y)
#         elif movelist[i] == 'D':
#             y -= distance
#             setXYcenter(SXM, x, y)
#         else:
#             print("Wrong input")

#         # stay for a while to wait for the tip to be stable
#         time.sleep(waittime)

#         # repeat the scan
#         for repeat_time in range(repeat+1):
#             print("scan " + str(repeat_time+1) + " times")
#             startScan(SXM)
#             SXM_status = SXM.GetScanPara('Scan')

#             while SXM_status == 1.:
#                 SXM_status = SXM.GetScanPara('Scan')

# automoveScanArea(MySXM, ['R', 'U', 'L','L','D','D','R','R'], 5, 5)
