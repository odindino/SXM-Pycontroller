"""
STM-SMU Controller Main Program
啟動GUI並管理系統生命週期

Author: Zi-Liang Yang
Version: 1.0.0
Date: 2024-11-26
"""

import os
import sys
import signal
import webview
import logging
from pathlib import Path
from api import SMUControlAPI
from contextlib import contextmanager

class ApplicationManager:
    """應用程式管理器"""
    
    def __init__(self):
        self.api = None
        self.window = None
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """設定日誌記錄"""
        logger = logging.getLogger("STM-SMU")
        logger.setLevel(logging.DEBUG)
        
        # 檔案處理器
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / "app.log",
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)
        
        # 控制台處理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(levelname)s: %(message)s'
        ))
        logger.addHandler(console_handler)
        
        return logger
        
    def signal_handler(self, sig, frame):
        """處理系統信號"""
        self.logger.info("\n接收到中斷信號，正在關閉程式...")
        self.cleanup()
        sys.exit(0)
        
    def on_closed(self):
        """視窗關閉處理"""
        self.logger.info("視窗已關閉，正在清理資源...")
        self.cleanup()
        
    def cleanup(self):
        """清理系統資源"""
        try:
            if self.api:
                self.api.cleanup()
            self.logger.info("系統資源已清理完成")
        except Exception as e:
            self.logger.error(f"清理資源時發生錯誤: {str(e)}")
            
    @contextmanager
    def error_handling(self):
        """錯誤處理上下文管理器"""
        try:
            yield
        except Exception as e:
            self.logger.error(f"程式錯誤: {str(e)}")
            sys.exit(1)
            
    def run(self):
        """啟動應用程式"""
        with self.error_handling():
            # 設定信號處理
            signal.signal(signal.SIGINT, self.signal_handler)
            
            # 獲取GUI路徑
            base_dir = Path(__file__).parent
            gui_path = base_dir / 'GUIs' / 'SXMPycontroller-GUI.html'
            
            if not gui_path.exists():
                raise FileNotFoundError(f"找不到GUI檔案: {gui_path}")
                
            # 初始化API
            self.api = SMUControlAPI()
            
            # 創建視窗
            self.window = webview.create_window(
                title='STM-SMU Controller',
                url=str(gui_path),
                js_api=self.api,
                width=1200,
                height=800,
                resizable=True,
                text_select=True
            )
            
            # 設定視窗關閉處理
            self.window.events.closed += self.on_closed
            
            # 啟動GUI
            self.logger.info("正在啟動應用程式...")
            webview.start(debug=True)

def main():
    """程式進入點"""
    app = ApplicationManager()
    app.run()

if __name__ == '__main__':
    main()