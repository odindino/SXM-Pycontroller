<template>
    <div class="space-y-8">
      <ConnectionPanel
        :visa-address="visaAddress"
        :is-connected="isConnected"
        @connect="handleConnect"
        @disconnect="handleDisconnect"
        @update:visa-address="updateVisaAddress"
      />
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <ChannelPanel
            v-for="channel in [1, 2]"
            :key="channel"
            :channel="channel"
            :state="channelStates[channel]"
            @set-value="handleSetValue"
            @toggle-output="handleToggleOutput"
            @read-values="handleReadValues"
            @set-compliance="handleSetCompliance"
        />
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, reactive } from 'vue'
  import ConnectionPanel from './ConnectionPanel.vue'
  import ChannelPanel from './ChannelPanel.vue'
  import { useSMU } from '../../composables/useSMU'
  
  const {
    isConnected,
    connect,
    disconnect,
    setChannelValue,
    toggleOutput,
    readValues
  } = useSMU()
  
  const visaAddress = ref('TCPIP0::172.30.32.98::inst0::INSTR')
  const channelStates = reactive({
    1: { outputOn: false, mode: 'VOLTAGE', value: 0 },
    2: { outputOn: false, mode: 'VOLTAGE', value: 0 }
  })
  
  const handleConnect = async () => {
    await connect(visaAddress.value)
  }
  
  const handleDisconnect = async () => {
    await disconnect()
  }
  
  const updateVisaAddress = (value) => {
    visaAddress.value = value
  }
  
  const handleSetValue = async (channel, mode, value) => {
    await setChannelValue(channel, mode, value)
  }

  const handleSetCompliance = async (channel, value) => {
    try {
        await window.pywebview.api.set_compliance(channel, value)
    } catch (error) {
        console.error('Set compliance error:', error)
    }
 }
  
  const handleToggleOutput = async (channel) => {
    await toggleOutput(channel)
  }
  
  const handleReadValues = async (channel) => {
    await readValues(channel)
  }
  </script>