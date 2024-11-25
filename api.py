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
        self.smu: Optional[KeysightB2902B] = None
        self.stm = SXMSpectroControl(debug_mode=True)
        self._lock = threading.Lock()
        self._reading_active = {1: False, 2: False}
        self._reading_threads: Dict[int, threading.Thread] = {}

    def connect_smu(self, address: str) -> bool:
        """
        連接SMU

        Args:
            address: VISA address string
        """
        try:
            with self._lock:
                if self.smu is not None:
                    self.disconnect_smu()

                self.smu = KeysightB2902B()
                return self.smu.connect(address)

        except Exception as e:
            raise Exception(f"連接失敗: {str(e)}")

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

            return self.smu.configure_source(
                channel=channel_enum,
                mode=output_mode,
                level=value,
                compliance=self._compliance
            )

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
                return self.smu.enable_output(channel_enum)
            else:
                return self.smu.disable_output(channel_enum)

        except Exception as e:
            raise Exception(f"設定通道{channel}輸出狀態失敗: {str(e)}")

    def set_compliance(self, value: float) -> bool:
        """設定電流限制值"""
        try:
            if not self.smu:
                raise Exception("SMU未連接")

            self._compliance = value
            return True

        except Exception as e:
            raise Exception(f"設定限制值失敗: {str(e)}")

    def read_channel(self, channel: int) -> Dict[str, float]:
        """
        讀取通道數值

        Args:
            channel: 通道號(1或2)

        Returns:
            Dict containing voltage and current readings
        """
        try:
            if not self.smu:
                raise Exception("SMU未連接")

            channel_enum = Channel.CH1 if channel == 1 else Channel.CH2
            reading = self.smu.measure(channel_enum, ['VOLT', 'CURR'])

            return {
                'voltage': reading[0],
                'current': reading[1]
            }

        except Exception as e:
            raise Exception(f"讀取通道{channel}失敗: {str(e)}")

    def start_reading(self, channel: int) -> bool:
        """開始持續讀值"""
        with self._lock:
            if channel in self._reading_threads:
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

    def stop_reading(self, channel: int) -> bool:
        """停止持續讀值"""
        with self._lock:
            self._reading_active[channel] = False
            if channel in self._reading_threads:
                self._reading_threads[channel].join(timeout=1.0)
                del self._reading_threads[channel]
            return True

    def _reading_loop(self, channel: int):
        """讀值循環"""
        while self._reading_active[channel]:
            try:
                reading = self.read_channel(channel)
                # 通過window.pywebview.api回傳數據到前端
                window = webview.windows[0]
                window.evaluate_js(
                    f"updateChannelReading({channel}, {reading['voltage']}, {reading['current']})"
                )
            except Exception as e:
                print(f"讀值錯誤(通道{channel}): {str(e)}")
            time.sleep(0.1)  # 100ms讀值間隔

    def start_sts(self) -> bool:
        """開始STS測量"""
        try:
            success = self.stm.spectroscopy_start()
            if not success:
                raise Exception("啟動STS失敗")
            return True

        except Exception as e:
            raise Exception(f"STS測量失敗: {str(e)}")

    def __del__(self):
        """清理資源"""
        try:
            self.disconnect_smu()
        except:
            pass
