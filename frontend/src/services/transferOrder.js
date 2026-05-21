import axios from 'axios'

const _http = axios.create({
  baseURL: '/api/transfer-orders',
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

export const TransferOrderService = {
  // 列表
  async list(params = {}) {
    try {
      const response = await _http.get('/', { params })
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // 统计
  async stats() {
    try {
      const response = await _http.get('/stats')
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // 详情
  async get(id) {
    try {
      const response = await _http.get(`/${id}`)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // 创建
  async create(data) {
    try {
      const response = await _http.post('/', data)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // 更新
  async update(id, data) {
    try {
      const response = await _http.put(`/${id}`, data)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // 删除
  async delete(id) {
    try {
      const response = await _http.delete(`/${id}`)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // 提交审批
  async submit(id) {
    try {
      const response = await _http.post(`/${id}/submit`)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // 审批通过
  async approve(id) {
    try {
      const response = await _http.post(`/${id}/approve`)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // 驳回
  async reject(id, reason) {
    try {
      const response = await _http.post(`/${id}/reject`, { reason })
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // 发货
  async ship(id) {
    try {
      const response = await _http.post(`/${id}/ship`)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // 确认收货
  async receive(id) {
    try {
      const response = await _http.post(`/${id}/receive`)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },
}
