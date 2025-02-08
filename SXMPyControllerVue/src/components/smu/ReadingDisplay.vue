<template>
  <div class="bg-gray-50 p-4 rounded-md space-y-2">
    <div class="font-mono">
      Voltage: {{ formatNumber(reading.voltage, 6) }} V
    </div>
    <div class="font-mono">
      Current: {{ formatCurrent(reading.current) }} μA
    </div>
    <div class="text-sm text-gray-500">
      Last Read: {{ reading.lastRead ?? 'Never' }}
    </div>
  </div>
</template>

<script setup>
defineProps({
  channel: { type: Number, required: true },
  reading: { type: Object, required: true }
})

// 格式化數字的函數
const formatNumber = (value, decimals = 6) => {
  if (value === null || value === undefined) return '0.000000'
  return Number(value).toFixed(decimals)
}

// 格式化電流值（轉換為 μA）
const formatCurrent = (value) => {
  if (value === null || value === undefined) return '0.000000'
  return (value * 1e6).toFixed(6)
}
</script>