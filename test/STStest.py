"""
改進版STS測試程式
使用 SXM 原生語法進行連接測試
"""

import webview
import time
from pathlib import Path
import sys

# 添加主程式目錄到系統路徑
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from modules import SXMPySpectro

class STSTestAPI:
    def __init__(self):
        """初始化時不立即建立控制器"""
        self.stm_controller = None
        print("STSTestAPI initialized")

    def ensure_controller(self) -> bool:
        """確保控制器存在且連接正常"""
        try:
            # 如果控制器不存在，建立新的控制器
            if self.stm_controller is None:
                print("Creating new STM controller...")
                self.stm_controller = SXMPySpectro.SXMSpectroControl(debug_mode=True)
                print("STM controller created")
                
                # 使用簡單的變數賦值來測試連接
                self.stm_controller.MySXM.SendWait("a := 0;")
                return True
                
            # 如果控制器存在，檢查DDE連接
            try:
                # 使用簡單的變數賦值來測試連接
                self.stm_controller.MySXM.SendWait("a := 0;")
                return True
            except:
                print("Connection lost, recreating controller...")
                self.stm_controller = None
                return self.ensure_controller()
                
        except Exception as e:
            print(f"Controller initialization error: {str(e)}")
            return False

    def execute_sts(self) -> bool:
        """執行STS測量"""
        try:
            print("\nPreparing for STS measurement...")
            
            # 確保控制器就緒
            if not self.ensure_controller():
                raise Exception("Failed to initialize controller")
                
            print("Starting STS measurement...")
            success = self.stm_controller.spectroscopy_start()
            
            if success:
                print("STS measurement started successfully")
            else:
                print("Failed to start STS measurement")
                
            return success
            
        except Exception as e:
            print(f"STS execution error: {str(e)}")
            return False

def main():
    try:
        # 建立API實例
        api = STSTestAPI()
        
        # 建立視窗並設定標題
        window = webview.create_window(
            'STS Test',
            str(Path(__file__).parent / 'STStestGUI.html'),
            js_api=api,
            width=400,
            height=200,
            text_select=True  # 允許選取文字，方便複製錯誤訊息
        )
        
        # 啟動GUI
        webview.start(debug=True)
        
    except Exception as e:
        print(f"Application error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()