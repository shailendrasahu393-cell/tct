import api from "./api";

export const adminService = {
  async createAdmin(payload) {
    const { data } = await api.post("/admin", {
      username: payload.email,
      recovery_email: payload.recoveryEmail,
      name: payload.name,
      password: payload.password,
      lab_name: payload.lab,
      class_name: payload.section,
    });
    return data;
  },
  async requestPasswordReset(identity) {
    const { data } = await api.post("/password-reset/request", { identity });
    return data;
  },
  async completePasswordReset(token, newPassword) {
    const { data } = await api.post("/password-reset/complete", {
      token,
      new_password: newPassword,
    });
    return data;
  },
  async resetPassword(payload, username) {
    await api.put(`/faculty/${encodeURIComponent(username)}/password`, {
      old_password: payload.current,
      new_password: payload.password,
    });
  },
  async getAdmins() {
    const { data } = await api.get("/admin");
    return data;
  },
  async deleteAdmin(username) {
    await api.delete(`/admin/${encodeURIComponent(username)}`);
  },
};
