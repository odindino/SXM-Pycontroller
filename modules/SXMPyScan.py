import time
import math
from . import SXMRemote
from .SXMPyEvent import SXMEventHandler
from utils.logger import get_logger, track_function
from utils.SXMPyCalc import AutoMoveCalculator
import threading


class SXMScanControl(SXMEventHandler):
    """
    掃描控制和位置控制類別
    繼承事件處理器以獲得事件處理和狀態管理功能
    """

    def __init__(self, debug_mode=False):
        super().__init__(debug_mode)
        self.current_angle = 0
        self._stop_flag = threading.Event()
        
    def check_if_stopped(self):
        """
        檢查停止標記是否被設置
        如果已設置則拋出 StopIteration 以中斷執行
        """
        if self._stop_flag.is_set():
            raise StopIteration()
        
    def stop_operation(self):
        """設置停止標記"""
        self._stop_flag.set()
        self.scan_off()

    def clear_stop_flag(self):
        """清除停止標記"""
        self._stop_flag.clear()

    # ========== 位置控制功能 ========== #
    @track_function
    def get_position(self):
        """
        獲取當前位置

        Returns
        -------
        tuple
            (X座標, Y座標)，若讀取失敗則返回(None, None)
        """
        x = self.GetScanPara('X')
        y = self.GetScanPara('Y')
        return (x, y)

    @track_function
    def set_position(self, x, y, verify=True, max_retries=3, retry_delay=1.0):
        """
        增強版位置設定功能

        Parameters
        ----------
        x, y : float
            目標座標
        verify : bool
            是否驗證位置設定
        max_retries : int
            最大重試次數
        retry_delay : float
            重試間隔時間（秒）

        Returns
        -------
        bool
            設定是否成功
        """
        for attempt in range(max_retries):
            try:
                # 發送位置設定命令
                success = (self.SetScanPara('X', x) and
                           self.SetScanPara('Y', y))

                if not success:
                    if self.debug_mode:
                        print(f"Position set failed on attempt {attempt + 1}")
                    time.sleep(retry_delay)
                    continue
                if success:
                    return True

                # 驗證位置
                if verify:
                    verification_success = self.verify_position(x, y)
                    if verification_success:
                        if self.debug_mode:
                            print(f"Position verified at ({x}, {y})")
                        return True

                    if self.debug_mode:
                        print(
                            f"Position verification failed on attempt {attempt + 1}")
                else:
                    return True

            except Exception as e:
                if self.debug_mode:
                    print(
                        f"Error in set_position attempt {attempt + 1}: {str(e)}")

            time.sleep(retry_delay)

        return False

    @track_function
    def verify_position(self, x, y, tolerance=1e-3, max_retries=3):
        """
        驗證位置設定

        Parameters
        ----------
        x, y : float
            目標座標
        tolerance : float
            允許的誤差範圍（nm）
        max_retries : int
            最大重試次數

        Returns
        -------
        bool
            驗證是否通過
        """
        for _ in range(max_retries):
            current_x, current_y = self.get_position()
            print(f"Current position: ({current_x}, {current_y})")
            if (current_x is not None and current_y is not None and
                abs(current_x - x) < tolerance and
                    abs(current_y - y) < tolerance):
                return True
            print(f"abs(current_x - x): {abs(current_x - x)}")
            print(f"abs(current_y - y): {abs(current_y - y)}")
            time.sleep(0.5)
        return False

    # ========== 掃描控制功能 ========== #
    @track_function
    def scan_on(self):
        """開始掃描"""
        return self.SetScanPara('Scan', 1)

    @track_function
    def scan_off(self):
        """停止掃描"""
        return self.SetScanPara('Scan', 0)

    @track_function
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

    @track_function
    def setup_scan_area(self, center_x, center_y, scan_range, angle=0):
        """
        設定掃描區域

        Parameters
        ----------
        center_x, center_y : float
            中心座標（nm）
        scan_range : float
            掃描範圍（nm）
        angle : float, optional
            掃描角度（度）
        pixels : int, optional
            像素數，預設256

        Returns
        -------
        bool
            設定是否全部成功
        """
        try:
            # 設定各項參數
            success = True
            success &= self.SetScanPara('X', center_x)
            success &= self.SetScanPara('Y', center_y)
            success &= self.SetScanPara('Range', scan_range)
            success &= self.SetScanPara('Angle', angle)

            if success:
                self.current_angle = angle

            return success

        except Exception as e:
            if self.debug_mode:
                print(f"Setup scan area error: {str(e)}")
            return False

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
            command = f"ScanLine({num_lines});"
            success, _ = self._send_command(command)

            if not success:
                return False

            # 等待掃描完成
            current_line = 0
            while True:
                if not self.is_scanning():
                    return True

                new_line = self.GetScanPara('LineNr')
                if new_line != current_line:
                    current_line = new_line
                    if self.debug_mode:
                        print(f"Scanning line {current_line}")

                time.sleep(0.1)

        except Exception as e:
            if self.debug_mode:
                print(f"Error during line scan: {str(e)}")
            return False

    def scan_lines_for_sts(self, num_lines: int, timeout: float = None) -> bool:
        """
        執行指定行數的掃描並等待完成，專門為STS測量設計

        Parameters
        ----------
        num_lines : int
            要掃描的行數
        timeout : float, optional
            等待超時時間（秒）。如果不指定，預設為每行10秒

        Returns
        -------
        bool
            掃描是否成功完成
        """
        try:
            if self.debug_mode:
                print(f"開始掃描 {num_lines} 條線")

            # 設定合理的超時時間
            if timeout is None:
                timeout = num_lines * 10  # 每行給10秒

            # 發送掃描命令
            command = f"ScanLine({num_lines});"
            success, _ = self._send_command(command)

            if not success:
                if self.debug_mode:
                    print("發送掃描命令失敗")
                return False

            # 等待掃描開始（短暫延遲）
            # time.sleep(0.5)

            # 使用wait_for_scan_complete等待掃描完成
            if not self.wait_for_scan_complete(timeout):
                if self.debug_mode:
                    print("掃描等待超時")
                return False

            # 額外等待系統穩定
            time.sleep(0.5)

            if self.debug_mode:
                print("掃描完成")
            return True

        except Exception as e:
            if self.debug_mode:
                print(f"掃描過程發生錯誤: {str(e)}")
            return False

    @track_function
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
            True表示掃描完成，False表示超時或被中斷
        """
        start_time = time.time()
        try:
            while True:
                # 檢查掃描狀態
                current_status = self.check_scan()

                # 如果掃描已結束
                if current_status is False:
                    if self.debug_mode:
                        print("Scan completed")
                    return True

                # 檢查超時
                if timeout and (time.time() - start_time > timeout):
                    if self.debug_mode:
                        print("Scan monitoring timeout")
                    return False

                # Windows消息處理
                SXMRemote.loop()

                # 短暫休息以減少CPU使用
                time.sleep(1)

        except KeyboardInterrupt:
            if self.debug_mode:
                print("\nMonitoring interrupted by user")
            return False

    @track_function
    def check_scan(self):
        """
        檢查掃描狀態

        Returns
        -------
        bool or None
            True if scanning, False if not scanning, None if error
        """
        try:

            # 檢查掃描參數
            scan_value = self.GetScanPara('Scan')

            # 處理直接的數值回應
            if isinstance(scan_value, (int, float)):
                is_scanning = bool(scan_value)
                self.scan_status.is_scanning = is_scanning
                if self.debug_mode:
                    print(
                        f"Scan status from direct value: {'On' if is_scanning else 'Off'}")
                return is_scanning

            # 檢查行掃描訊息
            response = self.MySXM.LastAnswer
            if isinstance(response, bytes):
                response_str = str(response, 'utf-8').strip()

                # 檢查掃描行訊息格式
                if len(response_str) > 1 and response_str[0] in ['f', 'b']:
                    try:
                        direction = 'forward' if response_str[0] == 'f' else 'backward'
                        line_number = int(response_str[1:])
                        self.scan_status.is_scanning = True
                        self.scan_status.direction = direction
                        self.scan_status.line_number = line_number
                        if self.debug_mode:
                            print(f"Scanning: {direction} line {line_number}")
                        return True
                    except ValueError:
                        pass

            return False

        except Exception as e:
            if self.debug_mode:
                print(f"Error in check_scan: {str(e)}")
            return None

    # ========== 座標轉換功能 ========== #
    def rotate_coordinates(self, x, y, angle_deg, center_x=0, center_y=0):
        """
        旋轉座標

        Parameters
        ----------
        x, y : float
            原始座標
        angle_deg : float
            旋轉角度（度）
        center_x, center_y : float
            旋轉中心點

        Returns
        -------
        tuple
            (旋轉後的x, 旋轉後的y)
        """
        angle_rad = math.radians(angle_deg)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)

        # 平移到原點
        x_shifted = x - center_x
        y_shifted = y - center_y

        # 旋轉
        x_rot = x_shifted * cos_angle - y_shifted * sin_angle
        y_rot = x_shifted * sin_angle + y_shifted * cos_angle

        # 平移回原位
        return (x_rot + center_x, y_rot + center_y)

    def get_real_coordinates(self, x_nm, y_nm):
        """
        將物理座標轉換為當前掃描範圍內的實際座標

        Parameters
        ----------
        x_nm, y_nm : float
            目標座標（nm）

        Returns
        -------
        tuple
            實際座標，如果超出範圍則進行限制
        """
        try:
            scan_range = self.GetScanPara('Range')
            half_range = scan_range / 2

            # 檢查是否在範圍內
            x_limited = max(-half_range, min(half_range, x_nm))
            y_limited = max(-half_range, min(half_range, y_nm))

            if x_limited != x_nm or y_limited != y_nm:
                if self.debug_mode:
                    print(
                        f"Coordinates limited: ({x_nm}, {y_nm}) -> ({x_limited}, {y_limited})")

            return (x_limited, y_limited)

        except Exception as e:
            if self.debug_mode:
                print(f"Coordinate conversion error: {str(e)}")
            return None

    @track_function
    def perform_scan_sequence(self, repeat_count=1):
        """
        在當前位置執行指定次數的掃描

        Parameters
        ----------
        repeat_count : int
            掃描重複次數

        Returns
        -------
        bool
            所有掃描是否成功完成
        """
        try:
            success = True
            for i in range(repeat_count):
                if self.debug_mode:
                    print(f"Starting scan {i+1}/{repeat_count}")

                # 開始掃描
                self.scan_on()
                if not self.is_scanning():
                    if self.debug_mode:
                        print(f"Failed to start scan {i+1}")
                    success = False
                    break

                # 等待掃描完成
                if self.wait_for_scan_complete():
                    if self.debug_mode:
                        print(f"Scan {i+1} completed")
                else:
                    if self.debug_mode:
                        print(f"Scan {i+1} failed or interrupted")
                    success = False
                    break

                # 掃描之間的短暫暫停
                time.sleep(0.5)

            return success

        except Exception as e:
            if self.debug_mode:
                print(f"Error during scan sequence: {str(e)}")
            return False

    def auto_move(self, movement_script: str, distance: float, center_x: float,
                  center_y: float, angle: float, debug_mode) -> list:
        """
        生成自動移動序列的座標列表

        Parameters
        ----------
        movement_script : str
            移動指令序列，如 "RULLDDRR"
            R: 右, L: 左, U: 上, D: 下
        distance : float
            每次移動的距離（nm）
        center_x : float
            起始中心 X 座標
        center_y : float
            起始中心 Y 座標
        angle : float
            目前的掃描角度

        Returns
        -------
        list
            移動位置的座標列表，格式為 [(x1, y1), (x2, y2), ...]
        """
        try:
            return AutoMoveCalculator.auto_move(movement_script, 
                                                distance, center_x, center_y, 
                                                angle, debug_mode)
        
        except Exception as e:
            if self.debug_mode:
                print(f"Auto move error: {str(e)}")
            raise

    # combine auto_move and perform_scan_sequence
    @track_function
    def auto_move_scan_area(self, movement_script: str, distance: float,
                            wait_time: float, repeat_count: int = 1) -> bool:
        """
        執行自動移動和掃描序列

        Parameters
        ----------
        movement_script : str
            移動指令序列，如 "RULLDDRR"
            R: 右, L: 左, U: 上, D: 下
        distance : float
            每次移動的距離（nm）
        wait_time : float
            每次移動後的等待時間（秒）
        repeat_count : int, optional
            每個位置的掃描重複次數

        Returns
        -------
        bool
            序列是否成功完成
        """
        try:
            # 獲取當前掃描參數
            center_x = self.GetScanPara('X')
            center_y = self.GetScanPara('Y')
            angle = self.GetScanPara('Angle')

            if any(v is None for v in [center_x, center_y, angle]):
                raise ValueError("無法獲取掃描參數")

            if self.debug_mode:
                print(f"Starting auto move scan sequence:")
                print(f"Initial position: ({center_x}, {center_y})")
                print(f"Scan angle: {angle}°")

            # 獲取移動序列的座標列表
            try:
                positions = self.auto_move(
                    movement_script=movement_script,
                    distance=distance,
                    center_x=center_x,
                    center_y=center_y,
                    angle=angle,
                    debug_mode=self.debug_mode
                )

                # 在每個位置執行掃描（包含初始位置）
                for i, (x, y) in enumerate(positions):
                    # 除了初始位置外，需要先移動
                    if i > 0:
                        if self.debug_mode:
                            print(
                                f"\nMoving to position {i}/{len(positions)-1}")

                        # 移動到新位置
                        if not self.set_position(x, y):
                            print(
                                f"Warning: Failed to move to position ({x}, {y})")
                            continue

                        # 等待系統穩定
                        time.sleep(wait_time)

                    # 執行掃描
                    if not self.perform_scan_sequence(repeat_count):
                        position_type = "initial position" if i == 0 else f"position {i}"
                        print(f"Warning: Scan failed at {position_type}")
                        continue

            except Exception as e:
                if self.debug_mode:
                    print(f"Movement sequence error: {str(e)}")
                return False

            if self.debug_mode:
                print("\nAuto move scan sequence completed successfully")
            return True

        except Exception as e:
            if self.debug_mode:
                print(f"Auto move scan error: {str(e)}")
            return False


    # ========== Scan Ratio and Aspect Ratio ========== #

    def get_pixel_ratio(self) -> float:
        """
        獲取Pixel Density值

        Returns
        -------
        float
            Pixel Density比例，預設為1.0
        """
        try:
            ratio = self.GetScanPara('PixelRatio')
            if ratio is not None:
                self.current_state['pixel_ratio'] = ratio
            return ratio if ratio is not None else self.current_state['pixel_ratio']
        except Exception as e:
            if self.debug_mode:
                print(f"Error getting pixel ratio: {str(e)}")
            return self.current_state['pixel_ratio']

    def get_aspect_ratio(self) -> float:
        """
        獲取Image Format值

        Returns
        -------
        float
            Image Format比例，預設為1.0
        """
        try:
            ratio = self.GetScanPara('AspectRatio')
            if ratio is not None:
                self.current_state['aspect_ratio'] = ratio
            return ratio if ratio is not None else self.current_state['aspect_ratio']
        except Exception as e:
            if self.debug_mode:
                print(f"Error getting aspect ratio: {str(e)}")
            return self.current_state['aspect_ratio']

    def calculate_actual_scan_dimensions(self) -> tuple:
        """
        計算實際的掃描範圍尺寸

        當image format改變時，會影響慢軸的掃描範圍。
        例如：當image format設為0.5時，慢軸掃描範圍會是原來的兩倍。

        Returns
        -------
        tuple
            (快軸範圍, 慢軸範圍) 單位nm
        """
        try:
            scan_range = self.current_state['range']
            aspect_ratio = self.get_aspect_ratio()

            if scan_range is None:
                scan_range = self.GetScanPara('Range')

            if scan_range is None or aspect_ratio is None:
                return (None, None)

            fast_axis_range = scan_range
            slow_axis_range = scan_range / aspect_ratio  # 當aspect_ratio < 1時，慢軸範圍會變大

            return (fast_axis_range, slow_axis_range)

        except Exception as e:
            if self.debug_mode:
                print(f"Error calculating scan dimensions: {str(e)}")
            return (None, None)

    def calculate_scan_lines(self) -> tuple:
        """
        計算實際的掃描線數和間距

        掃描線數會受到image format和pixel density的共同影響：
        1. 當image format變小（例如0.5）時，慢軸範圍變大，掃描線數會等比例增加
        2. 當pixel density變小（例如0.5）時，每個pixel會再分成更多條線

        Returns
        -------
        tuple
            (掃描線數, 線間距nm)
            如果計算失敗則返回(None, None)
        """
        try:
            # 取得必要參數
            pixels = self.GetScanPara('Pixel')
            pixel_ratio = self.get_pixel_ratio()
            aspect_ratio = self.get_aspect_ratio()

            if any(x is None for x in [pixels, pixel_ratio, aspect_ratio]):
                return (None, None)

            # 計算實際掃描範圍
            _, slow_axis_range = self.calculate_actual_scan_dimensions()

            # 計算實際掃描線數
            # 1. 基礎線數等於pixel數
            # 2. 因image format改變而增加的線數：除以aspect_ratio
            # 3. 因pixel density改變而增加的線數：除以pixel_ratio
            total_lines = int(pixels / (aspect_ratio * pixel_ratio))

            # 計算線間距
            line_spacing = slow_axis_range / total_lines if total_lines > 0 else None

            return (total_lines, line_spacing)

        except Exception as e:
            if self.debug_mode:
                print(f"Error calculating scan lines: {str(e)}")
            return (None, None)

    def get_sxm_status(self) -> dict:
        """
        獲取STM當前的掃描參數和狀態

        Returns
        -------
        dict
            包含所有掃描相關參數的字典，包括：
            - center_x, center_y: 掃描中心座標 (nm)
            - range: 設定的掃描範圍 (nm)
            - angle: 掃描角度 (度)
            - fast_axis_range: 快軸實際掃描範圍 (nm)
            - slow_axis_range: 慢軸實際掃描範圍 (nm)
            - total_lines: 總掃描線數
            - line_spacing: 掃描線間距 (nm)
            - pixel_ratio: 像素密度比例
            - aspect_ratio: 影像長寬比例
        """
        try:
            # 基本掃描參數
            center_x = self.GetScanPara('X')
            center_y = self.GetScanPara('Y')
            range_value = self.GetScanPara('Range')
            angle = self.GetScanPara('Angle')

            # 計算實際掃描範圍
            fast_axis_range, slow_axis_range = self.calculate_actual_scan_dimensions()

            # 計算掃描線參數
            total_lines, line_spacing = self.calculate_scan_lines()

            # 獲取比例參數
            pixel_ratio = self.get_pixel_ratio()
            aspect_ratio = self.get_aspect_ratio()

            return {
                'center_x': center_x,
                'center_y': center_y,
                'range': range_value,
                'angle': angle,
                'fast_axis_range': fast_axis_range,
                'slow_axis_range': slow_axis_range,
                'total_lines': total_lines,
                'line_spacing': line_spacing,
                'pixel_ratio': pixel_ratio,
                'aspect_ratio': aspect_ratio,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            raise ValueError(f"獲取掃描狀態失敗: {str(e)}")
