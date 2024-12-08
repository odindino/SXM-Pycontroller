<template>
  <div class="bg-white p-6 rounded-lg shadow">
    <h2 class="text-xl font-semibold text-gray-900 mb-6">STS Control</h2>

    <div class="space-y-6">
      <!-- SMU腳本選擇區域 -->
      <div class="flex space-x-4 items-end">
        <div class="flex-1">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Select SMU Script
          </label>
          <select
            :value="selectedScript"
            @change="handleScriptChange"
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
  
        <!-- STS控制按鈕 -->
        <div class="grid grid-cols-2 gap-4">
          <button
            @click="$emit('start-single-sts')"
            :disabled="isRunning"
            class="px-4 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Single STS
          </button>
  
          <button
            @click="$emit('start-multi-sts')"
            :disabled="isRunning || !selectedScript"
            class="px-4 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Multi-STS
          </button>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  defineProps({
    availableSMUScripts: {
      type: Array,
      default: () => []
    },
    selectedScript: {
      type: String,
      default: ''
    },
    isRunning: {
      type: Boolean,
      default: false
    }
  })

  defineEmits(['select-script', 'refresh-scripts', 'start-single-sts', 'start-multi-sts'])

  const handleScriptChange = (event) => {
    event.target.value && emit('select-script', event.target.value)
  }
  </script>