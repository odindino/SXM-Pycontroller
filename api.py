"""
Backend API Implementation
Handles communication between WebView GUI and instrument control.

Author: Zi-Liang Yang
Version: 1.0.0
Date: 2024-11-25
"""

import threading
import time
import webview
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json

from utils.KB2902BSMU import KeysightB2902B, Channel, OutputMode
from utils.SXMPyCalc import LocalCITSParams
from modules.SXMPycontroller import SXMController


@dataclass
class ChannelReading:
    """通道讀數數據結構"""
    voltage: float
    current: float
    timestamp: float


class SMUControlAPI:
    """WebView API 實作"""

    def __init__(self):
        """初始化API"""

        self.smu = None
        self.stm = None
        self._stop_flag = threading.Event()  # 新增停止標記
        self._lock = threading.Lock()
        self._reading_active = {1: False, 2: False}
        self._reading_threads: Dict[int, threading.Thread] = {}
        self._compliance = {1: 0.01, 2: 0.01}  # 預設compliance值（分通道）
        # 註冊清理處理器
        self._cleanup_handler = None
        self._cleanup_event = threading.Event()


        # 腳本相關設定
        # 取得主程式所在的目錄
        self.base_dir = Path(__file__).parent
        
        # 設定腳本存放目錄
        self.scripts_dir = self.base_dir / "SXMPycontroller_scripts"
        self.sts_scripts_dir = self.scripts_dir / "sts_scripts"
        self.move_scripts_dir = self.scripts_dir / "move_scripts"
        
        # 確保目錄存在
        self.scripts_dir.mkdir(exist_ok=True)
        self.sts_scripts_dir.mkdir(exist_ok=True)
        self.move_scripts_dir.mkdir(exist_ok=True)
        
    def stop_measurement(self) -> bool:
        """中止當前測量"""
        try:
            if self.stm:
                self.stm.stop_operation()  # 呼叫stop_operation
                if self.stm.debug_mode:
                    print("Measurement stopped")
                    
                return True
            return False
        except Exception as e:
            print(f"停止測量錯誤: {str(e)}")
            return False
    

    # ========== SMU General functions ========== #
    def connect_smu(self, address: str) -> bool:
        """
        連接SMU

        Args:
            address: VISA address string
        """
        try:
            self.smu = KeysightB2902B()
            success = self.smu.connect(address)
            if success:
                # 連接時設定初始compliance
                # self.stm.initialize_sts_controller(self)
                self.smu.smu.write(":SYST:BEEP:STAT ON")
                self.set_compliance(1, self._compliance[1])
                self.set_compliance(2, self._compliance[2])
                self.beep()
            return success
        except Exception as e:
            raise Exception(f"連接失敗: {str(e)}")

    def beep(self, frequency=1000, duration=0.1):
        """發出蜂鳴聲"""
        try:
            if self.smu and self.smu.smu:
                self.smu.smu.write(f":SYST:BEEP {frequency},{duration}")
        except Exception:
            pass  # 蜂鳴器失敗不影響主要功能

    def disconnect_smu(self) -> bool:
        """中斷SMU連接"""
        try:
            with self._lock:
                if self.smu:
                    # 停止所有讀值
                    for channel in [1, 2]:
                        self.stop_reading(channel)

                    # 關閉輸出
                    for channel in Channel:
                        self.smu.disable_output(channel)

                    # 中斷連接
                    self.smu.disconnect()
                    self.smu = None
                return True

        except Exception as e:
            raise Exception(f"中斷連接失敗: {str(e)}")
    # ========== SMU General functions END ========== #

    # ========== SMU Channel functions ========== #

    def set_channel_value(self, channel: int, mode: str, value: float) -> bool:
        """
        設定通道輸出值

        Args:
            channel: 通道號(1或2)
            mode: 'VOLTAGE'或'CURRENT'
            value: 輸出值
        """
        try:
            if not self.smu:
                raise Exception("SMU未連接")

            channel_enum = Channel.CH1 if channel == 1 else Channel.CH2
            output_mode = OutputMode.VOLTAGE if mode == 'VOLTAGE' else OutputMode.CURRENT

            success = self.smu.configure_source(
                channel=channel_enum,
                mode=output_mode,
                level=value,
                compliance=self._compliance[channel]
            )

            if success:
                self.beep()
            return success

        except Exception as e:
            raise Exception(f"設定通道{channel}失敗: {str(e)}")

    def set_channel_output(self, channel: int, state: bool) -> bool:
        """
        設定通道輸出開關

        Args:
            channel: 通道號(1或2)
            state: True開啟, False關閉
        """
        try:
            if not self.smu:
                raise Exception("SMU未連接")

            channel_enum = Channel.CH1 if channel == 1 else Channel.CH2

            if state:
                success = self.smu.enable_output(channel_enum)
            else:
                success = self.smu.disable_output(channel_enum)

            if success:
                self.beep()
            return success

        except Exception as e:
            raise Exception(f"設定通道{channel}輸出狀態失敗: {str(e)}")

    def set_compliance(self, channel: int, value: float) -> bool:
        """設定指定通道的compliance值"""
        try:
            if not self.smu:
                raise Exception("SMU未連接")

            self._compliance[channel] = value
            self.smu.smu.write(f":SENS{channel}:CURR:PROT {value}")
            self.beep()
            return True

        except Exception as e:
            raise Exception(f"設定通道{channel} compliance失敗: {str(e)}")

    def get_compliance(self, channel: int) -> float:
        """讀取指定通道的compliance值"""
        try:
            if not self.smu:
                raise Exception("SMU未連接")

            value = float(self.smu.smu.query(f":SENS{channel}:CURR:PROT?"))
            return value

        except Exception as e:
            raise Exception(f"讀取通道{channel} compliance失敗: {str(e)}")

    def read_channel(self, channel: int) -> dict:
        """
        執行單次讀值

        Args:
            channel: 通道號(1或2)

        Returns:
            dict: 包含電壓和電流的讀值
        """
        try:
            if not self.smu:
                raise Exception("SMU未連接")

            with self._lock:
                # 清除錯誤佇列和狀態
                self.smu.smu.write("*CLS")
                self.smu.smu.write(":STAT:PRES")

                # 讀取前儲存原始輸出狀態
                original_output_state = bool(int(self.smu.smu.query(f":OUTP{channel}?")))

                # 配置測量設定
                self.smu.smu.write(f":SENS{channel}:CURR:NPLC 0.1")
                self.smu.smu.write(":FORM:ELEM:SENS VOLT,CURR")

                try:
                    # 執行測量
                    voltage = float(self.smu.smu.query(f":MEAS:VOLT? (@{channel})"))
                    time.sleep(0.05)  # 增加適當的延遲
                    current = float(self.smu.smu.query(f":MEAS:CURR? (@{channel})"))

                    # 確認是否有錯誤發生
                    error_check = self.smu.smu.query("SYST:ERR?")
                    if not error_check.startswith("+0"):
                        print(f"Warning: SMU reported error: {error_check}")

                    self.beep()  # 讀值成功時發出聲音

                    return {
                        'voltage': voltage,
                        'current': current
                    }

                finally:
                    # 確保輸出狀態不變
                    if not original_output_state:
                        self.smu.smu.write(f":OUTP{channel} OFF")

                    # 再次清除任何可能的錯誤狀態
                    self.smu.smu.write("*CLS")

        except Exception as e:
            raise Exception(f"讀取通道{channel}失敗: {str(e)}")

    def start_reading(self, channel: int) -> bool:
        """開始持續讀值"""
        try:
            with self._lock:
                if channel in self._reading_threads and self._reading_threads[channel].is_alive():
                    return False

                self._reading_active[channel] = True
                thread = threading.Thread(
                    target=self._reading_loop,
                    args=(channel,),
                    daemon=True
                )
                self._reading_threads[channel] = thread
                thread.start()
                return True

        except Exception as e:
            print(f"Failed to start reading channel {channel}: {str(e)}")
            return False

    def stop_reading(self, channel: int) -> bool:
        """停止持續讀值"""
        try:
            with self._lock:
                self._reading_active[channel] = False
                if channel in self._reading_threads:
                    self._reading_threads[channel].join(timeout=1.0)
                    del self._reading_threads[channel]
                return True

        except Exception as e:
            print(f"Failed to stop reading channel {channel}: {str(e)}")
            return False

    def _reading_loop(self, channel: int):
        """讀值循環"""
        retry_count = 0
        max_retries = 3

        while self._reading_active[channel] and not self._cleanup_event.is_set():
            try:
                with self._lock:  # 防止同時讀取造成衝突
                    if self.smu:
                        channel_enum = Channel.CH1 if channel == 1 else Channel.CH2

                        # 配置測量參數
                        self.smu.write(
                            f":SENS{channel}:CURR:NPLC 0.1")  # 快速測量模式
                        self.smu.write(f":FORM:ELEM:SENS VOLT,CURR")

                        # 分別讀取電壓和電流
                        voltage = float(self.smu.query(
                            f":MEAS:VOLT? (@{channel})"))
                        time.sleep(0.01)  # 短暫延遲
                        current = float(self.smu.query(
                            f":MEAS:CURR? (@{channel})"))

                        # 發送到前端
                        window = webview.windows[0]
                        window.evaluate_js(
                            f"updateChannelReading({channel}, {voltage}, {current})"
                        )

                        # 重置重試計數
                        retry_count = 0

            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(
                        f"Channel {channel} reading failed after {max_retries} retries")
                    self._reading_active[channel] = False
                    break

                time.sleep(0.5)  # 錯誤後等待時間

            # 讀值間隔
            time.sleep(0.1)

    # ========== SMU Channel functions END ========== #

    # ========== SXM functions ========== #
    # ========== SXM connection ========== #
    def ensure_controller(self) -> bool:
        """確保控制器存在且連接正常"""
        print("Ensuring STM controller...")
        try:
            # 如果控制器不存在，建立新的控制器
            if self.stm is None:
                print("Creating new STM controller...")
                self.stm = SXMController(debug_mode=True)
                print("STM controller created")
                self.stm.initialize_smu_controller(self.smu)

                # 使用簡單的變數賦值來測試連接
                self.stm.MySXM.SendWait("a := 0;")
                return True

            # 如果控制器存在，檢查DDE連接
            try:
                # 使用簡單的變數賦值來測試連接
                self.stm.MySXM.SendWait("a := 0;")
                return True
            except:
                print("Connection lost, recreating controller...")
                self.stm = None
                return self.ensure_controller()

        except Exception as e:
            print(f"Controller initialization error: {str(e)}")
            return False

    # ========== SXM functions END ========== #

    # ========== STS functions ==========
    def start_sts(self) -> bool:
        """
        開始STS測量

        Returns
        -------
        bool
            測量是否成功開始
        """
        try:
            print("\nPreparing for STS measurement...")

            # 確保控制器就緒
            if not self.ensure_controller():
                print("not ensure controller")
                raise Exception("Failed to initialize controller")

            print("Starting STS measurement...")
            success = self.stm.spectroscopy_start()

            if success:
                print("STS measurement started successfully")
            else:
                print("Failed to start STS measurement")

            return success

        except Exception as e:
            print(f"STS execution error: {str(e)}")
            return False

    def perform_multi_sts(self, script_name: str) -> bool:
        """
        執行多組STS量測

        Parameters
        ----------
        script_name : str
            要執行的腳本名稱

        Returns
        -------
        bool
            測量是否成功完成

        Raises
        ------
        Exception
            當執行過程中發生錯誤時
        """
        try:
            # 確保STM控制器已初始化
            if not self.ensure_controller():
                raise Exception("STM控制器未初始化")

            # 確保SMU已連接
            if not self.smu:
                raise Exception("SMU未連接")

            # 取得腳本
            script = self.stm.get_script(script_name)
            if not script:
                raise ValueError(f"找不到腳本: {script_name}")

            # 執行多重STS量測
            return self.stm.perform_multi_sts(script)

        except Exception as e:
            print(f"Multi-STS execution error: {str(e)}")
            raise Exception(f"執行Multi-STS失敗: {str(e)}")

    # ========== STS functions END ========== #

    def save_sts_script(self, name: str, vds_list: list[float], vg_list: list[float]) -> bool:
        """
        儲存 STS 腳本
        
        Parameters
        ----------
        name : str
            腳本名稱
        vds_list : list[float]
            Vds 電壓列表
        vg_list : list[float]
            Vg 電壓列表
        
        Returns
        -------
        bool
            儲存是否成功
        """
        try:
            sts_dir = self.sts_scripts_dir
            sts_dir.mkdir(parents=True, exist_ok=True)

            script_data = {
                'name': name,
                'vds_list': vds_list,
                'vg_list': vg_list,
                'created_time': time.strftime("%Y-%m-%d %H:%M:%S")
            }

            script_file = sts_dir / f"{name}.json"
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"儲存 STS 腳本失敗: {str(e)}")
            raise Exception(f"無法儲存腳本: {str(e)}")

    def get_sts_scripts(self) -> dict:
        """
        獲取所有 STS 腳本
        
        Returns
        -------
        dict
            腳本名稱和內容的映射
        """
        try:
            if not self.sts_scripts_dir.exists():
                return {}

            scripts = {}
            for script_file in self.sts_scripts_dir.glob("*.json"):
                with open(script_file, encoding='utf-8') as f:
                    script_data = json.load(f)
                    scripts[script_data['name']] = script_data

            return scripts

        except Exception as e:
            print(f"讀取 STS 腳本失敗: {str(e)}")
            return {}



    # ========== CITS functions ========== #
    def start_ssts_cits(self, points_x: int, points_y: int, use_multi_sts: bool = False, scan_direction: int = 1) -> bool:
        """
        啟動 CITS 量測

        Parameters
        ----------
        points_x : int
            X方向的測量點數
        points_y : int
            Y方向的測量點數
        use_multi_sts : bool
            是否使用 Multi-STS 模式
        scan_direction : int
            掃描方向 (1: 向上, -1: 向下)

        Returns
        -------
        bool
            是否成功啟動量測
        """
        try:
            # 確保 STM 控制器連接正常
            if not self.ensure_controller():
                print("Failed to ensure STM controller")
                raise Exception("Failed to initialize controller")

            # 參數驗證
            if not (1 <= points_x <= 512 and 1 <= points_y <= 512):
                raise ValueError("點數必須在 1 到 512 之間")

            if scan_direction not in (1, -1):
                raise ValueError("掃描方向必須是 1 (向上) 或 -1 (向下)")

            # 移除 use_multi_sts 參數
            success = self.stm.standard_cits(
                num_points_x=points_x,
                num_points_y=points_y,
                scan_direction=scan_direction
            )

            return success

        except Exception as e:
            raise Exception(f"CITS量測失敗: {str(e)}")

    def start_msts_cits(self, points_x: int, points_y: int, script_name: str, scan_direction: int = 1) -> bool:
        """
        啟動 Multi-STS CITS 量測

        在每個 CITS 點位上執行多組不同偏壓組合的 STS 量測，同時整合了掃描、定位和
        偏壓控制功能。

        Parameters
        ----------
        points_x : int
            X方向的測量點數（1-512）
        points_y : int
            Y方向的測量點數（1-512）
        script_name : str
            要執行的 Multi-STS 腳本名稱，定義了 Vds 和 Vg 的組合
        scan_direction : int, optional
            掃描方向：1 表示由下到上，-1 表示由上到下

        Returns
        -------
        bool
            量測是否成功開始

        Raises
        ------
        Exception
            當發生錯誤時拋出異常，包含詳細的錯誤訊息
        """
        try:
            # 確保 STM 控制器已初始化
            if not self.ensure_controller():
                raise Exception("STM 控制器未初始化")

            # 確保 SMU 已連接
            if not self.smu:
                raise Exception("SMU 未連接")

            # 參數驗證
            if not (1 <= points_x <= 512 and 1 <= points_y <= 512):
                raise ValueError("點數必須在 1 到 512 之間")

            if scan_direction not in (1, -1):
                raise ValueError("掃描方向必須是 1 (向上) 或 -1 (向下)")

            if not script_name:
                raise ValueError("必須提供 Multi-STS 腳本名稱")

            # 執行 Multi-STS CITS 量測
            success = self.stm.standard_msts_cits(
                num_points_x=points_x,
                num_points_y=points_y,
                script_name=script_name,
                scan_direction=scan_direction
            )

            if not success:
                raise Exception("Multi-STS CITS 量測失敗")

            return success

        except Exception as e:
            error_message = f"Multi-STS CITS 量測錯誤: {str(e)}"
            print(error_message)
            raise Exception(error_message)
    # ========== CITS functions END ========== #

    # ========== Local CITS functions ========== #
    def start_local_ssts_cits(self, local_areas_params: list, scan_direction: int = 1) -> bool:
        """
        啟動局部區域 CITS 量測

        對特定區域執行 CITS 量測，提供更精確的空間分布控制。此函數允許定義多個
        局部量測區域，每個區域可以有不同的點密度和分布方式。

        Parameters
        ----------
        local_areas_params : list
            局部區域參數列表，每個元素都是包含以下鍵值的字典：
            - start_x (float): 起始 X 座標（nm）
            - start_y (float): 起始 Y 座標（nm）
            - dx (float): X 方向步進（nm）
            - dy (float): Y 方向步進（nm）
            - nx (int): X 方向點數
            - ny (int): Y 方向點數
            - startpoint_direction (int): 起始點方向（1: 向上, -1: 向下）
        scan_direction : int, optional
            掃描方向（1: 由下到上, -1: 由上到下），預設為 1

        Returns
        -------
        bool
            量測是否成功啟動

        Raises
        ------
        Exception
            當參數無效或執行過程中發生錯誤時
        """
        try:
            # 確保 STM 控制器已初始化
            if not self.ensure_controller():
                print("Failed to ensure STM controller")
                raise Exception("Failed to initialize controller")

            # 參數驗證
            if not local_areas_params:
                raise ValueError("必須提供至少一個局部區域參數")

            if scan_direction not in (1, -1):
                raise ValueError("掃描方向必須是 1 (向上) 或 -1 (向下)")

            # 驗證每個局部區域的參數
            local_areas = []
            for params in local_areas_params:
                # 檢查必要參數
                required_params = ['start_x',
                                   'start_y', 'dx', 'dy', 'nx', 'ny']
                missing_params = [
                    p for p in required_params if p not in params]
                if missing_params:
                    raise ValueError(f"缺少必要參數: {', '.join(missing_params)}")

                # 驗證點數範圍
                if not (1 <= params['nx'] <= 512 and 1 <= params['ny'] <= 512):
                    raise ValueError(
                        f"點數必須在 1 到 512 之間，目前: nx={params['nx']}, ny={params['ny']}"
                    )

                # 建立 LocalCITSParams 物件
                local_area = LocalCITSParams(
                    start_x=params['start_x'],
                    start_y=params['start_y'],
                    dx=params['dx'],
                    dy=params['dy'],
                    nx=params['nx'],
                    ny=params['ny'],
                    startpoint_direction=params.get('startpoint_direction', 1)
                )
                local_areas.append(local_area)

            # 執行局部 CITS 量測
            success = self.stm.standard_local_cits(
                local_areas=local_areas,
                scan_direction=scan_direction
            )

            if success:
                print("Local CITS measurement started successfully")
            else:
                print("Failed to start local CITS measurement")

            return success

        except Exception as e:
            error_message = f"Local CITS measurement error: {str(e)}"
            print(error_message)
            raise Exception(error_message)

    def start_local_msts_cits(self, local_areas_params: list,
                              script_name: str, scan_direction: int = 1) -> bool:
        """
        啟動局部區域 Multi-STS CITS 量測

        此 API 函數整合了局部區域 CITS 和 Multi-STS 功能，允許在指定的局部區域內執行
        CITS 量測，並在每個量測點上進行多組不同偏壓的 STS 量測。

        Parameters
        ----------
        local_areas_params : list
            局部區域參數列表，每個元素都是包含以下鍵值的字典：
            - start_x (float): 起始 X 座標（nm）
            - start_y (float): 起始 Y 座標（nm）
            - dx (float): X 方向步進（nm）
            - dy (float): Y 方向步進（nm）
            - nx (int): X 方向點數
            - ny (int): Y 方向點數
            - startpoint_direction (int): 起始點方向（1: 向上, -1: 向下）
        script_name : str
            Multi-STS 腳本名稱，定義了要執行的 Vds 和 Vg 組合
        scan_direction : int, optional
            掃描方向（1: 由下到上, -1: 由上到下），預設為 1

        Returns
        -------
        bool
            量測是否成功啟動
        """
        try:
            # 確保控制器初始化
            if not self.ensure_controller():
                raise Exception("Failed to initialize controller")

            # 確保 SMU 已連接
            if not self.smu:
                raise Exception("SMU 未連接")

            # 參數驗證
            if not local_areas_params:
                raise ValueError("必須提供至少一個局部區域參數")

            if not script_name:
                raise ValueError("必須提供 Multi-STS 腳本名稱")

            if scan_direction not in (1, -1):
                raise ValueError("掃描方向必須是 1 (向上) 或 -1 (向下)")

            # 驗證每個局部區域的參數並轉換為 LocalCITSParams 物件
            local_areas = []
            for params in local_areas_params:
                # 檢查必要參數
                required_params = ['start_x',
                                   'start_y', 'dx', 'dy', 'nx', 'ny']
                missing_params = [
                    p for p in required_params if p not in params]
                if missing_params:
                    raise ValueError(f"缺少必要參數: {', '.join(missing_params)}")

                # 驗證點數範圍
                if not (1 <= params['nx'] <= 512 and 1 <= params['ny'] <= 512):
                    raise ValueError(
                        f"點數必須在 1 到 512 之間，目前: nx={params['nx']}, ny={params['ny']}"
                    )

                # 建立 LocalCITSParams 物件
                local_area = LocalCITSParams(
                    start_x=params['start_x'],
                    start_y=params['start_y'],
                    dx=params['dx'],
                    dy=params['dy'],
                    nx=params['nx'],
                    ny=params['ny'],
                    startpoint_direction=params.get('startpoint_direction', 1)
                )
                local_areas.append(local_area)

            # 執行局部 Multi-STS CITS 量測
            success = self.stm.standard_local_msts_cits(
                local_areas=local_areas,
                script_name=script_name,
                scan_direction=scan_direction
            )

            if success:
                print("Local Multi-STS CITS measurement started successfully")
            else:
                print("Failed to start local Multi-STS CITS measurement")

            return success

        except Exception as e:
            error_message = f"Local Multi-STS CITS measurement error: {str(e)}"
            print(error_message)
            raise Exception(error_message)

    # def get_sxm_status(self) -> dict:
    #     """獲取STM當前狀態"""
    #     try:
    #         if not self.ensure_controller():
    #             raise Exception("STM控制器未初始化")
    #         return self.stm.get_sxm_status()
    #     except Exception as e:
    #         raise Exception(f"獲取SXM狀態失敗: {str(e)}")
    def get_sxm_status(self) -> dict:
        """
        獲取STM當前狀態，並轉換為前端所需的格式
        
        Returns
        -------
        dict
            轉換後的狀態資訊
        """
        try:
            if not self.ensure_controller():
                raise Exception("STM控制器未初始化")
                
            # 從 SXMController 獲取完整狀態
            status = self.stm.get_sxm_status()
            
            # 轉換為前端所需的格式
            return {
                'center_x': float(status['center_x']),
                'center_y': float(status['center_y']),
                'scan_range': float(status['range']),  # 注意這裡的鍵名轉換
                'scan_angle': float(status['angle']),  # 注意這裡的鍵名轉換
                'total_lines': int(status['total_lines']),
                'aspect_ratio': float(status['aspect_ratio'])
            }
            
        except Exception as e:
            print(f"獲取SXM狀態失敗: {str(e)}")
            raise
        
    def save_local_cits_area_script(self, script_data: dict) -> bool:
        """
        儲存局部 CITS 區域腳本

        Parameters
        ----------
        script_data : dict
            腳本資料，包含：
            - name: str, 腳本名稱
            - areas: list, 區域設定列表
            - description: str, 可選的描述
        
        Returns
        -------
        bool
            儲存是否成功
        """
        try:
            # 驗證必要欄位
            if not all(key in script_data for key in ['name', 'areas']):
                raise ValueError("缺少必要的腳本資料欄位")
            
            # 設定腳本存放路徑
            local_cits_dir = self.scripts_dir / "local_cits_areas"
            local_cits_dir.mkdir(parents=True, exist_ok=True)

            # 準備腳本資料
            script = {
                'name': script_data['name'],
                'areas': script_data['areas'],
                'description': script_data.get('description', ''),
                'created_time': time.strftime("%Y-%m-%d %H:%M:%S")
            }

            # 儲存腳本
            script_file = local_cits_dir / f"{script_data['name']}.json"
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(script, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"儲存局部 CITS 區域腳本失敗: {str(e)}")
            raise Exception(f"無法儲存腳本: {str(e)}")

    def get_local_cits_area_scripts(self) -> dict:
        """
        獲取所有已儲存的局部 CITS 區域腳本

        Returns
        -------
        dict
            腳本名稱和內容的映射
        """
        try:
            local_cits_dir = self.scripts_dir / "local_cits_areas"
            if not local_cits_dir.exists():
                return {}

            scripts = {}
            for script_file in local_cits_dir.glob("*.json"):
                with open(script_file, encoding='utf-8') as f:
                    script_data = json.load(f)
                    scripts[script_data['name']] = script_data

            return scripts

        except Exception as e:
            print(f"讀取局部 CITS 區域腳本失敗: {str(e)}")
            return {}
    # ========== Local CITS functions END ========== #

    # ========== Auto move measurement functions ========== #
    def auto_move_scan_area(self, movement_script: str, distance: float,
                            wait_time: float, repeat_count: int = 1) -> bool:
        """
        執行自動移動和掃描序列

        Parameters
        ----------
        movement_script : str
            移動指令序列，如 "RULLDDRR"
        distance : float
            每次移動的距離（nm）
        wait_time : float
            每次移動後的等待時間（秒）
        repeat_count : int
            每個位置的掃描重複次數

        Returns
        -------
        bool
            執行是否成功
        """
        try:
            if not self.stm:
                raise Exception("STM控制器未初始化")

            return self.stm.auto_move_scan_area(
                movement_script=movement_script,
                distance=distance,
                wait_time=wait_time,
                repeat_count=repeat_count
            )

        except Exception as e:
            print(f"自動移動掃描錯誤: {str(e)}")
            return False

    def auto_move_ssts_cits(self, movement_script: str, distance: float,
                            num_points_x: int, num_points_y: int,
                            initial_direction: int = 1,
                            wait_time: float = 1.0,
                            repeat_count: int = 1) -> bool:
        """
        執行自動移動和標準 CITS 量測序列

        Parameters
        ----------
        movement_script : str
            移動指令序列，如 "RULLDDRR"
        distance : float
            每次移動的距離（nm）
        num_points_x, num_points_y : int
            CITS 的 X、Y 方向點數
        initial_direction : int
            起始掃描方向（1: 向上, -1: 向下）
        wait_time : float
            每次移動後的等待時間（秒）
        repeat_count : int
            每個位置的CITS重複次數

        Returns
        -------
        bool
            執行是否成功
        """
        try:
            if not self.ensure_controller():
                raise Exception("STM控制器未初始化")

            return self.stm.auto_move_ssts_CITS(
                movement_script=movement_script,
                distance=distance,
                num_points_x=num_points_x,
                num_points_y=num_points_y,
                initial_direction=initial_direction,
                wait_time=wait_time,
                repeat_count=repeat_count
            )

        except Exception as e:
            print(f"自動移動CITS錯誤: {str(e)}")
            return False

    def auto_move_msts_cits(self, movement_script: str, distance: float,
                            num_points_x: int, num_points_y: int,
                            script_name: str,
                            initial_direction: int = 1,
                            wait_time: float = 1.0,
                            repeat_count: int = 1) -> bool:
        """
        執行自動移動和Multi-STS CITS量測序列

        Parameters
        ----------
        movement_script : str
            移動指令序列，如 "RULLDDRR"
        distance : float
            每次移動的距離（nm）
        num_points_x, num_points_y : int
            CITS 的 X、Y 方向點數
        script_name : str
            Multi-STS 腳本名稱
        initial_direction : int
            起始掃描方向（1: 向上, -1: 向下）
        wait_time : float
            每次移動後的等待時間（秒）
        repeat_count : int
            每個位置的CITS重複次數

        Returns
        -------
        bool
            執行是否成功
        """
        try:
            if not self.ensure_controller():
                raise Exception("STM控制器未初始化")

            return self.stm.auto_move_msts_CITS(
                movement_script=movement_script,
                distance=distance,
                num_points_x=num_points_x,
                num_points_y=num_points_y,
                script_name=script_name,
                initial_direction=initial_direction,
                wait_time=wait_time,
                repeat_count=repeat_count
            )

        except Exception as e:
            print(f"自動移動Multi-STS CITS錯誤: {str(e)}")
            return False

    def auto_move_local_ssts_cits(self, movement_script: str, distance: float,
                                  local_areas_params: list,
                                  initial_direction: int = 1,
                                  wait_time: float = 1.0,
                                  repeat_count: int = 1) -> bool:
        """
        執行自動移動和Local CITS量測序列

        Parameters
        ----------
        movement_script : str
            移動指令序列，如 "RULLDDRR"
        distance : float
            每次移動的距離（nm）
        local_areas_params : list of dict
            小區參數列表，每個字典包含：
            {
                'x_dev': float,  # X偏移（nm）
                'y_dev': float,  # Y偏移（nm）
                'nx': int,      # X方向點數
                'ny': int,      # Y方向點數
                'dx': float,    # X方向步進（nm）
                'dy': float,    # Y方向步進（nm）
                'startpoint_direction': int  # 起始點方向
            }
        initial_direction : int
            起始掃描方向（1: 向上, -1: 向下）
        wait_time : float
            每次移動後的等待時間（秒）
        repeat_count : int
            每個位置的CITS重複次數

        Returns
        -------
        bool
            執行是否成功
        """
        try:
            if not self.ensure_controller():
                raise Exception("STM控制器未初始化")

            return self.stm.auto_move_local_ssts_CITS(
                movement_script=movement_script,
                distance=distance,
                local_areas_params=local_areas_params,
                initial_direction=initial_direction,
                wait_time=wait_time,
                repeat_count=repeat_count
            )

        except Exception as e:
            print(f"自動移動Local CITS錯誤: {str(e)}")
            return False

    def auto_move_local_msts_cits(self, movement_script: str, distance: float,
                                  local_areas_params: list, script_name: str,
                                  initial_direction: int = 1,
                                  wait_time: float = 1.0,
                                  repeat_count: int = 1) -> bool:
        """
        執行自動移動和Local Multi-STS CITS量測序列

        Parameters
        ----------
        movement_script : str
            移動指令序列，如 "RULLDDRR"
        distance : float
            每次移動的距離（nm）
        local_areas_params : list of dict
            小區參數列表，每個字典包含：
            {
                'x_dev': float,  # X偏移（nm）
                'y_dev': float,  # Y偏移（nm）
                'nx': int,      # X方向點數
                'ny': int,      # Y方向點數
                'dx': float,    # X方向步進（nm）
                'dy': float,    # Y方向步進（nm）
                'startpoint_direction': int  # 起始點方向
            }
        script_name : str
            Multi-STS 腳本名稱
        initial_direction : int
            起始掃描方向（1: 向上, -1: 向下）
        wait_time : float
            每次移動後的等待時間（秒）
        repeat_count : int
            每個位置的CITS重複次數

        Returns
        -------
        bool
            執行是否成功
        """
        try:
            if not self.ensure_controller():
                raise Exception("STM控制器未初始化")

            return self.stm.auto_move_local_msts_CITS(
                movement_script=movement_script,
                distance=distance,
                local_areas_params=local_areas_params,
                script_name=script_name,
                initial_direction=initial_direction,
                wait_time=wait_time,
                repeat_count=repeat_count
            )

        except Exception as e:
            print(f"自動移動Local Multi-STS CITS錯誤: {str(e)}")
            return False

    def save_auto_move_script(self, script_data: dict) -> bool:
        """
        儲存自動移動腳本
        
        Parameters
        ----------
        script_data : dict
            腳本資料，包含：
            - name: 腳本名稱
            - script: 移動指令（例如：'RULLDDRR'）
            - distance: 移動距離（nm）
            - waitTime: 等待時間（秒）
            - repeatCount: 重複次數
        
        Returns
        -------
        bool
            儲存是否成功
        """
        try:
            # 驗證必要欄位
            required_fields = ['name', 'script', 'distance', 'waitTime', 'repeatCount']
            if not all(field in script_data for field in required_fields):
                raise ValueError("缺少必要的腳本資料欄位")
            
            # 驗證移動指令格式
            if not all(c in 'RULD' for c in script_data['script']):
                raise ValueError("移動指令只能包含 R, U, L, D")

            # 設定腳本存放路徑
            base_dir = Path(__file__).parent
            scripts_dir = base_dir / "SXMPycontroller_scripts" / "move_scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)

            # 儲存腳本
            script_file = scripts_dir / f"{script_data['name']}.json"
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'name': script_data['name'],
                    'script': script_data['script'],
                    'distance': float(script_data['distance']),
                    'waitTime': float(script_data['waitTime']),
                    'repeatCount': int(script_data['repeatCount']),
                    'created_time': time.strftime("%Y-%m-%d %H:%M:%S")
                }, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"儲存自動移動腳本失敗: {str(e)}")
            raise Exception(f"無法儲存腳本: {str(e)}")

    def get_auto_move_scripts(self) -> dict:
        """
        獲取所有已儲存的自動移動腳本
        
        Returns
        -------
        dict
            腳本名稱和內容的映射
        """
        try:
            base_dir = Path(__file__).parent
            scripts_dir = base_dir / "SXMPycontroller_scripts" / "move_scripts"
            if not scripts_dir.exists():
                return {}

            scripts = {}
            for script_file in scripts_dir.glob("*.json"):
                with open(script_file, encoding='utf-8') as f:
                    script_data = json.load(f)
                    scripts[script_data['name']] = script_data

            return scripts

        except Exception as e:
            print(f"讀取自動移動腳本失敗: {str(e)}")
            return {}

    def get_auto_move_script(self, script_name: str) -> dict:
        """
        獲取指定的自動移動腳本
        
        Parameters
        ----------
        script_name : str
            腳本名稱
        
        Returns
        -------
        dict
            腳本資料
        """
        try:
            base_dir = Path(__file__).parent
            script_file = base_dir / "SXMPycontroller_scripts" / "move_scripts" / f"{script_name}.json"

            if not script_file.exists():
                raise ValueError(f"找不到腳本: {script_name}")

            with open(script_file, encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            raise Exception(f"無法讀取腳本: {str(e)}")
    # ========== Auto move measurement functions END ========== #

    # ========== Preview functions ========== #
    def preview_auto_move(self, params: dict) -> dict:
        """
        生成自動移動預覽圖資料
        
        Parameters
        ----------
        params : dict
            預覽參數，包含：
            - movement_script: str
            - distance: float
            - center_x: float
            - center_y: float
            - angle: float
        
        Returns
        -------
        dict
            可序列化的圖表資料
        """
        try:
            from utils.SXMPyPlot import AutoMovePreviewer
            
            # 建立預覽器實例
            previewer = AutoMovePreviewer(
                movement_script=params['movement_script'],
                distance=params['distance'],
                center_x=params['center_x'],
                center_y=params['center_y'],
                angle=params['angle'],
                debug_mode=True
            )
            
            # 獲取可序列化的數據
            plot_data = previewer.get_serializable_plot_data()

            return plot_data
            
        except Exception as e:
            print(f"Auto move preview error: {str(e)}")
            raise Exception(f"Failed to generate preview: {str(e)}")
        
    def preview_local_cits(self, params: dict) -> dict:
        """
        生成 Local CITS 預覽圖資料
        """
        try:
            from utils.SXMPyPlot import LocalCITSPreviewer
            from utils.SXMPyCalc import LocalCITSParams
            
            # 將字典轉換為 LocalCITSParams 物件列表
            local_areas = []
            for area_dict in params['local_areas']:
                area = LocalCITSParams(
                    start_x=area_dict['start_x'],
                    start_y=area_dict['start_y'],
                    dx=area_dict['dx'],
                    dy=area_dict['dy'],
                    nx=area_dict['nx'],
                    ny=area_dict['ny'],
                    startpoint_direction=area_dict['startpoint_direction']
                )
                local_areas.append(area)
                
            # 更新參數字典，替換為正確的物件類型
            params['local_areas'] = local_areas
            
            # 生成預覽
            previewer = LocalCITSPreviewer()
            plot_data = previewer.get_serializable_plot_data(params)
            
            return plot_data
                
        except Exception as e:
            print(f"Local CITS preview error: {str(e)}")
            raise Exception(f"Failed to generate Local CITS preview: {str(e)}")

    # ========== CITS functions END ========== #

    def cleanup(self):
        """清理資源"""
        try:
            if self.smu:
                # 關閉所有輸出
                for channel in [1, 2]:
                    try:
                        self.set_channel_output(channel, False)
                    except:
                        pass

                # 斷開連接
                try:
                    self.smu.disconnect()
                except:
                    pass

                self.smu = None

        except Exception as e:
            print(f"清理時發生錯誤: {str(e)}")

    def __del__(self):
        """解構子"""
        self.cleanup()
