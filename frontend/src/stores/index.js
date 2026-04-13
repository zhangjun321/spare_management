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
