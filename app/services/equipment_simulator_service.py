"""
设备数据模拟器服务
提供模拟设备数据推送功能
"""

from datetime import datetime, timedelta
import random
from app.extensions import db
from app.models.equipment import Equipment

def simulate_equipment_data(equipment_id):
    """
    模拟设备数据
    
    Args:
        equipment_id: 设备 ID
    
    Returns:
        模拟的设备数据
    """
    # 生成随机数据（有一定的趋势性）
    is_running = random.choice([True, True, False])
    
    # 温度：正常范围25-30度
    base_temp = 27.5
    temp_variation = random.uniform(-2, 5)
    temperature = round(base_temp + temp_variation, 1)
    
    # 振动：正常范围1.0-3.0
    base_vib = 1.8
    vib_variation = random.uniform(-0.6, 1.5)
    vibration = round(base_vib + vib_variation, 2)
    
    # 电压：220V±5V
    voltage = round(220 + random.uniform(-5, 5), 1)
    
    # 电流：10A±5A
    current = round(10 + random.uniform(-2, 5), 1)
    
    # 今日检测数（递增）
    today_scans = random.randint(100, 200)
    total_scans = random.randint(10000, 20000)
    
    # 健康评分
    health_base = 78
    health_variation = random.uniform(-8, 12)
    health_score = round(max(50, min(98, health_base + health_variation)), 1)
    
    return {
        'equipment_id': equipment_id,
        'is_running': is_running,
        'temperature': temperature,
        'vibration': vibration,
        'voltage': voltage,
        'current': current,
        'today_scans': today_scans,
        'total_scans': total_scans,
        'health_score': health_score,
        'timestamp': datetime.now().isoformat()
    }


def simulate_alert(equipment_id):
    """
    模拟设备告警
    
    Args:
        equipment_id: 设备 ID
    
    Returns:
        告警数据，或 None（无告警）
    """
    # 5%的概率生成告警
    if random.random() > 0.95:
        alert_types = ['warning', 'warning', 'critical']
        alert_type = random.choice(alert_types)
        
        alert_messages = {
            'warning': [
                '温度略高于正常范围',
                '振动值接近警戒值',
                '建议进行预防性维护'
            ],
            'critical': [
                '温度超过安全阈值！',
                '振动异常！需要立即检查',
                '检测到潜在故障风险！'
            ]
        }
        
        message = random.choice(alert_messages[alert_type])
        
        return {
            'alert_type': alert_type,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
    
    return None


def simulate_health_data(equipment_id):
    """
    模拟健康评分数据
    
    Args:
        equipment_id: 设备 ID
    
    Returns:
        健康数据
    """
    health_score = round(75 + random.uniform(-10, 15), 1)
    
    # 确定健康等级
    if health_score >= 90:
        health_level = 'excellent'
    elif health_score >= 80:
        health_level = 'good'
    elif health_score >= 70:
        health_level = 'normal'
    elif health_score >= 60:
        health_level = 'warning'
    else:
        health_level = 'critical'
    
    return {
        'health_score': health_score,
        'health_level': health_level,
        'reliability_score': round(health_score * 0.95, 1),
        'performance_score': round(health_score * 0.9, 1),
        'maintenance_score': round(health_score * 0.85, 1),
        'risk_level': health_level,
        'timestamp': datetime.now().isoformat()
    }


def send_equipment_update(equipment_id):
    """
    发送设备更新通知（WebSocket）
    
    Args:
        equipment_id: 设备 ID
    """
    try:
        from app.services.websocket_service import (
            send_equipment_status_update,
            send_equipment_alert,
            send_health_score_update
        )
        
        # 发送设备状态
        status_data = simulate_equipment_data(equipment_id)
        send_equipment_status_update(equipment_id, status_data)
        
        # 发送健康评分
        health_data = simulate_health_data(equipment_id)
        send_health_score_update(equipment_id, health_data)
        
        # 检查是否需要发送告警
        alert = simulate_alert(equipment_id)
        if alert:
            send_equipment_alert(
                equipment_id,
                alert['alert_type'],
                {'message': alert['message']}
            )
            
        return True
        
    except Exception as e:
        print(f"发送设备更新失败: {e}")
        return False


def start_equipment_monitoring(equipment_id):
    """
    启动设备监控（后台任务）
    
    注意：这是一个示例，实际应用中应该使用
    Celery 或 APScheduler 等任务调度器
    """
    print(f"启动设备监控: {equipment_id}")
    send_equipment_update(equipment_id)
    return True


def get_all_active_equipments():
    """
    获取所有活跃设备
    
    Returns:
        设备ID列表
    """
    try:
        equipments = Equipment.query.filter_by(is_active=True).all()
        return [eq.id for eq in equipments]
    except Exception as e:
        print(f"获取活跃设备失败: {e}")
        return []


def broadcast_equipment_dashboard_data():
    """
    广播设备仪表板数据
    
    Returns:
        设备数据列表
    """
    try:
        from app.services.websocket_service import broadcast_equipment_dashboard_update
        
        equipments = Equipment.query.filter_by(is_active=True).all()
        
        dashboard_data = []
        for eq in equipments:
            dashboard_data.append({
                'id': eq.id,
                'equipment_code': eq.equipment_code,
                'name': eq.name,
                'status': eq.status,
                'health_score': round(75 + random.uniform(-10, 15), 1)
            })
        
        broadcast_equipment_dashboard_update(dashboard_data)
        
        return dashboard_data
        
    except Exception as e:
        print(f"广播仪表板数据失败: {e}")
        return []
