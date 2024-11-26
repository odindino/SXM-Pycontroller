from modules.SXMPycontroller import SXMController
from utils.logger import get_logger, track_function

@track_function
def test():
    """
    執行簡單的掃描測試
    """
    stm = None
    try:
        # 初始化控制器
        stm = SXMController(debug_mode=True)
        
        # 執行自動移動掃描
        success = stm.auto_move_scan_area(
            movement_script="RULD",
            distance=20.0,
            wait_time=10,
            repeat_count=1
        )
        
        if success:
            print("掃描完成")
        else:
            print("掃描過程發生錯誤")
            
    except KeyboardInterrupt:
        print("\n使用者中斷測量")
    except Exception as e:
        print(f"\n執行期間發生錯誤: {str(e)}")
    finally:
        # 確保系統安全關閉
        if stm is not None:
            stm.safe_shutdown()
        # 停止日誌記錄
        get_logger().stop()

if __name__ == "__main__":
    test()