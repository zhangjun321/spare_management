import axios from 'axios'

const _http = axios.create({
  baseURL: '/api/stock-take',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

_http.interceptors.request.use((config) => {
  const csrfToken = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrf_token='))
    ?.split('=')[1]
  if (csrfToken) config.headers['X-CSRFToken'] = csrfToken
  return config
})

export const StockTakeService = {
  // ===== 任务 =====

  async listTasks(params = {}) {
    try {
      const response = await _http.get('/tasks', { params })
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  async stats() {
    try {
      const response = await _http.get('/stats')
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  async getTask(id) {
    try {
      const response = await _http.get(`/tasks/${id}`)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  async createTask(data) {
    try {
      const response = await _http.post('/tasks', data)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  async updateTask(id, data) {
    try {
      const response = await _http.put(`/tasks/${id}`, data)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  async deleteTask(id) {
    try {
      const response = await _http.delete(`/tasks/${id}`)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // 开始盘点
  async startTask(id) {
    try {
      const response = await _http.post(`/tasks/${id}/start`)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // ===== 明细 =====

  async listItems(taskId) {
    try {
      const response = await _http.get(`/tasks/${taskId}/items`)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  async updateItem(taskId, itemId, data) {
    try {
      const response = await _http.put(`/tasks/${taskId}/items/${itemId}`, data)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // 批量更新盘点数量
  async batchUpdateItems(taskId, items) {
    try {
      const response = await _http.put(`/tasks/${taskId}/items/batch`, { items })
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // 完成盘点
  async completeTask(id) {
    try {
      const response = await _http.post(`/tasks/${id}/complete`)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // ===== 调整单 =====

  async listAdjustments(params = {}) {
    try {
      const response = await _http.get('/adjustments', { params })
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  async getAdjustment(id) {
    try {
      const response = await _http.get(`/adjustments/${id}`)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  async approveAdjustment(id) {
    try {
      const response = await _http.post(`/adjustments/${id}/approve`)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  async rejectAdjustment(id, reason) {
    try {
      const response = await _http.post(`/adjustments/${id}/reject`, { reason })
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },
}
