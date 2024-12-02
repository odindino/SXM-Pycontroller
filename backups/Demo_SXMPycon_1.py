from modules.SXMPycontroller import SXMController

def demonstrate_sxm_control():
    """
    展示SXM控制器的基本用法
    """
    print("=== SXM控制器示例 ===")
    
    try:
        # 創建控制器實例
        sxm = SXMController()
        
        # 獲取並顯示當前狀態
        sxm.print_current_state()
        
        # 示範單個參數讀取
        x_pos = sxm.GetScanPara('X')
        y_pos = sxm.GetScanPara('Y')
        print(f"\n當前位置: X = {x_pos}, Y = {y_pos}")
        
        # 示範獲取完整狀態
        state = sxm.get_current_state()
        scan_range = state['Range']
        scan_angle = state['Angle']
        print(f"掃描範圍: {scan_range}")
        print(f"掃描角度: {scan_angle}")
        
    except Exception as e:
        print(f"示例執行過程中發生錯誤: {str(e)}")

if __name__ == "__main__":
    demonstrate_sxm_control()