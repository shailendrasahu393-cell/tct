import api from './api';

export const adminService = {
  async createAdmin(payload) {
    const { data } = await api.post('/admin', {
      username: payload.email,
      name: payload.name,
      password: payload.password,
      lab_name: payload.lab,
      class_name: payload.section,
    });
    return data;
  },
  async resetPassword(payload, username) {
    await api.put(`/faculty/${encodeURIComponent(username)}/password`, {
      old_password: payload.current,
      new_password: payload.password,
    });
  }
};
