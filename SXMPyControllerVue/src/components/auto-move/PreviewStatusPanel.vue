<template>
    <div class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-xl font-semibold text-gray-900 mb-6">Preview & Status</h2>
      
      <!-- 上方按鈕組 -->
      <div class="flex space-x-4 mb-6">
        <button
          @click="$emit('get-status')"
          class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          Get SXM Status
        </button>
        
        <button
          @click="$emit('preview-auto-move')"
          class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          Preview Movement
        </button>
      </div>
      
      <!-- 狀態顯示 -->
      <div
        class="p-4 rounded-md mb-6"
        :class="statusContainerClass"
      >
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <component
              :is="statusIcon"
              class="h-5 w-5"
              :class="statusIconClass"
            />
          </div>
          <div class="ml-3">
            <h3
              class="text-sm font-medium"
              :class="statusTextClass"
            >
              {{ status }}
            </h3>
          </div>
        </div>
      </div>
      
      <!-- 預覽資訊 -->
      <div v-if="previewData" class="space-y-4">
        <div class="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-md">
          <div class="space-y-1">
            <label class="text-sm text-gray-500">Position</label>
            <p class="font-mono">
              ({{ previewData.center_x?.toFixed(2) ?? '-' }},
               {{ previewData.center_y?.toFixed(2) ?? '-' }}) nm
            </p>
          </div>
          <div class="space-y-1">
            <label class="text-sm text-gray-500">Angle</label>
            <p class="font-mono">{{ previewData.angle?.toFixed(2) ?? '-' }}°</p>
          </div>
        </div>
        
        <!-- 預覽圖 -->
        <div class="border border-gray-200 rounded-lg overflow-hidden">
          <div id="movePreview" class="w-full h-96"></div>
        </div>
      </div>
      
      <!-- 最近測量記錄 -->
      <div v-if="lastMeasurement" class="mt-6">
        <h3 class="text-lg font-medium text-gray-900 mb-2">Last Measurement</h3>
        <div class="bg-gray-50 p-4 rounded-md">
          <div class="space-y-2 font-mono text-sm">
            <div>Time: {{ formatTime(lastMeasurement.timestamp) }}</div>
            <div>Type: {{ lastMeasurement.type }}</div>
            <div>Total Points: {{ lastMeasurement.total_points }}</div>
            <div>Duration: {{ formatDuration(lastMeasurement.duration) }}</div>
            <div v-if="lastMeasurement.script">Script: {{ lastMeasurement.script }}</div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { computed, watch, onMounted, onUnmounted } from 'vue'
  import { formatDateTime, formatDuration } from '../../utils/formatters'
  
  const props = defineProps({
    status: {
      type: String,
      required: true
    },
    previewData: {
      type: Object,
      default: null
    },
    lastMeasurement: {
      type: Object,
      default: null
    }
  })
  
  defineEmits(['get-status', 'preview-auto-move'])
  
  // 狀態樣式計算
  const statusContainerClass = computed(() => {
    const baseClass = 'border'
    if (props.status.includes('Error')) {
      return `${baseClass} bg-red-50 border-red-200`
    }
    if (props.status.includes('completed') || props.status.includes('success')) {
      return `${baseClass} bg-green-50 border-green-200`
    }
    if (props.status.includes('Starting') || props.status.includes('Running')) {
      return `${baseClass} bg-blue-50 border-blue-200`
    }
    return `${baseClass} bg-gray-50 border-gray-200`
  })
  
  // 預覽圖更新邏輯
  let plot = null
  
  watch(() => props.previewData, (newData) => {
    if (newData && window.Plotly) {
      updatePreviewPlot(newData)
    }
  }, { deep: true })
  
  const updatePreviewPlot = (data) => {
    const plotElement = document.getElementById('movePreview')
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
  
  // 生命週期處理
  onMounted(() => {
    if (props.previewData) {
      updatePreviewPlot(props.previewData)
    }
    window.addEventListener('resize', handleResize)
  })
  
  onUnmounted(() => {
    if (plot) {
      Plotly.purge(document.getElementById('movePreview'))
    }
    window.removeEventListener('resize', handleResize)
  })
  
  const handleResize = () => {
    if (plot && props.previewData) {
      Plotly.Plots.resize(document.getElementById('movePreview'))
    }
  }
  </script>