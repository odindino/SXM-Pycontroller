"""
通用函式追蹤與日誌記錄系統
提供兩個主要功能：
1. 函式追蹤：記錄程式執行過程中重要函式的呼叫順序
2. 執行紀錄：將所有 print 內容保存到日誌檔案

author: Zi-Liang Yang
version: 1.0.0
date: 2024-11-24
"""

import os
import sys
import time
import logging
import threading
import datetime
from pathlib import Path
from typing import Optional, Set, TextIO
from functools import wraps

class Logger:
    """
    通用函式追蹤與日誌記錄器
    可用於追蹤任何Python程式的函式執行順序
    """
    
    def __init__(self, 
                 log_dir: str = "logs",
                 tracking_interval: int = 5,
                 enable_print_log: bool = True):
        """
        初始化日誌記錄器
        
        Parameters
        ----------
        log_dir : str
            日誌檔案存放目錄
        tracking_interval : int
            函式追蹤的時間戳記間隔（秒）
        enable_print_log : bool
            是否記錄 print 輸出內容
        """
        # 建立日誌目錄
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 產生時間戳記
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 設定日誌記錄器
        self.func_logger = self._setup_logger(
            "function", 
            f"function_{self.timestamp}.log"
        )
        
        # Print 輸出記錄器
        self.print_logger = None
        if enable_print_log:
            self.print_logger = self._setup_logger(
                "print", 
                f"print_{self.timestamp}.log"
            )
            self._setup_print_redirect()
        
        # 函式追蹤設定
        self.tracking_interval = tracking_interval
        self.active_functions = set()  # 目前執行中的函式
        self.last_log_time = time.time()
        self.is_tracking = True
        
        # 啟動時間戳記執行緒
        self._start_tracking_thread()
        
    def _setup_logger(self, name: str, filename: str) -> logging.Logger:
        """設定個別日誌記錄器"""
        logger = logging.getLogger(f"{name}_{self.timestamp}")
        logger.setLevel(logging.INFO)
        
        # 清除現有的處理器
        logger.handlers = []
        
        # 檔案處理器
        handler = logging.FileHandler(
            self.log_dir / filename,
            encoding='utf-8'
        )
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(message)s')
        )
        logger.addHandler(handler)
        
        return logger
        
    def _setup_print_redirect(self):
        """設定 print 輸出重導向"""
        # 保存原始的 stdout
        self.original_stdout = sys.stdout
        
        # 建立重導向器
        class PrintRedirector:
            def __init__(self, logger, original_stdout):
                self.logger = logger
                self.original_stdout = original_stdout
                
            def write(self, message):
                # 同時輸出到原始 stdout 和日誌
                self.original_stdout.write(message)
                if message.strip():
                    self.logger.info(message.rstrip())
                    
            def flush(self):
                self.original_stdout.flush()
        
        # 重導向 stdout
        sys.stdout = PrintRedirector(self.print_logger, self.original_stdout)
        
    def _start_tracking_thread(self):
        """啟動函式追蹤執行緒"""
        def tracking_loop():
            while self.is_tracking:
                current_time = time.time()
                if current_time - self.last_log_time >= self.tracking_interval:
                    self._log_timestamp()
                    self.last_log_time = current_time
                time.sleep(0.1)
        
        self.tracking_thread = threading.Thread(
            target=tracking_loop,
            daemon=True
        )
        self.tracking_thread.start()
        
    def _log_timestamp(self):
        """記錄時間戳記和當前函式堆疊"""
        if self.active_functions:
            self.func_logger.info(
                f"=== 時間戳記 {datetime.datetime.now()} ===\n"
                f"目前執行函式：{' -> '.join(self.active_functions)}\n"
            )
            
    def log_function_enter(self, func_name: str):
        """記錄函式進入"""
        self.active_functions.add(func_name)
        self.func_logger.info(f"進入函式：{func_name}")
        
    def log_function_exit(self, func_name: str):
        """記錄函式退出"""
        if func_name in self.active_functions:
            self.active_functions.remove(func_name)
        self.func_logger.info(f"離開函式：{func_name}")
        
    def stop(self):
        """停止日誌記錄"""
        self.is_tracking = False
        if hasattr(self, 'tracking_thread'):
            self.tracking_thread.join(timeout=1.0)
            
        # 恢復原始的 stdout
        if hasattr(self, 'original_stdout'):
            sys.stdout = self.original_stdout

# 全域日誌記錄器
_global_logger: Optional[Logger] = None

def get_logger() -> Logger:
    """獲取全域日誌記錄器"""
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger()
    return _global_logger

def track_function(func):
    """函式追蹤裝飾器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 檢查是否為我們想要追蹤的函式
        # 排除私有方法（以底線開頭）和內建函式
        if not func.__name__.startswith('_') and \
           not func.__module__.startswith('_'):
            logger = get_logger()
            logger.log_function_enter(func.__name__)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                logger.log_function_exit(func.__name__)
        else:
            return func(*args, **kwargs)
    return wrapper