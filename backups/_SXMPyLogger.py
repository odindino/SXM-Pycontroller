import logging
import datetime
from pathlib import Path

class SXMLogger:
    """日誌處理類別"""
    
    def __init__(self, debug_mode=False):
        self.logger = logging.getLogger('SXM')
        self.debug_mode = debug_mode
        self.setup_logger()
        
    def setup_logger(self):
        """設定日誌處理器"""
        # 設定日誌格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 設定檔案處理器
        log_dir = Path('./logs')
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f'sxm_{datetime.datetime.now():%Y%m%d_%H%M%S}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        
        # 設定控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # 設定日誌等級
        self.logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        
        # 添加處理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def log_scan_event(self, event_type, details=None):
        """記錄掃描事件"""
        message = f"Scan event: {event_type}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
        
    def log_spectro_event(self, event_type, position=None, details=None):
        """記錄光譜測量事件"""
        message = f"Spectroscopy event: {event_type}"
        if position:
            message += f" at position ({position[0]}, {position[1]})"
        if details:
            message += f" - {details}"
        self.logger.info(message)
        
    def log_error(self, error_type, error_message):
        """記錄錯誤"""
        self.logger.error(f"{error_type}: {error_message}")
        
    def log_debug(self, message):
        """記錄除錯信息"""
        if self.debug_mode:
            self.logger.debug(message)