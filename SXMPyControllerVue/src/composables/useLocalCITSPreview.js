import { ref, watchEffect } from 'vue';

// 創建持久化的響應式狀態
const previewSettings = ref(null);
const previewData = ref(null);

// 初始化狀態
try {
  const savedSettings = localStorage.getItem('localCITSPreviewSettings');
  const savedPreviewData = localStorage.getItem('localCITSPreviewData');
  
  if (savedSettings) {
    previewSettings.value = JSON.parse(savedSettings);
  } else {
    // 設定預設值
    previewSettings.value = {
      center_x: 0,
      center_y: 0,
      scan_range: 100,
      scan_angle: 0,
      total_lines: 500,
      aspect_ratio: 1
    };
  }
  
  if (savedPreviewData) {
    previewData.value = JSON.parse(savedPreviewData);
  }
} catch (error) {
  console.error('Error parsing stored preview data:', error);
}

// 監聽狀態變化並自動保存
watchEffect(() => {
  if (previewSettings.value) {
    localStorage.setItem('localCITSPreviewSettings', JSON.stringify(previewSettings.value));
  }
  
  if (previewData.value) {
    localStorage.setItem('localCITSPreviewData', JSON.stringify(previewData.value));
  }
});

export function useLocalCITSPreview() {
  const updatePreviewSettings = (newSettings) => {
    previewSettings.value = {
      ...previewSettings.value,
      ...newSettings
    };
  };

  const updatePreviewData = (newData) => {
    previewData.value = newData;
  };

  const clearPreviewState = () => {
    previewSettings.value = {
      center_x: 0,
      center_y: 0,
      scan_range: 100,
      scan_angle: 0,
      total_lines: 500,
      aspect_ratio: 1
    };
    previewData.value = null;
    localStorage.removeItem('localCITSPreviewSettings');
    localStorage.removeItem('localCITSPreviewData');
  };

  return {
    previewSettings,
    previewData,
    updatePreviewSettings,
    updatePreviewData,
    clearPreviewState
  };
}