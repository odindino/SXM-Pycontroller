<template>
  <div class="bg-white p-6 rounded-lg shadow">
    <h2 class="text-xl font-semibold text-gray-900 mb-6">Preview Settings</h2>

    <!-- 設定輸入區域 -->
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
    </div>

    <!-- 按鈕區域 -->
    <div class="flex justify-end space-x-4 mb-6">
      <button
        @click="handleGetSXMStatus"
        class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
      >
        Get SXM Status
      </button>
      <button
        @click="handlePreviewAutoMove"
        class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
      >
        Preview Auto-Move
      </button>
    </div>

    <!-- 預覽結果顯示 -->
    <div v-if="previewData" class="space-y-4">
      <div class="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-md">
        <div>
          <span class="text-sm text-gray-500">Position:</span>
          <p class="font-mono">
            ({{ formatNumber(previewSettings.center_x) }}, {{ formatNumber(previewSettings.center_y) }}) nm
          </p>
        </div>
        <div>
          <span class="text-sm text-gray-500">Angle:</span>
          <p class="font-mono">{{ formatNumber(previewSettings.scan_angle) }}°</p>
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
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  previewData: {
    type: Object,
    default: null
  },
  movementScript: {
    type: String,
    required: true
  },
  moveDistance: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['update:preview-data'])

const previewSettings = ref({
  center_x: 0,
  center_y: 0,
  scan_range: 100,
  scan_angle: 0
})

// 格式化數字顯示
const formatNumber = (value) => {
  return Number(value).toFixed(2)
}

// 取得 SXM 狀態
const handleGetSXMStatus = async () => {
  try {
    const status = await window.pywebview.api.get_sxm_status()
    previewSettings.value = {
      center_x: Number(status.center_x || 0),
      center_y: Number(status.center_y || 0),
      scan_range: Number(status.range || 100),
      scan_angle: Number(status.angle || 0)
    }
  } catch (error) {
    console.error('Failed to get SXM status:', error)
    alert('Failed to get SXM status. Check connection and try again.')
  }
}

// 生成預覽
const handlePreviewAutoMove = async () => {
  try {
    const preview = await window.pywebview.api.preview_auto_move({
      movement_script: props.movementScript,
      distance: props.moveDistance,
      center_x: previewSettings.value.center_x,
      center_y: previewSettings.value.center_y,
      angle: previewSettings.value.scan_angle
    })
    emit('update:preview-data', preview)
  } catch (error) {
    console.error('Preview generation error:', error)
    alert('Failed to generate preview. Please check your settings.')
  }
}

// Plotly 圖表管理
let plot = null

watch(() => props.previewData, (newData) => {
  if (newData && window.Plotly) {
    updatePreviewPlot(newData)
  }
}, { deep: true })

const updatePreviewPlot = (data) => {
  const plotElement = document.getElementById('previewPlot')
  if (!plotElement) return

  if (plot) {
    Plotly.purge(plotElement)
  }

  plot = Plotly.newPlot(plotElement, data.data, {
    ...data.layout,
    showlegend: true,
    margin: { l: 50, r: 30, t: 30, b: 50 },
    hovermode: 'closest'
  }, {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d']
  })
}

// 組件生命週期處理
onMounted(() => {
  if (props.previewData) {
    updatePreviewPlot(props.previewData)
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (plot) {
    Plotly.purge(document.getElementById('previewPlot'))
  }
  window.removeEventListener('resize', handleResize)
})

const handleResize = () => {
  if (plot && props.previewData) {
    Plotly.Plots.resize(document.getElementById('previewPlot'))
  }
}
</script>