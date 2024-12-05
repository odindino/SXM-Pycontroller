<template>
    <div class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-xl font-semibold mb-6 text-gray-900">Connection Settings</h2>
      
      <div class="flex items-center space-x-4">
        <div class="flex-1">
          <label class="block text-sm font-medium text-gray-700 mb-1">
            VISA Address:
          </label>
          <input
            type="text"
            :value="visaAddress"
            @input="$emit('update:visa-address', $event.target.value)"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            :disabled="isConnected"
          />
        </div>
        
        <button
          v-if="!isConnected"
          @click="$emit('connect')"
          class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Connect
        </button>
        
        <button
          v-else
          @click="$emit('disconnect')"
          class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
        >
          Disconnect
        </button>
        
        <div
          :class="[
            'w-3 h-3 rounded-full',
            isConnected ? 'bg-green-500' : 'bg-red-500'
          ]"
        />
      </div>
    </div>
  </template>
  
  <script setup>
  import { defineProps, defineEmits } from 'vue'
  
  defineProps({
    visaAddress: { type: String, required: true },
    isConnected: { type: Boolean, required: true }
  })
  
  defineEmits(['connect', 'disconnect', 'update:visa-address'])
  </script>