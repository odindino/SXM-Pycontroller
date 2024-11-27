from typing import List, Dict, Optional
import time
import json
from pathlib import Path
from modules.SXMPyCITS import SXMCITSControl
from utils.logger import track_function
from utils.KB2902BSMU import KeysightB2902B, Channel, OutputMode

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

    # def initialize_sts_controller(self, smu_controller):
    #     """初始化STS控制器"""
    #     from modules.SXMSTSController import STSController
    #     self.sts_controller = STSController(self, smu_controller)

    # ========== STSxSMU functions ========== #
    # def perform_multi_sts(self, script: STSScript) -> bool:
    #     """
    #     執行多組STS量測
        
    #     Parameters
    #     ----------
    #     script : STSScript
    #         要執行的STS腳本
            
    #     Returns
    #     -------
    #     bool
    #         量測是否成功完成
    #     """
    #     try:
    #         # 驗證輸入
    #         if len(script.vds_list) != len(script.vg_list):
    #             raise ValueError("Vds和Vg列表長度必須相同")
            
    #         # 記錄初始狀態
    #         original_states = {
    #             'feedback': self.get_feedback_state(),
    #             'ch1_output': False,
    #             'ch1_voltage': 0.0,
    #             'ch2_output': False, 
    #             'ch2_voltage': 0.0
    #         }
            
    #         # 檢查並記錄SMU狀態
    #         for ch in [1, 2]:
    #             try:
    #                 # 讀取當前output狀態
    #                 response = self.smu.smu.query(f":OUTP{ch}?")
    #                 original_states[f'ch{ch}_output'] = bool(int(response))
                    
    #                 # 如果output on，讀取當前電壓
    #                 if original_states[f'ch{ch}_output']:
    #                     voltage = float(self.smu.smu.query(f":SOUR{ch}:VOLT?"))
    #                     original_states[f'ch{ch}_voltage'] = voltage
                        
    #             except Exception as e:
    #                 print(f"Warning: Failed to read channel {ch} state: {str(e)}")
            
    #         # 確保兩個通道都開啟
    #         for ch in [1, 2]:
    #             if not original_states[f'ch{ch}_output']:
    #                 self.smu.set_channel_output(ch, True)
    #                 time.sleep(0.5)  # 等待output穩定
            
    #         # 關閉回饋
    #         self.feedback_off()
    #         time.sleep(0.5)  # 等待系統穩定
            
    #         # 執行每組STS
    #         for vds, vg in zip(script.vds_list, script.vg_list):
    #             # 設定SMU電壓
    #             self.smu.set_channel_value(1, "VOLTAGE", vds)  # Vds
    #             self.smu.set_channel_value(2, "VOLTAGE", vg)   # Vg
                
    #             # 等待電壓穩定
    #             time.sleep(0.01)
                
    #             # 執行STS
    #             self.spectroscopy_start()
                
    #             # # 等待STS完成並儲存數據
    #             # time.sleep(2.0)  # 此時間需要根據實際STS參數調整
            
    #         return True
            
    #     except Exception as e:
    #         print(f"Multi-STS measurement error: {str(e)}")
    #         return False
            
    #     finally:
    #         try:
    #             # 恢復原始電壓
    #             for ch in [1, 2]:
    #                 if original_states[f'ch{ch}_output']:
    #                     # 如果原本就是開啟的,恢復原始電壓
    #                     self.smu.set_channel_value(
    #                         ch, 
    #                         "VOLTAGE",
    #                         original_states[f'ch{ch}_voltage']
    #                     )
    #                 else:
    #                     # 如果原本是關閉的,關閉output
    #                     self.smu.set_channel_output(ch, False)
                
    #             # 恢復回饋狀態
    #             if original_states['feedback']:
    #                 self.feedback_on()
                
    #         except Exception as e:
    #             print(f"Error restoring original states: {str(e)}")
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
                    print(f"Warning: Failed to read channel {ch} state: {str(e)}")
            
            # 確保兩個通道都開啟
            for ch in [1, 2]:
                if not original_states[f'ch{ch}_output']:
                    self.smu.enable_output(Channel(ch))
                    time.sleep(0.5)  # 等待output穩定
            
            # 關閉回饋
            
            self.set_zoffset(0.0)
            self.feedback_off()
            time.sleep(0.5)  # 等待系統穩定
            
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
                time.sleep(0.01)
                
                # 執行STS
                self.spectroscopy_start()
                
                # 等待STS完成
                time.sleep(2.0)  # 根據實際STS參數調整等待時間
            
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

                
            except Exception as e:
                print(f"Error restoring original states: {str(e)}")
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
