<template>
    <div class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-xl font-semibold text-gray-900 mb-6">Movement Script Settings</h2>
      
      <!-- 腳本名稱與選擇 -->
      <div class="space-y-6">
        <div class="flex space-x-4 items-end">
          <div class="flex-1">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Script Name
            </label>
            <input
              type="text"
              :value="scriptName"
              @input="$emit('update:script-name', $event.target.value)"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="Enter script name"
            />
          </div>
          
          <button
            @click="$emit('save-script')"
            class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            Save Script
          </button>
        </div>
        
        <!-- 腳本選擇 -->
        <div class="flex space-x-4">
          <select
            :value="selectedScript"
            @change="$emit('select-script', $event.target.value)"
            class="flex-1 px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">Select Script...</option>
            <option
              v-for="script in availableScripts"
              :key="script.name"
              :value="script.name"
            >
              {{ script.name }}
            </option>
          </select>
          
          <button
            @click="$emit('refresh-scripts')"
            class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            Update Scripts
          </button>
        </div>
        
        <!-- 移動參數設定 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-2">
            <label class="block text-sm font-medium text-gray-700">
              Movement Script (R: Right, U: Up, L: Left, D: Down)
            </label>
            <input
              type="text"
              :value="movementScript"
              @input="$emit('update:movement-script', $event.target.value)"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="e.g., RULD"
            />
          </div>
          
          <div class="space-y-2">
            <label class="block text-sm font-medium text-gray-700">
              Distance (nm)
            </label>
            <input
              type="number"
              :value="distance"
              @input="$emit('update:distance', parseFloat($event.target.value))"
              step="0.1"
              min="0"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          
          <div class="space-y-2">
            <label class="block text-sm font-medium text-gray-700">
              Wait Time (s)
            </label>
            <input
              type="number"
              :value="waitTime"
              @input="$emit('update:wait-time', parseFloat($event.target.value))"
              step="0.1"
              min="0"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          
          <div class="space-y-2">
            <label class="block text-sm font-medium text-gray-700">
              Repeat Count
            </label>
            <input
              type="number"
              :value="repeatCount"
              @input="$emit('update:repeat-count', parseInt($event.target.value))"
              min="1"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  defineProps({
    scriptName: {
      type: String,
      required: true
    },
    selectedScript: {
      type: String,
      required: true
    },
    availableScripts: {
      type: Array,
      required: true
    },
    movementScript: {
      type: String,
      required: true
    },
    distance: {
      type: Number,
      required: true
    },
    waitTime: {
      type: Number,
      required: true
    },
    repeatCount: {
      type: Number,
      required: true
    }
  })
  
  defineEmits([
    'update:script-name',
    'update:movement-script',
    'update:distance',
    'update:wait-time',
    'update:repeat-count',
    'save-script',
    'select-script',
    'refresh-scripts'
  ])
  </script>