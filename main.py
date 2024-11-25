"""
STM-SMU Controller Main Program
Launches the WebView GUI and initializes backend services.

Author: Zi-Liang Yang
Version: 1.0.0
Date: 2024-11-25
"""

import os
import webview
from pathlib import Path
from api import SMUControlAPI


def main():
    try:
        # 獲取GUI HTML檔案路徑
        base_dir = Path(__file__).parent
        gui_path = os.path.join(base_dir, 'GUIs', 'SXMPycontroller.html')

        if not os.path.exists(gui_path):
            raise FileNotFoundError(f"GUI file not found at: {gui_path}")

        # 初始化API
        api = SMUControlAPI()

        # 創建視窗
        window = webview.create_window(
            title='STM-SMU Controller',
            url=gui_path,
            js_api=api,
            width=1200,
            height=800,
            resizable=True
        )

        # 啟動GUI
        webview.start(debug=True)

    except Exception as e:
        print(f"啟動錯誤: {str(e)}")


if __name__ == '__main__':
    main()
