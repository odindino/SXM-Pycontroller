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