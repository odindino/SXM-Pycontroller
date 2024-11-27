# modules/SXMPyCITS.py

import time
import math
from .SXMPySpectro import SXMSpectroControl
from utils.SXMPyCalc import CITSCalculator

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

    def standard_cits(self, num_points_x: int, num_points_y: int, 
                 scan_direction: int = 1) -> bool:
        """
        執行標準 CITS 量測
        
        Parameters
        ----------
        num_points_x : int
            X方向量測點數
        num_points_y : int
            Y方向量測點數
        scan_direction : int
            掃描方向 (1: 由下到上, -1: 由上到下)
        
        Returns
        -------
        bool
            量測是否成功完成
        """
        try:
            # 獲取當前掃描參數
            center_x = self.GetScanPara('X')
            center_y = self.GetScanPara('Y')
            scan_range = self.GetScanPara('Range')
            scan_angle = self.GetScanPara('Angle')
            total_lines = self.GetScanPara('Pixel')
            
            if any(v is None for v in [center_x, center_y, scan_range, scan_angle, total_lines]):
                raise ValueError("無法獲取掃描參數")
            
            # 計算CITS座標和掃描線分配
            coordinates, _, _, scanlines = CITSCalculator.calculate_cits_coordinates(
                center_x, center_y, scan_range, scan_angle,
                num_points_x, num_points_y, total_lines, scan_direction
            )
            
            if self.debug_mode:
                print(f"掃描線分配: {scanlines}")
                print(f"總掃描線數: {sum(scanlines)}")
            
            # 執行量測循環
            for i, (sts_line, scan_count) in enumerate(zip(coordinates, scanlines[:-1])):
                # 掃描指定的線數
                if scan_count > 0:
                    self.scan_on()
                    if not self.scan_lines(scan_count):
                        raise RuntimeError(f"掃描第 {i} 段失敗")
                    self.scan_off()
                
                # 執行該行的 STS 量測
                if self.debug_mode:
                    print(f"執行第 {i+1}/{num_points_y} 條 STS 線")
                
                for j, (x, y) in enumerate(sts_line):
                    if self.debug_mode:
                        print(f"STS 點 ({x:.3f}, {y:.3f})")
                    
                    success = self.simple_spectroscopy(x, y)
                    if not success:
                        raise RuntimeError(f"STS 量測失敗於點 ({x}, {y})")
            
            # 執行最後一段掃描（如果有的話）
            if scanlines[-1] > 0:
                self.scan_on()
                if not self.scan_lines(scanlines[-1]):
                    raise RuntimeError("最後一段掃描失敗")
                self.scan_off()
            
            return True
            
        except Exception as e:
            if self.debug_mode:
                print(f"CITS 量測錯誤: {str(e)}")
            return False
            
        finally:
            # 確保掃描結束時回到正確狀態
            self.scan_off()
            self.feedback_on()

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