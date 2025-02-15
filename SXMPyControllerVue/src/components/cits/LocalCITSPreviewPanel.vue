<template>
  <div class="bg-white p-6 rounded-lg shadow">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-xl font-semibold text-gray-900">Preview Settings</h2>
      <div class="flex space-x-4">
        <button
          @click="handleGetSXMStatus"
          class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Get SXM Status
        </button>
        <button
          @click="generatePreview"
          :disabled="isGenerating"
          class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
        >
          Preview Local CITS
        </button>
      </div>
    </div>

    <!-- 掃描參數設定 -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <!-- 掃描中心座標 -->
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">
          Scan Center X (nm)
        </label>
        <input
          type="number"
          v-model.number="previewSettings.center_x"
          step="0.1"
          class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>

      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">
          Scan Center Y (nm)
        </label>
        <input
          type="number"
          v-model.number="previewSettings.center_y"
          step="0.1"
          class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>

      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">
          Scan Range (nm)
        </label>
        <input
          type="number"
          v-model.number="previewSettings.scan_range"
          min="0.1"
          step="0.1"
          class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>

      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">
          Scan Angle (degrees)
        </label>
        <input
          type="number"
          v-model.number="previewSettings.scan_angle"
          step="0.1"
          class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>

      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">
          Total Lines
        </label>
        <input
          type="number"
          v-model.number="previewSettings.total_lines"
          min="1"
          class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>

      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">
          Aspect Ratio
        </label>
        <input
          type="number"
          v-model.number="previewSettings.aspect_ratio"
          min="0.1"
          max="1"
          step="0.1"
          class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>
    </div>

    <!-- 預覽疊圖圖片 -->
    <div class="space-y-4 mb-6">
    <h3 class="text-lg font-medium text-gray-900">Background Image</h3>
    
    <div class="flex items-center space-x-4">
      <div class="flex-1">
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Upload Background Image
        </label>
        <input
          ref="fileInput"
          type="file"
          accept="image/*"
          @change="handleImageUpload"
          class="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-md file:border-0
                file:text-sm file:font-semibold
                file:bg-indigo-50 file:text-indigo-700
                hover:file:bg-indigo-100"
        />
      </div>
        
        <!-- 清除圖片按鈕 -->
        <button
          v-if="backgroundImage"
          @click="clearBackgroundImage"
          class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
        >
          Clear Image
        </button>
      </div>

      <!-- 圖片設定 -->
      <div v-if="backgroundImage" class="grid grid-cols-2 gap-4">
          <label class="block text-sm font-medium text-gray-700">
            Image Opacity
          </label>
          <input
            type="range"
            v-model.number="imageSettings.opacity"
            @input="handleOpacityChange"
            min="0"
            max="1"
            step="0.1"
            class="w-full"
          />
      </div>
    </div>

    <!-- 預覽資訊顯示 -->
    <div v-if="storedPreviewData" class="space-y-4">
      <div class="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-md">
        <div>
          <span class="text-sm text-gray-500">Scan Center:</span>
          <p class="font-mono">
            ({{ formatNumber(previewSettings.center_x) }}, {{ formatNumber(previewSettings.center_y) }}) nm
          </p>
        </div>
        <div>
          <span class="text-sm text-gray-500">Total Points:</span>
          <p class="font-mono">{{ getTotalPoints() }}</p>
        </div>
      </div>

      <!-- 預覽圖表 -->
      <div class="border border-gray-200 rounded-lg overflow-hidden">
        <div id="previewPlot" class="w-full h-96"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useLocalCITSPreview } from '../../composables/useLocalCITSPreview';

const props = defineProps({
  localAreas: {
    type: Array,
    required: true
  },
  scanDirection: {
    type: Number,
    required: true
  }
});

// 使用預覽狀態管理
const { 
  previewSettings, 
  previewData: storedPreviewData, 
  updatePreviewSettings,
  updatePreviewData 
} = useLocalCITSPreview();

const isGenerating = ref(false);
const fileInput = ref(null);
let plot = null;

// 格式化數字
const formatNumber = (value) => {
  return Number(value).toFixed(2);
};

// 計算總點數
const getTotalPoints = () => {
  return props.localAreas.reduce((sum, area) => {
    return sum + (Number(area.nx) * Number(area.ny));
  }, 0);
};

// 從 SXM 獲取狀態
async function handleGetSXMStatus() {
  try {
    const status = await window.pywebview.api.get_sxm_status();
    
    // 更新預覽設定
    updatePreviewSettings({
      center_x: Number(status.center_x || 0),
      center_y: Number(status.center_y || 0),
      scan_range: Number(status.scan_range || 100),
      scan_angle: Number(status.scan_angle || 0),
      total_lines: Number(status.total_lines || 500),
      aspect_ratio: Number(status.aspect_ratio || 1)
    });
    
  } catch (error) {
    console.error('Failed to get SXM status:', error);
    alert('Failed to get SXM status. Check connection and try again.');
  }
}

// 轉換區域參數
function transformAreas() {
  return props.localAreas.map(area => ({
    start_x: Number(area.start_x || 0),
    start_y: Number(area.start_y || 0),
    dx: Number(area.dx),
    dy: Number(area.dy) * (area.startpoint_direction === -1 ? -1 : 1),
    nx: Number(area.nx),
    ny: Number(area.ny),
    startpoint_direction: Number(area.startpoint_direction)
  }));
}

// 背景圖片相關狀態
const { 
  backgroundImage,
  imageSettings,
  updateBackgroundImage,
  updateImageSettings
} = useLocalCITSPreview();

// 處理圖片上傳
async function handleImageUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const reader = new FileReader();
    reader.onload = (e) => {
      updateBackgroundImage(e.target.result);
      if (storedPreviewData.value) {
        updatePreviewPlot(storedPreviewData.value);
      }
    };
    reader.readAsDataURL(file);
  } catch (error) {
    console.error('Image upload error:', error);
    alert('Failed to load image');
  }
}

// 清除背景圖片
function clearBackgroundImage() {
  updateBackgroundImage(null);
  // 重置檔案輸入
  if (fileInput.value) {
    fileInput.value.value = '';
  }
  if (storedPreviewData.value) {
    updatePreviewPlot(storedPreviewData.value);
  }
}

// 更新預覽圖
function updatePreviewPlot(data) {
  const plotElement = document.getElementById('previewPlot');
  if (!plotElement) return;
  
  if (plot) {
    Plotly.purge(plotElement);
  }
  
  const range = Number(previewSettings.value.scan_range);
  const center_x = Number(previewSettings.value.center_x);
  const center_y = Number(previewSettings.value.center_y);
  const margin = range * 0.2;

  const layout = {
    ...data.layout,
    hoverlabel: {
      bgcolor: '#FFF',
      font: { size: 12 }
    },
    margin: { l: 50, r: 50, t: 30, b: 50 },
    showlegend: true,
    legend: {
      x: 1.05,
      y: 1,
      xanchor: 'left',
      yanchor: 'top'
    },
    xaxis: {
      range: [center_x - range - margin, center_x + range + margin],
      title: 'X Position (nm)'
    },
    yaxis: {
      range: [center_y - range - margin, center_y + range + margin],
      title: 'Y Position (nm)',
      scaleanchor: 'x',
      scaleratio: 1
    },
    dragmode: 'pan'
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    toImageButtonOptions: {
      format: 'svg',
      filename: 'local_cits_preview'
    }
  };

  if (backgroundImage.value) {
    // 定義掃描區域的邊界
    const scanArea = {
      x0: center_x - range/2,
      x1: center_x + range/2,
      y0: center_y - range/2,
      y1: center_y + range/2
    };

    layout.images = [{
      source: backgroundImage.value,
      x: scanArea.x0,            // 左邊界對齊掃描區域
      y: scanArea.y1,            // 上邊界對齊掃描區域
      sizex: scanArea.x1 - scanArea.x0,  // 寬度等於掃描區域寬度
      sizey: scanArea.y1 - scanArea.y0,  // 高度等於掃描區域高度
      xref: 'x',
      yref: 'y',
      opacity: imageSettings.value.opacity,
      layer: 'below',
      sizing: 'fill',           // 使用 'fill' 而不是 'contain' 來確保圖片完全填充區域
      xanchor: 'left',          // 確保圖片左對齊
      yanchor: 'top'            // 確保圖片頂部對齊
    }];

    // 更新視圖範圍以確保掃描區域和圖片都完全可見
    layout.xaxis.range = [scanArea.x0 - margin, scanArea.x1 + margin];
    layout.yaxis.range = [scanArea.y0 - margin, scanArea.y1 + margin];
  }

  plot = Plotly.newPlot(plotElement, data.data, layout, config);
}

// 添加在其他函數附近
function handleOpacityChange(event) {
  updateImageSettings({ opacity: Number(event.target.value) });
  if (storedPreviewData.value) {
    updatePreviewPlot(storedPreviewData.value);
  }
}

// 生成預覽
async function generatePreview() {
  if (isGenerating.value) return;

  try {
    isGenerating.value = true;

    const previewParams = {
      scan_center_x: Number(previewSettings.value.center_x),
      scan_center_y: Number(previewSettings.value.center_y),
      scan_range: Number(previewSettings.value.scan_range),
      scan_angle: Number(previewSettings.value.scan_angle),
      total_lines: Number(previewSettings.value.total_lines),
      scan_direction: Number(props.scanDirection),
      aspect_ratio: Number(previewSettings.value.aspect_ratio),
      local_areas: transformAreas()
    };

    const preview = await window.pywebview.api.preview_local_cits(previewParams);
    
    // 更新預覽數據
    updatePreviewData({
      ...preview,
      center_x: previewSettings.value.center_x,
      center_y: previewSettings.value.center_y
    });

    // 更新圖表
    updatePreviewPlot(preview);

  } catch (error) {
    console.error('Preview generation error:', error);
    alert(`Preview error: ${error.message}`);
  } finally {
    isGenerating.value = false;
  }
}

// 監聽預覽數據變化
watch(() => storedPreviewData.value, (newData) => {
  if (newData && window.Plotly) {
    updatePreviewPlot(newData);
  }
}, { deep: true });

// 視窗大小調整處理
const handleResize = () => {
  if (plot && storedPreviewData.value) {
    Plotly.Plots.resize(document.getElementById('previewPlot'));
  }
};

// 生命週期處理
onMounted(() => {
  if (storedPreviewData.value) {
    updatePreviewPlot(storedPreviewData.value);
  }
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  if (plot) {
    Plotly.purge(document.getElementById('previewPlot'));
  }
  window.removeEventListener('resize', handleResize);
});

// 導出設定與方法
defineExpose({
  previewSettings,
  handleGetSXMStatus,
  generatePreview,
  getSettings: () => previewSettings.value
});

//添加對 imageSettings 的監聽
watch(() => imageSettings.value, (newSettings) => {
  if (storedPreviewData.value) {
    updatePreviewPlot(storedPreviewData.value);
  }
}, { deep: true });
</script>