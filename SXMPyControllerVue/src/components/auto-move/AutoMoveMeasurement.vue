<template>
  <div class="space-y-8">
    <!-- 移動腳本設定 -->
    <MoveScriptPanel
      v-model:script-name="scriptName"
      v-model:movement-script="movementScript"
      v-model:distance="moveDistance"
      v-model:wait-time="waitTime"
      v-model:repeat-count="repeatCount"
      :available-scripts="availableMoveScripts"
      @save-script="saveMoveScript"
      @select-script="handleScriptSelect"
      @refresh-scripts="refreshMoveScripts"
    />

    <!-- 測量控制區域 -->
    <div class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-xl font-semibold text-gray-900 mb-6">
        Measurement Control
      </h2>
      <div class="space-y-4">
        <!-- 掃描區域 -->
        <button
          @click="startAutoMoveScan"
          :disabled="isRunning"
          class="w-full px-4 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Start Auto-Move Scan Area
        </button>

        <!-- 標準 CITS -->
        <div class="grid grid-cols-2 gap-4">
          <button
            @click="startAutoMoveSingleSTS"
            :disabled="isRunning"
            class="px-4 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Auto-Move Single-STS CITS
          </button>

          <button
            @click="startAutoMoveMultiSTS"
            :disabled="isRunning || !selectedSMUScript"
            class="px-4 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Auto-Move Multi-STS CITS
          </button>
        </div>

        <!-- 局部 CITS -->
        <div class="grid grid-cols-2 gap-4">
          <button
            @click="startAutoMoveLocalSingleSTS"
            :disabled="isRunning || !selectedLocalAreaScript"
            class="px-4 py-3 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Auto-Move Local Single-STS CITS
          </button>

          <button
            @click="startAutoMoveLocalMultiSTS"
            :disabled="
              isRunning || !selectedLocalAreaScript || !selectedSMUScript
            "
            class="px-4 py-3 bg-pink-600 text-white rounded-md hover:bg-pink-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Auto-Move Local Multi-STS CITS
          </button>
        </div>
      </div>
    </div>

    <!-- 預覽與狀態顯示 -->
    <PreviewStatusPanel
      :status="status"
      :preview-data="previewData"
      :last-measurement="lastMeasurement"
      @get-status="getSXMStatus"
      @preview-auto-move="previewAutoMove"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import MoveScriptPanel from "./MoveScriptPanel.vue";
import PreviewStatusPanel from "./PreviewStatusPanel.vue";
import { useAutoMove } from "../../composables/useAutoMove";
import { useSharedSTSState } from "../../composables/useSharedSTSState";
import { useSharedAutoMoveState } from "../../composables/useSharedAutoMoveState";
import { useLocalCITSAreas } from "../../composables/useLocalCITSAreas";

// 基本狀態管理
const scriptName = ref("");
const movementScript = ref("");
const moveDistance = ref(200);
const waitTime = ref(1.0);
const repeatCount = ref(1);
const availableMoveScripts = ref([]);
const isRunning = ref(false);
const status = ref("Ready");
const previewData = ref(null);
const lastMeasurement = ref(null);

// 使用共享狀態
const { selectedScript: selectedSMUScript } = useSharedSTSState();
const { selectedAreaScript: selectedLocalAreaScript, areaScriptSettings } =
  useLocalCITSAreas();
const { selectedMoveScript, moveScriptSettings, updateSelectedScript } =
  useSharedAutoMoveState();

// 使用 composable
const {
  loadMoveScripts,
  saveMoveScript: saveAutoMoveScript,
  previewAutoMove: previewMove,
} = useAutoMove();

// SXM 狀態獲取
const getSXMStatus = async () => {
  try {
    const sxmStatus = await window.pywebview.api.get_sxm_status();
    status.value = "SXM status updated";
    return sxmStatus;
  } catch (error) {
    status.value = `Error getting SXM status: ${error.message}`;
    throw error;
  }
};

// 腳本管理
const refreshMoveScripts = async () => {
  try {
    const scripts = await loadMoveScripts();
    availableMoveScripts.value = scripts;
    status.value = "Movement scripts refreshed";
  } catch (error) {
    status.value = `Error loading scripts: ${error.message}`;
  }
};

const saveMoveScript = async () => {
  try {
    status.value = "Saving movement script...";
    await saveAutoMoveScript({
      name: scriptName.value,
      script: movementScript.value,
      distance: moveDistance.value,
      waitTime: waitTime.value,
      repeatCount: repeatCount.value,
    });
    status.value = "Movement script saved successfully";
    await refreshMoveScripts();
  } catch (error) {
    status.value = `Error saving script: ${error.message}`;
  }
};

const handleScriptSelect = (scriptData) => {
  if (scriptData) {
    scriptName.value = scriptData.name;
    movementScript.value = scriptData.script;
    moveDistance.value = scriptData.distance;
    waitTime.value = scriptData.waitTime;
    repeatCount.value = scriptData.repeatCount;
    updateSelectedScript(scriptData.name, scriptData);
  }
};

// 預覽功能
const previewAutoMove = async () => {
  try {
    status.value = "Generating preview...";
    const sxmStatus = await getSXMStatus();

    const preview = await previewMove({
      movement_script: movementScript.value,
      distance: moveDistance.value,
      center_x: sxmStatus.center_x,
      center_y: sxmStatus.center_y,
      angle: sxmStatus.angle,
    });

    previewData.value = preview;
    status.value = "Preview generated successfully";
  } catch (error) {
    status.value = `Preview error: ${error.message}`;
  }
};

// 在 AutoMoveMeasurement.vue 的 script 部分添加
const handlePreviewMovement = async () => {
  try {
    status.value = "Getting SXM status...";
    const sxmStatus = await getSXMStatus();

    status.value = "Generating preview...";
    const preview = await previewMove({
      movement_script: movementScript.value,
      distance: moveDistance.value,
      center_x: sxmStatus.center_x,
      center_y: sxmStatus.center_y,
      angle: sxmStatus.angle,
    });

    previewData.value = preview;
    status.value = "Preview generated successfully";
  } catch (error) {
    status.value = `Preview error: ${error.message}`;
  }
};

// 測量功能
const startAutoMoveScan = async () => {
  if (isRunning.value) return;

  try {
    isRunning.value = true;
    status.value = "Starting Auto-Move scan...";
    await window.pywebview.api.auto_move_scan_area(
      movementScript.value,
      moveDistance.value,
      waitTime.value,
      repeatCount.value
    );
    status.value = "Auto-Move scan completed";
    lastMeasurement.value = {
      type: "Auto-Move Scan",
      timestamp: new Date().toISOString(),
      script: scriptName.value,
    };
  } catch (error) {
    status.value = `Error: ${error.message}`;
  } finally {
    isRunning.value = false;
  }
};

const startAutoMoveSingleSTS = async () => {
  if (isRunning.value) return;

  try {
    isRunning.value = true;
    status.value = "Starting Auto-Move Single-STS CITS...";
    await window.pywebview.api.auto_move_ssts_cits(
      movementScript.value,
      moveDistance.value,
      waitTime.value,
      repeatCount.value
    );
    status.value = "Auto-Move Single-STS CITS completed";
    lastMeasurement.value = {
      type: "Auto-Move Single-STS CITS",
      timestamp: new Date().toISOString(),
      script: scriptName.value,
    };
  } catch (error) {
    status.value = `Error: ${error.message}`;
  } finally {
    isRunning.value = false;
  }
};

const startAutoMoveMultiSTS = async () => {
  if (isRunning.value || !selectedSMUScript.value) return;

  try {
    isRunning.value = true;
    status.value = "Starting Auto-Move Multi-STS CITS...";
    await window.pywebview.api.auto_move_msts_cits(
      movementScript.value,
      moveDistance.value,
      selectedSMUScript.value,
      waitTime.value,
      repeatCount.value
    );
    status.value = "Auto-Move Multi-STS CITS completed";
    lastMeasurement.value = {
      type: "Auto-Move Multi-STS CITS",
      timestamp: new Date().toISOString(),
      script: scriptName.value,
      smu_script: selectedSMUScript.value,
    };
  } catch (error) {
    status.value = `Error: ${error.message}`;
  } finally {
    isRunning.value = false;
  }
};

const startAutoMoveLocalSingleSTS = async () => {
  if (isRunning.value || !selectedLocalAreaScript.value) return;

  try {
    isRunning.value = true;
    status.value = "Starting Auto-Move Local Single-STS CITS...";
    await window.pywebview.api.auto_move_local_ssts_cits(
      movementScript.value,
      moveDistance.value,
      areaScriptSettings.value.areas,
      waitTime.value,
      repeatCount.value
    );
    status.value = "Auto-Move Local Single-STS CITS completed";
    lastMeasurement.value = {
      type: "Auto-Move Local Single-STS CITS",
      timestamp: new Date().toISOString(),
      script: scriptName.value,
      local_area_script: selectedLocalAreaScript.value,
    };
  } catch (error) {
    status.value = `Error: ${error.message}`;
  } finally {
    isRunning.value = false;
  }
};

const startAutoMoveLocalMultiSTS = async () => {
  if (
    isRunning.value ||
    !selectedLocalAreaScript.value ||
    !selectedSMUScript.value
  )
    return;

  try {
    isRunning.value = true;
    status.value = "Starting Auto-Move Local Multi-STS CITS...";
    await window.pywebview.api.auto_move_local_msts_cits(
      movementScript.value,
      moveDistance.value,
      areaScriptSettings.value.areas,
      selectedSMUScript.value,
      waitTime.value,
      repeatCount.value
    );
    status.value = "Auto-Move Local Multi-STS CITS completed";
    lastMeasurement.value = {
      type: "Auto-Move Local Multi-STS CITS",
      timestamp: new Date().toISOString(),
      script: scriptName.value,
      smu_script: selectedSMUScript.value,
      local_area_script: selectedLocalAreaScript.value,
    };
  } catch (error) {
    status.value = `Error: ${error.message}`;
  } finally {
    isRunning.value = false;
  }
};

// 初始化
onMounted(async () => {
  await refreshMoveScripts();
  // 如果有已保存的腳本設定，恢復它
  if (moveScriptSettings.value) {
    handleScriptSelect({
      name: selectedMoveScript.value,
      ...moveScriptSettings.value,
    });
  }
});
</script>
