<template>
  <div class="min-h-screen bg-gray-100">
    <Navigation :active-tab="activeTab" @change-tab="handleTabChange" />
    
    <main class="container mx-auto px-4 py-8 mt-16"> <!-- 添加 mt-16 -->
      <component
        :is="currentComponent"
        v-if="currentComponent"
      />
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import Navigation from './components/Navigation.vue'
import SMUConfig from './components/smu/SMUConfig.vue'
import STSMeasurement from './components/sts/STSMeasurement.vue'
import CITSMeasurement from './components/cits/CITSMeasurement.vue'
import AutoMoveMeasurement from './components/auto-move/AutoMoveMeasurement.vue'

const activeTab = ref('smu-config')

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

const handleTabChange = (tab) => {
  activeTab.value = tab
}
</script>

<style>
.container {
  max-width: 1400px;
}
</style>