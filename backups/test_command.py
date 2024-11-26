from modules.SXMPycontroller import SXMController
import time

def test_command_formats():
    """
    測試不同命令格式的效果
    """
    print("=== SXM 命令格式測試 ===")
    
    try:
        sxm = SXMController()
        MySXM = sxm.MySXM
        
        # 測試不同格式的命令
        test_commands = [
            # 1. 不初始化變數
            "a := GetScanPara('X');\nWriteln(a);",
            
            # 2. 有初始化變數
            "a := 0.0;\na := GetScanPara('X');\nWriteln(a);",
            
            # 3. 直接輸出
            "Writeln(GetScanPara('X'));",
            
            # 4. 更簡潔的賦值和輸出
            "a := GetScanPara('X'); Writeln(a);"
        ]
        
        for i, cmd in enumerate(test_commands, 1):
            print(f"\n測試格式 #{i}:")
            print(f"命令內容:\n{cmd}")
            
            MySXM.execute(cmd, 5000)
            time.sleep(0.5)
            
            print(f"NotGotAnswer: {MySXM.NotGotAnswer}")
            if MySXM.LastAnswer:
                if isinstance(MySXM.LastAnswer, bytes):
                    response = MySXM.LastAnswer.decode('utf-8').split('\r\n')
                    print("回應行:")
                    for line in response:
                        print(f"  {line}")
                else:
                    print(f"回應內容: {repr(MySXM.LastAnswer)}")
            
            print("-" * 50)
            time.sleep(1)  # 在每個測試之間稍作暫停
            
    except Exception as e:
        print(f"測試過程發生錯誤: {str(e)}")

if __name__ == "__main__":
    test_command_formats()