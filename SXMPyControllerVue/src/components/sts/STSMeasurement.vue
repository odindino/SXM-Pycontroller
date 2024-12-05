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
  
  // 分離 SMU 腳本控制和 STS 測量的邏輯
  const {
    loadScripts: loadSMUScripts,
    saveScript: saveSMUScriptToAPI
  } = useSMUScripts()
  
  const {
    startSTS,
    startMultiSTS: startMultiSTSMeasurement
  } = useSTS()
  
  // 狀態管理
  const scriptName = ref('')
  const vdsList = ref([])
  const vgList = ref([])
  const selectedScript = ref('')
  const availableSMUScripts = ref([])  // 改名以更明確表示這是 SMU 腳本
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
    try {
      status.value = 'Saving SMU script...'
      await saveSMUScriptToAPI(scriptName.value, vdsList.value, vgList.value)
      status.value = 'SMU script saved successfully'
      await refreshSMUScripts()
    } catch (error) {
      status.value = `Error saving SMU script: ${error.message}`
    }
  }
  
  // 載入 SMU 腳本列表
  const refreshSMUScripts = async () => {
    try {
      const scripts = await loadSMUScripts()
      availableSMUScripts.value = scripts
      status.value = 'SMU scripts refreshed'
    } catch (error) {
      status.value = `Error loading SMU scripts: ${error.message}`
    }
  }
  
  // 載入選定的 SMU 腳本
  const loadSMUScript = async (name) => {
    try {
      selectedScript.value = name
      const script = availableSMUScripts.value.find(s => s.name === name)
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
  
  // 組件掛載時載入 SMU 腳本列表
  onMounted(() => {
    refreshSMUScripts()
  })
  </script>