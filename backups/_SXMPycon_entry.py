# from SXMPycontroller import SXMController


# def main():
#     # try:
#     #     sxm = SXMController()
#     #     sxm.debug_mode = True

#     #     print("Starting scan...")
#     #     sxm.scan_on()
#     #     print("Waiting for scan to complete...")

#     #     # 等待掃描完成（可以按Ctrl+C中斷）
#     #     if sxm.wait_for_scan_complete(timeout=1800):  # 30分鐘超時
#     #         scan_history = sxm.get_scan_history()
#     #         print(f"Scan finished at: {scan_history['last_scan_finished']}")
#     #         print(f"File saved as: {scan_history['last_saved_file']}")
#     #     else:
#     #         print("Scan monitoring ended without completion")

#     # except Exception as e:
#     #     print(f"Error during scan monitoring: {str(e)}")
#     # finally:
#     #     # 確保正確清理資源
#     #     sxm.stop_monitoring()
#     # controller = SXMController()

#     # # 使用直接I/O讀取位置
#     # x, y = controller.get_real_position()
#     # z = controller.get_real_topography()
#     # print(f"Tip position: ({x}, {y}, {z})")

#     # # 讀取電流和偏壓
#     # current = controller.get_real_current()
#     # bias = controller.get_real_bias()
#     # print(f"Tunneling current: {current}, Bias: {bias}")
    
#     sxm = SXMController()
#     # sxm.standard_cits(50, 50, scan_direction=0, sts_params=None)
#     sxm.GetScanPara('Scan')


# if __name__ == "__main__":
#     main()


# # SXM = SXMController()
# # SXM.scan_on()


# # scan_with_monitoring()
# # I want to scan 3 times, after sending scan_on, I will check the scan status every 2 minutes, once the scan is done, I will send the next scan_on command, and also print the current time.
# # for i in range(3):
# #     SXM.scan_on()
# #     SXM.check_scan()
# #     print("Scan on", i)
# #     time.sleep(5)
# #     while SXM.scan_status == 1.0:
# #         print("Scan is not done")
# #         time.sleep(10)
# #         SXM.check_scan()
# #     print("Scan is done")
# #     time.sleep(5)
# #     SXM.check_scan()
# #     SXM.check_scanXY()
# #     print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
# #     time.sleep(5)

# # # # scan 3 times
# # # for i in range(6):
# # #     SXM.scan_on()
# # #     print("Scan on", i)
# # #     time.sleep(10)
# # # SXMController
# # SXM.check_scan()
# # print("scan status", SXM.scan_status)
# # SXM.scan_on()
# # time.sleep(5)
# # print('check scan')
# # SXM.check_scan()
# # print("scan status", SXM.scan_status)
# # SXM.scan_off()
# # time.sleep(5)
# # print('check scan')
# # SXM.check_scan()
# # print("scan status", SXM.scan_status)
# # SXM.check_scanXY()

# # SXM.scan_off()
# # time.sleep(5)
# # # time.sleep(5)
# # # SXM.clear_memo()
# # # time.sleep(5)
# # print('check scan')
# # SXM.check_scan()
# # SXM.check_scanXY()
# # # SXM.scan_off()

# # MySXM = SXMRemote.DDEClient("SXM", "Remote")
# # print(MySXM.GetScanPara('Angle'))


# # def automoveScanArea(SXM, movelist, distance, waittime, repeat=0):
# #     SXM_status = SXM.GetScanPara('Scan')
# #     x, y = getXYcenter(SXM)

# #     # move the scan area
# #     for i in range(len(movelist)):
# #         print("move to " + str(i) + "th scan area")
# #         if movelist[i] == 'R':
# #             x += distance
# #             setXYcenter(SXM, x, y)
# #         elif movelist[i] == 'L':
# #             x -= distance
# #             setXYcenter(SXM, x, y)
# #         elif movelist[i] == 'U':
# #             y += distance
# #             setXYcenter(SXM, x, y)
# #         elif movelist[i] == 'D':
# #             y -= distance
# #             setXYcenter(SXM, x, y)
# #         else:
# #             print("Wrong input")

# #         # stay for a while to wait for the tip to be stable
# #         time.sleep(waittime)

# #         # repeat the scan
# #         for repeat_time in range(repeat+1):
# #             print("scan " + str(repeat_time+1) + " times")
# #             startScan(SXM)
# #             SXM_status = SXM.GetScanPara('Scan')

# #             while SXM_status == 1.:
# #                 SXM_status = SXM.GetScanPara('Scan')

# # automoveScanArea(MySXM, ['R', 'U', 'L','L','D','D','R','R'], 5, 5)


# # ==== CITS test ==== #
# # 創建SXM控制器實例
# # sxm_controller = SXMController()

# # # 設定CITS參數
# # sts_settings = {
# #     'start_bias': -1.5,    # 起始偏壓 -1.5V
# #     'end_bias': 1.5,       # 結束偏壓 1.5V
# #     'points': 200,         # 每條STS曲線的點數
# #     'delay': 50            # 每點的延遲時間(ms)
# # }

# # # 執行CITS量測
# # sxm_controller.CITS(
# #     start_x=0,      # 起始X座標 (nm)
# #     start_y=0,      # 起始Y座標 (nm)
# #     dx=5,           # X方向點間距 (nm)
# #     dy=5,           # Y方向線間距 (nm)
# #     nx=100,         # X方向點數
# #     ny=100,         # Y方向線數
# #     sts_params=sts_settings
# # )
# # ==== CITS test ==== #


from modules.SXMPycontroller import SXMController
from SXMDiagnosizer import run_diagnostics

def main():
    # 基本使用
    sxm = SXMController()
    x, y = sxm.get_position()
    print(f"當前位置: ({x}, {y})")

    # 獲取完整狀態
    state = sxm.get_current_state()
    print(f"掃描範圍: {state['Range']}")
    print(f"掃描角度: {state['Angle']}")

    # 檢查掃描狀態
    if sxm.is_scanning():
        print("正在掃描中...")

if __name__ == "__main__":
    main()