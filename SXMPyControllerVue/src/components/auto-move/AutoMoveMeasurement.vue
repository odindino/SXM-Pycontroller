<template>
    <div class="space-y-8">
      <!-- 移動腳本設定 -->
      <MoveScriptPanel
        v-model:script-name="scriptName"
        v-model:movement-script="movementScript"
        v-model:distance="moveDistance"
        v-model:wait-time="waitTime"
        v-model:repeat-count="repeatCount"
        :available-scripts="availableMoveScripts"
        @save-script="saveMoveScript"
        @select-script="loadMoveScript"
        @refresh-scripts="refreshMoveScripts"
      />
  
      <!-- CITS 控制面板 -->
      <AMCITSControlPanel
        v-model:points-x="pointsX"
        v-model:points-y="pointsY"
        v-model:scan-direction="scanDirection"
        :available-smu-scripts="availableSMUScripts"
        :selected-script="selectedSMUScript"
        :is-running="isRunning"
        @select-script="handleSMUScriptSelect"
        @refresh-scripts="refreshSMUScripts"
        @start-auto-move-ssts="startAutoMoveSingleCITS"
        @start-auto-move-msts="startAutoMoveMultiCITS"
      />
  
      <!-- 局部 CITS 設定 -->
      <LocalCITSPanel
        v-model:global-direction="globalDirection"
        v-model:local-areas="localAreas"
        :available-smu-scripts="availableSMUScripts"
        :selected-script="selectedSMUScript"
        :is-running="isRunning"
        @add-area="addLocalArea"
        @remove-area="removeLocalArea"
        @get-status="getLocalCITSStatus"
        @preview-local-cits="previewLocalCITS"
        @start-local-ssts="startAutoMoveLocalSingleCITS"
        @start-local-msts="startAutoMoveLocalMultiCITS"
      />
  
      <!-- 預覽與狀態顯示 -->
      <PreviewStatusPanel
        :status="status"
        :preview-data="previewData"
        :last-measurement="lastMeasurement"
        @get-status="getSXMStatus"
        @preview-auto-move="previewAutoMove"
      />
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import MoveScriptPanel from './MoveScriptPanel.vue'
  import AMCITSControlPanel from './AMCITSControlPanel.vue'
  import LocalCITSPanel from './LocalCITSPanel.vue'
  import PreviewStatusPanel from './PreviewStatusPanel.vue'
  import { useAutoMove } from '../../composables/useAutoMove'
  import { useSMUScripts } from '../../composables/useSMUScripts'
  
  // 狀態管理
  const scriptName = ref('')
  const movementScript = ref('')
  const moveDistance = ref(200)
  const waitTime = ref(1.0)
  const repeatCount = ref(1)
  const pointsX = ref(128)
  const pointsY = ref(128)
  const scanDirection = ref(1)
  const globalDirection = ref(1)
  const localAreas = ref([])
  const selectedSMUScript = ref('')
  const availableMoveScripts = ref([])
  const availableSMUScripts = ref([])
  const isRunning = ref(false)
  const status = ref('Ready')
  const previewData = ref(null)
  const lastMeasurement = ref(null)
  
  // Composables
  const {
    loadMoveScripts: loadAutoMoveScripts,
    saveMoveScript: saveAutoMoveScript,
    previewAutoMove: previewMove
  } = useAutoMove()
  
  const {
    loadScripts: loadSMUScripts,
  } = useSMUScripts()
  
  // 腳本管理
  const refreshMoveScripts = async () => {
    try {
      const scripts = await loadAutoMoveScripts()
      availableMoveScripts.value = scripts
      status.value = 'Movement scripts refreshed'
    } catch (error) {
      status.value = `Error loading movement scripts: ${error.message}`
    }
  }
  
  const refreshSMUScripts = async () => {
    try {
      const scripts = await loadSMUScripts()
      availableSMUScripts.value = scripts
      status.value = 'SMU scripts refreshed'
    } catch (error) {
      status.value = `Error loading SMU scripts: ${error.message}`
    }
  }
  
  const saveMoveScript = async () => {
    try {
      status.value = 'Saving movement script...'
      await saveAutoMoveScript({
        name: scriptName.value,
        script: movementScript.value,
        distance: moveDistance.value,
        waitTime: waitTime.value,
        repeatCount: repeatCount.value
      })
      status.value = 'Movement script saved successfully'
      await refreshMoveScripts()
    } catch (error) {
      status.value = `Error saving script: ${error.message}`
    }
  }
  
  // 預覽功能
  const previewAutoMove = async () => {
    try {
      status.value = 'Generating auto-move preview...'
      const preview = await previewMove({
        movement_script: movementScript.value,
        distance: moveDistance.value,
        center_x: null,  // Will be obtained from current SXM status
        center_y: null,
        angle: null
      })
      previewData.value = preview
      status.value = 'Preview generated successfully'
    } catch (error) {
      status.value = `Preview error: ${error.message}`
    }
  }
  
  // CITS操作
  const startAutoMoveSingleCITS = async () => {
    if (isRunning.value) return
    
    try {
      isRunning.value = true
      status.value = 'Starting Auto-Move Single-STS CITS...'
      await window.pywebview.api.auto_move_ssts_cits(
        movementScript.value,
        moveDistance.value,
        pointsX.value,
        pointsY.value,
        scanDirection.value,
        waitTime.value,
        repeatCount.value
      )
      status.value = 'Auto-Move Single-STS CITS completed'
    } catch (error) {
      status.value = `Error: ${error.message}`
    } finally {
      isRunning.value = false
    }
  }
  
  const startAutoMoveMultiCITS = async () => {
    if (isRunning.value || !selectedSMUScript.value) return
    
    try {
      isRunning.value = true
      status.value = 'Starting Auto-Move Multi-STS CITS...'
      await window.pywebview.api.auto_move_msts_cits(
        movementScript.value,
        moveDistance.value,
        pointsX.value,
        pointsY.value,
        selectedSMUScript.value,
        scanDirection.value,
        waitTime.value,
        repeatCount.value
      )
      status.value = 'Auto-Move Multi-STS CITS completed'
    } catch (error) {
      status.value = `Error: ${error.message}`
    } finally {
      isRunning.value = false
    }
  }

  const addLocalArea = () => {
    // 創建新的區域預設值
    const newArea = {
        x_dev: 200,  // 預設偏移
        y_dev: 200,
        dx: 20,      // 預設步進
        dy: 20,
        nx: 5,       // 預設點數
        ny: 3,
        startpoint_direction: 1
    }
    
    // 將新區域加入到陣列中
    localAreas.value.push(newArea)
 }
  
  // 初始化
  onMounted(() => {
    refreshMoveScripts()
    refreshSMUScripts()
  })
  </script>