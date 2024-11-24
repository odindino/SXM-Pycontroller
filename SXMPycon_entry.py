from SXMPycontroller import SXMController
from utils.SXMPyLogger import log_execution, get_logger

@log_execution()
def test():
    """執行簡單的掃描測試"""
    stm = None
    logger = get_logger()
    
    try:
        logger.procedure("=== 開始掃描測試 ===")
        
        # 初始化控制器
        stm = SXMController(debug_mode=True)
        logger.procedure("控制器初始化完成")
        
        # 執行自動移動掃描
        success = stm.auto_move_scan_area(
            movement_script="RULD",
            distance=20.0,
            wait_time=10,
            repeat_count=1
        )
        
        if success:
            logger.procedure("測試完成：掃描成功")
            print("掃描完成")
        else:
            logger.procedure("測試完成：掃描失敗")
            print("掃描過程發生錯誤")
            
    except KeyboardInterrupt:
        logger.procedure("使用者中斷測量")
        print("\n使用者中斷測量")
    except Exception as e:
        logger.procedure(f"測試過程發生錯誤: {str(e)}")
        logger.error(f"執行期間錯誤: {str(e)}")
        print(f"\n執行期間發生錯誤: {str(e)}")
    finally:
        # 確保系統安全關閉
        if stm is not None:
            stm.safe_shutdown()
            logger.procedure("=== 測試結束 ===")

if __name__ == "__main__":
    test()