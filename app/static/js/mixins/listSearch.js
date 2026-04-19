/**
 * 列表搜索通用混入
 * 为所有列表页面提供搜索功能
 */

export const listSearchMixin = {
    data() {
        return {
            // 搜索表单
            searchForm: {
                keyword: '',
                // 其他搜索字段在组件中定义
            },
            // 是否显示搜索面板
            showSearch: true,
            // 是否显示关键词搜索
            showKeywordSearch: true,
            // 列表数据
            list: [],
            // 加载状态
            loading: false,
            // 分页
            pagination: {
                page: 1,
                pageSize: 10,
                total: 0
            }
        };
    },
    
    methods: {
        /**
         * 搜索
         */
        handleSearch() {
            this.pagination.page = 1;
            this.fetchList();
        },
        
        /**
         * 重置搜索
         */
        handleReset() {
            this.searchForm = {
                keyword: ''
            };
            this.handleSearch();
        },
        
        /**
         * 分页变化
         */
        handlePageChange(page) {
            this.pagination.page = page;
            this.fetchList();
        },
        
        /**
         * 每页数量变化
         */
        handlePageSizeChange(size) {
            this.pagination.pageSize = size;
            this.pagination.page = 1;
            this.fetchList();
        },
        
        /**
         * 获取列表数据（需要子类实现）
         */
        fetchList() {
            console.warn('fetchList method should be implemented in child component');
        }
    }
};
