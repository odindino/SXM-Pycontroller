const STSMeasurementModule = {
    elements: {
        addRowBtn: document.getElementById('addStsRow'),
        settingsRows: document.getElementById('stsSettingsRows'),
        scriptName: document.getElementById('scriptName'),
        smuscriptSelect: document.getElementById('smuscriptSelect'),
        saveScriptBtn: document.getElementById('saveScript'),
        startSingleStsBtn: document.getElementById('startSingleSts'),
        startMultiStsBtn: document.getElementById('startMultiSts'),
        stsStatus: document.getElementById('stsStatus'),
        updateBtn: document.getElementById('updateScriptBtn')
    },

    state: {
        isRunning: false,
        currentScript: null,
        scripts: new Map()
    },

    init() {
        this.setupEventListeners();
        this.loadScripts();
    },

    init() {
        console.log('Initializing STS Measurement Module...');
        
        // 檢查必要的元素是否存在
        Object.entries(this.elements).forEach(([key, element]) => {
            if (!element) {
                console.warn(`Missing element: ${key}`);
            }
        });
        
        // 先載入腳本，再設定事件監聽器
        this.loadScripts().then(() => {
            this.setupEventListeners();
            console.log('STS Measurement Module initialized successfully');
        }).catch(error => {
            console.error('Failed to initialize STS Measurement Module:', error);
        });
    },

    setupEventListeners() {
        // Add row按鈕
        this.elements.addRowBtn.addEventListener('click', () => this.addSettingRow());

        // 儲存腳本按鈕
        this.elements.saveScriptBtn.addEventListener('click', () => this.saveCurrentScript());

        // 腳本選擇下拉選單
        this.elements.smuscriptSelect.addEventListener('change', (e) => {
            this.loadScript(e.target.value);
        });

        // 新增更新按鈕的事件監聽器
        this.elements.updateBtn.addEventListener('click', () => this.refreshScripts());

        // Single STS按鈕
        this.elements.startSingleStsBtn.addEventListener('click', () => {
            this.startSTS(false);
        });

        // Multi-STS按鈕
        this.elements.startMultiStsBtn.addEventListener('click', () => {
            this.perform_multi_sts();
        });

        // 動態移除row按鈕的事件委派
        this.elements.settingsRows.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-row')) {
                this.removeSettingRow(e.target);
            }
        });
    },

    addSettingRow() {
        const row = document.createElement('div');
        row.className = 'sts-row';
        row.innerHTML = `
            <input type="number" class="vds-input" value="0" step="0.1">
            <input type="number" class="vg-input" value="0" step="0.1">
            <button class="remove-row" title="Remove">×</button>
        `;
        this.elements.settingsRows.appendChild(row);
    },

    removeSettingRow(button) {
        const rows = document.querySelectorAll('.sts-row');
        if (rows.length > 1) {
            button.closest('.sts-row').remove();
        } else {
            alert('At least one setting row must be maintained');
        }
    },

    async saveCurrentScript() {
        try {
            const name = this.elements.scriptName.value.trim();
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
                await this.loadScripts();
                this.updateStatus('Script saved successfully');
            }
        } catch (error) {
            this.updateStatus(`Error saving script: ${error}`);
            alert(`Error saving script: ${error}`);
        }
    },

    async refreshScripts() {
        try {
            // 更新按鈕視覺反饋
            const updateBtn = document.getElementById('updateScriptBtn');
            updateBtn.disabled = true;
            updateBtn.textContent = 'Updating...';

            // 清空現有的選項
            const select = this.elements.smuscriptSelect;
            select.innerHTML = '<option value="">Select Script...</option>';

            // 重新載入腳本
            const scripts = await pywebview.api.get_sts_scripts();
            
            // 更新下拉選單
            Object.keys(scripts).forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
            });

            this.updateStatus('Scripts updated successfully');

        } catch (error) {
            this.updateStatus(`Error updating scripts: ${error}`);
            console.error('Script refresh error:', error);
        } finally {
            // 恢復按鈕狀態
            const updateBtn = document.getElementById('updateScriptBtn');
            updateBtn.disabled = false;
            updateBtn.textContent = 'Update Scripts';
        }
    },

    // async loadScripts() {
    //     try {
    //         const scripts = await pywebview.api.get_sts_scripts();
    //         this.state.scripts = new Map(Object.entries(scripts));
            
    //         const select = this.elements.scriptSelect;
    //         select.innerHTML = '<option value="">Select Script...</option>';
            
    //         this.state.scripts.forEach((script, name) => {
    //             const option = document.createElement('option');
    //             option.value = name;
    //             option.textContent = name;
    //             select.appendChild(option);
    //         });
    //     } catch (error) {
    //         console.error('Error loading scripts:', error);
    //         this.updateStatus('Error loading scripts');
    //     }
    // },

    async loadScripts() {
        try {
            console.log('Loading STS scripts...');
            
            const scripts = await pywebview.api.get_sts_scripts();
            console.log('Received scripts:', scripts);
            
            this.state.scripts = new Map(Object.entries(scripts));
            
            const select = this.elements.smuscriptSelect;
            if (!select) {
                throw new Error('Script select element not found');
            }
            
            // 更新選單
            select.innerHTML = '<option value="">Select Script...</option>';
            let scriptCount = 0;
            
            this.state.scripts.forEach((script, name) => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
                scriptCount++;
            });
            
            console.log(`Loaded ${scriptCount} scripts successfully`);
            
        } catch (error) {
            console.error('Error loading scripts:', error);
            this.updateStatus('Error loading scripts');
            throw error;
        }
    },

    loadScript(scriptName) {
        if (!scriptName) return;
        
        const script = this.state.scripts.get(scriptName);
        if (!script) return;

        // 清除現有的所有行
        this.elements.settingsRows.innerHTML = '';

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
            this.elements.settingsRows.appendChild(row);
        }

        this.elements.scriptName.value = scriptName;
        this.state.currentScript = scriptName;
        this.updateStatus(`Loaded script: ${scriptName}`);
    },

    async loadScripts() {
        try {
            console.log('開始載入 STS 腳本...');
            
            // 等待腳本資料
            const response = await pywebview.api.get_sts_scripts();
            console.log('收到腳本資料:', response);
            
            if (!response) {
                throw new Error('未收到腳本資料');
            }
            
            // 更新內部狀態
            this.state.scripts = new Map(Object.entries(response));
            
            // 獲取選單元素
            const select = this.elements.smuscriptSelect;
            if (!select) {
                throw new Error('找不到腳本選單元素');
            }
            
            // 重置選單
            select.innerHTML = '<option value="">Select Script...</option>';
            
            // 填充選單
            let addedScripts = 0;
            this.state.scripts.forEach((script, name) => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
                addedScripts++;
            });
            
            console.log(`成功載入 ${addedScripts} 個腳本`);
            this.updateStatus(`已載入 ${addedScripts} 個腳本`);
            
        } catch (error) {
            console.error('載入腳本時發生錯誤:', error);
            this.updateStatus('載入腳本時發生錯誤');
            
            // 顯示詳細錯誤資訊
            console.error('完整錯誤資訊:', {
                message: error.message,
                stack: error.stack,
                state: this.state,
                elements: Object.keys(this.elements).reduce((acc, key) => {
                    acc[key] = this.elements[key] ? 'exists' : 'missing';
                    return acc;
                }, {})
            });
        }
    },

    collectCurrentSettings() {
        const rows = document.querySelectorAll('.sts-row');
        const vds_list = [];
        const vg_list = [];

        rows.forEach(row => {
            vds_list.push(parseFloat(row.querySelector('.vds-input').value));
            vg_list.push(parseFloat(row.querySelector('.vg-input').value));
        });

        return { vds_list, vg_list };
    },

    async startSTS() {
        if (this.state.isRunning) return;

        try {
            this.state.isRunning = true;
            this.elements.startSingleStsBtn.disabled = true;
            this.elements.startSingleStsBtn.textContent = 'Starting STS...';
            
            this.updateStatus('Initiating STS measurement...');
            const success = await pywebview.api.start_sts();
            
            if (success) {
                this.updateStatus('STS measurement completed successfully');
            } else {
                throw new Error('STS measurement failed');
            }
            
        } catch (error) {
            this.updateStatus(`Error: ${error.message}`);
            alert(`Error performing STS: ${error.message}`);
        } finally {
            this.state.isRunning = false;
            this.elements.startSingleStsBtn.disabled = false;
            this.elements.startSingleStsBtn.textContent = 'Start Single STS';
        }
    },

    async perform_multi_sts() {
        if (this.state.isRunning) return;

        try {
            const scriptName = this.elements.smuscriptSelect.value;
            if (!scriptName) {
                alert('Please select a script first');
                return;
            }

            this.state.isRunning = true;
            this.elements.startMultiStsBtn.disabled = true;
            this.elements.startMultiStsBtn.textContent = 'Running Multi-STS...';
            
            this.updateStatus('Performing Multi-STS measurement...');
            const success = await pywebview.api.perform_multi_sts(scriptName);
            
            if (success) {
                this.updateStatus('Multi-STS measurements completed successfully');
            } else {
                throw new Error('Multi-STS measurements failed');
            }
            
        } catch (error) {
            this.updateStatus(`Error: ${error.message}`);
            alert(`Error performing Multi-STS: ${error.message}`);
        } finally {
            this.state.isRunning = false;
            this.elements.startMultiStsBtn.disabled = false;
            this.elements.startMultiStsBtn.textContent = 'Start Multi-STS';
        }
    },

    updateStatus(message) {
        if (this.elements.stsStatus) {
            this.elements.stsStatus.textContent = message;
        }
        console.log(`[STS Status] ${message}`);
    }
};

// 匯出模組
export default STSMeasurementModule;