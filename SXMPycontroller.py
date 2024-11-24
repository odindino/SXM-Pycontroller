from modules.SXMPyCITS import SXMCITSControl
from utils.SXMPyLogger import initialize_logger, log_execution, log_procedure, get_logger

class SXMController(SXMCITSControl):
    """
    STM控制器主類別
    整合所有功能模組並提供統一的操作介面
    """
    def __init__(self, debug_mode=False):
        """
        初始化STM控制器
        
        Parameters
        ----------
        debug_mode : bool
            是否啟用除錯模式
        """
        super().__init__(debug_mode)
        self.logger = initialize_logger(debug_mode)
        
        if debug_mode:
            self.logger.debug("STM Controller initialized")
            
    @log_execution()
    def initialize_system(self):
        """初始化系統並設定基本參數"""
        try:
            self.logger.procedure("開始系統初始化")
            
            # 確認系統狀態
            self.feedback_on()  
            self.logger.procedure("回饋控制已開啟")
            
            # 設定基本參數
            self.SetScanPara('Speed', 2.0)     
            self.SetScanPara('Range', 100.0)   
            self.logger.procedure("基本掃描參數已設定")
            
            # 讀取位置
            x, y = self.get_position()
            self.logger.procedure(f"系統初始位置: ({x}, {y})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"初始化錯誤: {str(e)}")
            return False
    
    @log_execution()
    def safe_shutdown(self):
        """安全關閉系統"""
        try:
            self.logger.procedure("開始系統關閉程序")
            
            # 停止掃描
            self.scan_off()
            self.logger.procedure("掃描已停止")
            
            # 確保回饋開啟
            self.feedback_on()
            self.logger.procedure("回饋控制已重新開啟")
            
            # 停止監控
            self.stop_monitoring()
            self.logger.procedure("系統監控已停止")
            
            # 停止函數追蹤
            self.logger.stop_tracking()
            
            self.logger.debug("系統已安全關閉")
            
        except Exception as e:
            self.logger.error(f"關閉錯誤: {str(e)}")
            
    @log_execution()
    @log_procedure("開始執行自動移動掃描")
    def auto_move_scan_area(self, movement_script: str, distance: float,
                           wait_time: float, repeat_count: int = 1) -> bool:
        """自動移動掃描區域"""
        try:
            self.logger.procedure(
                f"掃描參數設定:\n"
                f"移動腳本: {movement_script}\n"
                f"移動距離: {distance} nm\n"
                f"等待時間: {wait_time} s\n"
                f"重複次數: {repeat_count}"
            )
            
            # 記錄初始位置
            x, y = self.get_position()
            self.logger.procedure(f"起始位置: ({x}, {y})")
            
            result = super().auto_move_scan_area(
                movement_script, distance, wait_time, repeat_count
            )
            
            if result:
                self.logger.procedure("自動掃描完成")
            else:
                self.logger.procedure("自動掃描失敗")
            
            return result
            
        except Exception as e:
            self.logger.error(f"自動掃描錯誤: {str(e)}")
            return False
            
    @log_execution()
    def get_position(self):
        """獲取當前位置"""
        self.logger.procedure("讀取當前位置")
        return super().get_position()
    
    @log_execution()
    def scan_on(self):
        """開始掃描"""
        self.logger.procedure("啟動掃描")
        return super().scan_on()
    
    @log_execution()
    def scan_off(self):
        """停止掃描"""
        self.logger.procedure("停止掃描")
        return super().scan_off()
    
    @log_execution()
    def check_scan(self):
        """檢查掃描狀態"""
        try:
            response = super().check_scan()
            
            if isinstance(response, bytes):
                response_str = str(response, 'utf-8').strip()
                self.logger.procedure(f"掃描狀態: {response_str}")
            else:
                self.logger.procedure(f"掃描狀態: {response}")
                
            return response
            
        except Exception as e:
            self.logger.error(f"檢查掃描狀態錯誤: {str(e)}")
            return None