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
      :available-smu-scripts="scriptsList"
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
import { ref, onMounted, computed } from 'vue'
import SMUScriptEditor from './SMUScriptEditor.vue'
import STSControlPanel from './STSControlPanel.vue'
import STSStatusDisplay from './STSStatusDisplay.vue'
import { useSMUScripts } from '../../composables/useSMUScripts'
import { useSTS } from '../../composables/useSTS'


const {
  scripts,
  loadScripts: loadSMUScripts,
  saveScript: saveSMUScriptToAPI
} = useSMUScripts()

// // 改用 computed 屬性
// const availableSMUScripts = computed(() => {

//   // 顯示scripts.value的內容
//   console.log('scripts.value:', scripts.value)

//   const scriptData = scripts.value
//   if (!scriptData || Object.keys(scriptData).length === 0) return []
  
//   return Object.entries(scriptData).map(([name, data]) => ({
//     name,
//     vds_list: Array.isArray(data.vds_list) ? data.vds_list : [],
//     vg_list: Array.isArray(data.vg_list) ? data.vg_list : []
//   }))
// })

const availableSMUScripts = computed(() => {

  console.log("raw scripts:", scripts.value)
  const scriptData = scripts.value
  if (!scriptData) return []
  
  // 將物件轉換為陣列格式
  return Object.keys(scriptData).map(key => ({
    name: scriptData[key].name,
    vds_list: scriptData[key].vds_list,
    vg_list: scriptData[key].vg_list
  }))
})


console.log('availableSMUScripts:', availableSMUScripts.value)


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

const scriptsList = ref([])

// const refreshSMUScripts = async () => {
//   try {
//     status.value = 'Refreshing SMU scripts...'
//     const scripts = await loadSMUScripts()
//     console.log('Scripts refreshed:', scripts)
//     status.value = 'SMU scripts refreshed'
//     return scripts
//   } catch (error) {
//     console.error('Error loading scripts:', error)
//     status.value = `Error loading SMU scripts: ${error.message}`
//   }
// }
const refreshSMUScripts = async () => {
  try {
    status.value = 'Refreshing SMU scripts...'
    const response = await loadSMUScripts()
    
    // 將物件轉換為陣列格式並儲存
    scriptsList.value = Object.entries(response).map(([_, script]) => ({
      name: script.name,
      vds_list: script.vds_list,
      vg_list: script.vg_list
    }))
    
    console.log('Scripts refreshed:', scriptsList.value)
    status.value = 'SMU scripts refreshed'
  } catch (error) {
    console.error('Error loading scripts:', error)
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