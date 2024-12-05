<template>
  <div class="min-h-screen bg-gray-100">
    <Navigation :active-tab="activeTab" @change-tab="handleTabChange" />
    
    <main class="container mx-auto px-4 py-8">
      <SMUConfig v-if="activeTab === 'smu-config'" />
      <div v-else-if="activeTab === 'sts-measurement'">STS Measurement</div>
      <div v-else-if="activeTab === 'cits-measurement'">CITS Measurement</div>
      <div v-else-if="activeTab === 'auto-move-measurement'">Auto Move Measurement</div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Navigation from './components/Navigation.vue'
import SMUConfig from './components/smu/SMUConfig.vue'

const activeTab = ref('smu-config')

const handleTabChange = (tab) => {
  activeTab.value = tab
}
</script>