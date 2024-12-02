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
        # self.sts_controller = None  # 將在連接SMU後初始
        self.scripts_path = Path.home() / ".stm_controller" / "sts_scripts.json"
        self.scripts_path.parent.mkdir(exist_ok=True)
        self.loaded_scripts: Dict[str, STSScript] = {}
        self._load_scripts()

    def initialize_smu_controller(self, smu_instance):
        """初始化SMU控制器"""
        self.smu = smu_instance

    # ========== STSxSMU functions ========== #
    def perform_multi_sts(self, script: STSScript) -> bool:
        """
        執行多組STS量測

        Parameters
        ----------
        script : STSScript
            要執行的STS腳本

        Returns
        -------
        bool
            量測是否成功完成
        """
        try:
            # 驗證輸入
            if len(script.vds_list) != len(script.vg_list):
                raise ValueError("Vds和Vg列表長度必須相同")

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
                    # 讀取當前output狀態
                    response = self.smu.smu.query(f":OUTP{ch}?")
                    original_states[f'ch{ch}_output'] = bool(int(response))

                    # 如果output on，讀取當前電壓
                    if original_states[f'ch{ch}_output']:
                        voltage = float(self.smu.smu.query(f":SOUR{ch}:VOLT?"))
                        original_states[f'ch{ch}_voltage'] = voltage

                except Exception as e:
                    print(
                        f"Warning: Failed to read channel {ch} state: {str(e)}")

            # 確保兩個通道都開啟
            for ch in [1, 2]:
                if not original_states[f'ch{ch}_output']:
                    self.smu.enable_output(Channel(ch))
                    time.sleep(0.001)  # 等待output穩定

             # 執行一次基本STS以確認探針位置
            self.spectroscopy_start()
            # time.sleep(0.5)  # 等待系統穩定

            # 關閉回饋
            self.set_zoffset(0.0)
            self.feedback_off()
            # time.sleep(0.5)  # 等待系統穩定

            # 執行每組STS
            for vds, vg in zip(script.vds_list, script.vg_list):
                # 設定SMU電壓
                self.smu.configure_source(
                    channel=Channel(1),
                    mode=OutputMode.VOLTAGE,
                    level=vds,
                    compliance=0.1  # 設定適當的compliance值
                )

                self.smu.configure_source(
                    channel=Channel(2),
                    mode=OutputMode.VOLTAGE,
                    level=vg,
                    compliance=0.1  # 設定適當的compliance值
                )

                # 等待電壓穩定
                time.sleep(0.001)

                # 執行STS
                self.spectroscopy_start()

                # 等待STS完成
                # time.sleep(2.0)  # 根據實際STS參數調整等待時間

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

    # ========== STSxSMU functions END ========== #

    # ========== STSxSMU script functions ========== #
    def save_script(self, script: STSScript) -> bool:
        """儲存STS腳本"""
        try:
            self.loaded_scripts[script.name] = script
            self._save_scripts()
            return True
        except Exception as e:
            print(f"Save script error: {str(e)}")
            return False

    def get_script(self, name: str) -> Optional[STSScript]:
        """取得指定腳本"""
        return self.loaded_scripts.get(name)

    def get_all_scripts(self) -> Dict[str, STSScript]:
        """取得所有腳本"""
        return self.loaded_scripts

    def _load_scripts(self):
        """從檔案載入腳本"""
        try:
            if self.scripts_path.exists():
                with open(self.scripts_path) as f:
                    data = json.load(f)
                    self.loaded_scripts = {
                        name: STSScript.from_dict(script_data)
                        for name, script_data in data.items()
                    }
        except Exception as e:
            print(f"Load scripts error: {str(e)}")
            self.loaded_scripts = {}

    def _save_scripts(self):
        """儲存腳本到檔案"""
        try:
            data = {
                name: script.to_dict()
                for name, script in self.loaded_scripts.items()
            }
            with open(self.scripts_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Save scripts error: {str(e)}")
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
