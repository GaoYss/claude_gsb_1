import http, { createResourceApi } from './client'

export const treeApi = {
  ...createResourceApi('trees'),
  /** 有树木建档的行政区及株数 */
  districts: () => http.get('/trees/districts'),
  /** 树木档案：基础信息 + 养护统计 + 全部养护措施 */
  profile: (id) => http.get(`/trees/${id}/profile`),
  /** 某株树下的全部养护措施记录 */
  maintenances: (treeId) => http.get(`/trees/${treeId}/maintenances`),
  createMaintenance: (treeId, payload) => http.post(`/trees/${treeId}/maintenances`, payload),
  updateMaintenance: (treeId, id, payload) =>
    http.put(`/trees/${treeId}/maintenances/${id}`, payload),
  removeMaintenance: (treeId, id) => http.delete(`/trees/${treeId}/maintenances/${id}`),
}
