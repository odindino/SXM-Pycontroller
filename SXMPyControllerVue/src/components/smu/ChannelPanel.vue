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
        
        <!-- Compliance Setting -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Compliance:
          </label>
          <div class="flex items-center space-x-2">
            <input
              v-model.number="compliance"
              type="number"
              step="0.001"
              class="w-40 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
            <span class="text-gray-600">A</span>
            <button
              @click="handleSetCompliance"
              class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              Set
            </button>
            
          </div>
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
            @click="handleReadValues"
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
  import { ref, watch } from 'vue'
  import ReadingDisplay from './ReadingDisplay.vue'
  
  const props = defineProps({
    channel: { type: Number, required: true },
    state: { type: Object, required: true }
  })
  
  const emit = defineEmits(['set-value', 'toggle-output', 'read-values', 'set-compliance', 'read-compliance'])
  
  const reading = ref({
    voltage: 0,
    current: 0,
    lastRead: null
  })
  
  const compliance = ref(0.01) // 預設值 0.01 A
  
  const handleSetValue = () => {
    emit('set-value', props.channel, props.state.mode, props.state.value)
  }
  
  const handleToggleOutput = async () => {
    try {
      await emit('toggle-output', props.channel)
      console.log(`Channel ${props.channel} output state:`, props.state.outputOn)
    } catch (error) {
      console.error('Toggle output error:', error)
    }
  }

  // 讀值處理函數
  const handleReadValues = async () => {
    try {
      const values = await window.pywebview.api.read_channel(props.channel)
      if (values) {
        reading.value = {
          voltage: values.voltage,
          current: values.current,
          lastRead: new Date().toLocaleString()
        }
        console.log('Updated reading values:', reading.value)
      }
    } catch (error) {
      console.error('Error reading values:', error)
    }
  }
  
  const handleSetCompliance = () => {
    emit('set-compliance', props.channel, compliance.value)
  }
  
  const handleReadCompliance = async () => {
    const value = await emit('read-compliance', props.channel)
    if (value) {
      compliance.value = value
    }

  // 監聽狀態變化
  watch(() => props.state.outputOn, (newValue) => {
    console.log(`Channel ${props.channel} output state changed to:`, newValue)
  })

  // 監聽讀值更新
  watch(() => reading.value, (newValue) => {
    console.log(`Channel ${props.channel} reading updated:`, newValue)
  }, { deep: true })

  }
  </script>