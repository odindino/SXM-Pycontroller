// auto-move-measurement.js

const AutoMoveMeasurementModule = {
    elements: {
        // Movement Script Controls
        scriptName: document.getElementById('amScriptName'),
        scriptSelect: document.getElementById('amScriptSelect'),
        saveScriptBtn: document.getElementById('amSaveScript'),
        updateMovementScriptsBtn: document.getElementById('amUpdateMovementScriptBtn'), // 新增的 Update Movement Scripts 按鈕
        movementScript: document.getElementById('amMovementScript'),  // 修正: 之前是'movementScript'
        moveDistance: document.getElementById('amDistance'),         // 修正: 之前是'moveDistance'
        waitTime: document.getElementById('amWaitTime'),            // 修正: 之前是'waitTime'
        repeatCount: document.getElementById('amRepeatCount'),      // 修正: 之前是'repeatCount'
        
        // STS Settings
        stsScriptName: document.getElementById('amStsScriptName'),
        stsScriptSelect: document.getElementById('amStsScriptSelect'),
        saveStsScriptBtn: document.getElementById('amSaveScriptSts'),  // 修正: 之前是'amSaveStsScript'
        updateStsScriptsBtn: document.getElementById('amUpdateStsScriptBtn'), // 新增的 Update STS Scripts 按鈕
        stsSettingsRows: document.getElementById('amStsSettingsRows'),
        addStsRowBtn: document.getElementById('amAddStsRow'),

        // Preview & Status
        previewCanvas: document.getElementById('amMovePreview'),
        getSxmStatusBtn: document.getElementById('getSxmStatusBtn'),
        previewAutoMoveBtn: document.getElementById('previewAutoMoveBtn'),
        
        
        // CITS Controls
        pointsX: document.getElementById('amCitsPointsX'),
        pointsY: document.getElementById('amCitsPointsY'),
        scanDirection: document.getElementById('amCitsScanDirection'),  // 修正: 之前是'amScanDirection'
        startAutoMoveSstsBtn: document.getElementById('amStartSstsCits'), // 修正: 之前名稱不符
        startAutoMoveMstsBtn: document.getElementById('amStartMstsCits'), // 修正: 之前名稱不符
        
        // Local CITS Controls
        globalDirection: document.getElementById('amGlobalDirection'),
        localAreasContainer: document.getElementById('amLocalAreasContainer'),
        addLocalAreaBtn: document.getElementById('amAddLocalArea'),
        startLocalSstsBtn: document.getElementById('amStartLocalSstsCits'),
        startLocalMstsBtn: document.getElementById('amStartLocalMstsCits'),
        
        // Preview & Status

        // Local CITS Preview elements
        getLocalCitsStatusBtn: document.getElementById('getLocalCitsStatusBtn'),
        previewLocalCitsBtn: document.getElementById('previewLocalCitsBtn'),
        localPreviewCanvas: document.getElementById('amLocalCitsPreview'),
        localPreviewCenter: document.getElementById('localPreviewCenter'),
        localPreviewRange: document.getElementById('localPreviewRange'),
        localPreviewAngle: document.getElementById('localPreviewAngle'),
        localPreviewTotalPoints: document.getElementById('localPreviewTotalPoints'),
        localCitsStatus: document.getElementById('amLocalCitsStatus'),
        localCitsProgress: document.getElementById('amLocalCitsProgress'),
        localCitsLastTime: document.getElementById('amLocalCitsLastTime'),

        // previewCanvas: document.getElementById('amMovePreview'),
        // localCitsPreview: document.getElementById('amLocalCitsPreview'),
        // statusDisplay: document.getElementById('amLocalCitsStatus'),
        // progressDisplay: document.getElementById('amLocalCitsProgress'),
        // lastTimeDisplay: document.getElementById('amLocalCitsLastTime')
    },

    state: {
        movementScripts: new Map(),
        stsScripts: new Map(),
        currentMovementScript: null,
        currentStsScript: null,
        isRunning: false,
        currentScript: null,
        currentStsScript: null,
        localAreas: [],
        areaCounter: 0,
        previewContext: null,
        localPreviewContext: null
    },

    init() {

        //     console.log('Initializing Auto Move Measurement Module...');
        
        // // 為初始的 Remove Area 按鈕綁定事件
        // const initialRemoveBtn = document.querySelector('.local-area-container .remove-area');
        // if (initialRemoveBtn) {
        //     const areaContainer = initialRemoveBtn.closest('.local-area-container');
        //     if (areaContainer) {
        //         initialRemoveBtn.addEventListener('click', () => this.removeArea(areaContainer.id));
        //     }
        // }
        console.log('Initializing Auto Move Measurement Module...');

        // 檢查 Plotly 是否已載入
        if (typeof Plotly === 'undefined') {
            console.error('Plotly library not loaded');
            this.updateStatus('Plotly library not loaded');
            return;
        }

        this.setupEventListeners();
        // this.refreshMovementScripts();
        // this.refreshStsScripts();
        // this.initializeCanvases();
        // this.createInitialArea();
        // this.loadScripts();
    },

    setupEventListeners() {
        // Movement Script Controls
        this.elements.saveScriptBtn.addEventListener('click', () => this.saveMovementScript());
        this.elements.updateMovementScriptsBtn.addEventListener('click', () => this.refreshMovementScripts()); // 綁定更新 Movement Script 的事件
        this.elements.scriptSelect.addEventListener('change', (e) => this.loadMovementScript(e.target.value));
        
        // STS Controls
        this.elements.saveStsScriptBtn.addEventListener('click', () => this.saveStsScript());
        this.elements.updateStsScriptsBtn.addEventListener('click', () => this.refreshStsScripts()); // 綁定更新 STS Script 的事件
        this.elements.addStsRowBtn.addEventListener('click', () => this.addStsRow());
        this.elements.stsScriptSelect.addEventListener('change', (e) => this.loadStsScript(e.target.value));
        
        // Preview 按鈕事件
        if (this.elements.getSxmStatusBtn) {
            this.elements.getSxmStatusBtn.addEventListener('click', () => this.updateSxmStatus());
        } else {
            console.error('Get SXM Status button not found');
        }

        if (this.elements.previewAutoMoveBtn) {
            this.elements.previewAutoMoveBtn.addEventListener('click', () => this.previewAutoMove());
        } else {
            console.error('Preview Auto Move button not found');
        }

        // this.elements.getSxmStatusBtn.addEventListener('click', () => this.updateSxmStatus());
        // this.elements.previewAutoMoveBtn.addEventListener('click', () => this.previewAutoMove());
       
        // CITS Controls
        this.elements.startAutoMoveSstsBtn.addEventListener('click', () => this.startAutoMoveSstsCits());
        this.elements.startAutoMoveMstsBtn.addEventListener('click', () => this.startAutoMoveMstsCits());
        
        // Local CITS Controls
        this.elements.addLocalAreaBtn.addEventListener('click', () => this.addLocalArea());
        this.elements.startLocalSstsBtn.addEventListener('click', () => this.startAutoMoveLocalSstsCits());
        this.elements.startLocalMstsBtn.addEventListener('click', () => this.startAutoMoveLocalMstsCits());
        
        // Input Validation
        this.elements.pointsX.addEventListener('change', () => this.validatePoints(this.elements.pointsX));
        this.elements.pointsY.addEventListener('change', () => this.validatePoints(this.elements.pointsY));
    
        // Local CITS Preview 按鈕事件
        if (this.elements.getLocalCitsStatusBtn) {
            this.elements.getLocalCitsStatusBtn.addEventListener('click', () => this.updateLocalCitsStatus());
        } else {
            console.error('Get Local CITS Status button not found');
        }

        if (this.elements.previewLocalCitsBtn) {
            this.elements.previewLocalCitsBtn.addEventListener('click', () => this.previewLocalCits());
        } else {
            console.error('Preview Local CITS button not found');
        }
    },

    async refreshMovementScripts() {
        try {
            const scripts = await pywebview.api.get_auto_move_scripts();
            console.log('Movement Scripts from API:', scripts);
            this.state.movementScripts.clear();
            this.elements.scriptSelect.innerHTML = '<option value="">Select Script...</option>';

            for (const [name, data] of Object.entries(scripts)) {
                this.state.movementScripts.set(name, data);
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                this.elements.scriptSelect.appendChild(option);
            }

            this.updateStatus('Movement scripts updated successfully');
        } catch (error) {
            console.error('Failed to update movement scripts:', error);
            this.updateStatus('Failed to update movement scripts');
        }
    },

    async refreshStsScripts() {
        try {
            const scripts = await pywebview.api.get_sts_scripts();
            console.log('STS Scripts from API:', scripts);
            this.state.stsScripts.clear();
            this.elements.stsScriptSelect.innerHTML = '<option value="">Select STS Script...</option>';

            for (const [name, data] of Object.entries(scripts)) {
                this.state.stsScripts.set(name, data);
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                this.elements.stsScriptSelect.appendChild(option);
            }

            this.updateStatus('STS scripts updated successfully');
        } catch (error) {
            console.error('Failed to update STS scripts:', error);
            this.updateStatus('Failed to update STS scripts');
        }
    },

    loadMovementScript(scriptName) {
        if (!scriptName) return;

        const script = this.state.movementScripts.get(scriptName);
        if (!script) {
            console.warn(`Script not found: ${scriptName}`);
            return;
        }

        // 將腳本數據加載到 UI
        this.elements.scriptName.value = script.name;
        this.elements.movementScript.value = script.script;
        this.elements.moveDistance.value = script.distance;
        this.elements.waitTime.value = script.waitTime;
        this.elements.repeatCount.value = script.repeatCount;
        
        this.updateStatus(`Loaded movement script: ${scriptName}`);
    },

    loadStsScript(scriptName) {
        if (!scriptName) return;
    
        const script = this.state.stsScripts.get(scriptName);
        if (!script) {
            console.warn(`Script not found: ${scriptName}`);
            return;
        }
    
        // 確認 stsSettingsRows 存在
        if (!this.elements.stsSettingsRows) {
            console.error('Error: stsSettingsRows element not found');
            return;
        }
    
        // 清除現有的設定行
        this.elements.stsSettingsRows.innerHTML = '';
    
        // 確保 vds_list 和 vg_list 長度相同
        const length = Math.min(script.vds_list.length, script.vg_list.length);
        for (let i = 0; i < length; i++) {
            this.addStsRow(script.vds_list[i], script.vg_list[i]);
        }
    
        // 更新腳本名稱
        this.elements.stsScriptName.value = scriptName;
        this.updateStatus(`Loaded STS script: ${scriptName}`);
    },

    async saveMovementScript() {
        const scriptData = {
            name: this.elements.scriptName.value.trim(),
            script: this.elements.movementScript.value.trim(),
            distance: parseFloat(this.elements.moveDistance.value),
            waitTime: parseFloat(this.elements.waitTime.value),
            repeatCount: parseInt(this.elements.repeatCount.value, 10),
        };

        if (!this.validateMovementScript(scriptData)) {
            return;
        }

        try {
            await pywebview.api.save_auto_move_script(scriptData);
            this.updateStatus('Movement script saved successfully');
            this.refreshMovementScripts();
        } catch (error) {
            console.error('Failed to save movement script:', error);
            this.updateStatus(`Failed to save movement script: ${error.message}`);
        }
    },

    async saveStsScript() {
        const name = this.elements.stsScriptName.value.trim();
        if (!name) {
            this.updateStatus('Please provide a script name to save');
            return;
        }

        const vdsList = [];
        const vgList = [];
        this.elements.stsSettingsRows.querySelectorAll('.sts-row').forEach((row) => {
            const vds = parseFloat(row.querySelector('.vds-input').value);
            const vg = parseFloat(row.querySelector('.vg-input').value);
            vdsList.push(vds);
            vgList.push(vg);
        });

        try {
            await pywebview.api.save_sts_script(name, vdsList, vgList);
            this.updateStatus(`STS script "${name}" saved successfully`);
            this.refreshStsScripts();
        } catch (error) {
            console.error('Failed to save STS script:', error);
            this.updateStatus(`Failed to save STS script: ${error.message}`);
        }
    },

    addStsRow(vds = 0, vg = 0) {
        if (!this.elements.stsSettingsRows) {
            console.error('Error: stsSettingsRows element not found');
            return;
        }
    
        const row = document.createElement('div');
        row.className = 'sts-row';
        row.innerHTML = `
            <input type="number" class="vds-input" value="${vds}" step="0.1">
            <input type="number" class="vg-input" value="${vg}" step="0.1">
            <button class="remove-row" title="Remove">×</button>
        `;
    
        // 綁定移除行按鈕事件
        row.querySelector('.remove-row').addEventListener('click', () => row.remove());
    
        // 將新建的行添加到 stsSettingsRows 中
        this.elements.stsSettingsRows.appendChild(row);
    },

    updateStatus(message) {
        if (this.elements.statusDisplay) {
            this.elements.statusDisplay.textContent = message;
        }
        console.log(`[Auto-Move Status] ${message}`);
    },

    // initializeCanvases() {
    //     // 初始化移動預覽畫布
    //     const movePreview = this.elements.previewCanvas;
    //     movePreview.width = movePreview.offsetWidth;
    //     movePreview.height = movePreview.offsetHeight;
    //     this.state.previewContext = movePreview.getContext('2d');
        
    //     // 初始化Local CITS預覽畫布
    //     const localPreview = this.elements.localCitsPreview;
    //     localPreview.width = localPreview.offsetWidth;
    //     localPreview.height = localPreview.offsetHeight;
    //     this.state.localPreviewContext = localPreview.getContext('2d');
    // },

    async previewAutoMove() {
        try {
            console.log('Starting preview generation...');
            
            // 確認已選擇腳本
            const scriptSelect = this.elements.scriptSelect;
            if (!scriptSelect) {
                console.error('Script select element not found');
                this.updateStatus('Script select element not found');
                return;
            }
    
            if (!scriptSelect.value) {
                this.updateStatus('Please select a movement script');
                return;
            }
    
            // 從狀態中取得已載入的腳本
            const selectedScript = this.state.movementScripts.get(scriptSelect.value);
            console.log('Selected script:', selectedScript);
            
            if (!selectedScript) {
                this.updateStatus('Selected script not found');
                return;
            }
    
            // 準備參數
            const params = {
                movement_script: selectedScript.script,
                distance: selectedScript.distance,
                center_x: null,
                center_y: null,
                angle: null
            };
    
            console.log('Fetching SXM status...');
            // 取得 SXM 狀態
            const sxmStatus = await pywebview.api.get_sxm_status();
            console.log('SXM status:', sxmStatus);
            
            // 更新參數
            params.center_x = sxmStatus.center_x;
            params.center_y = sxmStatus.center_y;
            params.angle = sxmStatus.angle;
            
            console.log('Generating preview with params:', params);

            
            // 生成預覽圖
            const plotData = await pywebview.api.preview_auto_move(params);
            
            // 確保 preview canvas 存在
            if (!this.elements.previewCanvas) {
                console.error('Preview canvas element not found');
                this.updateStatus('Preview canvas not found');
                return;
            }
            
            // 設定配置選項
            const config = {
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                hovermode: 'closest'
            };

            // 額外的版面配置設定
            const layout = {
                ...plotData.layout,
                hoverlabel: {
                    bgcolor: '#FFF',
                    font: { size: 14 },
                    bordercolor: '#888'
                },
                showlegend: true,
                legend: {
                    x: 1.05,
                    y: 1
                }
            };

            // 將圖表放入預覽區域
            console.log('Plotting data:', plotData);
            Plotly.newPlot(this.elements.previewCanvas, plotData.data, layout, config);
            
            // 監聽視窗大小變化
            window.addEventListener('resize', () => {
                Plotly.Plots.resize(this.elements.previewCanvas);
            });
            
            this.updateStatus('Preview generated successfully');
    
        } catch (error) {
            console.error('Preview error:', error);
            this.updateStatus(`Preview error: ${error.message}`);
        }
    },

    // 新增 updateSxmStatus 方法
    async updateSxmStatus() {
        try {
            const status = await pywebview.api.get_sxm_status();
            const centerX = status.center_x.toFixed(2);
            const centerY = status.center_y.toFixed(2);
            const angle = status.angle.toFixed(2);
            const range = status.range.toFixed(2);
            
            this.updateStatus(`Scan center: (${centerX}, ${centerY}) nm, `+
                            `Range: ${range} nm, Angle: ${angle}°`);
        } catch (error) {
            this.updateStatus(`Failed to get SXM status: ${error.message}`);
        }
    },

    // createInitialArea() {
    //     this.elements.localAreasContainer.innerHTML = '';
    //     // this.addLocalArea();
    // },

    addLocalArea() {
        const areaId = `am-area-${++this.state.areaCounter}`;
        const container = document.createElement('div');
        container.className = 'local-area-container';
        container.id = areaId;
        
        container.innerHTML = `
            <div class="input-group position-group">
                <label>Start Position:</label>
                <div class="position-inputs">
                    <div class="coordinate-input">
                        <label>x_dev:</label>
                        <div class="input-with-unit">
                            <input type="number" class="x-dev" value="200" step="0.1">
                            <span class="unit">nm</span>
                        </div>
                    </div>
                    <div class="coordinate-input">
                        <label>y_dev:</label>
                        <div class="input-with-unit">
                            <input type="number" class="y-dev" value="200" step="0.1">
                            <span class="unit">nm</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="input-group">
                <label>Start Point Direction:</label>
                <select class="start-direction">
                    <option value="1">Up</option>
                    <option value="-1">Down</option>
                </select>
            </div>

            <div class="parameters-row">
                <div class="input-field">
                    <label>Step Size X (ΔX)</label>
                    <div class="input-with-unit">
                        <input type="number" class="dx" value="20" step="0.1">
                        <span class="unit">nm</span>
                    </div>
                </div>
                <div class="input-field">
                    <label>Step Size Y (ΔY)</label>
                    <div class="input-with-unit">
                        <input type="number" class="dy" value="20" step="0.1">
                        <span class="unit">nm</span>
                    </div>
                </div>
                <div class="input-field">
                    <label>Points X (Nx)</label>
                    <input type="number" class="nx" value="5" min="1" max="512">
                </div>
                <div class="input-field">
                    <label>Points Y (Ny)</label>
                    <input type="number" class="ny" value="3" min="1" max="512">
                </div>
            </div>
            
            <button class="remove-area" data-area-id="${areaId}">Remove Area</button>
        `;
        
        const removeBtn = container.querySelector('.remove-area');
        removeBtn.addEventListener('click', () => this.removeArea(areaId));
        
        this.elements.localAreasContainer.appendChild(container);
        this.updateAreaCount();
    },

    removeArea(areaId) {
        const container = document.getElementById(areaId);
        if (this.elements.localAreasContainer.children.length > 1) {
            container.remove();
            this.updateAreaCount();
        } else {
            this.updateStatus('At least one area must be maintained');
        }
    },

    updateAreaCount() {
        const count = this.elements.localAreasContainer.children.length;
        this.updateStatus(`Active areas: ${count}`);
    },

    // Movement Script Functions
    async saveMovementScript() {
        try {
            const scriptData = {
                name: this.elements.scriptName.value.trim(),
                script: this.elements.movementScript.value.trim(),
                distance: parseFloat(this.elements.moveDistance.value),
                waitTime: parseFloat(this.elements.waitTime.value),
                repeatCount: parseInt(this.elements.repeatCount.value)
            };
            
            if (!this.validateMovementScript(scriptData)) {
                return;
            }
            
            const success = await pywebview.api.save_auto_move_script(scriptData);
            if (success) {
                this.updateStatus('Movement script saved successfully');
                await this.loadScripts();
            }
            
        } catch (error) {
            this.updateStatus(`Error saving script: ${error.message}`);
            console.error('Script save error:', error);
        }
    },

    validateMovementScript(data) {
        if (!data.name) {
            this.updateStatus('Please enter a script name');
            return false;
        }
        
        if (!data.script || !/^[RULD]+$/.test(data.script)) {
            this.updateStatus('Invalid movement script format');
            return false;
        }
        
        if (isNaN(data.distance) || data.distance <= 0) {
            this.updateStatus('Invalid distance value');
            return false;
        }
        
        if (isNaN(data.waitTime) || data.waitTime < 0) {
            this.updateStatus('Invalid wait time value');
            return false;
        }
        
        if (isNaN(data.repeatCount) || data.repeatCount < 1) {
            this.updateStatus('Invalid repeat count');
            return false;
        }
        
        return true;
    },

    // addStsRow(vds = 0, vg = 0) {
    //     const row = document.createElement('div');
    //     row.className = 'sts-row';
    //     row.innerHTML = `
    //         <input type="number" class="vds-input" value="${vds}" step="0.1">
    //         <input type="number" class="vg-input" value="${vg}" step="0.1">
    //         <button class="remove-row" title="Remove">×</button>
    //     `;

    //     // 移除行按鈕
    //     row.querySelector('.remove-row').addEventListener('click', () => {
    //         row.remove();
    //     });

    //     this.elements.settingsRows.appendChild(row);
    // },

    // Auto-Move CITS Functions
    async startAutoMoveLocalSstsCits() {
        if (this.state.isRunning) return;
        
        try {
            // 檢查基本參數
            if (!this.elements.movementScript.value || 
                !this.elements.moveDistance.value) {
                this.updateStatus('Please fill in all required fields');
                return;
            }
            
            // 收集局部區域參數
            const localAreas = this.collectLocalAreasData();
            if (localAreas.length === 0) {
                this.updateStatus('Please add at least one local area');
                return;
            }
            
            // 收集其他參數
            const params = {
                movement_script: this.elements.movementScript.value.trim(),
                distance: parseFloat(this.elements.moveDistance.value),
                initial_direction: parseInt(this.elements.globalDirection.value),
                wait_time: parseFloat(this.elements.waitTime.value),
                repeat_count: parseInt(this.elements.repeatCount.value)
            };
            
            // 驗證移動指令
            if (!/^[RULD]+$/.test(params.movement_script)) {
                this.updateStatus('Invalid movement script format');
                return;
            }
            
            // 更新UI狀態
            this.state.isRunning = true;
            this.elements.startAutoMoveSstsBtn.disabled = true;
            this.updateStatus('Starting Auto-Move Local SSTS CITS...');
            
            // 執行測量
            const success = await pywebview.api.auto_move_local_ssts_cits(
                params.movement_script,
                params.distance,
                localAreas,
                params.initial_direction,
                params.wait_time,
                params.repeat_count
            );
            
            if (success) {
                this.updateStatus('Auto-Move Local SSTS CITS completed successfully');
            } else {
                throw new Error('Local SSTS CITS measurement failed');
            }
            
        } catch (error) {
            this.updateStatus(`Error: ${error.message}`);
            console.error('Auto-Move Local SSTS CITS error:', error);
        } finally {
            this.state.isRunning = false;
            this.elements.startAutoMoveSstsBtn.disabled = false;
        }
    },

    async startAutoMoveMstsCits() {
        if (this.state.isRunning) return;
        
        try {
            // 驗證必要參數,包含STS腳本
            if (!this.elements.movementScript.value || !this.elements.moveDistance.value || 
                !this.elements.pointsX.value || !this.elements.pointsY.value ||
                !this.elements.stsScriptSelect.value) {
                this.updateStatus('Please fill in all required fields and select an STS script');
                return;
            }
    
            // 取得並驗證參數
            const params = {
                movement_script: this.elements.movementScript.value.trim(),
                distance: parseFloat(this.elements.moveDistance.value),
                num_points_x: parseInt(this.elements.pointsX.value),
                num_points_y: parseInt(this.elements.pointsY.value),
                script_name: this.elements.stsScriptSelect.value,
                initial_direction: parseInt(this.elements.scanDirection.value),
                wait_time: parseFloat(this.elements.waitTime.value),
                repeat_count: parseInt(this.elements.repeatCount.value)
            };
    
            // 參數驗證
            if (!/^[RULD]+$/.test(params.movement_script)) {
                this.updateStatus('Invalid movement script format');
                return;
            }
            if (!params.distance || params.distance <= 0) {
                this.updateStatus('Invalid distance value');
                return;
            }
            if (params.num_points_x < 1 || params.num_points_x > 512 ||
                params.num_points_y < 1 || params.num_points_y > 512) {
                this.updateStatus('Points must be between 1 and 512');
                return;
            }
    
            // 更新UI狀態
            this.state.isRunning = true;
            this.elements.startAutoMoveMstsBtn.disabled = true;
            this.updateStatus('Starting Auto-Move MSTS CITS...');
    
            // 呼叫API執行測量
            const success = await pywebview.api.auto_move_msts_cits(
                params.movement_script,
                params.distance,
                params.num_points_x,
                params.num_points_y,
                params.script_name,
                params.initial_direction,
                params.wait_time,
                params.repeat_count
            );
    
            if (success) {
                this.updateStatus('Auto-Move MSTS CITS completed successfully');
            } else {
                throw new Error('MSTS CITS measurement failed');
            }
    
        } catch (error) {
            this.updateStatus(`Error: ${error.message}`);
            console.error('Auto-Move MSTS CITS error:', error);
        } finally {
            this.state.isRunning = false;
            this.elements.startAutoMoveMstsBtn.disabled = false;
        }
    },

    async startAutoMoveLocalSstsCits() {
        if (this.state.isRunning) return;
        
        try {
            // 驗證基本參數
            if (!this.elements.movementScript.value || !this.elements.moveDistance.value) {
                this.updateStatus('Please fill in all required fields');
                return;
            }
    
            // 收集局部區域參數
            const localAreas = [];
            const areaContainers = this.elements.localAreasContainer.querySelectorAll('.local-area-container');
            
            if (areaContainers.length === 0) {
                this.updateStatus('Please add at least one local area');
                return;
            }
    
            // 處理每個局部區域的參數
            for (const container of areaContainers) {
                const areaParams = {
                    x_dev: parseFloat(container.querySelector('.x-dev').value),
                    y_dev: parseFloat(container.querySelector('.y-dev').value),
                    dx: parseFloat(container.querySelector('.dx').value),
                    dy: parseFloat(container.querySelector('.dy').value),
                    nx: parseInt(container.querySelector('.nx').value),
                    ny: parseInt(container.querySelector('.ny').value),
                    startpoint_direction: parseInt(container.querySelector('.start-direction').value)
                };
    
                // 驗證單個區域參數
                if (isNaN(areaParams.x_dev) || isNaN(areaParams.y_dev) ||
                    isNaN(areaParams.dx) || isNaN(areaParams.dy) ||
                    isNaN(areaParams.nx) || isNaN(areaParams.ny) ||
                    ![1, -1].includes(areaParams.startpoint_direction)) {
                    this.updateStatus('Invalid parameters in one of the local areas');
                    return;
                }
    
                // 驗證點數範圍
                if (areaParams.nx < 1 || areaParams.nx > 512 ||
                    areaParams.ny < 1 || areaParams.ny > 512) {
                    this.updateStatus('Points must be between 1 and 512 in all areas');
                    return;
                }
    
                localAreas.push(areaParams);
            }
    
            // 收集其他參數
            const params = {
                movement_script: this.elements.movementScript.value.trim(),
                distance: parseFloat(this.elements.moveDistance.value),
                initial_direction: parseInt(this.elements.globalDirection.value),
                wait_time: parseFloat(this.elements.waitTime.value),
                repeat_count: parseInt(this.elements.repeatCount.value)
            };
    
            // 驗證移動指令
            if (!/^[RULD]+$/.test(params.movement_script)) {
                this.updateStatus('Invalid movement script format');
                return;
            }
    
            // 更新UI狀態
            this.state.isRunning = true;
            this.elements.startLocalSstsBtn.disabled = true;
            this.updateStatus('Starting Auto-Move Local SSTS CITS...');
    
            // 執行測量
            const success = await pywebview.api.auto_move_local_ssts_cits(
                params.movement_script,
                params.distance,
                localAreas,
                params.initial_direction,
                params.wait_time,
                params.repeat_count
            );
    
            if (success) {
                this.updateStatus('Auto-Move Local SSTS CITS completed successfully');
            } else {
                throw new Error('Local SSTS CITS measurement failed');
            }
    
        } catch (error) {
            this.updateStatus(`Error: ${error.message}`);
            console.error('Auto-Move Local SSTS CITS error:', error);
        } finally {
            this.state.isRunning = false;
            this.elements.startLocalSstsBtn.disabled = false;
        }
    },
    
    async startAutoMoveLocalMstsCits() {
        if (this.state.isRunning) return;
        
        try {
            // 驗證基本參數和STS腳本選擇
            if (!this.elements.movementScript.value || !this.elements.moveDistance.value || 
                !this.elements.stsScriptSelect.value) {
                this.updateStatus('Please fill in all required fields and select an STS script');
                return;
            }
    
            // 收集局部區域參數
            const localAreas = [];
            const areaContainers = this.elements.localAreasContainer.querySelectorAll('.local-area-container');
            
            if (areaContainers.length === 0) {
                this.updateStatus('Please add at least one local area');
                return;
            }
    
            // 處理每個局部區域的參數
            for (const container of areaContainers) {
                const areaParams = {
                    x_dev: parseFloat(container.querySelector('.x-dev').value),
                    y_dev: parseFloat(container.querySelector('.y-dev').value),
                    dx: parseFloat(container.querySelector('.dx').value),
                    dy: parseFloat(container.querySelector('.dy').value),
                    nx: parseInt(container.querySelector('.nx').value),
                    ny: parseInt(container.querySelector('.ny').value),
                    startpoint_direction: parseInt(container.querySelector('.start-direction').value)
                };
    
                // 驗證單個區域參數
                if (isNaN(areaParams.x_dev) || isNaN(areaParams.y_dev) ||
                    isNaN(areaParams.dx) || isNaN(areaParams.dy) ||
                    isNaN(areaParams.nx) || isNaN(areaParams.ny) ||
                    ![1, -1].includes(areaParams.startpoint_direction)) {
                    this.updateStatus('Invalid parameters in one of the local areas');
                    return;
                }
    
                // 驗證點數範圍
                if (areaParams.nx < 1 || areaParams.nx > 512 ||
                    areaParams.ny < 1 || areaParams.ny > 512) {
                    this.updateStatus('Points must be between 1 and 512 in all areas');
                    return;
                }
    
                localAreas.push(areaParams);
            }
    
            // 收集其他參數
            const params = {
                movement_script: this.elements.movementScript.value.trim(),
                distance: parseFloat(this.elements.moveDistance.value),
                script_name: this.elements.stsScriptSelect.value,
                initial_direction: parseInt(this.elements.globalDirection.value),
                wait_time: parseFloat(this.elements.waitTime.value),
                repeat_count: parseInt(this.elements.repeatCount.value)
            };
    
            // 驗證移動指令
            if (!/^[RULD]+$/.test(params.movement_script)) {
                this.updateStatus('Invalid movement script format');
                return;
            }
    
            // 更新UI狀態
            this.state.isRunning = true;
            this.elements.startLocalMstsBtn.disabled = true;
            this.updateStatus('Starting Auto-Move Local MSTS CITS...');
    
            // 執行測量
            const success = await pywebview.api.auto_move_local_msts_cits(
                params.movement_script,
                params.distance,
                localAreas,
                params.script_name,
                params.initial_direction,
                params.wait_time,
                params.repeat_count
            );
    
            if (success) {
                this.updateStatus('Auto-Move Local MSTS CITS completed successfully');
            } else {
                throw new Error('Local MSTS CITS measurement failed');
            }
    
        } catch (error) {
            this.updateStatus(`Error: ${error.message}`);
            console.error('Auto-Move Local MSTS CITS error:', error);
        } finally {
            this.state.isRunning = false;
            this.elements.startLocalMstsBtn.disabled = false;
        }
    },

    // Helper Functions
    collectCitsParams() {
        return {
            movementScript: this.elements.movementScript.value.trim(),
            distance: parseFloat(this.elements.moveDistance.value),
            pointsX: parseInt(this.elements.pointsX.value),
            pointsY: parseInt(this.elements.pointsY.value),
            scanDirection: parseInt(this.elements.scanDirection.value),
            waitTime: parseFloat(this.elements.waitTime.value),
            repeatCount: parseInt(this.elements.repeatCount.value)
        };
    },

    collectLocalCitsParams() {
        const localAreas = [];
        this.elements.localAreasContainer.querySelectorAll('.local-area-container').forEach(container => {
            localAreas.push({
                x_dev: parseFloat(container.querySelector('.x-dev').value),
                y_dev: parseFloat(container.querySelector('.y-dev').value),
                dx: parseFloat(container.querySelector('.dx').value),
                dy: parseFloat(container.querySelector('.dy').value),
                nx: parseInt(container.querySelector('.nx').value),
                ny: parseInt(container.querySelector('.ny').value),
                startpoint_direction: parseInt(container.querySelector('.start-direction').value)
            });
        });
        
        return {
            movementScript: this.elements.movementScript.value.trim(),
            distance: parseFloat(this.elements.moveDistance.value),
            localAreas: localAreas,
            initialDirection: parseInt(this.elements.globalDirection.value),
            waitTime: parseFloat(this.elements.waitTime.value),
            repeatCount: parseInt(this.elements.repeatCount.value)
        };
    },

    validatePoints(input) {
        const value = parseInt(input.value);
        if (value < 1) input.value = 1;
        if (value > 512) input.value = 512;
    },

    validateCitsParams(params) {
        if (!params.movementScript || !/^[RULD]+$/.test(params.movementScript)) {
            this.updateStatus('Invalid movement script format');
            return false;
        }
        
        if (isNaN(params.distance) || params.distance <= 0) {
            this.updateStatus('Invalid distance value');
            return false;
        }
        
        if (isNaN(params.pointsX) || params.pointsX < 1 || params.pointsX > 512 ||
            isNaN(params.pointsY) || params.pointsY < 1 || params.pointsY > 512) {
            this.updateStatus('CITS points must be between 1 and 512');
            return false;
        }
        
        if (params.scanDirection !== 1 && params.scanDirection !== -1) {
            this.updateStatus('Invalid scan direction');
            return false;
        }
        
        if (isNaN(params.waitTime) || params.waitTime < 0) {
            this.updateStatus('Invalid wait time value');
            return false;
        }
        
        if (isNaN(params.repeatCount) || params.repeatCount < 1) {
            this.updateStatus('Invalid repeat count');
            return false;
        }
        
        return true;
    },

    validateLocalCitsParams(params) {
        if (!this.validateCitsParams(params)) {
            return false;
        }
        
        if (!params.localAreas.length) {
            this.updateStatus('No local areas defined');
            return false;
        }
        
        for (let i = 0; i < params.localAreas.length; i++) {
            const area = params.localAreas[i];
            if (!this.validateLocalArea(area, i)) {
                return false;
            }
        }
        
        return true;
    },

    validateLocalArea(area) {
        const validationRules = {
            start_x: { min: -10000, max: 10000 },
            start_y: { min: -10000, max: 10000 },
            dx: { min: 0.1, max: 1000 },
            dy: { min: 0.1, max: 1000 },
            nx: { min: 1, max: 512 },
            ny: { min: 1, max: 512 }
        };
    
        for (const [key, rule] of Object.entries(validationRules)) {
            const value = area[key];
            if (value < rule.min || value > rule.max) {
                throw new Error(
                    `Invalid ${key}: ${value}. Must be between ${rule.min} and ${rule.max}`
                );
            }
        }
    
        if (![1, -1].includes(area.startpoint_direction)) {
            throw new Error('Invalid startpoint direction. Must be 1 or -1');
        }
    
        return true;
    },

    collectLocalAreasData() {
        const localAreas = [];
        const containers = this.elements.localAreasContainer.querySelectorAll('.local-area-container');
        
        if (!containers || containers.length === 0) {
            this.updateStatus('No local areas defined');
            return [];
        }
        
        try {
            containers.forEach(container => {
                // 確保所有必要的輸入元素存在
                const xDevInput = container.querySelector('.x-dev');
                const yDevInput = container.querySelector('.y-dev');
                const dxInput = container.querySelector('.dx');
                const dyInput = container.querySelector('.dy');
                const nxInput = container.querySelector('.nx');
                const nyInput = container.querySelector('.ny');
                const directionSelect = container.querySelector('.start-direction');
                
                if (!xDevInput || !yDevInput || !dxInput || !dyInput || 
                    !nxInput || !nyInput || !directionSelect) {
                    throw new Error('Missing required input elements');
                }
                
                const localArea = {
                    x_dev: parseFloat(xDevInput.value),
                    y_dev: parseFloat(yDevInput.value),
                    dx: parseFloat(dxInput.value),
                    dy: parseFloat(dyInput.value),
                    nx: parseInt(nxInput.value),
                    ny: parseInt(nyInput.value),
                    startpoint_direction: parseInt(directionSelect.value)
                };
                
                // 驗證數值
                if (Object.values(localArea).some(value => 
                    value === null || isNaN(value))) {
                    throw new Error('Invalid input values');
                }
                
                localAreas.push(localArea);
            });
            
            return localAreas;
            
        } catch (error) {
            this.updateStatus(`Local area validation error: ${error.message}`);
            console.error('Local area validation error:', error);
            return [];
        }
    },

    updateStatus(message) {
        if (this.elements.statusDisplay) {
            this.elements.statusDisplay.textContent = message;
        }
        console.log(`[Auto-Move Status] ${message}`);
    },

    async loadScripts() {
        try {
            const scripts = await pywebview.api.get_auto_move_scripts();
            const stsScripts = await pywebview.api.get_sts_scripts();
            
            this.updateScriptSelects(scripts, stsScripts);
        } catch (error) {
            console.error('Error loading scripts:', error);
            this.updateStatus('Error loading scripts');
        }
    },

    updateScriptSelects(moveScripts, stsScripts) {
        // 更新移動腳本選單
        const moveSelect = this.elements.scriptSelect;
        moveSelect.innerHTML = '<option value="">Select Script...</option>';
        
        Object.entries(moveScripts).forEach(([name, script]) => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            moveSelect.appendChild(option);
        });
        
        // 更新STS腳本選單
        const stsSelect = this.elements.stsScriptSelect;
        stsSelect.innerHTML = '<option value="">Select STS Script...</option>';
        
        Object.entries(stsScripts).forEach(([name, script]) => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            stsSelect.appendChild(option);
        });
    },

    async updateLocalCitsStatus() {
        try {
            const status = await pywebview.api.get_sxm_status();
            
            // 更新預覽資訊
            this.elements.localPreviewCenter.textContent = 
                `(${status.center_x.toFixed(2)}, ${status.center_y.toFixed(2)})`;
            this.elements.localPreviewRange.textContent = 
                status.range.toFixed(2);
            this.elements.localPreviewAngle.textContent = 
                status.angle.toFixed(2);
                
            // 計算並更新總點數
            const totalPoints = this.calculateTotalLocalCitsPoints();
            this.elements.localPreviewTotalPoints.textContent = totalPoints;
            
            this.updateStatus('Local CITS status updated successfully');
        } catch (error) {
            this.updateStatus(`Failed to get Local CITS status: ${error.message}`);
            console.error('Local CITS status error:', error);
        }
    },

    calculateTotalLocalCitsPoints() {
        let total = 0;
        const containers = this.elements.localAreasContainer.querySelectorAll('.local-area-container');
        containers.forEach(container => {
            const nx = parseInt(container.querySelector('.nx').value) || 0;
            const ny = parseInt(container.querySelector('.ny').value) || 0;
            total += nx * ny;
        });
        return total;
    },

    async previewLocalCits() {
        try {
            // 先獲取 SXM 狀態以取得掃描參數
            const sxmStatus = await pywebview.api.get_sxm_status();
            
            // 收集所有區域的參數
            const localAreas = [];
            const containers = this.elements.localAreasContainer.querySelectorAll('.local-area-container');
            
            containers.forEach(container => {
                const x_dev = parseFloat(container.querySelector('.x-dev').value);
                const y_dev = parseFloat(container.querySelector('.y-dev').value);
                const dx = parseFloat(container.querySelector('.dx').value);
                const dy = parseFloat(container.querySelector('.dy').value);
                const nx = parseInt(container.querySelector('.nx').value);
                const ny = parseInt(container.querySelector('.ny').value);
                const startpoint_direction = parseInt(container.querySelector('.start-direction').value);
                
                // 確保所有參數都有效
                if (isNaN(x_dev) || isNaN(y_dev) || isNaN(dx) || isNaN(dy) || 
                    isNaN(nx) || isNaN(ny)) {
                    throw new Error('Invalid input values');
                }
                
                // 將相對座標轉換為絕對座標，同時保留原始參數
                const area = {
                    start_x: sxmStatus.center_x + x_dev,
                    start_y: sxmStatus.center_y + y_dev,
                    dx: dx,
                    dy: dy,
                    nx: nx,
                    ny: ny,
                    startpoint_direction: startpoint_direction
                };
                
                localAreas.push(area);
            });
            
            if (!localAreas.length) {
                this.updateStatus('No local areas defined');
                return;
            }
            
            // 準備完整的預覽參數
            const params = {
                scan_center_x: sxmStatus.center_x,
                scan_center_y: sxmStatus.center_y,
                scan_range: sxmStatus.range,
                scan_angle: sxmStatus.angle,
                total_lines: sxmStatus.total_lines,
                scan_direction: parseInt(this.elements.globalDirection.value),
                aspect_ratio: sxmStatus.aspect_ratio || 1.0,
                local_areas: localAreas
            };
            
            // 生成預覽
            const plotData = await pywebview.api.preview_local_cits(params);
            
            // 設定繪圖配置
            const config = {
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                hovermode: 'closest',
                hoverlabel: {
                    bgcolor: "#FFF",
                    font: { size: 14 },
                    bordercolor: "#888"
                }
            };

            // 擴充layout設定
            const layout = {
                ...plotData.layout,
                // 確保hover標籤完整顯示
                margin: { l: 60, r: 30, t: 50, b: 60, pad: 4 }
            };
            
            // 更新預覽圖
            Plotly.newPlot(this.elements.localPreviewCanvas, plotData.data, layout, config);
            
            this.updateStatus('Local CITS preview generated successfully');
            
        } catch (error) {
            this.updateStatus(`Local CITS preview error: ${error.message}`);
            console.error('Local CITS preview error:', error);
        }
    },
    
    updateLocalPreviewInfo(status) {
        // 更新預覽資訊
        if (this.elements.localPreviewCenter) {
            this.elements.localPreviewCenter.textContent = 
                `(${status.center_x.toFixed(2)}, ${status.center_y.toFixed(2)})`;
        }
        if (this.elements.localPreviewRange) {
            this.elements.localPreviewRange.textContent = 
                status.range.toFixed(2);
        }
        if (this.elements.localPreviewAngle) {
            this.elements.localPreviewAngle.textContent = 
                status.angle.toFixed(2);
        }
        if (this.elements.localPreviewTotalPoints) {
            this.elements.localPreviewTotalPoints.textContent = 
                this.calculateTotalPoints();
        }
    },
    
    calculateTotalPoints() {
        let total = 0;
        document.querySelectorAll('.local-area-container').forEach(container => {
            const nx = parseInt(container.querySelector('.nx').value);
            const ny = parseInt(container.querySelector('.ny').value);
            total += nx * ny;
        });
        return total;
    }
};

// 匯出模組
export default AutoMoveMeasurementModule;