import math
import numpy as np

class SXMCalculator:
    """計算工具類別"""
    
    @staticmethod
    def rotate_coordinates(x, y, angle_deg, center_x=0, center_y=0):
        """座標旋轉計算"""
        angle_rad = math.radians(angle_deg)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        x_shifted = x - center_x
        y_shifted = y - center_y
        
        x_rot = x_shifted * cos_angle - y_shifted * sin_angle
        y_rot = x_shifted * sin_angle + y_shifted * cos_angle
        
        return (x_rot + center_x, y_rot + center_y)
        
    @staticmethod
    def calculate_grid_points(start_x, start_y, width, height, nx, ny):
        """計算網格點位置"""
        x = np.linspace(start_x, start_x + width, nx)
        y = np.linspace(start_y, start_y + height, ny)
        return np.meshgrid(x, y)
        
    @staticmethod
    def calculate_movement_vector(direction, distance, angle):
        """計算移動向量"""
        angle_rad = math.radians(angle)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        
        if direction == 'R':
            return (distance * cos_angle, distance * sin_angle)
        elif direction == 'L':
            return (-distance * cos_angle, -distance * sin_angle)
        elif direction == 'U':
            return (-distance * sin_angle, distance * cos_angle)
        elif direction == 'D':
            return (distance * sin_angle, -distance * cos_angle)
        else:
            raise ValueError(f"Unknown direction: {direction}")
        

class CITSCalculator:
    """CITS 座標計算工具類別"""
    
    @staticmethod
    def calculate_cits_coordinates(center_x: float, center_y: float, 
                                scan_range: float, angle: float,
                                num_points_x: int, num_points_y: int,
                                total_scan_lines: int = 500,
                                scan_direction: int = 1) -> tuple:
        """
        計算 CITS 量測點的座標矩陣
        
        工作流程：
        1. 在原點(0,0)建立網格點
        2. 旋轉網格點
        3. 平移到掃描中心位置
        
        Parameters
        ----------
        center_x, center_y : float
            掃描中心座標 (nm)
        scan_range : float
            掃描範圍 (nm)
        angle : float
            掃描角度 (度)
        num_points_x : int
            X 方向點數
        num_points_y : int
            Y 方向點數
        total_scan_lines : int
            總掃描線數
        scan_direction : int
            掃描方向 (1: 由下到上, -1: 由上到下)
            
        Returns
        -------
        tuple
            (座標矩陣, 起始點列表, 結束點列表, 掃描線分配列表)
        """
        import numpy as np
        
        # 計算實際掃描範圍 (考慮安全邊距)
        safe_margin = 0.004  # 0.4% 邊距 
        effective_range = scan_range * (1 - safe_margin)
        half_range = effective_range / 2

        # 計算 scanline 的步數 --> list
        scanlines = CITSCalculator.calculate_scanline_distribution(total_scan_lines, num_points_y, safe_margin)
        
        # 步驟1：在原點建立網格點
        x = np.linspace(-half_range, half_range, num_points_x)
        y = np.linspace(-half_range, half_range, num_points_y)
        if scan_direction == -1:
            y = y[::-1]    
        X, Y = np.meshgrid(x, y)
        
        # 步驟2：旋轉網格點
        angle_rad = np.radians(angle)
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)
        
        X_rot = X * cos_angle - Y * sin_angle
        Y_rot = X * sin_angle + Y * cos_angle
        
        # 步驟3：平移到掃描中心
        X_final = X_rot + center_x
        Y_final = Y_rot + center_y
        
        # 組合成座標矩陣 (Ny x Nx x 2)
        coordinates = np.stack([X_final, Y_final], axis=2)
        
        # 計算每條掃描線的起始和結束點
        line_starts = coordinates[:, 0, :]
        line_ends = coordinates[:, -1, :]
        
        return coordinates, line_starts, line_ends, scanlines
        
    @staticmethod
    def calculate_scanline_distribution(total_lines: int, num_points: int, safe_margin: float = 0.02):
        """
        計算掃描線的均勻分配，適用於任意點數的情況
        
        工作原理：
        1. 計算總共需要分配的線數（扣除頭尾安全邊距）
        2. 計算平均每段應該分配的理想線數（可能是小數）
        3. 使用累積誤差的方式決定每段實際分配的線數
        4. 確保總和等於指定的總線數
        
        Parameters
        ----------
        total_lines : int
            總掃描線數
        num_points : int
            CITS的Y方向點數
        safe_margin : float
            安全邊距比例
            
        Returns
        -------
        list
            均勻分布的掃描線數列表
        """
        # 計算頭尾的掃描線數
        firstlast = int(total_lines * safe_margin / 2)
        
        # 計算中間需要分配的總線數
        middle_lines = total_lines - 2 * firstlast
        segments = num_points - 1
        
        # 計算理想的每段線數（允許小數）
        ideal_lines_per_segment = middle_lines / segments
        
        # 使用累積誤差方法分配線數
        scanlines = [firstlast]
        accumulated_lines = 0
        
        for i in range(segments):
            # 計算理想的累積總線數
            ideal_accumulated = (i + 1) * ideal_lines_per_segment
            # 計算實際應該累積的線數（取整）
            actual_accumulated = round(ideal_accumulated)
            # 本段應分配的線數
            current_segment_lines = actual_accumulated - accumulated_lines
            scanlines.append(current_segment_lines)
            accumulated_lines = actual_accumulated
        
        scanlines.append(firstlast)
        
        # 驗證總和
        assert sum(scanlines) == total_lines, (
            f"總線數不符：期望 {total_lines}，實際 {sum(scanlines)}"
        )
        
        return scanlines