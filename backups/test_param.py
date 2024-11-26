# test_param.py

from modules.SXMPycontroller import SXMController
from RemoteSXM import SXMRemote
import time

def test_raw_parameter_reading():
    """
    測試參數讀取的原始回應
    顯示所有中間步驟和原始回應
    """
    print("=== SXM 參數讀取原始測試 ===")
    
    try:
        # 建立連接
        MySXM = SXMRemote.DDEClient("SXM", "Remote")
        print("DDE連接已建立")
        
        # 測試參數
        param = 'X'  # 我們先專注測試X參數
        
        # 1. 最基本的讀取測試
        print(f"\n1. 基本測試 - 讀取 {param}")
        command = f"a:=GetScanPara('{param}');\r\n  writeln(a);"
        print(f"發送命令: {command}")
        
        MySXM.execute(command, 5000)
        
        # 等待並觀察回應
        for i in range(10):  # 等待1秒，每0.1秒檢查一次
            print(f"\n檢查 #{i+1}")
            print(f"NotGotAnswer: {MySXM.NotGotAnswer}")
            print(f"LastAnswer 型別: {type(MySXM.LastAnswer)}")
            print(f"LastAnswer 內容: {repr(MySXM.LastAnswer)}")
            time.sleep(0.1)
            
        # 2. 使用不同的命令格式測試
        print("\n2. 替代命令測試")
        
        # 測試不同的命令格式
        test_commands = [
            "writeln(GetScanPara('X'));",
            "a:=GetScanPara('X'); writeln(a);",
            "b:=0; b:=GetScanPara('X'); writeln(b);",
        ]
        
        for cmd in test_commands:
            print(f"\n嘗試命令: {cmd}")
            MySXM.execute(cmd, 5000)
            time.sleep(0.5)
            print(f"NotGotAnswer: {MySXM.NotGotAnswer}")
            print(f"LastAnswer 型別: {type(MySXM.LastAnswer)}")
            print(f"LastAnswer 內容: {repr(MySXM.LastAnswer)}")
            
        # 3. 測試簡單的系統命令
        print("\n3. 系統命令測試")
        MySXM.execute("writeln('test');", 1000)
        time.sleep(0.5)
        print(f"NotGotAnswer: {MySXM.NotGotAnswer}")
        print(f"LastAnswer 型別: {type(MySXM.LastAnswer)}")
        print(f"LastAnswer 內容: {repr(MySXM.LastAnswer)}")
            
    except Exception as e:
        print(f"\n發生錯誤: {str(e)}")
        import traceback
        print("\n完整錯誤訊息:")
        traceback.print_exc()

def test_parameter_control():
    """
    測試參數控制功能
    """
    print("=== SXM參數控制測試 ===")
    
    try:
        sxm = SXMController(debug_mode=True)
        
        # 1. 讀取當前位置
        print("\n1. 當前位置:")
        x, y = sxm.get_position()
        print(f"X: {x}, Y: {y}")
        
        # 2. 測試參數設定
        print("\n2. 設定掃描範圍:")
        if sxm.SetScanPara('Range', 200.0):
            print("範圍設定成功")
            new_range = sxm.GetScanPara('Range')
            print(f"新的掃描範圍: {new_range}")
            
        # 3. 設定完整掃描區域
        print("\n3. 設定掃描區域:")
        if sxm.setup_scan_area(
            center_x=0.0,
            center_y=0.0,
            scan_range=100.0,
            angle=0.0
        ):
            print("掃描區域設定成功")
            
        # 4. 讀取完整狀態
        print("\n4. 當前狀態:")
        state = sxm.get_current_state()
        for param, value in state.items():
            print(f"{param}: {value}")
            
    except Exception as e:
        print(f"測試過程發生錯誤: {str(e)}")

def test_parameter_setting():
    """
    詳細測試參數設定功能
    """
    print("=== 參數設定測試 ===")
    
    try:
        sxm = SXMController(debug_mode=True)
        
        # 測試參數
        test_cases = [
            ('Range', 200.0),
            ('X', 50.0),
            ('Y', 50.0),
            ('Angle', 45.0)
        ]
        
        for param, value in test_cases:
            print(f"\n測試設定 {param} = {value}")
            print("-" * 50)
            
            # 讀取原始值
            original = sxm.GetScanPara(param)
            print(f"原始值: {original}")
            
            # 設定新值
            if sxm.SetScanPara(param, value):
                print(f"參數設定命令執行成功")
                
                # 驗證設定
                if sxm.verify_parameter_change(param, value):
                    print("參數設定已驗證")
                else:
                    print("參數設定驗證失敗")
            else:
                print("參數設定失敗")
                
            # 顯示最終值
            final = sxm.GetScanPara(param)
            print(f"最終值: {final}")
            
    except Exception as e:
        print(f"測試過程發生錯誤: {str(e)}")

if __name__ == "__main__":
    # test_raw_parameter_reading()
    # test_parameter_control()
    test_parameter_setting()