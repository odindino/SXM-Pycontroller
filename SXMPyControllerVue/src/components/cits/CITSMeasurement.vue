<template>
  <div class="space-y-8">
    <!-- 標準 CITS 控制 -->
    <StandardCITSPanel
      v-model:points-x="pointsX"
      v-model:points-y="pointsY"
      v-model:scan-direction="scanDirection"
      :is-running="isRunning"
      @start-single-cits="startSingleCITS"
      @start-multi-cits="startMultiCITS"
    />

    <!-- 局部 CITS 控制 -->
    <LocalCITSPanel
      v-model:global-direction="globalDirection"
      v-model:local-areas="localAreas"
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
import { useSharedSTSState } from '../../composables/useSharedSTSState'
import { useCITS } from '../../composables/useCITS'

// 使用共享的 STS 狀態
const { selectedScript } = useSharedSTSState()

// 基本狀態管理
const pointsX = ref(128)
const pointsY = ref(128)
const scanDirection = ref(1)
const globalDirection = ref(1)
const localAreas = ref([])
const isRunning = ref(false)
const status = ref('Ready')
const previewData = ref(null)
const lastMeasurement = ref(null)

// 使用 CITS composable
const {
  startSingleCITS: startSingleCITSMeasurement,
  startMultiCITS: startMultiCITSMeasurement,
  startLocalSingleCITS: startLocalSingleCITSMeasurement,
  startLocalMultiCITS: startLocalMultiCITSMeasurement,
  previewLocalCITS: generateLocalCITSPreview
} = useCITS()

// CITS 操作函數
const startSingleCITS = async () => {
  if (isRunning.value) return
  
  try {
    isRunning.value = true
    status.value = 'Starting Single-STS CITS...'
    await startSingleCITSMeasurement(pointsX.value, pointsY.value, scanDirection.value)
    status.value = 'CITS measurement completed'
    lastMeasurement.value = {
      type: 'Single-STS CITS',
      timestamp: new Date().toISOString(),
      total_points: pointsX.value * pointsY.value,
      duration: null
    }
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
    lastMeasurement.value = {
      type: 'Multi-STS CITS',
      timestamp: new Date().toISOString(),
      total_points: pointsX.value * pointsY.value,
      script: selectedScript.value,
      duration: null
    }
  } catch (error) {
    status.value = `Error during Multi-STS CITS: ${error.message}`
  } finally {
    isRunning.value = false
  }
}

// 局部區域相關函數
const addLocalArea = () => {
  localAreas.value.push({
    start_x: 0,
    start_y: 0,
    dx: 20,
    dy: 20,
    nx: 5,
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
    lastMeasurement.value = {
      type: 'Local Single-STS CITS',
      timestamp: new Date().toISOString(),
      total_points: localAreas.value.reduce((sum, area) => sum + area.nx * area.ny, 0),
      duration: null
    }
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
    lastMeasurement.value = {
      type: 'Local Multi-STS CITS',
      timestamp: new Date().toISOString(),
      total_points: localAreas.value.reduce((sum, area) => sum + area.nx * area.ny, 0),
      script: selectedScript.value,
      duration: null
    }
  } catch (error) {
    status.value = `Error during Local Multi-STS CITS: ${error.message}`
  } finally {
    isRunning.value = false
  }
}

// 初始化
onMounted(() => {
  addLocalArea() // 添加預設的局部區域
})
</script>