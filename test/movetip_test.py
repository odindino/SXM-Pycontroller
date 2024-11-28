import sys
from pathlib import Path

# 添加主程式目錄到系統路徑
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from modules.SXMPycontroller import STSScript, SXMController
from modules.SXMRemote import DDEClient

def main():
    MySXM = DDEClient("SXM", "Remote")
    oldx=MySXM.GetChannel(-2)
    oldy=MySXM.GetChannel(-3)
    # print("old x: " + str(oldx))
    # print("old y: " + str(oldy))
    # pixel = MySXM.GetScanPara('Pixel')
    # print("pixel: " + str(pixel))
    MySXM.SendWait("SpectPara(1, "+str(oldx)+");")
    MySXM.SendWait("SpectPara(2, "+str(oldy)+");")


if __name__ == "__main__":
    main()