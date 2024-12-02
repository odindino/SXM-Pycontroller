"""
CITS Testing and Visualization Module
用於測試和視覺化CITS量測點的分布

This module provides functionality to:
1. Calculate CITS measurement points
2. Visualize scan area and measurement points
3. Verify measurement sequence and timing
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap
import sys
from pathlib import Path

# 添加主程式目錄到系統路徑
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from utils.SXMPyCalc import CITSCalculator

class CITSVisualizer:
    def __init__(self):
        # 建立自定義的顏色映射，從深藍到淺藍
        colors = [(0, 0, 0.8), (0.8, 0.8, 1)]  # 深藍到淺藍
        self.cmap = LinearSegmentedColormap.from_list('custom_blues', colors)
        
    def visualize_cits_points(self, params):
        """
        視覺化CITS量測點和掃描範圍

        使用正確的方式繪製和旋轉掃描範圍框框，
        確保框框是以掃描中心為基準進行旋轉
        
        Parameters
        ----------
        params : dict
            包含以下鍵值:
            - center_x, center_y: 掃描中心座標
            - scan_range: 掃描範圍
            - angle: 掃描角度
            - num_points_x, num_points_y: CITS點數
            - scan_direction: 掃描方向
            - total_scan_lines: 總掃描線數
        """
        # # 建立新的圖形
        # plt.figure(figsize=(12, 8))
        
        # 計算CITS點座標
        calculator = CITSCalculator()
        coordinates, line_starts, line_ends, line_between = calculator.calculate_cits_coordinates(
            params['center_x'], 
            params['center_y'],
            params['scan_range'],
            params['angle'],
            params['num_points_x'],
            params['num_points_y'],
            params['scan_direction']
        )
        
        
        # # 計算掃描參數
        # scan_params = calculator.calculate_scan_parameters(
        #     total_lines=params['total_scan_lines'],
        #     points_per_sts=params['num_points_y']
        # )
        
        # 修改掃描範圍框框的繪製
        plt.figure(figsize=(12, 8))
        
        # 計算矩形的四個角點（相對於中心點）
        half_range = params['scan_range'] / 2
        angle_rad = np.radians(params['angle'])
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)
        
        # 定義未旋轉時的角點（相對於中心點）
        corners = np.array([
            [-half_range, -half_range],  # 左下
            [half_range, -half_range],   # 右下
            [half_range, half_range],    # 右上
            [-half_range, half_range],   # 左上
            [-half_range, -half_range]   # 回到起點，形成封閉形狀
        ])
        
        # 旋轉角點並平移到掃描中心
        rotated_corners = np.zeros_like(corners)
        for i, (x, y) in enumerate(corners):
            rotated_corners[i, 0] = (x * cos_angle - y * sin_angle) + params['center_x']
            rotated_corners[i, 1] = (x * sin_angle + y * cos_angle) + params['center_y']
        
        # 繪製框框
        plt.plot(rotated_corners[:, 0], rotated_corners[:, 1], 
                'k--', linewidth=1, label='Scan Area')
        
        # 標示掃描中心
        plt.plot(params['center_x'], params['center_y'], 
                'r+', markersize=10, label='Scan Center')
        
        # 繪製 CITS 點（保持原有的程式碼）
        coordinates, _, _, _ = CITSCalculator.calculate_cits_coordinates(
            params['center_x'], 
            params['center_y'],
            params['scan_range'],
            params['angle'],
            params['num_points_x'],
            params['num_points_y'],
            params['scan_direction']
        )
        
        total_points = params['num_points_x'] * params['num_points_y']
        for i in range(params['num_points_y']):
            for j in range(params['num_points_x']):
                point_number = i * params['num_points_x'] + j
                color = self.cmap(point_number / total_points)
                plt.plot(
                    coordinates[i, j, 0],
                    coordinates[i, j, 1],
                    'o',
                    color=color,
                    markersize=0.1
                )
        
        # 設定圖形屬性
        plt.title('CITS Measurement Points Visualization')
        plt.xlabel('X Position (nm)')
        plt.ylabel('Y Position (nm)')
        plt.axis('equal')
        plt.grid(True)
        plt.legend()
        
        # 繪製CITS點
        total_points = params['num_points_x'] * params['num_points_y']
        for i in range(params['num_points_y']):
            for j in range(params['num_points_x']):
                point_number = i * params['num_points_x'] + j
                color = self.cmap(point_number / total_points)
                plt.plot(
                    coordinates[i, j, 0],
                    coordinates[i, j, 1],
                    'o',
                    color=color,
                    markersize=8
                )
        
        # 設定圖形屬性
        plt.title('CITS Measurement Points Visualization')
        plt.xlabel('X Position (nm)')
        plt.ylabel('Y Position (nm)')
        plt.axis('equal')
        plt.grid(True)
        
        # 添加顏色條
        sm = plt.cm.ScalarMappable(
            cmap=self.cmap,
            norm=plt.Normalize(0, total_points)
        )
        plt.colorbar(sm, label='Measurement Sequence')
        
        # 顯示掃描參數
        info_text = (
            f'Scan Center: ({params["center_x"]}, {params["center_y"]}) nm\n'
            f'Scan Range: {params["scan_range"]} nm\n'
            f'Scan Angle: {params["angle"]}°\n'
            f'Points: {params["num_points_x"]}×{params["num_points_y"]}\n'
            f'Direction: {"Up" if params["scan_direction"]==1 else "Down"}\n'
            
            f'Total scan lines: {params["total_scan_lines"]}'
        )
        plt.text(
            1.2, 0.5, info_text,
            transform=plt.gca().transAxes,
            bbox=dict(facecolor='white', alpha=0.8)
        )
        
        # 顯示座標矩陣
        print("\nCITS Measurement Points Coordinates:")
        print("Format: [Line Number, Point Number]: (X, Y)")
        for i in range(params['num_points_y']):
            for j in range(params['num_points_x']):
                print(f"[{i+1}, {j+1}]: ({coordinates[i,j,0]:.2f}, {coordinates[i,j,1]:.2f})")
        
        # print(f"\nScan {scan_params['lines_between_sts']} lines between each STS line")
        # print(f"Estimated STS positions at lines: {scan_params['estimated_sts_positions']}")
        print(f"Line between STS: {line_between}")
        plt.show()

def main():
    """主測試函數"""
    # 測試參數
    test_params = {
        'center_x': 900,      # 掃描中心X座標 (nm)
        'center_y': 900,      # 掃描中心Y座標 (nm)
        'scan_range': 500,    # 掃描範圍 (nm)
        'angle': 30,          # 掃描角度 (度)
        'num_points_x': 11,   # X方向CITS點數
        'num_points_y': 21,   # Y方向CITS點數
        'scan_direction': 1,  # 掃描方向 (1: 向上, -1: 向下)
        'total_scan_lines': 500  # 總掃描線數
    }
    
    # 建立視覺化器並執行測試
    visualizer = CITSVisualizer()
    visualizer.visualize_cits_points(test_params)

if __name__ == '__main__':
    main()