const STSMeasurementModule = {
    elements: {
        settingsRows: document.getElementById('stsSettingsRows'),
        scriptName: document.getElementById('smuscriptName'),
        saveScriptBtn: document.getElementById('saveScript'),
        scriptSelect: document.getElementById('smuscriptSelect'),
        updateScriptsBtn: document.getElementById('updateScriptBtn'),
        addStsRowBtn: document.getElementById('addStsRow'),
        startSingleStsBtn: document.getElementById('startSingleSts'),
        startMultiStsBtn: document.getElementById('startMultiSts'),
        statusDisplay: document.getElementById('stsStatus'),
    },
    state: {
        scripts: new Map(),
        currentScript: null,
    },

    init() {
        this.setupEventListeners();
        this.refreshScripts();
    },

    setupEventListeners() {
        // 添加新的設定行
        this.elements.addStsRowBtn.addEventListener('click', () => {
            this.addSettingRow();
        });

        // 儲存腳本
        this.elements.saveScriptBtn.addEventListener('click', () => {
            this.saveCurrentScript();
        });

        // 更新腳本列表
        this.elements.updateScriptsBtn.addEventListener('click', () => {
            this.refreshScripts();
        });

        // 當選擇不同腳本時加載腳本
        this.elements.scriptSelect.addEventListener('change', (e) => {
            this.loadScript(e.target.value);
        });

        // 啟動單次 STS 測量
        this.elements.startSingleStsBtn.addEventListener('click', () => {
            this.startSingleSts();
        });

        // 啟動多次 STS 測量
        this.elements.startMultiStsBtn.addEventListener('click', () => {
            this.startMultiSts();
        });
    },

    async refreshScripts() {
        try {
            const scripts = await pywebview.api.get_sts_scripts();
            console.log('Scripts from API:', scripts);
            this.state.scripts.clear();
            this.elements.scriptSelect.innerHTML = '<option value="">Select Script...</option>';

            for (const [name, data] of Object.entries(scripts)) {
                this.state.scripts.set(name, data);
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                this.elements.scriptSelect.appendChild(option);
            }

            this.updateStatus('Scripts updated successfully');
        } catch (error) {
            console.error('Failed to update scripts:', error);
            this.updateStatus('Failed to update scripts');
        }
    },

    loadScript(scriptName) {
        if (!scriptName) return;

        const script = this.state.scripts.get(scriptName);
        if (!script) {
            console.warn(`Script not found: ${scriptName}`);
            return;
        }

        // 清除現有的設定行
        this.elements.settingsRows.innerHTML = '';

        // 確保 vds_list 和 vg_list 長度相同
        const length = Math.min(script.vds_list.length, script.vg_list.length);

        // 根據腳本數據建立新的設定行
        for (let i = 0; i < length; i++) {
            this.addSettingRow(script.vds_list[i], script.vg_list[i]);
        }

        // 更新腳本名稱
        this.elements.scriptName.value = scriptName;
        this.state.currentScript = scriptName;
        this.updateStatus(`Loaded script: ${scriptName}`);
    },

    addSettingRow(vds = 0, vg = 0) {
        const row = document.createElement('div');
        row.className = 'sts-row';
        row.innerHTML = `
            <input type="number" class="vds-input" value="${vds}" step="0.1">
            <input type="number" class="vg-input" value="${vg}" step="0.1">
            <button class="remove-row" title="Remove">×</button>
        `;

        // 移除行按鈕
        row.querySelector('.remove-row').addEventListener('click', () => {
            row.remove();
        });

        this.elements.settingsRows.appendChild(row);
    },

    async saveCurrentScript() {
        const name = this.elements.scriptName.value.trim();
        if (!name) {
            this.updateStatus('Please provide a script name to save');
            return;
        }

        const vdsList = [];
        const vgList = [];
        this.elements.settingsRows.querySelectorAll('.sts-row').forEach((row) => {
            const vds = parseFloat(row.querySelector('.vds-input').value);
            const vg = parseFloat(row.querySelector('.vg-input').value);
            vdsList.push(vds);
            vgList.push(vg);
        });

        try {
            await pywebview.api.save_sts_script(name, vdsList, vgList);
            this.updateStatus(`Script "${name}" saved successfully`);
            this.refreshScripts();
        } catch (error) {
            console.error('Failed to save script:', error);
            this.updateStatus(`Failed to save script: ${error.message}`);
        }
    },

    async startSingleSts() {
        try {
            const success = await pywebview.api.start_sts();
            if (success) {
                this.updateStatus('Single STS measurement started');
            } else {
                this.updateStatus('Failed to start single STS measurement');
            }
        } catch (error) {
            console.error('Failed to start single STS:', error);
            this.updateStatus('Error starting single STS');
        }
    },

    async startMultiSts() {
        const scriptName = this.elements.scriptSelect.value;
        if (!scriptName) {
            this.updateStatus('Please select a script to start Multi-STS');
            return;
        }

        try {
            const success = await pywebview.api.perform_multi_sts(scriptName);
            if (success) {
                this.updateStatus(`Multi-STS measurement started with script "${scriptName}"`);
            } else {
                this.updateStatus('Failed to start Multi-STS measurement');
            }
        } catch (error) {
            console.error('Failed to start Multi-STS:', error);
            this.updateStatus('Error starting Multi-STS');
        }
    },

    updateStatus(message) {
        this.elements.statusDisplay.textContent = message;
    },
};

// // 初始化 STS 測量模組，當文檔完成載入時
// document.addEventListener('DOMContentLoaded', () => {
//     STSMeasurementModule.init();
// });

export default STSMeasurementModule;
