/**
 * 仪表盘性能优化工具
 * 包含懒加载、数据缓存、虚拟滚动等优化功能
 */

class DashboardOptimizer {
    constructor() {
        this.dataCache = new Map();
        this.cacheTimeout = 30000; // 30秒缓存
        this.loadedElements = new WeakSet();
        this.observer = null;
        this.requestQueue = [];
        this.isProcessingQueue = false;
        this.init();
    }

    init() {
        this.setupIntersectionObserver();
        this.setupPerformanceMonitoring();
    }

    /**
     * 设置交叉观察器（用于懒加载）
     */
    setupIntersectionObserver() {
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver(
                (entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            this.lazyLoadElement(entry.target);
                            this.observer.unobserve(entry.target);
                        }
                    });
                },
                { rootMargin: '200px' } // 提前200px加载
            );
        }
    }

    /**
     * 懒加载元素
     */
    lazyLoadElement(element) {
        if (this.loadedElements.has(element)) return;
        
        this.loadedElements.add(element);
        
        // 处理延迟加载的图表
        if (element.dataset.chartId) {
            this.loadChart(element.dataset.chartId);
        }
        
        // 处理图片懒加载
        if (element.dataset.src) {
            element.src = element.dataset.src;
        }
        
        // 添加淡入动画
        element.classList.add('fade-in');
    }

    /**
     * 注册需要懒加载的元素
     */
    registerLazyElement(element) {
        if (this.observer) {
            this.observer.observe(element);
        } else {
            // 降级方案：直接加载
            this.lazyLoadElement(element);
        }
    }

    /**
     * 缓存数据
     */
    setCache(key, data) {
        this.dataCache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    /**
     * 获取缓存数据
     */
    getCache(key) {
        const cached = this.dataCache.get(key);
        if (cached && (Date.now() - cached.timestamp) < this.cacheTimeout) {
            return cached.data;
        }
        return null;
    }

    /**
     * 带缓存的API请求
     */
    async fetchWithCache(url, options = {}) {
        const cacheKey = url + JSON.stringify(options);
        const cached = this.getCache(cacheKey);
        
        if (cached) {
            return cached;
        }
        
        // 添加到请求队列
        return new Promise((resolve, reject) => {
            this.requestQueue.push({ url, options, resolve, reject });
            this.processQueue();
        });
    }

    /**
     * 处理请求队列（避免并发请求过多）
     */
    async processQueue() {
        if (this.isProcessingQueue || this.requestQueue.length === 0) return;
        
        this.isProcessingQueue = true;
        
        while (this.requestQueue.length > 0) {
            const { url, options, resolve, reject } = this.requestQueue.shift();
            
            try {
                const response = await fetch(url, options);
                const data = await response.json();
                
                // 缓存结果
                const cacheKey = url + JSON.stringify(options);
                this.setCache(cacheKey, data);
                
                resolve(data);
            } catch (error) {
                reject(error);
            }
            
            // 小延迟避免拥塞
            await this.delay(50);
        }
        
        this.isProcessingQueue = false;
    }

    /**
     * 延迟函数
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * 防抖函数
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * 节流函数
     */
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * 设置性能监控
     */
    setupPerformanceMonitoring() {
        if ('performance' in window) {
            // 监控页面加载性能
            window.addEventListener('load', () => {
                const timing = performance.timing;
                const loadTime = timing.loadEventEnd - timing.navigationStart;
                console.log(`页面加载时间: ${loadTime}ms`);
            });
        }
    }

    /**
     * 虚拟滚动列表（用于大数据列表）
     */
    createVirtualList(container, items, itemHeight = 50) {
        const visibleCount = Math.ceil(container.clientHeight / itemHeight) + 2;
        let startIndex = 0;
        
        const update = () => {
            const scrollTop = container.scrollTop;
            startIndex = Math.floor(scrollTop / itemHeight);
            const endIndex = Math.min(startIndex + visibleCount, items.length);
            
            // 只渲染可见区域的项目
            const visibleItems = items.slice(startIndex, endIndex);
            
            // 更新内容
            container.innerHTML = visibleItems.map((item, i) => `
                <div style="height: ${itemHeight}px; transform: translateY(${startIndex * itemHeight}px)">
                    ${item.content}
                </div>
            `).join('');
        };
        
        container.addEventListener('scroll', this.throttle(update, 16));
        update();
    }

    /**
     * 加载图表（带优化）
     */
    async loadChart(chartId) {
        // 图表加载优化逻辑
        console.log(`Loading chart: ${chartId}`);
    }

    /**
     * 批量更新DOM
     */
    batchUpdate(callback) {
        if ('requestAnimationFrame' in window) {
            requestAnimationFrame(callback);
        } else {
            setTimeout(callback, 0);
        }
    }

    /**
     * 清理资源
     */
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
        this.dataCache.clear();
        this.requestQueue = [];
    }
}

// 全局实例
const dashboardOptimizer = new DashboardOptimizer();

// 导出使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardOptimizer;
}
