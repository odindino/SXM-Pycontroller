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
from modules import SXMRemote

# 其餘程式碼保持不變...

class STSTestAPI:
    def __init__(self):
        self.dde_client = None
        
    def initialize_dde(self):
        """初始化DDE連接"""
        try:
            if self.dde_client is None:
                self.dde_client = SXMRemote.DDEClient("SXM", "Remote")
            
            # 測試連接
            self.dde_client.SendWait("*OPC?")
            while self.dde_client.NotGotAnswer:
                SXMRemote.loop()
                
            return True
            
        except Exception as e:
            print(f"DDE initialization error: {str(e)}")
            return False

    def execute_sts(self) -> bool:
        """執行STS測量"""
        try:
            # 確保DDE連接
            if not self.initialize_dde():
                raise Exception("Failed to initialize DDE")
                
            print("Starting STS measurement...")
            
            # 發送STS開始命令
            self.dde_client.SendWait("SpectStart;")
            
            # 等待回應
            wait_count = 0
            while self.dde_client.NotGotAnswer and wait_count < 50:
                SXMRemote.loop()
                time.sleep(0.1)
                wait_count += 1
                
            if wait_count >= 50:
                raise Exception("STS response timeout")
                
            print("STS command sent successfully")
            return True
            
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