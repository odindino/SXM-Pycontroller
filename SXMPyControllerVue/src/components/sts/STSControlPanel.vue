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
            v-model="selectedScriptLocal"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
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
        </div>

        <button
          @click="handleRefreshScripts"
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
          :disabled="isRunning || !selectedScriptLocal"
          class="px-4 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Start Multi-STS
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useSMUScripts } from '../../composables/useSMUScripts'

const { loadScripts } = useSMUScripts()

// 在組件內部管理狀態
const availableScripts = ref([])
const selectedScriptLocal = ref('')
const isRunning = ref(false)

const handleRefreshScripts = async () => {
  try {
    console.log('Requesting script refresh')
    const response = await loadScripts()
    
    // 直接處理回應數據
    availableScripts.value = Object.entries(response).map(([_, script]) => ({
      name: script.name,
      vds_list: script.vds_list,
      vg_list: script.vg_list
    }))
    
    console.log('Available scripts updated:', availableScripts.value)
  } catch (error) {
    console.error('Script refresh error:', error)
  }
}

// 監視本地選擇的腳本變化
watch(selectedScriptLocal, (newValue) => {
  emit('select-script', newValue)
})

// 組件掛載時載入腳本
onMounted(() => {
  handleRefreshScripts()
})

const emit = defineEmits(['select-script', 'start-single-sts', 'start-multi-sts'])
</script>