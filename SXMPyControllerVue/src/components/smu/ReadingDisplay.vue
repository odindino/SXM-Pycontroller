<template>
    <div class="bg-gray-50 p-4 rounded-md space-y-2">
      <div class="font-mono">
        Voltage: {{ reading.voltage?.toFixed(6) ?? '0.000000' }} V
      </div>
      <div class="font-mono">
        Current: {{ (reading.current * 1e6)?.toFixed(6) ?? '0.000000' }} μA
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
  </script>