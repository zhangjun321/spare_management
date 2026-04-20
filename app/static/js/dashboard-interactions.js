/**
 * 仪表盘交互增强
 * 包含快捷键、快捷操作、操作反馈等功能
 */

class DashboardInteractions {
    constructor() {
        this.shortcuts = new Map();
        this.actionHistory = [];
        this.notificationQueue = [];
        this.init();
    }

    init() {
        this.setupShortcuts();
        this.setupQuickActions();
        this.setupNotifications();
        this.setupDragAndDrop();
        this.setupContextMenu();
    }

    /**
     * 设置快捷键
     */
    setupShortcuts() {
        // 定义快捷键
        this.shortcuts = new Map([
            ['r', { description: '刷新数据', action: () => this.refreshData() }],
            ['f', { description: '搜索/过滤', action: () => this.focusSearch() }],
            ['1', { description: '跳转到概览', action: () => this.scrollToSection('overview') }],
            ['2', { description: '跳转到分析', action: () => this.scrollToSection('analysis') }],
            ['3', { description: '跳转到告警', action: () => this.scrollToSection('alerts') }],
            ['?', { description: '显示快捷键帮助', action: () => this.showShortcutHelp() }],
            ['h', { description: '返回首页', action: () => window.location.href = '/home' }],
            ['e', { description: '导出数据', action: () => this.exportData() }],
            ['Escape', { description: '关闭弹窗', action: () => this.closeAllModals() }]
        ]);

        // 监听键盘事件
        document.addEventListener('keydown', (e) => {
            // 忽略输入框中的按键
            if (e.target.tagName === 'INPUT' || 
                e.target.tagName === 'TEXTAREA' || 
                e.target.isContentEditable) {
                return;
            }

            // 处理快捷键
            const key = e.key;
            const shortcut = this.shortcuts.get(key);
            
            if (shortcut) {
                e.preventDefault();
                shortcut.action();
                this.showToast(`快捷键: ${shortcut.description}`, 'info');
            }
        });
    }

    /**
     * 显示快捷键帮助
     */
    showShortcutHelp() {
        const modal = document.createElement('div');
        modal.className = 'shortcut-help-modal';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="dashboardInteractions.closeAllModals()"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>键盘快捷键</h3>
                    <button onclick="dashboardInteractions.closeAllModals()" class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="shortcut-list">
                        ${Array.from(this.shortcuts.entries()).map(([key, value]) => `
                            <div class="shortcut-item">
                                <kbd>${key}</kbd>
                                <span>${value.description}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 添加样式
        const style = document.createElement('style');
        style.textContent = `
            .shortcut-help-modal { position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 10000; }
            .modal-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); }
            .modal-content { position: relative; background: white; max-width: 500px; margin: 100px auto; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
            .modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px; border-bottom: 1px solid #e5e7eb; }
            .modal-header h3 { margin: 0; font-size: 18px; }
            .close-btn { background: none; border: none; font-size: 24px; cursor: pointer; color: #6b7280; }
            .modal-body { padding: 20px; }
            .shortcut-list { display: flex; flex-direction: column; gap: 12px; }
            .shortcut-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #f9fafb; border-radius: 8px; }
            .shortcut-item kbd { background: #fff; border: 1px solid #d1d5db; border-bottom-width: 2px; border-radius: 4px; padding: 4px 8px; font-family: monospace; font-weight: 600; }
        `;
        document.head.appendChild(style);
    }

    /**
     * 关闭所有弹窗
     */
    closeAllModals() {
        document.querySelectorAll('.shortcut-help-modal').forEach(el => el.remove());
    }

    /**
     * 刷新数据
     */
    refreshData() {
        if (window.loadDashboardData) {
            window.loadDashboardData();
        }
        this.showToast('数据已刷新', 'success');
    }

    /**
     * 聚焦搜索框
     */
    focusSearch() {
        const searchInput = document.querySelector('input[type="search"], input[placeholder*="搜索"]');
        if (searchInput) {
            searchInput.focus();
        }
    }

    /**
     * 滚动到指定区域
     */
    scrollToSection(sectionId) {
        const section = document.getElementById(sectionId) || 
                       document.querySelector(`[data-section="${sectionId}"]`);
        if (section) {
            section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    /**
     * 导出数据
     */
    exportData() {
        if (window.exportDashboardData) {
            window.exportDashboardData();
        }
    }

    /**
     * 设置快捷操作
     */
    setupQuickActions() {
        // 双击卡片进入详情
        document.addEventListener('dblclick', (e) => {
            const card = e.target.closest('.stat-card, .data-card, .quick-action-card');
            if (card) {
                this.handleCardDoubleClick(card);
            }
        });

        // 添加右键菜单触发
        document.addEventListener('contextmenu', (e) => {
            const actionable = e.target.closest('[data-context-menu]');
            if (actionable) {
                e.preventDefault();
                this.showContextMenu(e, actionable);
            }
        });
    }

    /**
     * 处理卡片双击
     */
    handleCardDoubleClick(card) {
        const cardType = card.dataset.cardType;
        if (cardType) {
            this.showToast(`进入${cardType}详情`, 'info');
        }
    }

    /**
     * 显示上下文菜单
     */
    showContextMenu(event, element) {
        // 移除现有菜单
        document.querySelectorAll('.context-menu').forEach(el => el.remove());

        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.innerHTML = `
            <div class="menu-item" data-action="refresh">刷新数据</div>
            <div class="menu-item" data-action="export">导出数据</div>
            <div class="menu-divider"></div>
            <div class="menu-item" data-action="settings">设置</div>
        `;

        menu.style.position = 'fixed';
        menu.style.left = event.clientX + 'px';
        menu.style.top = event.clientY + 'px';
        menu.style.minWidth = '160px';
        menu.style.background = 'white';
        menu.style.border = '1px solid #e5e7eb';
        menu.style.borderRadius = '8px';
        menu.style.boxShadow = '0 10px 40px rgba(0,0,0,0.15)';
        menu.style.zIndex = '10000';
        menu.style.padding = '4px 0';

        const style = document.createElement('style');
        style.textContent = `
            .menu-item { padding: 10px 16px; cursor: pointer; font-size: 14px; transition: background 0.2s; }
            .menu-item:hover { background: #f3f4f6; }
            .menu-divider { height: 1px; background: #e5e7eb; margin: 4px 0; }
        `;
        document.head.appendChild(style);

        menu.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            if (action) {
                this.handleContextAction(action);
                menu.remove();
            }
        });

        document.body.appendChild(menu);

        // 点击其他地方关闭菜单
        setTimeout(() => {
            document.addEventListener('click', function closeMenu(clickEvent) {
                if (!menu.contains(clickEvent.target)) {
                    menu.remove();
                    document.removeEventListener('click', closeMenu);
                }
            });
        }, 0);
    }

    /**
     * 处理上下文菜单操作
     */
    handleContextAction(action) {
        switch (action) {
            case 'refresh':
                this.refreshData();
                break;
            case 'export':
                this.exportData();
                break;
            case 'settings':
                this.showToast('设置功能开发中', 'info');
                break;
        }
    }

    /**
     * 设置通知系统
     */
    setupNotifications() {
        // 创建通知容器
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '10000';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.gap = '10px';
        document.body.appendChild(container);
    }

    /**
     * 显示Toast通知
     */
    showToast(message, type = 'info') {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };

        toast.style.background = 'white';
        toast.style.border = '1px solid #e5e7eb';
        toast.style.borderLeft = `4px solid ${colors[type]}`;
        toast.style.borderRadius = '8px';
        toast.style.padding = '14px 18px';
        toast.style.boxShadow = '0 4px 20px rgba(0,0,0,0.15)';
        toast.style.display = 'flex';
        toast.style.alignItems = 'center';
        toast.style.gap = '10px';
        toast.style.minWidth = '280px';
        toast.style.animation = 'slideInRight 0.3s ease-out';

        toast.innerHTML = `
            <span style="color: ${colors[type]}; font-size: 18px; font-weight: bold;">${icons[type]}</span>
            <span style="flex: 1; font-size: 14px; color: #374151;">${message}</span>
            <button onclick="this.parentElement.remove()" style="background: none; border: none; cursor: pointer; color: #9ca3af; font-size: 18px;">&times;</button>
        `;

        container.appendChild(toast);

        // 自动消失
        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease-out forwards';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    /**
     * 设置拖放功能
     */
    setupDragAndDrop() {
        let draggedElement = null;

        document.addEventListener('dragstart', (e) => {
            if (e.target.draggable) {
                draggedElement = e.target;
                e.target.style.opacity = '0.5';
            }
        });

        document.addEventListener('dragend', (e) => {
            if (draggedElement) {
                draggedElement.style.opacity = '1';
                draggedElement = null;
            }
        });

        document.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        document.addEventListener('drop', (e) => {
            e.preventDefault();
            // 处理拖放逻辑
        });
    }

    /**
     * 设置右键菜单
     */
    setupContextMenu() {
        // 已在 setupQuickActions 中处理
    }

    /**
     * 记录操作历史
     */
    recordAction(actionType, details = {}) {
        this.actionHistory.push({
            type: actionType,
            details: details,
            timestamp: new Date().toISOString()
        });

        // 保持历史记录在合理范围内
        if (this.actionHistory.length > 100) {
            this.actionHistory.shift();
        }
    }

    /**
     * 获取操作历史
     */
    getActionHistory() {
        return this.actionHistory;
    }
}

// 添加所需的动画
const additionalStyles = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes fadeOut {
        from {
            opacity: 1;
        }
        to {
            opacity: 0;
        }
    }
`;

const styleEl = document.createElement('style');
styleEl.textContent = additionalStyles;
document.head.appendChild(styleEl);

// 全局实例
const dashboardInteractions = new DashboardInteractions();

// 导出使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardInteractions;
}
