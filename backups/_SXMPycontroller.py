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
from SXMDIO import SXMDIO
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
    def __init__(self, debug_mode=False):
        """
        初始化SXM控制器
        
        Parameters
        ----------
        debug_mode : bool, optional
            是否啟用除錯模式，預設為False
        """

        self.MySXM = SXMRemote.DDEClient("SXM", "Remote")
        self.dio = SXMDIO()

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

        # 控制事件監聽器的運行
        self._stop_event = threading.Event()

        # 啟動事件監聽器
        self._start_event_listener()

    def get_current_state(self):
        """
        獲取當前掃描器狀態
        
        Returns
        -------
        dict
            包含所有基本參數的字典
        """
        state = {}
        basic_params = ['X', 'Y', 'Range', 'Scan', 'Angle']
        
        for param in basic_params:
            state[param] = self.GetScanPara(param)
            
        return state
    
    def print_current_state(self):
        """
        打印當前掃描器狀態
        """
        state = self.get_current_state()
        print("\n=== 當前掃描器狀態 ===")
        for param, value in state.items():
            print(f"{param}: {value}")

    # ========== Event handling ========== #
    def _start_event_listener(self):
        """啟動背景事件監聽器"""
        self.event_listener = threading.Thread(
            target=self._event_listener_loop, daemon=True)
        self.event_listener.start()

    def _event_listener_loop(self):
        """背景事件處理循環"""
        while not self._stop_event.is_set():
            try:
                # 使用較短的超時時間以便及時響應停止信號
                event = self.event_queue.get(timeout=0.1)
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
        try:
            while True:
                # 檢查掃描狀態
                current_status = self.check_scan(verbose=True)

                # 如果收到掃描結束的信號
                if not self.scan_status.is_scanning and self.scan_status.scan_finished_time:
                    print(
                        f"Scan completed at {self.scan_status.scan_finished_time}")
                    return True

                # 檢查超時
                if timeout and (time.time() - start_time > timeout):
                    print("Scan monitoring timeout")
                    return False

                # Windows消息處理
                SXMRemote.loop()

                # 短暫休息以減少CPU使用
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nMonitoring interrupted by user")
            return False

    def stop_monitoring(self):
        """停止事件監聽"""
        self._stop_event.set()
        self.event_listener.join(timeout=1.0)

    # ========== General calculations ========== #
    def rotate_coordinates(self, x, y, angle_deg, center_x=0, center_y=0):
        """
        旋轉座標系

        Parameters
        ----------
        x, y : float
            原始座標
        angle_deg : float
            旋轉角度（度），逆時針為正
        center_x, center_y : float
            旋轉中心點

        Returns
        -------
        tuple (float, float)
            旋轉後的座標
        """
        # 轉換到弧度
        angle_rad = math.radians(angle_deg)

        # 平移到原點
        x_shifted = x - center_x
        y_shifted = y - center_y

        # 旋轉
        x_rot = x_shifted * math.cos(angle_rad) - \
            y_shifted * math.sin(angle_rad)
        y_rot = x_shifted * math.sin(angle_rad) + \
            y_shifted * math.cos(angle_rad)

        # 平移回原位
        x_final = x_rot + center_x
        y_final = y_rot + center_y

        return x_final, y_final

    def get_real_coordinates(self, x_nm, y_nm):
        """
        將物理座標（nm）轉換為當前掃描範圍內的實際座標，考慮掃描角度

        Parameters
        ----------
        x_nm, y_nm : float
            目標座標（nm）

        Returns
        -------
        tuple (float, float)
            在當前掃描範圍內的實際座標
        """
        try:
            # 獲取當前掃描參數
            center_x = self.GetScanPara('X')
            center_y = self.GetScanPara('Y')
            scan_range = self.GetScanPara('Range')
            angle = self.GetScanPara('Angle')

            # 計算掃描範圍的邊界（未旋轉時的）
            half_range = scan_range / 2

            # 將目標點相對於中心點進行反向旋轉
            # （因為我們要在旋轉的掃描框中確定位置）
            x_rot, y_rot = self.rotate_coordinates(
                x_nm, y_nm,
                -angle,  # 使用負角度進行反向旋轉
                center_x, center_y
            )

            # 檢查是否在未旋轉的範圍內
            if (abs(x_rot - center_x) > half_range or
                    abs(y_rot - center_y) > half_range):
                print(f"Warning: Point ({x_nm}, {y_nm}) outside scan range")

                # 限制在範圍內
                x_rot = max(center_x - half_range,
                            min(center_x + half_range, x_rot))
                y_rot = max(center_y - half_range,
                            min(center_y + half_range, y_rot))

            # 將限制後的點旋轉回去
            x_final, y_final = self.rotate_coordinates(
                x_rot, y_rot,
                angle,  # 使用正角度旋轉回原方向
                center_x, center_y
            )

            return x_final, y_final

        except Exception as e:
            print(f"Error calculating coordinates: {str(e)}")
            return None

    # ========== General calculations END ========== #

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
        float or None
            參數值
        """
        try:
            # 使用驗證過的命令格式
            command = (
                "a := 0.0;\n"
                f"a := GetScanPara('{param}');\n"
                "Writeln(a);"
            )
            
            self.MySXM.execute(command, 5000)
            
            # 等待回應
            wait_count = 0
            while self.MySXM.NotGotAnswer and wait_count < 50:
                SXMRemote.loop()
                time.sleep(0.1)
                wait_count += 1
            
            # 處理回應
            if not self.MySXM.NotGotAnswer and isinstance(self.MySXM.LastAnswer, bytes):
                response_lines = self.MySXM.LastAnswer.decode('utf-8').split('\r\n')
                
                # 尋找第一個可轉換為數值的行
                for line in response_lines:
                    if line.startswith('DDE Cmd'):
                        continue
                    try:
                        if line.strip():
                            return float(line.strip())
                    except ValueError:
                        continue
                        
            return None
            
        except Exception as e:
            if self.debug_mode:
                print(f"GetScanPara error for {param}: {str(e)}")
            return None

    def print_current_state(self):
        """
        打印當前掃描器狀態（包含除錯資訊）
        """
        print("\n=== 當前掃描器狀態 ===")
        self.debug_mode = True  # 臨時開啟除錯模式
        
        basic_params = ['X', 'Y', 'Range', 'Scan', 'Angle']
        results = {}
        
        for param in basic_params:
            print(f"\n讀取 {param} 參數:")
            value = self.GetScanPara(param)
            results[param] = value
            print(f"{param}: {value}")
            print("-" * 50)
            
        self.debug_mode = False  # 恢復原始除錯模式設置
        
        return results
    # ========== Get parameter (General) END ========== #

    # ========== SXMDIO ========== #
    def get_real_position(self):
        """
        使用直接I/O獲取探針實際位置
        這比使用DDE更快且更準確

        Returns
        -------
        tuple (float, float)
            (x, y) 實際位置座標
        """
        return self.dio.get_position()

    def get_real_topography(self):
        """
        使用直接I/O獲取探針高度

        Returns
        -------
        float
            Z方向高度值
        """
        return self.dio.get_topography()

    def get_real_bias(self):
        """
        使用直接I/O獲取實際偏壓

        Returns
        -------
        float
            偏壓值(mV)
        """
        return self.dio.get_bias()

    def get_real_current(self):
        """
        使用直接I/O獲取實際穿隧電流

        Returns
        -------
        float
            穿隧電流值
        """
        return self.dio.get_tunneling_current()

    # ========== SXMDIO END ========== #

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

    # ========== Spectroscopy Section ========== #
    # Move the tip
    def move_tip(self, x, y):
        self.MySXM.SendWait("SpectPara(1, " + str(x) + ");")
        self.MySXM.SendWait("SpectPara(2, " + str(y) + ");")

    def spectroscopy_on(self):
        self.MySXM.SendWait("SpectStart;")

    # ========== Spectroscopy Section END ========== #

    # ========== Scan Section ========== #
    # ========== Check scan status ========== #
    def is_scanning(self):
        """
        檢查是否正在掃描
        
        Returns
        -------
        bool
            True表示正在掃描，False表示未在掃描
        """
        scan_value = self.GetScanPara('Scan')
        return bool(scan_value) if scan_value is not None else False
    
    def check_scan(self):
        """
        檢查掃描狀態

        Returns
        -------
        bool or None
            True if scanning, False if not scanning, None if error
        """
        try:
            command = "a:=GetScanPara('Scan');\r\n  writeln(a);"
            self.MySXM.execute(command, 5000)

            wait_count = 0
            while self.MySXM.NotGotAnswer and wait_count < 50:
                SXMRemote.loop()
                time.sleep(0.1)
                wait_count += 1

            response = self.MySXM.LastAnswer

            if isinstance(response, bytes):
                response_str = str(response, 'utf-8').strip()

                # 檢查掃描行信息 (f123, b123)
                if response_str[:1] in ['f', 'b']:
                    direction = 'forward' if response_str[0] == 'f' else 'backward'
                    try:
                        line_number = int(response_str[1:])
                        self.scan_status.is_scanning = True
                        self.scan_status.direction = direction
                        self.scan_status.line_number = line_number
                        if self.debug_mode:
                            print(f"Scanning: {direction} line {line_number}")
                        return True
                    except ValueError:
                        pass

                # 檢查數字回應
                if response_str.isdigit():
                    value = int(response_str)
                    self.scan_status.is_scanning = bool(value)
                    if not value:
                        self.scan_status.direction = None
                        self.scan_status.line_number = 0
                    if self.debug_mode:
                        print("Scan status:", "On" if value else "Off")
                    return bool(value)

            elif isinstance(response, int):
                self.scan_status.is_scanning = bool(response)
                if self.debug_mode:
                    print("Scan status:", "On" if response else "Off")
                return bool(response)

        except Exception as e:
            if self.debug_mode:
                print(f"Error checking scan status: {str(e)}")
            return None

        return None
    
    def SetScanPara(self, param, value):
        """
        設定掃描參數（改進的版本）
        
        Parameters
        ----------
        param : str
            參數名稱
        value : float
            參數值
            
        Returns
        -------
        bool
            設定是否成功
        """
        try:
            # 記錄原始值
            original_value = self.GetScanPara(param)
            
            if self.debug_mode:
                print(f"\n=== 設定參數 {param} ===")
                print(f"目前值: {original_value}")
                print(f"目標值: {value}")
            
            # 嘗試不同的命令格式
            commands = [
                # 格式1: 基本格式
                f"ScanPara('{param}', {value});",
                
                # 格式2: begin-end 區塊
                f"begin\nScanPara('{param}', {value});\nend.",
                
                # 格式3: 使用變數
                f"a := {value};\nScanPara('{param}', a);",
                
                # 格式4: 完整程式區塊
                f"begin\na := {value};\nScanPara('{param}', a);\nend."
            ]
            
            success = False
            for i, cmd in enumerate(commands, 1):
                if self.debug_mode:
                    print(f"\n嘗試命令格式 #{i}:")
                    print(cmd)
                    
                self.MySXM.execute(cmd, 5000)
                time.sleep(0.5)  # 給系統一些反應時間
                
                # 驗證設定
                new_value = self.GetScanPara(param)
                
                if self.debug_mode:
                    print(f"執行後的值: {new_value}")
                    if isinstance(self.MySXM.LastAnswer, bytes):
                        print(f"原始回應: {self.MySXM.LastAnswer.decode('utf-8')}")
                    
                # 檢查值是否正確設定（允許小誤差）
                if new_value is not None:
                    if abs(float(new_value) - float(value)) < 1e-6:
                        success = True
                        if self.debug_mode:
                            print(f"命令格式 #{i} 成功")
                        break
                    else:
                        if self.debug_mode:
                            print(f"值不符合預期")
                            
            if self.debug_mode:
                print(f"\n設定{'成功' if success else '失敗'}")
                print(f"最終值: {new_value}")
                
            return success
            
        except Exception as e:
            if self.debug_mode:
                print(f"SetScanPara錯誤: {str(e)}")
                import traceback
                traceback.print_exc()
            return False

    def verify_parameter_change(self, param, value, max_retries=3):
        """
        驗證參數變更
        
        Parameters
        ----------
        param : str
            參數名稱
        value : float
            預期值
        max_retries : int
            最大重試次數
            
        Returns
        -------
        bool
            驗證是否成功
        """
        for i in range(max_retries):
            actual_value = self.GetScanPara(param)
            if actual_value is not None and abs(float(actual_value) - float(value)) < 1e-6:
                return True
            time.sleep(0.5)  # 等待系統響應
        return False

    def setup_scan_area(self, center_x, center_y, scan_range, angle=0):
        """
        設定掃描區域
        
        Parameters
        ----------
        center_x : float
            掃描中心X座標
        center_y : float
            掃描中心Y座標
        scan_range : float
            掃描範圍（nm）
        angle : float, optional
            掃描角度（度），預設為0
            
        Returns
        -------
        bool
            設定是否全部成功
        """
        try:
            success = True
            # 設定各項參數
            success &= self.SetScanPara('X', center_x)
            success &= self.SetScanPara('Y', center_y)
            success &= self.SetScanPara('Range', scan_range)
            success &= self.SetScanPara('Angle', angle)
            
            if self.debug_mode:
                if success:
                    print("掃描區域設定成功")
                else:
                    print("部分參數設定失敗")
                    
            return success
            
        except Exception as e:
            if self.debug_mode:
                print(f"Setup scan area error: {str(e)}")
            return False

    def move_to_position(self, x, y, wait_time=1.0):
        """
        移動到指定位置
        
        Parameters
        ----------
        x : float
            目標X座標
        y : float
            目標Y座標
        wait_time : float, optional
            移動後的等待時間（秒），預設為1秒
            
        Returns
        -------
        bool
            移動是否成功
        """
        try:
            # 設定新位置
            if not (self.SetScanPara('X', x) and self.SetScanPara('Y', y)):
                return False
                
            # 等待系統響應
            time.sleep(wait_time)
            
            # 驗證位置
            current_x, current_y = self.get_position()
            if current_x is None or current_y is None:
                return False
                
            # 檢查是否到達目標位置（允許些微誤差）
            position_tolerance = 1e-3  # 1 nm的容差
            return (abs(current_x - x) < position_tolerance and 
                    abs(current_y - y) < position_tolerance)
                    
        except Exception as e:
            if self.debug_mode:
                print(f"Move to position error: {str(e)}")
            return False

    def perform_scan_sequence(self, repeat_count=1):
        """
        在當前位置執行指定次數的掃描

        Parameters
        ----------
        repeat_count : int
            掃描重複次數
        """
        for i in range(repeat_count):
            print(f"Starting scan {i+1}/{repeat_count}")
            self.scan_on()

            # 等待掃描完成
            if self.wait_for_scan_complete():
                print(f"Scan {i+1} completed")
            else:
                print(f"Scan {i+1} failed or interrupted")
                break

    def scan_on(self):
        self.MySXM.execute(
            "ScanPara('Scan', 1);\r\n", 5000)

    def scan_off(self):
        self.MySXM.execute(
            "ScanPara('Scan', 0);\r\n", 5000)

    def scan_lines(self, num_lines):
        """
        掃描指定行數

        Parameters
        ----------
        num_lines : int
            要掃描的行數

        Returns
        -------
        bool
            掃描是否成功完成
        """
        try:
            self.MySXM.SendWait(f"ScanLine({num_lines});")

            # 等待掃描完成
            current_line = 0
            while True:
                status = self.check_scan()
                if status is False:
                    return True  # 掃描完成

                # 獲取當前掃描行數
                new_line = self.GetScanPara('LineNr')
                if new_line != current_line:
                    current_line = new_line
                    print(f"Scanning line {current_line}")

                time.sleep(0.1)

        except Exception as e:
            print(f"Error during line scan: {str(e)}")
            return False
        
    def get_position(self):
        """
        獲取當前位置
        
        Returns
        -------
        tuple
            (X座標, Y座標)，如果讀取失敗則返回(None, None)
        """
        x = self.GetScanPara('X')
        y = self.GetScanPara('Y')
        return (x, y)

    # ========== Scan Section END ========== #

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

    # ========= Special functions ========= #
    # ========== CITS section ========== #
    def calculate_cits_parameters(self, num_points_x, num_points_y, scan_direction=1):
        """
        計算CITS的基本參數

        Parameters
        ----------
        num_points_x : int
            X方向的測量點數
        num_points_y : int
            Y方向的測量點數
        scan_direction : int
            掃描方向: 1表示向上掃描, -1表示向下掃描

        Returns
        -------
        dict
            CITS參數，包含起始點、間距等
        """
        try:
            # 獲取掃描參數
            scan_range = self.GetScanPara('Range')
            scan_angle = self.GetScanPara('Angle')
            pixels = self.GetScanPara('Pixel')

            # 獲取當前中心位置
            center_x, center_y = self.get_center_position()
            print(f"Scan center: ({center_x:.3f}, {center_y:.3f})")
            print(f"Scan angle: {scan_angle}°")

            # 計算實際範圍（稍微縮小以避免超出範圍）
            safe_margin = 0.02
            effective_range = scan_range * (1 - safe_margin)
            half_range = effective_range / 2

            # 計算起始點（相對於中心點）
            if scan_direction == 1:  # 向上掃描
                rel_x = -half_range  # 從左邊開始
                rel_y = -half_range  # 從下面開始
            else:  # 向下掃描
                rel_x = -half_range  # 從左邊開始
                rel_y = half_range   # 從上面開始

            # 將相對座標旋轉到實際角度（以中心點為旋轉中心）
            start_x, start_y = self.rotate_coordinates(
                rel_x, rel_y,
                scan_angle,
                center_x, center_y  # 使用實際的掃描中心
            )

            # 計算步長（在旋轉座標系中）
            dx = effective_range / (num_points_x - 1)
            dy = effective_range / (num_points_y - 1)
            if scan_direction == -1:
                dy = -dy

            # 步長向量需要旋轉到實際角度
            dx_rot, dy_temp = self.rotate_coordinates(
                dx, 0,
                scan_angle,
                0, 0  # 步長是相對量，不需要考慮中心點
            )
            temp_x, dy_rot = self.rotate_coordinates(
                0, dy,
                scan_angle,
                0, 0
            )

            return {
                'start_x': start_x,
                'start_y': start_y,
                'dx': dx_rot,                   # 旋轉後的X步長
                'dy': dy_rot,                   # 旋轉後的Y步長
                'center_x': center_x,           # 掃描中心X
                'center_y': center_y,           # 掃描中心Y
                'lines_per_sts': pixels // (num_points_y + 1),
                'scan_angle': scan_angle,
                'total_lines': pixels,
                'effective_range': effective_range,
                'scan_direction': scan_direction
            }

        except Exception as e:
            print(f"Error calculating CITS parameters: {str(e)}")
            return None

    def standard_cits(self, num_points_x, num_points_y, scan_direction=1, sts_params=None):
        """
        執行標準CITS測量
        """
        try:
            # 檢查當前掃描狀態
            if self.check_scan():
                print("Scan in progress, continuing with CITS")
            else:
                print("Starting new scan")
                self.scan_on()
                time.sleep(0.5)  # 給予掃描啟動的時間

            params = self.calculate_cits_parameters(
                num_points_x, num_points_y, scan_direction
            )
            if not params:
                raise ValueError("Failed to calculate CITS parameters")

            print(f"\nStarting standard CITS measurement:")
            print(
                f"Center position: ({params['center_x']:.3f}, {params['center_y']:.3f})")
            print(
                f"Starting position: ({params['start_x']:.3f}, {params['start_y']:.3f})")
            print(f"Step sizes: dx={params['dx']:.3f}, dy={params['dy']:.3f}")
            print(f"Number of points: {num_points_x}x{num_points_y}")
            print(f"Lines between STS: {params['lines_per_sts']}")
            print(f"Scan direction: {'Up' if scan_direction == 1 else 'Down'}")

            current_line = 0
            completed_points = 0
            total_points = num_points_x * num_points_y

            for y_idx in range(num_points_y):
                # 計算當前行的位置
                current_y = params['start_y'] + y_idx * params['dy']

                # 掃描到適當的行
                lines_to_scan = params['lines_per_sts']
                print(
                    f"\nScanning {lines_to_scan} lines before STS line {y_idx + 1}/{num_points_y}")
                if not self.scan_lines(lines_to_scan):
                    raise RuntimeError("Failed to scan lines")

                current_line += lines_to_scan
                print(
                    f"Current scan line: {current_line}/{params['total_lines']}")

                # 在當前行進行STS測量
                print(f"Performing STS measurements on line {y_idx + 1}")
                for x_idx in range(num_points_x):
                    # 直接使用旋轉後的步長計算位置
                    current_x = params['start_x'] + x_idx * params['dx']

                    # 執行STS
                    completed_points += 1
                    progress = (completed_points / total_points) * 100
                    print(f"STS point {completed_points}/{total_points} "
                          f"({progress:.1f}%) at ({current_x:.3f}, {current_y:.3f})")
                    self.perform_sts(current_x, current_y, sts_params)

                # 檢查是否接近圖像結束
                remaining_lines = params['total_lines'] - current_line
                if remaining_lines < params['lines_per_sts']:
                    print("Warning: Approaching end of scan, stopping CITS")
                    break

            print("\nCITS measurement completed")
            print(f"Total points measured: {completed_points}/{total_points}")

        except Exception as e:
            print(f"Error during standard CITS: {str(e)}")
            # 確保掃描繼續
            self.scan_on()

    def define_cits_area(self, start_x, start_y, width, height):
        """
        定義CITS測量區域，考慮掃描角度

        Parameters
        ----------
        start_x, start_y : float
            起始座標（nm）
        width, height : float
            區域寬度和高度（nm）

        Returns
        -------
        dict
            CITS區域的定義，包含旋轉後的四個角點座標
        """
        try:
            # 獲取當前掃描角度
            angle = self.GetScanPara('Angle')
            center_x = self.GetScanPara('X')
            center_y = self.GetScanPara('Y')

            # 計算矩形四個角點（相對於起始點）
            corners = [
                (start_x, start_y),                    # 左下
                (start_x + width, start_y),            # 右下
                (start_x + width, start_y + height),   # 右上
                (start_x, start_y + height)            # 左上
            ]

            # 轉換所有角點到實際座標
            real_corners = []
            for x, y in corners:
                real_x, real_y = self.get_real_coordinates(x, y)
                if real_x is None or real_y is None:
                    raise ValueError("Invalid coordinates")
                real_corners.append((real_x, real_y))

            # 計算旋轉後的寬度和高度
            # （使用對角線點的距離）
            actual_width = math.sqrt(
                (real_corners[1][0] - real_corners[0][0])**2 +
                (real_corners[1][1] - real_corners[0][1])**2
            )
            actual_height = math.sqrt(
                (real_corners[3][0] - real_corners[0][0])**2 +
                (real_corners[3][1] - real_corners[0][1])**2
            )

            return {
                'corners': real_corners,
                'start_x': real_corners[0][0],
                'start_y': real_corners[0][1],
                'width': actual_width,
                'height': actual_height,
                'angle': angle
            }

        except Exception as e:
            print(f"Error defining CITS area: {str(e)}")
            return None

    def perform_cits(self, cits_area, lines_between_sts, points_per_line, sts_params=None):
        """
        執行CITS測量，考慮掃描角度
        """
        try:
            # 獲取掃描參數
            angle = cits_area['angle']

            # 計算每個測量點的位置
            for line in range(lines_between_sts):
                # 計算當前行的起點和終點
                t = line / (lines_between_sts - 1)
                start = (
                    cits_area['corners'][0][0] *
                        (1-t) + cits_area['corners'][3][0] * t,
                    cits_area['corners'][0][1] *
                        (1-t) + cits_area['corners'][3][1] * t
                )
                end = (
                    cits_area['corners'][1][0] *
                    (1-t) + cits_area['corners'][2][0] * t,
                    cits_area['corners'][1][1] *
                    (1-t) + cits_area['corners'][2][1] * t
                )

                # 在當前行上執行測量
                for point in range(points_per_line):
                    t = point / (points_per_line - 1)
                    x = start[0] * (1-t) + end[0] * t
                    y = start[1] * (1-t) + end[1] * t

                    self.perform_sts(x, y, sts_params)

            # 其餘執行邏輯...

        except Exception as e:
            print(f"Error during CITS: {str(e)}")

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
        try:
            while True:
                # 檢查掃描狀態
                current_status = self.check_scan()

                # 如果掃描已結束
                if current_status is False:
                    print("Scan completed")
                    return True

                # 檢查超時
                if timeout and (time.time() - start_time > timeout):
                    print("Scan monitoring timeout")
                    return False

                # Windows消息處理
                SXMRemote.loop()

                # 短暫休息以減少CPU使用
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nMonitoring interrupted by user")
            return False

    # ========== Auto move and scan area ========== #
    def auto_move_scan_area(self, movement_script, distance, wait_time, repeat_count=1):
        """
        執行自動移動和掃描序列

        Parameters
        ----------
        movement_script : str
            移動指令序列，如 "RULLDDRR"
        distance : float
            每次移動的距離
        wait_time : float
            每次移動後的等待時間（秒）
        repeat_count : int, optional
            每個位置的掃描重複次數
        """
        # 獲取初始位置和角度
        self.get_scan_angle()
        x, y = self.get_center_position()
        print(f"Starting position: ({x}, {y}), Angle: {self.current_angle}°")

        # 執行初始位置的掃描
        self.perform_scan_sequence(repeat_count)

        # 執行移動和掃描序列
        for i, direction in enumerate(movement_script):
            print(f"\nMoving to position {i+1}/{len(movement_script)}")

            try:
                # 計算新位置
                dx, dy = self.calculate_movement(direction, distance)
                new_x = x + dx
                new_y = y + dy

                print(f"Moving to: ({new_x}, {new_y})")
                self.move_to_position(new_x, new_y, wait_time)

                # 更新當前位置
                x, y = new_x, new_y

                # 執行掃描
                self.perform_scan_sequence(repeat_count)

            except Exception as e:
                print(f"Error at position {i+1}: {str(e)}")
                break

        print("\nMovement sequence completed")
    # ========== Auto move and scan area END ========== #
