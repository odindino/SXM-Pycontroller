from typing import List, Dict, Optional
import time
import json
from pathlib import Path
from modules.SXMPyCITS import SXMCITSControl
from utils.logger import track_function
from utils.KB2902BSMU import KeysightB2902B, Channel, OutputMode
from utils.SXMPyCalc import CITSCalculator, LocalCITSCalculator, LocalCITSParams


class STSScript:
    """STS量測腳本資料結構"""

    def __init__(self, name: str, vds_list: List[float], vg_list: List[float]):
        self.name = name
        self.vds_list = vds_list
        self.vg_list = vg_list
        self.created_time = time.strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> dict:
        """轉換為字典格式以便儲存"""
        return {
            "name": self.name,
            "vds_list": self.vds_list,
            "vg_list": self.vg_list,
            "created_time": self.created_time
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'STSScript':
        """從字典格式建立物件"""
        script = cls(
            name=data["name"],
            vds_list=data["vds_list"],
            vg_list=data["vg_list"]
        )
        script.created_time = data.get("created_time", "Unknown")
        return script


class SXMController(SXMCITSControl):
    """
    STM控制器主類別
    整合所有功能模組並提供統一的操作介面
    """

    def __init__(self, debug_mode=False):
        super().__init__(debug_mode)
        self.base_dir = Path(__file__).parent.parent  # 取得主程式目錄
        self.scripts_dir = self.base_dir / "SXMPycontroller_scripts" / "sts_scripts"
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        self.loaded_scripts: Dict[str, STSScript] = {}
        self._load_scripts()

    def initialize_smu_controller(self, smu_instance):
        """初始化SMU控制器"""
        self.smu = smu_instance
        print("SMU controller initialized")

    # ========== STSxSMU functions ========== #
    @track_function
    def perform_multi_sts(self, script: STSScript) -> bool:
        """
        執行多組STS量測

        改良的工作流程:
        1. 先設定第一組SMU偏壓並執行STS，確認探針位置並獲得第一組數據
        2. 關閉回饋後執行剩餘的SMU偏壓組合
        3. 最後恢復系統狀態

        Parameters
        ----------
        script : STSScript
            要執行的STS腳本，包含多組Vds和Vg組合

        Returns
        -------
        bool
            量測是否成功完成
        """
        try:
            self.clear_stop_flag()
            # 驗證輸入
            if len(script.vds_list) != len(script.vg_list):
                raise ValueError("Vds和Vg列表長度必須相同")
            if not script.vds_list:
                raise ValueError("腳本必須至少包含一組偏壓設定")
                
            # 記錄初始狀態
            original_states = {
                'feedback': self.get_feedback_state(),
                'ch1_output': False,
                'ch1_voltage': 0.0,
                'ch2_output': False,
                'ch2_voltage': 0.0
            }

            # 檢查並記錄SMU狀態
            for ch in [1, 2]:
                try:
                    response = self.smu.smu.query(f":OUTP{ch}?")
                    original_states[f'ch{ch}_output'] = bool(int(response))
                    
                    if original_states[f'ch{ch}_output']:
                        voltage = float(self.smu.smu.query(f":SOUR{ch}:VOLT?"))
                        original_states[f'ch{ch}_voltage'] = voltage
                        
                except Exception as e:
                    print(f"Warning: Failed to read channel {ch} state: {str(e)}")

            # 確保兩個通道都開啟
            for ch in [1, 2]:
                if not original_states[f'ch{ch}_output']:
                    self.smu.enable_output(Channel(ch))
                    time.sleep(0.001)  # 等待output穩定

            # 設定第一組SMU偏壓
            first_vds = script.vds_list[0]
            first_vg = script.vg_list[0]
            
            self.smu.configure_source(
                channel=Channel(1),
                mode=OutputMode.VOLTAGE,
                level=first_vds,
                compliance=0.1
            )
            
            self.smu.configure_source(
                channel=Channel(2),
                mode=OutputMode.VOLTAGE,
                level=first_vg,
                compliance=0.1
            )
            
            time.sleep(0.001)  # 等待電壓穩定
            
            # 執行第一次STS (此時feedback仍開啟)
            if not self.spectroscopy_start():
                raise RuntimeError("First STS measurement failed")
            
            # 關閉回饋並設定Z偏移
            self.set_zoffset(0.0)
            self.feedback_off()
            
            # 執行剩餘的STS量測
            for vds, vg in zip(script.vds_list[1:], script.vg_list[1:]):
                self.check_if_stopped()
                self.smu.configure_source(
                    channel=Channel(1),
                    mode=OutputMode.VOLTAGE,
                    level=vds,
                    compliance=0.1
                )
                
                self.smu.configure_source(
                    channel=Channel(2),
                    mode=OutputMode.VOLTAGE,
                    level=vg,
                    compliance=0.1
                )
                
                time.sleep(0.001)
                
                if not self.spectroscopy_start():
                    print(f"Warning: STS failed at Vds={vds}V, Vg={vg}V")
                    continue

            return True

        except Exception as e:
            print(f"Multi-STS measurement error: {str(e)}")
            return False

        finally:
            try:
                # 恢復原始電壓
                for ch in [1, 2]:
                    if original_states[f'ch{ch}_output']:
                        # 如果原本就是開啟的，恢復原始電壓
                        self.smu.configure_source(
                            channel=Channel(ch),
                            mode=OutputMode.VOLTAGE,
                            level=original_states[f'ch{ch}_voltage'],
                            compliance=0.1
                        )
                    else:
                        # 如果原本是關閉的，關閉output
                        self.smu.disable_output(Channel(ch))

                # 恢復回饋狀態
                if original_states['feedback'] != self.FbOn:
                    self.feedback_on()
                    self.set_zoffset(10)
                    print(f"Feedback recover to {self.FbOn}")

            except Exception as e:
                print(f"Error restoring original states: {str(e)}")

    @track_function
    def standard_msts_cits(self, num_points_x: int, num_points_y: int,
                           script_name: str = None, scan_direction: int = 1) -> bool:
        """
        執行 Multi-STS CITS 量測，在每個 CITS 點位執行多組不同偏壓的 STS 量測

        此函數將 CITS 和 Multi-STS 整合在一起，在每個 CITS 點位上執行一系列
        不同偏壓組合的 STS 量測。整個過程會自動管理掃描、定位和回饋控制。

        Parameters
        ----------
        num_points_x : int
            X方向量測點數（1-512）
        num_points_y : int
            Y方向量測點數（1-512）
        script_name : str
            Multi-STS 腳本名稱，定義了要執行的 Vds 和 Vg 組合
        scan_direction : int, optional
            掃描方向：1 表示由下到上，-1 表示由上到下

        Returns
        -------
        bool
            量測是否成功完成

        Notes
        -----
        執行流程：
        1. 驗證參數和獲取 Multi-STS 腳本
        2. 計算 CITS 掃描座標和線數分配
        3. 對每個 CITS 點位：
        - 移動到指定位置
        - 執行 Multi-STS 量測（包含多組偏壓設定）
        4. 在適當位置執行掃描線
        5. 確保系統回到安全狀態
        """
        try:
            self.clear_stop_flag()
            # 驗證和獲取 Multi-STS 腳本
            if not script_name:
                raise ValueError("必須提供 Multi-STS 腳本名稱")

            script = self.get_script(script_name)
            if not script:
                raise ValueError(f"找不到腳本: {script_name}")

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

            # 計算 CITS 座標點位
            coordinates, _, _, scanlines = CITSCalculator.calculate_cits_coordinates(
                center_x, center_y, scan_range, scan_angle,
                num_points_x, num_points_y, total_lines, scan_direction, aspect_ratio
            )

            if self.debug_mode:
                print(f"\n開始 Multi-STS CITS 量測:")
                print(f"點數: {num_points_x}x{num_points_y}")
                print(f"掃描範圍: {scan_range} nm")
                print(f"掃描線分配: {scanlines}")
                print(f"總掃描線數: {sum(scanlines)}")

            # 執行主要量測循環
            for i, (sts_line, scan_count) in enumerate(zip(coordinates, scanlines[:-1])):
                self.check_if_stopped()
                # 執行掃描線（如果需要）
                if scan_count > 0:
                    if self.debug_mode:
                        print(f"\n=== 掃描第 {i+1} 段 {scan_count} 條線 ===")

                    if not self.scan_lines_for_sts(scan_count):
                        print(f"警告: 掃描第 {i+1} 段失敗")
                        continue

                # 執行該行的 Multi-STS 量測
                if self.debug_mode:
                    print(f"\n>>> 執行第 {i+1}/{num_points_y} 條 Multi-STS 線")

                for j, point in enumerate(sts_line):
                    self.check_if_stopped()
                    try:
                        if self.debug_mode:
                            print(f"  Multi-STS點 ({j+1}/{len(sts_line)}): "
                                  f"({point[0]:.3f}, {point[1]:.3f})")

                        # 移動到量測點位並執行 Multi-STS
                        self.move_tip_for_spectro(point[0], point[1])

                        # 執行該點的 Multi-STS 量測
                        if not self.perform_multi_sts(script):
                            print(f"警告: 位置 ({point[0]}, {point[1]}) "
                                  f"的 Multi-STS 量測失敗")

                    except Exception as e:
                        print(
                            f"Multi-STS點量測失敗 ({point[0]}, {point[1]}): {str(e)}")
                        continue

            # 執行最後一段掃描（如果有的話）
            if scanlines[-1] > 0:
                if self.debug_mode:
                    print(f"\n=== 執行最後 {scanlines[-1]} 條掃描線 ===")
                if not self.scan_lines_for_sts(scanlines[-1]):
                    print("警告: 最後一段掃描失敗")

            if self.debug_mode:
                print("\nMulti-STS CITS 量測完成")
            return True

        except Exception as e:
            print(f"\nMulti-STS CITS 量測錯誤: {str(e)}")
            return False

        finally:
            # 確保系統回到安全狀態
            try:
                self.feedback_on()
                if self.debug_mode:
                    print("系統回到安全狀態")
            except Exception as e:
                print(f"回復安全狀態時發生錯誤: {str(e)}")

    @track_function
    def standard_local_msts_cits(self, local_areas: List[LocalCITSParams],
                                 script_name: str = None,
                                 scan_direction: int = 1) -> bool:
        """
        執行局部區域 Multi-STS CITS 量測

        此函數整合了局部區域掃描、Multi-STS 以及 CITS 功能。在特定的局部區域內執行 CITS 量測，
        並在每個量測點上進行多組不同偏壓的 STS 量測。

        Parameters
        ----------
        local_areas : List[LocalCITSParams]
            要執行 CITS 的局部區域參數列表
        script_name : str
            Multi-STS 腳本名稱，定義了要執行的 Vds 和 Vg 組合
        scan_direction : int
            掃描方向，1 表示由下到上，-1 表示由上到下

        Returns
        -------
        bool
            量測是否成功完成
        """
        try:
            self.clear_stop_flag()
            # 驗證和獲取 Multi-STS 腳本
            if not script_name:
                raise ValueError("必須提供 Multi-STS 腳本名稱")

            script = self.get_script(script_name)
            if not script:
                raise ValueError(f"找不到腳本: {script_name}")

            # 獲取掃描參數
            center_x = self.GetScanPara('X')
            center_y = self.GetScanPara('Y')
            # scan_range = self.GetScanPara('Range')
            (_, scan_range) = self.calculate_actual_scan_dimensions()
            scan_angle = self.GetScanPara('Angle')
            # total_lines = self.GetScanPara('Pixel')
            (total_lines, line_spacing) = self.calculate_scan_lines()

            if any(v is None for v in [center_x, center_y, scan_range, scan_angle, total_lines]):
                raise ValueError("無法獲取掃描參數")

            # 計算局部區域的座標點
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
                print(f"\n開始局部 Multi-STS CITS 量測:")
                print(f"腳本名稱: {script_name}")
                print(f"局部區域數: {len(local_areas)}")
                print(f"掃描線分配: {scanline_distribution}")
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
                        print(f"警告: 掃描第 {i+1} 段失敗")
                        continue

                # 執行該群組的 Multi-STS 量測
                if self.debug_mode:
                    print(
                        f"\n>>> 執行第 {i+1}/{len(coordinate_distribution)} 群組的 Multi-STS 量測")

                for j, (x, y) in enumerate(coords_group):
                    self.check_if_stopped()
                    try:
                        if self.debug_mode:
                            print(f"  Multi-STS點 ({j+1}/{len(coords_group)}): "
                                  f"({x:.3f}, {y:.3f})")

                        # 移動到量測點位
                        if not self.move_tip_for_spectro(x, y):
                            print(f"警告: 移動到位置 ({x}, {y}) 失敗")
                            continue

                        # 執行 Multi-STS 量測
                        if not self.perform_multi_sts(script):
                            print(f"警告: 位置 ({x}, {y}) 的 Multi-STS 量測失敗")
                            continue

                    except Exception as e:
                        print(f"Multi-STS點量測失敗 ({x}, {y}): {str(e)}")
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
                print("\n局部 Multi-STS CITS 量測完成")
            return True

        except Exception as e:
            if self.debug_mode:
                print(f"\n局部 Multi-STS CITS 量測錯誤: {str(e)}")
            return False

        finally:
            # 確保系統回到安全狀態
            try:
                self.feedback_on()
                if self.debug_mode:
                    print("系統回到安全狀態")
            except Exception as e:
                print(f"回復安全狀態時發生錯誤: {str(e)}")

    @track_function
    def auto_move_msts_CITS(self, movement_script: str, distance: float,
                            num_points_x: int, num_points_y: int,
                            script_name: str,
                            initial_direction: int = 1,
                            wait_time: float = 1.0,
                            repeat_count: int = 1) -> bool:
        """
        執行自動移動和 Multi-STS CITS 量測序列
        在每個移動位置進行多組偏壓的 CITS 量測

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
        script_name : str
            Multi-STS 腳本名稱，定義了要執行的 Vds 和 Vg 組合
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

            # 驗證 Multi-STS 腳本
            script = self.get_script(script_name)
            if not script:
                raise ValueError(f"找不到腳本: {script_name}")

            # 獲取當前掃描參數
            center_x = self.GetScanPara('X')
            center_y = self.GetScanPara('Y')
            angle = self.GetScanPara('Angle')

            if any(v is None for v in [center_x, center_y, angle]):
                raise ValueError("無法獲取掃描參數")

            if self.debug_mode:
                print(f"\nStarting auto move Multi-STS CITS sequence:")
                print(f"Initial position: ({center_x}, {center_y})")
                print(f"Scan angle: {angle}°")
                print(f"CITS points: {num_points_x}x{num_points_y}")
                print(f"Script name: {script_name}")
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
                            print(f"Starting Multi-STS CITS at {position_type}, "
                                  f"repeat {repeat + 1}/{repeat_count}, "
                                  f"direction: {'up' if current_direction == 1 else 'down'}")

                        # 執行 Multi-STS CITS 量測
                        if not self.standard_msts_cits(
                            num_points_x=num_points_x,
                            num_points_y=num_points_y,
                            script_name=script_name,
                            scan_direction=current_direction
                        ):
                            print(f"Warning: Multi-STS CITS failed at {position_type}, "
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
                    print(f"Multi-STS CITS sequence error: {str(e)}")
                return False

            if self.debug_mode:
                print("\nAuto move Multi-STS CITS sequence completed successfully")
            return True

        except Exception as e:
            if self.debug_mode:
                print(f"Auto move Multi-STS CITS error: {str(e)}")
            return False

    @track_function
    def auto_move_local_msts_CITS(self, movement_script: str, distance: float,
                                  local_areas_params: List[dict], script_name: str,
                                  initial_direction: int = 1,
                                  wait_time: float = 1.0,
                                  repeat_count: int = 1) -> bool:
        """
        執行自動移動和 Local Multi-STS CITS 量測序列
        在每個移動位置的多個相對偏移區域進行多組偏壓的 CITS 量測

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
        script_name : str
            Multi-STS 腳本名稱，定義了要執行的 Vds 和 Vg 組合
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

            # 驗證 Multi-STS 腳本
            script = self.get_script(script_name)
            if not script:
                raise ValueError(f"找不到腳本: {script_name}")

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
                print(f"\nStarting auto move Local Multi-STS CITS sequence:")
                print(f"Initial center: ({center_x}, {center_y})")
                print(f"Number of local areas: {len(local_areas_params)}")
                print(f"Script name: {script_name}")
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

            # 在每個位置執行 Local Multi-STS CITS
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

                # 在當前位置重複執行 Local Multi-STS CITS
                for repeat in range(repeat_count):
                    self.check_if_stopped()
                    if self.debug_mode:
                        print(f"\nStarting Local Multi-STS CITS sequence at {position_type}, "
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

                    # 執行所有小區的 Local Multi-STS CITS 量測
                    if not self.standard_local_msts_cits(
                        local_areas=local_areas,
                        script_name=script_name,
                        scan_direction=current_direction
                    ):
                        print(f"Warning: Local Multi-STS CITS failed at {position_type}, "
                              f"repeat {repeat + 1}")
                        continue

                    # 等待CITS完成
                    while self.is_scanning():
                        time.sleep(0.1)

                    # 反轉掃描方向
                    current_direction *= -1

                    # 如果不是最後一次重複，則等待系統穩定
                    if repeat < repeat_count - 1:
                        time.sleep(wait_time)

            if self.debug_mode:
                print("\nAuto move Local Multi-STS CITS sequence completed successfully")
            return True

        except Exception as e:
            if self.debug_mode:
                print(f"Auto move Local Multi-STS CITS error: {str(e)}")
            return False

    # ========== STSxSMU functions END ========== #

    # ========== STSxSMU script functions ========== #
    # def save_script(self, script: STSScript) -> bool:
    #     """儲存STS腳本到獨立檔案"""
    #     try:
    #         # 取得腳本存放路徑
    #         sts_dir = Path(__file__).parent.parent / "SXMPycontroller_scripts" / "sts_scripts"
    #         sts_dir.mkdir(parents=True, exist_ok=True)

    #         script_file = sts_dir / f"{script.name}.json"
    #         with open(script_file, 'w', encoding='utf-8') as f:
    #             json.dump(script.to_dict(), f, indent=2, ensure_ascii=False)

    #         return True
    #     except Exception as e:
    #         print(f"Save script error: {str(e)}")
    #         return False

    def get_script(self, name: str) -> Optional[STSScript]:
        """從獨立檔案讀取指定腳本"""
        try:
            script_file = Path(__file__).parent.parent / "SXMPycontroller_scripts" / "sts_scripts" / f"{name}.json"
            if not script_file.exists():
                return None

            with open(script_file, encoding='utf-8') as f:
                data = json.load(f)
                return STSScript.from_dict(data)

        except Exception as e:
            print(f"Get script error: {str(e)}")
            return None

    def get_all_scripts(self) -> Dict[str, STSScript]:
        """讀取所有STS腳本"""
        try:
            scripts_dir = Path(__file__).parent.parent / "SXMPycontroller_scripts" / "sts_scripts"
            if not scripts_dir.exists():
                return {}

            scripts = {}
            for script_file in scripts_dir.glob("*.json"):
                with open(script_file, encoding='utf-8') as f:
                    data = json.load(f)
                    scripts[data['name']] = STSScript.from_dict(data)

            return scripts

        except Exception as e:
            print(f"Get all scripts error: {str(e)}")
            return {}

    def _load_scripts(self):
        """從檔案夾載入所有STS腳本"""
        try:
            if not self.scripts_dir.exists():
                return

            self.loaded_scripts = {}
            for script_file in self.scripts_dir.glob("*.json"):
                with open(script_file, encoding='utf-8') as f:
                    data = json.load(f)
                    self.loaded_scripts[data['name']] = STSScript.from_dict(data)

        except Exception as e:
            print(f"Load scripts error: {str(e)}")
            self.loaded_scripts = {}

    # ========== STSxSMU script functions END ========== #

    @track_function
    def initialize_system(self):
        try:
            self.feedback_on()
            self.SetScanPara('Speed', 2.0)
            self.SetScanPara('Range', 100.0)
            x, y = self.get_position()
            print(f"System initialized at position ({x}, {y})")
            return True
        except Exception as e:
            print(f"Initialization Error: {str(e)}")
            return False

    @track_function
    def safe_shutdown(self):
        try:
            self.scan_off()
            self.feedback_on()
            self.stop_monitoring()
            print("System safely shut down")
        except Exception as e:
            print(f"Shutdown Error: {str(e)}")

    @track_function
    def auto_move_scan_area(self, movement_script: str, distance: float,
                            wait_time: float, repeat_count: int = 1) -> bool:
        try:
            print(
                f"Starting auto move scan:\n"
                f"Movement script: {movement_script}\n"
                f"Distance: {distance} nm\n"
                f"Wait time: {wait_time} s\n"
                f"Repeat count: {repeat_count}"
            )
            return super().auto_move_scan_area(
                movement_script, distance, wait_time, repeat_count
            )
        except Exception as e:
            print(f"Auto move scan error: {str(e)}")
            return False
