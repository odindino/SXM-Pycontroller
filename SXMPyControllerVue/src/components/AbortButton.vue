<template>
  <div class="fixed right-4 top-24 z-50">
    <button
      @click="handleAbort"
      class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 
             shadow-lg transform hover:scale-105 transition-transform duration-200
             focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
             flex items-center space-x-2"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
      </svg>
      <span>Stop Measurement</span>
    </button>
  </div>

  <!-- 確認對話框 -->
  <div v-if="showConfirm" 
       class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white p-6 rounded-lg shadow-xl max-w-sm w-full mx-4">
      <h3 class="text-lg font-medium text-gray-900 mb-4">
        確認停止測量
      </h3>
      <p class="text-gray-600 mb-6">
        這會中斷所有操作並重置系統。確定要繼續嗎？
      </p>
      <div class="flex justify-end space-x-4">
        <button
          @click="showConfirm = false"
          class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 
                 hover:bg-gray-50 focus:outline-none focus:ring-2 
                 focus:ring-offset-2 focus:ring-indigo-500"
        >
          取消
        </button>
        <button
          @click="confirmAbort"
          class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 
                 focus:outline-none focus:ring-2 focus:ring-offset-2 
                 focus:ring-red-500"
        >
          確定停止
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['measurement-stopped'])
const showConfirm = ref(false)

const handleAbort = () => {
  showConfirm.value = true
}

const confirmAbort = async () => {
  try {
    const success = await window.pywebview.api.stop_measurement()
    
    if (success) {
      emit('measurement-stopped')
    }
    
  } catch (error) {
    console.error('Stop measurement error:', error)
  } finally {
    showConfirm.value = false
  }
}
</script>