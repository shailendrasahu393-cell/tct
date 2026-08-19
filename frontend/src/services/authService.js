import api from './api';

export const authService = {
  async login(credentials) {
    const { data } = await api.post('/login', { username: credentials.identity, password: credentials.password });
    const user = data.user;
    return user;
  },
  async logout() { await api.post('/logout'); },
  async getCurrentUser() {
    try { const { data } = await api.get('/me'); return data.user; } catch (error) { if (error.response?.status === 401) return null; throw error; }
  }
};
