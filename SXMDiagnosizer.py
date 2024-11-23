import time
from RemoteSXM import SXMRemote

class SXMDiagnostics:
    """SXM診斷工具類別"""
    
    def __init__(self, sxm_controller):
        self.controller = sxm_controller
        self.MySXM = sxm_controller.MySXM
        self.debug_log = []
        
    def test_dde_connection(self):
        """測試DDE連接狀態"""
        try:
            print("\n=== 測試DDE連接 ===")
            
            # 檢查DDE客戶端是否已初始化
            if not self.MySXM:
                print("錯誤: DDE客戶端未初始化")
                return False
                
            # 嘗試執行簡單命令
            print("正在測試DDE基本命令...")
            self.MySXM.execute("ClrScr;", 5000)
            time.sleep(0.5)
            
            if self.MySXM.NotGotAnswer:
                print("警告: 未收到命令回應")
                return False
                
            print("DDE基本連接測試通過")
            return True
            
        except Exception as e:
            print(f"DDE連接測試失敗: {str(e)}")
            return False
            
    def test_parameter_reading(self, param_name, param_type):
        """測試特定參數讀取"""
        print(f"\n=== 測試參數讀取: {param_name} ===")
        
        try:
            # 構建測試命令
            command = f"a:=GetScanPara('{param_name}');\r\n  writeln(a);"
            print(f"執行命令: {command}")
            
            # 執行命令
            self.MySXM.execute(command, 5000)
            
            # 等待並檢查回應
            wait_count = 0
            while self.MySXM.NotGotAnswer and wait_count < 50:
                SXMRemote.loop()
                time.sleep(0.1)
                wait_count += 1
                print(f"等待回應... ({wait_count}/50)")
                
            if wait_count >= 50:
                print("錯誤: 命令超時")
                return False
                
            # 檢查回應
            response = self.MySXM.LastAnswer
            print(f"原始回應: {response}")
            
            if response is None:
                print("錯誤: 沒有收到回應")
                return False
                
            # 分析回應
            if isinstance(response, bytes):
                response_str = str(response, 'utf-8').strip()
                print(f"解碼回應: {response_str}")
                
                try:
                    # 嘗試轉換為指定類型
                    if param_type == bool:
                        value = bool(int(float(response_str)))
                    elif param_type == int:
                        value = int(float(response_str))
                    elif param_type == float:
                        value = float(response_str)
                    print(f"轉換後的值: {value} (類型: {type(value)})")
                    return True
                except ValueError as ve:
                    print(f"值轉換失敗: {str(ve)}")
                    return False
                    
        except Exception as e:
            print(f"參數讀取測試失敗: {str(e)}")
            return False
            
    def run_full_diagnosis(self):
        """執行完整診斷"""
        print("開始SXM診斷程序...")
        
        # 測試DDE連接
        if not self.test_dde_connection():
            print("DDE連接測試失敗，終止診斷")
            return False
            
        # 測試基本參數讀取
        test_params = [
            ('X', float),
            ('Y', float),
            ('Range', float),
            ('Scan', bool),
            ('Angle', float)
        ]
        
        results = []
        for param_name, param_type in test_params:
            result = self.test_parameter_reading(param_name, param_type)
            results.append((param_name, result))
            time.sleep(0.5)  # 避免發送命令太快
            
        # 顯示診斷結果
        print("\n=== 診斷結果摘要 ===")
        for param_name, result in results:
            status = "通過" if result else "失敗"
            print(f"參數 {param_name}: {status}")
            
        return all(result for _, result in results)

def create_diagnostics(controller):
    """建立診斷工具實例"""
    return SXMDiagnostics(controller)