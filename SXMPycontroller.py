# This file is the to make a user-friendly module for SXM controlling
# Scenarios:
# 1. Conduct a spectroscopy measurement(point, line or array) at a given position with varying Vds or Vg bias
# 1-1. After moving the tip to the position, turn off the feedback loop
# 1-2. Conduct the command for SMU, set the Vds or Vg bias, and turn on the SMU
# 1-3. Conduct the spectroscopy measurement
# 1-4. Turn off the SMU
# 1-5. Turn on the feedback loop
# 1-6. Repeat the above steps for different Vds or Vg bias, if any.
# 1-7. Move the tip to the next position and repeat the above steps.
from RemoteSXM import SXMRemote
import time
import pyvisa
import ksb2902bsmu as smu


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

    # ========== CITS section ========== #
    def CITS(self, start_x, start_y, dx, dy, nx, ny, sts_params=None):
        """
        Perform Current Imaging Tunneling Spectroscopy (CITS) measurement.

        This function combines STM imaging with STS measurements. It scans the surface
        line by line, and performs STS at specified intervals during the scan.

        Parameters
        ----------
        start_x : float
            Starting X position for the CITS measurement (in nm)
        start_y : float
            Starting Y position for the CITS measurement (in nm)
        dx : float
            Distance between STS points along X axis (in nm)
        dy : float
            Distance between scan lines where STS will be performed (in nm)
        nx : int
            Number of STS points along X axis
        ny : int
            Number of scan lines where STS will be performed
        sts_params : dict, optional
            Dictionary containing STS measurement parameters:
            {
                'start_bias': float,  # Starting bias voltage (V)
                'end_bias': float,    # Ending bias voltage (V)
                'points': int,        # Number of points in STS
                'delay': float        # Delay time between points (ms)
            }
        """
        # Check if scan is already running
        if self.check_scan() == 1:
            print("Warning: Scan is already running. Stopping current scan...")
            self.scan_off()
            time.sleep(2)

        # Set default STS parameters if not provided
        if sts_params is None:
            sts_params = {
                'start_bias': -2.0,
                'end_bias': 2.0,
                'points': 200,
                'delay': 100
            }

        # Configure STS parameters
        # Set to I(V) spectroscopy mode
        self.MySXM.SendWait(f"SpectPara(0, 1);")
        self.MySXM.SendWait(f"SpectPara('Points', {sts_params['points']});")
        self.MySXM.SendWait(
            f"SpectPara(7, {sts_params['start_bias']});")  # Start bias
        self.MySXM.SendWait(
            f"SpectPara(8, {sts_params['end_bias']});")    # End bias
        self.MySXM.SendWait(
            f"SpectPara(4, {sts_params['delay']});")       # Delay time

        # Calculate total scan range
        total_x_range = dx * (nx - 1)
        total_y_range = dy * (ny - 1)

        # Set scan parameters
        self.MySXM.SendWait(
            f"ScanPara('Range', {max(total_x_range, total_y_range)});")
        self.MySXM.SendWait(f"ScanPara('X', {start_x});")
        self.MySXM.SendWait(f"ScanPara('Y', {start_y});")

        try:
            # Start the scan
            self.scan_on()

            # Monitor scan progress line by line
            for y_idx in range(ny):
                current_y = start_y + y_idx * dy

                # Wait until scanner reaches the current y position
                while True:
                    current_line = self.MySXM.GetScanPara('LineNr')
                    if current_line >= y_idx:
                        break
                    time.sleep(0.1)

                # Perform STS measurements along the line
                for x_idx in range(nx):
                    current_x = start_x + x_idx * dx

                    # Pause the scan
                    self.scan_off()
                    time.sleep(0.5)  # Wait for scanner to stabilize

                    # Move to exact position
                    self.move_tip(current_x, current_y)
                    time.sleep(0.5)

                    # Perform STS
                    self.feedback_off()  # Turn off feedback
                    time.sleep(0.2)
                    self.spectroscopy_on()  # Start spectroscopy

                    # Wait for spectroscopy to complete
                    time.sleep((sts_params['points'] *
                               sts_params['delay']) / 1000 + 1)

                    self.feedback_on()  # Turn feedback back on
                    time.sleep(0.2)

                    # Resume scanning
                    self.scan_on()

                print(f"Completed line {y_idx + 1} of {ny}")

        except Exception as e:
            print(f"Error during CITS measurement: {str(e)}")
            self.feedback_on()  # Ensure feedback is on
            raise

        finally:
            # Ensure proper cleanup
            self.scan_off()
            self.feedback_on()
            print("CITS measurement completed")
    # ========== CITS section END ========== #


SXM = SXMController()
SXM.scan_on()
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


# ==== CITS test ==== #
# 創建SXM控制器實例
# sxm_controller = SXMController()

# # 設定CITS參數
# sts_settings = {
#     'start_bias': -1.5,    # 起始偏壓 -1.5V
#     'end_bias': 1.5,       # 結束偏壓 1.5V
#     'points': 200,         # 每條STS曲線的點數
#     'delay': 50            # 每點的延遲時間(ms)
# }

# # 執行CITS量測
# sxm_controller.CITS(
#     start_x=0,      # 起始X座標 (nm)
#     start_y=0,      # 起始Y座標 (nm)
#     dx=5,           # X方向點間距 (nm)
#     dy=5,           # Y方向線間距 (nm)
#     nx=100,         # X方向點數
#     ny=100,         # Y方向線數
#     sts_params=sts_settings
# )
# ==== CITS test ==== #
