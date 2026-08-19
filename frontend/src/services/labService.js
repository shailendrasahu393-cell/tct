import api from "./api";

export const labService = {
  async getLabs() {
    const { data } = await api.get("/labs");
    return data;
  },
  async getLabById(id) {
    try {
      const { data } = await api.get(`/labs/${id}`);
      return data;
    } catch (error) {
      if (error.response?.status === 404) return null;
      throw error;
    }
  },
  async deleteLab(id) {
    await api.delete(`/labs/${id}`);
  },
};
