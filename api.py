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
from pathlib import Path
from utils.KB2902BSMU import KeysightB2902B, Channel, OutputMode, ConnectionError
from modules.SXMPycontroller import SXMController

class SMUControlAPI:
    """WebView GUI API實作"""
    
    def __init__(self):
        """初始化API"""
        self._setup_logging()
        
        # 初始化控制器
        self.smu = None
        self.stm = SXMController(debug_mode=True)
        
        # 執行緒同步
        self._lock = threading.Lock()
        self._reading_active = {1: False, 2: False}
        self._reading_threads: Dict[int, threading.Thread] = {}
        
        # SMU設定
        self._compliance = {1: 0.01, 2: 0.01}  # 預設compliance值
        
        # 註冊STS控制器回調
        self._register_sts_callbacks()
        
    def _setup_logging(self):
        """設定日誌記錄"""
        self.logger = logging.getLogger("SMUControlAPI")
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _register_sts_callbacks(self):
        """註冊STS控制器回調函數"""
        try:
            self.stm.sts_controller.on_status_change = self._update_sts_status
            self.stm.sts_controller.on_progress = self._update_sts_progress
        except Exception as e:
            self.logger.error(f"Failed to register callbacks: {str(e)}")

    # ========== SMU Control Functions ========== #
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
                # 初始化設定
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

    def beep(self, frequency=1000, duration=0.1):
        """發出蜂鳴聲"""
        try:
            if self.smu and self.smu.smu:
                self.smu.beep(frequency, duration)
        except Exception:
            pass  # 蜂鳴器失敗不影響主要功能

    # ========== Channel Control Functions ========== #
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
                actual_state = bool(int(self.smu.smu.query(f":OUTP{channel}?")))
                if actual_state != state:
                    raise Exception(f"輸出狀態設定失敗（預期：{state}，實際：{actual_state}）")
                    
            return success
            
        except Exception as e:
            self.logger.error(f"Set channel output failed: {str(e)}")
            raise Exception(f"設定通道{channel}輸出狀態失敗: {str(e)}")

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
                
                voltage = float(self.smu.smu.query(f":MEAS:VOLT? (@{channel})"))
                time.sleep(0.05)
                current = float(self.smu.smu.query(f":MEAS:CURR? (@{channel})"))
                
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

    # ========== STS Control Functions ========== #
    def start_sts(self) -> bool:
        """執行單點STS測量"""
        try:
            if not self.stm:
                raise ConnectionError("STM未連接")
                
            self._update_sts_status("開始STS測量")
            success = self.stm.sts_controller.start_single_sts()
            
            if success:
                self.beep()
                self._update_sts_status("測量完成")
            else:
                self._update_sts_status("測量失敗")
                
            return success
            
        except Exception as e:
            self.logger.error(f"STS execution error: {str(e)}")
            self._update_sts_status(f"錯誤: {str(e)}")
            return False

    def perform_multi_sts(self, script_name: str) -> bool:
        """執行多點STS測量"""
        try:
            script = self.stm.sts_controller.load_script(script_name)
            if not script:
                raise ValueError(f"找不到腳本: {script_name}")
            return self.stm.sts_controller.execute_sts_script(script)
        except Exception as e:
            self.logger.error(f"Multi-STS execution error: {str(e)}")
            return False

    def save_sts_script(self, name: str, vds_list: list, vg_list: list) -> bool:
        """儲存STS測量腳本"""
        try:
            from modules.SXMSTSController import STSScript
            script = STSScript(name, vds_list, vg_list)
            return self.stm.sts_controller.save_script(script)
        except Exception as e:
            self.logger.error(f"Save script error: {str(e)}")
            return False

    def get_sts_scripts(self) -> dict:
        """獲取所有STS測量腳本"""
        try:
            scripts = self.stm.sts_controller.get_all_scripts()
            return {
                name: script.to_dict()
                for name, script in scripts.items()
            }
        except Exception as e:
            self.logger.error(f"Get scripts error: {str(e)}")
            return {}

    # ========== UI Update Callbacks ========== #
    def _update_sts_status(self, status: str):
        """更新STS狀態到UI"""
        try:
            window = webview.windows[0]
            window.evaluate_js(f"updateSTSStatus('{status}')")
        except Exception as e:
            self.logger.error(f"Status update error: {str(e)}")

    def _update_sts_progress(self, progress: float):
        """更新STS進度到UI"""
        try:
            window = webview.windows[0]
            window.evaluate_js(f"updateSTSProgress({progress})")
        except Exception as e:
            self.logger.error(f"Progress update error: {str(e)}")

    def cleanup(self):
        """清理資源"""
        try:
            self.disconnect_smu()
            if self.stm:
                self.stm.safe_shutdown()
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")