// composables/useSMU.js
import { ref, reactive } from 'vue'

// 建立全域狀態儲存
const globalState = {
  isConnected: false,
  visaAddress: 'TCPIP0::172.30.32.98::inst0::INSTR',
  channelStates: {
    1: { outputOn: false, mode: 'VOLTAGE', value: 0 },
    2: { outputOn: false, mode: 'VOLTAGE', value: 0 }
  }
}

export function useSMU() {
  const isConnected = ref(globalState.isConnected)
  const visaAddress = ref(globalState.visaAddress)
  const channelStates = reactive(globalState.channelStates)

  const connect = async (address) => {
    try {
      const success = await window.pywebview.api.connect_smu(address)
      if (success) {
        isConnected.value = true
        globalState.isConnected = true
        visaAddress.value = address
      }
      return success
    } catch (error) {
      console.error('Connection error:', error)
      throw error
    }
  }

  const disconnect = async () => {
    try {
      const success = await window.pywebview.api.disconnect_smu()
      if (success) {
        isConnected.value = false
        globalState.isConnected = false
        channelStates[1].outputOn = false
        channelStates[2].outputOn = false
      }
      return success
    } catch (error) {
      console.error('Disconnect error:', error)
      throw error
    }
  }

  const setChannelValue = async (channel, mode, value) => {
    try {
      const success = await window.pywebview.api.set_channel_value(channel, mode, value)
      if (success) {
        channelStates[channel].mode = mode
        channelStates[channel].value = value
      }
      return success
    } catch (error) {
      console.error('Set value error:', error)
      throw error
    }
  }

  const toggleOutput = async (channel) => {
    try {
      const newState = !channelStates[channel].outputOn
      const success = await window.pywebview.api.set_channel_output(channel, newState)
      if (success) {
        channelStates[channel].outputOn = newState
      }
      return success
    } catch (error) {
      console.error('Toggle output error:', error)
      throw error
    }
  }

  const readValues = async (channel) => {
    try {
      const result = await window.pywebview.api.read_channel(channel)
      if (result) {
        channelStates[channel].lastReading = {
          voltage: result.voltage,
          current: result.current,
          lastRead: new Date().toLocaleString()
        }
      }
      return result
    } catch (error) {
      console.error('Read values error:', error)
      throw error
    }
  }

  return {
    isConnected,
    visaAddress,
    channelStates,
    connect,
    disconnect,
    setChannelValue,
    toggleOutput,
    readValues
  }
}