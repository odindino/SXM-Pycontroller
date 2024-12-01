from . import SXMRemote
import time
from config.SXMParameters import SXMParameters
from typing import Optional

class SXMBase:
    """
    SXM控制器的基礎類別
    提供基本的DDE通訊和參數存取功能
    """
    def __init__(self, debug_mode=False):
        # DDE客戶端
        self.MySXM = SXMRemote.DDEClient("SXM", "Remote")
        self.debug_mode = debug_mode
        
        # 參數定義
        self.parameters = SXMParameters()
        
        # 當前狀態
        self.current_state = {
            'x': None,          # X位置 (nm)
            'y': None,          # Y位置 (nm)
            'range': None,      # 掃描範圍 (nm)
            'angle': None,      # 掃描角度 (degrees)
            'scan_state': None, # 掃描狀態
            'speed': None,      # 掃描速度
            'pixel_ratio': 1.0, # Pixel density (預設1.0)
            'aspect_ratio': 1.0 # Image format (預設1.0)
        }
        
        # 時間戳記
        self.last_update = None

    def _send_command(self, command: str) -> tuple[bool, Optional[str]]:
        """
        發送DDE命令到SXM
        
        Parameters
        ----------
        command : str
            DDE命令
            
        Returns
        -------
        Tuple[bool, Optional[str]]
            (成功與否, 回應內容)
        """
        try:
            if self.debug_mode:
                print(f"Sending command: {command}")
                
            # 使用SendWait而不是execute
            self.MySXM.SendWait(command)
            response = self.MySXM.LastAnswer
                
            if self.debug_mode:
                print(f"Response: {response}")
                
            return True, response
            
        except Exception as e:
            if self.debug_mode:
                print(f"Command error: {str(e)}")
            return False, None

    def _parse_response(self, response):
        """
        解析DDE回應
        
        Parameters
        ----------
        response : bytes or str
            DDE回應
            
        Returns
        -------
        Any
            解析後的值
        """
        try:
            if isinstance(response, bytes):
                response_str = response.decode('utf-8').strip()
                lines = response_str.split('\r\n')
                
                # 跳過DDE命令行
                for line in lines:
                    if not line.startswith('DDE Cmd'):
                        try:
                            return float(line.strip())
                        except ValueError:
                            continue
                            
            return None
            
        except Exception as e:
            if self.debug_mode:
                print(f"Parse error: {str(e)}")
            return None

    def GetScanPara(self, param):
        """
        獲取掃描參數
        
        Parameters
        ----------
        param : str
            參數名稱
            
        Returns
        -------
        float or None
            參數值
        """
        try:
            if param not in self.parameters.SCAN_PARAMS:
                raise ValueError(f"Unknown scan parameter: {param}")

            command = (
                "a := 0.0;\n"
                f"a := GetScanPara('{param}');\n"
                "Writeln(a);"
            )
            success, response = self._send_command(command)
            
            if success:
                value = self._parse_response(response)
                if value is not None:
                    # 更新狀態
                    self._update_state(param.lower(), value)
                return value
            return None
            
        except Exception as e:
            if self.debug_mode:
                print(f"GetScanPara error: {str(e)}")
            return None

    def GetFeedbackPara(self, param):
        """
        獲取回饋參數
        
        Parameters
        ----------
        param : str
            參數名稱
            
        Returns
        -------
        Any
            參數值
        """
        try:
            if param not in self.parameters.FEEDBACK_PARAMS:
                raise ValueError(f"Unknown feedback parameter: {param}")

            command = (
                "a := 0.0;\n"
                f"a := GetFeedPara('{param}');\n"
                "Writeln(a);"
            )
            success, response = self._send_command(command)
            
            if success:
                return self._parse_response(response)
            return None
            
        except Exception as e:
            if self.debug_mode:
                print(f"GetFeedbackPara error: {str(e)}")
            return None

    def SetScanPara(self, param, value):
        """
        設定掃描參數
        
        Parameters
        ----------
        param : str
            參數名稱
        value : float
            參數值
            
        Returns
        -------
        bool
            設定是否成功
        """
        try:
            if param not in self.parameters.SCAN_PARAMS:
                raise ValueError(f"Unknown scan parameter: {param}")

            command = f"ScanPara('{param}', {value});"
            success, _ = self._send_command(command)
            
            if success:
                # 驗證設定
                current_value = self.GetScanPara(param)
                if current_value is not None and abs(float(current_value) - float(value)) < 1e-2:
                    self._update_state(param.lower(), value)
                    return True
            return False
            
        except Exception as e:
            if self.debug_mode:
                print(f"SetScanPara error: {str(e)}")
            return False
        
    def SetFeedPara(self, param, value):
        """
        設定回饋參數
        
        Parameters
        ----------
        param : str
            參數名稱
        value : Any
            參數值
            
        Returns
        -------
        bool
            設定是否成功
        """
        try:
            if param not in self.parameters.FEEDBACK_PARAMS:
                raise ValueError(f"Unknown feedback parameter: {param}")

            command = f"FeedPara('{param}', {value});"
            success, _ = self._send_command(command)
            
            if success and param != 'ZOffset':
                # 驗證設定
                current_value = self.GetFeedbackPara(param)
                if current_value is not None:
                    if isinstance(value, bool):
                        return bool(current_value) == value
                    else:
                        return abs(float(current_value) - float(value)) < 1e-6
            return False
            
        except Exception as e:
            if self.debug_mode:
                print(f"SetFeedPara error: {str(e)}")
            return False

    def _update_state(self, key, value):
        """
        更新狀態並記錄時間戳記
        
        Parameters
        ----------
        key : str
            狀態鍵值
        value : Any
            狀態值
        """
        if key in self.current_state:
            self.current_state[key] = value
            self.last_update = time.time()