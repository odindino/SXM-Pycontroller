import { ref } from 'vue'

export function useSTS() {
  const isRunning = ref(false)

  const startSTS = async () => {
    try {
      return await window.pywebview.api.start_sts()
    } catch (error) {
      console.error('Failed to start STS:', error)
      throw error
    }
  }

  const startMultiSTS = async (scriptName) => {
    try {
      return await window.pywebview.api.perform_multi_sts(scriptName)
    } catch (error) {
      console.error('Failed to start Multi-STS:', error)
      throw error
    }
  }

  return {
    isRunning,
    startSTS,
    startMultiSTS
  }
}