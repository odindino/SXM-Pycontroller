import { ref } from 'vue'

export function useCITS() {
  const isLoading = ref(false)
  const currentOperation = ref(null)

  // 標準 CITS 操作
  const startSingleCITS = async (pointsX, pointsY, scanDirection) => {
    try {
      isLoading.value = true
      currentOperation.value = 'single-cits'
      return await window.pywebview.api.start_ssts_cits(pointsX, pointsY, scanDirection)
    } catch (error) {
      console.error('Single CITS error:', error)
      throw error
    } finally {
      isLoading.value = false
      currentOperation.value = null
    }
  }

  const startMultiCITS = async (pointsX, pointsY, scriptName, scanDirection) => {
    try {
      isLoading.value = true
      currentOperation.value = 'multi-cits'
      return await window.pywebview.api.start_msts_cits(
        pointsX,
        pointsY,
        scriptName,
        scanDirection
      )
    } catch (error) {
      console.error('Multi CITS error:', error)
      throw error
    } finally {
      isLoading.value = false
      currentOperation.value = null
    }
  }

  // 局部 CITS 操作
  const startLocalSingleCITS = async (localAreas, scanDirection) => {
    try {
      isLoading.value = true
      currentOperation.value = 'local-single-cits'
      return await window.pywebview.api.start_local_ssts_cits(
        localAreas,
        scanDirection
      )
    } catch (error) {
      console.error('Local Single CITS error:', error)
      throw error
    } finally {
      isLoading.value = false
      currentOperation.value = null
    }
  }

  const startLocalMultiCITS = async (localAreas, scriptName, scanDirection) => {
    try {
      isLoading.value = true
      currentOperation.value = 'local-multi-cits'
      return await window.pywebview.api.start_local_msts_cits(
        localAreas,
        scriptName,
        scanDirection
      )
    } catch (error) {
      console.error('Local Multi CITS error:', error)
      throw error
    } finally {
      isLoading.value = false
      currentOperation.value = null
    }
  }

  // 預覽功能
  const previewLocalCITS = async (params) => {
    try {
      isLoading.value = true
      currentOperation.value = 'preview'
      return await window.pywebview.api.preview_local_cits(params)
    } catch (error) {
      console.error('Preview generation error:', error)
      throw error
    } finally {
      isLoading.value = false
      currentOperation.value = null
    }
  }

  return {
    isLoading,
    currentOperation,
    startSingleCITS,
    startMultiCITS,
    startLocalSingleCITS,
    startLocalMultiCITS,
    previewLocalCITS
  }
}