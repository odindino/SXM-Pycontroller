from RemoteSXM import SXMRemote
import time

def test_basic_commands():
    """
    測試SXMRemote的基本功能
    """
    print("=== SXMRemote基本功能測試 ===")
    
    # 1. 建立連接
    print("\n1. 建立DDE連接")
    try:
        MySXM = SXMRemote.DDEClient("SXM", "Remote")
        print("DDE客戶端建立成功")
    except Exception as e:
        print(f"DDE連接失敗: {str(e)}")
        return
        
    # 2. 測試最簡單的命令
    print("\n2. 測試基本命令")
    try:
        # 清除螢幕命令
        print("測試 ClrScr 命令...")
        MySXM.execute("ClrScr;", 1000)
        time.sleep(0.5)
        print(f"命令執行狀態: {'無回應' if MySXM.NotGotAnswer else '有回應'}")
        print(f"最後回應: {MySXM.LastAnswer}")
        
        # 讀取掃描參數
        print("\n測試讀取掃描參數...")
        MySXM.execute("writeln(GetScanPara('X'));", 1000)
        time.sleep(0.5)
        print(f"命令執行狀態: {'無回應' if MySXM.NotGotAnswer else '有回應'}")
        print(f"最後回應: {MySXM.LastAnswer}")
        
    except Exception as e:
        print(f"命令執行失敗: {str(e)}")
        
    # 3. 測試簡單參數設定
    print("\n3. 測試參數設定")
    try:
        MySXM.SendWait("ScanPara('Range', 100);")
        print("Range參數設定完成")
    except Exception as e:
        print(f"參數設定失敗: {str(e)}")

if __name__ == "__main__":
    test_basic_commands()