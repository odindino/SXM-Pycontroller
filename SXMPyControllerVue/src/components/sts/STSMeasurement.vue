<template>
  <div class="space-y-8">
    <!-- SMU腳本編輯區域 -->
    <SMUScriptEditor
      :script-name="scriptName"
      :vds-list="vdsList"
      :vg-list="vgList"
      @update:script-name="updateScriptName"
      @add-row="addSettingRow"
      @remove-row="removeSettingRow"
      @save-script="saveSMUScript"
    />

    <!-- STS控制面板 -->
    <STSControlPanel
      :available-smu-scripts="availableSMUScripts"
      :selected-script="selectedScript"
      :is-running="isRunning"
      @select-script="loadSMUScript"
      @refresh-scripts="refreshSMUScripts"
      @start-single-sts="startSingleSTS"
      @start-multi-sts="startMultiSTS"
    />

    <!-- 狀態顯示 -->
    <STSStatusDisplay
      :status="status"
      :last-measurement="lastMeasurement"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import SMUScriptEditor from './SMUScriptEditor.vue'
import STSControlPanel from './STSControlPanel.vue'
import STSStatusDisplay from './STSStatusDisplay.vue'
import { useSMUScripts } from '../../composables/useSMUScripts'
import { useSTS } from '../../composables/useSTS'

const availableSMUScripts = ref([])
const {
  scripts: scripts,
  loadScripts: loadSMUScripts,
  saveScript: saveSMUScriptToAPI
} = useSMUScripts()

// 修改 availableSMUScripts 的計算方式
// const availableSMUScripts = computed(() => {
//   console.log('Computing available scripts:', scripts.value)
//   if (!scripts.value) return []
//   return Object.entries(scripts.value).map(([name, data]) => {
//     console.log('Processing script:', name, data)
//     return {
//       name,
//       vds_list: data.vds_list || [],
//       vg_list: data.vg_list || []
//     }
//   })
// })



const {
  startSTS,
  startMultiSTS: startMultiSTSMeasurement
} = useSTS()
  
// 基本狀態管理
const scriptName = ref('')
const vdsList = ref([])
const vgList = ref([])
const selectedScript = ref('')
const isRunning = ref(false)
const status = ref('Ready')
const lastMeasurement = ref(null)

// 更新腳本名稱
const updateScriptName = (name) => {
  scriptName.value = name
}

// 添加新的 SMU 設定行
const addSettingRow = () => {
  vdsList.value.push(0)
  vgList.value.push(0)
}

// 移除 SMU 設定行
const removeSettingRow = (index) => {
  vdsList.value.splice(index, 1)
  vgList.value.splice(index, 1)
}

// 保存 SMU 腳本
const saveSMUScript = async () => {
  if (!scriptName.value.trim()) {
    status.value = 'Please provide a script name'
    return
  }
  
  try {
    status.value = 'Saving SMU script...'
    await saveSMUScriptToAPI(scriptName.value, vdsList.value, vgList.value)
    status.value = 'SMU script saved successfully'
    await refreshSMUScripts()
  } catch (error) {
    status.value = `Error saving SMU script: ${error.message}`
  }
}

// // 重新整理 SMU 腳本列表
// const refreshSMUScripts = async () => {
//   try {
//     status.value = 'Refreshing SMU scripts...'
//     const result = await loadSMUScripts()
//     console.log('Loaded scripts result:', result)
    
//     if (result) {
//       scripts.value = result
//       console.log('Updated scripts value:', scripts.value)
//       console.log('Available scripts computed:', availableSMUScripts.value)
//       status.value = 'SMU scripts refreshed'
//     } else {
//       status.value = 'No scripts found'
//     }
//   } catch (error) {
//     console.error('Error loading scripts:', error)
//     status.value = `Error loading SMU scripts: ${error.message}`
//   }
// }

const processScripts = (scriptsData) => {
  if (!scriptsData) return []
  return Object.entries(scriptsData).map(([name, data]) => ({
    name,
    vds_list: data.vds_list || [],
    vg_list: data.vg_list || []
  }))
}

const refreshSMUScripts = async () => {
  try {
    status.value = 'Refreshing SMU scripts...'
    const result = await loadSMUScripts()
    console.log('Loaded scripts:', result)
    
    if (result) {
      availableSMUScripts.value = processScripts(result)
      console.log('Processed scripts:', availableSMUScripts.value)
      status.value = 'SMU scripts refreshed'
    } else {
      availableSMUScripts.value = []
      status.value = 'No scripts found'
    }
  } catch (error) {
    console.error('Error loading scripts:', error)
    availableSMUScripts.value = []
    status.value = `Error loading SMU scripts: ${error.message}`
  }
}


// 載入選定的 SMU 腳本
const loadSMUScript = async (name) => {
  try {
    selectedScript.value = name
    const scripts = await loadSMUScripts()
    const script = scripts[name]
    
    if (script) {
      scriptName.value = script.name
      vdsList.value = [...script.vds_list]
      vgList.value = [...script.vg_list]
      status.value = `Loaded SMU script: ${name}`
    }
  } catch (error) {
    status.value = `Error loading SMU script: ${error.message}`
  }
}

// STS 測量功能
const startSingleSTS = async () => {
  if (isRunning.value) return
  
  try {
    isRunning.value = true
    status.value = 'Starting STS measurement...'
    await startSTS()
    status.value = 'STS measurement completed'
  } catch (error) {
    status.value = `Error during STS measurement: ${error.message}`
  } finally {
    isRunning.value = false
  }
}

const startMultiSTS = async () => {
  if (isRunning.value || !selectedScript.value) return
  
  try {
    isRunning.value = true
    status.value = 'Starting Multi-STS with SMU script...'
    await startMultiSTSMeasurement(selectedScript.value)
    status.value = 'Multi-STS measurement completed'
  } catch (error) {
    status.value = `Error during Multi-STS measurement: ${error.message}`
  } finally {
    isRunning.value = false
  }
}

// 在組件掛載時載入腳本
onMounted(async () => {
  console.log('Component mounted, refreshing scripts...')
  await refreshSMUScripts()
})
</script>