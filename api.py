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

from utils.KB2902BSMU import KeysightB2902B, Channel, OutputMode
from modules.SXMPySpectro import SXMSpectroControl
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
        self.stm_controller = None
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
            address: VISA address string
        """
        try:
            self.smu = KeysightB2902B()
            success = self.smu.connect(address)
            if success:
                # 連接時設定初始compliance
                self.stm.initialize_sts_controller(self)
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

                # 讀取前儲存原始輸出狀態
                original_output_state = bool(int(self.smu.smu.query(f":OUTP{channel}?")))

                # 使用正確的smu物件
                self.smu.smu.write("*CLS")
                self.smu.smu.write(f":CONF:VOLT (@{channel})")
                self.smu.smu.write(f":CONF:CURR (@{channel})")
                self.smu.smu.write(f":SENS{channel}:CURR:NPLC 0.1")
                
                try:
                    voltage = float(self.smu.smu.query(f":MEAS:VOLT? (@{channel})"))
                    time.sleep(0.05)
                    current = float(self.smu.smu.query(f":MEAS:CURR? (@{channel})"))
                    self.beep()  # 讀值成功時發出聲音
                    
                    return {
                        'voltage': voltage,
                        'current': current
                    }
                finally:
                    # 確保輸出狀態不變
                    if not original_output_state:
                        self.smu.smu.write(f":OUTP{channel} OFF")

                # except Exception as e:
                #     self.logger.error(f"測量錯誤: {str(e)}")
                #     raise
                    
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
                        self.smu.write(f":SENS{channel}:CURR:NPLC 0.1")  # 快速測量模式
                        self.smu.write(f":FORM:ELEM:SENS VOLT,CURR")
                        
                        # 分別讀取電壓和電流
                        voltage = float(self.smu.query(f":MEAS:VOLT? (@{channel})"))
                        time.sleep(0.01)  # 短暫延遲
                        current = float(self.smu.query(f":MEAS:CURR? (@{channel})"))
                        
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
                    print(f"Channel {channel} reading failed after {max_retries} retries")
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
        try:
            # 如果控制器不存在，建立新的控制器
            if self.stm_controller is None:
                print("Creating new STM controller...")
                self.stm_controller = SXMController(debug_mode=True)
                print("STM controller created")
                
                # 使用簡單的變數賦值來測試連接
                self.stm_controller.MySXM.SendWait("a := 0;")
                return True
                
            # 如果控制器存在，檢查DDE連接
            try:
                # 使用簡單的變數賦值來測試連接
                self.stm_controller.MySXM.SendWait("a := 0;")
                return True
            except:
                print("Connection lost, recreating controller...")
                self.stm_controller = None
                return self.ensure_controller()
                
        except Exception as e:
            print(f"Controller initialization error: {str(e)}")
            return False

    # ========== SXM functions END ========== #

    ## ========== STS functions ==========
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
                raise Exception("Failed to initialize controller")
                
            print("Starting STS measurement...")
            success = self.stm_controller.spectroscopy_start()
            
            if success:
                print("STS measurement started successfully")
            else:
                print("Failed to start STS measurement")
                
            return success
            
        except Exception as e:
            print(f"STS execution error: {str(e)}")
            return False
        

    def perform_multi_sts(self, script_name: str) -> bool:
        """執行多組STS量測"""
        try:
            if not self.stm.sts_controller:
                raise Exception("STS Controller未初始化")
                
            script = self.stm.sts_controller.get_script(script_name)
            if not script:
                raise ValueError(f"找不到腳本: {script_name}")
                
            return self.stm.sts_controller.perform_multi_sts(script)
            
        except Exception as e:
            raise Exception(f"執行STS量測失敗: {str(e)}")

    def save_sts_script(self, name: str, vds_list: list[float], vg_list: list[float]) -> bool:
        """儲存STS腳本"""
        try:
            if not self.stm.sts_controller:
                raise Exception("STS Controller未初始化")
                
            from modules.SXMSTSController import STSScript
            script = STSScript(name, vds_list, vg_list)
            return self.stm.sts_controller.save_script(script)
            
        except Exception as e:
            raise Exception(f"儲存腳本失敗: {str(e)}")

    def get_sts_scripts(self) -> dict:
        """取得所有腳本資訊"""
        try:
            if not self.stm.sts_controller:
                raise Exception("STS Controller未初始化")
                
            scripts = self.stm.sts_controller.get_all_scripts()
            return {
                name: script.to_dict()
                for name, script in scripts.items()
            }
        except Exception as e:
            raise Exception(f"取得腳本列表失敗: {str(e)}")
    ## ========== STS functions END ==========

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
