"""
STM-SMU Controller API
提供WebView GUI與後端控制系統的介面

Author: Zi-Liang Yang
Version: 1.0.0
Date: 2024-11-26
"""

import threading
import time
import logging
import webview
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from utils.KB2902BSMU import KeysightB2902B, Channel, OutputMode
from utils.SXMPyCalc import LocalCITSParams
from modules.SXMPySpectro import SXMSpectroControl
from modules.SXMPycontroller import SXMController


@dataclass
class ChannelReading:
    """通道讀數數據結構"""
    voltage: float
    current: float
    timestamp: float


class SMUControlAPI:
    """WebView GUI API實作"""

    def __init__(self):
        """初始化API"""

        self.smu = None
        self.stm = None
        self._lock = threading.Lock()
        self._reading_active = {1: False, 2: False}
        self._reading_threads: Dict[int, threading.Thread] = {}
        self._compliance = {1: 0.01, 2: 0.01}  # 預設compliance值（分通道）
        # 註冊清理處理器
        self._cleanup_handler = None
        self._cleanup_event = threading.Event()

    # ========== SMU General functions ========== #
    def connect_smu(self, address: str) -> bool:
        """
        連接SMU

        Args:
            address: VISA地址

        Returns:
            bool: 連接是否成功
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

                self.logger.info(f"Connected to SMU at {address}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Connection failed: {str(e)}")
            raise Exception(f"連接失敗: {str(e)}")

    def disconnect_smu(self) -> bool:
        """
        中斷SMU連接

        Returns:
            bool: 是否成功中斷連接
        """
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

                self.logger.info("Disconnected from SMU")
                return True

        except Exception as e:
            self.logger.error(f"Disconnect failed: {str(e)}")
            raise Exception(f"中斷連接失敗: {str(e)}")
    # ========== SMU General functions END ========== #

    # ========== SMU Channel functions ========== #

    def set_channel_value(self, channel: int, mode: str, value: float) -> bool:
        """設定通道輸出值"""
        try:
            if not self.smu:
                raise ConnectionError("SMU未連接")

            channel_enum = Channel.CH1 if channel == 1 else Channel.CH2
            output_mode = OutputMode.VOLTAGE if mode == 'VOLTAGE' else OutputMode.CURRENT

            # 驗證輸入值的範圍
            if output_mode == OutputMode.VOLTAGE:
                if abs(value) > 200:  # 假設最大電壓為±200V
                    raise ValueError("電壓值超出範圍（最大±200V）")
            else:
                if abs(value) > 0.1:  # 假設最大電流為±100mA
                    raise ValueError("電流值超出範圍（最大±100mA）")

            success = self.smu.configure_source(
                channel=channel_enum,
                mode=output_mode,
                level=value,
                compliance=self._compliance[channel]
            )

            if success:
                self.beep()
                # 驗證設定值
                actual_value = float(self.smu.smu.query(
                    f":SOUR{channel}:{output_mode.value}?"
                ))
                if abs(actual_value - value) > 1e-6:
                    raise Exception(f"設定值驗證失敗（預期：{value}，實際：{actual_value}）")

                self.logger.info(f"Set channel {channel} to {value} ({mode})")

            return success

        except Exception as e:
            self.logger.error(f"Set channel value failed: {str(e)}")
            raise Exception(f"設定通道{channel}失敗: {str(e)}")

    def set_channel_output(self, channel: int, state: bool) -> bool:
        """設定通道輸出開關"""
        try:
            if not self.smu:
                raise ConnectionError("SMU未連接")

            channel_enum = Channel.CH1 if channel == 1 else Channel.CH2

            if state:
                success = self.smu.enable_output(channel_enum)
            else:
                success = self.smu.disable_output(channel_enum)

            if success:
                self.beep()
                self.logger.info(f"Set channel {channel} output to {state}")

                # 回傳實際的輸出狀態
                actual_state = bool(
                    int(self.smu.smu.query(f":OUTP{channel}?")))
                if actual_state != state:
                    raise Exception(f"輸出狀態設定失敗（預期：{state}，實際：{actual_state}）")

            return success

        except Exception as e:
            self.logger.error(f"Set channel output failed: {str(e)}")
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
        """讀取通道數值"""
        try:
            if not self.smu:
                raise ConnectionError("SMU未連接")

            with self._lock:
                self.smu.smu.write("*CLS")
                self.smu.smu.write(f":CONF:VOLT (@{channel})")
                self.smu.smu.write(f":CONF:CURR (@{channel})")
                self.smu.smu.write(f":SENS{channel}:CURR:NPLC 0.1")

                voltage = float(self.smu.smu.query(
                    f":MEAS:VOLT? (@{channel})"))
                time.sleep(0.05)
                current = float(self.smu.smu.query(
                    f":MEAS:CURR? (@{channel})"))

                self.beep()
                return {'voltage': voltage, 'current': current}

        except Exception as e:
            self.logger.error(f"Read channel failed: {str(e)}")
            raise Exception(f"讀取通道{channel}失敗: {str(e)}")

    def set_compliance(self, channel: int, value: float) -> bool:
        """設定限制值"""
        try:
            if not self.smu:
                raise ConnectionError("SMU未連接")

            self._compliance[channel] = value
            self.smu.smu.write(f":SENS{channel}:CURR:PROT {value}")
            self.beep()
            return True

        except Exception as e:
            self.logger.error(f"Set compliance failed: {str(e)}")
            raise Exception(f"設定通道{channel}限制值失敗: {str(e)}")

    def get_compliance(self, channel: int) -> float:
        """獲取通道的compliance值"""
        try:
            if not self.smu:
                raise ConnectionError("SMU未連接")
            return self._compliance[channel]
        except Exception as e:
            self.logger.error(f"Get compliance failed: {str(e)}")
            raise Exception(f"獲取通道{channel}限制值失敗: {str(e)}")

    def abort_measurement(self) -> bool:
        """中止測量"""
        try:
            if self.stm.sts_controller:
                self.stm.sts_controller.abort_measurement()
                self.logger.info("Measurement aborted")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Abort measurement failed: {str(e)}")
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
        """執行單點STS測量"""
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

    def save_sts_script(self, name: str, vds_list: list, vg_list: list) -> bool:
        """儲存STS測量腳本"""
        try:
            if not self.ensure_controller():
                raise Exception("STM控制器未初始化")

            from modules.SXMSTSController import STSScript
            script = STSScript(name, vds_list, vg_list)
            return self.stm.save_script(script)

        except Exception as e:
            self.logger.error(f"Save script error: {str(e)}")
            return False

    def get_sts_scripts(self) -> dict:
        """獲取所有STS測量腳本"""
        try:
            if not self.stm:
                raise Exception("STS Controller未初始化")

            scripts = self.stm.get_all_scripts()
            return {
                name: script.to_dict()
                for name, script in scripts.items()
            }
        except Exception as e:
            raise Exception(f"取得腳本列表失敗: {str(e)}")
    # ========== STS functions END ========== #

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

    def get_sxm_status(self) -> dict:
        """
        獲取 SXM 的當前狀態

        Returns
        -------
        dict
            包含掃描中心、範圍、角度等資訊的字典
        """
        try:
            if not self.ensure_controller():
                raise Exception("STM 控制器未初始化")

            status = {
                'center_x': self.stm.GetScanPara('X'),
                'center_y': self.stm.GetScanPara('Y'),
                'range': self.stm.GetScanPara('Range'),
                'angle': self.stm.GetScanPara('Angle'),
                'total_lines': self.stm.GetScanPara('Pixel'),
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }

            return status

        except Exception as e:
            raise Exception(f"獲取 SXM 狀態失敗: {str(e)}")
    # ========== Local CITS functions END ========== #

    # ========== CITS functions END ========== #

    def cleanup(self):
        """清理資源"""
        try:
            self.disconnect_smu()
            if self.stm:
                self.stm.safe_shutdown()
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")
