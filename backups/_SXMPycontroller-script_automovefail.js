// 全域狀態管理
const state = {
    connected: false,
};

// DOM元素
const elements = {
    visaAddress: document.getElementById('visaAddress'),
    connectBtn: document.getElementById('connectBtn'),
    disconnectBtn: document.getElementById('disconnectBtn'),
    connectionStatus: document.getElementById('connectionStatus'),
    ch1: {
        mode: document.getElementById('ch1Mode'),
        value: document.getElementById('ch1Value'),
        unit: document.getElementById('ch1Unit'),
        setBtn: document.getElementById('ch1SetBtn'),
        outputBtn: document.getElementById('ch1OutputBtn'),
        readBtn: document.getElementById('ch1ReadBtn'),
        voltage: document.getElementById('ch1Voltage'),
        current: document.getElementById('ch1Current'),
        lastRead: document.getElementById('ch1LastRead'),
        compliance: document.getElementById('ch1Compliance'),
        setComplianceBtn: document.getElementById('ch1SetComplianceBtn'),
        readComplianceBtn: document.getElementById('ch1ReadComplianceBtn')
    },
    ch2: {
        mode: document.getElementById('ch2Mode'),
        value: document.getElementById('ch2Value'),
        unit: document.getElementById('ch2Unit'),
        setBtn: document.getElementById('ch2SetBtn'),
        outputBtn: document.getElementById('ch2OutputBtn'),
        readBtn: document.getElementById('ch2ReadBtn'),
        voltage: document.getElementById('ch2Voltage'),
        current: document.getElementById('ch2Current'),
        lastRead: document.getElementById('ch2LastRead'),
        compliance: document.getElementById('ch2Compliance'),
        setComplianceBtn: document.getElementById('ch2SetComplianceBtn'),
        readComplianceBtn: document.getElementById('ch2ReadComplianceBtn')
    },
    stsStartBtn: document.getElementById('stsStartBtn')
};

// 更新連接狀態UI
function updateConnectionStatus(connected) {
    try {
        state.connected = connected;
        
        // 更新狀態指示器
        if (elements.connectionStatus) {
            elements.connectionStatus.className = `status-indicator status-${connected ? 'connected' : 'disconnected'}`;
        }
        
        // 更新連接按鈕
        if (elements.connectBtn) {
            elements.connectBtn.disabled = connected;
        }
        if (elements.disconnectBtn) {
            elements.disconnectBtn.disabled = !connected;
        }
        
        // 更新通道控制項
        ['ch1', 'ch2'].forEach(channelId => {
            const ch = elements[channelId];
            if (ch) {
                // 確保每個元素存在再設置狀態
                if (ch.setBtn) ch.setBtn.disabled = !connected;
                if (ch.outputBtn) ch.outputBtn.disabled = !connected;
                if (ch.readBtn) ch.readBtn.disabled = !connected;
                if (ch.mode) ch.mode.disabled = !connected;
                if (ch.value) ch.value.disabled = !connected;
                if (ch.setComplianceBtn) ch.setComplianceBtn.disabled = !connected;
                if (ch.readComplianceBtn) ch.readComplianceBtn.disabled = !connected;
                if (ch.compliance) ch.compliance.disabled = !connected;
            }
        });
        
    } catch (error) {
        console.error('Error updating connection status:', error);
    }
}


function setupChannelEvents(channelNum) {
    const ch = elements[`ch${channelNum}`];
    
    // Compliance控制
    ch.setComplianceBtn.addEventListener('click', async () => {
        try {
            const value = parseFloat(ch.compliance.value);
            await pywebview.api.set_compliance(channelNum, value);
            console.log(`Set channel ${channelNum} compliance to ${value}A`);
        } catch (error) {
            alert(`設定compliance失敗: ${error}`);
        }
    });

    ch.readComplianceBtn.addEventListener('click', async () => {
        try {
            const value = await pywebview.api.get_compliance(channelNum);
            ch.compliance.value = value.toFixed(3);
            console.log(`Channel ${channelNum} compliance: ${value}A`);
        } catch (error) {
            alert(`讀取compliance失敗: ${error}`);
        }
    });
}    
// 單次讀值功能
async function readChannel(channel) {
    try {
        const btn = document.getElementById(`ch${channel}ReadBtn`);
        btn.disabled = true;
        btn.textContent = 'Reading...';
        
        const reading = await pywebview.api.read_channel(channel);
        
        // 電壓保持6位小數
        document.getElementById(`ch${channel}Voltage`).textContent = 
            `${reading.voltage.toFixed(6)} V`;
            
        // 電流轉換為μA並顯示6位小數
        const currentInMicroAmps = reading.current * 1e6;
        document.getElementById(`ch${channel}Current`).textContent = 
            `${currentInMicroAmps.toFixed(6)} μA`;
            
        document.getElementById(`ch${channel}LastRead`).textContent = 
            new Date().toLocaleTimeString();
            
    } catch (error) {
        alert(`讀值失敗: ${error}`);
    } finally {
        const btn = document.getElementById(`ch${channel}ReadBtn`);
        btn.disabled = false;
        btn.textContent = 'Read Values';
    }
}

// 事件處理器
// 連接處理函數
async function handleConnect() {
    try {
        const address = elements.visaAddress.value.trim();
        if (!address) {
            alert('請輸入VISA地址');
            return;
        }
        
        elements.connectBtn.disabled = true;
        elements.connectBtn.textContent = '連接中...';
        
        await pywebview.api.connect_smu(address);
        updateConnectionStatus(true);
        
    } catch (error) {
        alert('連接失敗: ' + error);
        updateConnectionStatus(false);
    } finally {
        elements.connectBtn.disabled = false;
        elements.connectBtn.textContent = 'Connect';
    }
}

// 斷開連接處理函數
async function handleDisconnect() {
    try {
        elements.disconnectBtn.disabled = true;
        elements.disconnectBtn.textContent = '斷開中...';
        
        await pywebview.api.disconnect_smu();
        updateConnectionStatus(false);
        
    } catch (error) {
        alert('斷開連接失敗: ' + error);
    } finally {
        elements.disconnectBtn.disabled = false;
        elements.disconnectBtn.textContent = 'Disconnect';
    }
}

function setupChannelEvents(channelNum) {
    const ch = elements[`ch${channelNum}`];
    
    // 模式變更處理
    ch.mode.addEventListener('change', () => {
        ch.unit.textContent = ch.mode.value === 'VOLTAGE' ? 'V' : 'A';
    });

    // 設定輸出值
    ch.setBtn.addEventListener('click', async () => {
        try {
            await pywebview.api.set_channel_value(
                channelNum,
                ch.mode.value,
                parseFloat(ch.value.value)
            );
        } catch (error) {
            alert(`設定通道 ${channelNum} 失敗: ${error}`);
        }
    });

    // 輸出開關
    ch.outputBtn.addEventListener('click', async () => {
        try {
            const newState = ch.outputBtn.textContent === 'Output OFF';
            await pywebview.api.set_channel_output(channelNum, newState);
            ch.outputBtn.textContent = `Output ${newState ? 'ON' : 'OFF'}`;
            ch.outputBtn.className = newState ? 'success' : 'warning';
        } catch (error) {
            alert(`切換輸出 ${channelNum} 失敗: ${error}`);
        }
    });
}


// 初始化
function initialize() {
    // 先檢查元素是否存在
    if (!elements.connectBtn || !elements.disconnectBtn) {
        console.warn('Required elements not found, skipping initialization');
        return;
    }
    
    // 再進行事件監聽器綁定
    elements.connectBtn.addEventListener('click', handleConnect);
    elements.disconnectBtn.addEventListener('click', handleDisconnect);

    
    // 設置通道事件
    setupChannelEvents(1);
    setupChannelEvents(2);
    
    // Compliance設置
    elements.setComplianceBtn.addEventListener('click', async () => {
        try {
            await pywebview.api.set_compliance(parseFloat(elements.compliance.value));
        } catch (error) {
            alert('設定限制值失敗: ' + error);
        }
    });

    // STS控制
    elements.stsStartBtn.addEventListener('click', async () => {
        try {
            await pywebview.api.start_sts();
        } catch (error) {
            alert('啟動STS失敗: ' + error);
        }
    });

    // 初始化UI狀態
    updateConnectionStatus(false);
}

// STS控制相關功能
class STSControl {
    constructor() {
        // 等待 pywebview 就緒
        this.waitForPywebview().then(() => {
            this.setupEventListeners();
            this.loadScripts();
        });
        this.stsStatus = document.getElementById('stsStatus');
    }

    setupEventListeners() {
        // Add row按鈕
        document.getElementById('addStsRow').addEventListener('click', () => {
            this.addSettingRow();
        });

        // 儲存腳本按鈕
        document.getElementById('saveScript').addEventListener('click', () => {
            this.saveCurrentScript();
        });

        // 腳本選擇下拉選單
        document.getElementById('scriptSelect').addEventListener('change', (e) => {
            this.loadScript(e.target.value);
        });

        // Single STS按鈕
        document.getElementById('startSingleSts').addEventListener('click', () => {
            this.startSTS(false);
        });

        // Multi-STS按鈕
        document.getElementById('startMultiSts').addEventListener('click', () => {
            this.perform_multi_sts();
        });

        // 動態移除row按鈕的事件委派
        document.getElementById('stsSettingsRows').addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-row')) {
                this.removeSettingRow(e.target);
            }
        });
    }


    addSettingRow() {
        const row = document.createElement('div');
        row.className = 'sts-row';
        row.innerHTML = `
            <input type="number" class="vds-input" value="0" step="0.1">
            <input type="number" class="vg-input" value="0" step="0.1">
            <button class="remove-row" title="Remove">×</button>
        `;
        document.getElementById('stsSettingsRows').appendChild(row);
    }

    removeSettingRow(button) {
        const rows = document.querySelectorAll('.sts-row');
        if (rows.length > 1) {  // 保持至少一行
            button.closest('.sts-row').remove();
        }
    }

    async waitForPywebview() {
        const maxAttempts = 10;
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            if (typeof pywebview !== 'undefined') {
                return true;
            }
            await new Promise(resolve => setTimeout(resolve, 500));
            attempts++;
        }
        throw new Error('pywebview initialization timeout');
    }

    async saveCurrentScript() {
        try {
            const name = document.getElementById('scriptName').value.trim();
            if (!name) {
                alert('Please enter a script name');
                return;
            }

            const settings = this.collectCurrentSettings();
            const success = await pywebview.api.save_sts_script(
                name, 
                settings.vds_list, 
                settings.vg_list
            );

            if (success) {
                await this.loadScripts();  // 重新載入腳本列表
                alert('Script saved successfully');
            }
        } catch (error) {
            alert(`Error saving script: ${error}`);
        }
    }

    async loadScripts() {
        try {
            const scripts = await pywebview.api.get_sts_scripts();
            const select = document.getElementById('scriptSelect');
            
            // 清除現有選項
            select.innerHTML = '<option value="">Select Script...</option>';
            
            // 添加腳本選項
            Object.entries(scripts).forEach(([name, script]) => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading scripts:', error);
        }
    }

    loadScript(scriptName) {
        if (!scriptName) return;
    
        try {
            // 從API獲取腳本資料
            pywebview.api.get_sts_scripts().then(scripts => {
                const script = scripts[scriptName];
                if (!script) return;
    
                // 清除現有的所有行
                const container = document.getElementById('stsSettingsRows');
                container.innerHTML = '';
    
                // 確保vds_list和vg_list長度相同
                const length = Math.min(script.vds_list.length, script.vg_list.length);
    
                // 依據腳本數據建立新的行
                for (let i = 0; i < length; i++) {
                    const row = document.createElement('div');
                    row.className = 'sts-row';
                    row.innerHTML = `
                        <input type="number" class="vds-input" value="${script.vds_list[i]}" step="0.1">
                        <input type="number" class="vg-input" value="${script.vg_list[i]}" step="0.1">
                        <button class="remove-row" title="Remove">×</button>
                    `;
                    container.appendChild(row);
                }
    
                // 更新腳本名稱輸入框
                document.getElementById('scriptName').value = scriptName;
    
                console.log(`Loaded script: ${scriptName}`);
            }).catch(error => {
                console.error('Error loading script:', error);
                alert('Error loading script');
            });
        } catch (error) {
            console.error('Error in loadScript:', error);
            alert('Error loading script');
        }
    }

    collectCurrentSettings() {
        const rows = document.querySelectorAll('.sts-row');
        const vds_list = [];
        const vg_list = [];

        rows.forEach(row => {
            vds_list.push(parseFloat(row.querySelector('.vds-input').value));
            vg_list.push(parseFloat(row.querySelector('.vg-input').value));
        });

        return { vds_list, vg_list };
    }

    async startSTS() {
        try {
            const startStsBtn = document.getElementById('startSingleSts');
            if (startStsBtn) {
                startStsBtn.disabled = true;
                startStsBtn.textContent = 'Starting STS...';
            }
            
            // 更新狀態顯示
            if (this.stsStatus) {
                this.stsStatus.textContent = 'Initiating STS measurement...';
            }

            // 調用後端API
            const success = await pywebview.api.start_sts();
            
            if (success) {
                if (this.stsStatus) {
                    this.stsStatus.textContent = 'STS measurement completed successfully';
                }
                console.log('STS measurement completed successfully');
            } else {
                throw new Error('STS measurement failed');
            }
            
        } catch (error) {
            console.error('STS Error:', error);
            if (this.stsStatus) {
                this.stsStatus.textContent = `Error: ${error.message}`;
            }
            alert(`Error performing STS: ${error.message}`);
        } finally {
            // 恢復按鈕狀態
            const startStsBtn = document.getElementById('startSingleSts');
            if (startStsBtn) {
                startStsBtn.disabled = false;
                startStsBtn.textContent = 'Start Single STS';
            }
        }
    }

    async perform_multi_sts() {
        try {
            // 獲取當前腳本名稱
            const scriptName = document.getElementById('scriptSelect').value;
            if (!scriptName) {
                alert('Please select a script first');
                return;
            }
    
            const startMultiStsBtn = document.getElementById('startMultiSts');
            if (startMultiStsBtn) {
                startMultiStsBtn.disabled = true;
                startMultiStsBtn.textContent = 'Running Multi-STS...';
            }
            
            // 更新狀態顯示
            if (this.stsStatus) {
                this.stsStatus.textContent = 'Performing Multi-STS measurement...';
            }
    
            // 調用後端API
            const success = await pywebview.api.perform_multi_sts(scriptName);
            
            if (success) {
                if (this.stsStatus) {
                    this.stsStatus.textContent = 'Multi-STS measurements completed successfully';
                }
                console.log('Multi-STS measurements completed successfully');
            } else {
                throw new Error('Multi-STS measurements failed');
            }
            
        } catch (error) {
            console.error('Multi-STS Error:', error);
            if (this.stsStatus) {
                this.stsStatus.textContent = `Error: ${error.message}`;
            }
            alert(`Error performing Multi-STS: ${error.message}`);
        } finally {
            // 恢復按鈕狀態
            const startMultiStsBtn = document.getElementById('startMultiSts');
            if (startMultiStsBtn) {
                startMultiStsBtn.disabled = false;
                startMultiStsBtn.textContent = 'Start Multi-STS';
            }
        }
    }
}

// CITS Control class implementation
class CITSControl {
    constructor() {
        // Debug flag
        this.debug = true;
        this.log('Initializing CITS Control...');
        
        // State management
        this.isRunning = false;
        
        // Initialize controls
        this.setupControls();
    }
    
    setupControls() {
        // Points inputs
        this.pointsX = document.getElementById('citsPointsX');
        this.pointsY = document.getElementById('citsPointsY');
        
        // Direction selector
        this.scanDirection = document.getElementById('citsScanDirection');
        
        // Control buttons
        this.singleCitsBtn = document.getElementById('startSingleCits');
        this.multiCitsBtn = document.getElementById('startMstsCits');
        
        // Status displays
        this.status = document.getElementById('citsStatus');
        this.progress = document.getElementById('citsProgress');
        this.lastTime = document.getElementById('citsLastTime');
        
        this.validateElements();
        this.setupEventListeners();
    }
    
    validateElements() {
        // Validate all required elements exist
        const requiredElements = {
            'pointsX': this.pointsX,
            'pointsY': this.pointsY,
            'scanDirection': this.scanDirection,
            'singleCitsBtn': this.singleCitsBtn,
            'multiCitsBtn': this.multiCitsBtn,
            'status': this.status,
            'progress': this.progress,
            'lastTime': this.lastTime
        };
        
        for (const [name, element] of Object.entries(requiredElements)) {
            if (!element) {
                throw new Error(`Required element not found: ${name}`);
            }
        }
    }
    
    setupEventListeners() {
        // Single CITS button
        this.singleCitsBtn.onclick = () => {
            this.log('Single CITS button clicked');
            this.startSstsCits();
        };
        
        // Multi CITS button
        this.multiCitsBtn.onclick = () => {
            this.log('Multi CITS button clicked');
            this.startMstsCits();
        };
        
        // Input validation
        this.pointsX.onchange = () => this.validateInputValue(this.pointsX);
        this.pointsY.onchange = () => this.validateInputValue(this.pointsY);
    }
    
    async startSstsCits() {
        
        // 執行單一 STS CITS 量測
        // 每個 CITS 點位只執行一次基本的 STS 量測
        
        try {
            // 獲取並驗證參數
            const pointsX = parseInt(this.pointsX.value);
            const pointsY = parseInt(this.pointsY.value);
            const scanDirection = parseInt(this.scanDirection.value);
            
            // 驗證輸入
            if (!this.validateInputs(pointsX, pointsY)) {
                return;
            }
            
            // 更新介面狀態
            this.setRunningState(true);
            this.updateStatus('Starting Single-STS CITS...');
            
            // 呼叫後端 API
            this.log(`Starting Single-STS CITS: 
                     X=${pointsX}, Y=${pointsY}, 
                     direction=${scanDirection}`);
                     
            const success = await pywebview.api.start_ssts_cits(
                pointsX, 
                pointsY, 
                scanDirection
            );
            
            if (success) {
                this.updateStatus('Single-STS CITS completed successfully');
                this.updateLastTime();
            } else {
                throw new Error('Single-STS CITS measurement failed');
            }
            
        } catch (error) {
            this.handleError(error);
        } finally {
            this.setRunningState(false);
        }
    }

    async startMstsCits() {

        // 執行多重 STS CITS 量測
        // 在每個 CITS 點位執行多組不同偏壓的 STS 量測
        
        try {
            const pointsX = parseInt(this.pointsX.value);
            const pointsY = parseInt(this.pointsY.value);
            const scanDirection = parseInt(this.scanDirection.value);
            
            // 取得選擇的腳本
            const scriptSelect = document.getElementById('scriptSelect');
            const selectedScript = scriptSelect.value;
            
            if (!selectedScript) {
                throw new Error("請選擇 Multi-STS 腳本");
            }
            
            // 更新介面狀態
            this.setRunningState(true);
            this.updateStatus('Starting Multi-STS CITS...');
            
            // 調用後端 API
            const success = await pywebview.api.start_msts_cits(
                pointsX,
                pointsY,
                selectedScript,
                scanDirection
            );
            
            if (success) {
                this.updateStatus('Multi-STS CITS completed successfully');
                this.updateLastTime();
            } else {
                throw new Error('Multi-STS CITS measurement failed');
            }
            
        } catch (error) {
            this.handleError(error);
        } finally {
            this.setRunningState(false);
        }
    }

    
    validateInputs(pointsX, pointsY) {
        if (isNaN(pointsX) || isNaN(pointsY)) {
            this.showError('Please enter valid numbers for points');
            return false;
        }
        
        if (pointsX < 1 || pointsX > 512 || pointsY < 1 || pointsY > 512) {
            this.showError('Points must be between 1 and 512');
            return false;
        }
        
        return true;
    }
    
    validateInputValue(input) {
        const value = parseInt(input.value);
        if (value < 1) input.value = 1;
        if (value > 512) input.value = 512;
    }
    
    setRunningState(running) {
        this.isRunning = running;
        this.toggleControls(!running);
    }
    
    toggleControls(enabled) {
        // Disable/enable all inputs during measurement
        this.pointsX.disabled = !enabled;
        this.pointsY.disabled = !enabled;
        this.scanDirection.disabled = !enabled;
        this.singleCitsBtn.disabled = !enabled;
        this.multiCitsBtn.disabled = !enabled;
    }
    
    updateStatus(message) {
        if (this.status) {
            this.status.textContent = message;
        }
    }
    
    updateProgress(percent) {
        if (this.progress) {
            this.progress.textContent = `${Math.round(percent)}%`;
        }
    }
    
    updateLastTime() {
        if (this.lastTime) {
            this.lastTime.textContent = new Date().toLocaleTimeString();
        }
    }
    
    showError(message) {
        this.log('Error: ' + message);
        alert(message);
    }
    
    handleError(error) {
        const errorMessage = error.message || 'Unknown error occurred';
        this.updateStatus(`Error: ${errorMessage}`);
        this.showError(`CITS Error: ${errorMessage}`);
    }
    
    log(message) {
        if (this.debug) {
            console.log(`[CITS Control] ${message}`);
        }
    }
}

// 使用 DOMContentLoaded 確保 DOM 完全載入
document.addEventListener('DOMContentLoaded', function() {
    try {
        initialize();
    } catch (error) {
        console.error('Initialization error:', error);
    }
});

// // 初始化時建立STS控制實例
// document.addEventListener('DOMContentLoaded', () => {
    
// });

// Initialize CITS Control when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('Initializing CITS Control...');
        window.citsControl = new CITSControl();
        window.stsControl = new STSControl();
        console.log('CITS Control initialized successfully');
    } catch (error) {
        console.error('Failed to initialize CITS Control:', error);
    }
});

class LocalCITSControl {
    constructor() {
        this.localAreas = [];
        this.previewCanvas = null;
        this.previewContext = null;
        this.initialize();
    }

    initialize() {
        this.previewCanvas = document.getElementById('previewCanvas');
        this.previewContext = this.previewCanvas.getContext('2d');
        this.setupEventListeners();
        this.addLocalArea(); // 添加第一個預設區域
    }

    setupEventListeners() {
        document.getElementById('addLocalArea').addEventListener('click', () => {
            this.addLocalArea();
        });

        document.getElementById('previewLocalCits').addEventListener('click', () => {
            this.previewLocalCits();
        });

        document.getElementById('startLocalStsCits').addEventListener('click', () => {
            this.startLocalStsCits();
        });

        document.getElementById('startLocalMultiStsCits').addEventListener('click', () => {
            this.startLocalMultiStsCits();
        });

        // 移除區域按鈕的事件委派
        document.getElementById('localAreasContainer').addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-area')) {
                this.removeLocalArea(e.target.closest('.local-area-container'));
            }
        });
    }

    addLocalArea() {
        const container = document.createElement('div');
        container.className = 'local-area-container';
        container.innerHTML = `
            <div class="local-area-grid">
                <div class="input-row">
                    <div class="input-field">
                        <label>X Start Position</label>
                        <div class="input-with-unit">
                            <input type="number" class="local-cits-input start-x" value="200" step="0.1">
                            <span class="unit">nm</span>
                        </div>
                    </div>
                    <div class="input-field">
                        <label>Y Start Position</label>
                        <div class="input-with-unit">
                            <input type="number" class="local-cits-input start-y" value="200" step="0.1">
                            <span class="unit">nm</span>
                        </div>
                    </div>
                    <div class="input-field">
                        <label>Start Point Direction</label>
                        <select class="startpoint-direction-select">
                            <option value="1">Up</option>
                            <option value="-1">Down</option>
                        </select>
                    </div>
                </div>
                <div class="parameters-row">
                    <div class="input-field">
                        <label>Step Size X (ΔX)</label>
                        <div class="input-with-unit">
                            <input type="number" class="local-cits-input dx" value="20" step="0.1">
                            <span class="unit">nm</span>
                        </div>
                    </div>
                    <div class="input-field">
                        <label>Step Size Y (ΔY)</label>
                        <div class="input-with-unit">
                            <input type="number" class="local-cits-input dy" value="20" step="0.1">
                            <span class="unit">nm</span>
                        </div>
                    </div>
                    <div class="input-field">
                        <label>Points X (Nx)</label>
                        <input type="number" class="local-cits-input nx" value="5" min="1" max="512">
                    </div>
                    <div class="input-field">
                        <label>Points Y (Ny)</label>
                        <input type="number" class="local-cits-input ny" value="3" min="1" max="512">
                    </div>
                </div>
            </div>
            <div class="area-controls">
                <button class="danger-btn remove-area">Remove Area</button>
            </div>
        `;
    
        document.getElementById('localAreasContainer').appendChild(container);
    }

    removeLocalArea(container) {
        const containers = document.querySelectorAll('.local-area-container');
        if (containers.length > 1) {
            container.remove();
        } else {
            alert('At least one local area must be maintained');
        }
    }

    collectLocalAreas() {
        const areas = [];
        document.querySelectorAll('.local-area-container').forEach(container => {
            areas.push({
                start_x: parseFloat(container.querySelector('.start-x').value),
                start_y: parseFloat(container.querySelector('.start-y').value),
                dx: parseFloat(container.querySelector('.dx').value),
                dy: parseFloat(container.querySelector('.dy').value),
                nx: parseInt(container.querySelector('.nx').value),
                ny: parseInt(container.querySelector('.ny').value),
                startpoint_direction: parseInt(container.querySelector('.startpoint-direction-select').value)
            });
        });
        return areas;
    }

    async previewLocalCits() {
        try {
            const areas = this.collectLocalAreas();
            
            // 獲取掃描參數（從其他輸入欄）
            const scanCenter = document.getElementById('scanCenter');
            const scanRange = document.getElementById('scanRange');
            const scanAngle = document.getElementById('scanAngle');
            
            if (!scanCenter || !scanRange || !scanAngle) {
                throw new Error('Unable to find scan parameters');
            }

            const centerX = parseFloat(scanCenter.value) || 250;
            const centerY = parseFloat(scanCenter.value) || 250;
            const range = parseFloat(scanRange.value) || 500;
            const angle = parseFloat(scanAngle.value) || 60;
            
            // 清除畫布
            this.previewContext.clearRect(0, 0, this.previewCanvas.width, this.previewCanvas.height);
            
            // 設定座標系統
            this.setupCoordinateSystem();
            
            // 繪製掃描區域
            this.drawScanArea(centerX, centerY, range, angle);
            
            // 繪製局部區域點位
            this.drawLocalAreas(areas, centerX, centerY, angle);
            
            // 更新預覽資訊
            this.updatePreviewInfo(centerX, centerY, range, angle, areas);
            
        } catch (error) {
            console.error('Preview error:', error);
            this.updateStatus('Preview failed: ' + error.message);
        }
    }

    setupCoordinateSystem() {
        this.previewContext.setTransform(1, 0, 0, -1, 0, this.previewCanvas.height);
        this.previewContext.translate(this.previewCanvas.width/2, this.previewCanvas.height/2);
    }

    drawScanArea(centerX, centerY, range, angle) {
        const ctx = this.previewContext;
        const scale = 0.8; // 調整掃描區域在畫布中的大小

        ctx.save();
        ctx.rotate(angle * Math.PI / 180);

        // 繪製掃描範圍框
        ctx.strokeStyle = '#000';
        ctx.setLineDash([5, 5]);
        ctx.strokeRect(-range*scale/2, -range*scale/2, range*scale, range*scale);
        
        // 繪製掃描中心
        ctx.fillStyle = 'red';
        ctx.beginPath();
        ctx.arc(0, 0, 3, 0, 2*Math.PI);
        ctx.fill();
        
        // 繪製軸向
        ctx.strokeStyle = 'blue';
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, range*scale/3);
        ctx.stroke();
        
        ctx.strokeStyle = 'red';
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(range*scale/3, 0);
        ctx.stroke();

        ctx.restore();
    }

    drawLocalAreas(areas, centerX, centerY, angle) {
        const ctx = this.previewContext;
        const scale = 0.8;
        
        ctx.save();
        ctx.rotate(angle * Math.PI / 180);

        areas.forEach((area, index) => {
            const colorHue = (index * 360 / areas.length + 120) % 360;
            ctx.fillStyle = `hsla(${colorHue}, 70%, 50%, 0.6)`;
            
            for (let i = 0; i < area.nx; i++) {
                for (let j = 0; j < area.ny; j++) {
                    const x = (area.start_x + i * area.dx - centerX) * scale;
                    const y = (area.start_y + j * area.dy - centerY) * scale;
                    
                    ctx.beginPath();
                    ctx.arc(x, y, 2, 0, 2*Math.PI);
                    ctx.fill();
                    
                    // 標記特殊點位
                    if (i === 0 && j === 0) {
                        ctx.fillStyle = '#000';
                        ctx.beginPath();
                        ctx.arc(x, y, 4, 0, 2*Math.PI);
                        ctx.fill();
                    }
                    if (i === area.nx-1 && j === area.ny-1) {
                        ctx.fillStyle = 'red';
                        ctx.beginPath();
                        ctx.arc(x, y, 4, 0, 2*Math.PI);
                        ctx.fill();
                    }
                }
            }
        });
        
        ctx.restore();
    }

    updatePreviewInfo(centerX, centerY, range, angle, areas) {
        const totalPoints = areas.reduce((sum, area) => sum + area.nx * area.ny, 0);
        
        document.getElementById('previewCenter').textContent = `(${centerX}, ${centerY})`;
        document.getElementById('previewRange').textContent = range;
        document.getElementById('previewAngle').textContent = angle;
        document.getElementById('previewTotalPoints').textContent = totalPoints;
    }

    updateStatus(message) {
        document.getElementById('localCitsStatus').textContent = message;
    }

    updateProgress(value) {
        document.getElementById('localCitsProgress').textContent = value + '%';
    }

    updateLastTime() {
        document.getElementById('localCitsLastTime').textContent = 
            new Date().toLocaleTimeString();
    }

    async startLocalStsCits() {
        try {
            const areas = this.collectLocalAreas();
            const globalScanDirection = parseInt(document.getElementById('globalScanDirection').value);
            
            this.updateStatus('Starting Local CITS...');
            
            const success = await pywebview.api.start_local_ssts_cits(
                areas, 
                globalScanDirection
            );
            
            if (success) {
                this.updateStatus('Local CITS completed successfully');
                this.updateLastTime();
            } else {
                throw new Error('Local CITS failed');
            }
            
        } catch (error) {
            console.error('Local CITS error:', error);
            this.updateStatus('Error: ' + error.message);
        }
    }

    async startLocalMultiStsCits() {
        try {
            const areas = this.collectLocalAreas();
            const globalScanDirection = parseInt(document.getElementById('globalScanDirection').value);
            const scriptSelect = document.getElementById('scriptSelect');
            
            if (!globalScanDirection || !scriptSelect) {
                throw new Error('Required parameters not found');
            }
            
            if (!scriptSelect.value) {
                throw new Error('Please select a Multi-STS script');
            }
            
            this.updateStatus('Starting Local Multi-STS CITS...');
            
            const success = await pywebview.api.start_local_msts_cits(
                areas, scriptSelect.value, globalScanDirection
            );
            
            if (success) {
                this.updateStatus('Local Multi-STS CITS completed successfully');
                this.updateLastTime();
            } else {
                throw new Error('Local Multi-STS CITS failed');
            }
            
        } catch (error) {
            console.error('Local Multi-STS CITS error:', error);
            this.updateStatus('Error: ' + error.message);
        }
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    window.localCitsControl = new LocalCITSControl();
});

// 新增全局狀態對象
const sxmState = {
    center_x: null,
    center_y: null,
    range: null,
    angle: null,
    total_lines: null,
    last_update: null
};

// 更新狀態函數
function updateSxmState(newState) {
    Object.assign(sxmState, newState);
    updatePreviewDisplay();
}

// 更新預覽顯示
function updatePreviewDisplay() {
    document.getElementById('previewCenter').textContent = 
        `(${sxmState.center_x?.toFixed(2) || '-'}, ${sxmState.center_y?.toFixed(2) || '-'})`;
    document.getElementById('previewRange').textContent = 
        `${sxmState.range?.toFixed(2) || '-'}`;
    document.getElementById('previewAngle').textContent = 
        `${sxmState.angle?.toFixed(2) || '-'}`;
    
    // 如果有 canvas，也更新預覽圖
    if (sxmState.range && sxmState.angle) {
        updatePreviewCanvas();
    }
}

// 獲取 SXM 狀態
async function getSxmStatus() {
    try {
        const button = document.getElementById('getSxmStatus');
        button.disabled = true;
        button.textContent = 'Getting Status...';
        
        const status = await pywebview.api.get_sxm_status();
        updateSxmState(status);
        
        // 顯示成功消息
        const statusElement = document.getElementById('localCitsStatus');
        statusElement.textContent = `Status updated at ${status.timestamp}`;
        
    } catch (error) {
        console.error('Failed to get SXM status:', error);
        const statusElement = document.getElementById('localCitsStatus');
        statusElement.textContent = `Error: ${error.message}`;
    } finally {
        const button = document.getElementById('getSxmStatus');
        button.disabled = false;
        button.textContent = 'Get SXM Status';
    }
}

// 更新預覽畫布
function updatePreviewCanvas() {
    const canvas = document.getElementById('previewCanvas');
    const ctx = canvas.getContext('2d');
    
    // 清空畫布
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 計算縮放和旋轉
    const scale = Math.min(
        canvas.width / sxmState.range,
        canvas.height / sxmState.range
    ) * 0.8; // 留出邊距
    
    // 保存當前狀態
    ctx.save();
    
    // 移動到畫布中心
    ctx.translate(canvas.width/2, canvas.height/2);
    
    // 旋轉（角度轉弧度）
    ctx.rotate(sxmState.angle * Math.PI / 180);
    
    // 繪製掃描區域
    ctx.strokeStyle = '#2c3e50';
    ctx.lineWidth = 2;
    const size = sxmState.range * scale;
    ctx.strokeRect(-size/2, -size/2, size, size);
    
    // 繪製中心點
    ctx.fillStyle = '#e74c3c';
    ctx.beginPath();
    ctx.arc(0, 0, 3, 0, Math.PI * 2);
    ctx.fill();
    
    // 恢復狀態
    ctx.restore();
}

// 綁定事件監聽器
document.getElementById('getSxmStatus').addEventListener('click', getSxmStatus);

/**
 * Auto-Move Measurement Control
 * 整合了移動腳本控制、Multi-STS設定、CITS控制和Local CITS功能
 */
class AutoMoveControl {
    constructor() {
        // 初始化所有子控制器
        this.movementControl = new MovementScriptControl();
        this.smuVoltageControl = new AutoMoveSmuVoltageControl();
        this.previewControl = new AutoMovePreviewControl();
        this.citsControl = new AutoMoveCitsControl();
        this.localCitsControl = new AutoMoveLocalCitsControl();
    }
}

/**
 * 移動腳本控制器
 * 處理移動腳本的保存、載入和執行
 */
class MovementScriptControl {
    constructor() {
        this.bindEvents();
    }

    bindEvents() {
        const saveBtn = document.getElementById('saveAutoMoveScript');
        const scriptSelect = document.getElementById('autoMoveScriptSelect');
        
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveScript());
        }
        if (scriptSelect) {
            scriptSelect.addEventListener('change', (e) => this.loadScript(e.target.value));
        }

        // 載入現有腳本
        this.loadScriptList();
    }

    async saveScript() {
        try {
            const name = document.getElementById('moveScriptName').value.trim();
            const script = document.getElementById('movementScript').value.trim();
            const distance = parseFloat(document.getElementById('moveDistance').value);
            const waitTime = parseFloat(document.getElementById('waitTime').value);
            const repeatCount = parseInt(document.getElementById('repeatCount').value);

            if (!name || !script) {
                throw new Error('請輸入腳本名稱和移動指令');
            }

            await pywebview.api.save_auto_move_script({
                name,
                script,
                distance,
                waitTime,
                repeatCount
            });

            await this.loadScriptList();
            alert('腳本儲存成功');

        } catch (error) {
            alert('儲存腳本失敗: ' + error.message);
        }
    }

    async loadScriptList() {
        try {
            const scripts = await pywebview.api.get_auto_move_scripts();
            const select = document.getElementById('autoMoveScriptSelect');
            
            select.innerHTML = '<option value="">Select Script...</option>';
            
            Object.entries(scripts).forEach(([name, script]) => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
            });
        } catch (error) {
            console.error('載入腳本列表失敗:', error);
        }
    }

    async loadScript(scriptName) {
        if (!scriptName) return;

        try {
            const script = await pywebview.api.get_auto_move_script(scriptName);
            
            document.getElementById('moveScriptName').value = script.name;
            document.getElementById('movementScript').value = script.script;
            document.getElementById('moveDistance').value = script.distance;
            document.getElementById('waitTime').value = script.waitTime;
            document.getElementById('repeatCount').value = script.repeatCount;

        } catch (error) {
            alert('載入腳本失敗: ' + error.message);
        }
    }
}

/**
 * Auto-Move SMU電壓設定控制器
 */
class AutoMoveSmuVoltageControl {
    constructor() {
        this.bindEvents();
    }

    bindEvents() {
        document.getElementById('addAutoMoveStsRow')?.addEventListener('click', 
            () => this.addSettingRow());

        document.getElementById('autoMoveStsRows')?.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-row')) {
                this.removeSettingRow(e.target.closest('tr'));
            }
        });

        document.getElementById('saveAutoMoveStsScript')?.addEventListener('click',
            () => this.saveScript());

        document.getElementById('autoMoveStsScriptSelect')?.addEventListener('change',
            (e) => this.loadScript(e.target.value));
    }

    addSettingRow() {
        const tbody = document.getElementById('autoMoveStsRows');
        const row = document.createElement('tr');
        row.className = 'sts-row';
        row.innerHTML = `
            <td><input type="number" class="vds-input" value="0" step="0.1"></td>
            <td><input type="number" class="vg-input" value="0" step="0.1"></td>
            <td><button class="remove-row">×</button></td>
        `;
        tbody.appendChild(row);
    }

    removeSettingRow(row) {
        const rows = document.querySelectorAll('#autoMoveStsRows .sts-row');
        if (rows.length > 1) {
            row.remove();
        }
    }

    collectSettings() {
        const rows = document.querySelectorAll('#autoMoveStsRows .sts-row');
        const vds_list = [];
        const vg_list = [];

        rows.forEach(row => {
            vds_list.push(parseFloat(row.querySelector('.vds-input').value));
            vg_list.push(parseFloat(row.querySelector('.vg-input').value));
        });

        return { vds_list, vg_list };
    }

    async saveScript() {
        try {
            const name = document.getElementById('autoMoveStsScriptName').value.trim();
            if (!name) throw new Error('請輸入腳本名稱');

            const settings = this.collectSettings();
            await pywebview.api.save_sts_script(name, settings.vds_list, settings.vg_list);
            
            await this.loadScriptList();
            alert('腳本儲存成功');

        } catch (error) {
            alert('儲存腳本失敗: ' + error.message);
        }
    }

    async loadScriptList() {
        try {
            const scripts = await pywebview.api.get_sts_scripts();
            const select = document.getElementById('autoMoveStsScriptSelect');
            
            select.innerHTML = '<option value="">Select Script...</option>';
            
            Object.entries(scripts).forEach(([name, script]) => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
            });

        } catch (error) {
            console.error('載入腳本列表失敗:', error);
        }
    }
}

/**
 * Auto-Move預覽控制器
 */
class AutoMovePreviewControl {
    constructor() {
        this.canvas = document.getElementById('previewCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.setupCanvas();
        this.bindEvents();
    }

    setupCanvas() {
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        if (!this.canvas) return;

        const container = this.canvas.parentElement;
        const dpr = window.devicePixelRatio || 1;
        
        this.canvas.width = container.offsetWidth * dpr;
        this.canvas.height = container.offsetHeight * dpr;
        
        this.ctx.scale(dpr, dpr);
        this.canvas.style.width = `${container.offsetWidth}px`;
        this.canvas.style.height = `${container.offsetHeight}px`;
    }

    bindEvents() {
        document.getElementById('getSxmStatus')?.addEventListener('click',
            () => this.updateSxmStatus());
        document.getElementById('previewAutoMoveAreas')?.addEventListener('click',
            () => this.drawPreview());
        document.getElementById('startAutoMoveScan')?.addEventListener('click',
            () => this.startScan());
    }

    async updateSxmStatus() {
        try {
            const status = await pywebview.api.get_sxm_status();
            this.updateStatusDisplay(status);
            return status;
        } catch (error) {
            console.error('獲取SXM狀態失敗:', error);
            return null;
        }
    }

    updateStatusDisplay(status) {
        if (!status) return;

        document.getElementById('previewCenter').textContent = 
            `(${status.center_x?.toFixed(2) || '-'}, ${status.center_y?.toFixed(2) || '-'})`;
        document.getElementById('previewRange').textContent = 
            `${status.range?.toFixed(2) || '-'} nm`;
        document.getElementById('previewAngle').textContent = 
            `${status.angle?.toFixed(2) || '-'}°`;
    }

    drawPreview() {
        // 清除畫布
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        const status = this.updateSxmStatus();
        if (!status) return;

        // 繪製掃描範圍和移動路徑
        // 實際繪製邏輯將在後續實作...
    }

    async startScan() {
        try {
            const scriptName = document.getElementById('autoMoveScriptSelect').value;
            if (!scriptName) throw new Error('請選擇移動腳本');

            await pywebview.api.auto_move_scan_area(scriptName);
            
        } catch (error) {
            alert('啟動掃描失敗: ' + error.message);
        }
    }
}

/**
 * Auto-Move CITS控制器
 */
class AutoMoveCitsControl {
    constructor() {
        this.bindEvents();
    }

    bindEvents() {
        document.getElementById('startAutoMoveSstsCits')?.addEventListener('click',
            () => this.startSstsCits());
        document.getElementById('startAutoMoveMstsCits')?.addEventListener('click',
            () => this.startMstsCits());
    }

    async startSstsCits() {
        try {
            const pointsX = parseInt(document.getElementById('autoMoveCitsPointsX').value);
            const pointsY = parseInt(document.getElementById('autoMoveCitsPointsY').value);
            const direction = parseInt(document.getElementById('autoMoveCitsDirection').value);

            await pywebview.api.auto_move_ssts_cits(pointsX, pointsY, direction);
            
        } catch (error) {
            alert('啟動SSTS CITS失敗: ' + error.message);
        }
    }

    async startMstsCits() {
        try {
            const pointsX = parseInt(document.getElementById('autoMoveCitsPointsX').value);
            const pointsY = parseInt(document.getElementById('autoMoveCitsPointsY').value);
            const direction = parseInt(document.getElementById('autoMoveCitsDirection').value);
            const scriptName = document.getElementById('autoMoveStsScriptSelect').value;

            if (!scriptName) throw new Error('請選擇Multi-STS腳本');

            await pywebview.api.auto_move_msts_cits(
                pointsX, pointsY, scriptName, direction);
            
        } catch (error) {
            alert('啟動Multi-STS CITS失敗: ' + error.message);
        }
    }
}

/**
 * Auto-Move Local CITS控制器
 */
class AutoMoveLocalCitsControl {
    constructor() {
        this.canvas = document.getElementById('localPreviewCanvas');
        this.ctx = this.canvas?.getContext('2d');
        this.setupCanvas();
        this.bindEvents();
    }

    setupCanvas() {
        if (!this.canvas) return;
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        if (!this.canvas) return;

        const container = this.canvas.parentElement;
        const dpr = window.devicePixelRatio || 1;
        
        this.canvas.width = container.offsetWidth * dpr;
        this.canvas.height = container.offsetHeight * dpr;
        
        this.ctx.scale(dpr, dpr);
        this.canvas.style.width = `${container.offsetWidth}px`;
        this.canvas.style.height = `${container.offsetHeight}px`;
    }

    bindEvents() {
        document.getElementById('addAutoMoveLocalArea')?.addEventListener('click',
            () => this.addLocalArea());

        document.getElementById('autoMoveLocalAreasContainer')?.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-area')) {
                this.removeLocalArea(e.target.closest('.local-area-container'));
            }
        });

        document.getElementById('previewLocalCits')?.addEventListener('click',
            () => this.previewLocalCits());

        document.getElementById('startAutoMoveLocalSstsCits')?.addEventListener('click',
            () => this.startLocalSstsCits());

        document.getElementById('startAutoMoveLocalMstsCits')?.addEventListener('click',
            () => this.startLocalMstsCits());
    }

    addLocalArea() {
        const container = document.getElementById('autoMoveLocalAreasContainer');
        const areaTemplate = this.createLocalAreaTemplate();
        container.appendChild(areaTemplate);
    }

    removeLocalArea(areaElement) {
        const areas = document.querySelectorAll('.local-area-container');
        if (areas.length > 1) {
            areaElement.remove();
        }
    }

    createLocalAreaTemplate() {
        const div = document.createElement('div');
        div.className = 'local-area-container';
        div.innerHTML = `
            <div class="area-header">
                <span>Area Settings</span>
                <button class="remove-area danger-btn">Remove Area</button>
            </div>
    
            <div class="coordinate-settings">
                <div class="input-field">
                    <label>X Deviation (nm):</label>
                    <input type="number" class="x-dev" value="0" step="0.1">
                </div>
                <div class="input-field">
                    <label>Y Deviation (nm):</label>
                    <input type="number" class="y-dev" value="0" step="0.1">
                </div>
                <div class="input-field">
                    <label>Start Point Direction:</label>
                    <select class="startpoint-direction">
                        <option value="1">Up</option>
                        <option value="-1">Down</option>
                    </select>
                </div>
            </div>
    
            <div class="grid-settings">
                <div class="input-field">
                    <label>Step Size X (nm):</label>
                    <input type="number" class="dx" value="20" step="0.1">
                </div>
                <div class="input-field">
                    <label>Step Size Y (nm):</label>
                    <input type="number" class="dy" value="20" step="0.1">
                </div>
                <div class="input-field">
                    <label>X Points:</label>
                    <input type="number" class="nx" value="5" min="1" max="512">
                </div>
                <div class="input-field">
                    <label>Y Points:</label>
                    <input type="number" class="ny" value="3" min="1" max="512">
                </div>
            </div>
        `;
        return div;
    }

    collectLocalAreas() {
        const areas = [];
        document.querySelectorAll('.local-area-container').forEach(container => {
            areas.push({
                x_dev: parseFloat(container.querySelector('.x-dev').value),
                y_dev: parseFloat(container.querySelector('.y-dev').value),
                nx: parseInt(container.querySelector('.nx').value),
                ny: parseInt(container.querySelector('.ny').value),
                dx: parseFloat(container.querySelector('.dx').value),
                dy: parseFloat(container.querySelector('.dy').value),
                startpoint_direction: parseInt(container.querySelector('.startpoint-direction').value)
            });
        });
        return areas;
    }

    async previewLocalCits() {
        try {
            const areas = this.collectLocalAreas();
            const status = await pywebview.api.get_sxm_status();
            
            // 更新預覽...
            this.drawLocalPreview(status, areas);
            
        } catch (error) {
            console.error('預覽Local CITS失敗:', error);
        }
    }

    drawLocalPreview(status, areas) {
        if (!this.ctx) return;
        
        // 清除畫布
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 繪製預覽圖
        // 實際繪製邏輯將在後續實作...
    }

    async startLocalSstsCits() {
        try {
            const areas = this.collectLocalAreas();
            const direction = parseInt(document.getElementById('autoMoveLocalCitsGlobalDirection').value);
            
            this.updateStatus('Starting Auto-Move Local SSTS CITS...');
            
            const success = await pywebview.api.auto_move_local_ssts_cits(
                areas, direction
            );
            
            if (success) {
                this.updateStatus('Auto-Move Local SSTS CITS completed successfully');
                this.updateLastTime();
            } else {
                throw new Error('測量執行失敗');
            }
            
        } catch (error) {
            this.updateStatus(`Error: ${error.message}`);
            console.error('Local SSTS CITS失敗:', error);
        }
    }

    async startLocalMstsCits() {
        try {
            const areas = this.collectLocalAreas();
            const direction = parseInt(document.getElementById('autoMoveLocalCitsGlobalDirection').value);
            const scriptName = document.getElementById('autoMoveStsScriptSelect').value;
            
            if (!scriptName) {
                throw new Error('請選擇Multi-STS腳本');
            }
            
            this.updateStatus('Starting Auto-Move Local Multi-STS CITS...');
            
            const success = await pywebview.api.auto_move_local_msts_cits(
                areas, scriptName, direction
            );
            
            if (success) {
                this.updateStatus('Auto-Move Local Multi-STS CITS completed successfully');
                this.updateLastTime();
            } else {
                throw new Error('測量執行失敗');
            }
            
        } catch (error) {
            this.updateStatus(`Error: ${error.message}`);
            console.error('Local Multi-STS CITS失敗:', error);
        }
    }

    updateStatus(message) {
        const statusElement = document.getElementById('localCitsStatus');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }

    updateProgress(percent) {
        const progressElement = document.getElementById('localCitsProgress');
        if (progressElement) {
            progressElement.textContent = `${Math.round(percent)}%`;
        }
    }

    updateLastTime() {
        const timeElement = document.getElementById('localCitsLastTime');
        if (timeElement) {
            timeElement.textContent = new Date().toLocaleTimeString();
        }
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('Initializing Auto-Move Control...');
        window.autoMoveControl = new AutoMoveControl();
        console.log('Auto-Move Control initialized successfully');
    } catch (error) {
        console.error('Failed to initialize Auto-Move Control:', error);
    }
});