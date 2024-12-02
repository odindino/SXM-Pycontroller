# test_sxm_pascal.py

from modules.SXMPycontroller import SXMController
import time

# def test_pascal_syntax():
#     """
#     根據SXM的Pascal語法規範測試命令
#     參考Language Description.pdf的語法要求
#     """
#     print("=== SXM Pascal語法測試 ===")
    
#     try:
#         sxm = SXMController()
#         MySXM = sxm.MySXM
        
#         # 測試不同的Pascal語法版本
#         print("\n1. 測試變數賦值和讀取")
#         test_commands = [
#             # 單行變數賦值
#             "a := GetScanPara('X'); Writeln(a);",
            
#             # Label定義和變數賦值
#             "LABEL test;\nbegin\na := GetScanPara('X');\nWriteln(a);\nend.",
            
#             # 直接讀取並輸出
#             "Writeln(GetScanPara('X'));",
            
#             # 完整程式結構
#             "LABEL start;\nbegin\nWriteln(GetScanPara('X'));\nend.",
            
#             # 使用數值變數
#             "a := 0.0;\na := GetScanPara('X');\nWriteln(a);",
#         ]
        
#         for i, cmd in enumerate(test_commands):
#             print(f"\n測試命令 #{i+1}:")
#             print(f"命令內容:\n{cmd}")
#             MySXM.execute(cmd, 5000)
#             time.sleep(0.5)
            
#             print(f"NotGotAnswer: {MySXM.NotGotAnswer}")
#             print(f"LastAnswer型別: {type(MySXM.LastAnswer)}")
#             if MySXM.LastAnswer:
#                 if isinstance(MySXM.LastAnswer, bytes):
#                     response = MySXM.LastAnswer.decode('utf-8').split('\r\n')
#                     print("回應行:")
#                     for line in response:
#                         print(f"  {line}")
#                 else:
#                     print(f"回應內容: {repr(MySXM.LastAnswer)}")
            
#             time.sleep(0.5)  # 等待系統處理
            
#         # 測試其他參數
#         print("\n2. 使用最佳語法測試其他參數")
#         test_params = ['Y', 'Range', 'Scan', 'Angle']
        
#         # 使用測試中效果最好的命令格式
#         best_format = "a := 0.0;\na := GetScanPara('%s');\nWriteln(a);"
        
#         for param in test_params:
#             print(f"\n讀取參數: {param}")
#             cmd = best_format % param
#             print(f"命令內容:\n{cmd}")
            
#             MySXM.execute(cmd, 5000)
#             time.sleep(0.5)
            
#             if MySXM.LastAnswer:
#                 if isinstance(MySXM.LastAnswer, bytes):
#                     response = MySXM.LastAnswer.decode('utf-8').split('\r\n')
#                     print("回應行:")
#                     for line in response:
#                         print(f"  {line}")
                        
#     except Exception as e:
#         print(f"測試過程發生錯誤: {str(e)}")
#         import traceback
#         print("\n完整錯誤訊息:")
#         traceback.print_exc()

# if __name__ == "__main__":
#     test_pascal_syntax()
# def verify_parameters():
#     """
#     驗證修改後的GetScanPara功能
#     """
#     print("=== 參數讀取驗證 ===")
    
#     try:
#         sxm = SXMController()
#         sxm.debug_mode = True  # 開啟除錯模式
        
#         # 測試所有基本參數
#         test_params = [
#             'X', 'Y', 'Range', 'Scan', 'Angle'
#         ]
        
#         for param in test_params:
#             print(f"\n讀取參數: {param}")
#             value = sxm.GetScanPara(param)
#             print(f"值: {value}")
            
#     except Exception as e:
#         print(f"驗證過程發生錯誤: {str(e)}")

# if __name__ == "__main__":
#     verify_parameters()
def test_sxm_controller():
    """
    測試已驗證的SXM控制器
    """
    try:
        print("初始化SXM控制器...")
        sxm = SXMController()
        
        # 開啟除錯模式
        sxm.debug_mode = True
        
        # 讀取並顯示當前狀態
        results = sxm.print_current_state()
        
        # 顯示總結
        print("\n=== 測試結果總結 ===")
        success_count = sum(1 for v in results.values() if v is not None)
        print(f"成功讀取參數: {success_count}/{len(results)}")
        
        if success_count == 0:
            print("\n可能的問題:")
            print("1. DDE連接可能不穩定")
            print("2. SXM軟體可能需要重新啟動")
            print("3. 命令格式可能需要調整")
            
    except Exception as e:
        print(f"測試過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sxm_controller()