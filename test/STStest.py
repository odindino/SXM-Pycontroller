"""
簡化版STS測試程式
只測試基本的DDE通訊和STS啟動功能
"""

import webview
import time
from pathlib import Path
import sys

# 添加主程式目錄到系統路徑
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# 現在可以直接從 modules 導入
from modules import SXMPySpectro

class STSTestAPI:
    def __init__(self):
        self.stm_controller = SXMPySpectro.SXMSpectroControl(debug_mode=True)

    def execute_sts(self) -> bool:
        """執行STS測量"""
        try:
            return self.stm_controller.spectroscopy_start()
            
        except Exception as e:
            print(f"STS execution error: {str(e)}")
            return False

def main():
    try:
        # 建立API實例
        api = STSTestAPI()
        
        # 建立視窗
        window = webview.create_window(
            'STS Test',
            str(Path(__file__).parent / 'STStestGUI.html'),
            js_api=api,
            width=400,
            height=200
        )
        
        # 啟動GUI
        webview.start(debug=True)
        
    except Exception as e:
        print(f"Application error: {str(e)}")

if __name__ == '__main__':
    main()