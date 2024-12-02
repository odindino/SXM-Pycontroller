# modules/SXMPyCITS.py

import time
import math
from .SXMPySpectro import SXMSpectroControl
from utils.SXMPyCalc import CITSCalculator, LocalCITSCalculator, LocalCITSParams
from typing import List


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
            # total_lines = self.GetScanPara('Pixel')
            (total_lines, line_spacing) = self.calculate_scan_lines()
            aspect_ratio = self.get_aspect_ratio()

            if any(v is None for v in [center_x, center_y, scan_range, scan_angle, total_lines]):
                raise ValueError("無法獲取掃描參數")

            # 計算CITS座標和掃描線分配
            coordinates, _, _, scanlines = CITSCalculator.calculate_cits_coordinates(
                center_x, center_y, scan_range, scan_angle,
                num_points_x, num_points_y, total_lines, scan_direction, aspect_ratio
            )

            # check coordinates
            print(f"coordinates: {coordinates}")

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
                            print(
                                f"  STS點 ({j+1}/{len(sts_line)}): ({x:.3f}, {y:.3f})")

                        if not self.simple_spectroscopy(x, y):
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
            if self.debug_mode:
                print("feedback on")

    def standard_local_cits(self, local_areas: List[LocalCITSParams], scan_direction: int = 1) -> bool:
        """
        執行局部區域 CITS 量測

        此函數將在指定的局部區域內執行 CITS 量測，整合了掃描和 STS 量測功能。
        執行流程為：掃描線 -> STS 量測點 -> 掃描線 -> STS 量測點，依此循環直到完成所有區域。

        Parameters
        ----------
        local_areas : List[LocalCITSParams]
            要執行 CITS 的局部區域參數列表，每個區域包含：
            - 起始位置 (start_x, start_y)
            - 步進大小 (dx, dy)
            - 點數 (nx, ny)
            - 起始點方向 (startpoint_direction)
        scan_direction : int, optional
            掃描方向，1 表示由下到上，-1 表示由上到下

        Returns
        -------
        bool
            量測是否成功完成
        """
        try:
            # 獲取掃描參數
            center_x = self.GetScanPara('X')
            center_y = self.GetScanPara('Y')

            # scan_range here is the slow axis range
            (_, scan_range) = self.calculate_actual_scan_dimensions()
            # scan_range = self.GetScanPara('Range')
            scan_angle = self.GetScanPara('Angle')
            # total_lines = self.GetScanPara('Pixel')
            (total_lines, line_spacing) = self.calculate_scan_lines()

            if any(v is None for v in [center_x, center_y, scan_range, scan_angle, total_lines]):
                raise ValueError("無法獲取掃描參數")

            if self.debug_mode:
                print(f"\n開始局部 CITS 量測:")
                print(f"中心位置: ({center_x}, {center_y}) nm")
                print(f"掃描範圍: {scan_range} nm")
                print(f"掃描角度: {scan_angle}°")

            # 計算所有區域的座標點
            coordinates, _, _, (slow_axis, fast_axis) = LocalCITSCalculator.combi_local_cits_coordinates(
                center_x, center_y, scan_range, scan_angle,
                total_lines, scan_direction, local_areas
            )

            # 計算掃描線分配和座標群組
            scanline_distribution, coordinate_distribution = LocalCITSCalculator.calculate_local_scanline_distribution(
                coordinates, center_x, center_y, scan_angle,
                scan_range, scan_direction, total_lines
            )

            if self.debug_mode:
                print(f"掃描線分配: {scanline_distribution}")
                print(f"座標群組數: {len(coordinate_distribution)}")
                print(
                    f"總量測點數: {sum(len(coords) for coords in coordinate_distribution)}")

            # 執行量測循環
            for i, (coords_group, scan_count) in enumerate(zip(coordinate_distribution, scanline_distribution[:-1])):
                # 執行掃描線
                if scan_count > 0:
                    if self.debug_mode:
                        print(f"\n=== 掃描第 {i+1} 段 {scan_count} 條線 ===")

                    if not self.scan_lines_for_sts(scan_count):
                        raise RuntimeError(f"掃描第 {i+1} 段失敗")

                # 執行該群組的 STS 量測
                if self.debug_mode:
                    print(
                        f"\n>>> 執行第 {i+1}/{len(coordinate_distribution)} 群組的 STS 量測")

                for j, (x, y) in enumerate(coords_group):
                    try:
                        if self.debug_mode:
                            print(
                                f"  STS點 ({j+1}/{len(coords_group)}): ({x:.3f}, {y:.3f})")

                        # 執行單點 STS 量測
                        if not self.simple_spectroscopy(x, y):
                            print(f"警告: 位置 ({x}, {y}) 的 STS 量測失敗")
                            continue

                        # 等待 STS 完成
                        time.sleep(1.0)

                    except Exception as e:
                        print(f"STS點量測失敗 ({x}, {y}): {str(e)}")
                        continue

                if self.debug_mode:
                    print(f"<<< 完成第 {i+1}/{len(coordinate_distribution)} 群組")

            # 執行最後一段掃描
            if scanline_distribution[-1] > 0:
                if self.debug_mode:
                    print(f"\n=== 執行最後 {scanline_distribution[-1]} 條掃描線 ===")
                if not self.scan_lines_for_sts(scanline_distribution[-1]):
                    print("警告: 最後一段掃描失敗")

            if self.debug_mode:
                print("\n局部 CITS 量測完成")
            return True

        except Exception as e:
            if self.debug_mode:
                print(f"\n局部 CITS 量測錯誤: {str(e)}")
            return False

        finally:
            # 確保回到安全狀態
            try:
                self.feedback_on()
                if self.debug_mode:
                    print("系統回到安全狀態")
            except Exception as e:
                print(f"回復安全狀態時發生錯誤: {str(e)}")
