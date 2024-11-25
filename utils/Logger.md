# Logger 程式說明文件

## 1. 概述

### 1.1 設計目的
Logger 系統的主要目的是提供一個通用的函式追蹤和記錄系統，可以：
- 追蹤程式執行過程中的函式呼叫順序
- 記錄所有 print 輸出的內容
- 定期提供時間戳記以便追蹤執行時間
- 協助開發者在程式出現問題時快速定位原因

### 1.2 核心功能
- **函式追蹤**：記錄函式的進入和退出
- **Print 輸出記錄**：將所有 print 內容保存到日誌檔案
- **時間戳記**：定期記錄執行狀態
- **智能過濾**：只追蹤重要的公開函式

## 2. 類別結構

### 2.1 Logger 類別
這是整個系統的核心類別，負責所有日誌記錄功能。

```python
class Logger:
    def __init__(self, 
                 log_dir: str = "logs",
                 tracking_interval: int = 5,
                 enable_print_log: bool = True):
```

#### 初始化參數說明：
| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| log_dir | str | "logs" | 日誌檔案的存放目錄 |
| tracking_interval | int | 5 | 記錄時間戳記的間隔（秒）|
| enable_print_log | bool | True | 是否要記錄 print 輸出 |

### 2.2 主要屬性
| 屬性名稱 | 類型 | 說明 |
|----------|------|------|
| log_dir | Path | 日誌目錄路徑 |
| timestamp | str | 日誌檔案的時間戳記 |
| func_logger | Logger | 函式追蹤的日誌記錄器 |
| print_logger | Logger | print 輸出的日誌記錄器 |
| active_functions | Set[str] | 目前執行中的函式集合 |
| is_tracking | bool | 追蹤狀態標記 |
| original_stdout | TextIO | 原始的標準輸出 |
## 3. 核心功能實作

### 3.1 日誌記錄器設定
```python
def _setup_logger(self, name: str, filename: str) -> logging.Logger:
```

這個方法負責建立和配置個別的日誌記錄器。

#### 關鍵實作細節：
1. 使用 `logging.getLogger()` 建立唯一的記錄器
2. 設定日誌格式為含時間戳記的格式
3. 設定檔案處理器以寫入日誌檔案

#### 方法參數：
| 參數 | 類型 | 說明 |
|------|------|------|
| name | str | 記錄器名稱 |
| filename | str | 日誌檔案名稱 |

### 3.2 Print 輸出重導向
```python
def _setup_print_redirect(self):
```

#### 實作原理：
1. 保存原始的 `sys.stdout`
2. 建立自訂的輸出重導向器類別 `PrintRedirector`
3. 重導向 `sys.stdout` 到自訂的重導向器

#### 重導向器程式碼：
```python
class PrintRedirector:
    def write(self, message):
        # 同時輸出到原始 stdout 和日誌
        self.original_stdout.write(message)
        if message.strip():
            self.logger.info(message.rstrip())
```

### 3.3 函式追蹤系統
```python
def _start_tracking_thread(self):
```

#### 執行緒運作邏輯：
1. 每 0.1 秒檢查一次是否需要記錄時間戳記
2. 當到達指定間隔時，記錄當前時間和執行中的函式
3. 使用 daemon 執行緒確保程式結束時自動關閉

#### 關鍵程式碼：
```python
def tracking_loop():
    while self.is_tracking:
        current_time = time.time()
        if current_time - self.last_log_time >= self.tracking_interval:
            self._log_timestamp()
            self.last_log_time = current_time
        time.sleep(0.1)
```
## 4. 裝飾器實作

### 4.1 函式追蹤裝飾器
```python
@wraps(func)
def track_function(func):
    def wrapper(*args, **kwargs):
        if not func.__name__.startswith('_'):
            logger = get_logger()
            logger.log_function_enter(func.__name__)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                logger.log_function_exit(func.__name__)
        else:
            return func(*args, **kwargs)
    return wrapper
```

#### 裝飾器工作原理：
1. 使用 `wraps` 保留原始函式的資訊
2. 檢查函式名稱是否以底線開頭
3. 記錄函式的進入和退出
4. 確保即使發生異常也能正確記錄函式退出

## 5. 使用方式

### 5.1 基本使用
```python
from utils.logger import get_logger, track_function

# 在要追蹤的函式上加上裝飾器
@track_function
def your_function():
    pass

# 初始化（可選）
logger = get_logger()

# 程式結束時
logger.stop()
```

### 5.2 日誌檔案格式
系統會產生兩種日誌檔案：

1. 函式追蹤日誌（`function_YYYYMMDD_HHMMSS.log`）：
```
2024-01-24 14:03:06 - 進入函式：test
2024-01-24 14:03:06 - 進入函式：auto_move_scan_area
2024-01-24 14:03:06 - 進入函式：get_position
...
```

2. Print 輸出日誌（`print_YYYYMMDD_HHMMSS.log`）：
```
2024-01-24 14:03:06 - Starting auto move scan
2024-01-24 14:03:06 - Movement script: RULD
2024-01-24 14:03:06 - Distance: 20.0 nm
...
```

### 5.3 時間戳記格式
```
=== 時間戳記 2024-01-24 14:03:06.123 ===
目前執行函式：function1 -> function2 -> function3
```
## 6. 使用建議

### 6.1 應追蹤的函式
- 重要的邏輯函式
- 關鍵的控制流程函式
- 可能出錯的複雜操作

例如：
```python
@track_function
def auto_move_scan_area(self):
    """重要的掃描控制函式"""
    pass

@track_function
def perform_measurement(self):
    """關鍵的測量操作"""
    pass
```

### 6.2 不需追蹤的函式
- 私有輔助函式（以底線開頭）
- 簡單的 getter/setter
- 外部庫函式

例如：
```python
def _calculate_position(self):
    """不需追蹤的內部輔助函式"""
    pass

@property
def current_position(self):
    """簡單的屬性存取器"""
    return self._position
```

## 7. 注意事項

### 7.1 性能考慮
- 使用 daemon 執行緒減少資源佔用
- 智能過濾減少不必要的記錄
- 使用緩衝區處理 print 輸出

### 7.2 安全性考慮
- 正確處理檔案開啟和關閉
- 使用 try-finally 確保資源釋放
- 線程安全的日誌記錄

## 8. 擴展性

系統設計允許以下擴展：

### 8.1 新增日誌類型
```python
class CustomLogger(Logger):
    def __init__(self):
        super().__init__()
        self.custom_logger = self._setup_logger(
            "custom",
            f"custom_{self.timestamp}.log"
        )
```

### 8.2 自訂過濾規則
```python
def custom_filter(func_name: str) -> bool:
    """自訂的函式過濾規則"""
    return not func_name.startswith('_') and \
           not func_name.endswith('_helper')
```

### 8.3 修改記錄格式
```python
handler.setFormatter(
    logging.Formatter('%(asctime)s - [%(levelname)s] %(message)s')
)
```

## 9. 錯誤處理

### 9.1 常見問題與解決方案

| 問題 | 可能原因 | 解決方案 |
|------|----------|----------|
| 日誌檔案無法建立 | 權限問題 | 確認目錄存取權限 |
| 日誌記錄不完整 | 程式異常結束 | 使用 try-finally 確保正確關閉 |
| 記憶體使用過高 | 追蹤過多函式 | 調整追蹤範圍 |

### 9.2 除錯建議
1. 檢查日誌檔案是否正確建立
2. 確認時間戳記是否正常記錄
3. 驗證函式追蹤的完整性