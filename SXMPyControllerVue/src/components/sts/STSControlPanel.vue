<template>
  <div class="bg-white p-6 rounded-lg shadow">
    <h2 class="text-xl font-semibold text-gray-900 mb-6">STS Control</h2>

    <div class="space-y-6">
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
  selectedScript: {
    type: String,
    default: ''
  },
  isRunning: {
    type: Boolean,
    default: false
  }
})

defineEmits(['start-single-sts', 'start-multi-sts'])
</script>