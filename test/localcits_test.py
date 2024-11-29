"""
Local CITS Testing and Visualization Module
Focuses on visualizing CITS measurement points and their scanning sequence
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add project root to system path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from utils.SXMPyCalc import LocalCITSCalculator, LocalCITSParams

class LocalCITSVisualizer:
    """Visualization tool for local area CITS measurements"""
    
    def visualize_cits_points(self, params: dict):
        """
        Visualize CITS measurement points with scanning sequence.
        
        Parameters
        ----------
        params : dict
            Measurement parameters including scan area and local CITS settings
        """
        plt.figure(figsize=(12, 8))
        
        # Calculate combined coordinates
        coordinates, _, _, (slow_axis, fast_axis) = LocalCITSCalculator.combi_local_cits_coordinates(
            params['scan_center_x'],
            params['scan_center_y'],
            params['scan_range'],
            params['scan_angle'],
            params['local_areas']
        )
        
        # Draw scan area frame
        self._draw_scan_area(params)
        
        # Plot measurement points with sequential coloring
        self._plot_measurement_sequence(coordinates)
        
        # Set plot properties
        self._set_plot_properties(params)
        
        # Print coordinates for reference
        self._print_coordinates_info(coordinates)

        # Plot scan axes
        self._plot_scan_axes(params['scan_center_x'], params['scan_center_y'],
                        slow_axis, fast_axis)
        
        plt.show()

    def _plot_scan_axes(self, center_x: float, center_y: float, 
                   slow_axis: np.ndarray, fast_axis: np.ndarray,
                   scale: float = 100):
        """繪製掃描軸方向"""
        # 繪製慢軸（藍色）
        plt.arrow(center_x, center_y, 
                slow_axis[0] * scale, slow_axis[1] * scale,
                color='blue', width=2, head_width=10,
                label='Slow Axis')
                
        # 繪製快軸（紅色）
        plt.arrow(center_x, center_y,
                fast_axis[0] * scale, fast_axis[1] * scale,
                color='red', width=2, head_width=10,
                label='Fast Axis')
        
    def _draw_scan_area(self, params: dict):
        """
        繪製掃描範圍框架，確保與座標點旋轉方向一致
        
        Parameters
        ----------
        params : dict
            掃描參數，包含中心點座標、範圍和角度
        """
        half_range = params['scan_range'] / 2
        # 改變角度符號使旋轉方向一致（逆時針為正）
        angle_rad = np.radians(params['scan_angle'])
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)
        
        # 定義掃描範圍的四個角點（逆時針順序）
        corners = np.array([
            [-half_range, -half_range],  # 左下
            [half_range, -half_range],   # 右下
            [half_range, half_range],    # 右上
            [-half_range, half_range],   # 左上
            [-half_range, -half_range]   # 回到起點以封閉圖形
        ])
        
        # 旋轉並平移角點
        rotated_corners = np.zeros_like(corners)
        for i, (x, y) in enumerate(corners):
            # 使用標準的旋轉矩陣
            rotated_corners[i, 0] = x * cos_angle - y * sin_angle + params['scan_center_x']
            rotated_corners[i, 1] = x * sin_angle + y * cos_angle + params['scan_center_y']
        
        # 繪製掃描範圍和中心點
        plt.plot(rotated_corners[:, 0], rotated_corners[:, 1], 
                'k--', linewidth=1, label='Scan Area')
        plt.plot(params['scan_center_x'], params['scan_center_y'], 
                'r+', markersize=10, label='Scan Center')
    
    def _plot_measurement_sequence(self, coordinates: np.ndarray):
        """Plot points with color indicating measurement sequence"""
        n_points = len(coordinates)
        colors = plt.cm.viridis(np.linspace(0, 1, n_points))
        
        # Plot all points with sequential coloring
        for i, (x, y) in enumerate(coordinates):
            plt.plot(x, y, 'o', color=colors[i], markersize=4)
            
        # Highlight first and last points
        plt.plot(coordinates[0, 0], coordinates[0, 1], 'k*', 
                markersize=10, label='First Point')
        plt.plot(coordinates[-1, 0], coordinates[-1, 1], 'r*', 
                markersize=10, label='Last Point')
        
        # Add arrow to show scanning direction
        mid_point = len(coordinates) // 2
        plt.arrow(coordinates[mid_point, 0], coordinates[mid_point, 1],
                 coordinates[mid_point + 1, 0] - coordinates[mid_point, 0],
                 coordinates[mid_point + 1, 1] - coordinates[mid_point, 1],
                 head_width=2, head_length=4, fc='k', ec='k',
                 label='Scan Direction')
    
    def _set_plot_properties(self, params: dict):
        """
        設定圖表屬性和資訊顯示，將圖例放置在圖表內部適當位置
        
        Parameters
        ----------
        params : dict
            包含掃描參數的字典
        """
        plt.title('CITS Measurement Points and Scanning Sequence')
        plt.xlabel('X Position (nm)')
        plt.ylabel('Y Position (nm)')
        plt.axis('equal')
        plt.grid(True)
        
        # 將圖例放在圖表右上角的內部
        plt.legend(loc='upper right', bbox_to_anchor=(0.98, 0.98))
        
        # 計算總點數
        total_points = sum(area.nx * area.ny for area in params['local_areas'])
        
        # 建立資訊文字，放在圖表右側
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
    def _rotate_and_translate(points, angle, tx, ty):
        """Rotate points and translate them"""
        cos_angle = np.cos(angle)
        sin_angle = np.sin(angle)
        rotation_matrix = np.array([[cos_angle, sin_angle],
                                  [-sin_angle, cos_angle]])
        rotated = points @ rotation_matrix
        return rotated + np.array([tx, ty])
    
    @staticmethod
    def _print_coordinates_info(coordinates: np.ndarray):
        """Print coordinates in sequence"""
        print("\nCITS Measurement Points Sequence:")
        for i, (x, y) in enumerate(coordinates):
            print(f"Point {i+1}: ({x:.2f}, {y:.2f})")

def main():
    """Main test function"""
    test_params = {
        'scan_center_x': 250,
        'scan_center_y': 250,
        'scan_range': 500,
        'scan_angle': 80,
        'local_areas': [
            LocalCITSParams(
                start_x=125, start_y=125,
                dx=10, dy=10,
                nx=10, ny=10,
                scan_direction=1,
                startpoint_direction=1
            ),
            LocalCITSParams(
                start_x=125, start_y=125,
                dx=20, dy=20,
                nx=5, ny=5,
                scan_direction=1,
                startpoint_direction=-1
            ),
            LocalCITSParams(
                start_x=250, start_y=250,
                dx=30, dy=30,
                nx=5, ny=5,
                scan_direction=1,
                startpoint_direction=-1
            )
        ]
    }
    
    visualizer = LocalCITSVisualizer()
    visualizer.visualize_cits_points(test_params)

if __name__ == '__main__':
    main()