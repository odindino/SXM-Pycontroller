import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap
import sys
from pathlib import Path

# 添加主程式目錄到系統路徑
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from modules.SXMPycontroller import STSScript, SXMController

def main():
    sxm = SXMController(debug_mode=True)
    if sxm.scan_on():
        print("Scan on successfully")

if __name__ == "__main__":
    main()
