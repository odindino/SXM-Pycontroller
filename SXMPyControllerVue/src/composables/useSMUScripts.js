import { ref, computed } from 'vue'

export function useSMUScripts() {
  const isLoading = ref(false)
  const rawScripts = ref({})

  const scripts = computed(() => {
    return rawScripts.value || {}
  })

  const loadScripts = async () => {
    try {
      isLoading.value = true
      console.log('Fetching scripts from API...')
      const response = await window.pywebview.api.get_sts_scripts()
      console.log('API response:', response)
      rawScripts.value = response || {}
      return response
    } catch (error) {
      console.error('Script loading error:', error)
      rawScripts.value = {}
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const saveScript = async (name, vdsList, vgList) => {
    try {
      isLoading.value = true
      await window.pywebview.api.save_sts_script(name, vdsList, vgList)
      await loadScripts()  // 儲存後重新載入腳本列表
    } catch (error) {
      console.error('Failed to save SMU script:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  return {
    isLoading,
    scripts,
    loadScripts,
    saveScript
  }
}