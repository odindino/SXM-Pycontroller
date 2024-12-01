"""
CITS Calculator Testing and Visualization Module

此模組用於測試和視覺化 CITS 量測點的分布，主要功能包括：
1. 視覺化 CITS 量測點的空間分布
2. 展示不同影像長寬比的效果
3. 驗證掃描線的分配
4. 提供詳細的量測參數資訊

Author: Zi-Liang Yang
Version: 1.0.0
Date: 2024-12-02
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
from typing import List, Tuple, Dict, Any

# 添加專案根目錄到系統路徑
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from utils.SXMPyCalc import CITSCalculator

class CITSVisualizer:
    """
    CITS 量測的視覺化工具
    
    提供完整的視覺化功能，包括：
    - 量測點的空間分布
    - 掃描範圍和方向
    - 掃描線的分布
    - 詳細的量測資訊
    """
    
    def visualize_cits_points(self, params: Dict[str, Any]) -> None:
        """
        視覺化 CITS 量測點和掃描序列
        
        Parameters
        ----------
        params : Dict[str, Any]
            量測參數字典，包含：
            - center_x, center_y: 掃描中心座標 (nm)
            - scan_range: 快軸掃描範圍 (nm)
            - angle: 掃描角度 (度)
            - points_x, points_y: X和Y方向的點數
            - total_lines: 總掃描線數
            - scan_direction: 掃描方向 (1/-1)
            - aspect_ratio: 影像長寬比
        """
        plt.figure(figsize=(12, 8))
        
        # 計算 CITS 座標和掃描參數
        result = CITSCalculator.calculate_cits_coordinates(
            center_x=params['center_x'],
            center_y=params['center_y'],
            scan_range=params['scan_range'],
            angle=params['angle'],
            num_points_x=params['points_x'],
            num_points_y=params['points_y'],
            total_scan_lines=params['total_lines'],
            scan_direction=params['scan_direction'],
            aspect_ratio=params['aspect_ratio']
        )
        
        if result is None:
            print("Error: Failed to calculate CITS coordinates")
            return
            
        coordinates, starts, ends, scanlines = result
        
        # 繪製各個視覺化層
        self._draw_scan_area(params)
        self._draw_scanlines(params, scanlines)
        self._draw_measurement_points(coordinates)
        self._draw_scan_axes(params)
        
        # 設定圖表屬性和顯示資訊
        self._set_plot_properties(params, coordinates)
        self._print_coordinates_info(coordinates)
        self._plot_measurement_sequence(coordinates)
        
        plt.show()

    # Label the first and last points of each coordinate sequence
    def _plot_measurement_sequence(self, coordinates: np.ndarray) -> None:
        """
        Plot the first and last points of each coordinate sequence
        
        Parameters
        ----------
        coordinates : np.ndarray
            Coordinate array
        """
        for i, row in enumerate(coordinates):
            plt.text(row[0, 0], row[0, 1], f'Start {i+1}', fontsize=8)
            plt.text(row[-1, 0], row[-1, 1], f'End {i+1}', fontsize=8)

    def _draw_scan_area(self, params: Dict[str, Any]) -> None:
        """繪製掃描範圍框架"""
        half_fast_range = params['scan_range'] / 2
        half_slow_range = params['scan_range'] / (2 * params['aspect_ratio'])
        angle_rad = np.radians(params['angle'])
        
        # 定義掃描範圍的四個角點（逆時針）
        corners = np.array([
            [-half_fast_range, -half_slow_range],  # 左下
            [half_fast_range, -half_slow_range],   # 右下
            [half_fast_range, half_slow_range],    # 右上
            [-half_fast_range, half_slow_range],   # 左上
            [-half_fast_range, -half_slow_range]   # 回到起點
        ])
        
        # 旋轉和平移角點
        rotated_corners = self._rotate_and_translate_points(
            corners,
            params['angle'],
            params['center_x'],
            params['center_y']
        )
        
        # 繪製掃描範圍和中心點
        plt.plot(rotated_corners[:, 0], rotated_corners[:, 1],
                'k--', linewidth=1, label='Scan Area')
        plt.plot(params['center_x'], params['center_y'],
                'r+', markersize=10, label='Scan Center')

    def _draw_scanlines(self, params: Dict[str, Any], scanlines: List[int]) -> None:
        """
        繪製掃描線
        
        Parameters
        ----------
        params : Dict[str, Any]
            量測參數
        scanlines : List[int]
            每段的掃描線數列表
        """
        half_fast_range = params['scan_range'] / 2
        half_slow_range = params['scan_range'] / (2 * params['aspect_ratio'])
        angle_rad = np.radians(params['angle'])
        
        # 計算實際的線間距
        total_lines = sum(scanlines)
        line_spacing = (2 * half_slow_range) / total_lines
        
        # 設定起始位置
        current_y = -half_slow_range
        if params['scan_direction'] == -1:
            current_y = half_slow_range
            line_spacing *= -1
            
        # 繪製每條掃描線
        for line_count in scanlines:
            for _ in range(line_count):
                start_point = [-half_fast_range, current_y]
                end_point = [half_fast_range, current_y]
                
                # 旋轉並平移線段端點
                rotated_start = self._rotate_and_translate_point(
                    start_point,
                    params['angle'],
                    params['center_x'],
                    params['center_y']
                )
                rotated_end = self._rotate_and_translate_point(
                    end_point,
                    params['angle'],
                    params['center_x'],
                    params['center_y']
                )
                
                plt.plot([rotated_start[0], rotated_end[0]],
                        [rotated_start[1], rotated_end[1]],
                        'gray', alpha=0.2)
                        
                current_y += line_spacing

    def _draw_measurement_points(self, coordinates: np.ndarray) -> None:
        """
        繪製量測點
        
        Parameters
        ----------
        coordinates : np.ndarray
            量測點座標陣列
        """
        # 使用漸變色標繪製點位
        n_points = coordinates.shape[0] * coordinates.shape[1]
        colors = plt.cm.viridis(np.linspace(0, 1, n_points))
        
        for i, row in enumerate(coordinates):
            for j, point in enumerate(row):
                color_idx = i * coordinates.shape[1] + j
                plt.plot(point[0], point[1], 'o',
                        color=colors[color_idx],
                        markersize=4)

    def _draw_scan_axes(self, params: Dict[str, Any], scale: float = 100) -> None:
        """
        繪製掃描軸方向
        
        Parameters
        ----------
        params : Dict[str, Any]
            量測參數
        scale : float
            箭頭長度比例
        """
        angle_rad = np.radians(params['angle'])
        
        # 計算快軸和慢軸方向向量
        fast_axis = np.array([
            np.cos(angle_rad) * scale,
            np.sin(angle_rad) * scale
        ])
        slow_axis = np.array([
            -np.sin(angle_rad) * scale,
            np.cos(angle_rad) * scale
        ]) * params['scan_direction']
        
        # 繪製方向箭頭
        plt.arrow(params['center_x'], params['center_y'],
                 fast_axis[0], fast_axis[1],
                 color='red', width=2, head_width=10,
                 label='Fast Axis')
        plt.arrow(params['center_x'], params['center_y'],
                 slow_axis[0], slow_axis[1],
                 color='blue', width=2, head_width=10,
                 label='Slow Axis')

    @staticmethod
    def _rotate_and_translate_point(point: List[float],
                                  angle: float,
                                  tx: float,
                                  ty: float) -> List[float]:
        """旋轉並平移單一點"""
        x, y = point
        angle_rad = np.radians(angle)
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)
        
        x_rot = x * cos_angle - y * sin_angle + tx
        y_rot = x * sin_angle + y * cos_angle + ty
        
        return [x_rot, y_rot]

    @staticmethod
    def _rotate_and_translate_points(points: np.ndarray,
                                   angle: float,
                                   tx: float,
                                   ty: float) -> np.ndarray:
        """旋轉並平移點陣列"""
        angle_rad = np.radians(angle)
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)
        
        rotated = np.zeros_like(points)
        rotated[:, 0] = points[:, 0] * cos_angle - points[:, 1] * sin_angle + tx
        rotated[:, 1] = points[:, 0] * sin_angle + points[:, 1] * cos_angle + ty
        
        return rotated

    def _set_plot_properties(self, params: Dict[str, Any],
                           coordinates: np.ndarray) -> None:
        """設定圖表屬性和資訊"""
        aspect_ratio = params['aspect_ratio']
        scan_direction = "Up" if params['scan_direction'] == 1 else "Down"
        
        plt.title(
            f'CITS Measurement Points Distribution\n'
            f'(Aspect Ratio: {aspect_ratio}, Scan Direction: {scan_direction})'
        )
        plt.xlabel('X Position (nm)')
        plt.ylabel('Y Position (nm)')
        plt.axis('equal')
        plt.grid(True)
        
        # 添加資訊文字
        info_text = (
            f"Scan Center: ({params['center_x']}, {params['center_y']}) nm\n"
            f"Fast Axis Range: {params['scan_range']} nm\n"
            f"Slow Axis Range: {params['scan_range']/aspect_ratio} nm\n"
            f"Points: {params['points_x']}×{params['points_y']}\n"
            f"Total Points: {params['points_x']*params['points_y']}"
        )
        
        plt.text(0.02, 0.98, info_text,
                transform=plt.gca().transAxes,
                bbox=dict(facecolor='white', alpha=0.8),
                verticalalignment='top')

    @staticmethod
    def _print_coordinates_info(coordinates: np.ndarray) -> None:
        """印出座標資訊"""
        print("\nCITS Measurement Points Information:")
        print(f"Shape: {coordinates.shape}")
        print(f"Total Points: {coordinates.shape[0] * coordinates.shape[1]}")
        print("\nSample Points:")
        print(f"First Point: ({coordinates[0,0,0]:.2f}, {coordinates[0,0,1]:.2f})")
        print(f"Last Point: ({coordinates[-1,-1,0]:.2f}, {coordinates[-1,-1,1]:.2f})")

def main():
    """主測試函數"""
    # 基本測試參數
    base_params = {
        'center_x': 0,
        'center_y': 0,
        'scan_range': 500,
        'angle': 0,
        'points_x': 5,
        'points_y': 5,
        'total_lines': 1000,
        'scan_direction': -1
    }
    
    # 測試不同的影像長寬比
    aspect_ratios = [0.5, 1.0, 2.0]
    visualizer = CITSVisualizer()
    
    for ar in aspect_ratios:
        test_params = base_params.copy()
        test_params['aspect_ratio'] = ar
        visualizer.visualize_cits_points(test_params)
    
    # 測試不同的掃描角度
    angles = [0, 30, 45, 60, 90]
    for angle in angles:
        test_params = base_params.copy()
        test_params['angle'] = angle
        test_params['aspect_ratio'] = 1.0
        visualizer.visualize_cits_points(test_params)

if __name__ == '__main__':
    main()