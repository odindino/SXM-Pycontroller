from modules.SXMPyCITS import SXMCITSControl
from utils.SXMPyLogger import SXMLogger

class SXMController(SXMCITSControl):
    """
    STM控制器主類別
    整合所有功能模組並提供統一的操作介面
    """
    def __init__(self, debug_mode=False):
        super().__init__(debug_mode)
        self.logger = SXMLogger(debug_mode)
        
        if debug_mode:
            self.logger.log_debug("SXM Controller initialized")
            
    def initialize_system(self):
        """
        初始化系統
        設定基本參數並檢查系統狀態
        """
        try:
            # 確認系統狀態
            self.feedback_on()  # 確保回饋開啟
            
            # 設定一些基本參數
            self.SetScanPara('Speed', 2.0)     # 掃描速度
            self.SetScanPara('Range', 100.0)   # 掃描範圍 (nm)
            
            # 讀取當前位置
            x, y = self.get_position()
            self.logger.log_debug(f"System initialized at position ({x}, {y})")
            
            return True
            
        except Exception as e:
            self.logger.log_error("Initialization Error", str(e))
            return False
            
    def safe_shutdown(self):
        """
        安全關閉系統
        確保所有操作都已完成並回到安全狀態
        """
        try:
            # 停止掃描
            self.scan_off()
            
            # 確保回饋開啟
            self.feedback_on()
            
            # 停止事件監聽
            self.stop_monitoring()
            
            self.logger.log_debug("System safely shut down")
            
        except Exception as e:
            self.logger.log_error("Shutdown Error", str(e))