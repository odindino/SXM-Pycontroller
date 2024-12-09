<template>
  <nav class="fixed top-0 left-0 right-0 z-50 bg-white shadow">
    <div class="container mx-auto px-4">
      <div class="flex space-x-8 h-16">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="[
            'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium',
            activeTab === tab.id
              ? 'border-indigo-500 text-gray-900'
              : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
          ]"
          @click="$emit('change-tab', tab.id)"
        >
          {{ tab.name }}
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  activeTab: { type: String, required: true }
})

defineEmits(['change-tab'])

const tabs = [
  { id: 'smu-config', name: 'SMU Config' },
  { id: 'sts-measurement', name: 'STS Measurement' },
  { id: 'cits-measurement', name: 'CITS Measurement' },
  { id: 'auto-move-measurement', name: 'Auto Move' }
]
</script>