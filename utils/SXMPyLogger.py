"""
STM 實驗日誌記錄系統
提供完整的日誌記錄功能，包含：
1. 基本的日誌記錄（調試訊息、錯誤等）
2. 函數執行追蹤（呼叫順序、執行時間等）
3. 可配置的時間戳記記錄

Author: Zi-Liang Yang
Date: 2024-01-24
"""

import os
import sys
import time
import logging
import functools
import threading
import datetime
from pathlib import Path
from typing import Optional, Any, Callable, Dict, List
from dataclasses import dataclass

@dataclass
class LogConfig:
    """日誌設定資料類別"""
    debug_mode: bool = False
    log_dir: str = "logs"
    function_tracking: bool = False
    tracking_interval: int = 5  # 函數追蹤的時間戳記間隔（秒）
    
class SXMLogger:
    """
    STM 實驗日誌記錄器
    負責管理所有日誌記錄相關功能
    """
    
    def __init__(self, config: LogConfig = None):
        """
        初始化日誌記錄器
        
        Parameters
        ----------
        config : LogConfig, optional
            日誌設定，若未提供則使用預設值
        """
        self.config = config or LogConfig()
        self.log_dir = Path(self.config.log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 建立日誌檔案
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.debug_log_file = self.log_dir / f"stm_debug_{timestamp}.log"
        self.func_log_file = self.log_dir / f"stm_function_{timestamp}.log"
        
        # 設定主要日誌記錄器
        self.debug_logger = self._setup_logger(
            "STM_Debug", 
            self.debug_log_file,
            '%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s'
        )
        
        # 設定函數追蹤記錄器
        self.func_logger = self._setup_logger(
            "STM_Function", 
            self.func_log_file,
            '%(asctime)s - %(message)s'
        )
        
        # 函數追蹤相關
        self.function_call_stack: List[str] = []
        self.last_timestamp = time.time()
        self.tracking_active = False
        self._lock = threading.Lock()
        
        if self.config.function_tracking:
            self._start_function_tracking()
    
    def _setup_logger(self, name: str, log_file: Path, format_str: str) -> logging.Logger:
        """
        設定個別的日誌記錄器
        
        Parameters
        ----------
        name : str
            記錄器名稱
        log_file : Path
            日誌檔案路徑
        format_str : str
            日誌格式
            
        Returns
        -------
        logging.Logger
            設定完成的記錄器
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG if self.config.debug_mode else logging.INFO)
        
        # 檔案處理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(format_str))
        logger.addHandler(file_handler)
        
        # 控制台處理器（僅用於除錯模式）
        if self.config.debug_mode:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(format_str))
            logger.addHandler(console_handler)
            
        return logger
    
    def _start_function_tracking(self):
        """啟動函數追蹤"""
        self.tracking_active = True
        self.tracking_thread = threading.Thread(
            target=self._tracking_loop,
            daemon=True
        )
        self.tracking_thread.start()
        
    def _tracking_loop(self):
        """函數追蹤的主迴圈"""
        while self.tracking_active:
            current_time = time.time()
            if current_time - self.last_timestamp >= self.config.tracking_interval:
                with self._lock:
                    if self.function_call_stack:
                        self.func_logger.info(
                            f"=== 時間戳記 {datetime.datetime.now()} ===\n"
                            f"目前執行堆疊: {' -> '.join(self.function_call_stack)}\n"
                        )
                self.last_timestamp = current_time
            time.sleep(0.1)
    
    def stop_tracking(self):
        """停止函數追蹤"""
        self.tracking_active = False
        if hasattr(self, 'tracking_thread'):
            self.tracking_thread.join()
    
    def debug(self, message: str):
        """記錄除錯訊息"""
        self.debug_logger.debug(message)
    
    def error(self, message: str):
        """記錄錯誤訊息"""
        self.debug_logger.error(message)
    
    def function_enter(self, func_name: str):
        """記錄函數進入"""
        if self.config.function_tracking:
            with self._lock:
                self.function_call_stack.append(func_name)
                self.func_logger.info(f"進入函數: {func_name}")
    
    def function_exit(self, func_name: str):
        """記錄函數退出"""
        if self.config.function_tracking:
            with self._lock:
                if func_name in self.function_call_stack:
                    self.function_call_stack.remove(func_name)
                self.func_logger.info(f"離開函數: {func_name}")

# 全域日誌記錄器實例
_stm_logger: Optional[SXMLogger] = None

def initialize_logger(config: LogConfig = None) -> SXMLogger:
    """
    初始化全域日誌記錄器
    
    Parameters
    ----------
    config : LogConfig, optional
        日誌設定
        
    Returns
    -------
    STMLogger
        初始化完成的日誌記錄器
    """
    global _stm_logger
    if _stm_logger is None:
        _stm_logger = SXMLogger(config)
    return _stm_logger

def get_logger() -> SXMLogger:
    """
    獲取全域日誌記錄器
    
    Returns
    -------
    STMLogger
        日誌記錄器實例
    """
    if _stm_logger is None:
        return initialize_logger()
    return _stm_logger

def log_execution(level: str = "DEBUG"):
    """
    函數執行日誌裝飾器
    
    Parameters
    ----------
    level : str
        日誌等級，可選 "DEBUG" 或 "ERROR"
        
    Returns
    -------
    Callable
        裝飾器函數
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger()
            func_name = func.__name__
            
            # 記錄函數進入
            logger.function_enter(func_name)
            logger.debug(f"開始執行函數: {func_name}")
            logger.debug(f"參數: args={args}, kwargs={kwargs}")
            
            try:
                # 執行原始函數
                result = func(*args, **kwargs)
                
                # 記錄成功執行
                logger.debug(f"函數 {func_name} 執行成功")
                return result
                
            except Exception as e:
                # 記錄錯誤
                logger.error(f"函數 {func_name} 執行失敗: {str(e)}")
                raise
            
            finally:
                # 記錄函數退出
                logger.function_exit(func_name)
                
        return wrapper
    return decorator