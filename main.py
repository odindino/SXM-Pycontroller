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
import sys


def signal_handler(sig, frame):
    """處理Ctrl+C信號"""
    print("\n正在關閉程式...")
    sys.exit(0)


def on_closed():
    """視窗關閉時的處理"""
    print("視窗已關閉，正在清理資源...")
    sys.exit(0)


def main():
    try:
        # 獲取GUI HTML檔案路徑
        base_dir = Path(__file__).parent
        gui_path = os.path.join(base_dir, 'GUIs', 'SXMPycontroller-GUI.html')

        if not os.path.exists(gui_path):
            raise FileNotFoundError(f"GUI file not found at: {gui_path}")

        # 設定Ctrl+C信號處理
        signal.signal(signal.SIGINT, signal_handler)

        # 初始化API
        api = SMUControlAPI()

        # 創建視窗
        window = webview.create_window(
            title='STM-SMU Controller',
            url=gui_path,
            js_api=api,
            width=1280,
            height=800,
            resizable=True
        )

        # 設定視窗關閉時的處理
        window.events.closed += on_closed

        # 啟動GUI
        webview.start(debug=True)


def main():
    """程式進入點"""
    app = ApplicationManager()
    app.run()


if __name__ == '__main__':
    main()
