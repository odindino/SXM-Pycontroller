# modules/SXMPySpectro.py

import time
from .SXMPyScan import SXMScanControl
from utils.KB2902BSMU import KeysightB2902B


class SXMSpectroControl(SXMScanControl):
    """
    光譜測量和回饋控制類別
    繼承掃描控制以獲得位置控制和掃描功能
    """

    def __init__(self, debug_mode=False):
        super().__init__(debug_mode)
        self.FbOn = None  # 回饋狀態

    # ========== 回饋控制功能 ========== #
    def feedback_on(self):
        """
        開啟回饋控制

        Returns
        -------
        bool
            是否成功開啟
        """
        success = self.SetFeedPara('Enable', 0)
        if success:
            self.FbOn = 0
        return success

    def feedback_off(self):
        """
        關閉回饋控制

        Returns
        -------
        bool
            是否成功關閉
        """
        success = self.SetFeedPara('Enable', 1)
        if success:
            self.FbOn = 1
        return success

    def get_feedback_state(self):
        """
        獲取回饋控制狀態

        Returns
        -------
        bool
            True表示回饋正常，False表示異常
        """
        current_state = self.GetFeedbackPara('Enable')
        return self.FbOn == current_state

    def set_feedback_mode(self, mode):
        """
        設定回饋模式

        Parameters
        ----------
        mode : int
            回饋模式（參考SXMParameters.FEEDBACK_PARAMS的定義）

        Returns
        -------
        bool
            設定是否成功
        """
        return self.SetFeedPara('Mode', mode)

    # ========== 光譜測量功能 ========== #
    def move_tip_for_spectro(self, x, y):
        """
        移動探針到指定位置進行光譜測量

        Parameters
        ----------
        x, y : float
            目標位置（nm）

        Returns
        -------
        bool
            移動是否成功
        """
        try:
            # 設定光譜測量位置
            command1 = f"SpectPara(1, {x});"
            command2 = f"SpectPara(2, {y});"

            success = (self._send_command(command1)[0] and
                       self._send_command(command2)[0])

            return success

        except Exception as e:
            if self.debug_mode:
                print(f"Move tip error: {str(e)}")
            return False

    def setup_spectroscopy(self, mode, params=None):
        """
        設定光譜測量參數

        Parameters
        ----------
        mode : int
            測量模式
        params : dict, optional
            測量參數，包含：
            - start_bias: 起始偏壓（V）
            - end_bias: 結束偏壓（V）
            - points: 測量點數
            - delay: 延遲時間（ms）

        Returns
        -------
        bool
            設定是否成功
        """
        try:
            success = True

            # 設定模式
            command = f"SpectPara(0, {mode});"
            success &= self._send_command(command)[0]

            if params:
                # 設定點數
                if 'points' in params:
                    command = f"SpectPara('Points', {params['points']});"
                    success &= self._send_command(command)[0]

                # 設定偏壓範圍
                if 'start_bias' in params:
                    command = f"SpectPara(7, {params['start_bias']});"
                    success &= self._send_command(command)[0]

                if 'end_bias' in params:
                    command = f"SpectPara(8, {params['end_bias']});"
                    success &= self._send_command(command)[0]

                # 設定延遲
                if 'delay' in params:
                    command = f"SpectPara(4, {params['delay']});"
                    success &= self._send_command(command)[0]

            return success

        except Exception as e:
            if self.debug_mode:
                print(f"Setup spectroscopy error: {str(e)}")
            return False

    def spectroscopy_start(self):
        """
        開始光譜測量

        Returns
        -------
        bool
            啟動是否成功
        """
        return self._send_command("SpectStart;")[0]

    def perform_spectroscopy(self, x, y, wait_time=1.0, params=None):
        """
        在指定位置執行完整的光譜測量

        Parameters
        ----------
        x, y : float
            測量位置（nm）
        wait_time : float
            移動後的等待時間（秒）
        params : dict, optional
            測量參數

        Returns
        -------
        bool
            測量是否成功
        """
        try:
            # 移動到測量位置
            if not self.move_tip_for_spectro(x, y):
                return False

            # 等待穩定
            time.sleep(wait_time)

            # 關閉回饋
            if not self.feedback_off():
                return False

            # 如果有參數，設定測量參數
            # 模式1: I(V)測量
            if params and not self.setup_spectroscopy(1, params):
                return False

            # 開始測量
            if not self.spectroscopy_start():
                return False

            # 等待測量完成（根據參數計算等待時間）
            if params:
                total_time = (params.get('points', 200) *
                              params.get('delay', 100) / 1000 + 1)
                time.sleep(total_time)

            # 重新開啟回饋
            self.feedback_on()

            return True

        except Exception as e:
            if self.debug_mode:
                print(f"Perform spectroscopy error: {str(e)}")
            # 確保回饋被重新開啟
            self.feedback_on()
            return False

    def perform_spectroscopy_sequence(self, positions, params=None):
        """
        執行一系列位置的光譜測量

        Parameters
        ----------
        positions : list of tuple
            測量位置列表，每個元素為(x, y)
        params : dict, optional
            測量參數

        Returns
        -------
        list
            成功測量的位置索引列表
        """
        successful_measurements = []

        for i, (x, y) in enumerate(positions):
            if self.debug_mode:
                print(f"Measuring position {i+1}/{len(positions)}: ({x}, {y})")

            if self.perform_spectroscopy(x, y, params=params):
                successful_measurements.append(i)
                if self.debug_mode:
                    print(f"Measurement at position {i} successful")
            else:
                if self.debug_mode:
                    print(f"Measurement at position {i} failed")

        return successful_measurements
