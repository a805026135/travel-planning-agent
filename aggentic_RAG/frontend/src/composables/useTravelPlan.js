import { ref } from "vue";
import api from "../services/api.js";
import { marked } from "marked";

/**
 * 旅行规划编排 composable
 */
export function useTravelPlan() {
  const loading = ref(false);
  const error = ref("");
  const meta = ref(null);
  const travelPlanHtml = ref("");

  async function submitPlan(query, sseEvents, sseStart, sseRunning) {
    if (!query.trim()) {
      error.value = "请先填写出行需求。";
      return;
    }

    loading.value = true;
    error.value = "";
    travelPlanHtml.value = "";
    meta.value = null;

    try {
      // 1. 发起流式规划请求
      const { data } = await api.post("/api/plan/stream", { query });

      // 2. 建立 SSE 连接
      sseStart(data.task_id);

      // 3. 等待 SSE 完成
      await new Promise((resolve) => {
        const check = setInterval(() => {
          if (!sseRunning.value) {
            clearInterval(check);
            resolve();
          }
        }, 200);
      });

      // 4. 检查 SSE 结果
      if (sseEvents.value.length > 0) {
        const lastEvent = sseEvents.value[sseEvents.value.length - 1];
        if (lastEvent.type === "error") {
          error.value = lastEvent.error || "规划失败";
          return;
        }
      }

      // 通过结果轮询获取最终数据
      const resultData = await fetchResult();
      if (resultData) {
        return resultData;
      }

      // 回退: 使用同步接口
      await fetchPlanSync(query);
    } catch (e) {
      // 如果流式启动失败，回退到同步接口
      await fetchPlanSync(query);
    } finally {
      loading.value = false;
    }
  }

  async function fetchResult() {
    try {
      // 从事件中尝试找 task_id 需要重新设计
      return null;
    } catch {
      return null;
    }
  }

  async function fetchPlanSync(query) {
    try {
      const { data } = await api.post("/api/plan", { query });
      if (data.success) {
        travelPlanHtml.value = data.travel_plan ? marked.parse(data.travel_plan) : "";
        meta.value = data.meta || null;
      } else {
        error.value = data.error || "规划失败";
      }
    } catch (e) {
      error.value =
        e.response?.data?.detail ||
        e.message ||
        "请求失败，请确认后端已启动（FastAPI :8000）。";
    }
  }

  return { loading, error, meta, travelPlanHtml, submitPlan };
}
