<template>
  <div class="bg-white p-6 rounded-lg shadow">
    <h2 class="text-xl font-semibold text-gray-900 mb-6">
      Movement Script Settings
    </h2>

    <div class="space-y-6">
      <!-- 腳本名稱與儲存按鈕 -->
      <div class="flex space-x-4 items-end">
        <div class="flex-1">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Script Name
          </label>
          <input
            type="text"
            :value="scriptName"
            @input="$emit('update:script-name', $event.target.value)"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Enter script name"
          />
        </div>

        <button
          @click="$emit('save-script')"
          class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
        >
          Save Script
        </button>
      </div>

      <!-- 腳本選擇 -->
      <div class="flex space-x-4">
        <select
          :value="selectedScript"
          @change="handleScriptSelect($event.target.value)"
          class="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="">Select Script...</option>
          <option
            v-for="script in scriptsList"
            :key="script.name"
            :value="script.name"
          >
            {{ script.name }}
          </option>
        </select>

        <button
          @click="$emit('refresh-scripts')"
          class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
        >
          Update Scripts
        </button>
      </div>

      <!-- 移動參數設定 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">
            Movement Script (R: Right, U: Up, L: Left, D: Down)
          </label>
          <input
            type="text"
            :value="movementScript"
            @input="$emit('update:movement-script', $event.target.value)"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="e.g., RULD"
          />
        </div>

        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">
            Distance (nm)
          </label>
          <input
            type="number"
            :value="distance"
            @input="$emit('update:distance', parseFloat($event.target.value))"
            step="0.1"
            min="0"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">
            Wait Time (s)
          </label>
          <input
            type="number"
            :value="waitTime"
            @input="$emit('update:wait-time', parseFloat($event.target.value))"
            step="0.1"
            min="0"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">
            Repeat Count
          </label>
          <input
            type="number"
            :value="repeatCount"
            @input="$emit('update:repeat-count', parseInt($event.target.value))"
            min="1"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";

const props = defineProps({
  scriptName: {
    type: String,
    required: true,
  },
  selectedScript: {
    type: String,
    required: "",
  },
  availableScripts: {
    type: [Array, Object],
    required: true,
    default: () => [],
  },
  movementScript: {
    type: String,
    required: true,
  },
  distance: {
    type: Number,
    required: true,
  },
  waitTime: {
    type: Number,
    required: true,
  },
  repeatCount: {
    type: Number,
    required: true,
  },
});

const emit = defineEmits([
  "update:script-name",
  "update:movement-script",
  "update:distance",
  "update:wait-time",
  "update:repeat-count",
  "save-script",
  "select-script",
  "refresh-scripts",
]);

// 將 availableScripts 轉換為陣列形式
const scriptsList = computed(() => {
  if (Array.isArray(props.availableScripts)) {
    return props.availableScripts;
  }
  return Object.values(props.availableScripts);
});

const handleScriptSelect = (scriptName) => {
  if (!scriptName) return;

  const script = scriptsList.value.find((s) => s.name === scriptName);
  if (script) {
    // 更新所有欄位
    emit("update:script-name", script.name);
    emit("update:movement-script", script.script);
    emit("update:distance", parseFloat(script.distance));
    emit("update:wait-time", parseFloat(script.waitTime));
    emit("update:repeat-count", parseInt(script.repeatCount));

    // 通知父組件腳本已選擇
    emit("select-script", script);
  }
};

// 監聽腳本列表變化
watch(
  () => props.availableScripts,
  (newScripts) => {
    if (props.selectedScript) {
      const scripts = Array.isArray(newScripts)
        ? newScripts
        : Object.values(newScripts);
      const script = scripts.find((s) => s.name === props.selectedScript);
      if (script) {
        handleScriptSelect(script.name);
      }
    }
  },
  { deep: true }
);

// 組件掛載時初始化
onMounted(() => {
  if (props.selectedScript) {
    handleScriptSelect(props.selectedScript);
  }
});
</script>
