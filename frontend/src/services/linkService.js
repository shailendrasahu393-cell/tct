import api from './api';

export const linkService = {
  async getLabLinks(labId) { const { data } = await api.get('/links', { params: { lab_id: labId } }); return data; },
  async getMyLinks(labId) { return this.getLabLinks(labId); },
  async createLink(payload) { const { data } = await api.post('/links', { ...payload, lab_id: payload.labId }); return data; },
  async updateLink(id, payload) { const { data } = await api.put(`/links/${id}`, { ...payload, lab_id: payload.labId }); return data; },
  async deleteLink(id) { await api.delete(`/links/${id}`); }
};
