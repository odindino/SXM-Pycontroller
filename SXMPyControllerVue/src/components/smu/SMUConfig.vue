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
import ConnectionPanel from './ConnectionPanel.vue'
import ChannelPanel from './ChannelPanel.vue'
import { useSMU } from '../../composables/useSMU'

const {
  isConnected,
  visaAddress,
  channelStates,
  connect,
  disconnect,
  setChannelValue,
  toggleOutput,
  readValues
} = useSMU()

const handleConnect = async () => {
  try {
    await connect(visaAddress.value)
  } catch (error) {
    console.error('Connection error:', error)
  }
}

const handleDisconnect = async () => {
  try {
    await disconnect()
  } catch (error) {
    console.error('Disconnect error:', error)
  }
}

const updateVisaAddress = (value) => {
  visaAddress.value = value
}

const handleSetValue = async (channel, mode, value) => {
  try {
    await setChannelValue(channel, mode, value)
  } catch (error) {
    console.error('Set value error:', error)
  }
}

const handleToggleOutput = async (channel) => {
  try {
    await toggleOutput(channel)
  } catch (error) {
    console.error('Toggle output error:', error)
  }
}

const handleReadValues = async (channel) => {
  try {
    await readValues(channel)
  } catch (error) {
    console.error('Read values error:', error)
  }
}

const handleSetCompliance = async (channel, value) => {
  try {
    await window.pywebview.api.set_compliance(channel, value)
  } catch (error) {
    console.error('Set compliance error:', error)
  }
}
</script>