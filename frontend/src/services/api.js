import axios from 'axios';
const api = axios.create({
	baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
	timeout: Number(import.meta.env.VITE_API_TIMEOUT_MS || 10000),
	withCredentials: true,
});
export default api;
