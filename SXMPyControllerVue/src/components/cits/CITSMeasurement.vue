<template>
    <div class="space-y-8">
      <!-- 標準 CITS 控制 -->
      <StandardCITSPanel
        v-model:points-x="pointsX"
        v-model:points-y="pointsY"
        v-model:scan-direction="scanDirection"
        :available-smu-scripts="availableSMUScripts"
        :selected-script="selectedScript"
        :is-running="isRunning"
        @select-script="handleScriptSelect"
        @refresh-scripts="refreshSMUScripts"
        @start-single-cits="startSingleCITS"
        @start-multi-cits="startMultiCITS"
      />
  
      <!-- 局部 CITS 控制 -->
      <LocalCITSPanel
        v-model:global-direction="globalDirection"
        v-model:local-areas="localAreas"
        :available-smu-scripts="availableSMUScripts"
        :selected-script="selectedScript"
        :is-running="isRunning"
        @add-area="addLocalArea"
        @remove-area="removeLocalArea"
        @preview-local-cits="previewLocalCITS"
        @start-local-single-cits="startLocalSingleCITS"
        @start-local-multi-cits="startLocalMultiCITS"
      />
  
      <!-- 狀態顯示 -->
      <CITSStatusDisplay
        :status="status"
        :preview-data="previewData"
        :last-measurement="lastMeasurement"
      />
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import StandardCITSPanel from './StandardCITSPanel.vue'
  import LocalCITSPanel from './LocalCITSPanel.vue'
  import CITSStatusDisplay from './CITSStatusDisplay.vue'
  import { useSMUScripts } from '../../composables/useSMUScripts'
  import { useCITS } from '../../composables/useCITS'
  
  // 狀態管理
  const pointsX = ref(128)
  const pointsY = ref(128)
  const scanDirection = ref(1) // 1: 向上, -1: 向下
  const globalDirection = ref(1)
  const localAreas = ref([])
  const selectedScript = ref('')
  const availableSMUScripts = ref([])
  const isRunning = ref(false)
  const status = ref('Ready')
  const previewData = ref(null)
  const lastMeasurement = ref(null)
  
  // 使用 composables
  const { loadScripts: loadSMUScripts } = useSMUScripts()
  const {
    startSingleCITS: startSingleCITSMeasurement,
    startMultiCITS: startMultiCITSMeasurement,
    startLocalSingleCITS: startLocalSingleCITSMeasurement,
    startLocalMultiCITS: startLocalMultiCITSMeasurement,
    previewLocalCITS: generateLocalCITSPreview
  } = useCITS()
  
  // SMU腳本相關
  const refreshSMUScripts = async () => {
    try {
      const scripts = await loadSMUScripts()
      availableSMUScripts.value = scripts
      status.value = 'SMU scripts refreshed'
    } catch (error) {
      status.value = `Error loading SMU scripts: ${error.message}`
    }
  }
  
  const handleScriptSelect = (scriptName) => {
    selectedScript.value = scriptName
  }
  
  // CITS操作
  const startSingleCITS = async () => {
    if (isRunning.value) return
    
    try {
      isRunning.value = true
      status.value = 'Starting Single-STS CITS...'
      await startSingleCITSMeasurement(pointsX.value, pointsY.value, scanDirection.value)
      status.value = 'CITS measurement completed'
    } catch (error) {
      status.value = `Error during CITS measurement: ${error.message}`
    } finally {
      isRunning.value = false
    }
  }
  
  const startMultiCITS = async () => {
    if (isRunning.value || !selectedScript.value) return
    
    try {
      isRunning.value = true
      status.value = 'Starting Multi-STS CITS...'
      await startMultiCITSMeasurement(
        pointsX.value,
        pointsY.value,
        selectedScript.value,
        scanDirection.value
      )
      status.value = 'Multi-STS CITS completed'
    } catch (error) {
      status.value = `Error during Multi-STS CITS: ${error.message}`
    } finally {
      isRunning.value = false
    }
  }
  
  // 區域CITS操作
  const addLocalArea = () => {
    localAreas.value.push({
      x_dev: 200,    // 預設偏移
      y_dev: 200,
      dx: 20,        // 預設步進
      dy: 20,
      nx: 5,         // 預設點數
      ny: 3,
      startpoint_direction: 1
    })
  }
  
  const removeLocalArea = (index) => {
    localAreas.value.splice(index, 1)
  }
  
  const previewLocalCITS = async () => {
    try {
      status.value = 'Generating preview...'
      const preview = await generateLocalCITSPreview({
        local_areas: localAreas.value,
        scan_direction: globalDirection.value
      })
      previewData.value = preview
      status.value = 'Preview generated'
    } catch (error) {
      status.value = `Preview error: ${error.message}`
      previewData.value = null
    }
  }
  
  const startLocalSingleCITS = async () => {
    if (isRunning.value) return
    
    try {
      isRunning.value = true
      status.value = 'Starting Local Single-STS CITS...'
      await startLocalSingleCITSMeasurement(
        localAreas.value,
        globalDirection.value
      )
      status.value = 'Local CITS completed'
    } catch (error) {
      status.value = `Error during Local CITS: ${error.message}`
    } finally {
      isRunning.value = false
    }
  }
  
  const startLocalMultiCITS = async () => {
    if (isRunning.value || !selectedScript.value) return
    
    try {
      isRunning.value = true
      status.value = 'Starting Local Multi-STS CITS...'
      await startLocalMultiCITSMeasurement(
        localAreas.value,
        selectedScript.value,
        globalDirection.value
      )
      status.value = 'Local Multi-STS CITS completed'
    } catch (error) {
      status.value = `Error during Local Multi-STS CITS: ${error.message}`
    } finally {
      isRunning.value = false
    }
  }
  
  // 初始化
  onMounted(() => {
    refreshSMUScripts()
    addLocalArea() // 添加一個預設的局部區域
  })
  </script>