"""
STM 實驗日誌記錄系統
提供完整的日誌記錄功能，包含：
1. 基本的日誌記錄（調試訊息、錯誤等）
2. 函數執行追蹤（呼叫順序、執行時間等）
3. 可配置的時間戳記記錄

提供三種日誌記錄：
1. Function Tracking: 追蹤函數呼叫順序與堆疊
2. Debug: 記錄除錯訊息和重要狀態變更
3. Procedure: 記錄詳細的執行步驟和命令回應

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
import inspect
from pathlib import Path
from typing import Optional, Any, Callable, Dict, List, Set

class STMLogger:
    """STM 實驗日誌記錄器"""
    
    def __init__(self, debug_mode: bool = False):
        """
        初始化日誌記錄器
        
        Parameters
        ----------
        debug_mode : bool
            是否啟用除錯模式
        """
        self.debug_mode = debug_mode
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # 產生時間戳記
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 設定三種日誌檔案
        self.function_logger = self._setup_logger(
            "Function", 
            self.log_dir / f"function_{timestamp}.log",
            '%(asctime)s - %(message)s'
        )
        
        self.debug_logger = self._setup_logger(
            "Debug", 
            self.log_dir / f"debug_{timestamp}.log",
            '%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s'
        )
        
        self.procedure_logger = self._setup_logger(
            "Procedure", 
            self.log_dir / f"procedure_{timestamp}.log",
            '%(asctime)s - %(message)s'
        )
        
        # 函數追蹤相關
        self.function_stack: List[str] = []
        self.last_timestamp = time.time()
        self.tracking_active = True
        self._lock = threading.Lock()
        
        # 已追蹤的公開函數集合
        self.tracked_functions: Set[str] = set()
        
        # 啟動時間戳記執行緒
        self._start_timestamp_thread()
        
    def _setup_logger(self, name: str, log_file: Path, format_str: str) -> logging.Logger:
        """設定個別日誌記錄器"""
        logger = logging.getLogger(f"STM_{name}")
        logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        
        # 清除現有的處理器
        logger.handlers.clear()
        
        # 檔案處理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(format_str))
        logger.addHandler(file_handler)
        
        # 控制台處理器（僅用於除錯模式）
        if self.debug_mode:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(format_str))
            logger.addHandler(console_handler)
            
        return logger
        
    def _start_timestamp_thread(self):
        """啟動時間戳記執行緒"""
        self.timestamp_thread = threading.Thread(
            target=self._timestamp_loop,
            daemon=True
        )
        self.timestamp_thread.start()
        
    def _timestamp_loop(self):
        """時間戳記執行緒的主迴圈"""
        while self.tracking_active:
            current_time = time.time()
            if current_time - self.last_timestamp >= 5:  # 每5秒記錄一次
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                message = f"=== 時間戳記 {timestamp} ===\n"
                
                # 記錄當前函數堆疊
                with self._lock:
                    if self.function_stack:
                        message += f"目前執行堆疊: {' -> '.join(self.function_stack)}\n"
                
                # 寫入所有日誌
                self.function_logger.info(message)
                self.procedure_logger.info(message)
                
                self.last_timestamp = current_time
            time.sleep(0.1)
            
    def stop_tracking(self):
        """停止追蹤"""
        self.tracking_active = False
        if hasattr(self, 'timestamp_thread'):
            self.timestamp_thread.join(timeout=1.0)
            
    def function_enter(self, func_name: str, args: tuple = None, kwargs: dict = None):
        """記錄函數進入"""
        with self._lock:
            # 檢查是否為公開函數（不以底線開頭）
            if not func_name.startswith('_'):
                self.function_stack.append(func_name)
                self.function_logger.info(f"進入函數: {func_name}")
                if args is not None or kwargs is not None:
                    self.debug_logger.debug(
                        f"函數參數: args={args}, kwargs={kwargs}"
                    )
                
    def function_exit(self, func_name: str, result: Any = None):
        """記錄函數退出"""
        with self._lock:
            if not func_name.startswith('_'):
                if func_name in self.function_stack:
                    self.function_stack.remove(func_name)
                self.function_logger.info(f"離開函數: {func_name}")
                if result is not None:
                    self.debug_logger.debug(f"函數返回值: {result}")
                    
    def debug(self, message: str):
        """記錄除錯訊息"""
        self.debug_logger.debug(message)
        
    def error(self, message: str):
        """記錄錯誤訊息"""
        self.debug_logger.error(message)
        
    def procedure(self, message: str):
        """記錄執行步驟"""
        self.procedure_logger.info(message)

def log_execution(level: str = "DEBUG"):
    """函數執行日誌裝飾器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger()
            func_name = func.__name__
            
            # 記錄函數進入
            logger.function_enter(func_name, args, kwargs)
            
            try:
                # 執行原始函數
                result = func(*args, **kwargs)
                
                # 記錄執行成功
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

def log_procedure(message: str):
    """記錄執行步驟的裝飾器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger()
            logger.procedure(message.format(*args, **kwargs))
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 全域日誌記錄器
_stm_logger: Optional[STMLogger] = None

def get_logger() -> STMLogger:
    """獲取全域日誌記錄器"""
    global _stm_logger
    if _stm_logger is None:
        _stm_logger = STMLogger()
    return _stm_logger

def initialize_logger(debug_mode: bool = False) -> STMLogger:
    """初始化全域日誌記錄器"""
    global _stm_logger
    if _stm_logger is None:
        _stm_logger = STMLogger(debug_mode)
    return _stm_logger