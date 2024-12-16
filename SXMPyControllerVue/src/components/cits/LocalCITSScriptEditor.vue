<template>
    <div class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-xl font-semibold text-gray-900 mb-6">Local CITS Area Script</h2>
  
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
                v-for="(script, key) in availableScripts"
                :key="key"
                :value="key"
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
  
      <!-- 腳本名稱和描述 -->
      <div class="space-y-4 mb-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Script Name
          </label>
          <input
            type="text"
            v-model="scriptName"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Enter script name"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Description
          </label>
          <textarea
            v-model="description"
            rows="2"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Optional description"
          ></textarea>
        </div>
      </div>
  
      <!-- 儲存按鈕 -->
      <div class="flex justify-end">
        <button
          @click="handleSaveScript"
          class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
        >
          Save Script
        </button>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, watch } from 'vue';
  import { useLocalCITSAreas } from '../../composables/useLocalCITSAreas';
  
  const props = defineProps({
    areas: {
      type: Array,
      required: true
    }
  });
  
  const emit = defineEmits(['update-areas']);
  
  // Composable
  const { 
    selectedAreaScript,
    areaScriptSettings,
    saveAreaScript,
    loadAreaScripts,
    updateSelectedScript
  } = useLocalCITSAreas();
  
  // Local state
  const selectedScript = ref(selectedAreaScript.value || '');
  const availableScripts = ref({});
  const scriptName = ref('');
  const description = ref('');
  
  // Initialize
  onMounted(async () => {
    await handleRefreshScripts();
    if (areaScriptSettings.value && selectedAreaScript.value) {
      selectedScript.value = selectedAreaScript.value;
      handleScriptSelect();
    }
  });
  
  // Handle script selection
  const handleScriptSelect = () => {
    const script = availableScripts.value[selectedScript.value];
    if (script) {
      updateSelectedScript(script.name, script);
      scriptName.value = script.name;
      description.value = script.description || '';
      
      // 更新區域設定
      if (script.areas && Array.isArray(script.areas)) {
        emit('update-areas', [...script.areas]); // 使用展開運算子建立新陣列
      }
    }
  };
  
  // Load available scripts
  const handleRefreshScripts = async () => {
    try {
      const scripts = await loadAreaScripts();
      availableScripts.value = scripts;
      
      if (areaScriptSettings.value && selectedAreaScript.value) {
        const script = scripts[selectedAreaScript.value];
        if (script) {
          selectedScript.value = script.name;
          handleScriptSelect();
        }
      }
    } catch (error) {
      console.error('Script refresh error:', error);
    }
  };
  
  // Save script
  const handleSaveScript = async () => {
    if (!scriptName.value.trim()) {
      alert('Please provide a script name');
      return;
    }
  
    try {
      const scriptData = {
        name: scriptName.value,
        areas: props.areas,
        description: description.value
      };
  
      await saveAreaScript(scriptData);
      await handleRefreshScripts();
      alert('Script saved successfully');
    } catch (error) {
      console.error('Save script error:', error);
      alert('Failed to save script: ' + error.message);
    }
  };
  
  // Watch for shared state changes
  watch(selectedAreaScript, (newValue) => {
    if (newValue !== selectedScript.value) {
      selectedScript.value = newValue;
      handleScriptSelect();
    }
  });
  </script>