"""
STS測試程式
用於測試DDE通訊和STS功能
"""

import time
from modules import SXMRemote
from modules.SXMPySpectro import SXMSpectroControl

def test_dde_sts():
    """測試直接使用DDE執行STS"""
    try:
        print("\n=== 測試直接DDE執行STS ===")
        print("正在連接SXM...")
        MySXM = SXMRemote.DDEClient("SXM", "Remote")
        print("連接成功")

        time.sleep(1)

        print("\n開始執行STS...")
        MySXM.SendWait("SpectStart;")
        
        while MySXM.NotGotAnswer:
            SXMRemote.loop()
        
        response = MySXM.LastAnswer
        print(f"STS回應: {response}")
        
        return True

    except Exception as e:
        print(f"DDE執行STS錯誤: {str(e)}")
        return False

def test_spectro_sts():
    """測試使用SXMSpectroControl執行STS"""
    try:
        print("\n=== 測試SXMSpectroControl執行STS ===")
        print("初始化SXMSpectroControl...")
        spectro = SXMSpectroControl(debug_mode=True)
        
        print("\n開始執行STS...")
        success = spectro.spectroscopy_start()
        
        print(f"STS執行{'成功' if success else '失敗'}")
        return success

    except Exception as e:
        print(f"SXMSpectroControl執行STS錯誤: {str(e)}")
        return False

def run_all_tests():
    """執行所有測試"""
    results = []
    
    # 測試1: DDE直接執行
    print("\n開始DDE直接執行測試...")
    dde_result = test_dde_sts()
    results.append(("DDE直接執行", dde_result))
    
    # 測試之間稍微暫停
    time.sleep(2)
    
    # 測試2: SXMSpectroControl執行
    print("\n開始SXMSpectroControl測試...")
    spectro_result = test_spectro_sts()
    results.append(("SXMSpectroControl執行", spectro_result))
    
    # 顯示測試結果摘要
    print("\n=== 測試結果摘要 ===")
    for test_name, result in results:
        print(f"{test_name}: {'成功' if result else '失敗'}")
    
    return all(result for _, result in results)

if __name__ == "__main__":
    # 執行所有測試
    try:
        overall_success = run_all_tests()
        print(f"\n整體測試{'成功' if overall_success else '失敗'}")
    except Exception as e:
        print(f"\n測試過程發生錯誤: {str(e)}")
    finally:
        # 等待使用者按鍵結束
        input("\n按Enter結束程式...")