import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "",
  timeout: 0,
});

// 请求拦截器：自动附带 token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * 订阅 SSE 流，获取 Agent 实时进度
 * @param {string} taskId
 * @param {object} callbacks - { onProgress, onComplete, onError }
 * @returns {{ close: () => void }}
 */
export function subscribeSSE(taskId, { onProgress = () => {}, onComplete = () => {}, onError = () => {} } = {}) {
  const base = import.meta.env.VITE_API_BASE || "";
  const url = `${base}/api/plan/stream/${taskId}`;
  const es = new EventSource(url);

  es.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case "progress":
          onProgress(data);
          break;
        case "complete":
          onComplete(data.result);
          es.close();
          break;
        case "error":
          onError(data.error || "Agent 执行出错");
          es.close();
          break;
        default:
          break;
      }
    } catch {
      // ignore parse errors
    }
  };

  es.onerror = () => {
    onError("SSE 连接失败，请确认后端已启动");
    es.close();
  };

  return {
    close: () => es.close(),
  };
}

export default api;
