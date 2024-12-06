export const formatDateTime = (timestamp) => {
    if (!timestamp) return 'N/A'
    return new Date(timestamp).toLocaleString()
  }
  
  export const formatDuration = (milliseconds) => {
    if (!milliseconds) return 'N/A'
    
    const seconds = Math.floor(milliseconds / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    
    const parts = []
    if (hours > 0) parts.push(`${hours}h`)
    if (minutes % 60 > 0) parts.push(`${minutes % 60}m`)
    if (seconds % 60 > 0) parts.push(`${seconds % 60}s`)
    
    return parts.join(' ') || '0s'
  }
  
  export const validateNumber = (value, min, max) => {
    const num = Number(value)
    if (isNaN(num)) return false
    if (min !== undefined && num < min) return false
    if (max !== undefined && num > max) return false
    return true
  }