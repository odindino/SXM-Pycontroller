// SMU Configuration Module
const SMUConfigModule = {
    elements: {
        visaAddress: document.getElementById('visaAddress'),
        connectBtn: document.getElementById('connectBtn'),
        disconnectBtn: document.getElementById('disconnectBtn'),
        connectionStatus: document.getElementById('connectionStatus'),
        channels: {
            1: {
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
            2: {
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
            }
        }
    },

    state: {
        connected: false,
        channelStates: {
            1: { outputOn: false },
            2: { outputOn: false }
        }
    },

    init() {
        this.setupConnectionHandlers();
        this.setupChannelHandlers(1);
        this.setupChannelHandlers(2);
        this.updateConnectionStatus(false);
    },

    setupConnectionHandlers() {
        this.elements.connectBtn.addEventListener('click', () => this.handleConnect());
        this.elements.disconnectBtn.addEventListener('click', () => this.handleDisconnect());
    },

    async handleConnect() {
        try {
            const address = this.elements.visaAddress.value.trim();
            if (!address) {
                alert('請輸入VISA地址');
                return;
            }
            
            this.elements.connectBtn.disabled = true;
            this.elements.connectBtn.textContent = '連接中...';
            
            await pywebview.api.connect_smu(address);
            this.updateConnectionStatus(true);
            
        } catch (error) {
            alert('連接失敗: ' + error);
            this.updateConnectionStatus(false);
        } finally {
            this.elements.connectBtn.disabled = false;
            this.elements.connectBtn.textContent = 'Connect';
        }
    },

    async handleDisconnect() {
        try {
            this.elements.disconnectBtn.disabled = true;
            this.elements.disconnectBtn.textContent = '斷開中...';
            
            await pywebview.api.disconnect_smu();
            this.updateConnectionStatus(false);
            
        } catch (error) {
            alert('斷開連接失敗: ' + error);
        } finally {
            this.elements.disconnectBtn.disabled = false;
            this.elements.disconnectBtn.textContent = 'Disconnect';
        }
    },

    setupChannelHandlers(channelNum) {
        const ch = this.elements.channels[channelNum];
        
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
                this.state.channelStates[channelNum].outputOn = newState;
            } catch (error) {
                alert(`切換輸出 ${channelNum} 失敗: ${error}`);
            }
        });

        // 讀值按鈕
        ch.readBtn.addEventListener('click', () => this.readChannel(channelNum));

        // Compliance控制
        ch.setComplianceBtn.addEventListener('click', async () => {
            try {
                const value = parseFloat(ch.compliance.value);
                await pywebview.api.set_compliance(channelNum, value);
            } catch (error) {
                alert(`設定compliance失敗: ${error}`);
            }
        });

        ch.readComplianceBtn.addEventListener('click', async () => {
            try {
                const value = await pywebview.api.get_compliance(channelNum);
                ch.compliance.value = value.toFixed(3);
            } catch (error) {
                alert(`讀取compliance失敗: ${error}`);
            }
        });
    },

    async readChannel(channel) {
        try {
            const ch = this.elements.channels[channel];
            ch.readBtn.disabled = true;
            ch.readBtn.textContent = 'Reading...';
            
            const reading = await pywebview.api.read_channel(channel);
            
            ch.voltage.textContent = `${reading.voltage.toFixed(6)} V`;
            const currentInMicroAmps = reading.current * 1e6;
            ch.current.textContent = `${currentInMicroAmps.toFixed(6)} μA`;
            ch.lastRead.textContent = new Date().toLocaleTimeString();
            
        } catch (error) {
            alert(`讀值失敗: ${error}`);
        } finally {
            const ch = this.elements.channels[channel];
            ch.readBtn.disabled = false;
            ch.readBtn.textContent = 'Read Values';
        }
    },

    updateConnectionStatus(connected) {
        this.state.connected = connected;
        
        if (this.elements.connectionStatus) {
            this.elements.connectionStatus.className = 
                `status-indicator status-${connected ? 'connected' : 'disconnected'}`;
        }
        
        this.elements.connectBtn.disabled = connected;
        this.elements.disconnectBtn.disabled = !connected;
        
        // 更新通道控制狀態
        [1, 2].forEach(channelNum => {
            const ch = this.elements.channels[channelNum];
            ch.setBtn.disabled = !connected;
            ch.outputBtn.disabled = !connected;
            ch.readBtn.disabled = !connected;
            ch.mode.disabled = !connected;
            ch.value.disabled = !connected;
            ch.setComplianceBtn.disabled = !connected;
            ch.readComplianceBtn.disabled = !connected;
            ch.compliance.disabled = !connected;
        });
    }
};

// 匯出模組
export default SMUConfigModule;