<template>
  <div class="bg-white p-6 rounded-lg shadow">
    <h2 class="text-xl font-semibold text-gray-900 mb-6">Local CITS Control</h2>

    <div class="space-y-6">
      <!-- 全域掃描方向設定 -->
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">
          Global Direction
        </label>
        <div class="flex space-x-4">
          <label class="inline-flex items-center">
            <input
              type="radio"
              :value="1"
              :checked="globalDirection === 1"
              @change="$emit('update:global-direction', 1)"
              class="form-radio h-4 w-4 text-indigo-600"
            />
            <span class="ml-2 text-gray-700">Up</span>
          </label>
          <label class="inline-flex items-center">
            <input
              type="radio"
              :value="-1"
              :checked="globalDirection === -1"
              @change="$emit('update:global-direction', -1)"
              class="form-radio h-4 w-4 text-indigo-600"
            />
            <span class="ml-2 text-gray-700">Down</span>
          </label>
        </div>
      </div>

      <!-- SMU腳本資訊顯示 -->
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">
          Selected SMU Script
        </label>
        <div class="p-4 bg-gray-50 rounded-md border border-gray-200">
          <p class="text-sm text-gray-600">
            {{ selectedScript ? selectedScript : 'No script selected' }}
          </p>
          <p v-if="!selectedScript" class="text-xs text-amber-600 mt-2">
            Note: Multi-STS CITS requires a script selected in STS Measurement page
          </p>
        </div>
      </div>

      <!-- 局部區域列表 -->
      <div class="space-y-4">
        <div
          v-for="(area, index) in localAreas"
          :key="index"
          class="bg-gray-50 p-4 rounded-lg border border-gray-200"
        >
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-medium text-gray-900">
              Area {{ index + 1 }}
            </h3>
            <button
              @click="$emit('remove-area', index)"
              class="text-red-600 hover:text-red-800"
              :disabled="localAreas.length === 1"
            >
              Remove
            </button>
          </div>

          <!-- 位置設定 -->
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div class="space-y-1">
              <label class="block text-sm font-medium text-gray-700">
                Start X (nm)
              </label>
              <input
                type="number"
                v-model.number="area.start_x"
                step="0.1"
                class="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div class="space-y-1">
              <label class="block text-sm font-medium text-gray-700">
                Start Y (nm)
              </label>
              <input
                type="number"
                v-model.number="area.start_y"
                step="0.1"
                class="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>

          <!-- 步進和點數設定 -->
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div class="space-y-1">
              <label class="block text-sm font-medium text-gray-700">
                Step Size X (nm)
              </label>
              <input
                type="number"
                v-model.number="area.dx"
                step="0.1"
                min="0.1"
                class="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div class="space-y-1">
              <label class="block text-sm font-medium text-gray-700">
                Step Size Y (nm)
              </label>
              <input
                type="number"
                v-model.number="area.dy"
                step="0.1"
                min="0.1"
                class="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4 mb-4">
            <div class="space-y-1">
              <label class="block text-sm font-medium text-gray-700">
                Points X (1-512)
              </label>
              <input
                type="number"
                v-model.number="area.nx"
                min="1"
                max="512"
                class="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div class="space-y-1">
              <label class="block text-sm font-medium text-gray-700">
                Points Y (1-512)
              </label>
              <input
                type="number"
                v-model.number="area.ny"
                min="1"
                max="512"
                class="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>

          <!-- 起始點方向 -->
          <div class="space-y-1">
            <label class="block text-sm font-medium text-gray-700">
              Start Point Direction
            </label>
            <select
              v-model.number="area.startpoint_direction"
              class="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option :value="1">Up</option>
              <option :value="-1">Down</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 控制按鈕 -->
      <div class="space-y-4">
        <button
          @click="$emit('add-area')"
          class="w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          Add Local Area
        </button>

        <button
          @click="$emit('preview-local-cits')"
          class="w-full px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
        >
          Preview Local CITS
        </button>

        <div class="grid grid-cols-2 gap-4">
          <button
            @click="$emit('start-local-single-cits')"
            :disabled="isRunning"
            class="px-4 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            Start Local Single-STS CITS
          </button>

          <button
            @click="$emit('start-local-multi-cits')"
            :disabled="isRunning || !selectedScript"
            class="px-4 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            Start Local Multi-STS CITS
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useSharedSTSState } from '../../composables/useSharedSTSState'

// 使用共享的 STS 狀態
const { selectedScript } = useSharedSTSState()

defineProps({
  globalDirection: {
    type: Number,
    required: true,
    validator: value => value === 1 || value === -1
  },
  localAreas: {
    type: Array,
    required: true
  },
  isRunning: {
    type: Boolean,
    default: false
  }
})

defineEmits([
  'update:global-direction',
  'update:local-areas',
  'add-area',
  'remove-area',
  'preview-local-cits',
  'start-local-single-cits',
  'start-local-multi-cits'
])
</script>