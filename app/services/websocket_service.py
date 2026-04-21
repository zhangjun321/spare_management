"""
WebSocket 实时通知服务
提供库存变更、订单状态、设备监控等实时推送功能
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
from flask import request, session
import json
from datetime import datetime
import random

# 全局 SocketIO 实例
socketio = None

def init_socketio(app):
    """初始化 SocketIO"""
    global socketio
    
    # 配置 SocketIO
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",  # 允许跨域
        async_mode='threading',    # 使用线程模式
        logger=False,              # 生产环境关闭日志
        engineio_logger=False
    )
    
    # 注册事件处理器
    register_socketio_events()
    
    return socketio


def register_socketio_events():
    """注册 SocketIO 事件处理器"""
    
    @socketio.on('connect')
    def handle_connect():
        """客户端连接"""
        print(f'客户端连接：{request.sid}')
        
        # 如果用户已登录，加入个人房间
        if current_user.is_authenticated:
            join_room(f'user_{current_user.id}')
            print(f'用户 {current_user.id} 加入房间')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """客户端断开连接"""
        print(f'客户端断开：{request.sid}')
        
        # 离开所有房间
        if current_user.is_authenticated:
            leave_room(f'user_{current_user.id}')
    
    @socketio.on('join_warehouse')
    def handle_join_warehouse(data):
        """加入仓库房间（监控特定仓库）"""
        warehouse_id = data.get('warehouse_id')
        if warehouse_id:
            join_room(f'warehouse_{warehouse_id}')
            print(f'用户加入仓库房间：warehouse_{warehouse_id}')
    
    @socketio.on('leave_warehouse')
    def handle_leave_warehouse(data):
        """离开仓库房间"""
        warehouse_id = data.get('warehouse_id')
        if warehouse_id:
            leave_room(f'warehouse_{warehouse_id}')
            print(f'用户离开仓库房间：warehouse_{warehouse_id}')
    
    @socketio.on('join_equipment')
    def handle_join_equipment(data):
        """加入设备监控房间（监控特定设备）"""
        equipment_id = data.get('equipment_id')
        if equipment_id:
            join_room(f'equipment_{equipment_id}')
            print(f'用户加入设备监控房间：equipment_{equipment_id}')
            # 发送当前设备状态
            send_equipment_status_update(equipment_id)
    
    @socketio.on('leave_equipment')
    def handle_leave_equipment(data):
        """离开设备监控房间"""
        equipment_id = data.get('equipment_id')
        if equipment_id:
            leave_room(f'equipment_{equipment_id}')
            print(f'用户离开设备监控房间：equipment_{equipment_id}')


def send_notification(user_id, notification_type, data):
    """
    发送通知给用户
    
    Args:
        user_id: 用户 ID
        notification_type: 通知类型
            - inventory_change: 库存变更
            - order_status: 订单状态
            - low_stock: 低库存预警
            - system: 系统通知
        data: 通知数据
    """
    if not socketio:
        return
    
    notification = {
        'type': notification_type,
        'data': data,
        'timestamp': datetime.utcnow().isoformat(),
        'read': False
    }
    
    # 发送给用户
    socketio.emit('notification', notification, room=f'user_{user_id}')


def send_inventory_change(warehouse_id, spare_part_id, change_type, quantity_before, quantity_after):
    """
    发送库存变更通知
    
    Args:
        warehouse_id: 仓库 ID
        spare_part_id: 备件 ID
        change_type: 变更类型 (inbound/outbound/adjustment)
        quantity_before: 变更前数量
        quantity_after: 变更后数量
    """
    if not socketio:
        return
    
    data = {
        'warehouse_id': warehouse_id,
        'spare_part_id': spare_part_id,
        'change_type': change_type,
        'quantity_before': quantity_before,
        'quantity_after': quantity_after,
        'change_amount': quantity_after - quantity_before
    }
    
    # 通知监控该仓库的所有用户
    socketio.emit('inventory_change', data, room=f'warehouse_{warehouse_id}')
    
    # 检查是否需要低库存预警
    if quantity_after < 10:  # 低库存阈值
        send_low_stock_warning(warehouse_id, spare_part_id, quantity_after)


def send_low_stock_warning(warehouse_id, spare_part_id, current_quantity):
    """
    发送低库存预警
    
    Args:
        warehouse_id: 仓库 ID
        spare_part_id: 备件 ID
        current_quantity: 当前库存
    """
    if not socketio:
        return
    
    data = {
        'warehouse_id': warehouse_id,
        'spare_part_id': spare_part_id,
        'current_quantity': current_quantity,
        'warning_level': 'low' if current_quantity < 10 else 'critical',
        'message': f'备件 {spare_part_id} 库存不足，当前库存：{current_quantity}'
    }
    
    # 发送给仓库管理员
    from app.models.warehouse import Warehouse
    warehouse = Warehouse.query.get(warehouse_id)
    if warehouse and warehouse.manager_id:
        send_notification(warehouse.manager_id, 'low_stock', data)


def send_order_status_update(user_id, order_id, order_type, old_status, new_status):
    """
    发送订单状态更新通知
    
    Args:
        user_id: 用户 ID
        order_id: 订单 ID
        order_type: 订单类型 (inbound/outbound)
        old_status: 旧状态
        new_status: 新状态
    """
    if not socketio:
        return
    
    data = {
        'order_id': order_id,
        'order_type': order_type,
        'old_status': old_status,
        'new_status': new_status,
        'message': f'订单 {order_id} 状态已更新：{old_status} → {new_status}'
    }
    
    send_notification(user_id, 'order_status', data)


def broadcast_system_message(message, level='info'):
    """
    广播系统消息
    
    Args:
        message: 消息内容
        level: 消息级别 (info/warning/error)
    """
    if not socketio:
        return
    
    data = {
        'message': message,
        'level': level,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    socketio.emit('system_message', data)


# ============================================
# 设备管理相关的通知函数
# ============================================

def send_equipment_status_update(equipment_id, status_data=None):
    """
    发送设备状态更新通知
    
    Args:
        equipment_id: 设备 ID
        status_data: 状态数据 (可选，否则生成模拟数据)
    """
    if not socketio:
        return
    
    # 如果没有提供数据，生成模拟数据
    if not status_data:
        status_data = {
            'equipment_id': equipment_id,
            'is_running': random.choice([True, True, False]),
            'temperature': round(25 + random.uniform(-2, 5), 1),
            'vibration': round(1.5 + random.uniform(-0.5, 1.5), 2),
            'voltage': 220 + round(random.uniform(-5, 5), 1),
            'current': round(10 + random.uniform(-2, 5), 1),
            'today_scans': random.randint(100, 200),
            'total_scans': random.randint(10000, 20000),
            'health_score': round(75 + random.uniform(-10, 15), 1),
            'timestamp': datetime.now().isoformat()
        }
    
    # 发送给监控该设备的所有用户
    socketio.emit('equipment_status', status_data, room=f'equipment_{equipment_id}')


def send_equipment_alert(equipment_id, alert_type, alert_data):
    """
    发送设备告警通知
    
    Args:
        equipment_id: 设备 ID
        alert_type: 告警类型 (critical/warning/info)
        alert_data: 告警数据
    """
    if not socketio:
        return
    
    alert = {
        'equipment_id': equipment_id,
        'alert_type': alert_type,
        'data': alert_data,
        'timestamp': datetime.now().isoformat()
    }
    
    # 发送给设备监控房间
    socketio.emit('equipment_alert', alert, room=f'equipment_{equipment_id}')
    
    # 如果是严重告警，同时发送给设备负责人
    if alert_type in ['critical', 'warning']:
        try:
            from app.models.equipment import Equipment
            equipment = Equipment.query.get(equipment_id)
            if equipment and equipment.responsible_person:
                # 发送给负责人（这里可以根据实际情况查找用户ID）
                notification_data = {
                    'equipment_id': equipment_id,
                    'equipment_name': equipment.name,
                    'alert_type': alert_type,
                    'alert_message': alert_data.get('message', '')
                }
                socketio.emit('equipment_alert_notification', notification_data)
        except Exception:
            pass


def send_maintenance_task_update(equipment_id, task_id, task_data):
    """
    发送维护任务更新通知
    
    Args:
        equipment_id: 设备 ID
        task_id: 任务 ID
        task_data: 任务数据
    """
    if not socketio:
        return
    
    data = {
        'equipment_id': equipment_id,
        'task_id': task_id,
        'task_data': task_data,
        'timestamp': datetime.now().isoformat()
    }
    
    # 发送给设备监控房间
    socketio.emit('maintenance_task_update', data, room=f'equipment_{equipment_id}')


def send_health_score_update(equipment_id, health_data):
    """
    发送健康评分更新通知
    
    Args:
        equipment_id: 设备 ID
        health_data: 健康数据
    """
    if not socketio:
        return
    
    data = {
        'equipment_id': equipment_id,
        'health_data': health_data,
        'timestamp': datetime.now().isoformat()
    }
    
    # 发送给设备监控房间
    socketio.emit('health_score_update', data, room=f'equipment_{equipment_id}')


def send_iot_data_stream(equipment_id, iot_data):
    """
    发送IoT数据流
    
    Args:
        equipment_id: 设备 ID
        iot_data: IoT数据
    """
    if not socketio:
        return
    
    data = {
        'equipment_id': equipment_id,
        'iot_data': iot_data,
        'timestamp': datetime.now().isoformat()
    }
    
    # 发送给设备监控房间
    socketio.emit('iot_data_stream', data, room=f'equipment_{equipment_id}')


def broadcast_equipment_dashboard_update(equipment_list):
    """
    广播设备仪表板更新（适用于设备列表页面）
    
    Args:
        equipment_list: 设备列表数据
    """
    if not socketio:
        return
    
    data = {
        'equipment_list': equipment_list,
        'timestamp': datetime.now().isoformat()
    }
    
    socketio.emit('dashboard_update', data)


# ============================================
# 原有的库存相关函数（保持不变）
# ============================================

# 装饰器：自动发送库存变更通知
def notify_inventory_change(func):
    """
    库存变更通知装饰器
    
    用法:
    @notify_inventory_change
    def create_inbound_order(data):
        ...
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 执行原函数
        result = func(*args, **kwargs)
        
        # 如果成功，发送通知
        if result and isinstance(result, dict):
            if result.get('success'):
                # 从结果中提取信息
                warehouse_id = result.get('warehouse_id')
                spare_part_id = result.get('spare_part_id')
                if warehouse_id and spare_part_id:
                    send_inventory_change(
                        warehouse_id,
                        spare_part_id,
                        'inbound',
                        result.get('quantity_before', 0),
                        result.get('quantity_after', 0)
                    )
        
        return result
    
    return wrapper
