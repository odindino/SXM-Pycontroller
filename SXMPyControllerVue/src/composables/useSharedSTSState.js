// composables/useSharedSTSState.js
import { ref, watchEffect } from 'vue'

// 創建持久化的響應式狀態
const selectedScript = ref(localStorage.getItem('selectedSTSScript') || '')
const scriptSettings = ref(null)

try {
  const savedSettings = localStorage.getItem('stsScriptSettings')
  if (savedSettings) {
    scriptSettings.value = JSON.parse(savedSettings)
  }
} catch (error) {
  console.error('Error parsing stored settings:', error)
}

// 監聽狀態變化並自動保存
watchEffect(() => {
  if (selectedScript.value) {
    localStorage.setItem('selectedSTSScript', selectedScript.value)
  }
  
  if (scriptSettings.value) {
    localStorage.setItem('stsScriptSettings', JSON.stringify(scriptSettings.value))
  }
})

export function useSharedSTSState() {
  const updateSelectedScript = (scriptName, settings = null) => {
    selectedScript.value = scriptName
    if (settings) {
      scriptSettings.value = settings
      localStorage.setItem('stsScriptSettings', JSON.stringify(settings))
    }
  }

  const clearScriptState = () => {
    selectedScript.value = ''
    scriptSettings.value = null
    localStorage.removeItem('selectedSTSScript')
    localStorage.removeItem('stsScriptSettings')
  }

  return {
    selectedScript,
    scriptSettings,
    updateSelectedScript,
    clearScriptState
  }
}