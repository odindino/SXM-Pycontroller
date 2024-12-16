import { ref, watchEffect } from 'vue';

// 創建持久化的響應式狀態
const selectedAreaScript = ref(localStorage.getItem('selectedLocalCITSAreaScript') || '');
const areaScriptSettings = ref(null);

try {
  const savedSettings = localStorage.getItem('localCITSAreaSettings');
  if (savedSettings) {
    areaScriptSettings.value = JSON.parse(savedSettings);
  }
} catch (error) {
  console.error('Error parsing stored area settings:', error);
}

// 監聽狀態變化並自動保存
watchEffect(() => {
  if (selectedAreaScript.value) {
    localStorage.setItem('selectedLocalCITSAreaScript', selectedAreaScript.value);
  }
  
  if (areaScriptSettings.value) {
    localStorage.setItem('localCITSAreaSettings', JSON.stringify(areaScriptSettings.value));
  }
});

export function useLocalCITSAreas() {
  const saveAreaScript = async (scriptData) => {
    try {
      // 驗證必要欄位
      if (!scriptData.name || !scriptData.areas || !Array.isArray(scriptData.areas)) {
        throw new Error('Invalid script data format');
      }

      // 使用 API 儲存腳本
      const success = await window.pywebview.api.save_local_cits_area_script(scriptData);
      
      if (success) {
        // 更新本地狀態
        updateSelectedScript(scriptData.name, scriptData);
      }

      return success;
    } catch (error) {
      console.error('Failed to save area script:', error);
      throw error;
    }
  };

  const loadAreaScripts = async () => {
    try {
      // 使用 API 讀取腳本
      return await window.pywebview.api.get_local_cits_area_scripts();
    } catch (error) {
      console.error('Failed to load area scripts:', error);
      return {};
    }
  };

  const updateSelectedScript = (scriptName, settings = null) => {
    selectedAreaScript.value = scriptName;
    if (settings) {
      areaScriptSettings.value = settings;
      localStorage.setItem('localCITSAreaSettings', JSON.stringify(settings));
    }
  };

  const clearScriptState = () => {
    selectedAreaScript.value = '';
    areaScriptSettings.value = null;
    localStorage.removeItem('selectedLocalCITSAreaScript');
    localStorage.removeItem('localCITSAreaSettings');
  };

  return {
    selectedAreaScript,
    areaScriptSettings,
    saveAreaScript,
    loadAreaScripts,
    updateSelectedScript,
    clearScriptState
  };
}