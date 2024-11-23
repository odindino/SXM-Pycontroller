import threading
import queue
import datetime
from .SXMPyBase import SXMBase

class ScanStatus:
    """掃描狀態的數據類別"""
    def __init__(self):
        self.is_scanning = False
        self.direction = None
        self.line_number = 0
        self.total_lines = 0
        self.last_saved_file = None
        self.scan_finished_time = None
        self.missed_callbacks = []
        self._lock = threading.Lock()

    def update(self, **kwargs):
        """線程安全的狀態更新"""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)

    def __str__(self):
        with self._lock:
            status = "Scanning" if self.is_scanning else "Not scanning"
            details = []
            if self.is_scanning and self.direction:
                details.append(f"{self.direction} line {self.line_number}")
            if self.last_saved_file:
                details.append(f"Last saved: {self.last_saved_file}")
            if self.scan_finished_time:
                details.append(f"Finished at: {self.scan_finished_time}")
            return f"{status} " + " - ".join(details) if details else status

class SXMEventHandler(SXMBase):
    """事件處理器類別"""
    def __init__(self, debug_mode=False):
        super().__init__(debug_mode)
        self.scan_status = ScanStatus()
        self.event_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._event_listener = None
        self._initialize_callbacks()
        self._start_event_listener()

    def _initialize_callbacks(self):
        """初始化回調函數"""
        self.MySXM.ScanOffCallBack = self._handle_scan_off
        self.MySXM.SaveIsDone = self._handle_save_done
        self.MySXM.ScanOnCallBack = self._handle_scan_on

    def _start_event_listener(self):
        """啟動事件監聽器"""
        self._event_listener = threading.Thread(
            target=self._event_listener_loop,
            daemon=True
        )
        self._event_listener.start()

    def _event_listener_loop(self):
        """事件監聽迴圈"""
        while not self._stop_event.is_set():
            try:
                event = self.event_queue.get(timeout=0.1)
                self._process_event(event)
            except queue.Empty:
                continue
            except Exception as e:
                if self.debug_mode:
                    print(f"Event listener error: {str(e)}")

    def _process_event(self, event):
        """處理事件"""
        event_type = event.get('type')
        event_data = event.get('data')

        if event_type == 'scan_off':
            self._process_scan_off(event_data)
        elif event_type == 'save_done':
            self._process_save_done(event_data)
        elif event_type == 'scan_on':
            self._process_scan_on(event_data)

    def _handle_scan_off(self):
        """掃描結束回調"""
        self.event_queue.put({
            'type': 'scan_off',
            'data': {'time': datetime.datetime.now()}
        })

    def _handle_save_done(self, filename):
        """檔案儲存回調"""
        self.event_queue.put({
            'type': 'save_done',
            'data': {'filename': filename}
        })

    def _handle_scan_on(self):
        """掃描開始回調"""
        self.event_queue.put({
            'type': 'scan_on',
            'data': {'time': datetime.datetime.now()}
        })

    def _process_scan_off(self, data):
        """處理掃描結束事件"""
        self.scan_status.update(
            is_scanning=False,
            direction=None,
            line_number=0,
            scan_finished_time=data['time']
        )
        if self.debug_mode:
            print(f"Scan finished at {data['time']}")

    def _process_save_done(self, data):
        """處理檔案儲存事件"""
        self.scan_status.update(last_saved_file=data['filename'])
        if self.debug_mode:
            print(f"File saved: {data['filename']}")

    def _process_scan_on(self, data):
        """處理掃描開始事件"""
        self.scan_status.update(
            is_scanning=True,
            scan_finished_time=None
        )
        if self.debug_mode:
            print(f"Scan started at {data['time']}")

    def get_scan_history(self):
        """獲取掃描歷史記錄"""
        with self.scan_status._lock:
            return {
                'last_scan_finished': self.scan_status.scan_finished_time,
                'last_saved_file': self.scan_status.last_saved_file,
                'missed_callbacks': self.scan_status.missed_callbacks.copy()
            }

    def stop_monitoring(self):
        """停止事件監聽"""
        self._stop_event.set()
        if self._event_listener:
            self._event_listener.join(timeout=1.0)