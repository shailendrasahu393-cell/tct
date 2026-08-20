import axios from "axios";
const apiBaseUrl = "/api";
const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: Number(import.meta.env.VITE_API_TIMEOUT_MS || 10000),
  withCredentials: true,
});
export default api;
