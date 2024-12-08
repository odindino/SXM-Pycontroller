import { ref, computed } from 'vue'

export function useSMUScripts() {
  const isLoading = ref(false)
  const rawScripts = ref({})

  const scripts = computed(() => {
    return rawScripts.value || {}
  })

  // const loadScripts = async () => {
  //   try {
  //     isLoading.value = true
  //     const response = await window.pywebview.api.get_sts_scripts()
  //     // 確保回傳的數據被正確解構
  //     rawScripts.value = JSON.parse(JSON.stringify(response)) || {}
  //     return rawScripts.value
  //   } catch (error) {
  //     console.error('Script loading error:', error)
  //     rawScripts.value = {}
  //     throw error
  //   } finally {
  //     isLoading.value = false
  //   }
  // }
  const loadScripts = async () => {
    try {
      isLoading.value = true
      const response = await window.pywebview.api.get_sts_scripts()
      rawScripts.value = response || {}
      return Object.keys(rawScripts.value).map(key => ({
        name: rawScripts.value[key].name,
        vds_list: rawScripts.value[key].vds_list,
        vg_list: rawScripts.value[key].vg_list
      }))
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