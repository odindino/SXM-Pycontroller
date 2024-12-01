class SXMParameters:
    """SXM參數定義"""
    
    # 參數範圍定義
    PARAM_RANGES = {
        'X': (-8000.0, 8000.0),     # nm
        'Y': (-8000.0, 8000.0),     # nm
        'Range': (0.1, 5000.0),     # nm
        'Scan': (0, 1),             # 0: off, 1: on
        'Angle': (-180.0, 180.0),   # degrees
        'Speed': (0.1, 10.0),       # lines/s
        'Pixel': [32, 64, 128, 250, 256, 500, 512, 1000, 1024],  # valid pixel values
        'PixelRatio': (0.1, 10.0),  # Pixel density ratio
        'AspectRatio': (0.1, 10.0)  # Image format ratio
    }
    
    # 回饋參數定義
    FEEDBACK_PARAMS = {
        'Enable': bool,      # 回饋開關
        'Mode': int,        # 回饋模式
        'Bias': float,      # 偏壓
        'Ki': float,        # 積分增益
        'Kp': float,        # 比例增益
        'PreAmp': int,      # 前置放大器範圍
        'BiasDiv': int,     # 偏壓分壓範圍
        'Ratio': float,     # STM/AFM比例
        'ZOffset': float,   # Z軸偏移
        'ZOffsetSlew': float  # Z軸偏移速率
    }
    
    # 掃描參數定義
    SCAN_PARAMS = {
        'Scan': bool,       # 掃描狀態
        'Range': float,     # 掃描範圍
        'Speed': float,     # 掃描速度
        'Pixel': int,       # 像素數
        'X': float,         # X位置
        'Y': float,         # Y位置
        'Angle': float,     # 掃描角度
        'LineNr': int,      # 當前掃描行數
        'AutoSave': int,    # 自動儲存
        'PixelRatio': float,   # Pixel density
        'AspectRatio': float,  # Image format
        'DriftX': float,    # X漂移補償
        'DriftY': float,    # Y漂移補償
        'Slope': int,       # 平面校正模式
        'SlopeX': float,    # X斜率校正
        'SlopeY': float     # Y斜率校正
    }