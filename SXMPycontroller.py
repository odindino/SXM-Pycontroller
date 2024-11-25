from modules.SXMPyCITS import SXMCITSControl
from utils.logger import track_function


class SXMController(SXMCITSControl):
    """
    STM控制器主類別
    整合所有功能模組並提供統一的操作介面
    """

    def __init__(self, debug_mode=False):
        super().__init__(debug_mode)

    @track_function
    def initialize_system(self):
        try:
            self.feedback_on()
            self.SetScanPara('Speed', 2.0)
            self.SetScanPara('Range', 100.0)
            x, y = self.get_position()
            print(f"System initialized at position ({x}, {y})")
            return True
        except Exception as e:
            print(f"Initialization Error: {str(e)}")
            return False

    @track_function
    def safe_shutdown(self):
        try:
            self.scan_off()
            self.feedback_on()
            self.stop_monitoring()
            print("System safely shut down")
        except Exception as e:
            print(f"Shutdown Error: {str(e)}")

    @track_function
    def auto_move_scan_area(self, movement_script: str, distance: float,
                            wait_time: float, repeat_count: int = 1) -> bool:
        try:
            print(
                f"Starting auto move scan:\n"
                f"Movement script: {movement_script}\n"
                f"Distance: {distance} nm\n"
                f"Wait time: {wait_time} s\n"
                f"Repeat count: {repeat_count}"
            )
            return super().auto_move_scan_area(
                movement_script, distance, wait_time, repeat_count
            )
        except Exception as e:
            print(f"Auto move scan error: {str(e)}")
            return False
