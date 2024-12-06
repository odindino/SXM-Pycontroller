"""
STM-SMU Controller Main Program
Launches the WebView GUI and initializes backend services.

Author: Zi-Liang Yang
Version: 1.0.0
Date: 2024-11-25
"""

import os
import signal
import webview
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
        # gui_path = os.path.join(base_dir, 'GUIs', 'SXMPycontroller-GUI.html')
        # gui_path = os.path.join(base_dir, 'SXMPyControllerVue', 'index.html')
        gui_path = 'http://localhost:5173/'

        # if not os.path.exists(gui_path):
        #     raise FileNotFoundError(f"GUI file not found at: {gui_path}")

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

    except KeyboardInterrupt:
        print("\n接收到中斷信號，正在關閉程式...")
        sys.exit(0)
    except Exception as e:
        print(f"程式錯誤: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
