/**
 * 仓库管理 API 服务
 */

import axios from 'axios';

const API_BASE_URL = '/api';

/**
 * 带 CSRF Token 自动注入的内部 axios 实例
 * 注意：不使用 apiClient，因为 apiClient 的响应拦截器直接返回 response.data，
 * 而本文件中所有方法已自行处理 response.data，保持兼容性。
 */
const _http = axios.create({ baseURL: API_BASE_URL });
_http.interceptors.request.use((config) => {
  const csrfToken = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrf_token='))
    ?.split('=')[1];
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken;
  }
  return config;
});

class WarehouseService {
  /**
   * 获取仓库列表
   */
  static async getWarehouses(params = {}) {
    try {
      const response = await _http.get('/warehouses', { params });
      return response.data;
    } catch (error) {
      console.error('获取仓库列表失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '请求失败'
      };
    }
  }

  /**
   * 获取仓库详情
   */
  static async getWarehouse(warehouseId) {
    try {
      const response = await _http.get(`/warehouses/${warehouseId}`);
      return response.data;
    } catch (error) {
      console.error('获取仓库详情失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '请求失败'
      };
    }
  }

  /**
   * 创建仓库
   */
  static async createWarehouse(data) {
    try {
      const response = await _http.post('/warehouses', data);
      return response.data;
    } catch (error) {
      console.error('创建仓库失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '创建失败'
      };
    }
  }

  /**
   * 更新仓库
   */
  static async updateWarehouse(warehouseId, data) {
    try {
      const response = await _http.put(`/warehouses/${warehouseId}`, data);
      return response.data;
    } catch (error) {
      console.error('更新仓库失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '更新失败'
      };
    }
  }

  /**
   * 删除仓库
   */
  static async deleteWarehouse(warehouseId) {
    try {
      const response = await _http.delete(`/warehouses/${warehouseId}`);
      return response.data;
    } catch (error) {
      console.error('删除仓库失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '删除失败'
      };
    }
  }

  /**
   * 获取仓库统计信息
   */
  static async getWarehouseStatistics(warehouseId) {
    try {
      const response = await _http.get(`/warehouses/${warehouseId}/statistics`);
      return response.data;
    } catch (error) {
      console.error('获取仓库统计失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '请求失败'
      };
    }
  }

  /**
   * 获取仓库库存列表（库存联动展示）
   */
  static async getWarehouseInventory(warehouseId, params = {}) {
    try {
      const response = await _http.get(`/warehouses/${warehouseId}/inventory`, { params });
      return response.data;
    } catch (error) {
      console.error('获取仓库库存失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '请求失败'
      };
    }
  }

  /**
   * 获取仓库库位列表
   */
  static async getWarehouseLocations(warehouseId, params = {}) {
    try {
      const response = await _http.get(`/warehouses/${warehouseId}/locations`, { params });
      return response.data;
    } catch (error) {
      console.error('获取库位列表失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '请求失败'
      };
    }
  }

  /**
   * 获取所有启用的仓库
   */
  static async getAllWarehouses() {
    try {
      const response = await _http.get('/warehouses/all');
      return response.data;
    } catch (error) {
      console.error('获取所有仓库失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '请求失败'
      };
    }
  }

  /**
   * 批量删除仓库
   */
  static async batchDeleteWarehouses(ids) {
    try {
      const response = await _http.post('/warehouses/batch/delete', { ids });
      return response.data;
    } catch (error) {
      console.error('批量删除失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '批量删除失败'
      };
    }
  }

  /**
   * 批量导出仓库
   */
  static async batchExportWarehouses(ids = []) {
    try {
      const params = ids.length > 0 ? { ids: ids.join(',') } : {};
      const response = await _http.get('/warehouses/batch/export', {
        params,
        responseType: 'blob' // 重要：设置为 blob 以接收文件
      });

      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `仓库列表_${new Date().getTime()}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      return { success: true };
    } catch (error) {
      console.error('批量导出失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '批量导出失败'
      };
    }
  }

  /**
   * 批量导入仓库
   */
  static async batchImportWarehouses(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await _http.post('/warehouses/batch/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('批量导入失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '批量导入失败'
      };
    }
  }

  /**
   * 批量更新仓库
   */
  static async batchUpdateWarehouses(ids, field, value) {
    try {
      const response = await _http.post('/warehouses/batch/update', {
        ids,
        field,
        value
      });
      return response.data;
    } catch (error) {
      console.error('批量更新失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '批量更新失败'
      };
    }
  }

  /**
   * 获取仓库健康分析（AI）
   */
  static async getWarehouseHealth(warehouseId) {
    try {
      const response = await _http.get(`/warehouses/${warehouseId}/health`);
      return response.data;
    } catch (error) {
      console.error('获取仓库健康分析失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '请求失败'
      };
    }
  }

  /**
   * AI 推荐仓库和货位
   */
  static async recommendLocation(sparePartData) {
    try {
      const response = await _http.post('/locations/recommend', sparePartData);
      return response.data;
    } catch (error) {
      console.error('AI 推荐失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '推荐失败'
      };
    }
  }

  /**
   * 获取货位列表
   */
  static async getLocations(params = {}) {
    try {
      const response = await _http.get('/locations', { params });
      return response.data;
    } catch (error) {
      console.error('获取货位列表失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '请求失败'
      };
    }
  }

  /**
   * 获取货位详情
   */
  static async getLocation(locationId) {
    try {
      const response = await _http.get(`/locations/${locationId}`);
      return response.data;
    } catch (error) {
      console.error('获取货位详情失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '请求失败'
      };
    }
  }
}

// 仓库统计服务
const warehouseStatsService = {
  async getAllStats() {
    try {
      const response = await _http.get('/warehouses/stats/overview');
      return response.data;
    } catch (error) {
      console.error('获取统计失败:', error);
      return {
        todayInbound: 0,
        todayOutbound: 0,
        totalItems: 0,
        lowStockCount: 0,
        outOfStockCount: 0,
        aiInsightsCount: 0
      };
    }
  },

  async getWarehouseStats(warehouseId) {
    try {
      const response = await _http.get(`/warehouses/${warehouseId}/statistics`);
      return response.data;
    } catch (error) {
      console.error('获取仓库统计失败:', error);
      return null;
    }
  }
};

// AI 分析服务
const aiAnalysisService = {
  async getInsights() {
    try {
      const response = await _http.get('/warehouses/ai/insights');
      return response.data;
    } catch (error) {
      console.error('获取 AI 洞察失败:', error);
      return [];
    }
  },

  async getInventoryAnalysis(days = 30) {
    try {
      const response = await _http.get('/warehouses/ai/inventory-analysis', {
        params: { days }
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('获取库存分析失败:', error);
      return {
        success: false,
        error: error.response?.data?.error || '获取分析失败'
      };
    }
  },

  async getWarehouseHealth(warehouseId) {
    try {
      const response = await _http.get(`/warehouses/${warehouseId}/health`);
      return response.data;
    } catch (error) {
      console.error('获取健康分析失败:', error);
      return null;
    }
  }
};

// 入库单服务
const inboundOrderService = {
  async getList(params = {}) {
    try {
      const response = await _http.get('/inbound/orders', { params });
      return response.data;
    } catch (error) {
      console.error('获取入库单列表失败:', error);
      return { items: [], total: 0 };
    }
  },

  async create(data) {
    try {
      const response = await _http.post('/inbound/orders', data);
      return response.data;
    } catch (error) {
      console.error('创建入库单失败:', error);
      return { success: false, error: error.response?.data?.error || '创建失败' };
    }
  },

  async getPendingOrders() {
    try {
      const response = await _http.get('/inbound/orders/pending');
      return response.data.items || [];
    } catch (error) {
      console.error('获取待处理入库单失败:', error);
      return [];
    }
  },

  async complete(orderId) {
    try {
      const response = await _http.post(`/inbound/orders/${orderId}/complete`);
      return response.data;
    } catch (error) {
      console.error('完成入库单失败:', error);
      return { success: false, error: error.response?.data?.error || '操作失败' };
    }
  },

  async cancel(orderId) {
    try {
      const response = await _http.post(`/inbound/orders/${orderId}/cancel`);
      return response.data;
    } catch (error) {
      console.error('取消入库单失败:', error);
      return { success: false, error: error.response?.data?.error || '操作失败' };
    }
  }
};

// 出库单服务
const outboundOrderService = {
  async getList(params = {}) {
    try {
      const response = await _http.get('/outbound/orders', { params });
      return response.data;
    } catch (error) {
      console.error('获取出库单列表失败:', error);
      return { items: [], total: 0 };
    }
  },

  async create(data) {
    try {
      const response = await _http.post('/outbound/orders', data);
      return response.data;
    } catch (error) {
      console.error('创建出库单失败:', error);
      return { success: false, error: error.response?.data?.error || '创建失败' };
    }
  },

  async getPendingOrders() {
    try {
      const response = await _http.get('/outbound/orders/pending');
      return response.data.items || [];
    } catch (error) {
      console.error('获取待处理出库单失败:', error);
      return [];
    }
  },

  async complete(orderId) {
    try {
      const response = await _http.post(`/outbound/orders/${orderId}/complete`);
      return response.data;
    } catch (error) {
      console.error('完成出库单失败:', error);
      return { success: false, error: error.response?.data?.error || '操作失败' };
    }
  },

  async cancel(orderId) {
    try {
      const response = await _http.post(`/outbound/orders/${orderId}/cancel`);
      return response.data;
    } catch (error) {
      console.error('取消出库单失败:', error);
      return { success: false, error: error.response?.data?.error || '操作失败' };
    }
  }
};

// 库存服务
const inventoryService = {
  async getList(params = {}) {
    try {
      const response = await _http.get('/inventory/records', { params });
      return response.data;
    } catch (error) {
      console.error('获取库存列表失败:', error);
      return { success: false, data: { items: [], total: 0 } };
    }
  },

  async getStats(params = {}) {
    try {
      const response = await _http.get('/inventory/stats', { params });
      return response.data;
    } catch (error) {
      console.error('获取库存统计失败:', error);
      return { success: false, data: { total: 0, low_stock: 0, out_of_stock: 0, normal: 0 } };
    }
  },

  async update(id, data) {
    try {
      const response = await _http.put(`/inventory/records/${id}`, data);
      return response.data;
    } catch (error) {
      console.error('更新库存失败:', error);
      return { success: false, error: error.response?.data?.error || '更新失败' };
    }
  }
};

export default WarehouseService;
export { warehouseStatsService, aiAnalysisService, inboundOrderService, outboundOrderService, inventoryService };
