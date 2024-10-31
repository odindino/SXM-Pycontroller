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
import threading
import queue
import datetime
import math


class SXMParameters:
    """SXM參數類型定義"""
    # Feedback參數
    FEEDBACK_PARAMS = {
        'Enable': bool,      # 回饋開關
        'Mode': int,        # 回饋模式
        'Bias': float,      # 偏壓
        'Ki': float,        # 積分增益
        'Kp': float,        # 比例增益
        'PreAmp': int,      # 前置放大器範圍
        'BiasDiv': int,     # 偏壓分壓範圍
        'Ratio': float,     # STM/AFM比例
        'ZOffset': float,   # Z軸偏移
        'ZOffsetSlew': float  # Z軸偏移速率
    }

    # Scan參數
    SCAN_PARAMS = {
        'Scan': bool,       # 掃描狀態
        'Range': float,     # 掃描範圍
        'Speed': float,     # 掃描速度
        'Pixel': int,       # 像素數
        'X': float,        # X位置
        'Y': float,        # Y位置
        'Angle': float,     # 掃描角度
        'LineNr': int,      # 當前掃描行數
        'AutoSave': int,   # 自動儲存
        'AspectRatio': float,  # 長寬比
        'DriftX': float,    # X漂移補償
        'DriftY': float,    # Y漂移補償
        'Slope': int,       # 平面校正模式
        'SlopeX': float,    # X斜率校正
        'SlopeY': float     # Y斜率校正
    }


class ScanStatus:
    """掃描狀態的數據類別"""

    def __init__(self):
        self.is_scanning = False
        self.direction = None
        self.line_number = 0
        self.total_lines = 0
        self.last_saved_file = None
        self.scan_finished_time = None  # 記錄掃描結束時間
        self.missed_callbacks = []      # 記錄錯過的回調
        self._lock = threading.Lock()   # 用於線程安全的狀態更新

    def update(self, **kwargs):
        """線程安全的狀態更新"""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)

    def __str__(self):
        with self._lock:
            status = "Scanning" if self.is_scanning else "Not scanning"
            details = []
            if self.is_scanning and self.direction:
                details.append(f"{self.direction} line {self.line_number}")
            if self.last_saved_file:
                details.append(f"Last saved: {self.last_saved_file}")
            if self.scan_finished_time:
                details.append(f"Finished at: {self.scan_finished_time}")
            return f"{status} " + " - ".join(details) if details else status


class SXMController:
    def __init__(self):
        self.MySXM = SXMRemote.DDEClient("SXM", "Remote")

        self.FbOn = 0
        self.tip_pos_X = None
        self.tip_pos_Y = None
        self.current_angle = 0  # 儲存當前掃描角度
        self.scan_status = None
        self.re_scan_status = None

        self.debug_mode = False
        self.scan_status = ScanStatus()
        self.parameters = SXMParameters()

        # 設定回調處理
        self.MySXM.ScanOffCallBack = self._handle_scan_off
        self.MySXM.SaveIsDone = self._handle_save_done
        self.MySXM.ScanOnCallBack = self._handle_scan_on

        # 用於事件記錄的佇列
        self.event_queue = queue.Queue()

        # 啟動事件監聽器
        self._start_event_listener()

    # ========== Event handling ========== #
    def _start_event_listener(self):
        """啟動背景事件監聽器"""
        self.event_listener = threading.Thread(
            target=self._event_listener_loop, daemon=True)
        self.event_listener.start()

    def _event_listener_loop(self):
        """背景事件處理循環"""
        while True:
            try:
                event = self.event_queue.get(timeout=1.0)  # 1秒超時
                event_type = event.get('type')
                event_data = event.get('data')

                if event_type == 'scan_off':
                    self._process_scan_off(event_data)
                elif event_type == 'save_done':
                    self._process_save_done(event_data)
                elif event_type == 'scan_on':
                    self._process_scan_on(event_data)
            except queue.Empty:
                continue
            except Exception as e:
                if self.debug_mode:
                    print(f"Event listener error: {str(e)}")
    # ========== Event handling END ========== #

    # ========== Scan on/off Callbacks ========== #

    def _handle_scan_off(self):
        """掃描結束回調"""
        current_time = datetime.datetime.now()
        self.event_queue.put({
            'type': 'scan_off',
            'data': {'time': current_time}
        })

    def _handle_save_done(self, filename):
        """檔案儲存回調"""
        self.event_queue.put({
            'type': 'save_done',
            'data': {'filename': filename}
        })

    def _handle_scan_on(self):
        """掃描開始回調"""
        self.event_queue.put({
            'type': 'scan_on',
            'data': {'time': datetime.datetime.now()}
        })
    # ========== Scan on/off Callbacks END ========== #

    # ========== Event processing ========== #

    def _process_scan_off(self, data):
        """處理掃描結束事件"""
        self.scan_status.update(
            is_scanning=False,
            direction=None,
            line_number=0,
            scan_finished_time=data['time']
        )
        if self.debug_mode:
            print(f"Scan finished at {data['time']}")

    def _process_save_done(self, data):
        """處理檔案儲存事件"""
        self.scan_status.update(last_saved_file=data['filename'])
        if self.debug_mode:
            print(f"File saved: {data['filename']}")

    def _process_scan_on(self, data):
        """處理掃描開始事件"""
        self.scan_status.update(
            is_scanning=True,
            scan_finished_time=None
        )
        if self.debug_mode:
            print(f"Scan started at {data['time']}")
    # ========== Event processing END ========== #

    # ========== Scan history ========== #

    def get_scan_history(self):
        """獲取掃描歷史記錄"""
        with self.scan_status._lock:
            return {
                'last_scan_finished': self.scan_status.scan_finished_time,
                'last_saved_file': self.scan_status.last_saved_file,
                'missed_callbacks': self.scan_status.missed_callbacks.copy()
            }
    # ========== Scan history END ========== #

    def wait_for_scan_complete(self, timeout=None):
        """
        等待掃描完成

        Parameters
        ----------
        timeout : float, optional
            等待超時時間（秒）

        Returns
        -------
        bool
            True if scan completed, False if timeout
        """
        start_time = time.time()
        while self.scan_status.is_scanning:
            if timeout and (time.time() - start_time > timeout):
                return False
            time.sleep(0.5)
        return True

    # ========== Get parameter (General) ========== #
    # ========== Parse response ========== #
    def _parse_response(self, response, param_name=None, param_type=None):
        """
        通用回應解析器

        Parameters
        ----------
        response : bytes or int
            SXM的回應
        param_name : str, optional
            參數名稱，用於特殊處理
        param_type : type, optional
            期望的參數類型

        Returns
        -------
        Any
            解析後的值
        """
        try:
            # 處理掃描狀態特殊回應
            if isinstance(response, bytes):
                response_str = str(response, 'utf-8').strip()

                # 處理掃描行信息 (f123, b123)
                if param_name == 'Scan' and response_str[:1] in ['f', 'b']:
                    direction = 'forward' if response_str[0] == 'f' else 'backward'
                    line_number = int(response_str[1:])
                    self.scan_status.direction = direction
                    self.scan_status.line_number = line_number
                    return True

                # 處理系統命令回應
                if response_str.startswith('DDE Cmd'):
                    return None

                # 分割回應行
                lines = response_str.split('\r\n')

                # 尋找有效數值
                for line in lines:
                    if not line:
                        continue

                    # 清理並轉換數值
                    cleaned = line.strip('b').replace(',', '.')

                    try:
                        # 根據期望的參數類型進行轉換
                        if param_type == bool:
                            return bool(int(float(cleaned)))
                        elif param_type == int:
                            return int(float(cleaned))
                        elif param_type == float:
                            return float(cleaned)
                        else:
                            # 嘗試自動判斷類型
                            return float(cleaned)
                    except ValueError:
                        continue

            elif isinstance(response, int):
                if param_type == bool:
                    return bool(response)
                elif param_type == float:
                    return float(response)
                return response

        except Exception as e:
            if self.debug_mode:
                print(f"Parse error for {param_name}: {str(e)}")
            return None

        return None
    # ========== Parse response END ========== #

    def get_parameter(self, command, param_name, param_type=None, max_retries=3):
        """
        通用參數獲取函數

        Parameters
        ----------
        command : str
            完整的SXM命令
        param_name : str
            參數名稱
        param_type : type, optional
            期望的參數類型
        max_retries : int, optional
            最大重試次數

        Returns
        -------
        Any
            參數值
        """
        for retry in range(max_retries):
            try:
                self.MySXM.execute(command, 5000)

                # 等待回應
                wait_count = 0
                while self.MySXM.NotGotAnswer and wait_count < 50:
                    SXMRemote.loop()
                    time.sleep(0.1)
                    wait_count += 1

                if wait_count >= 50:
                    if self.debug_mode:
                        print(
                            f"Timeout waiting for {param_name}, attempt {retry + 1}/{max_retries}")
                    continue

                # 解析回應
                result = self._parse_response(
                    self.MySXM.LastAnswer, param_name, param_type)
                if result is not None:
                    return result

            except Exception as e:
                if self.debug_mode:
                    print(
                        f"Error getting {param_name}: {str(e)}, attempt {retry + 1}/{max_retries}")

            time.sleep(0.2)

        print(f"Failed to get {param_name} after {max_retries} attempts")
        return None

    def GetFeedbackPara(self, param):
        """
        獲取回饋參數

        Parameters
        ----------
        param : str
            參數名稱

        Returns
        -------
        Any
            參數值
        """
        if param not in self.parameters.FEEDBACK_PARAMS:
            raise ValueError(f"Unknown feedback parameter: {param}")

        command = f"a:=GetFeedPara('{param}');\r\n  writeln(a);"
        return self.get_parameter(command, param, self.parameters.FEEDBACK_PARAMS[param])

    def GetScanPara(self, param):
        """
        獲取掃描參數

        Parameters
        ----------
        param : str
            參數名稱

        Returns
        -------
        Any
            參數值
        """
        if param not in self.parameters.SCAN_PARAMS:
            raise ValueError(f"Unknown scan parameter: {param}")

        command = f"a:=GetScanPara('{param}');\r\n  writeln(a);"
        return self.get_parameter(command, param, self.parameters.SCAN_PARAMS[param])
    # ========== Get parameter (General) END ========== #

    def addsmu(self, smu):
        self.rm = pyvisa.ResourceManager()
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

    def get_center_position(self):
        """
        獲取當前掃描區域的中心座標

        Returns
        -------
        tuple (float, float)
            (x, y) 中心座標，單位為當前物理單位（如nm）
        """
        x = self.GetScanPara('X')
        y = self.GetScanPara('Y')
        return x, y

    def get_scan_angle(self):
        """
        獲取當前掃描角度

        Returns
        -------
        float
            掃描角度（度），逆時針方向為正
        """
        angle = self.GetScanPara('Angle')
        self.current_angle = angle
        return angle

    def calculate_movement(self, direction, distance):
        """
        根據掃描角度計算實際的移動向量

        Parameters
        ----------
        direction : str
            移動方向 ('R', 'L', 'U', 'D')
        distance : float
            移動距離

        Returns
        -------
        tuple (float, float)
            (dx, dy) 需要移動的x和y分量
        """
        angle_rad = math.radians(self.current_angle)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)

        if direction == 'R':
            dx = distance * cos_angle
            dy = distance * sin_angle
        elif direction == 'L':
            dx = -distance * cos_angle
            dy = -distance * sin_angle
        elif direction == 'U':
            dx = -distance * sin_angle
            dy = distance * cos_angle
        elif direction == 'D':
            dx = distance * sin_angle
            dy = -distance * cos_angle
        else:
            raise ValueError(f"Unknown direction: {direction}")

        return dx, dy

    def move_to_position(self, x, y, wait_time=1):
        """
        移動掃描中心到指定座標

        Parameters
        ----------
        x : float
            目標X座標
        y : float
            目標Y座標
        wait_time : float, optional
            移動後的等待時間（秒）
        """
        try:
            self.MySXM.SendWait(f"ScanPara('X', {x});")
            self.MySXM.SendWait(f"ScanPara('Y', {y});")

            # 快速掃描以移動到新位置
            self.scan_on()
            time.sleep(0.5)  # 給予足夠時間開始移動
            self.scan_off()

            # 等待指定時間以穩定
            time.sleep(wait_time)

        except Exception as e:
            print(f"Error moving to position ({x}, {y}): {str(e)}")

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


# SXM = SXMController()
# SXM.scan_on()

def scan_with_monitoring():
    sxm = SXMController()
    sxm.debug_mode = True

    print("Starting scan...")
    sxm.scan_on()

    try:
        # 設定最長等待時間（例如30分鐘）
        if sxm.wait_for_scan_complete(timeout=1800):
            print("Scan completed normally")
            scan_history = sxm.get_scan_history()
            print(
                f"Scan finished at: {scan_history['last_scan_finished']}")
            print(f"File saved as: {scan_history['last_saved_file']}")
        else:
            print("Scan timeout")
    except KeyboardInterrupt:
        print("Monitoring interrupted by user")

    # 即使中斷監控，之後仍然可以查詢歷史記錄
    scan_history = sxm.get_scan_history()
    print("Final scan status:", str(sxm.scan_status))


scan_with_monitoring()
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
