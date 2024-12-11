<template>
  <div class="space-y-8">
    <!-- SMU腳本編輯區域 -->
    <SMUScriptEditor
      v-model:script-name="scriptName"
      :vds-list="vdsList"
      :vg-list="vgList"
      @update:script-name="updateScriptName"
      @add-row="addSettingRow"
      @remove-row="removeSettingRow"
      @save-script="saveSMUScript"
      @script-selected="handleScriptSelect"
    />

    <!-- STS控制面板 -->
    <STSControlPanel
      :is-running="isRunning"
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
import { ref } from 'vue'
import SMUScriptEditor from './SMUScriptEditor.vue'
import STSControlPanel from './STSControlPanel.vue'
import STSStatusDisplay from './STSStatusDisplay.vue'
import { useSMUScripts } from '../../composables/useSMUScripts'
import { useSTS } from '../../composables/useSTS'

// 基本狀態管理
const scriptName = ref('')
const vdsList = ref([0])
const vgList = ref([0])
const isRunning = ref(false)
const status = ref('Ready')
const lastMeasurement = ref(null)

// 使用 composables
const { saveScript: saveSMUScriptToAPI } = useSMUScripts()
const { startSTS, startMultiSTS: startMultiSTSMeasurement } = useSTS()

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

// 處理腳本選擇
const handleScriptSelect = (script) => {
  scriptName.value = script.name
  vdsList.value = [...script.vds_list]
  vgList.value = [...script.vg_list]
  status.value = `Loaded script: ${script.name}`
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
  } catch (error) {
    status.value = `Error saving SMU script: ${error.message}`
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
    lastMeasurement.value = {
      type: 'Single STS',
      timestamp: new Date().toISOString(),
      script: null
    }
  } catch (error) {
    status.value = `Error during STS measurement: ${error.message}`
  } finally {
    isRunning.value = false
  }
}

const startMultiSTS = async () => {
  if (isRunning.value || !scriptName.value) return
  
  try {
    isRunning.value = true
    status.value = 'Starting Multi-STS measurement...'
    await startMultiSTSMeasurement(scriptName.value)
    status.value = 'Multi-STS measurement completed'
    lastMeasurement.value = {
      type: 'Multi-STS',
      timestamp: new Date().toISOString(),
      script: scriptName.value
    }
  } catch (error) {
    status.value = `Error during Multi-STS measurement: ${error.message}`
  } finally {
    isRunning.value = false
  }
}
</script>