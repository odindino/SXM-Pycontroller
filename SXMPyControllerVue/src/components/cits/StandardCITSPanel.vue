<template>
  <div class="bg-white p-6 rounded-lg shadow">
    <h2 class="text-xl font-semibold text-gray-900 mb-6">CITS Control</h2>

    <div class="space-y-6">
      <!-- 點數設定 -->
      <div class="grid grid-cols-2 gap-6">
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">
            Points X (1-512)
          </label>
          <input
            type="number"
            :value="pointsX"
            @input="$emit('update:points-x', parseInt($event.target.value))"
            min="1"
            max="512"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">
            Points Y (1-512)
          </label>
          <input
            type="number"
            :value="pointsY"
            @input="$emit('update:points-y', parseInt($event.target.value))"
            min="1"
            max="512"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
      </div>

      <!-- 掃描方向 -->
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">
          Scan Direction
        </label>
        <div class="flex space-x-4">
          <label class="inline-flex items-center">
            <input
              type="radio"
              :value="1"
              :checked="scanDirection === 1"
              @change="$emit('update:scan-direction', 1)"
              class="form-radio h-4 w-4 text-indigo-600"
            />
            <span class="ml-2 text-gray-700">Scan Up</span>
          </label>
          <label class="inline-flex items-center">
            <input
              type="radio"
              :value="-1"
              :checked="scanDirection === -1"
              @change="$emit('update:scan-direction', -1)"
              class="form-radio h-4 w-4 text-indigo-600"
            />
            <span class="ml-2 text-gray-700">Scan Down</span>
          </label>
        </div>
      </div>

      <!-- SMU腳本資訊顯示 -->
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">
          Selected SMU Script
        </label>
        <div class="p-4 bg-gray-50 rounded-md border border-gray-200">
          <p class="text-sm text-gray-600">
            {{ selectedScript ? selectedScript : 'No script selected' }}
          </p>
          <p v-if="!selectedScript" class="text-xs text-amber-600 mt-2">
            Note: Multi-STS CITS requires a script selected in STS Measurement page
          </p>
        </div>
      </div>

      <!-- 執行按鈕 -->
      <div class="grid grid-cols-2 gap-4">
        <button
          @click="$emit('start-single-cits')"
          :disabled="isRunning"
          class="px-4 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Start Single-STS CITS
        </button>

        <button
          @click="$emit('start-multi-cits')"
          :disabled="isRunning || !selectedScript"
          class="px-4 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Start Multi-STS CITS
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useSharedSTSState } from '../../composables/useSharedSTSState'

// 使用共享的 STS 狀態
const { selectedScript } = useSharedSTSState()

// Props 定義
defineProps({
  pointsX: {
    type: Number,
    required: true,
    validator: value => value >= 1 && value <= 512
  },
  pointsY: {
    type: Number,
    required: true,
    validator: value => value >= 1 && value <= 512
  },
  scanDirection: {
    type: Number,
    required: true,
    validator: value => value === 1 || value === -1
  },
  isRunning: {
    type: Boolean,
    default: false
  }
})

// Emits 定義
defineEmits([
  'update:points-x',
  'update:points-y',
  'update:scan-direction',
  'start-single-cits',
  'start-multi-cits'
])
</script>