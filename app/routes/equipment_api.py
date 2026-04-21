"""
设备管理高级API - 符合RESTful规范和工业4.0标准
包含IoT数据、预测性维护、健康指数、性能分析等功能
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models.equipment import Equipment
from app.models.equipment_advanced import (
    EquipmentHealthIndex,
    EquipmentIotData,
    EquipmentPredictiveMaintenance,
    EquipmentPerformanceMetric,
    EquipmentComponent,
    EquipmentMaintenanceTask,
    EquipmentDocument
)
from app.extensions import db
from datetime import datetime, timedelta, date
from sqlalchemy import func, or_, and_
import json

equipment_api_bp = Blueprint('equipment_api', __name__, url_prefix='/api/equipment')


# ==================== 健康指数API ====================
@equipment_api_bp.route('/<int:id>/health/current')
@login_required
def get_current_health(id):
    """获取设备当前健康状况"""
    equipment = Equipment.query.get_or_404(id)

    latest_health = EquipmentHealthIndex.query.filter_by(equipment_id=id).order_by(
        EquipmentHealthIndex.record_date.desc()
    ).first()

    if not latest_health:
        # 计算并创建初始健康记录
        score = EquipmentHealthIndex.calculate_health_score(equipment)
        latest_health = EquipmentHealthIndex(
            equipment_id=id,
            health_score=score,
            reliability_score=score * 0.95,
            performance_score=score * 0.9,
            maintenance_score=score * 0.85,
            health_level=_determine_health_level(score),
            risk_level=_determine_risk_level(score),
            risk_score=100 - score,
            mtbf_prediction=8000,
            rul_prediction=180,
            failure_risk=round((100 - score) / 100 * 30, 2)
        )
        db.session.add(latest_health)
        db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'health_score': float(latest_health.health_score) if latest_health.health_score else 0,
            'health_level': latest_health.health_level,
            'reliability_score': float(latest_health.reliability_score) if latest_health.reliability_score else 0,
            'performance_score': float(latest_health.performance_score) if latest_health.performance_score else 0,
            'maintenance_score': float(latest_health.maintenance_score) if latest_health.maintenance_score else 0,
            'risk_level': latest_health.risk_level,
            'risk_score': float(latest_health.risk_score) if latest_health.risk_score else 0,
            'mtbf_prediction': latest_health.mtbf_prediction,
            'rul_prediction': latest_health.rul_prediction,
            'failure_risk': float(latest_health.failure_risk) if latest_health.failure_risk else 0
        }
    })


@equipment_api_bp.route('/<int:id>/health/history')
@login_required
def get_health_history(id):
    """获取设备健康历史趋势"""
    equipment = Equipment.query.get_or_404(id)
    days = request.args.get('days', 30, type=int)
    start_date = date.today() - timedelta(days=days)

    health_records = EquipmentHealthIndex.query.filter(
        EquipmentHealthIndex.equipment_id == id,
        EquipmentHealthIndex.record_date >= start_date
    ).order_by(EquipmentHealthIndex.record_date).all()

    history_data = [{
        'date': h.record_date.strftime('%Y-%m-%d'),
        'health_score': float(h.health_score) if h.health_score else 0,
        'performance_score': float(h.performance_score) if h.performance_score else 0,
        'risk_score': float(h.risk_score) if h.risk_score else 0
    } for h in health_records]

    return jsonify({
        'success': True,
        'data': history_data
    })


# ==================== IoT数据API ====================
@equipment_api_bp.route('/<int:id>/iot/latest')
@login_required
def get_latest_iot(id):
    """获取最新IoT数据"""
    equipment = Equipment.query.get_or_404(id)
    latest_iot = EquipmentIotData.query.filter_by(equipment_id=id).order_by(
        EquipmentIotData.timestamp.desc()
    ).first()

    if not latest_iot:
        # 返回模拟数据
        latest_iot = {
            'is_running': equipment.status == 'running',
            'uptime_hours': 1234.5,
            'temperature': 28.5,
            'vibration': 2.3,
            'voltage': 220.0,
            'current': 15.5,
            'today_scans': 156,
            'total_scans': 123456,
            'has_alarms': False,
            'timestamp': datetime.now().isoformat()
        }

    return jsonify({
        'success': True,
        'data': {
            'is_running': getattr(latest_iot, 'is_running', False),
            'uptime_hours': float(getattr(latest_iot, 'uptime_hours', 0)),
            'temperature': float(getattr(latest_iot, 'temperature', 25.0)),
            'vibration': float(getattr(latest_iot, 'vibration', 1.5)),
            'voltage': float(getattr(latest_iot, 'voltage', 220)),
            'current': float(getattr(latest_iot, 'current', 10)),
            'today_scans': getattr(latest_iot, 'today_scans', 0),
            'total_scans': getattr(latest_iot, 'total_scans', 0),
            'has_alarms': getattr(latest_iot, 'has_alarms', False),
            'timestamp': getattr(latest_iot, 'timestamp', datetime.now()).isoformat() if getattr(latest_iot, 'timestamp') else datetime.now().isoformat()
        }
    })


@equipment_api_bp.route('/<int:id>/iot/history')
@login_required
def get_iot_history(id):
    """获取IoT历史数据"""
    equipment = Equipment.query.get_or_404(id)
    hours = request.args.get('hours', 24, type=int)
    start_time = datetime.now() - timedelta(hours=hours)

    iot_records = EquipmentIotData.query.filter(
        EquipmentIotData.equipment_id == id,
        EquipmentIotData.timestamp >= start_time
    ).order_by(EquipmentIotData.timestamp).limit(100).all()

    history_data = [{
        'timestamp': r.timestamp.isoformat(),
        'temperature': float(r.temperature) if r.temperature else 0,
        'vibration': float(r.vibration) if r.vibration else 0,
        'is_running': r.is_running
    } for r in iot_records]

    return jsonify({
        'success': True,
        'data': history_data
    })


@equipment_api_bp.route('/<int:id>/iot/submit', methods=['POST'])
@login_required
def submit_iot_data(id):
    """提交IoT数据（模拟设备数据上报）"""
    try:
        equipment = Equipment.query.get_or_404(id)
        data = request.get_json()

        iot_record = EquipmentIotData(
            equipment_id=id,
            is_running=data.get('is_running', True),
            uptime_hours=data.get('uptime_hours'),
            temperature=data.get('temperature'),
            vibration=data.get('vibration'),
            voltage=data.get('voltage'),
            current=data.get('current'),
            pressure=data.get('pressure'),
            radiation_power=data.get('radiation_power'),
            radiation_on_time=data.get('radiation_on_time'),
            today_scans=data.get('today_scans', 0),
            today_images=data.get('today_images', 0),
            total_scans=data.get('total_scans', 0),
            has_alarms=data.get('has_alarms', False),
            alarm_count=data.get('alarm_count', 0),
            raw_data=data
        )

        db.session.add(iot_record)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'IoT数据提交成功',
            'data': {'id': iot_record.id}
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'提交失败: {str(e)}'
        }), 400


# ==================== 预测性维护API ====================
@equipment_api_bp.route('/<int:id>/predictive/analysis')
@login_required
def get_predictive_analysis(id):
    """获取预测性维护分析"""
    equipment = Equipment.query.get_or_404(id)

    # 获取最新预测
    predictions = EquipmentPredictiveMaintenance.query.filter_by(equipment_id=id).order_by(
        EquipmentPredictiveMaintenance.created_at.desc()
    ).limit(5).all()

    # 模拟预测数据（如果没有实际数据）
    if not predictions:
        return jsonify({
            'success': True,
            'data': {
                'predictions': [{
                    'id': 0,
                    'prediction_type': 'failure',
                    'predicted_failure_date': (date.today() + timedelta(days=45)).isoformat(),
                    'confidence_level': 72.5,
                    'priority': 'medium',
                    'failure_probability': 35.2,
                    'predicted_component': '射线源管',
                    'recommendations': '建议在下个月安排预防性更换',
                    'prediction_date': date.today().isoformat(),
                    'acknowledged': False
                }],
                'mtbf_trend': {
                    'current': 7800,
                    'previous': 8200,
                    'trend': 'decreasing'
                }
            }
        })

    return jsonify({
        'success': True,
        'data': {
            'predictions': [{
                'id': p.id,
                'prediction_type': p.prediction_type,
                'predicted_failure_date': p.predicted_failure_date.isoformat() if p.predicted_failure_date else None,
                'confidence_level': float(p.confidence_level) if p.confidence_level else 0,
                'priority': p.priority,
                'failure_probability': float(p.failure_probability) if p.failure_probability else 0,
                'predicted_component': p.predicted_component,
                'recommendations': p.recommendations,
                'prediction_date': p.prediction_date.isoformat(),
                'acknowledged': p.acknowledged
            } for p in predictions]
        }
    })


@equipment_api_bp.route('/<int:id>/predictive/acknowledge/<int:prediction_id>', methods=['POST'])
@login_required
def acknowledge_prediction(id, prediction_id):
    """确认预测通知"""
    prediction = EquipmentPredictiveMaintenance.query.get_or_404(prediction_id)
    prediction.acknowledged = True
    prediction.acknowledged_by = current_user.id
    prediction.acknowledged_at = datetime.now()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '预测已确认'
    })


# ==================== 性能指标API ====================
@equipment_api_bp.route('/<int:id>/performance/dashboard')
@login_required
def get_performance_dashboard(id):
    """获取设备性能仪表板数据"""
    equipment = Equipment.query.get_or_404(id)

    # 获取最新性能指标
    latest_metric = EquipmentPerformanceMetric.query.filter_by(equipment_id=id).order_by(
        EquipmentPerformanceMetric.period_date.desc()
    ).first()

    # 生成模拟数据
    if not latest_metric:
        oee = 82.5
        availability = 92.0
        performance = 91.0
        quality = 98.5
    else:
        oee = latest_metric.oee_score or 82.5
        availability = latest_metric.availability_rate or 92.0
        performance = latest_metric.performance_rate or 91.0
        quality = latest_metric.quality_rate or 98.5

    return jsonify({
        'success': True,
        'data': {
            'oee': float(oee),
            'availability': float(availability),
            'performance': float(performance),
            'quality': float(quality),
            'status': equipment.status,
            'status_label': _get_status_label(equipment.status),
            'today_scans': 156,
            'total_scans': 123456,
            'efficiency_trend': 'stable'
        }
    })


@equipment_api_bp.route('/<int:id>/performance/history')
@login_required
def get_performance_history(id):
    """获取性能历史趋势"""
    equipment = Equipment.query.get_or_404(id)
    period = request.args.get('period', 'daily')
    months = request.args.get('months', 3, type=int)
    start_date = date.today() - timedelta(days=months*30)

    metrics = EquipmentPerformanceMetric.query.filter(
        EquipmentPerformanceMetric.equipment_id == id,
        EquipmentPerformanceMetric.period_date >= start_date,
        EquipmentPerformanceMetric.metric_type == period
    ).order_by(EquipmentPerformanceMetric.period_date).all()

    if not metrics:
        # 生成模拟历史数据
        mock_data = []
        base_date = start_date
        while base_date <= date.today():
            mock_data.append({
                'date': base_date.isoformat(),
                'oee': 80.0 + (base_date.day % 10) * 0.5,
                'availability': 90.0 + (base_date.day % 5) * 0.3,
                'performance': 88.0 + (base_date.day % 8) * 0.4,
                'quality': 97.0 + (base_date.day % 6) * 0.2
            })
            base_date += timedelta(days=1)
        history_data = mock_data[-30:]
    else:
        history_data = [{
            'date': m.period_date.isoformat(),
            'oee': float(m.oee_score) if m.oee_score else 0,
            'availability': float(m.availability_rate) if m.availability_rate else 0,
            'performance': float(m.performance_rate) if m.performance_rate else 0,
            'quality': float(m.quality_rate) if m.quality_rate else 0
        } for m in metrics]

    return jsonify({
        'success': True,
        'data': history_data
    })


# ==================== 组件/备件API ====================
@equipment_api_bp.route('/<int:id>/components')
@login_required
def get_components(id):
    """获取设备组件列表"""
    equipment = Equipment.query.get_or_404(id)
    components = EquipmentComponent.query.filter_by(equipment_id=id).all()

    if not components:
        # 返回模拟组件数据
        components_data = [
            {
                'id': 0,
                'component_name': 'X射线管',
                'component_type': 'critical',
                'status': 'normal',
                'usage_hours': 2345,
                'expected_lifetime': 8000,
                'installation_date': (date.today() - timedelta(days=180)).isoformat(),
                'next_replacement_date': (date.today() + timedelta(days=120)).isoformat()
            },
            {
                'id': 1,
                'component_name': '探测器阵列',
                'component_type': 'important',
                'status': 'normal',
                'usage_hours': 1890,
                'expected_lifetime': 10000,
                'installation_date': (date.today() - timedelta(days=120)).isoformat(),
                'next_replacement_date': (date.today() + timedelta(days=240)).isoformat()
            }
        ]
    else:
        components_data = [{
            'id': c.id,
            'component_name': c.component_name,
            'component_type': c.component_type,
            'status': c.status,
            'usage_hours': float(c.usage_hours) if c.usage_hours else 0,
            'expected_lifetime': c.expected_lifetime,
            'installation_date': c.installation_date.isoformat() if c.installation_date else None,
            'next_replacement_date': c.next_replacement_date.isoformat() if c.next_replacement_date else None
        } for c in components]

    return jsonify({
        'success': True,
        'data': components_data
    })


# ==================== 维护任务API ====================
@equipment_api_bp.route('/<int:id>/tasks')
@login_required
def get_maintenance_tasks(id):
    """获取设备维护任务"""
    equipment = Equipment.query.get_or_404(id)
    status_filter = request.args.get('status', None)

    query = EquipmentMaintenanceTask.query.filter_by(equipment_id=id)
    if status_filter:
        query = query.filter_by(status=status_filter)

    tasks = query.order_by(
        EquipmentMaintenanceTask.scheduled_date.asc().nullslast()
    ).limit(20).all()

    tasks_data = [{
        'id': t.id,
        'task_code': t.task_code,
        'task_name': t.task_name,
        'task_type': t.task_type,
        'priority': t.priority,
        'status': t.status,
        'progress': t.progress,
        'scheduled_date': t.scheduled_date.isoformat() if t.scheduled_date else None,
        'assigned_to': t.assigned_to
    } for t in tasks]

    return jsonify({
        'success': True,
        'data': tasks_data
    })


@equipment_api_bp.route('/<int:id>/tasks/create', methods=['POST'])
@login_required
def create_maintenance_task(id):
    """创建维护任务"""
    try:
        equipment = Equipment.query.get_or_404(id)
        data = request.get_json()

        task = EquipmentMaintenanceTask(
            equipment_id=id,
            task_name=data['task_name'],
            task_code=f"TASK{datetime.now().strftime('%Y%m%d%H%M%S')}",
            task_type=data.get('task_type', 'preventive'),
            priority=data.get('priority', 'medium'),
            description=data.get('description'),
            scheduled_date=datetime.strptime(data['scheduled_date'], '%Y-%m-%d').date() if data.get('scheduled_date') else None,
            estimated_duration=data.get('estimated_duration'),
            created_by=current_user.id
        )

        db.session.add(task)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '任务创建成功',
            'data': {'id': task.id, 'task_code': task.task_code}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 400


@equipment_api_bp.route('/<int:id>/tasks/<int:task_id>/update', methods=['PUT'])
@login_required
def update_maintenance_task(id, task_id):
    """更新维护任务状态"""
    task = EquipmentMaintenanceTask.query.get_or_404(task_id)
    data = request.get_json()

    if 'status' in data:
        task.status = data['status']
    if 'progress' in data:
        task.progress = data['progress']
    if 'actual_start_date' in data:
        task.actual_start_date = datetime.fromisoformat(data['actual_start_date'])
    if 'actual_end_date' in data:
        task.actual_end_date = datetime.fromisoformat(data['actual_end_date'])

    db.session.commit()

    return jsonify({
        'success': True,
        'message': '任务更新成功'
    })


# ==================== 文档/知识库API ====================
@equipment_api_bp.route('/<int:id>/documents')
@login_required
def get_documents(id):
    """获取设备文档列表"""
    equipment = Equipment.query.get_or_404(id)
    doc_type = request.args.get('type', None)

    query = EquipmentDocument.query.filter_by(equipment_id=id, is_active=True)
    if doc_type:
        query = query.filter_by(document_type=doc_type)

    documents = query.order_by(EquipmentDocument.created_at.desc()).all()

    docs_data = [{
        'id': d.id,
        'title': d.title,
        'document_type': d.document_type,
        'description': d.description,
        'version': d.version,
        'file_url': d.file_url,
        'category': d.category,
        'download_count': d.download_count,
        'created_at': d.created_at.isoformat()
    } for d in documents]

    return jsonify({
        'success': True,
        'data': docs_data
    })


# ==================== 高级统计API ====================
@equipment_api_bp.route('/advanced/overview')
@login_required
def get_advanced_overview():
    """获取设备管理高级概览"""
    total = Equipment.query.count()
    running = Equipment.query.filter_by(status='running').count()
    maintenance = Equipment.query.filter_by(status='maintenance').count()
    stopped = Equipment.query.filter_by(status='stopped').count()
    scrapped = Equipment.query.filter_by(status='scrapped').count()

    # 获取高风险设备
    high_risk_query = EquipmentHealthIndex.query.filter(
        EquipmentHealthIndex.health_score < 60
    ).group_by(EquipmentHealthIndex.equipment_id).limit(5)
    high_risk_ids = [h.equipment_id for h in high_risk_query]

    high_risk_equipments = Equipment.query.filter(Equipment.id.in_(high_risk_ids)).all()

    # 即将到期的维护
    thirty_days_later = date.today() + timedelta(days=30)
    upcoming_maintenance = EquipmentMaintenanceTask.query.filter(
        EquipmentMaintenanceTask.status == 'pending',
        EquipmentMaintenanceTask.scheduled_date <= thirty_days_later
    ).order_by(EquipmentMaintenanceTask.scheduled_date).limit(10).all()

    return jsonify({
        'success': True,
        'data': {
            'summary': {
                'total': total,
                'running': running,
                'maintenance': maintenance,
                'stopped': stopped,
                'scrapped': scrapped,
                'health_rate': round((total - maintenance - stopped - scrapped) / max(total, 1) * 100, 1)
            },
            'high_risk_equipment': [{
                'id': e.id,
                'name': e.name,
                'equipment_code': e.equipment_code,
                'status': e.status
            } for e in high_risk_equipments],
            'upcoming_maintenance': [{
                'id': t.id,
                'task_name': t.task_name,
                'scheduled_date': t.scheduled_date.isoformat() if t.scheduled_date else None,
                'equipment_id': t.equipment_id
            } for t in upcoming_maintenance]
        }
    })


# ==================== 辅助函数 ====================
def _determine_health_level(score):
    """根据分数确定健康等级"""
    if score >= 90:
        return 'excellent'
    elif score >= 80:
        return 'good'
    elif score >= 70:
        return 'normal'
    elif score >= 60:
        return 'warning'
    else:
        return 'critical'


def _determine_risk_level(score):
    """根据健康分数确定风险等级"""
    if score >= 90:
        return 'low'
    elif score >= 80:
        return 'low'
    elif score >= 70:
        return 'medium'
    elif score >= 60:
        return 'high'
    else:
        return 'critical'


def _get_status_label(status):
    """获取状态标签"""
    labels = {
        'running': '运行中',
        'stopped': '停机',
        'maintenance': '维修中',
        'scrapped': '已报废'
    }
    return labels.get(status, status)
