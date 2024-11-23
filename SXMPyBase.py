import time
class SXMBase:
    """
    SXM控制器的基礎類別
    包含基本的DDE連接和共享資料
    """
    def __init__(self):
        self.MySXM = None
        self.debug_mode = False
        
        # 掃描參數
        self.x = None          # X位置 (nm)
        self.y = None          # Y位置 (nm)
        self.range = None      # 掃描範圍 (nm)
        self.angle = None      # 掃描角度 (degrees)
        self.scan_state = None # 掃描狀態
        self.pixels = None     # 像素數
        self.speed = None      # 掃描速度
        
        # 時間戳記
        self.last_update = None  # 最後更新時間
        
    def _update_parameter(self, param_name, value):
        """
        更新參數值並記錄時間戳記
        """
        if hasattr(self, param_name):
            setattr(self, param_name, value)
            self.last_update = time.time()