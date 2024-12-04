const CITSMeasurementModule = {
    elements: {
        // Standard CITS elements
        pointsX: document.getElementById('citsPointsX'),
        pointsY: document.getElementById('citsPointsY'),
        scanDirection: document.getElementById('citsScanDirection'),
        singleCitsBtn: document.getElementById('startSingleCits'),
        multiCitsBtn: document.getElementById('startMstsCits'),
        
        // Local CITS elements
        globalDirection: document.getElementById('globalDirection'),
        localAreasContainer: document.getElementById('localAreasContainer'),
        addLocalAreaBtn: document.getElementById('addLocalArea'),
        
        // Preview elements
        previewInfo: document.getElementById('previewInfo'),
        statusDisplay: document.getElementById('localCitsStatus')
    },

    state: {
        isRunning: false,
        localAreas: [],
        areaCounter: 0
    },

    init() {
        this.setupEventListeners();
        this.createInitialArea();
    },

    setupEventListeners() {
        // Standard CITS buttons
        this.elements.singleCitsBtn.addEventListener('click', () => this.startSingleCits());
        this.elements.multiCitsBtn.addEventListener('click', () => this.startMultiCits());
        
        // Local CITS controls
        this.elements.addLocalAreaBtn.addEventListener('click', () => this.addLocalArea());
        
        // Input validation
        this.elements.pointsX.addEventListener('change', () => this.validatePoints(this.elements.pointsX));
        this.elements.pointsY.addEventListener('change', () => this.validatePoints(this.elements.pointsY));
    },

    createInitialArea() {
        // 清空容器
        this.elements.localAreasContainer.innerHTML = '';
        // 新增第一個區域
        this.addLocalArea();
    },

    addLocalArea() {
        const areaId = `area-${++this.state.areaCounter}`;
        const container = document.createElement('div');
        container.className = 'local-area-container';
        container.id = areaId;
        
        container.innerHTML = `
            <div class="input-group">
                <label>Start Position:</label>
                <div class="input-with-unit">
                    <label> X: </label>
                    <input type="number" class="x-start" value="200" step="0.1">
                    <span class="unit">nm</span>
                    <label> Y: </label>
                    <input type="number" class="y-start" value="200" step="0.1">
                    <span class="unit">nm</span>
                </div>
            </div>
            
            <div class="input-field">
                <label>Start Point Direction</label>
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
        
        // 加入移除按鈕事件
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

    collectAreaData() {
        const areas = [];
        this.elements.localAreasContainer.querySelectorAll('.local-area-container').forEach(container => {
            areas.push({
                start_x: parseFloat(container.querySelector('.x-start').value),
                start_y: parseFloat(container.querySelector('.y-start').value),
                dx: parseFloat(container.querySelector('.dx').value),
                dy: parseFloat(container.querySelector('.dy').value),
                nx: parseInt(container.querySelector('.nx').value),
                ny: parseInt(container.querySelector('.ny').value),
                startpoint_direction: parseInt(container.querySelector('.start-direction').value)
            });
        });
        return areas;
    },

    validatePoints(input) {
        const value = parseInt(input.value);
        if (value < 1) input.value = 1;
        if (value > 512) input.value = 512;
    },

    async startSingleCits() {
        if (this.state.isRunning) return;
        
        try {
            this.state.isRunning = true;
            this.elements.singleCitsBtn.disabled = true;
            
            const pointsX = parseInt(this.elements.pointsX.value);
            const pointsY = parseInt(this.elements.pointsY.value);
            const scanDirection = parseInt(this.elements.scanDirection.value);
            
            this.updateStatus('Starting Single-STS CITS...');
            
            const success = await pywebview.api.start_ssts_cits(
                pointsX,
                pointsY,
                scanDirection
            );
            
            if (success) {
                this.updateStatus('Single-STS CITS completed successfully');
            } else {
                throw new Error('CITS measurement failed');
            }
            
        } catch (error) {
            this.updateStatus(`Error: ${error.message}`);
            alert(`CITS Error: ${error.message}`);
        } finally {
            this.state.isRunning = false;
            this.elements.singleCitsBtn.disabled = false;
        }
    },

    async startMultiCits() {
        if (this.state.isRunning) return;
        
        try {
            const scriptSelect = document.getElementById('smuscriptSelect');
            if (!scriptSelect.value) {
                throw new Error('Please select a Multi-STS script');
            }
            
            this.state.isRunning = true;
            this.elements.multiCitsBtn.disabled = true;
            
            const pointsX = parseInt(this.elements.pointsX.value);
            const pointsY = parseInt(this.elements.pointsY.value);
            const scanDirection = parseInt(this.elements.scanDirection.value);
            
            this.updateStatus('Starting Multi-STS CITS...');
            
            const success = await pywebview.api.start_msts_cits(
                pointsX,
                pointsY,
                scriptSelect.value,
                scanDirection
            );
            
            if (success) {
                this.updateStatus('Multi-STS CITS completed successfully');
            } else {
                throw new Error('Multi-STS CITS measurement failed');
            }
            
        } catch (error) {
            this.updateStatus(`Error: ${error.message}`);
            alert(`Multi-STS CITS Error: ${error.message}`);
        } finally {
            this.state.isRunning = false;
            this.elements.multiCitsBtn.disabled = false;
        }
    },

    updateStatus(message) {
        if (this.elements.statusDisplay) {
            this.elements.statusDisplay.textContent = message;
        }
        console.log(`[CITS Status] ${message}`);
    }
};

// 匯出模組
export default CITSMeasurementModule;