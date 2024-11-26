"""
STM STS Controller Module
提供完整的STS測量控制功能，包含單點測量和腳本執行

Author: Zi-Liang Yang
Version: 1.0.0
Date: 2024-11-26
"""

import time
import json
import threading
from typing import Optional, Dict, List, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import logging

@dataclass
class STSScript:
    """STS測量腳本數據結構"""
    name: str
    vds_list: List[float]
    vg_list: List[float]
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'STSScript':
        """從字典建立實例"""
        return cls(**data)

class STSController:
    """
    STS測量控制器
    負責管理和執行STS測量，包括單點測量和腳本執行
    """
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self._setup_logging()
        
        # 系統狀態
        self.measurement_active = False
        self.current_script: Optional[STSScript] = None
        self._abort_requested = False
        self._lock = threading.Lock()
        
        # 設定檔案路徑
        self.script_dir = Path("scripts")
        self.script_dir.mkdir(exist_ok=True)
        
        # 回調函數
        self.on_progress = None
        self.on_status_change = None
        
    def _setup_logging(self):
        """設定日誌記錄"""
        self.logger = logging.getLogger("STSController")
        self.logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def check_connection(self) -> bool:
        """
        檢查DDE連線狀態
        
        Returns:
            bool: 連線是否正常
        """
        try:
            self.execute_command("a := 0;")
            return True
        except Exception as e:
            self.logger.error(f"Connection check failed: {str(e)}")
            return False

    def execute_command(self, command: str) -> bool:
        """
        執行DDE命令並處理錯誤
        
        Args:
            command: DDE命令字串
            
        Returns:
            bool: 命令是否執行成功
        """
        max_retries = 3
        retry_delay = 1.0  # 秒
        
        for attempt in range(max_retries):
            try:
                if self._abort_requested:
                    raise Exception("Operation aborted by user")
                    
                # 確保連線存在
                if not hasattr(self, 'MySXM') or self.MySXM is None:
                    self._reinitialize_connection()
                    
                self.MySXM.SendWait(command)
                return True
                
            except Exception as e:
                self.logger.error(
                    f"Command execution failed (attempt {attempt + 1}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise
                
        return False

    def _reinitialize_connection(self):
        """重新初始化DDE連線"""
        try:
            import SXMRemote
            self.MySXM = SXMRemote.DDEClient("SXM", "Remote")
            self.logger.info("DDE connection reinitialized")
        except Exception as e:
            self.logger.error(f"Failed to reinitialize DDE: {str(e)}")
            raise

    def prepare_sts_measurement(self) -> bool:
        """
        準備STS測量環境
        
        Returns:
            bool: 準備是否成功
        """
        try:
            self._update_status("Preparing measurement...")
            
            # 設定自動儲存和關閉重複測量
            self.execute_command("SpectPara('AUTOSAVE', 1);")
            self.execute_command("SpectPara('Repeat', 0);")
            
            # 等待系統穩定
            time.sleep(0.5)
            
            self._update_status("Ready for measurement")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to prepare STS: {str(e)}")
            self._update_status("Preparation failed")
            return False

    def start_single_sts(self) -> bool:
        """
        執行單點STS測量
        
        Returns:
            bool: 測量是否成功
        """
        with self._lock:
            if self.measurement_active:
                raise RuntimeError("Measurement already in progress")
                
            self.measurement_active = True
            self._abort_requested = False
            
        try:
            if not self.prepare_sts_measurement():
                return False
                
            self._update_status("Executing STS measurement...")
            success = self.execute_command("SpectStart;")
            
            if success:
                # 等待測量完成
                time.sleep(2.0)
                self._update_status("Measurement completed")
                return True
            else:
                self._update_status("Measurement failed")
                return False
                
        except Exception as e:
            self.logger.error(f"STS measurement error: {str(e)}")
            self._update_status(f"Error: {str(e)}")
            return False
            
        finally:
            with self._lock:
                self.measurement_active = False

    def execute_sts_script(self, script: STSScript) -> bool:
        """
        執行STS測量腳本
        
        Args:
            script: STS測量腳本
            
        Returns:
            bool: 腳本是否執行成功
        """
        with self._lock:
            if self.measurement_active:
                raise RuntimeError("Measurement already in progress")
                
            self.measurement_active = True
            self._abort_requested = False
            self.current_script = script
            
        try:
            total_points = len(script.vds_list)
            self._update_status(f"Starting script: {script.name}")
            
            for i, (vds, vg) in enumerate(zip(script.vds_list, script.vg_list)):
                if self._abort_requested:
                    self._update_status("Measurement aborted by user")
                    return False
                    
                # 更新進度
                progress = (i + 1) / total_points * 100
                self._update_progress(progress)
                self._update_status(
                    f"Measuring point {i+1}/{total_points}: "
                    f"Vds={vds:.3f}V, Vg={vg:.3f}V"
                )
                
                # 設定偏壓並執行測量
                if not self.set_bias_and_measure(vds, vg):
                    raise Exception(f"Measurement failed at point {i+1}")
                    
                # 測量間隔
                if i < total_points - 1:
                    time.sleep(1.0)
                    
            self._update_status("Script completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Script execution error: {str(e)}")
            self._update_status(f"Script error: {str(e)}")
            return False
            
        finally:
            with self._lock:
                self.measurement_active = False
                self.current_script = None

    def set_bias_and_measure(self, vds: float, vg: float) -> bool:
        """
        設定偏壓並執行測量
        
        Args:
            vds: 源漏極電壓
            vg: 閘極電壓
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 這裡需要實作與SMU的整合
            # 暫時返回True作為示範
            return self.start_single_sts()
            
        except Exception as e:
            self.logger.error(f"Bias and measurement error: {str(e)}")
            return False

    def abort_measurement(self):
        """中止當前測量"""
        with self._lock:
            if self.measurement_active:
                self._abort_requested = True
                self._update_status("Aborting measurement...")

    def save_script(self, script: STSScript) -> bool:
        """
        儲存STS測量腳本
        
        Args:
            script: 要儲存的腳本
            
        Returns:
            bool: 是否儲存成功
        """
        try:
            file_path = self.script_dir / f"{script.name}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(script.to_dict(), f, indent=4)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save script: {str(e)}")
            return False

    def load_script(self, name: str) -> Optional[STSScript]:
        """
        載入STS測量腳本
        
        Args:
            name: 腳本名稱
            
        Returns:
            Optional[STSScript]: 載入的腳本，如果失敗則為None
        """
        try:
            file_path = self.script_dir / f"{name}.json"
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return STSScript.from_dict(data)
            
        except Exception as e:
            self.logger.error(f"Failed to load script: {str(e)}")
            return None

    def get_all_scripts(self) -> Dict[str, STSScript]:
        """
        獲取所有已儲存的腳本
        
        Returns:
            Dict[str, STSScript]: 腳本名稱到腳本對象的映射
        """
        scripts = {}
        for file_path in self.script_dir.glob("*.json"):
            name = file_path.stem
            script = self.load_script(name)
            if script:
                scripts[name] = script
        return scripts

    def _update_status(self, status: str):
        """更新狀態資訊"""
        self.logger.info(status)
        if self.on_status_change:
            self.on_status_change(status)

    def _update_progress(self, progress: float):
        """更新進度資訊"""
        if self.on_progress:
            self.on_progress(progress)