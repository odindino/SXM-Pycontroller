import { ref } from 'vue'

export function useSMU() {
  const isConnected = ref(false)
  
  const connect = async (address) => {
    try {
      const success = await window.pywebview.api.connect_smu(address)
      isConnected.value = success
      return success
    } catch (error) {
      console.error('Connection error:', error)
      throw error
    }
  }
  
  const disconnect = async () => {
    try {
      const success = await window.pywebview.api.disconnect_smu()
      isConnected.value = false
      return success
    } catch (error) {
      console.error('Disconnect error:', error)
      throw error
    }
  }
  
  const setChannelValue = async (channel, mode, value) => {
    try {
      return await window.pywebview.api.set_channel_value(channel, mode, value)
    } catch (error) {
      console.error('Set value error:', error)
      throw error
    }
  }
  
  const toggleOutput = async (channel) => {
    try {
      return await window.pywebview.api.set_channel_output(channel, !channelStates[channel].outputOn)
    } catch (error) {
      console.error('Toggle output error:', error)
      throw error
    }
  }
  
  const readValues = async (channel) => {
    try {
      return await window.pywebview.api.read_channel(channel)
    } catch (error) {
      console.error('Read values error:', error)
      throw error
    }
  }

  return {
    isConnected,
    connect,
    disconnect,
    setChannelValue,
    toggleOutput,
    readValues
  }
}