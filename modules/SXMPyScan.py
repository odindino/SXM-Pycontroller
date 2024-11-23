import time
import math
from . import SXMRemote
from .SXMPyEvent import SXMEventHandler


class SXMScanControl(SXMEventHandler):
    """
    掃描控制和位置控制類別
    繼承事件處理器以獲得事件處理和狀態管理功能
    """
    def __init__(self, debug_mode=False):
        super().__init__(debug_mode)
        self.current_angle = 0
    
    # ========== 位置控制功能 ========== #
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
                    
                # 驗證位置
                if verify:
                    verification_success = self.verify_position(x, y)
                    if verification_success:
                        if self.debug_mode:
                            print(f"Position verified at ({x}, {y})")
                        return True
                        
                    if self.debug_mode:
                        print(f"Position verification failed on attempt {attempt + 1}")
                else:
                    return True
                    
            except Exception as e:
                if self.debug_mode:
                    print(f"Error in set_position attempt {attempt + 1}: {str(e)}")
                    
            time.sleep(retry_delay)
            
        return False

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
    def scan_on(self):
        """開始掃描"""
        return self.SetScanPara('Scan', 1)
        
    def scan_off(self):
        """停止掃描"""
        return self.SetScanPara('Scan', 0)

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

    def wait_for_scan_complete(self, timeout=None, check_interval=1):
        """
        等待掃描完成，增強版本
        
        Parameters
        ----------
        timeout : float, optional
            等待超時時間（秒）
        check_interval : float
            狀態檢查間隔（秒）
            
        Returns
        -------
        bool
            True表示掃描完成，False表示超時或被中斷
        """
        start_time = time.time()
        last_line_number = None
        stable_count = 0
        required_stable_counts = 3  # 需要連續幾次確認才算真的停止
        
        try:
            while True:
                # 檢查掃描狀態
                scan_status = self.check_scan()
                
                if scan_status is None:
                    if self.debug_mode:
                        print("Error checking scan status")
                    return False
                    
                # 如果明確返回False（掃描已停止）
                if scan_status is False:
                    if self.debug_mode:
                        print("Scan explicitly reported as stopped")
                    return True
                    
                # 檢查是否正在掃描
                current_line = self.GetScanPara('LineNr')
                
                if current_line == last_line_number:
                    stable_count += 1
                    if stable_count >= required_stable_counts:
                        if self.debug_mode:
                            print(f"Scan line number stable at {current_line} for {required_stable_counts} checks")
                        return True
                else:
                    stable_count = 0
                    last_line_number = current_line
                    
                # 檢查超時
                if timeout and (time.time() - start_time > timeout):
                    if self.debug_mode:
                        print("Scan monitoring timeout")
                    return False
                    
                # Windows消息處理
                SXMRemote.loop()

                # 減少CPU使用率
                time.sleep(check_interval)
                
        except Exception as e:
            if self.debug_mode:
                print(f"Error in wait_for_scan_complete: {str(e)}")
            return False
        
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
                    print(f"Scan status from direct value: {'On' if is_scanning else 'Off'}")
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
                    print(f"Coordinates limited: ({x_nm}, {y_nm}) -> ({x_limited}, {y_limited})")
                    
            return (x_limited, y_limited)
            
        except Exception as e:
            if self.debug_mode:
                print(f"Coordinate conversion error: {str(e)}")
            return None
        

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

    def auto_move_scan_area(self, movement_script, distance, wait_time, repeat_count=1):
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
            # 記錄初始位置和角度
            self.current_angle = self.GetScanPara('Angle')
            x, y = self.get_position()
            
            if self.debug_mode:
                print(f"Starting position: ({x}, {y}), Angle: {self.current_angle}°")
            
            # 執行初始位置的掃描
            if not self.perform_scan_sequence(repeat_count):
                if self.debug_mode:
                    print("Initial position scan failed")
                return False

            # 執行移動和掃描序列
            for i, direction in enumerate(movement_script):
                if self.debug_mode:
                    print(f"\nMoving to position {i+1}/{len(movement_script)}")

                try:
                    # 計算新位置
                    dx, dy = self.calculate_movement(direction, distance)
                    new_x = x + dx
                    new_y = y + dy

                    if self.debug_mode:
                        print(f"Moving to: ({new_x}, {new_y})")
                    
                    # 移動到新位置
                    if not self.set_position(new_x, new_y):
                        if self.debug_mode:
                            print("Failed to move to new position")
                        return False

                    # 等待系統穩定
                    time.sleep(wait_time)

                    # 更新當前位置
                    x, y = new_x, new_y

                    # 執行掃描
                    if not self.perform_scan_sequence(repeat_count):
                        if self.debug_mode:
                            print(f"Scan sequence failed at position {i+1}")
                        return False

                except Exception as e:
                    if self.debug_mode:
                        print(f"Error at position {i+1}: {str(e)}")
                    return False

            if self.debug_mode:
                print("\nMovement sequence completed successfully")
            return True

        except Exception as e:
            if self.debug_mode:
                print(f"Error during auto move sequence: {str(e)}")
            return False

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