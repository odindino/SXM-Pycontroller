from SXMPyBase import SXMBase
import queue
import threading

class SXMEventListener(SXMBase):
    """
    處理SXM的事件監聽
    """
    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()
        self._event_queue = queue.Queue()
        self._start_event_listener()
        
    def _start_event_listener(self):
        """啟動事件監聽器"""
        self.event_listener = threading.Thread(
            target=self._event_listener_loop, 
            daemon=True
        )
        self.event_listener.start()
        
    def _event_listener_loop(self):
        """事件監聽迴圈"""
        while not self._stop_event.is_set():
            try:
                event = self._event_queue.get(timeout=0.1)
                self._process_event(event)
            except queue.Empty:
                continue
                
    def _process_event(self, event):
        """處理事件"""
        event_type = event.get('type')
        event_data = event.get('data')
        
        if self.debug_mode:
            print(f"處理事件: {event_type}")