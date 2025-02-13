"""
Local CITS Testing and Visualization Module

此模組用於測試和視覺化 Local CITS 量測點的分布，主要功能包括：
1. 視覺化 Local CITS 量測點的分布
2. 顯示掃描順序和方向
3. 繪製掃描線路徑
4. 提供掃描參數和量測點的詳細資訊

Author: Your Name
Version: 1.0.0
Date: 2024-01-03
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
from typing import List, Tuple

# 添加專案根目錄到系統路徑
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from utils.SXMPyCalc import LocalCITSCalculator, LocalCITSParams

class LocalCITSVisualizer:
    """
    Local CITS 量測的視覺化工具
    
    此類別提供完整的視覺化功能，包括：
    - 量測點的分布和順序
    - 掃描範圍和方向
    - 掃描線的路徑
    - 詳細的量測資訊
    """
    
    def visualize_cits_points(self, params: dict) -> None:
        """視覺化 Local CITS 量測點和掃描序列"""
        plt.figure(figsize=(12, 8))
        
        # 計算座標和掃描參數
        coordinates, _, _, (slow_axis, fast_axis) = LocalCITSCalculator.combi_local_cits_coordinates(
            params['scan_center_x'],
            params['scan_center_y'],
            params['scan_range'],
            params['scan_angle'],
            params['total_lines'],
            params['scan_direction'],
            params['local_areas']
        )
        
        # 計算掃描線分布（現在回傳一個元組）
        scanline_info = LocalCITSCalculator.calculate_local_scanline_distribution(
            coordinates,
            params['scan_center_x'],
            params['scan_center_y'],
            params['scan_angle'],
            params['scan_range'],
            params['scan_direction'],
            params['total_lines']
            
        )
        
        # 繪製各個圖層
        self._draw_scan_area(params)
        self._draw_scanlines(
            params['scan_center_x'],
            params['scan_center_y'],
            params['scan_range'],
            params['scan_angle'],
            params['scan_direction'],
            scanline_info
        )
        self._plot_measurement_sequence(coordinates)
        self._plot_scan_axes(
            params['scan_center_x'],
            params['scan_center_y'],
            slow_axis,
            fast_axis,
            params['scan_direction']
        )
        
        # 設定圖表屬性和資訊
        self._set_plot_properties(params)
        self._print_coordinates_info(coordinates)
        self._plot_coordinates_with_index(coordinates)
        plt.show()

    def _draw_scan_area(self, params: dict) -> None:
        """繪製掃描範圍框架"""
        half_range = params['scan_range'] / 2
        angle_rad = np.radians(params['scan_angle'])
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)
        
        # 定義掃描範圍的四個角點（逆時針順序）
        corners = np.array([
            [-half_range, -half_range],  # 左下
            [half_range, -half_range],   # 右下
            [half_range, half_range],    # 右上
            [-half_range, half_range],   # 左上
            [-half_range, -half_range]   # 回到起點
        ])
        
        # 旋轉並平移角點
        rotated_corners = np.zeros_like(corners)
        for i, (x, y) in enumerate(corners):
            rotated_corners[i, 0] = (x * cos_angle - y * sin_angle + 
                                   params['scan_center_x'])
            rotated_corners[i, 1] = (x * sin_angle + y * cos_angle + 
                                   params['scan_center_y'])
        
        # 繪製掃描範圍和中心點
        plt.plot(rotated_corners[:, 0], rotated_corners[:, 1], 
                'k--', linewidth=1, label='Scan Area')
        plt.plot(params['scan_center_x'], params['scan_center_y'], 
                'r+', markersize=10, label='Scan Center')

    def _draw_scanlines(self, center_x: float, center_y: float, 
                   scan_range: float, angle: float, scan_direction: int,
                   scanline_info: Tuple[List[int], List[np.ndarray]],
                   color: str = 'gray',
                   alpha: float = 0.5) -> None:
        """
        繪製掃描線
        
        Parameters
        ----------
        center_x, center_y : float
            掃描中心座標
        scan_range : float
            掃描範圍
        angle : float
            掃描角度（度）
        scanline_info : Tuple[List[int], List[np.ndarray]]
            第一個元素是掃描線分布列表
            第二個元素是每個掃描位置的量測點列表
        color : str
            掃描線顏色
        alpha : float
            透明度
        """
        scanline_distribution, coordinate_distribution = scanline_info  # 解構元組
        print("scanline_distribution: ", scanline_distribution)
        print("coordinate_distribution: ", coordinate_distribution)
        print(np.shape(coordinate_distribution))
        
        angle_rad = np.radians(angle)
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)
        
        half_range = scan_range / 2
        total_lines = sum(scanline_distribution)  # 現在可以正確計算總線數
        line_spacing = scan_range / total_lines
        if scan_direction == -1:
            line_spacing *= -1

        # 繪製每條掃描線
        current_y = -half_range
        if scan_direction == -1:
            current_y = half_range

        for step_count in scanline_distribution:
            # 計算線的起點和終點
            start_x = -half_range
            end_x = half_range
            
            # 旋轉並平移端點
            start_rotated_x = start_x * cos_angle - current_y * sin_angle + center_x
            start_rotated_y = start_x * sin_angle + current_y * cos_angle + center_y
            
            end_rotated_x = end_x * cos_angle - current_y * sin_angle + center_x
            end_rotated_y = end_x * sin_angle + current_y * cos_angle + center_y
            
            # 繪製掃描線
            plt.plot([start_rotated_x, end_rotated_x],
                    [start_rotated_y, end_rotated_y],
                    color=color, alpha=alpha, linestyle='-')
            
            # 更新位置
            current_y += step_count * line_spacing

    def _plot_measurement_sequence(self, coordinates: np.ndarray) -> None:
        """繪製量測點序列"""
        n_points = len(coordinates)
        colors = plt.cm.viridis(np.linspace(0, 1, n_points))
        
        # 繪製所有點
        for i, (x, y) in enumerate(coordinates):
            plt.plot(x, y, 'o', color=colors[i], markersize=4)
        
        # 標示起點和終點
        plt.plot(coordinates[0, 0], coordinates[0, 1], 'k*', 
                markersize=10, label='First Point')
        plt.plot(coordinates[-1, 0], coordinates[-1, 1], 'r*', 
                markersize=10, label='Last Point')

    def _plot_scan_axes(self, center_x: float, center_y: float, 
                       slow_axis: np.ndarray, fast_axis: np.ndarray, 
                       scan_direction: int = 1,
                       scale: float = 100) -> None:
        """繪製掃描軸方向"""
        # if scan_direction == -1:
        #     slow_axis[0] *= -1
        #     fast_axis[1] *= -1

        plt.arrow(center_x, center_y, 
                 slow_axis[0] * scale, slow_axis[1] * scale,
                 color='blue', width=2, head_width=10,
                 label='Slow Axis')
        plt.arrow(center_x, center_y,
                 fast_axis[0] * scale, fast_axis[1] * scale,
                 color='red', width=2, head_width=10,
                 label='Fast Axis')

    @staticmethod
    def _rotate_and_translate(point: List[float], angle: float, 
                            tx: float, ty: float) -> List[float]:
        """旋轉並平移點座標"""
        x, y = point
        cos_angle = np.cos(angle)
        sin_angle = np.sin(angle)
        x_rot = x * cos_angle - y * sin_angle + tx
        y_rot = x * sin_angle + y * cos_angle + ty
        return [x_rot, y_rot]

    def _set_plot_properties(self, params: dict) -> None:
        """設定圖表屬性"""
        plt.title('Local CITS Measurement Points and Scanning Sequence')
        plt.xlabel('X Position (nm)')
        plt.ylabel('Y Position (nm)')
        plt.axis('equal')
        plt.grid(True)
        plt.legend(loc='upper right', bbox_to_anchor=(0.98, 0.98))
        
        # 計算總點數
        total_points = sum(area.nx * area.ny for area in params['local_areas'])
        
        # 顯示資訊文字
        info_text = (
            f"Scan Center: ({params['scan_center_x']}, {params['scan_center_y']}) nm\n"
            f"Scan Range: {params['scan_range']} nm\n"
            f"Scan Angle: {params['scan_angle']}°\n"
            f"Total Points: {total_points}"
        )
        
        plt.text(0.98, 0.15, info_text, 
                transform=plt.gca().transAxes,
                bbox=dict(facecolor='white', alpha=0.8),
                horizontalalignment='right',
                verticalalignment='bottom')

    @staticmethod
    def _print_coordinates_info(coordinates: np.ndarray) -> None:
        """印出座標資訊"""
        print("\nLocal CITS Measurement Points Sequence:")
        for i, (x, y) in enumerate(coordinates):
            print(f"Point {i+1}: ({x:.2f}, {y:.2f})")

    def _plot_coordinates_with_index(self, coordinates, sample_indices=[-1, -2, -3]):
        """在特定點位標示序號，方便檢查排序結果"""
        for idx in sample_indices:
            plt.annotate(f'P{len(coordinates)+idx}', 
                        coordinates[idx],
                        xytext=(5, 5), 
                        textcoords='offset points')

def main():
    """主測試函數"""
    # 測試參數設定
    # test_params = {
    #     'scan_center_x': 0,
    #     'scan_center_y': 0,
    #     'scan_range': 100,
    #     'scan_angle': 0,
    #     'total_lines': 500,
    #     'scan_direction': 1,
    #     'local_areas': [
    #         LocalCITSParams(
    #             start_x=5, start_y=5,
    #             dx=1, dy=1,
    #             nx=3, ny=3,
    #             startpoint_direction=1
    #         ),
    #         LocalCITSParams(
    #             start_x=-5, start_y=-5,
    #             dx=2, dy=2,
    #             nx=3, ny=3,
    #             startpoint_direction=-1
    #         ),
    #         LocalCITSParams(
    #             start_x=-5, start_y=5,
    #             dx=1, dy=1,
    #             nx=3, ny=3,
    #             startpoint_direction=-1
    #         )
    #     ]
    # }
    test_params = {
        'scan_center_x': -357.66,
        'scan_center_y': 228.19,
        'scan_range': 50,
        'scan_angle': 0,
        'total_lines': 500,
        'scan_direction': -1,
        'local_areas': [
            LocalCITSParams(
                start_x=-8, start_y=-6,
                dx=0.4, dy=0.8,
                nx=45, ny=2,
                startpoint_direction=1
            )
        ]
    }
    
    # 建立視覺化器並執行測試
    visualizer = LocalCITSVisualizer()
    visualizer.visualize_cits_points(test_params)

if __name__ == '__main__':
    main()