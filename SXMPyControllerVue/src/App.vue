<template>
  <div class="min-h-screen bg-gray-100">
    <Navigation :active-tab="activeTab" @change-tab="handleTabChange" />
    
    <AbortButton 
      :is-running="isRunning"
      @measurement-stopped="handleMeasurementStopped" 
    />

    <main class="container mx-auto px-4 py-8 mt-16"> <!-- 添加 mt-16 -->
      <component
        :is="currentComponent"
        v-if="currentComponent"
        @measurement-started="handleMeasurementStarted"
        @measurement-completed="handleMeasurementCompleted"
      />
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Navigation from './components/Navigation.vue'
import AbortButton from './components/AbortButton.vue'
import SMUConfig from './components/smu/SMUConfig.vue'
import STSMeasurement from './components/sts/STSMeasurement.vue'
import CITSMeasurement from './components/cits/CITSMeasurement.vue'
import AutoMoveMeasurement from './components/auto-move/AutoMoveMeasurement.vue'

const activeTab = ref('smu-config')
const isRunning = ref(false)

const currentComponent = computed(() => {
  switch (activeTab.value) {
    case 'smu-config':
      return SMUConfig
    case 'sts-measurement':
      return STSMeasurement
    case 'cits-measurement':
      return CITSMeasurement
    case 'auto-move-measurement':
      return AutoMoveMeasurement
    default:
      return null
  }
})

// 事件處理函數
const handleTabChange = (tab) => {
  activeTab.value = tab
}

const handleMeasurementStarted = () => {
  isRunning.value = true
}

const handleMeasurementCompleted = () => {
  isRunning.value = false
}

const handleMeasurementStopped = () => {
  isRunning.value = false
}
</script>

<style>
.container {
  max-width: 1400px;
}
</style>