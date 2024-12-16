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
  
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <!-- 掃描中心座標 -->
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">
            Center X (nm)
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
            Center Y (nm)
          </label>
          <input
            type="number"
            v-model.number="previewSettings.center_y"
            step="0.1"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
  
        <!-- 掃描範圍設定 -->
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
  
        <!-- 掃描參數 -->
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
  
      <!-- 預覽資訊和圖表 -->
      <div v-if="previewData" class="space-y-4">
        <div class="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-md">
          <div>
            <span class="text-sm text-gray-500">Scan Center:</span>
            <p class="font-mono">
              ({{ previewData.center_x?.toFixed(2) }}, {{ previewData.center_y?.toFixed(2) }}) nm
            </p>
          </div>
          <div>
            <span class="text-sm text-gray-500">Total Points:</span>
            <p class="font-mono">{{ previewData.total_points }}</p>
          </div>
        </div>
  
        <!-- 預覽圖表區域 -->
        <div class="border border-gray-200 rounded-lg overflow-hidden">
          <div id="previewPlot" class="w-full h-96"></div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onUnmounted } from 'vue';
  
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
  
  // 預覽設定狀態
  const previewSettings = ref({
    center_x: 0,
    center_y: 0,
    scan_range: 50,
    scan_angle: 0,
    total_lines: 1000,
    aspect_ratio: 0.5
  });
  
  // 預覽資料和狀態
  const previewData = ref(null);
  const isGenerating = ref(false);
  
  // 從 SXM 獲取狀態
  async function handleGetSXMStatus() {
    try {
      const status = await window.pywebview.api.get_sxm_status();
      previewSettings.value = {
        ...previewSettings.value,
        center_x: status.center_x,
        center_y: status.center_y,
        scan_range: status.scan_range,
        scan_angle: status.scan_angle,
        total_lines: status.total_lines,
        aspect_ratio: status.aspect_ratio
      };
    } catch (error) {
      console.error('Failed to get SXM status:', error);
      alert('Failed to get SXM status. Check connection and try again.');
    }
  }
  
  // 生成預覽
  async function generatePreview() {
    if (isGenerating.value) return;
  
    try {
      isGenerating.value = true;
      const params = {
        ...previewSettings.value,
        scan_direction: props.scanDirection,
        local_areas: props.localAreas
      };
  
      const preview = await window.pywebview.api.preview_local_cits(params);
      previewData.value = preview;
  
      // 使用 Plotly 更新圖表
      const plotElement = document.getElementById('previewPlot');
      if (plotElement && window.Plotly) {
        window.Plotly.newPlot(plotElement, preview.data, {
          ...preview.layout,
          margin: { l: 50, r: 30, t: 30, b: 50 }
        }, {
          responsive: true,
          displayModeBar: true,
          displaylogo: false
        });
      }
    } catch (error) {
      console.error('Preview generation error:', error);
      alert('Failed to generate preview. Check settings and try again.');
    } finally {
      isGenerating.value = false;
    }
  }
  
  // 元件清理
  onUnmounted(() => {
    const plotElement = document.getElementById('previewPlot');
    if (plotElement && window.Plotly) {
      window.Plotly.purge(plotElement);
    }
  });
  </script>