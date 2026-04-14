/**
 * 备件管理 API 服务层
 * 所有请求统一经过带 CSRF Token 注入的 _http 实例
 */

import axios from 'axios'

const _http = axios.create({ baseURL: '/api/spare-parts' })

_http.interceptors.request.use((config) => {
  const csrfToken = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrf_token='))
    ?.split('=')[1]
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken
  }
  return config
})

// ── 列表 ─────────────────────────────────────
export const SparePartService = {
  /**
   * 获取备件列表（支持分页、搜索、筛选）
   * @param {Object} params - { page, per_page, keyword, category_id, supplier_id, stock_status, is_active }
   */
  async list(params = {}) {
    const response = await _http.get('/', { params })
    return response.data
  },

  /** 获取筛选选项（分类/供应商/仓库） */
  async getOptions() {
    const response = await _http.get('/options')
    return response.data
  },

  /** 获取备件详情 */
  async get(id) {
    const response = await _http.get(`/${id}`)
    return response.data
  },

  /** 新增备件 */
  async create(data) {
    const response = await _http.post('/', data)
    return response.data
  },

  /** 更新备件 */
  async update(id, data) {
    const response = await _http.put(`/${id}`, data)
    return response.data
  },

  /** 删除备件 */
  async delete(id) {
    const response = await _http.delete(`/${id}`)
    return response.data
  },

  /** 切换启用状态 */
  async toggleStatus(id) {
    const response = await _http.post(`/${id}/toggle-status`)
    return response.data
  },

  /** 检查备件代码是否已存在 */
  async checkCode(partCode, excludeId = null) {
    const response = await _http.post('/check-code', {
      part_code: partCode,
      exclude_id: excludeId,
    })
    return response.data
  },

  /** 条形码搜索 */
  async searchByBarcode(barcode) {
    const response = await _http.get('/search-by-barcode', { params: { barcode } })
    return response.data
  },

  /**
   * 导出备件数据
   * @param {'csv'|'excel'} format
   * @param {Object} params - 筛选条件或 ids
   */
  exportUrl(format = 'excel', params = {}) {
    const q = new URLSearchParams({ format, ...params }).toString()
    return `/api/spare-parts/export?${q}`
  },
}

// ── 图片管理 ──────────────────────────────────
export const SparePartImageService = {
  /** 获取所有图片 */
  async getImages(id) {
    const response = await _http.get(`/${id}/images`)
    return response.data
  },

  /** 上传图片（multipart/form-data） */
  async uploadImage(id, imageType, file) {
    const formData = new FormData()
    formData.append('image', file)
    formData.append('image_type', imageType)
    const csrfToken = document.cookie
      .split('; ')
      .find((row) => row.startsWith('csrf_token='))
      ?.split('=')[1]
    const response = await _http.post(`/${id}/upload-image`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
      },
    })
    return response.data
  },

  /** 删除图片 */
  async removeImage(id, imageType) {
    const response = await _http.post(`/${id}/remove-image`, { image_type: imageType })
    return response.data
  },

  /** 生成单张 AI 图片 */
  async generateSingleImage(id, imageType) {
    const response = await _http.post(`/${id}/generate-single-image`, { image_type: imageType })
    return response.data
  },

  /** 获取条形码图片 URL */
  barcodeUrl(id) {
    return `/api/spare-parts/${id}/barcode`
  },

  /** 生成并保存条形码 */
  async generateBarcode(id) {
    const response = await _http.post(`/${id}/generate-barcode`)
    return response.data
  },
}

// ── AI 填充 ───────────────────────────────────
export const SparePartAIService = {
  /** 请求 AI 智能填充 */
  async fill(id) {
    const response = await _http.get(`/${id}/ai-fill`)
    return response.data
  },

  /** 应用 AI 填充建议 */
  async applyFill(id, filledData) {
    const response = await _http.post(`/${id}/apply-ai-fill`, { filled_data: filledData })
    return response.data
  },
}

export default SparePartService
