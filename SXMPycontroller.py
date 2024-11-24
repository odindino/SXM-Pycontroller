from modules.SXMPyCITS import SXMCITSControl
from utils.SXMPyLogger import initialize_logger, log_execution, LogConfig

class SXMController(SXMCITSControl):
    """
    STM控制器主類別
    整合所有功能模組並提供統一的操作介面
    """
    def __init__(self, debug_mode=False, enable_function_tracking=True):
        """
        初始化STM控制器
        
        Parameters
        ----------
        debug_mode : bool
            是否啟用除錯模式
        enable_function_tracking : bool
            是否啟用函數執行追蹤
        """
        super().__init__(debug_mode)
        
        # 初始化日誌系統
        config = LogConfig(
            debug_mode=debug_mode,
            function_tracking=enable_function_tracking,
            tracking_interval=5  # 每5秒記錄一次時間戳記
        )
        self.logger = initialize_logger(config)
        
        if debug_mode:
            self.logger.debug("STM Controller initialized")
            
    @log_execution()
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
            self.logger.debug(f"System initialized at position ({x}, {y})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization Error: {str(e)}")
            return False
    
    @log_execution()
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
            
            # 停止函數追蹤
            self.logger.stop_tracking()
            
            self.logger.debug("System safely shut down")
            
        except Exception as e:
            self.logger.error(f"Shutdown Error: {str(e)}")
            
    @log_execution()
    def auto_move_scan_area(self, movement_script: str, distance: float,
                           wait_time: float, repeat_count: int = 1) -> bool:
        """
        自動移動掃描區域
        
        Parameters
        ----------
        movement_script : str
            移動腳本，例如 "RULD"
        distance : float
            移動距離（nm）
        wait_time : float
            等待時間（秒）
        repeat_count : int
            重複次數
        
        Returns
        -------
        bool
            移動是否成功
        """
        self.logger.debug(
            f"Starting auto move scan:\n"
            f"Movement script: {movement_script}\n"
            f"Distance: {distance} nm\n"
            f"Wait time: {wait_time} s\n"
            f"Repeat count: {repeat_count}"
        )
        
        # 原有的 auto_move_scan_area 實作...
        return super().auto_move_scan_area(
            movement_script, distance, wait_time, repeat_count
        )