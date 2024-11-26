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
    // 設置事件監聽器
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

// 頁面載入完成後初始化
document.addEventListener('DOMContentLoaded', initialize);

// STS控制相關功能
class STSControl {
    constructor() {
        this.setupEventListeners();
        this.loadScripts();
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
            this.startSTS(true);
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

        const scripts = this.scripts;
        const script = scripts[scriptName];
        if (!script) return;

        // 清除現有行
        const container = document.getElementById('stsSettingsRows');
        container.innerHTML = '';

        // 添加腳本中的設定
        script.vds_list.forEach((vds, index) => {
            const row = document.createElement('div');
            row.className = 'sts-row';
            row.innerHTML = `
                <input type="number" class="vds-input" value="${vds}" step="0.1">
                <input type="number" class="vg-input" value="${script.vg_list[index]}" step="0.1">
                <button class="remove-row" title="Remove">×</button>
            `;
            container.appendChild(row);
        });
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

    async startSTS(isMulti) {
        try {
            const buttons = document.querySelectorAll('#startSingleSts, #startMultiSts');
            buttons.forEach(btn => btn.disabled = true);
            
            if (isMulti) {
                const scriptName = document.getElementById('scriptSelect').value;
                if (!scriptName) {
                    alert('Please select a script');
                    return;
                }
                await pywebview.api.perform_multi_sts(scriptName);
            } else {
                // 單次STS
                await pywebview.api.start_sts();
            }
            
            console.log(`${isMulti ? 'Multi' : 'Single'} STS completed successfully`);
            
        } catch (error) {
            console.error('STS Error:', error);
            alert(`Error performing STS: ${error}`);
        } finally {
            buttons.forEach(btn => btn.disabled = false);
        }
    }
}

// 初始化時建立STS控制實例
document.addEventListener('DOMContentLoaded', () => {
    window.stsControl = new STSControl();
});