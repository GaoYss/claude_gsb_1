import { createResourceApi } from './client'
import http from './client'

export const treeApi = {
  ...createResourceApi('trees'),
  summary: (params) => http.get('/trees/summary', { params }),
}

export const treeMaintenanceApi = {
  ...createResourceApi('tree-maintenances'),
}
