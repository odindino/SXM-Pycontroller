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

  plot = Plotly.newPlot(plotElement, data.data, layout, config);
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
</script>