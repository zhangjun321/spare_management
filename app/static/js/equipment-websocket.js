/**
 * 设备管理 WebSocket 客户端
 * 提供实时设备监控、告警通知等功能
 */

class EquipmentWebSocketClient {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.currentEquipmentId = null;
        this.eventListeners = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 3000;
    }

    /**
     * 初始化连接
     */
    connect() {
        return new Promise((resolve, reject) => {
            try {
                // 使用 Socket.io 客户端
                this.socket = io();

                this.socket.on('connect', () => {
                    console.log('✅ WebSocket 连接成功');
                    this.connected = true;
                    this.reconnectAttempts = 0;
                    this.emit('connected', {});
                    resolve();
                });

                this.socket.on('disconnect', () => {
                    console.log('❌ WebSocket 连接断开');
                    this.connected = false;
                    this.emit('disconnected', {});
                    this.attemptReconnect();
                });

                this.socket.on('error', (error) => {
                    console.error('❌ WebSocket 错误:', error);
                    this.emit('error', { error });
                    reject(error);
                });

                // 设备相关事件
                this.socket.on('equipment_status', (data) => {
                    console.log('📡 设备状态更新:', data);
                    this.emit('equipment_status', data);
                });

                this.socket.on('equipment_alert', (data) => {
                    console.log('⚠️ 设备告警:', data);
                    this.emit('equipment_alert', data);
                    this.showNotification(data);
                });

                this.socket.on('equipment_alert_notification', (data) => {
                    console.log('🔔 设备告警通知:', data);
                    this.emit('equipment_alert_notification', data);
                    this.showAlertNotification(data);
                });

                this.socket.on('maintenance_task_update', (data) => {
                    console.log('🔧 维护任务更新:', data);
                    this.emit('maintenance_task_update', data);
                });

                this.socket.on('health_score_update', (data) => {
                    console.log('❤️ 健康评分更新:', data);
                    this.emit('health_score_update', data);
                });

                this.socket.on('iot_data_stream', (data) => {
                    console.log('📊 IoT数据流:', data);
                    this.emit('iot_data_stream', data);
                });

                this.socket.on('dashboard_update', (data) => {
                    console.log('📈 仪表板更新:', data);
                    this.emit('dashboard_update', data);
                });

            } catch (error) {
                console.error('❌ 连接初始化失败:', error);
                reject(error);
            }
        });
    }

    /**
     * 尝试重新连接
     */
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('❌ 重连次数已达上限');
            return;
        }

        this.reconnectAttempts++;
        console.log(`🔄 尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

        setTimeout(() => {
            this.connect();
        }, this.reconnectInterval);
    }

    /**
     * 断开连接
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.connected = false;
        }
    }

    /**
     * 加入设备监控
     */
    joinEquipment(equipmentId) {
        this.currentEquipmentId = equipmentId;
        this.socket.emit('join_equipment', { equipment_id: equipmentId });
        console.log(`📱 加入设备监控: ${equipmentId}`);
    }

    /**
     * 离开设备监控
     */
    leaveEquipment(equipmentId) {
        if (this.currentEquipmentId === equipmentId) {
            this.currentEquipmentId = null;
        }
        this.socket.emit('leave_equipment', { equipment_id: equipmentId });
        console.log(`📵 离开设备监控: ${equipmentId}`);
    }

    /**
     * 加入仓库监控
     */
    joinWarehouse(warehouseId) {
        this.socket.emit('join_warehouse', { warehouse_id: warehouseId });
        console.log(`🏠 加入仓库监控: ${warehouseId}`);
    }

    /**
     * 离开仓库监控
     */
    leaveWarehouse(warehouseId) {
        this.socket.emit('leave_warehouse', { warehouse_id: warehouseId });
        console.log(`🏚️  离开仓库监控: ${warehouseId}`);
    }

    /**
     * 添加事件监听器
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    /**
     * 移除事件监听器
     */
    off(event, callback) {
        if (!this.eventListeners.has(event)) return;
        
        const callbacks = this.eventListeners.get(event);
        const index = callbacks.indexOf(callback);
        if (index !== -1) {
            callbacks.splice(index, 1);
        }
    }

    /**
     * 触发事件
     */
    emit(event, data) {
        if (!this.eventListeners.has(event)) return;
        
        this.eventListeners.get(event).forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`❌ 事件处理错误 [${event}]:`, error);
            }
        });
    }

    /**
     * 显示通知
     */
    showNotification(data) {
        const { alert_type, data: alertData } = data;
        
        let title = '设备通知';
        let bgColor = '#3B82F6'; // blue
        
        switch (alert_type) {
            case 'critical':
                title = '⚠️ 严重告警';
                bgColor = '#EF4444'; // red
                break;
            case 'warning':
                title = '⚠️ 警告';
                bgColor = '#F59E0B'; // orange
                break;
            case 'info':
                title = 'ℹ️ 信息';
                bgColor = '#3B82F6'; // blue
                break;
        }
        
        this.createToast(title, alertData.message || '设备状态变更', bgColor);
    }

    /**
     * 显示告警通知
     */
    showAlertNotification(data) {
        const { equipment_name, alert_type, alert_message } = data;
        
        let title = '设备告警';
        let bgColor = '#3B82F6';
        
        if (alert_type === 'critical') {
            title = '🚨 严重设备告警';
            bgColor = '#EF4444';
        } else if (alert_type === 'warning') {
            title = '⚠️ 设备警告';
            bgColor = '#F59E0B';
        }
        
        this.createToast(title, `${equipment_name}: ${alert_message}`, bgColor);
    }

    /**
     * 创建Toast通知
     */
    createToast(title, message, bgColor) {
        // 检查是否已有Toast容器
        let container = document.getElementById('equipment-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'equipment-toast-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(container);
        }

        // 创建Toast
        const toast = document.createElement('div');
        toast.style.cssText = `
            background: white;
            border-left: 4px solid ${bgColor};
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-width: 300px;
            animation: slideInRight 0.3s ease-out;
        `;

        toast.innerHTML = `
            <div style="font-weight: bold; color: ${bgColor};">${title}</div>
            <div style="color: #4B5563;">${message}</div>
            <button onclick="this.parentElement.remove()" style="
                position: absolute;
                top: 8px;
                right: 8px;
                background: none;
                border: none;
                cursor: pointer;
                font-size: 18px;
                color: #9CA3AF;
            ">×</button>
        `;

        container.appendChild(toast);

        // 自动消失
        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease-out forwards';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
}

// 添加CSS动画
if (!document.getElementById('equipment-websocket-styles')) {
    const style = document.createElement('style');
    style.id = 'equipment-websocket-styles';
    style.textContent = `
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(100px); }
            to { opacity: 1; transform: translateX(0); }
        }
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
    `;
    document.head.appendChild(style);
}

// 全局实例
window.equipmentWebSocket = new EquipmentWebSocketClient();

// 页面加载完成后自动连接
document.addEventListener('DOMContentLoaded', () => {
    // 可以在这里初始化连接
    // 或者在需要时手动调用
});
