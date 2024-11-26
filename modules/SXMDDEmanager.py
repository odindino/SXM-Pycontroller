# modules/SXMDDEManager.py

class DDEConnectionManager:
    """DDE連線管理器"""
    
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
        self.connection_check_interval = 5  # 秒
        self._connected = False
        self._last_check_time = 0
        
    def check_connection(self) -> bool:
        """檢查DDE連線狀態"""
        try:
            # 使用簡單的變數賦值測試連線
            self.MySXM.SendWait("a := 0;")
            self._connected = True
            return True
        except Exception as e:
            if self.debug_mode:
                print(f"Connection check failed: {str(e)}")
            self._connected = False
            return False
            
    def ensure_connection(self) -> bool:
        """確保DDE連線可用"""
        if not self.check_connection():
            try:
                self._reinitialize_connection()
                return self.check_connection()
            except Exception as e:
                if self.debug_mode:
                    print(f"Connection reinitialization failed: {str(e)}")
                return False
        return True
        
    def _reinitialize_connection(self):
        """重新初始化DDE連線"""
        try:
            self.MySXM = None
            import SXMRemote
            self.MySXM = SXMRemote.DDEClient("SXM", "Remote")
            if self.debug_mode:
                print("DDE connection reinitialized")
        except Exception as e:
            raise ConnectionError(f"Failed to reinitialize DDE: {str(e)}")
            
    def execute_command(self, command: str) -> bool:
        """執行DDE命令並確保連線"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self.ensure_connection():
                    continue
                    
                self.MySXM.SendWait(command)
                return True
                
            except Exception as e:
                if self.debug_mode:
                    print(f"Command execution failed (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    raise
                    
        return False