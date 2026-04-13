"""
WebSocket 实时通知服务
提供库存变更、订单状态等实时推送功能
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
from flask import session
import json
from datetime import datetime

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
