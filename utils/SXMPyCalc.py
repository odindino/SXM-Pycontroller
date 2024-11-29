"""
SXMPyCalc Module
Advanced calculation utilities for STM measurements including CITS and Local CITS.

This module provides comprehensive coordinate calculation support for:
- Standard CITS measurements
- Local area CITS measurements
- Combined multi-area CITS measurements with different spacings
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Tuple, List

@dataclass
class LocalCITSParams:
    """Parameters for defining a local CITS measurement area"""
    start_x: float      # Starting X position (nm)
    start_y: float      # Starting Y position (nm)
    dx: float          # X direction step size (nm)
    dy: float          # Y direction step size (nm)
    nx: int            # Number of points in X direction
    ny: int            # Number of points in Y direction
    scan_direction: int = 1     # 1 for upward scan, -1 for downward scan
    startpoint_direction: int = 1  # 1 for upward distribution, -1 for downward distribution
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
    
"""
Local CITS Calculator Module
Provides functionality for calculating measurement points for local area CITS.

This calculator allows users to specify a local area within the scan range
and generates measurement coordinates for that specific region.
"""
class LocalCITSCalculator:
    """Local area CITS coordinate calculator with fixed base point"""
    
    @staticmethod
    def calculate_local_cits_coordinates(
        params: LocalCITSParams,
        scan_center_x: float,
        scan_center_y: float,
        scan_angle: float
    ) -> np.ndarray:
        """
        生成並轉換單一區域的 CITS 座標點
        
        工作流程：
        1. 在原點生成基本網格
        2. 移動到指定起始點
        3. 移動到掃描中心進行旋轉
        4. 移回正確位置
        """
        # 在原點生成基本網格
        x = np.linspace(0, params.dx * (params.nx - 1), params.nx)
        y = np.linspace(0, params.dy * (params.ny - 1), params.ny)
        if params.startpoint_direction == -1:
            y *= -1
        
        # 建立網格點(在原點)
        X, Y = np.meshgrid(x, y)
        coordinates = np.column_stack((X.ravel(), Y.ravel()))
        
        # 2. 旋轉（逆時針為正）
        angle_rad = np.radians(scan_angle)
        rotation_matrix = np.array([
            [ np.cos(angle_rad), np.sin(angle_rad)],
            [-np.sin(angle_rad), np.cos(angle_rad)]
        ])
        coordinates = np.matmul(coordinates, rotation_matrix)

        # 移動到起始點
        coordinates += np.array([params.start_x, params.start_y])
        
        return coordinates

    @staticmethod
    def get_scan_axes(scan_angle: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        計算掃描的快軸和慢軸方向向量
        
        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            (慢軸向量, 快軸向量)，都是單位向量
        """
        angle_rad = np.radians(scan_angle)
        
        # 慢軸：和x軸夾角為scan_angle
        slow_axis = np.array([np.cos(angle_rad), np.sin(angle_rad)])
        
        # 快軸：慢軸逆時針旋轉90度
        fast_axis = np.array([-np.sin(angle_rad), np.cos(angle_rad)])
        
        return slow_axis, fast_axis

    @staticmethod
    def sort_coordinates_by_scan_direction(
        coordinates: np.ndarray,
        slow_axis: np.ndarray,
        fast_axis: np.ndarray
    ) -> np.ndarray:
        """
        根據掃描方向對座標進行排序
        
        改進的排序邏輯：
        1. 計算快軸和慢軸投影
        2. 將快軸投影值四捨五入到特定精度，避免浮點數比較問題
        3. 對相同快軸值的點，根據慢軸投影進行二次排序
        4. 使用穩定的排序算法確保相對順序保持一致
        """
        # 計算投影值
        fast_proj = coordinates @ fast_axis
        slow_proj = coordinates @ slow_axis
        
        # 將投影值四捨五入到特定精度以處理浮點數誤差
        precision = 1e-10
        fast_proj = np.round(fast_proj / precision) * precision
        slow_proj = np.round(slow_proj / precision) * precision
        
        # 建立複合排序鍵
        # 首先依據快軸線上的群組進行排序
        fast_groups = np.unique(fast_proj)
        sorted_indices = []
        
        for fast_val in fast_groups:
            # 找出在同一快軸線上的點
            group_mask = (fast_proj == fast_val)
            group_indices = np.where(group_mask)[0]
            
            # 依據慢軸投影值排序同一快軸線上的點
            group_slow_proj = slow_proj[group_indices]
            group_sorted = group_indices[np.argsort(group_slow_proj)]
            sorted_indices.extend(group_sorted)
        
        return coordinates[sorted_indices]

    @staticmethod
    def combi_local_cits_coordinates(
        scan_center_x: float,
        scan_center_y: float,
        scan_range: float,
        scan_angle: float,
        local_areas: List[LocalCITSParams]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        組合多個區域的座標並排序
        
        Returns 增加了快慢軸方向向量
        """
        # 獲取快慢軸方向
        slow_axis, fast_axis = LocalCITSCalculator.get_scan_axes(scan_angle)
        
        # 收集並組合所有區域的座標
        coordinates = np.concatenate([
            LocalCITSCalculator.calculate_local_cits_coordinates(
                area, scan_center_x, scan_center_y, scan_angle
            )
            for area in local_areas
        ])
        
        # 根據掃描方向排序
        coordinates = LocalCITSCalculator.sort_coordinates_by_scan_direction(
            coordinates, slow_axis, fast_axis
        )
        
        # 移除重複點
        sorted_coordinates = coordinates.tolist()
        unique_coordinates = []
        for coord in sorted_coordinates:
            if coord not in unique_coordinates:
                unique_coordinates.append(coord)
        coordinates = np.array(unique_coordinates)
        
        # 產生掃描線的起點和終點
        start_points = coordinates[:-1]
        end_points = coordinates[1:]
        
        return coordinates, start_points, end_points, (slow_axis, fast_axis)

    @staticmethod
    def validate_local_area(
            scan_center_x: float,
            scan_center_y: float,
            scan_range: float,
            start_x: float,
            start_y: float,
            dx: float,
            dy: float,
            nx: int,
            ny: int,
            scan_angle: float) -> bool:
        """
        Validate if the local CITS area is within scan range.
        
        Parameters
        ----------
        Same as calculate_local_cits_coordinates
        
        Returns
        -------
        bool
            True if local area is valid, False otherwise
            
        Notes
        -----
        This method checks if all corner points of the measurement
        area fall within the scan range after rotation.
        """
        # Create test coordinates
        coords, _, _ = LocalCITSCalculator.calculate_local_cits_coordinates(
            scan_center_x, scan_center_y, scan_range, scan_angle,
            start_x, start_y, dx, dy, nx, ny
        )
        
        # Calculate scan area bounds
        half_range = scan_range / 2
        min_x = scan_center_x - half_range
        max_x = scan_center_x + half_range
        min_y = scan_center_y - half_range
        max_y = scan_center_y + half_range
        
        # Check if all points are within bounds
        x_coords = coords[:, :, 0].flatten()
        y_coords = coords[:, :, 1].flatten()
        
        return (np.all(x_coords >= min_x) and np.all(x_coords <= max_x) and
                np.all(y_coords >= min_y) and np.all(y_coords <= max_y))
    
    @staticmethod
    def validate_combined_areas(
            scan_center_x: float,
            scan_center_y: float,
            scan_range: float,
            scan_angle: float,
            local_areas: List[LocalCITSParams]) -> List[bool]:
        """
        Validate all local CITS areas.
        
        Parameters
        ----------
        Same as combi_local_cits_coordinates
        
        Returns
        -------
        List[bool]
            Validation result for each area
        """
        validation_results = []
        
        for area in local_areas:
            is_valid = LocalCITSCalculator.validate_local_area(
                scan_center_x=scan_center_x,
                scan_center_y=scan_center_y,
                scan_range=scan_range,
                scan_angle=scan_angle,
                start_x=area.start_x,
                start_y=area.start_y,
                dx=area.dx,
                dy=area.dy,
                nx=area.nx,
                ny=area.ny
            )
            validation_results.append(is_valid)
            
        return validation_results
    
    @staticmethod
    def calculate_local_scanline_distribution(
        coordinates: np.ndarray,
        scan_center_x: float,
        scan_center_y: float,
        scan_angle: float,
        scan_range: float,
        total_lines: int
    ) -> List[int]:
        """
        計算Local CITS量測時的掃描線分布
        
        此函數根據Local CITS點位的分布，計算每次應該掃描的線數。
        在接近CITS量測區時會自動減少掃描線數，以確保準確的量測位置。
        
        Parameters
        ----------
        coordinates : np.ndarray
            CITS量測點的座標陣列，形狀為(N, 2)，每行包含(x, y)座標
        scan_center_x, scan_center_y : float
            掃描中心座標
        scan_angle : float
            掃描角度（度）
        scan_range : float
            掃描範圍（nm）
        total_lines : int
            總掃描線數
            
        Returns
        -------
        List[int]
            掃描線分布列表，每個元素代表該次應掃描的線數
        """
        try:
            # 1. 將座標轉換回原點並旋轉至水平
            coordinates_normalized = LocalCITSCalculator._normalize_coordinates(
                coordinates, scan_center_x, scan_center_y, scan_angle)
            
            # 2. 計算掃描線間距
            line_spacing = scan_range / total_lines
            
            # 3. 初始化結果列表和計數器
            scanline_distribution = []
            current_y = -scan_range/2  # 從最底部開始
            accumulated_lines = 0
            step_count = 0
            
            # 4. 主要計算邏輯
            while accumulated_lines < total_lines:
                next_y = current_y + line_spacing
                
                # 檢查是否有CITS點位在這個範圍內
                points_in_range = np.sum(
                    (coordinates_normalized[:, 1] > current_y) & 
                    (coordinates_normalized[:, 1] <= next_y)
                )
                
                if points_in_range > 0:
                    # 如果有CITS點位，記錄當前累積的掃描線數
                    if step_count > 0:
                        scanline_distribution.append(step_count)
                        accumulated_lines += step_count
                        step_count = 0
                    # 加入單行掃描
                    scanline_distribution.append(1)
                    accumulated_lines += 1
                else:
                    step_count += 1
                    
                current_y = next_y
                
                # 處理最後剩餘的線數
                if current_y >= scan_range/2 and step_count > 0:
                    remaining_lines = total_lines - accumulated_lines
                    if remaining_lines > 0:
                        scanline_distribution.append(remaining_lines)
                    break
            
            return scanline_distribution
            
        except Exception as e:
            print(f"計算掃描線分布時發生錯誤: {str(e)}")
            return [1] * total_lines  # 發生錯誤時返回最安全的配置

    @staticmethod    
    def _normalize_coordinates(
        coordinates: np.ndarray,
        center_x: float,
        center_y: float,
        angle: float
    ) -> np.ndarray:
        """
        將座標平移到原點並旋轉至水平
        
        Parameters
        ----------
        coordinates : np.ndarray
            原始座標陣列
        center_x, center_y : float
            掃描中心座標
        angle : float
            要旋轉的角度（度）
            
        Returns
        -------
        np.ndarray
            正規化後的座標陣列
        """
        # 1. 平移到原點
        coords_centered = coordinates - np.array([center_x, center_y])
        
        # 2. 旋轉至水平（逆時針旋轉回原位）
        angle_rad = np.radians(angle)
        rotation_matrix = np.array([
            [np.cos(angle_rad), np.sin(angle_rad)],
            [-np.sin(angle_rad), np.cos(angle_rad)]
        ])
        
        return coords_centered @ rotation_matrix