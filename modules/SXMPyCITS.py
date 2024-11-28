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
    
    def standard_cits(self, num_points_x: int, num_points_y: int, scan_direction: int = 1) -> bool:
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
            # 獲取掃描參數
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
                print(f"開始CITS量測:")
                print(f"掃描線分配: {scanlines}")
                print(f"總掃描線數: {sum(scanlines)}")
            
            # 執行量測循環
            for i, (sts_line, scan_count) in enumerate(zip(coordinates, scanlines[:-1])):
                # 執行掃描
                if scan_count > 0:
                    if self.debug_mode:
                        print(f"\n=== 掃描第 {i+1} 段 {scan_count} 條線 ===")
                    
                    # 使用新的scan_lines_for_sts函數
                    if not self.scan_lines_for_sts(scan_count):
                        raise RuntimeError(f"掃描第 {i+1} 段失敗")
                
                # 執行STS線電性
                if self.debug_mode:
                    print(f"\n>>> 執行第 {i+1}/{num_points_y} 條 STS 線")
                
                for j, (x, y) in enumerate(sts_line):
                    try:
                        if self.debug_mode:
                            print(f"  STS點 ({j+1}/{len(sts_line)}): ({x:.3f}, {y:.3f})")
                        
                        # 移動探針
                        if not self.move_tip_for_spectro(x, y):
                            raise RuntimeError(f"移動探針失敗: ({x}, {y})")
                        
                        # 執行STS測量
                        success = self.spectroscopy_start()
                        if not success:
                            raise RuntimeError(f"STS測量失敗: ({x}, {y})")
                        
                        # 等待STS測量完成
                        time.sleep(1.0)  # 暫時使用固定等待時間
                        
                    except Exception as e:
                        print(f"STS點測量失敗 ({x}, {y}): {str(e)}")
                        continue
                
                if self.debug_mode:
                    print(f"<<< 完成第 {i+1}/{num_points_y} 條 STS 線")
            
            # 執行最後一段掃描（如果有的話）
            if scanlines[-1] > 0:
                if self.debug_mode:
                    print(f"\n=== 執行最後 {scanlines[-1]} 條掃描線 ===")
                if not self.scan_lines_for_sts(scanlines[-1]):
                    print("警告: 最後一段掃描失敗")
            
            if self.debug_mode:
                print("\nCITS量測完成")
            return True
            
        except Exception as e:
            if self.debug_mode:
                print(f"\nCITS量測錯誤: {str(e)}")
            return False
            
        finally:
            # 確保回到正確狀態
            self.feedback_on()

    # def define_cits_area(self, start_x, start_y, width, height):
    #     """
    #     定義CITS測量區域
        
    #     Parameters
    #     ----------
    #     start_x, start_y : float
    #         起始座標（nm）
    #     width, height : float
    #         區域寬度和高度（nm）
            
    #     Returns
    #     -------
    #     dict
    #         測量區域定義
    #     """
    #     try:
    #         angle = self.GetScanPara('Angle')
    #         center_x = self.GetScanPara('X')
    #         center_y = self.GetScanPara('Y')

    #         # 計算四個角點
    #         corners = [
    #             (start_x, start_y),                    # 左下
    #             (start_x + width, start_y),            # 右下
    #             (start_x + width, start_y + height),   # 右上
    #             (start_x, start_y + height)            # 左上
    #         ]

    #         # 轉換到實際座標
    #         real_corners = []
    #         for x, y in corners:
    #             real_coords = self.get_real_coordinates(x, y)
    #             if real_coords is None:
    #                 raise ValueError("Invalid coordinates")
    #             real_corners.append(real_coords)

    #         return {
    #             'corners': real_corners,
    #             'start_x': real_corners[0][0],
    #             'start_y': real_corners[0][1],
    #             'width': width,
    #             'height': height,
    #             'angle': angle
    #         }

    #     except Exception as e:
    #         if self.debug_mode:
    #             print(f"Error defining CITS area: {str(e)}")
    #         return None