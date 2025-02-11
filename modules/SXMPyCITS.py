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
            # 開始新操作前先清除停止標記
            self.clear_stop_flag()
            
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
                self.check_if_stopped()
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
                    self.check_if_stopped()
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
            self.clear_stop_flag()
            # 獲取掃描參數
            center_x = self.GetScanPara('X')
            center_y = self.GetScanPara('Y')

            # scan_range here is the slow axis range
            (_, slow_axis_range) = self.calculate_actual_scan_dimensions()
            # scan_range = self.GetScanPara('Range')
            scan_angle = self.GetScanPara('Angle')
            # total_lines = self.GetScanPara('Pixel')
            (total_lines, line_spacing) = self.calculate_scan_lines()

            if any(v is None for v in [center_x, center_y, slow_axis_range, scan_angle, total_lines]):
                raise ValueError("無法獲取掃描參數")

            if self.debug_mode:
                print(f"\n開始局部 CITS 量測:")
                print(f"中心位置: ({center_x}, {center_y}) nm")
                print(f"掃描慢軸範圍: {slow_axis_range} nm")
                print(f"掃描角度: {scan_angle}°")

            # 計算所有區域的座標點
            coordinates, _, _, (slow_axis, fast_axis) = LocalCITSCalculator.combi_local_cits_coordinates(
                center_x, center_y, slow_axis_range, scan_angle,
                total_lines, scan_direction, local_areas
            )

            # 計算掃描線分配和座標群組
            scanline_distribution, coordinate_distribution = LocalCITSCalculator.calculate_local_scanline_distribution(
                coordinates, center_x, center_y, scan_angle,
                slow_axis_range, scan_direction, total_lines
            )

            if self.debug_mode:
                print(f"掃描線分配: {scanline_distribution}")
                print(f"座標群組數: {len(coordinate_distribution)}")
                print(
                    f"總量測點數: {sum(len(coords) for coords in coordinate_distribution)}")

            # 執行量測循環
            for i, (coords_group, scan_count) in enumerate(zip(coordinate_distribution, scanline_distribution[:-1])):
                self.check_if_stopped()
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
                    self.check_if_stopped()
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

    # Auto-move CITS, the combination of auto-move and CITS
    def auto_move_ssts_CITS(self, movement_script: str, distance: float,
                            num_points_x: int, num_points_y: int,
                            initial_direction: int = 1,
                            wait_time: float = 1.0,
                            repeat_count: int = 1) -> bool:
        """
        執行自動移動和 CITS 量測序列，在每個移動位置進行 CITS 量測

        Parameters
        ----------
        movement_script : str
            移動指令序列，如 "RULLDDRR"
            R: 右, L: 左, U: 上, D: 下
        distance : float
            每次移動的距離（nm）
        num_points_x : int
            CITS X 方向的點數（1-512）
        num_points_y : int
            CITS Y 方向的點數（1-512）
        initial_direction : int, optional
            起始CITS掃描方向（1: 由下到上, -1: 由上到下）
        wait_time : float, optional
            每次移動後的等待時間（秒）
        repeat_count : int, optional
            每個位置的CITS重複次數

        Returns
        -------
        bool
            序列是否成功完成
        """
        try:
            self.clear_stop_flag()
            # 驗證 CITS 參數
            if not (1 <= num_points_x <= 512 and 1 <= num_points_y <= 512):
                raise ValueError("CITS 點數必須在 1 到 512 之間")

            if initial_direction not in (1, -1):
                raise ValueError("掃描方向必須是 1 (向上) 或 -1 (向下)")

            if repeat_count < 1:
                raise ValueError("重複次數必須大於 0")

            # 獲取當前掃描參數
            center_x = self.GetScanPara('X')
            center_y = self.GetScanPara('Y')
            angle = self.GetScanPara('Angle')

            if any(v is None for v in [center_x, center_y, angle]):
                raise ValueError("無法獲取掃描參數")

            if self.debug_mode:
                print(f"\nStarting auto move CITS sequence:")
                print(f"Initial position: ({center_x}, {center_y})")
                print(f"Scan angle: {angle}°")
                print(f"CITS points: {num_points_x}x{num_points_y}")
                print(f"Repeat count: {repeat_count}")

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

                # 追蹤當前掃描方向
                current_direction = initial_direction

                # 在每個位置執行 CITS（包含初始位置）
                for i, (x, y) in enumerate(positions):
                    self.check_if_stopped()
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

                    position_type = "initial position" if i == 0 else f"position {i}"

                    # 在當前位置重複執行CITS
                    for repeat in range(repeat_count):
                        self.check_if_stopped()
                        if self.debug_mode:
                            print(f"Starting CITS at {position_type}, "
                                  f"repeat {repeat + 1}/{repeat_count}, "
                                  f"direction: {'up' if current_direction == 1 else 'down'}")

                        # 執行 CITS 量測
                        if not self.standard_cits(
                            num_points_x=num_points_x,
                            num_points_y=num_points_y,
                            scan_direction=current_direction
                        ):
                            print(f"Warning: CITS failed at {position_type}, "
                                  f"repeat {repeat + 1}")
                            continue

                        # 等待CITS完成
                        while self.is_scanning():
                            time.sleep(1)

                        # 反轉掃描方向
                        current_direction *= -1

                        # 如果不是最後一次重複，則等待系統穩定
                        if repeat < repeat_count - 1:
                            time.sleep(wait_time)

            except Exception as e:
                if self.debug_mode:
                    print(f"CITS sequence error: {str(e)}")
                return False

            if self.debug_mode:
                print("\nAuto move CITS sequence completed successfully")
            return True

        except Exception as e:
            if self.debug_mode:
                print(f"Auto move CITS error: {str(e)}")
            return False

    def auto_move_local_ssts_CITS(self, movement_script: str, distance: float,
                                  local_areas_params: List[dict],
                                  initial_direction: int = 1,
                                  wait_time: float = 1.0,
                                  repeat_count: int = 1) -> bool:
        """
        執行自動移動和 Local CITS 量測序列，在每個移動位置的多個相對偏移區域進行 Local CITS 量測

        Parameters
        ----------
        movement_script : str
            移動指令序列，如 "RULLDDRR"
            R: 右, L: 左, U: 上, D: 下
        distance : float
            每次移動的距離（nm）
        local_areas_params : List[dict]
            小區參數列表，每個字典包含：
            {
                'x_dev': float,  # 相對於掃描中心的X偏移（nm）
                'y_dev': float,  # 相對於掃描中心的Y偏移（nm）
                'nx': int,      # X方向點數
                'ny': int,      # Y方向點數
                'dx': float,    # X方向步進（nm）
                'dy': float,    # Y方向步進（nm）
                'startpoint_direction': int  # 起始點方向（1: 向上, -1: 向下）
            }
        initial_direction : int, optional
            CITS掃描方向（1: 由下到上, -1: 由上到下）
        wait_time : float, optional
            每次移動後的等待時間（秒）
        repeat_count : int, optional
            每個位置的CITS重複次數

        Returns
        -------
        bool
            序列是否成功完成
        """
        try:
            self.clear_stop_flag()
            # 參數驗證
            if not local_areas_params:
                raise ValueError("必須提供至少一個小區參數")

            # 驗證每個小區的參數
            for i, params in enumerate(local_areas_params):
                if not all(key in params for key in ['x_dev', 'y_dev', 'nx', 'ny', 'dx', 'dy', 'startpoint_direction']):
                    raise ValueError(f"小區 {i} 缺少必要參數")

                if not (1 <= params['nx'] <= 512 and 1 <= params['ny'] <= 512):
                    raise ValueError(f"小區 {i} 的點數必須在 1 到 512 之間")

                if params['startpoint_direction'] not in (1, -1):
                    raise ValueError(f"小區 {i} 的起始點方向必須是 1 (向上) 或 -1 (向下)")

            if initial_direction not in (1, -1):
                raise ValueError("掃描方向必須是 1 (向上) 或 -1 (向下)")

            if repeat_count < 1:
                raise ValueError("重複次數必須大於 0")

            # 獲取當前掃描參數
            center_x = self.GetScanPara('X')
            center_y = self.GetScanPara('Y')
            angle = self.GetScanPara('Angle')

            if any(v is None for v in [center_x, center_y, angle]):
                raise ValueError("無法獲取掃描參數")

            if self.debug_mode:
                print(f"\nStarting auto move Local CITS sequence:")
                print(f"Initial center: ({center_x}, {center_y})")
                print(f"Number of local areas: {len(local_areas_params)}")
                print(f"Scan angle: {angle}°")
                print(f"Repeat count: {repeat_count}")

            # 獲取移動序列的座標列表
            positions = self.auto_move(
                movement_script=movement_script,
                distance=distance,
                center_x=center_x,
                center_y=center_y,
                angle=angle,
                debug_mode=self.debug_mode
            )

            # 追蹤當前掃描方向
            current_direction = initial_direction

            # 在每個位置執行 Local CITS
            for i, (center_x, center_y) in enumerate(positions):
                self.check_if_stopped()
                # 除了初始位置外，需要先移動中心點
                if i > 0:
                    if self.debug_mode:
                        print(
                            f"\nMoving to center {i}/{len(positions)-1}: ({center_x}, {center_y})")

                    # 移動到新的中心位置
                    if not self.set_position(center_x, center_y):
                        print(
                            f"Warning: Failed to move to center ({center_x}, {center_y})")
                        continue

                    # 等待系統穩定
                    time.sleep(wait_time)

                position_type = "initial position" if i == 0 else f"position {i}"

                # 在當前位置重複執行 Local CITS
                for repeat in range(repeat_count):
                    self.check_if_stopped()
                    if self.debug_mode:
                        print(f"\nStarting Local CITS sequence at {position_type}, "
                              f"repeat {repeat + 1}/{repeat_count}, "
                              f"direction: {'up' if current_direction == 1 else 'down'}")

                    # 為當前位置創建所有小區
                    local_areas = []
                    for area_params in local_areas_params:
                        # 計算這個小區的實際起始點
                        start_x = center_x + area_params['x_dev']
                        start_y = center_y + area_params['y_dev']

                        local_areas.append(LocalCITSParams(
                            start_x=start_x,
                            start_y=start_y,
                            dx=area_params['dx'],
                            dy=area_params['dy'],
                            nx=area_params['nx'],
                            ny=area_params['ny'],
                            scan_direction=current_direction,
                            startpoint_direction=area_params['startpoint_direction']
                        ))

                    # 執行所有小區的 Local CITS 量測
                    if not self.standard_local_cits(
                        local_areas=local_areas,
                        scan_direction=current_direction
                    ):
                        print(f"Warning: Local CITS failed at {position_type}, "
                              f"repeat {repeat + 1}")
                        continue

                    # 等待CITS完成
                    while self.is_scanning():
                        time.sleep(1)

                    # 反轉掃描方向
                    current_direction *= -1

                    # 如果不是最後一次重複，則等待系統穩定
                    if repeat < repeat_count - 1:
                        time.sleep(wait_time)

            if self.debug_mode:
                print("\nAuto move Local CITS sequence completed successfully")
            return True

        except Exception as e:
            if self.debug_mode:
                print(f"Auto move Local CITS error: {str(e)}")
            return False
