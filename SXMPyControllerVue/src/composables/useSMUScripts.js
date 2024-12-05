import { ref } from 'vue'

export function useSMUScripts() {
  const isLoading = ref(false)

  const loadScripts = async () => {
    try {
      return await window.pywebview.api.get_sts_scripts()
    } catch (error) {
      console.error('Failed to load SMU scripts:', error)
      throw error
    }
  }

  const saveScript = async (name, vdsList, vgList) => {
    try {
      return await window.pywebview.api.save_sts_script(name, vdsList, vgList)
    } catch (error) {
      console.error('Failed to save SMU script:', error)
      throw error
    }
  }

  return {
    isLoading,
    loadScripts,
    saveScript
  }
}