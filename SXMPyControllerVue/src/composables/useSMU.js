import { ref, reactive } from 'vue'

export function useSMU() {
  const isConnected = ref(false)
  const channelStates = reactive({
    1: { outputOn: false, mode: 'VOLTAGE', value: 0 },
    2: { outputOn: false, mode: 'VOLTAGE', value: 0 }
  })
  
  const connect = async (address) => {
    try {
      const success = await window.pywebview.api.connect_smu(address)
      if (success) {
        isConnected.value = true
        // 確保兩個通道都是關閉狀態
        channelStates[1].outputOn = false
        channelStates[2].outputOn = false
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
      const currentState = channelStates[channel].outputOn
      const newState = !currentState
      const success = await window.pywebview.api.set_channel_output(channel, newState)
      
      if (success) {
        // 使用響應式更新
        channelStates[channel] = {
          ...channelStates[channel],
          outputOn: newState
        }
        console.log(`Channel ${channel} output state updated to: ${newState}`)
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
        // 更新通道狀態
        channelStates[channel] = {
          ...channelStates[channel],
          lastReading: {
            voltage: result.voltage,
            current: result.current,
            lastRead: new Date().toLocaleString()
          }
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
    connect,
    disconnect,
    setChannelValue,
    toggleOutput,
    readValues
  }
}