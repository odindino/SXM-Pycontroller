<template>
    <div class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-xl font-semibold text-gray-900 mb-6">Preview & Status</h2>
  
      <div class="space-y-6">
        <!-- 狀態顯示區域 -->
        <div
          class="p-4 rounded-md"
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
  
        <!-- 預覽區域 -->
        <div v-if="previewData" class="space-y-4">
          <h3 class="text-lg font-medium text-gray-900">Preview Information</h3>
          
          <!-- 掃描參數顯示 -->
          <div class="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-md">
            <div class="space-y-1">
              <label class="text-sm text-gray-500">Scan Center</label>
              <p class="font-mono">
                ({{ previewData.center_x?.toFixed(2) ?? '-' }},
                {{ previewData.center_y?.toFixed(2) ?? '-' }}) nm
              </p>
            </div>
            <div class="space-y-1">
              <label class="text-sm text-gray-500">Scan Range</label>
              <p class="font-mono">
                {{ previewData.range?.toFixed(2) ?? '-' }} nm
              </p>
            </div>
            <div class="space-y-1">
              <label class="text-sm text-gray-500">Scan Angle</label>
              <p class="font-mono">
                {{ previewData.angle?.toFixed(2) ?? '-' }}°
              </p>
            </div>
            <div class="space-y-1">
              <label class="text-sm text-gray-500">Total Points</label>
              <p class="font-mono">
                {{ previewData.total_points ?? '-' }}
              </p>
            </div>
          </div>
  
          <!-- 預覽圖 -->
          <div class="border border-gray-200 rounded-lg overflow-hidden">
            <div id="previewPlot" class="w-full h-96"></div>
          </div>
        </div>
  
        <!-- 最近測量結果 -->
        <div v-if="lastMeasurement" class="space-y-4">
          <h3 class="text-lg font-medium text-gray-900">Last Measurement</h3>
          <div class="bg-gray-50 p-4 rounded-md">
            <div class="space-y-2 font-mono text-sm">
              <div class="grid grid-cols-2 gap-2">
                <span class="text-gray-500">Time:</span>
                <span>{{ formatTime(lastMeasurement.timestamp) }}</span>
  
                <span class="text-gray-500">Type:</span>
                <span>{{ lastMeasurement.type }}</span>
  
                <span class="text-gray-500">Points:</span>
                <span>{{ lastMeasurement.total_points }}</span>
  
                <span class="text-gray-500">Duration:</span>
                <span>{{ formatDuration(lastMeasurement.duration) }}</span>
  
                <span v-if="lastMeasurement.script" class="text-gray-500">Script:</span>
                <span v-if="lastMeasurement.script">{{ lastMeasurement.script }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { computed, watch, onMounted, onUnmounted } from 'vue'
  
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
  
  const statusIconClass = computed(() => {
    if (props.status.includes('Error')) return 'text-red-400'
    if (props.status.includes('completed') || props.status.includes('success')) return 'text-green-400'
    if (props.status.includes('Starting') || props.status.includes('Running')) return 'text-blue-400'
    return 'text-gray-400'
  })
  
  const statusTextClass = computed(() => {
    if (props.status.includes('Error')) return 'text-red-800'
    if (props.status.includes('completed') || props.status.includes('success')) return 'text-green-800'
    if (props.status.includes('Starting') || props.status.includes('Running')) return 'text-blue-800'
    return 'text-gray-800'
  })
  
  const statusIcon = computed(() => ({
    template: `
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        ${props.status.includes('Error')
          ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />'
          : props.status.includes('completed') || props.status.includes('success')
            ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />'
            : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />'
        }
      </svg>
    `
  }))
  
  // 時間格式化
  const formatTime = (timestamp) => {
    if (!timestamp) return 'N/A'
    return new Date(timestamp).toLocaleString()
  }
  
  const formatDuration = (ms) => {
    if (!ms) return 'N/A'
    const seconds = Math.floor(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    
    const remainingMinutes = minutes % 60
    const remainingSeconds = seconds % 60
    
    const parts = []
    if (hours > 0) parts.push(`${hours}h`)
    if (remainingMinutes > 0) parts.push(`${remainingMinutes}m`)
    if (remainingSeconds > 0) parts.push(`${remainingSeconds}s`)
    
    return parts.join(' ') || '0s'
  }
  
  // 預覽圖更新
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
      displaylogo: false
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