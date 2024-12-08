import { ref, computed } from 'vue'

export function useSMUScripts() {
  const isLoading = ref(false)
  const rawScripts = ref({})

  const scripts = computed(() => {
    const scriptData = rawScripts.value
    return Object.entries(scriptData).map(([name, data]) => ({
      name,
      vds_list: data.vds_list || [],
      vg_list: data.vg_list || []
    }))
  })

  const loadScripts = async () => {
    try {
      isLoading.value = true
      const response = await window.pywebview.api.get_sts_scripts()
      rawScripts.value = response || {}
      return scripts.value
    } catch (error) {
      console.error('Script loading error:', error)
      rawScripts.value = {}
      return []
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