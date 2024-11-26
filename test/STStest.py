"""
簡化版STS測試程式
使用 SXMSpectroControl 進行 STS 測量控制
"""

import webview
import time
from pathlib import Path
import sys

# 添加主程式目錄到系統路徑
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from modules import SXMPySpectro

sxm = SXMPySpectro.SXMSpectroControl(debug_mode=True)
sxm.spectroscopy_start()

# class STSTestAPI:
#     def __init__(self):
#         print("Initializing STM controller...")
#         self.stm_controller = SXMPySpectro.SXMSpectroControl(debug_mode=True)
#         print("STM controller initialized")

#     def execute_sts(self) -> bool:
#         """執行STS測量"""
#         try:
#             print("\nStarting STS measurement...")
#             success = self.stm_controller.spectroscopy_start()
            
#             if success:
#                 print("STS measurement started successfully")
#             else:
#                 print("Failed to start STS measurement")
                
#             return success
            
#         except Exception as e:
#             print(f"STS execution error: {str(e)}")
#             return False

# def main():
#     try:
#         # 建立API實例
#         api = STSTestAPI()
        
#         # 建立視窗
#         window = webview.create_window(
#             'STS Test',
#             str(Path(__file__).parent / 'STStestGUI.html'),
#             js_api=api,
#             width=400,
#             height=200
#         )
        
#         # 啟動GUI
#         webview.start(debug=True)
        
#     except Exception as e:
#         print(f"Application error: {str(e)}")
#         sys.exit(1)

# if __name__ == '__main__':
#     main()