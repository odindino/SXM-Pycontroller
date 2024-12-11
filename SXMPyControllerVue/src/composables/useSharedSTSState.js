import { ref } from 'vue'

const selectedScript = ref('')
const availableScripts = ref([])

export function useSharedSTSState() {
  const updateSelectedScript = (scriptName) => {
    selectedScript.value = scriptName
  }

  const updateAvailableScripts = (scripts) => {
    availableScripts.value = scripts
  }

  return {
    selectedScript,
    availableScripts,
    updateSelectedScript,
    updateAvailableScripts
  }
}