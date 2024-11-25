# Keysight B2902B SMU 控制函式庫說明文件

## 目錄

1. [基本介紹](#基本介紹)
2. [系統需求與安裝](#系統需求與安裝)
3. [核心概念](#核心概念)
4. [程式架構](#程式架構)
5. [類別與函式完整說明](#類別與函式完整說明)
6. [使用範例](#使用範例)
7. [故障排除](#故障排除)

## 基本介紹

### 函式庫目的
這個函式庫的開發目的是為了提供一個安全且易於使用的介面，用於控制 Keysight B2902B Source Measure Unit (SMU)。SMU 是一種精密的量測儀器，能夠同時作為電壓/電流源和量測設備，常用於半導體元件特性的量測。

### 主要功能
- 建立與 SMU 的通訊連線
- 控制電壓/電流輸出
- 執行精確的電氣量測
- 錯誤處理與安全保護
- 系統狀態監控
- 詳細的操作記錄

### 設計理念
1. **安全性優先**：
   - 所有操作都有完整的錯誤檢查
   - 異常情況下會自動關閉輸出
   - 內建多重保護機制

2. **易用性**：
   - 直覺的函式命名
   - 完整的型別提示
   - 豐富的使用範例

3. **可靠性**：
   - 完整的錯誤處理
   - 詳細的操作記錄
   - 狀態監控機制

## 系統需求與安裝

### 軟體需求
```plaintext
Python >= 3.7
pyvisa >= 1.11.0
pyvisa-py >= 0.5.2
```

### 硬體需求
- Keysight B2902B SMU
- 支援以下任一連線方式：
  - 網路連線（LAN）
  - USB 連線
- 支援 VISA 的電腦系統

### 安裝步驟

1. **安裝 Python 套件**
```bash
# 安裝 pyvisa 和 pyvisa-py
pip install pyvisa pyvisa-py
```

2. **函式庫檔案放置**
```plaintext
your_project/
├── utils/
│   └── KB2902BSMU.py  # 將函式庫檔案放在這裡
└── your_script.py
```

3. **VISA 位址設定**
- LAN 連線：`TCPIP0::<IP_ADDRESS>::inst0::INSTR`
  - 例如：`TCPIP0::172.30.32.98::inst0::INSTR`
- USB 連線：`USB0::0x0957::0x8B18::<SERIAL_NUMBER>::0::INSTR`
  - 例如：`USB0::0x0957::0x8B18::MY12345678::0::INSTR`

## 核心概念

### 列舉類別說明

#### Channel 列舉
```python
class Channel(Enum):
    CH1 = 1  # SMU 通道 1
    CH2 = 2  # SMU 通道 2
```

這個列舉類別定義了 SMU 的兩個通道。使用列舉而不是直接使用數字的原因：
1. **型別安全**：避免使用者輸入無效的通道號碼
2. **程式碼提示**：IDE 可以提供自動完成
3. **可讀性**：程式碼更容易理解
4. **維護性**：集中管理通道定義

#### OutputMode 列舉
```python
class OutputMode(Enum):
    VOLTAGE = 'VOLT'  # 電壓輸出模式
    CURRENT = 'CURR'  # 電流輸出模式
```

定義 SMU 的輸出模式：
1. **VOLTAGE**：電壓源模式
   - 設定電壓值
   - 限制（compliance）為電流值
2. **CURRENT**：電流源模式
   - 設定電流值
   - 限制（compliance）為電壓值

### 異常類別說明

```python
class ConnectionError(Exception):
    """連線相關錯誤
    
    當發生以下情況時拋出：
    1. VISA 資源名稱無效
    2. 無法建立連線
    3. 通訊逾時
    4. 連線意外中斷
    """
    pass

class MeasurementError(Exception):
    """測量相關錯誤
    
    當發生以下情況時拋出：
    1. 測量範圍溢出
    2. 達到 compliance 限制
    3. 測量數據無效
    4. 測量時發生通訊錯誤
    """
    pass
```

這些自訂異常類別有助於：
- 區分不同類型的錯誤
- 提供更準確的錯誤訊息
- 方便進行特定類型的錯誤處理

### 記錄器設定
函式庫使用 Python 內建的 `logging` 模組來記錄操作和錯誤：

```python
# 記錄器配置
self.logger = logging.getLogger(__name__)
self.logger.setLevel(logging.INFO)

# 記錄格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 記錄等級
- DEBUG：詳細的除錯資訊
- INFO：一般操作資訊
- WARNING：警告訊息
- ERROR：錯誤訊息
- CRITICAL：嚴重錯誤
```
## 類別與函式完整說明

### KeysightB2902B 類別

#### 初始化函式
```python
def __init__(self, resource_name: str = None, timeout: int = 10000):
    """初始化 SMU 控制器
    
    這個函式會建立 SMU 控制器的實例，但不會立即建立連線。連線需要另外呼叫 connect() 函式。
    
    參數:
        resource_name (str, optional): VISA 資源名稱
            - LAN 連線格式: 'TCPIP0::<IP_ADDRESS>::inst0::INSTR'
            - USB 連線格式: 'USB0::0x0957::0x8B18::<SERIAL_NUMBER>::0::INSTR'
            - 可以在初始化時提供，或之後在 connect() 時提供
        
        timeout (int): 通訊超時時間（毫秒）
            - 預設值: 10000 (10秒)
            - 建議值: 一般操作 5000-10000，長時間測量 30000+
    
    屬性初始化:
        self.resource_name: 儲存 VISA 資源名稱
        self.timeout: 儲存超時設定
        self.smu: 儲存 VISA 資源物件（初始為 None）
        self.logger: 設定記錄器
        
    使用範例:
        >>> # 基本初始化
        >>> smu = KeysightB2902B('TCPIP0::172.30.32.98::inst0::INSTR')
        
        >>> # 使用自訂超時時間
        >>> smu = KeysightB2902B(
        ...     'TCPIP0::172.30.32.98::inst0::INSTR',
        ...     timeout=30000
        ... )
        
    注意事項:
        1. 初始化不會檢查資源名稱的有效性
        2. 不會實際建立連線
        3. 超時時間建議根據操作類型調整
    """
```

#### 連線管理函式

##### connect
```python
def connect(self, resource_name: str = None) -> bool:
    """建立與 SMU 的連線
    
    這個函式執行連線建立的完整流程，包括：
    1. 建立 VISA 資源管理器
    2. 開啟與儀器的連線
    3. 重設儀器狀態
    4. 清除錯誤佇列
    5. 驗證儀器識別
    
    參數:
        resource_name (str, optional): VISA 資源名稱
            - 如果在初始化時已提供，可以省略
            - 如果提供，會覆蓋初始化時的設定
    
    返回:
        bool: 連線是否成功
    
    異常:
        ConnectionError: 當連線失敗時拋出，可能原因包括：
            - VISA 資源名稱無效
            - 儀器未開機或無法連線
            - 通訊逾時
            
    內部操作流程:
        1. 建立資源管理器：
           rm = pyvisa.ResourceManager()
        
        2. 開啟資源：
           self.smu = rm.open_resource(self.resource_name)
        
        3. 設定超時：
           self.smu.timeout = self.timeout
        
        4. 重設儀器：
           self.smu.write("*RST")
        
        5. 清除狀態：
           self.smu.write("*CLS")
        
        6. 驗證連線：
           idn = self.smu.query("*IDN?")
    
    使用範例:
        >>> smu = KeysightB2902B()
        >>> try:
        ...     smu.connect('TCPIP0::172.30.32.98::inst0::INSTR')
        ...     print("Connected successfully")
        ... except ConnectionError as e:
        ...     print(f"Connection failed: {e}")
    
    注意事項:
        1. 建議使用 try-except 來處理可能的連線錯誤
        2. 連線成功後，記得在適當時機呼叫 disconnect()
        3. 可以使用 with 語句來自動管理連線生命週期
    """
```

##### disconnect
```python
def disconnect(self):
    """安全地中斷與 SMU 的連線
    
    這個函式執行完整的關閉程序，確保：
    1. 所有輸出都被關閉
    2. 資源被正確釋放
    3. 連線狀態被重設
    
    無參數
    
    無返回值
    
    內部操作流程:
        1. 關閉所有通道輸出：
           for channel in Channel:
               self.disable_output(channel)
        
        2. 關閉 VISA 資源：
           self.smu.close()
        
        3. 重設連線狀態：
           self.smu = None
    
    使用範例:
        >>> smu.disconnect()
    
    注意事項:
        1. 即使發生錯誤，也會嘗試關閉所有輸出
        2. 建議在程式結束前呼叫此函式
        3. 使用 with 語句可以自動處理 disconnect
    """
```

##### check_connection
```python
def check_connection(self) -> bool:
    """檢查與 SMU 的連線狀態
    
    這個函式會：
    1. 檢查連線物件是否存在
    2. 嘗試與儀器通訊
    3. 驗證回應是否正確
    
    無參數
    
    返回:
        bool: 連線是否正常
            - True: 連線正常且可以通訊
            - False: 連線不存在或無法通訊
    
    內部操作流程:
        1. 檢查連線物件：
           if not self.smu:
               return False
        
        2. 嘗試通訊：
           try:
               self.smu.query("*IDN?")
               return True
           except:
               return False
    
    使用範例:
        >>> if smu.check_connection():
        ...     print("Connection is good")
        ... else:
        ...     print("Connection is lost")
    
    注意事項:
        1. 這是一個非侵入式的檢查，不會改變儀器狀態
        2. 建議在重要操作前檢查連線狀態
        3. 可能會有短暫的通訊延遲
    """
```
#### 配置與控制函式

##### configure_source
```python
def configure_source(self,
                    channel: Channel,
                    mode: OutputMode,
                    level: float,
                    compliance: float,
                    auto_range: bool = True) -> bool:
    """配置 SMU 的輸出參數
    
    這個函式用於設定 SMU 的輸出模式和相關參數，包括：
    - 輸出模式（電壓/電流）
    - 輸出等級
    - 限制值（compliance）
    - 量程設定
    
    參數:
        channel (Channel): 要配置的通道
            Channel.CH1: 通道 1
            Channel.CH2: 通道 2
            
        mode (OutputMode): 輸出模式
            OutputMode.VOLTAGE: 電壓源模式
            OutputMode.CURRENT: 電流源模式
            
        level (float): 輸出等級
            電壓模式: 單位為 V，範圍 ±210V
            電流模式: 單位為 A，範圍 ±3.03A
            
        compliance (float): 限制值
            電壓模式時: 電流限制值（A）
            電流模式時: 電壓限制值（V）
            
        auto_range (bool): 是否啟用自動量程
            True: 自動選擇最適合的量程（預設）
            False: 使用固定量程
    
    返回:
        bool: 配置是否成功
    
    內部操作流程:
        1. 設定源模式：
           :SOUR{CH}:FUNC:MODE {MODE}
        
        2. 設定輸出值：
           :SOUR{CH}:{MODE} {level}
        
        3. 設定限制值：
           :SENS{CH}:{comp_mode}:PROT {compliance}
        
        4. 配置量程：
           :SOUR{CH}:{MODE}:RANG:AUTO {ON|OFF}
    
    使用範例:
        >>> # 配置為 1V 電壓源，限制電流 100mA
        >>> smu.configure_source(
        ...     channel=Channel.CH1,
        ...     mode=OutputMode.VOLTAGE,
        ...     level=1.0,
        ...     compliance=0.1
        ... )
        
        >>> # 配置為 10mA 電流源，限制電壓 5V，固定量程
        >>> smu.configure_source(
        ...     Channel.CH2,
        ...     OutputMode.CURRENT,
        ...     0.01,
        ...     5.0,
        ...     auto_range=False
        ... )
    
    注意事項:
        1. 電壓/電流值不要超過儀器規格
        2. Compliance 值要設定適當，避免損壞待測元件
        3. 使用固定量程可能會影響測量精確度
        4. 配置時輸出不會自動開啟，需要另外呼叫 enable_output
    """
```

##### enable_output
```python
def enable_output(self, channel: Channel) -> bool:
    """開啟指定通道的輸出
    
    這個函式用於安全地開啟 SMU 的輸出。包含以下安全機制：
    1. 檢查連線狀態
    2. 確認輸出配置正確
    3. 等待輸出穩定
    4. 驗證輸出狀態
    
    參數:
        channel (Channel): 要開啟的通道
            Channel.CH1: 通道 1
            Channel.CH2: 通道 2
    
    返回:
        bool: 輸出是否成功開啟
    
    內部操作流程:
        1. 發送開啟命令：
           :OUTP{channel} ON
           
        2. 等待穩定（100ms）
        
        3. 驗證狀態：
           :OUTP{channel}?
    
    使用範例:
        >>> # 開啟通道 1
        >>> if smu.enable_output(Channel.CH1):
        ...     print("Output enabled")
        ... else:
        ...     print("Failed to enable output")
    
    注意事項:
        1. 開啟輸出前確保設定正確
        2. 觀察待測裝置反應
        3. 異常時會自動關閉輸出
        4. 建議使用 try-except 處理可能的錯誤
    """
```

##### disable_output
```python
def disable_output(self, channel: Channel) -> bool:
    """關閉指定通道的輸出
    
    這個函式會安全地關閉 SMU 的輸出，包括：
    1. 緩慢降低輸出（避免突波）
    2. 關閉輸出
    3. 確認輸出已關閉
    
    參數:
        channel (Channel): 要關閉的通道
            Channel.CH1: 通道 1
            Channel.CH2: 通道 2
    
    返回:
        bool: 輸出是否成功關閉
    
    內部操作流程:
        1. 發送關閉命令：
           :OUTP{channel} OFF
           
        2. 等待穩定（100ms）
        
        3. 驗證狀態：
           :OUTP{channel}?
    
    使用範例:
        >>> # 關閉通道 1
        >>> if smu.disable_output(Channel.CH1):
        ...     print("Output disabled")
        ... else:
        ...     print("Failed to disable output")
    
    注意事項:
        1. 這個函式會儘可能安全地關閉輸出
        2. 即使發生錯誤也會嘗試關閉輸出
        3. 建議在操作結束時始終呼叫此函式
        4. 使用 with 語句可以自動處理輸出關閉
    """
```

##### measure
```python
def measure(self,
           channel: Channel,
           parameters: List[str] = None) -> Union[float, Tuple[float, ...]]:
    """執行測量操作
    
    這個函式可以進行單一或多重參數的測量，支援：
    - 電壓測量
    - 電流測量
    - 電阻測量（需要適當配置）
    
    參數:
        channel (Channel): 要測量的通道
            Channel.CH1: 通道 1
            Channel.CH2: 通道 2
            
        parameters (List[str], optional): 要測量的參數列表
            預設值 None: 測量全部參數
            可用值:
                - ['VOLT']: 僅測量電壓
                - ['CURR']: 僅測量電流
                - ['RES']: 僅測量電阻
                - ['VOLT', 'CURR']: 同時測量電壓和電流
    
    返回:
        Union[float, Tuple[float, ...]]:
            - 單一參數時返回 float
            - 多參數時返回 tuple，順序與參數列表相同
    
    內部操作流程:
        1. 檢查參數有效性
        2. 設定測量配置
        3. 執行測量
        4. 讀取並解析結果
    
    使用範例:
        >>> # 測量電流
        >>> current = smu.measure(Channel.CH1, ['CURR'])
        >>> print(f"Current: {current:.9f} A")
        
        >>> # 同時測量電壓和電流
        >>> voltage, current = smu.measure(
        ...     Channel.CH1, 
        ...     ['VOLT', 'CURR']
        ... )
        >>> print(f"V: {voltage:.6f} V, I: {current:.9f} A")
    
    注意事項:
        1. 測量前確保通道已正確配置
        2. 注意測量範圍設定
        3. 若測量值超出範圍會拋出 MeasurementError
        4. 可能需要等待一段時間讓讀數穩定
    """
```
#### 測量配置與輔助功能

##### set_nplc
```python
def set_nplc(self, channel: Channel, nplc: float):
    """設定積分時間（Number of Power Line Cycles, NPLC）
    
    NPLC 是決定測量精確度和速度的重要參數：
    - 較大的 NPLC 值提供更高的精確度，但測量較慢
    - 較小的 NPLC 值測量較快，但可能較不精確
    
    參數:
        channel (Channel): 要設定的通道
            Channel.CH1: 通道 1
            Channel.CH2: 通道 2
            
        nplc (float): 積分時間，單位為工頻週期
            範圍: 0.01 到 10
            建議值:
                - 0.01: 最快速量測（較不精確）
                - 0.1: 快速量測
                - 1.0: 標準量測（預設）
                - 10.0: 高精確度量測
    
    內部操作流程:
        1. 設定電流測量 NPLC：
           :SENS{channel}:CURR:NPLC {nplc}
           
        2. 設定電壓測量 NPLC：
           :SENS{channel}:VOLT:NPLC {nplc}
    
    使用範例:
        >>> # 設定標準測量速度
        >>> smu.set_nplc(Channel.CH1, 1.0)
        
        >>> # 設定高速測量
        >>> smu.set_nplc(Channel.CH1, 0.1)
        
        >>> # 設定高精確度測量
        >>> smu.set_nplc(Channel.CH1, 10.0)
    
    注意事項:
        1. NPLC 值越大，測量噪聲越小
        2. 50Hz 電源時，1 NPLC = 20ms
        3. 60Hz 電源時，1 NPLC = 16.67ms
        4. 變更 NPLC 會影響測量速度和精確度
    """
```

##### get_error
```python
def get_error(self) -> Optional[str]:
    """讀取並返回錯誤訊息
    
    這個函式會：
    1. 檢查儀器的錯誤佇列
    2. 讀取最新的錯誤訊息
    3. 解析錯誤代碼和說明
    
    無參數
    
    返回:
        Optional[str]:
            - 有錯誤時返回錯誤訊息字串
            - 無錯誤時返回 None
    
    內部操作流程:
        1. 查詢錯誤：
           :SYST:ERR:ALL?
           
        2. 解析回應：
           - 格式：<錯誤碼>,"<錯誤說明>"
           - 無錯誤時返回：+0,"No error"
    
    使用範例:
        >>> # 檢查是否有錯誤
        >>> error = smu.get_error()
        >>> if error:
        ...     print(f"Error detected: {error}")
        ... else:
        ...     print("No errors")
    
    注意事項:
        1. 建議定期檢查錯誤
        2. 錯誤訊息讀取後會從佇列中移除
        3. 可能有多個錯誤排隊
        4. 重要操作前後都應該檢查錯誤
    """
```

##### enable_beeper
```python
def enable_beeper(self, enable: bool = True):
    """控制儀器的蜂鳴器
    
    這個函式用於開啟或關閉儀器的聲音提示功能。
    蜂鳴器可用於：
    - 操作確認
    - 錯誤警告
    - 測試完成提示
    
    參數:
        enable (bool): 是否啟用蜂鳴器
            True: 開啟蜂鳴器（預設）
            False: 關閉蜂鳴器
    
    內部操作流程:
        發送命令：
        :SYST:BEEP:STAT {ON|OFF}
    
    使用範例:
        >>> # 開啟蜂鳴器
        >>> smu.enable_beeper(True)
        
        >>> # 關閉蜂鳴器
        >>> smu.enable_beeper(False)
    
    注意事項:
        1. 設定會在關機後重設
        2. 建議在自動化測試時關閉
        3. 某些重要警告可能會忽略此設定
    """
```

##### beep
```python
def beep(self, frequency: int = 440, duration: float = 0.1):
    """發出蜂鳴聲
    
    這個函式可以控制儀器發出特定頻率和持續時間的聲音。
    可用於：
    - 操作確認提示
    - 測試階段標記
    - 錯誤警告
    
    參數:
        frequency (int): 蜂鳴頻率（Hz）
            範圍: 20 到 20000 Hz
            預設值: 440 Hz（標準音高 A）
            
        duration (float): 持續時間（秒）
            範圍: 0.01 到 5.0 秒
            預設值: 0.1 秒
    
    內部操作流程:
        發送命令：
        :SYST:BEEP {frequency},{duration}
    
    使用範例:
        >>> # 標準提示音
        >>> smu.beep()
        
        >>> # 錯誤警告音（低頻，較長）
        >>> smu.beep(220, 0.5)
        
        >>> # 完成提示音（高頻，短促）
        >>> smu.beep(880, 0.05)
    
    注意事項:
        1. 頻率超出範圍會被限制在有效範圍內
        2. 蜂鳴器必須是啟用狀態才會發聲
        3. 聲音可能會被系統音量設定影響
        4. 連續發聲可能會影響測量精確度
    """
```

##### get_system_status
```python
def get_system_status(self) -> dict:
    """獲取系統完整狀態資訊
    
    這個函式會收集儀器的各種狀態資訊，包括：
    - 連線狀態
    - 通道設定
    - 輸出狀態
    - 錯誤狀態
    
    無參數
    
    返回:
        dict: 包含系統狀態的字典
            格式:
            {
                'connected': bool,  # 連線狀態
                'channels': {       # 各通道資訊
                    1: {
                        'output': bool,        # 輸出狀態
                        'source_mode': str,    # 輸出模式
                        'error': str           # 錯誤訊息
                    },
                    2: {
                        # 通道 2 的相同資訊
                    }
                }
            }
    
    內部操作流程:
        1. 檢查連線狀態
        2. 讀取各通道設定
        3. 檢查錯誤狀態
        4. 整理回傳資訊
    
    使用範例:
        >>> # 獲取系統狀態
        >>> status = smu.get_system_status()
        >>> print(f"Connected: {status['connected']}")
        >>> for ch in status['channels']:
        ...     print(f"Channel {ch}:")
        ...     print(f"  Output: {status['channels'][ch]['output']}")
        ...     print(f"  Mode: {status['channels'][ch]['source_mode']}")
        ...     if status['channels'][ch]['error']:
        ...         print(f"  Error: {status['channels'][ch]['error']}")
    
    注意事項:
        1. 這個函式會進行多次儀器通訊
        2. 可能會稍微影響執行速度
        3. 建議在故障排除時使用
        4. 不建議在高速測量迴圈中使用
    """
```

#### 上下文管理功能

##### __enter__ 方法
```python
def __enter__(self):
    """上下文管理器的進入方法
    
    這個方法在使用 with 語句時自動調用，用於：
    1. 確保儀器連線
    2. 初始化系統狀態
    3. 準備開始操作
    
    無參數
    
    返回:
        self: 返回類別實例，供 with 語句使用
    
    內部操作流程:
        1. 檢查是否已連線
        2. 若未連線則建立連線
        3. 返回實例
    
    使用範例:
        >>> with KeysightB2902B('TCPIP0::172.30.32.98::inst0::INSTR') as smu:
        ...     # 在這個區塊中自動處理連線
        ...     smu.configure_source(Channel.CH1, OutputMode.VOLTAGE, 1.0, 0.1)
        ...     # 離開區塊時自動斷開連線
    
    注意事項:
        1. 連線失敗會拋出 ConnectionError
        2. 建議使用 with 語句來自動管理連線
        3. 確保所有操作都在 with 區塊內進行
    """
```

##### __exit__ 方法
```python
def __exit__(self, exc_type, exc_val, exc_tb):
    """上下文管理器的退出方法
    
    這個方法在離開 with 區塊時自動調用，用於：
    1. 安全地關閉所有輸出
    2. 斷開儀器連線
    3. 清理資源
    4. 處理可能的異常
    
    參數:
        exc_type: 異常類型（如果有）
        exc_val: 異常值（如果有）
        exc_tb: 異常追蹤資訊（如果有）
    
    內部操作流程:
        1. 關閉所有通道輸出
        2. 斷開儀器連線
        3. 記錄可能的錯誤
    
    使用範例:
        >>> try:
        ...     with KeysightB2902B('TCPIP0::172.30.32.98::inst0::INSTR') as smu:
        ...         # 即使發生異常，也會安全地清理資源
        ...         smu.configure_source(...)
        ...         smu.enable_output(...)
        ... except Exception as e:
        ...     print(f"Error occurred: {e}")
    
    注意事項:
        1. 即使發生異常也會執行清理操作
        2. 確保資源被正確釋放
        3. 記錄重要的錯誤資訊
    """
```

#### 輔助功能

##### _setup_logging
```python
def _setup_logging(self):
    """設定記錄器配置
    
    這是一個內部方法，用於：
    1. 建立和配置記錄器
    2. 設定記錄格式
    3. 設定記錄等級
    
    無參數
    無返回值
    
    內部操作流程:
        1. 建立記錄器：
           self.logger = logging.getLogger(__name__)
        
        2. 設定記錄等級：
           self.logger.setLevel(logging.INFO)
        
        3. 建立處理器：
           handler = logging.StreamHandler()
        
        4. 設定格式：
           formatter = logging.Formatter(...)
        
        5. 配置並添加處理器
    
    記錄等級說明：
        DEBUG (10): 詳細的除錯資訊
        INFO (20): 一般操作資訊
        WARNING (30): 警告訊息
        ERROR (40): 錯誤訊息
        CRITICAL (50): 嚴重錯誤
    
    注意事項:
        1. 這是私有方法，不應直接調用
        2. 記錄配置只在實例化時執行一次
        3. 可以通過環境變數調整記錄等級
    """
```

##### _send_command
```python
def _send_command(self, command: str, check_errors: bool = True) -> Tuple[bool, Optional[str]]:
    """發送 SCPI 命令到儀器
    
    這是一個內部方法，用於：
    1. 安全地發送命令
    2. 處理可能的錯誤
    3. 記錄命令執行情況
    
    參數:
        command (str): SCPI 命令字串
        check_errors (bool): 是否檢查命令執行後的錯誤
            預設值: True
    
    返回:
        Tuple[bool, Optional[str]]:
            - bool: 命令是否成功執行
            - Optional[str]: 錯誤訊息（如果有）
    
    內部操作流程:
        1. 檢查連線狀態
        2. 記錄即將執行的命令
        3. 發送命令
        4. 檢查錯誤（如果啟用）
        5. 記錄執行結果
    
    使用範例（內部使用）:
        >>> success, error = self._send_command(":OUTP1 ON")
        >>> if not success:
        ...     self.logger.error(f"Command failed: {error}")
    
    注意事項:
        1. 這是私有方法，不應直接調用
        2. 總是包含錯誤處理
        3. 所有命令都會被記錄
        4. 可能拋出通訊相關異常
    """
```