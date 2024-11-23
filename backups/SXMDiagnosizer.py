import time
from RemoteSXM import SXMRemote
import win32ui
import win32gui
import win32process
import win32con
from typing import Optional, Tuple, List

class SXMDiagsizer:
    """SXM系統診斷工具"""
    def __init__(self, sxm_controller):
        self.controller = sxm_controller
        self.MySXM = sxm_controller.MySXM
        self.diagnostic_results = []
        
    def find_sxm_window(self) -> Tuple[bool, Optional[int]]:
        """
        尋找SXM程式視窗
        
        Returns:
            Tuple[bool, Optional[int]]: (是否找到, 視窗handle)
        """
        def enum_window_callback(hwnd, result):
            window_text = win32gui.GetWindowText(hwnd)
            if "SXM" in window_text and win32gui.IsWindowVisible(hwnd):
                result.append(hwnd)
                
        windows = []
        win32gui.EnumWindows(enum_window_callback, windows)
        
        if windows:
            return True, windows[0]
        return False, None
        
    def check_sxm_process(self) -> dict:
        """
        檢查SXM程序狀態
        
        Returns:
            dict: 包含程序狀態信息
        """
        result = {
            'running': False,
            'window_found': False,
            'responding': False,
            'details': ''
        }
        
        try:
            # 檢查視窗
            window_found, hwnd = self.find_sxm_window()
            result['window_found'] = window_found
            
            if window_found:
                # 檢查程序響應狀態
                result['responding'] = win32gui.SendMessageTimeout(
                    hwnd, 
                    win32con.WM_NULL, 
                    0, 0, 
                    win32con.SMTO_ABORTIFHUNG, 
                    1000
                ) is not None
                
                # 獲取程序ID
                _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                result['running'] = process_id > 0
                result['details'] = f"進程ID: {process_id}"
                
        except Exception as e:
            result['details'] = f"檢查過程發生錯誤: {str(e)}"
            
        return result
        
    def test_dde_connection(self) -> Tuple[bool, str]:
        """
        測試DDE連接狀態
        
        Returns:
            Tuple[bool, str]: (測試結果, 詳細訊息)
        """
        print("\n=== DDE連接測試 ===")
        
        # 檢查SXM程序狀態
        process_status = self.check_sxm_process()
        if not process_status['running']:
            return False, "SXM程序未運行"
            
        if not process_status['responding']:
            return False, "SXM程序無響應"
            
        try:
            # 測試基本DDE命令
            print("測試DDE基本命令...")
            self.MySXM.execute("ClrScr;", 5000)
            time.sleep(0.5)
            
            if self.MySXM.NotGotAnswer:
                return False, "DDE命令無回應"
                
            return True, "DDE連接正常"
            
        except Exception as e:
            return False, f"DDE測試異常: {str(e)}"
            
    def test_parameter_access(self, parameter: str) -> Tuple[bool, str, Optional[str]]:
        """
        測試參數讀取
        
        Args:
            parameter: 要測試的參數名稱
            
        Returns:
            Tuple[bool, str, Optional[str]]: (成功與否, 錯誤訊息, 參數值)
        """
        print(f"\n測試參數: {parameter}")
        
        try:
            command = f"a:=GetScanPara('{parameter}');\r\n  writeln(a);"
            self.MySXM.execute(command, 5000)
            
            # 等待回應
            wait_count = 0
            while self.MySXM.NotGotAnswer and wait_count < 50:
                SXMRemote.loop()
                time.sleep(0.1)
                wait_count += 1
                print(f"等待回應... {wait_count}/50")
                
            if self.MySXM.NotGotAnswer:
                return False, "參數讀取超時", None
                
            response = self.MySXM.LastAnswer
            if response is None:
                return False, "無回應", None
                
            if isinstance(response, bytes):
                value = str(response, 'utf-8').strip()
                return True, "成功", value
                
            return True, "成功", str(response)
            
        except Exception as e:
            return False, f"參數存取錯誤: {str(e)}", None
            
    def run_diagnostics(self) -> List[dict]:
        """
        執行完整診斷
        
        Returns:
            List[dict]: 診斷結果列表
        """
        results = []
        
        # 1. 檢查SXM程序
        process_status = self.check_sxm_process()
        results.append({
            'test': 'SXM程序檢查',
            'success': process_status['running'] and process_status['responding'],
            'details': process_status
        })
        
        # 如果程序檢查失敗，直接返回
        if not (process_status['running'] and process_status['responding']):
            return results
            
        # 2. 測試DDE連接
        dde_success, dde_message = self.test_dde_connection()
        results.append({
            'test': 'DDE連接測試',
            'success': dde_success,
            'details': dde_message
        })
        
        # 如果DDE連接失敗，直接返回
        if not dde_success:
            return results
            
        # 3. 測試基本參數
        test_parameters = ['X', 'Y', 'Range', 'Scan', 'Angle']
        for param in test_parameters:
            success, message, value = self.test_parameter_access(param)
            results.append({
                'test': f'參數測試: {param}',
                'success': success,
                'details': {
                    'message': message,
                    'value': value
                }
            })
            
        return results

def run_diagnostics(controller):
    """
    執行診斷的便捷函數
    
    Args:
        controller: SXM控制器實例
    """
    diagsizer = SXMDiagsizer(controller)
    results = diagsizer.run_diagnostics()
    
    print("\n=== 診斷結果摘要 ===")
    for result in results:
        status = "✓" if result['success'] else "✗"
        print(f"{status} {result['test']}")
        if isinstance(result['details'], dict):
            for key, value in result['details'].items():
                print(f"  - {key}: {value}")
        else:
            print(f"  - {result['details']}")
            
    return results