import axios from "axios";
const apiBaseUrl = import.meta.env.DEV
  ? "/api"
  : import.meta.env.VITE_API_BASE_URL || "/api";
const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: Number(import.meta.env.VITE_API_TIMEOUT_MS || 10000),
  withCredentials: true,
});
export default api;
