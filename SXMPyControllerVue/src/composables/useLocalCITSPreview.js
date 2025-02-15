// composables/useLocalCITSPreview.js
import { ref, watchEffect } from 'vue';

// 創建持久化的響應式狀態
const previewSettings = ref(null);
const previewData = ref(null);
const backgroundImage = ref(localStorage.getItem('localCITSBackgroundImage') || null);
const imageSettings = ref(null);

// 初始化狀態
try {
  const savedSettings = localStorage.getItem('localCITSPreviewSettings');
  const savedPreviewData = localStorage.getItem('localCITSPreviewData');
  const savedImageSettings = localStorage.getItem('localCITSImageSettings');
  
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

  if (savedImageSettings) {
    imageSettings.value = JSON.parse(savedImageSettings);
  } else {
    imageSettings.value = {
      scale: 1.0,
      opacity: 0.5
    };
  }
} catch (error) {
  console.error('Error parsing stored preview data:', error);
  // 恢復預設值
  previewSettings.value = {
    center_x: 0,
    center_y: 0,
    scan_range: 100,
    scan_angle: 0,
    total_lines: 500,
    aspect_ratio: 1
  };
  imageSettings.value = {
    scale: 1.0,
    opacity: 0.5
  };
}

// 監聽狀態變化並自動保存
watchEffect(() => {
  if (previewSettings.value) {
    localStorage.setItem('localCITSPreviewSettings', JSON.stringify(previewSettings.value));
  }
  
  if (previewData.value) {
    localStorage.setItem('localCITSPreviewData', JSON.stringify(previewData.value));
  }

  if (backgroundImage.value) {
    localStorage.setItem('localCITSBackgroundImage', backgroundImage.value);
  } else {
    localStorage.removeItem('localCITSBackgroundImage');
  }
  
  if (imageSettings.value) {
    localStorage.setItem('localCITSImageSettings', JSON.stringify(imageSettings.value));
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

  const updateBackgroundImage = (image) => {
    backgroundImage.value = image;
  };

  const updateImageSettings = (settings) => {
    imageSettings.value = {
      ...imageSettings.value,
      ...settings
    };
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
    backgroundImage.value = null;
    imageSettings.value = {
      scale: 1.0,
      opacity: 0.5
    };
    localStorage.removeItem('localCITSPreviewSettings');
    localStorage.removeItem('localCITSPreviewData');
    localStorage.removeItem('localCITSBackgroundImage');
    localStorage.removeItem('localCITSImageSettings');
  };

  return {
    previewSettings,
    previewData,
    backgroundImage,
    imageSettings,
    updatePreviewSettings,
    updatePreviewData,
    updateBackgroundImage,
    updateImageSettings,
    clearPreviewState
  };
}