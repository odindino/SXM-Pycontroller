import { ref, watchEffect } from "vue";

// 使用 ref 來存儲狀態，確保響應式
const selectedMoveScript = ref("");
const moveScriptSettings = ref({
  name: "",
  script: "",
  distance: 200,
  waitTime: 1.0,
  repeatCount: 1,
});

// 監聽狀態變化
watchEffect(() => {
  if (selectedMoveScript.value || moveScriptSettings.value) {
    console.log("Auto move settings updated:", {
      script: selectedMoveScript.value,
      settings: moveScriptSettings.value,
    });
  }
});

export function useSharedAutoMoveState() {
  const updateSelectedScript = (scriptName, settings) => {
    selectedMoveScript.value = scriptName;
    if (settings) {
      moveScriptSettings.value = {
        name: scriptName,
        script: settings.script,
        distance: settings.distance,
        waitTime: settings.waitTime,
        repeatCount: settings.repeatCount,
      };
    }
  };

  const clearMoveScriptState = () => {
    selectedMoveScript.value = "";
    moveScriptSettings.value = {
      name: "",
      script: "",
      distance: 200,
      waitTime: 1.0,
      repeatCount: 1,
    };
  };

  return {
    selectedMoveScript,
    moveScriptSettings,
    updateSelectedScript,
    clearMoveScriptState,
  };
}
