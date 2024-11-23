from SXMPycontroller import SXMController
import time

def perform_measurement_sequence():
    """
    執行一個簡單的測量序列：
    1. 在當前位置進行掃描
    2. 移動到幾個不同位置進行STS測量
    3. 最後執行一個自動移動掃描序列
    """
    try:
        # 初始化控制器
        print("Initializing STM controller...")
        stm = SXMController(debug_mode=True)
        
        if not stm.initialize_system():
            print("Initialization failed")
            return
            
        # 1. 執行初始掃描
        print("\n=== Starting initial scan ===")
        stm.setup_scan_area(
            center_x=0.0,
            center_y=0.0,
            scan_range=100.0,  # nm
            angle=0,
            pixels=500
        )
        
        stm.scan_on()
        if stm.wait_for_scan_complete(timeout=300):  # 5分鐘超時
            print("Initial scan completed")
        else:
            print("Initial scan failed or timed out")
            return
            
        # 2. 執行STS測量
        print("\n=== Performing STS measurements ===")
        sts_positions = [
            (25.0, 25.0),
            (-25.0, 25.0),
            (-25.0, -25.0),
            (25.0, -25.0)
        ]
        
        sts_params = {
            'start_bias': -2.0,
            'end_bias': 2.0,
            'points': 400,
            'delay': 2
        }
        
        for i, (x, y) in enumerate(sts_positions):
            print(f"\nSTS measurement {i+1}/4 at position ({x}, {y})")
            stm.perform_spectroscopy(x, y, wait_time=1.0, params=sts_params)
            time.sleep(1)  # 測量之間的等待
            
        # 3. 執行自動移動掃描序列
        print("\n=== Starting auto move scan sequence ===")
        stm.auto_move_scan_area(
            movement_script="RULD",  # 右上左下的移動序列
            distance=50.0,           # 每次移動50nm
            wait_time=1.0,           # 每次移動後等待1秒
            repeat_count=1           # 每個位置掃描1次
        )
        
        # 安全關閉系統
        print("\n=== Measurement sequence completed ===")
        stm.safe_shutdown()
        
    except KeyboardInterrupt:
        print("\nMeasurement interrupted by user")
        stm.safe_shutdown()
    except Exception as e:
        print(f"\nError during measurement: {str(e)}")
        stm.safe_shutdown()

def test():
    """
    做一個簡單的scan
    """
    try:
        # 初始化控制器
        print("Initializing STM controller...")
        stm = SXMController(debug_mode=True)
        stm.scan_on()
        
    #     if not stm.initialize_system():
    #         print("Initialization failed")
    #         return
            
    #     # 1. 執行初始掃描
    #     print("\n=== Starting initial scan ===")
    #     stm.setup_scan_area(
    #         center_x=0.0,
    #         center_y=0.0,
    #         scan_range=100.0,  # nm
    #         angle=0,
    #     )
        
    #     stm.scan_on()
    #     if stm.wait_for_scan_complete(timeout=300):  # 5分鐘超時
    #         print("Initial scan completed")
    #     else:
    #         print("Initial scan failed or timed out")
    #         return
            
    #     # 安全關閉系統
    #     print("\n=== Measurement sequence completed ===")
    #     stm.safe_shutdown()
        
    except KeyboardInterrupt:
        print("\nMeasurement interrupted by user")
        stm.safe_shutdown()
    except Exception as e:
        print(f"\nError during measurement: {str(e)}")
        stm.safe_shutdown()

if __name__ == "__main__":
    # perform_measurement_sequence()
    test()