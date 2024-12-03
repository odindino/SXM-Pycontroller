// auto-move-measurement.js

const AutoMoveMeasurementModule = {
    elements: {
        // Movement Script Controls
        scriptName: document.getElementById('amScriptName'),
        scriptSelect: document.getElementById('amScriptSelect'),
        saveScriptBtn: document.getElementById('amSaveScript'),
        movementScript: document.getElementById('amMovementScript'),  // 修正: 之前是'movementScript'
        moveDistance: document.getElementById('amDistance'),         // 修正: 之前是'moveDistance'
        waitTime: document.getElementById('amWaitTime'),            // 修正: 之前是'waitTime'
        repeatCount: document.getElementById('amRepeatCount'),      // 修正: 之前是'repeatCount'
        
        // STS Settings
        stsScriptName: document.getElementById('amStsScriptName'),
        stsScriptSelect: document.getElementById('amStsScriptSelect'),
        saveStsScriptBtn: document.getElementById('amSaveScriptSts'),  // 修正: 之前是'amSaveStsScript'
        stsSettingsRows: document.getElementById('amStsSettingsRows'),
        addStsRowBtn: document.getElementById('amAddStsRow'),
        
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
        previewCanvas: document.getElementById('amMovePreview'),
        localCitsPreview: document.getElementById('amLocalCitsPreview'),
        statusDisplay: document.getElementById('amLocalCitsStatus'),
        progressDisplay: document.getElementById('amLocalCitsProgress'),
        lastTimeDisplay: document.getElementById('amLocalCitsLastTime')
    },

    state: {
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

        this.setupEventListeners();
        // this.initializeCanvases();
        this.createInitialArea();
        this.loadScripts();
    },

    setupEventListeners() {
        // Movement Script Controls
        this.elements.saveScriptBtn.addEventListener('click', () => this.saveMovementScript());
        this.elements.scriptSelect.addEventListener('change', (e) => this.loadMovementScript(e.target.value));
        
        // STS Controls
        this.elements.saveStsScriptBtn.addEventListener('click', () => this.saveStsScript());
        this.elements.addStsRowBtn.addEventListener('click', () => this.addStsRow());
        
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
    },

    initializeCanvases() {
        // 初始化移動預覽畫布
        const movePreview = this.elements.previewCanvas;
        movePreview.width = movePreview.offsetWidth;
        movePreview.height = movePreview.offsetHeight;
        this.state.previewContext = movePreview.getContext('2d');
        
        // 初始化Local CITS預覽畫布
        const localPreview = this.elements.localCitsPreview;
        localPreview.width = localPreview.offsetWidth;
        localPreview.height = localPreview.offsetHeight;
        this.state.localPreviewContext = localPreview.getContext('2d');
    },

    createInitialArea() {
        this.elements.localAreasContainer.innerHTML = '';
        this.addLocalArea();
    },

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

    // Auto-Move CITS Functions
    async startAutoMoveSstsCits() {
        if (this.state.isRunning) return;
        
        try {
            const params = this.collectCitsParams();
            if (!this.validateCitsParams(params)) {
                return;
            }
            
            this.state.isRunning = true;
            this.elements.startAutoMoveSstsBtn.disabled = true;
            this.updateStatus('Starting Auto-Move SSTS CITS...');
            
            const success = await pywebview.api.auto_move_ssts_cits(
                params.movementScript,
                params.distance,
                params.pointsX,
                params.pointsY,
                params.scanDirection,
                params.waitTime,
                params.repeatCount
            );
            
            if (success) {
                this.updateStatus('Auto-Move SSTS CITS completed successfully');
            } else {
                throw new Error('CITS measurement failed');
            }
            
        } catch (error) {
            this.updateStatus(`Error: ${error.message}`);
            console.error('CITS error:', error);
        } finally {
            this.state.isRunning = false;
            this.elements.startAutoMoveSstsBtn.disabled = false;
        }
    },

    async startAutoMoveMstsCits() {
        if (this.state.isRunning) return;
        
        try {
            const params = this.collectCitsParams();
            if (!this.validateCitsParams(params)) {
                return;
            }
            
            if (!this.elements.stsScriptSelect.value) {
                this.updateStatus('Please select an STS script');
                return;
            }
            
            this.state.isRunning = true;
            this.elements.startAutoMoveMstsBtn.disabled = true;
            this.updateStatus('Starting Auto-Move MSTS CITS...');
            
            const success = await pywebview.api.auto_move_msts_cits(
                params.movementScript,
                params.distance,
                params.pointsX,
                params.pointsY,
                this.elements.stsScriptSelect.value,
                params.scanDirection,
                params.waitTime,
                params.repeatCount
            );
            
            if (success) {
                this.updateStatus('Auto-Move MSTS CITS completed successfully');
            } else {
                throw new Error('MSTS CITS measurement failed');
            }
            
        } catch (error) {
            this.updateStatus(`Error: ${error.message}`);
            console.error('MSTS CITS error:', error);
        } finally {
            this.state.isRunning = false;
            this.elements.startAutoMoveMstsBtn.disabled = false;
        }
    },

    async startAutoMoveLocalSstsCits() {
        if (this.state.isRunning) return;
        
        try {
            const params = this.collectLocalCitsParams();
            if (!this.validateLocalCitsParams(params)) {
                return;
            }
            
            this.state.isRunning = true;
            this.elements.startLocalSstsBtn.disabled = true;
            this.updateStatus('Starting Auto-Move Local SSTS CITS...');
            
            const success = await pywebview.api.auto_move_local_ssts_cits(
                params.movementScript,
                params.distance,
                params.localAreas,
                params.initialDirection,
                params.waitTime,
                params.repeatCount
            );
            
            if (success) {
                this.updateStatus('Auto-Move Local SSTS CITS completed successfully');
            } else {
                throw new Error('Local SSTS CITS measurement failed');
            }
            
        } catch (error) {
            this.updateStatus(`Error: ${error.message}`);
            console.error('Local SSTS CITS error:', error);
        } finally {
            this.state.isRunning = false;
            this.elements.startLocalSstsBtn.disabled = false;
        }
    },

    async startAutoMoveLocalMstsCits() {
        if (this.state.isRunning) return;
        
        try {
            const params = this.collectLocalCitsParams();
            if (!this.validateLocalCitsParams(params)) {
                return;
            }
            
            if (!this.elements.stsScriptSelect.value) {
                this.updateStatus('Please select an STS script');
                return;
            }
            
            this.state.isRunning = true;
            this.elements.startLocalMstsBtn.disabled = true;
            this.updateStatus('Starting Auto-Move Local MSTS CITS...');
            
            const success = await pywebview.api.auto_move_local_msts_cits(
                params.movementScript,
                params.distance,
                params.localAreas,
                this.elements.stsScriptSelect.value,
                params.initialDirection,
                params.waitTime,
                params.repeatCount
            );
            
            if (success) {
                this.updateStatus('Auto-Move Local MSTS CITS completed successfully');
            } else {
                throw new Error('Local MSTS CITS measurement failed');
            }
            
        } catch (error) {
            this.updateStatus(`Error: ${error.message}`);
            console.error('Local MSTS CITS error:', error);
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

    validateLocalArea(area, index) {
        if (isNaN(area.x_dev) || isNaN(area.y_dev)) {
            this.updateStatus(`Invalid position in area ${index + 1}`);
            return false;
        }
        
        if (isNaN(area.dx) || area.dx <= 0 || isNaN(area.dy) || area.dy <= 0) {
            this.updateStatus(`Invalid step size in area ${index + 1}`);
            return false;
        }
        
        if (isNaN(area.nx) || area.nx < 1 || area.nx > 512 ||
            isNaN(area.ny) || area.ny < 1 || area.ny > 512) {
            this.updateStatus(`Invalid points in area ${index + 1}`);
            return false;
        }
        
        if (area.startpoint_direction !== 1 && area.startpoint_direction !== -1) {
            this.updateStatus(`Invalid start point direction in area ${index + 1}`);
            return false;
        }
        
        return true;
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

    updatePreview() {
        // 在畫布上繪製預覽
        const ctx = this.state.previewContext;
        ctx.clearRect(0, 0, this.elements.previewCanvas.width, this.elements.previewCanvas.height);
        
        // 繪製移動路徑和測量點位的預覽...
        // (根據實際需求實作預覽繪製邏輯)
    }
};

// 匯出模組
export default AutoMoveMeasurementModule;