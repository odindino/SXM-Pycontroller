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
  
        <!-- SMU腳本選擇 -->
        <div class="flex space-x-4 items-end">
          <div class="flex-1">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              SMU Script (for Multi-STS)
            </label>
            <select
              :value="selectedScript"
              @change="$emit('select-script', $event.target.value)"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Select Script...</option>
              <option
                v-for="script in availableSMUScripts"
                :key="script.name"
                :value="script.name"
              >
                {{ script.name }}
              </option>
            </select>
          </div>
  
          <button
            @click="$emit('refresh-scripts')"
            class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
          >
            Update Scripts
          </button>
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
  defineProps({
    pointsX: {
      type: Number,
      required: true
    },
    pointsY: {
      type: Number,
      required: true
    },
    scanDirection: {
      type: Number,
      required: true
    },
    availableSMUScripts: {
      type: Array,
      required: true
    },
    selectedScript: {
      type: String,
      required: true
    },
    isRunning: {
      type: Boolean,
      default: false
    }
  })
  
  defineEmits([
    'update:points-x',
    'update:points-y',
    'update:scan-direction',
    'select-script',
    'refresh-scripts',
    'start-single-cits',
    'start-multi-cits'
  ])
  </script>