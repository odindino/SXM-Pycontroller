"""
簡單的STS測試程式
使用延遲初始化DDE連接的方式
"""

import webview
import time
from pathlib import Path
import sys
import threading

# 添加父目錄到系統路徑
sys.path.append(str(Path(__file__).parent.parent))

from modules import SXMRemote
from modules.SXMPySpectro import SXMSpectroControl

class STSTestAPI:
    def __init__(self):
        self.spectro = None
        self.dde_client = None
        self.initialized = False
        self.init_lock = threading.Lock()

    def check_dde_connection(self) -> bool:
        """檢查DDE連接是否正常"""
        try:
            if not self.dde_client:
                return False
                
            # 嘗試發送簡單命令測試連接
            self.dde_client.SendWait("*OPC?")
            while self.dde_client.NotGotAnswer:
                SXMRemote.loop()
            return True
            
        except Exception as e:
            print(f"DDE connection check failed: {str(e)}")
            return False

    def initialize_connection(self) -> bool:
        """初始化DDE連接"""
        if self.initialized and self.check_dde_connection():
            return True
            
        with self.init_lock:
            try:
                print("Initializing DDE connection...")
                
                # 如果已存在連接，先清理
                if self.dde_client:
                    try:
                        del self.dde_client
                    except:
                        pass
                
                # 建立新連接
                self.dde_client = SXMRemote.DDEClient("SXM", "Remote")
                
                # 測試連接
                if not self.check_dde_connection():
                    raise Exception("Failed to verify DDE connection")
                    
                print("DDE connection established")
                
                # 初始化SXMSpectroControl
                self.spectro = SXMSpectroControl(debug_mode=True)
                print("SXMSpectroControl initialized")
                
                self.initialized = True
                return True
                
            except Exception as e:
                print(f"Initialization error: {str(e)}")
                self.initialized = False
                return False

    def execute_sts(self) -> bool:
        """執行單點STS測量"""
        try:
            # 確保連接正常
            if not self.initialized or not self.check_dde_connection():
                if not self.initialize_connection():
                    raise Exception("Failed to establish DDE connection")
            
            print("\nStarting STS measurement...")
            
            # 發送STS命令
            self.dde_client.SendWait("SpectStart;")
            
            # 等待回應
            timeout = 50  # 5秒超時
            while self.dde_client.NotGotAnswer and timeout > 0:
                SXMRemote.loop()
                time.sleep(0.1)
                timeout -= 1
                
            if timeout <= 0:
                raise Exception("STS response timeout")
            
            response = self.dde_client.LastAnswer
            print(f"STS response: {response}")
            
            # 執行完成後檢查連接狀態
            if not self.check_dde_connection():
                print("Warning: DDE connection lost after execution")
                self.initialized = False
            
            return True
            
        except Exception as e:
            print(f"STS execution error: {str(e)}")
            self.initialized = False
            raise Exception(f"STS failed: {str(e)}")

    def __del__(self):
        """清理資源"""
        try:
            if self.dde_client:
                del self.dde_client
        except:
            pass

def create_message_loop():
    """創建Windows消息循環"""
    import pythoncom
    pythoncom.PumpMessages()

def main():
    try:
        # 建立API實例
        api = STSTestAPI()
        
        # 啟動Windows消息循環
        message_loop_thread = threading.Thread(target=create_message_loop, daemon=True)
        message_loop_thread.start()
        
        # 取得HTML檔案路徑
        gui_path = str(Path(__file__).parent / 'STStestGUI.html')
        
        # 建立視窗
        window = webview.create_window(
            'STS Test',
            gui_path,
            js_api=api,
            width=400,
            height=300
        )
        
        # 啟動GUI
        webview.start(debug=True)
        
    except Exception as e:
        print(f"Application error: {str(e)}")

if __name__ == '__main__':
    main()