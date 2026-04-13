import { create } from 'zustand'

/**
 * 仓库状态管理
 */
export const useWarehouseStore = create((set) => ({
  // 统计数据
  stats: {
    todayInbound: 0,
    todayOutbound: 0,
    totalItems: 0,
    lowStockCount: 0,
    outOfStockCount: 0,
    aiInsightsCount: 0
  },

  // 设置统计数据
  setStats: (stats) => set({ stats }),

  // 更新单个统计项
  updateStat: (key, value) => set((state) => ({
    stats: {
      ...state.stats,
      [key]: value
    }
  }))
}))

/**
 * UI 状态管理
 */
export const useUIStore = create((set) => ({
  // 侧边栏状态
  sidebarCollapsed: false,
  
  // 切换侧边栏
  toggleSidebar: () => set((state) => ({ 
    sidebarCollapsed: !state.sidebarCollapsed 
  })),
  
  // 设置侧边栏状态
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

  // 加载状态
  loading: false,
  
  // 设置加载状态
  setLoading: (loading) => set({ loading }),

  // 消息提示
  message: null,
  
  // 显示消息
  showMessage: (message, type = 'info') => set({ message: { content: message, type } }),
  
  // 清除消息
  clearMessage: () => set({ message: null })
}))

/**
 * 仓库列表业务数据缓存 Store
 * TTL: 5 分钟内不重复请求
 */
const WAREHOUSE_LIST_TTL = 5 * 60 * 1000

export const useWarehouseListStore = create((set, get) => ({
  // 仓库列表数据
  list: [],
  // 分页信息
  pagination: { current: 1, pageSize: 20, total: 0 },
  // 筛选条件
  filters: {},
  // 加载状态
  loading: false,
  // 最后更新时间戳（用于 TTL 判断）
  lastFetchedAt: null,

  // 判断缓存是否有效
  isCacheValid: () => {
    const { lastFetchedAt } = get()
    return lastFetchedAt !== null && (Date.now() - lastFetchedAt) < WAREHOUSE_LIST_TTL
  },

  // 设置仓库列表
  setList: (list) => set({ list, lastFetchedAt: Date.now() }),

  // 设置分页
  setPagination: (pagination) => set((state) => ({
    pagination: { ...state.pagination, ...pagination }
  })),

  // 设置筛选条件（筛选变更时清空缓存）
  setFilters: (filters) => set({ filters, lastFetchedAt: null }),

  // 设置加载状态
  setLoading: (loading) => set({ loading }),

  // 清空缓存（强制下次重新请求）
  invalidateCache: () => set({ lastFetchedAt: null }),

  // 重置所有状态
  reset: () => set({
    list: [],
    pagination: { current: 1, pageSize: 20, total: 0 },
    filters: {},
    loading: false,
    lastFetchedAt: null
  })
}))

/**
 * 备件列表业务数据缓存 Store
 * TTL: 3 分钟内不重复请求
 */
const SPARE_PART_TTL = 3 * 60 * 1000

export const useSparePartStore = create((set, get) => ({
  // 备件列表数据
  list: [],
  // 分页信息
  pagination: { current: 1, pageSize: 20, total: 0 },
  // 筛选条件
  filters: {},
  // 加载状态
  loading: false,
  // 低库存备件统计
  lowStockList: [],
  lowStockCount: 0,
  // 最后更新时间戳
  lastFetchedAt: null,
  lowStockLastFetchedAt: null,

  // 判断列表缓存是否有效
  isCacheValid: () => {
    const { lastFetchedAt } = get()
    return lastFetchedAt !== null && (Date.now() - lastFetchedAt) < SPARE_PART_TTL
  },

  // 判断低库存缓存是否有效
  isLowStockCacheValid: () => {
    const { lowStockLastFetchedAt } = get()
    return lowStockLastFetchedAt !== null && (Date.now() - lowStockLastFetchedAt) < SPARE_PART_TTL
  },

  // 设置备件列表
  setList: (list) => set({ list, lastFetchedAt: Date.now() }),

  // 设置分页
  setPagination: (pagination) => set((state) => ({
    pagination: { ...state.pagination, ...pagination }
  })),

  // 设置筛选条件（清空缓存）
  setFilters: (filters) => set({ filters, lastFetchedAt: null }),

  // 设置加载状态
  setLoading: (loading) => set({ loading }),

  // 设置低库存统计
  setLowStockList: (lowStockList) => set({
    lowStockList,
    lowStockCount: lowStockList.length,
    lowStockLastFetchedAt: Date.now()
  }),

  // 清空缓存
  invalidateCache: () => set({ lastFetchedAt: null, lowStockLastFetchedAt: null }),

  // 重置所有状态
  reset: () => set({
    list: [],
    pagination: { current: 1, pageSize: 20, total: 0 },
    filters: {},
    loading: false,
    lowStockList: [],
    lowStockCount: 0,
    lastFetchedAt: null,
    lowStockLastFetchedAt: null
  })
}))

