<template>
    <div class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-xl font-semibold mb-6 text-gray-900">
        Channel {{ channel }} ({{ channel === 1 ? 'Source-Drain' : 'Gate' }})
      </h2>
      
      <div class="space-y-6">
        <!-- Mode Selection -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Mode:</label>
          <select
            v-model="state.mode"
            class="w-40 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="VOLTAGE">Voltage</option>
            <option value="CURRENT">Current</option>
          </select>
        </div>
        
        <!-- Output Value -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Output Value:
          </label>
          <div class="flex items-center space-x-2">
            <input
              v-model.number="state.value"
              type="number"
              step="0.1"
              class="w-40 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
            <span class="text-gray-600">{{ state.mode === 'VOLTAGE' ? 'V' : 'A' }}</span>
            <button
              @click="handleSetValue"
              class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              Set
            </button>
          </div>
        </div>
        
        <!-- Control Buttons -->
        <div class="flex space-x-4">
          <button
            @click="handleToggleOutput"
            :class="[
              'px-4 py-2 text-white rounded-md',
              state.outputOn ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
            ]"
          >
            Output {{ state.outputOn ? 'ON' : 'OFF' }}
          </button>
          
          <button
            @click="$emit('read-values', channel)"
            class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            Read Values
          </button>
        </div>
        
        <!-- Reading Display -->
        <ReadingDisplay
          :channel="channel"
          :reading="reading"
        />
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  import ReadingDisplay from './ReadingDisplay.vue'
  
  const props = defineProps({
    channel: { type: Number, required: true },
    state: { type: Object, required: true }
  })
  
  const emit = defineEmits(['set-value', 'toggle-output', 'read-values'])
  
  const reading = ref({
    voltage: 0,
    current: 0,
    lastRead: null
  })
  
  const handleSetValue = () => {
    emit('set-value', props.channel, props.state.mode, props.state.value)
  }
  
  const handleToggleOutput = () => {
    emit('toggle-output', props.channel)
  }
  </script>