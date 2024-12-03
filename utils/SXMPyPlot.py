import plotly.graph_objects as go
from SXMPyCalc import LocalCITSCalculator, LocalCITSParams, AutoMoveCalculator
import numpy as np
import matplotlib.cm as cm
from typing import Tuple

class LocalCITSPreviewer:
    """
    Local CITS Plotting Utility using Plotly for Interactive Visualizations.
    """

    @staticmethod
    def visualize_cits_points(params: dict) -> go.Figure:
        """
        Visualize Local CITS Measurement Points and Scanning Sequence.
        """
        # Calculate coordinates and scan parameters
        coordinates, _, _, (slow_axis, fast_axis) = LocalCITSCalculator.combi_local_cits_coordinates(
            params['scan_center_x'],
            params['scan_center_y'],
            params['scan_range'],
            params['scan_angle'],
            params['total_lines'],
            params['scan_direction'],
            params['local_areas']
        )

        # Calculate scanline distribution
        scanline_info = LocalCITSCalculator.calculate_local_scanline_distribution(
            coordinates,
            params['scan_center_x'],
            params['scan_center_y'],
            params['scan_angle'],
            params['scan_range'],
            params['scan_direction'],
            params['total_lines']
        )

        # Create a figure
        fig = go.Figure()

        # Add scan area
        LocalCITSPreviewer._add_scan_area(fig, params)

        # Add scan lines with color variation and customized legend labels
        LocalCITSPreviewer._add_scan_lines(fig, params, scanline_info)

        # Add measurement points
        LocalCITSPreviewer._add_measurement_points(fig, coordinates)

        # Add axes
        LocalCITSPreviewer._add_scan_axes(fig, params['scan_center_x'], params['scan_center_y'], slow_axis, fast_axis)

        # Configure layout to focus on scan area
        fig.update_layout(
            title='Local CITS Measurement Points and Scanning Sequence',
            xaxis_title='X Position (nm)',
            yaxis_title='Y Position (nm)',
            xaxis=dict(scaleanchor="y", showgrid=True, range=[params['scan_center_x'] - params['scan_range'], params['scan_center_x'] + params['scan_range']]),
            yaxis=dict(showgrid=True, range=[params['scan_center_y'] - params['scan_range'], params['scan_center_y'] + params['scan_range']]),
            showlegend=True,
            template="plotly_white"
        )

        # Show figure directly
        fig.show()

        return fig

    @staticmethod
    def _add_scan_area(fig, params: dict):
        """Add scan area boundary to the figure."""
        half_slow_range = params['scan_range'] / 2  # 慢軸為輸入的掃描範圍的一半
        half_fast_range = half_slow_range * params['aspect_ratio']  # 快軸範圍為慢軸範圍乘以 aspect_ratio
        angle_rad = np.radians(params['scan_angle'])
        corners = np.array([
            [-half_fast_range, -half_slow_range],
            [half_fast_range, -half_slow_range],
            [half_fast_range, half_slow_range],
            [-half_fast_range, half_slow_range],
            [-half_fast_range, -half_slow_range]
        ])
        rotation_matrix = np.array([
            [np.cos(angle_rad), -np.sin(angle_rad)],
            [np.sin(angle_rad), np.cos(angle_rad)]
        ])
        rotated_corners = np.dot(corners, rotation_matrix.T) + np.array([params['scan_center_x'], params['scan_center_y']])
        fig.add_trace(go.Scatter(
            x=rotated_corners[:, 0],
            y=rotated_corners[:, 1],
            mode='lines',
            line=dict(dash='dash', color='black'),
            name='Scan Area'
        ))

    @staticmethod
    def _add_scan_lines(fig, params: dict, scanline_info: Tuple[list, list]):
        """Add scan lines to the figure with color differentiation and proper labels."""
        scanline_distribution, _ = scanline_info
        print(f"scanline_distribution: {scanline_distribution}")

        # Correct ranges for scan area
        half_slow_range = params['scan_range'] / 2  # 慢軸較長
        half_fast_range = half_slow_range * params['aspect_ratio']  # 快軸較短
        total_lines = sum(scanline_distribution)
        line_spacing = (2 * half_slow_range) / total_lines  # Corrected to match the scan range limits

        # Set initial position for scanning, starting from the correct edge based on scan direction
        current_y = -half_slow_range if params['scan_direction'] == 1 else half_slow_range

        angle_rad = np.radians(params['scan_angle'])
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)

        # Set up color mapping for scan lines with a more distinct color palette
        colors = cm.jet(np.linspace(0, 1, total_lines))

        current_y_offset = current_y

        for idx, step_count in enumerate(scanline_distribution):

            # Update position for the next scan line, considering direction
            current_y_offset += (step_count * line_spacing) * params['scan_direction']
            print(f"current_y_offset: {current_y_offset}")

            # Calculate line start and end points along the fast axis
            start_x = -half_fast_range
            end_x = half_fast_range

            # Rotate and translate endpoints for each scan line based on current_y_offset
            start_rotated_x = start_x * cos_angle - current_y_offset * sin_angle + params['scan_center_x']
            start_rotated_y = start_x * sin_angle + current_y_offset * cos_angle + params['scan_center_y']

            end_rotated_x = end_x * cos_angle - current_y_offset * sin_angle + params['scan_center_x']
            end_rotated_y = end_x * sin_angle + current_y_offset * cos_angle + params['scan_center_y']

            # Draw the scan line with varying color and add label for legend
            fig.add_trace(go.Scatter(
                x=[start_rotated_x, end_rotated_x],
                y=[start_rotated_y, end_rotated_y],
                mode='lines',
                line=dict(color=f'rgba({colors[idx][0]*255}, {colors[idx][1]*255}, {colors[idx][2]*255}, 0.8)', width=1, dash='solid'),
                name=f'Scan Line {step_count}'
            ))

            

    @staticmethod
    def _add_measurement_points(fig, coordinates: np.ndarray):
        """Add measurement points to the figure."""
        fig.add_trace(go.Scatter(
            x=coordinates[:, 0],
            y=coordinates[:, 1],
            mode='markers',
            marker=dict(size=4, color=np.arange(len(coordinates)), colorscale='Viridis'),
            name='Measurement Points'
        ))

        # Mark the first and last points
        fig.add_trace(go.Scatter(
            x=[coordinates[0, 0], coordinates[-1, 0]],
            y=[coordinates[0, 1], coordinates[-1, 1]],
            mode='markers+text',
            marker=dict(size=10, color=['black', 'red']),
            text=['First Point', 'Last Point'],
            textposition='top center',
            name='Start/End Points'
        ))

    @staticmethod
    def _add_scan_axes(fig, center_x, center_y, slow_axis, fast_axis, scale=100):
        """Add scan axes to the figure."""
        # Slow axis should match the longer range
        fig.add_trace(go.Scatter(
            x=[center_x, center_x + slow_axis[0] * scale],
            y=[center_y, center_y + slow_axis[1] * scale],
            mode='lines+text',
            line=dict(color='blue', width=2),
            name='Slow Axis'
        ))

        # Fast axis should match the shorter range
        fig.add_trace(go.Scatter(
            x=[center_x, center_x + fast_axis[0] * scale],
            y=[center_y, center_y + fast_axis[1] * scale],
            mode='lines+text',
            line=dict(color='red', width=2),
            name='Fast Axis'
        ))


class AutoMovePreviewer:
    """
    AutoMovePreviewer: A class for visualizing the movement of scan centers using Plotly.
    """

    def __init__(self, movement_script: str, distance: float, center_x: float, center_y: float, angle: float, debug_mode: bool = False):
        """
        Initialize the AutoMovePreviewer.

        Parameters
        ----------
        movement_script : str
            Movement command sequence, e.g., "RULLDDRR" (R: right, L: left, U: up, D: down).
        distance : float
            Movement distance for each step (in nm).
        center_x : float
            Starting X coordinate of the scan center.
        center_y : float
            Starting Y coordinate of the scan center.
        angle : float
            Current scan angle (degrees).
        debug_mode : bool, optional
            Enable or disable debug mode (default is False).
        """
        self.movement_script = movement_script
        self.distance = distance
        self.center_x = center_x
        self.center_y = center_y
        self.angle = angle
        self.debug_mode = debug_mode
        self.positions = self.calculate_positions()

    def calculate_positions(self):
        """
        Calculate all the positions for the given movement script using AutoMoveCalculator's auto_move method.

        Returns
        -------
        List[Tuple[float, float]]
            List of all positions as (x, y) coordinates.
        """
        # 利用 AutoMoveCalculator 計算移動的所有座標
        positions = AutoMoveCalculator.auto_move(
            movement_script=self.movement_script,
            distance=self.distance,
            center_x=self.center_x,
            center_y=self.center_y,
            angle=self.angle,
            debug_mode=self.debug_mode
        )
        return positions

    def plot_movements(self):
        """
        Plot the movement of the scan center using Plotly.
        """
        # 將所有的 x, y 座標分離出來以繪製
        x_coords, y_coords = zip(*self.positions)

        # 建立圖形對象
        fig = go.Figure()

        # 添加移動路徑的線條和標記
        fig.add_trace(go.Scatter(
            x=x_coords,
            y=y_coords,
            mode='lines+markers',
            line=dict(color='blue', width=2),
            marker=dict(size=6, color='red'),
            name='Movement Path'
        ))

        # 添加起點和終點標記
        fig.add_trace(go.Scatter(
            x=[x_coords[0], x_coords[-1]],
            y=[y_coords[0], y_coords[-1]],
            mode='markers+text',
            marker=dict(size=10, color=['green', 'red']),
            text=['Start', 'End'],
            textposition='top center',
            name='Start/End Points'
        ))

        # 設定圖表佈局
        fig.update_layout(
            title='Auto Movement Path Preview',
            xaxis_title='X Position (nm)',
            yaxis_title='Y Position (nm)',
            xaxis=dict(showgrid=True),
            yaxis=dict(showgrid=True),
            showlegend=True,
            template="plotly_white"
        )

        # 顯示圖形
        fig.show()

# 測試 AutoMovePreviewer 的範例使用方法
if __name__ == "__main__":
    # 使用範例參數建立 AutoMovePreviewer 實例
    movement_script = "UUUUUUUUU"  # 移動腳本
    distance = 200  # 每次移動距離（單位：nm）
    center_x = 2100  # 起始位置 X
    center_y = 500  # 起始位置 Y
    angle = 0  # 移動的角度（度）

    previewer = AutoMovePreviewer(movement_script, distance, center_x, center_y, angle, debug_mode=True)
    previewer.plot_movements()





# def main():
#     """Generate interactive plot for Local CITS visualization with corrected axes and scanline directions."""
#     # Example parameters
#     params = {
#         'scan_center_x': 0,
#         'scan_center_y': 0,
#         'scan_range': 1000,
#         'scan_angle': 0,
#         'total_lines': 1000,
#         'scan_direction': -1,
#         'aspect_ratio': 0.5,  # Example aspect ratio (less than or equal to 1)
#         'local_areas': [
#             LocalCITSParams(
#                 start_x=125, start_y=125,
#                 dx=0.1, dy=0.1,
#                 nx=5, ny=20,
#                 startpoint_direction=1
#             ),
#             LocalCITSParams(
#                 start_x=0, start_y=0,
#                 dx=20, dy=30,
#                 nx=5, ny=5,
#                 startpoint_direction=-1
#             ),
#             LocalCITSParams(
#                 start_x=230, start_y=180,
#                 dx=40, dy=40,
#                 nx=3, ny=3,
#                 startpoint_direction=-1
#             )
#         ]
#     }

#     # Generate the figure
#     plotter = LocalCITSPreviewer()
#     plotter.visualize_cits_points(params)

# if __name__ == "__main__":
#     main()

