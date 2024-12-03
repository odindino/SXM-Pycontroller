// 導入所需模組
import NavigatorModule from './navigator.js';
import SMUConfigModule from './smu-config.js';
import STSMeasurementModule from './sts-measurement.js';
import CITSMeasurementModule from './cits-measurement.js';
import AutoMoveMeasurementModule from './auto-move-measurement.js';

// 全域錯誤處理
window.onerror = function(message, source, lineno, colno, error) {
    console.error('Global error:', {message, source, lineno, colno, error});
    alert(`An error occurred: ${message}`);
    return false;
};

// 初始化函數
function initializeApplication() {
    try {
        // 初始化導航
        NavigatorModule.init();
        
        // 初始化各模組
        SMUConfigModule.init();
        STSMeasurementModule.init();
        CITSMeasurementModule.init();
        AutoMoveMeasurementModule.init();
        
        console.log('Application initialized successfully');
    } catch (error) {
        console.error('Initialization error:', error);
        alert('Failed to initialize application: ' + error.message);
    }
}

// 等待 DOM 載入完成後初始化
document.addEventListener('DOMContentLoaded', initializeApplication);

// 匯出全域模組參照（如果需要）
window.modules = {
    navigator: NavigatorModule,
    smuConfig: SMUConfigModule,
    stsMeasurement: STSMeasurementModule,
    citsMeasurement: CITSMeasurementModule,
    autoMove: AutoMoveMeasurementModule
};