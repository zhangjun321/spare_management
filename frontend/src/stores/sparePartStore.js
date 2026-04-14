import { create } from 'zustand'
import SparePartService from '../services/sparePart'

const CACHE_TTL = 5 * 60 * 1000 // 5分钟缓存

const useSparePartStore = create((set, get) => ({
  // ── 列表状态 ──────────────────────────────
  parts: [],
  pagination: { page: 1, per_page: 20, total: 0, pages: 0, has_prev: false, has_next: false },
  filters: {
    keyword: '',
    category_id: '',
    supplier_id: '',
    stock_status: '',
    is_active: '',
    per_page: 20,
  },
  loading: false,
  error: null,

  // ── 选项缓存 ──────────────────────────────
  options: null,
  optionsLoadedAt: null,

  // ── 当前编辑备件 ──────────────────────────
  currentPart: null,
  currentLoading: false,

  // ── 图片状态 ──────────────────────────────
  images: {},

  // ── 操作 ─────────────────────────────────

  /** 设置筛选条件并重置到第1页 */
  setFilters: (newFilters) => {
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
    }))
  },

  /** 加载备件列表 */
  fetchParts: async (page = 1) => {
    const { filters } = get()
    set({ loading: true, error: null })
    try {
      const result = await SparePartService.list({
        page,
        per_page: filters.per_page,
        keyword: filters.keyword,
        category_id: filters.category_id,
        supplier_id: filters.supplier_id,
        stock_status: filters.stock_status,
        is_active: filters.is_active,
      })
      if (result.success) {
        set({ parts: result.data, pagination: { ...result.pagination, per_page: filters.per_page } })
      } else {
        set({ error: result.error || '加载失败' })
      }
    } catch (e) {
      set({ error: e.message })
    } finally {
      set({ loading: false })
    }
  },

  /** 加载选项（带 TTL 缓存，5分钟内不重复请求） */
  fetchOptions: async () => {
    const { options, optionsLoadedAt } = get()
    if (options && optionsLoadedAt && Date.now() - optionsLoadedAt < CACHE_TTL) return options

    try {
      const result = await SparePartService.getOptions()
      if (result.success) {
        set({ options: result, optionsLoadedAt: Date.now() })
        return result
      }
    } catch (e) {
      console.error('加载选项失败', e)
    }
    return null
  },

  /** 加载备件详情 */
  fetchPart: async (id) => {
    set({ currentLoading: true, currentPart: null })
    try {
      const result = await SparePartService.get(id)
      if (result.success) {
        set({ currentPart: result.data })
      }
    } catch (e) {
      console.error('加载备件详情失败', e)
    } finally {
      set({ currentLoading: false })
    }
  },

  /** 清除当前备件（离开详情/表单页时调用） */
  clearCurrentPart: () => set({ currentPart: null }),

  /** 删除备件后刷新列表 */
  deletePart: async (id) => {
    const result = await SparePartService.delete(id)
    if (result.success) {
      const { pagination, fetchParts } = get()
      await fetchParts(pagination.page)
    }
    return result
  },

  /** 切换备件启用状态 */
  toggleStatus: async (id) => {
    const result = await SparePartService.toggleStatus(id)
    if (result.success) {
      // 更新列表中对应条目
      set((state) => ({
        parts: state.parts.map((p) =>
          p.id === id ? { ...p, is_active: result.is_active } : p
        ),
      }))
    }
    return result
  },

  /** 重置筛选条件 */
  resetFilters: () => {
    set({
      filters: {
        keyword: '',
        category_id: '',
        supplier_id: '',
        stock_status: '',
        is_active: '',
        per_page: 20,
      },
    })
  },
}))

export default useSparePartStore
