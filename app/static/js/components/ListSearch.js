/**
 * 通用列表搜索组件
 * 可用于所有列表页面
 */

const ListSearchComponent = {
    template: `
        <div class="list-search-container">
            <!-- 搜索面板 -->
            <el-card shadow="hover" class="search-card">
                <el-form :inline="true" :model="searchForm" size="default">
                    <!-- 自定义搜索字段插槽 -->
                    <slot name="search-fields"></slot>
                    
                    <!-- 关键词搜索 -->
                    <el-form-item v-if="showKeyword">
                        <el-input 
                            v-model="searchForm.keyword" 
                            :placeholder="keywordPlaceholder"
                            clearable
                            @keyup.enter="handleSearch"
                            style="width: 250px;">
                            <template #prefix>
                                <el-icon><Search /></el-icon>
                            </template>
                        </el-input>
                    </el-form-item>
                    
                    <!-- 搜索按钮 -->
                    <el-form-item>
                        <el-button type="primary" @click="handleSearch" :icon="Search">
                            搜索
                        </el-button>
                    </el-form-item>
                    <el-form-item>
                        <el-button @click="handleReset" :icon="Refresh">
                            重置
                        </el-button>
                    </el-form-item>
                    <el-form-item v-if="showExport">
                        <el-button @click="handleExport" :icon="Download">
                            导出
                        </el-button>
                    </el-form-item>
                </el-form>
            </el-card>
            
            <!-- 数据表格 -->
            <el-card shadow="hover" class="table-card" style="margin-top: 20px;">
                <el-table 
                    :data="tableData" 
                    v-loading="loading"
                    stripe
                    border
                    style="width: 100%;"
                    :default-sort="defaultSort"
                    @sort-change="handleSortChange">
                    
                    <!-- 自定义列插槽 -->
                    <slot name="columns" :data="tableData"></slot>
                    
                    <!-- 操作列 -->
                    <el-table-column v-if="showActions" label="操作" fixed="right" :width="actionsWidth">
                        <template #default="scope">
                            <slot name="actions" :row="scope.row" :$index="scope.$index"></slot>
                        </template>
                    </el-table-column>
                </el-table>
                
                <!-- 分页 -->
                <el-pagination
                    v-model:current-page="pagination.page"
                    v-model:page-size="pagination.pageSize"
                    :page-sizes="pageSizes"
                    :total="pagination.total"
                    layout="total, sizes, prev, pager, next, jumper"
                    @size-change="handleSizeChange"
                    @current-change="handlePageChange"
                    style="margin-top: 20px; justify-content: flex-end;">
                </el-pagination>
            </el-card>
        </div>
    `,
    
    props: {
        // API 端点
        apiUrl: {
            type: String,
            required: true
        },
        // 是否显示关键词搜索
        showKeyword: {
            type: Boolean,
            default: true
        },
        // 关键词占位符
        keywordPlaceholder: {
            type: String,
            default: '搜索关键词...'
        },
        // 是否显示导出按钮
        showExport: {
            type: Boolean,
            default: false
        },
        // 是否显示操作列
        showActions: {
            type: Boolean,
            default: true
        },
        // 操作列宽度
        actionsWidth: {
            type: Number,
            default: 200
        },
        // 默认分页大小
        defaultPageSize: {
            type: Number,
            default: 20
        },
        // 分页大小选项
        pageSizes: {
            type: Array,
            default: () => [10, 20, 50, 100]
        },
        // 默认排序
        defaultSort: {
            type: Object,
            default: () => ({ prop: 'id', order: 'descending' })
        },
        // 额外的查询参数
        extraParams: {
            type: Object,
            default: () => ({})
        }
    },
    
    data() {
        return {
            searchForm: {
                keyword: ''
            },
            tableData: [],
            loading: false,
            pagination: {
                page: 1,
                pageSize: this.defaultPageSize,
                total: 0
            },
            sortField: 'id',
            sortOrder: 'desc'
        };
    },
    
    methods: {
        // 获取列表
        async fetchList() {
            this.loading = true;
            try {
                const params = new URLSearchParams({
                    page: this.pagination.page,
                    per_page: this.pagination.pageSize,
                    keyword: this.searchForm.keyword,
                    sort_field: this.sortField,
                    sort_order: this.sortOrder,
                    ...this.extraParams
                });
                
                const response = await fetch(`${this.apiUrl}?${params}`);
                const result = await response.json();
                
                if (result.code === 200) {
                    this.tableData = result.data.list;
                    this.pagination.total = result.data.total;
                    this.pagination.page = result.data.page;
                    this.pagination.pages = result.data.pages;
                    
                    this.$emit('data-loaded', result.data);
                } else {
                    ElementPlus.ElMessage.error(result.message || '获取数据失败');
                }
            } catch (error) {
                console.error('获取列表失败:', error);
                ElementPlus.ElMessage.error('网络错误，请稍后重试');
            } finally {
                this.loading = false;
            }
        },
        
        // 搜索
        handleSearch() {
            this.pagination.page = 1;
            this.fetchList();
        },
        
        // 重置
        handleReset() {
            this.searchForm.keyword = '';
            this.sortField = 'id';
            this.sortOrder = 'desc';
            this.pagination.page = 1;
            this.fetchList();
        },
        
        // 分页
        handlePageChange(page) {
            this.pagination.page = page;
            this.fetchList();
        },
        
        handleSizeChange(size) {
            this.pagination.pageSize = size;
            this.pagination.page = 1;
            this.fetchList();
        },
        
        // 排序
        handleSortChange({ prop, order }) {
            this.sortField = prop;
            this.sortOrder = order === 'ascending' ? 'asc' : 'desc';
            this.fetchList();
        },
        
        // 导出
        handleExport() {
            this.$emit('export');
        },
        
        // 刷新
        refresh() {
            this.fetchList();
        }
    },
    
    mounted() {
        this.fetchList();
    }
};

// 导出组件
if (typeof window !== 'undefined') {
    window.ListSearchComponent = ListSearchComponent;
}

export default ListSearchComponent;
