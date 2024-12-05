<template>
    <div class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-xl font-semibold text-gray-900 mb-6">Status</h2>
  
      <div class="space-y-4">
        <!-- 當前狀態顯示 -->
        <div class="p-4 rounded-md" :class="statusClass">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <component
                :is="statusIcon"
                class="h-5 w-5"
                :class="statusIconClass"
              />
            </div>
            <div class="ml-3">
              <p class="text-sm font-medium" :class="statusTextClass">
                {{ status }}
              </p>
            </div>
          </div>
        </div>
  
        <!-- 最近測量結果 -->
        <div v-if="lastMeasurement" class="mt-4">
          <h3 class="text-lg font-medium text-gray-900 mb-2">Last Measurement</h3>
          <div class="bg-gray-50 p-4 rounded-md">
            <div class="space-y-2 font-mono text-sm">
              <div>Time: {{ formatTime(lastMeasurement.timestamp) }}</div>
              <div>Position: ({{ lastMeasurement.x.toFixed(2) }}, {{ lastMeasurement.y.toFixed(2) }}) nm</div>
              <div v-if="lastMeasurement.script">Script: {{ lastMeasurement.script }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { computed } from 'vue'
  
  const props = defineProps({
    status: {
      type: String,
      required: true
    },
    lastMeasurement: {
      type: Object,
      default: null
    }
  })
  
  // 根據狀態計算顯示樣式
  const statusClass = computed(() => {
    if (props.status.includes('Error')) {
      return 'bg-red-50'
    }
    if (props.status.includes('completed') || props.status.includes('successfully')) {
      return 'bg-green-50'
    }
    if (props.status.includes('Starting') || props.status.includes('Running')) {
      return 'bg-blue-50'
    }
    return 'bg-gray-50'
  })
  
  // 狀態圖示
  const statusIcon = computed(() => {
    return {
      template: `
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          ${props.status.includes('Error')
            ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />'
            : props.status.includes('completed') || props.status.includes('successfully')
              ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />'
              : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />'
          }
        </svg>
      `
    }
  })
  
  // 圖示顏色
  const statusIconClass = computed(() => {
    if (props.status.includes('Error')) {
      return 'text-red-400'
    }
    if (props.status.includes('completed') || props.status.includes('successfully')) {
      return 'text-green-400'
    }
    return 'text-blue-400'
  })
  
  // 文字顏色
  const statusTextClass = computed(() => {
    if (props.status.includes('Error')) {
      return 'text-red-800'
    }
    if (props.status.includes('completed') || props.status.includes('successfully')) {
      return 'text-green-800'
    }
    return 'text-blue-800'
  })
  
  // 格式化時間戳記
  const formatTime = (timestamp) => {
    if (!timestamp) return 'N/A'
    return new Date(timestamp).toLocaleString()
  }
  </script>