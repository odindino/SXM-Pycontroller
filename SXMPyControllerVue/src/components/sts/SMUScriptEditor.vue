<template>
  <div class="bg-white p-6 rounded-lg shadow">
    <h2 class="text-xl font-semibold text-gray-900 mb-6">SMU Voltage Settings</h2>

    <!-- 腳本選擇和更新區域 -->
    <div class="mb-6">
      <div class="flex space-x-4 items-end">
        <div class="flex-1">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Load Existing Script
          </label>
          <select
            v-model="selectedScript"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            @change="handleScriptSelect"
          >
            <option value="">Select Script...</option>
            <option
              v-for="script in availableScripts"
              :key="script.name"
              :value="script.name"
            >
              {{ script.name }}
            </option>
          </select>
        </div>

        <button
          @click="handleRefreshScripts"
          class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
        >
          Update Scripts
        </button>
      </div>
    </div>

    <!-- 腳本名稱輸入 -->
    <div class="mb-6">
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

    <!-- 電壓設定表格 -->
    <div class="mb-6">
      <div class="bg-gray-50 px-4 py-3 border-b border-gray-200 grid grid-cols-12 gap-4">
        <div class="col-span-5 font-medium text-gray-700">Vds (V)</div>
        <div class="col-span-5 font-medium text-gray-700">Vg (V)</div>
        <div class="col-span-2"></div>
      </div>

      <div class="space-y-2">
        <div
          v-for="(_, index) in vdsList"
          :key="index"
          class="grid grid-cols-12 gap-4 px-4 py-2 items-center"
        >
          <div class="col-span-5">
            <input
              type="number"
              v-model.number="vdsList[index]"
              step="0.1"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div class="col-span-5">
            <input
              type="number"
              v-model.number="vgList[index]"
              step="0.1"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div class="col-span-2">
            <button
              @click="$emit('remove-row', index)"
              class="w-8 h-8 flex items-center justify-center text-red-600 hover:text-red-800 focus:outline-none"
              title="Remove row"
            >
              <span class="text-xl">×</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按鈕 -->
    <div class="flex justify-between">
      <button
        @click="$emit('add-row')"
        class="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
      >
        Add Setting
      </button>

      <button
        @click="$emit('save-script')"
        class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
      >
        Save Script
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useSMUScripts } from '../../composables/useSMUScripts'
import { useSharedSTSState } from '../../composables/useSharedSTSState'

// Props 定義
const props = defineProps({
  scriptName: {
    type: String,
    required: true
  },
  vdsList: {
    type: Array,
    required: true
  },
  vgList: {
    type: Array,
    required: true
  }
})

// Emits 定義
const emit = defineEmits([
  'update:script-name',
  'add-row',
  'remove-row',
  'save-script',
  'script-selected'
])

// Composables
const { loadScripts } = useSMUScripts()
const { 
  selectedScript: sharedScript, 
  scriptSettings,
  updateSelectedScript 
} = useSharedSTSState()

// 本地狀態
const selectedScript = ref(sharedScript.value || '')
const availableScripts = ref([])

// 初始化時載入腳本
onMounted(async () => {
  await handleRefreshScripts()
  if (scriptSettings.value && sharedScript.value) {
    selectedScript.value = sharedScript.value
  }
})

// 處理腳本選擇
const handleScriptSelect = () => {
  const script = availableScripts.value.find(s => s.name === selectedScript.value)
  if (script) {
    // 更新共享狀態
    updateSelectedScript(script.name, {
      vds_list: script.vds_list,
      vg_list: script.vg_list
    })
    
    // 觸發父組件更新
    emit('script-selected', {
      name: script.name,
      vds_list: script.vds_list,
      vg_list: script.vg_list
    })
    
    // 更新本地輸入框的值
    emit('update:script-name', script.name)
  }
}

// 載入可用腳本
const handleRefreshScripts = async () => {
  try {
    const response = await loadScripts()
    availableScripts.value = Object.entries(response).map(([_, script]) => ({
      name: script.name,
      vds_list: script.vds_list,
      vg_list: script.vg_list
    }))
    
    // 如果有已保存的腳本設定，恢復它
    if (scriptSettings.value && sharedScript.value) {
      const script = availableScripts.value.find(s => s.name === sharedScript.value)
      if (script) {
        selectedScript.value = script.name
        emit('script-selected', {
          name: script.name,
          vds_list: scriptSettings.value.vds_list,
          vg_list: scriptSettings.value.vg_list
        })
      }
    }
  } catch (error) {
    console.error('Script refresh error:', error)
  }
}

// 監聽共享狀態的變化
watch(sharedScript, (newValue) => {
  if (newValue !== selectedScript.value) {
    selectedScript.value = newValue
  }
})

// 監聽本地選擇的變化
watch(selectedScript, (newValue) => {
  if (newValue !== sharedScript.value) {
    handleScriptSelect()
  }
})

// 監聽外部腳本名稱變化
watch(() => props.scriptName, (newName) => {
  if (newName !== selectedScript.value) {
    selectedScript.value = newName
  }
})
</script>