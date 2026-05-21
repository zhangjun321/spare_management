import axios from 'axios'

const _http = axios.create({
  baseURL: '/api/reservations',
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

export const ReservationService = {
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

  // 释放
  async release(id) {
    try {
      const response = await _http.post(`/${id}/release`)
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // 延长有效期
  async extend(id, expireDays) {
    try {
      const response = await _http.post(`/${id}/extend`, { expire_days: expireDays })
      return response.data
    } catch (error) {
      return { success: false, error: error.response?.data?.error || '请求失败' }
    }
  },

  // 处理过期
  async expire(id) {
    try {
      const response = await _http.post(`/${id}/expire`)
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
}
