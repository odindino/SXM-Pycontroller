
import sys
from pathlib import Path
import time

# 添加主程式目錄到系統路徑
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))
from modules.SXMPycontroller import STSScript, SXMController
from modules.SXMRemote import DDEClient
def main():
    # 初始化控制器
    # MySXM= DDEClient("SXM","Remote")
    # MySXM.SendWait(f"SpectStart;")
    # MySXM.SendWait(f"ScanLine(5);")
    # MySXM.SendWait(f"SpectStart;")
    stm = SXMController(debug_mode=True)
    # print("Start scanning")
    stm.spectroscopy_start()
    stm.scan_lines(5)
    time.sleep(10)
    stm.scan_lines(5)
    # stm.spectroscopy_start()
    # time.sleep(5/1.5)
    # print("Start spectroscopy_1")
    # stm.spectroscopy_start()
    # print("Start scanning")
    # stm.scan_lines(5)
    # time.sleep(5/1.5)
    # print("Start spectroscopy_2")
    # stm.spectroscopy_start()
    # print("Start scanning")
    # stm.scan_lines(5)
    # time.sleep(5/1.5)
    # print("Start spectroscopy_3")
    # stm.spectroscopy_start()

if __name__ == "__main__":
    main()