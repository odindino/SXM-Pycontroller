# modules/SXMPyCITS.py

import time
import math
from .SXMPySpectro import SXMSpectroControl

class SXMCITSControl(SXMSpectroControl):
    """
    CITS（電流成像隧道掃描）控制類別
    繼承光譜測量控制以獲得掃描、位置和光譜測量功能
    """
    
    def __init__(self, debug_mode=False):
        super().__init__(debug_mode)
        self.default_sts_params = {
            'start_bias': -2.0,  # 起始偏壓 (V)
            'end_bias': 2.0,     # 結束偏壓 (V)
            'points': 200,       # 測量點數
            'delay': 100         # 每點延遲時間 (ms)
        }

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
            # 獲取當前掃描參數
            scan_range = self.GetScanPara('Range')
            scan_angle = self.GetScanPara('Angle')
            pixels = self.GetScanPara('Pixel')
            center_x, center_y = self.get_position()

            if self.debug_mode:
                print(f"Scan center: ({center_x:.3f}, {center_y:.3f})")
                print(f"Scan angle: {scan_angle}°")

            # 計算實際範圍（考慮安全邊距）
            safe_margin = 0.02  # 2% 的安全邊距
            effective_range = scan_range * (1 - safe_margin)
            half_range = effective_range / 2

            # 計算起始點（相對於中心點）
            if scan_direction == 1:  # 向上掃描
                rel_x = -half_range  # 從左邊開始
                rel_y = -half_range  # 從下面開始
            else:  # 向下掃描
                rel_x = -half_range  # 從左邊開始
                rel_y = half_range   # 從上面開始

            # 將起始點旋轉到實際角度
            start_x, start_y = self.rotate_coordinates(
                rel_x, rel_y,
                scan_angle,
                center_x, center_y
            )

            # 計算步長
            dx = effective_range / (num_points_x - 1)
            dy = effective_range / (num_points_y - 1)
            if scan_direction == -1:
                dy = -dy

            # 計算旋轉後的步長
            dx_rot, dy_temp = self.rotate_coordinates(dx, 0, scan_angle, 0, 0)
            temp_x, dy_rot = self.rotate_coordinates(0, dy, scan_angle, 0, 0)

            return {
                'start_x': start_x,
                'start_y': start_y,
                'dx': dx_rot,
                'dy': dy_rot,
                'center_x': center_x,
                'center_y': center_y,
                'lines_per_sts': pixels // (num_points_y + 1),
                'scan_angle': scan_angle,
                'total_lines': pixels,
                'effective_range': effective_range,
                'scan_direction': scan_direction
            }

        except Exception as e:
            if self.debug_mode:
                print(f"Error calculating CITS parameters: {str(e)}")
            return None

    def standard_cits(self, num_points_x, num_points_y, scan_direction=1, sts_params=None):
        """
        執行標準CITS測量
        
        Parameters
        ----------
        num_points_x : int
            X方向測量點數
        num_points_y : int
            Y方向測量點數
        scan_direction : int
            掃描方向：1向上，-1向下
        sts_params : dict, optional
            STS測量參數，如果未提供則使用默認值
            
        Returns
        -------
        bool
            測量是否成功完成
        """
        try:
            if sts_params is None:
                sts_params = self.default_sts_params

            # 檢查當前掃描狀態
            current_scanning = self.is_scanning()
            if not current_scanning:
                if self.debug_mode:
                    print("Starting new scan")
                self.scan_on()
                time.sleep(0.5)

            # 計算CITS參數
            params = self.calculate_cits_parameters(
                num_points_x, num_points_y, scan_direction
            )
            if not params:
                raise ValueError("Failed to calculate CITS parameters")

            if self.debug_mode:
                print("\nStarting standard CITS measurement:")
                print(f"Center position: ({params['center_x']:.3f}, {params['center_y']:.3f})")
                print(f"Starting position: ({params['start_x']:.3f}, {params['start_y']:.3f})")
                print(f"Step sizes: dx={params['dx']:.3f}, dy={params['dy']:.3f}")
                print(f"Points: {num_points_x}x{num_points_y}")
                print(f"Lines per STS: {params['lines_per_sts']}")

            # 執行CITS測量
            current_line = 0
            completed_points = 0
            total_points = num_points_x * num_points_y

            for y_idx in range(num_points_y):
                # 計算當前行位置
                current_y = params['start_y'] + y_idx * params['dy']

                # 掃描到適當的行
                lines_to_scan = params['lines_per_sts']
                if self.debug_mode:
                    print(f"\nScanning {lines_to_scan} lines before STS line {y_idx + 1}/{num_points_y}")

                if not self.scan_lines(lines_to_scan):
                    raise RuntimeError("Failed to scan lines")

                current_line += lines_to_scan
                if self.debug_mode:
                    print(f"Current scan line: {current_line}/{params['total_lines']}")

                # 執行當前行的STS測量
                if self.debug_mode:
                    print(f"Performing STS measurements on line {y_idx + 1}")

                for x_idx in range(num_points_x):
                    current_x = params['start_x'] + x_idx * params['dx']
                    
                    completed_points += 1
                    progress = (completed_points / total_points) * 100
                    
                    if self.debug_mode:
                        print(f"STS point {completed_points}/{total_points} "
                              f"({progress:.1f}%) at ({current_x:.3f}, {current_y:.3f})")
                    
                    success = self.perform_spectroscopy(
                        current_x, 
                        current_y, 
                        wait_time=0.5,
                        params=sts_params
                    )
                    
                    if not success and self.debug_mode:
                        print(f"Warning: STS measurement failed at point {completed_points}")

                # 檢查是否接近圖像結束
                remaining_lines = params['total_lines'] - current_line
                if remaining_lines < params['lines_per_sts']:
                    if self.debug_mode:
                        print("Approaching end of scan, stopping CITS")
                    break

            if self.debug_mode:
                print("\nCITS measurement completed")
                print(f"Total points measured: {completed_points}/{total_points}")

            return True

        except Exception as e:
            if self.debug_mode:
                print(f"Error during CITS: {str(e)}")
            return False
            
        finally:
            # 確保掃描繼續
            if not current_scanning:
                self.scan_off()

    def define_cits_area(self, start_x, start_y, width, height):
        """
        定義CITS測量區域
        
        Parameters
        ----------
        start_x, start_y : float
            起始座標（nm）
        width, height : float
            區域寬度和高度（nm）
            
        Returns
        -------
        dict
            測量區域定義
        """
        try:
            angle = self.GetScanPara('Angle')
            center_x = self.GetScanPara('X')
            center_y = self.GetScanPara('Y')

            # 計算四個角點
            corners = [
                (start_x, start_y),                    # 左下
                (start_x + width, start_y),            # 右下
                (start_x + width, start_y + height),   # 右上
                (start_x, start_y + height)            # 左上
            ]

            # 轉換到實際座標
            real_corners = []
            for x, y in corners:
                real_coords = self.get_real_coordinates(x, y)
                if real_coords is None:
                    raise ValueError("Invalid coordinates")
                real_corners.append(real_coords)

            return {
                'corners': real_corners,
                'start_x': real_corners[0][0],
                'start_y': real_corners[0][1],
                'width': width,
                'height': height,
                'angle': angle
            }

        except Exception as e:
            if self.debug_mode:
                print(f"Error defining CITS area: {str(e)}")
            return None