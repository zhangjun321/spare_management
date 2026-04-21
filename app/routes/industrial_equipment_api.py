#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业设备维护管理系统 - API路由
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.industrial_equipment import (
    IndDeviceType, IndDevice, IndDeviceComponent,
    IndAlert, IndMaintenanceWorkOrder, IndWorkOrderLog,
    IndMaintenancePlan, IndMaintenanceRecord,
    IndKnowledgeBase, IndSparePart, IndSparePartInventory,
    IndSparePartUse, IndComponentReplacement
)
from datetime import datetime

industrial_bp = Blueprint('industrial', __name__, url_prefix='/api/industrial')


# ==================== 设备类型管理 ====================
@industrial_bp.route('/device-types', methods=['GET'])
@login_required
def get_device_types():
    """获取设备类型列表"""
    types = IndDeviceType.query.all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'code': t.code,
        'description': t.description,
        'protocol': t.protocol
    } for t in types])


@industrial_bp.route('/device-types', methods=['POST'])
@login_required
def create_device_type():
    """创建设备类型"""
    data = request.get_json()
    device_type = IndDeviceType(
        name=data['name'],
        code=data['code'],
        description=data.get('description'),
        protocol=data.get('protocol')
    )
    db.session.add(device_type)
    db.session.commit()
    return jsonify({'id': device_type.id, 'message': '创建设备类型成功'}), 201


# ==================== 设备管理 ====================
@industrial_bp.route('/devices', methods=['GET'])
@login_required
def get_devices():
    """获取设备列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')

    query = IndDevice.query
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(IndDevice.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'items': [{
            'id': d.id,
            'device_code': d.device_code,
            'name': d.name,
            'device_type': {
                'id': d.device_type.id,
                'name': d.device_type.name
            } if d.device_type else None,
            'location': d.location,
            'status': d.status,
            'health_score': d.health_score,
            'manufacturer': d.manufacturer,
            'model': d.model
        } for d in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page
    })


@industrial_bp.route('/devices/<int:id>', methods=['GET'])
@login_required
def get_device_detail(id):
    """获取设备详情"""
    device = IndDevice.query.get_or_404(id)
    return jsonify({
        'id': device.id,
        'device_code': device.device_code,
        'name': device.name,
        'device_type_id': device.device_type_id,
        'location': device.location,
        'manufacturer': device.manufacturer,
        'model': device.model,
        'serial_number': device.serial_number,
        'purchase_date': str(device.purchase_date) if device.purchase_date else None,
        'warranty_period': device.warranty_period,
        'status': device.status,
        'health_score': device.health_score,
        'ip_address': device.ip_address,
        'port': device.port,
        'components': [{
            'id': c.id,
            'name': c.name,
            'type': c.type,
            'status': c.status,
            'health_score': c.health_score
        } for c in device.components],
        'recent_alerts': [{
            'id': a.id,
            'level': a.level,
            'title': a.title,
            'status': a.status,
            'created_at': str(a.created_at)
        } for a in IndAlert.query.filter_by(device_id=id).order_by(IndAlert.created_at.desc()).limit(5)]
    })


@industrial_bp.route('/devices', methods=['POST'])
@login_required
def create_device():
    """创建设备"""
    data = request.get_json()
    device = IndDevice(
        device_code=data['device_code'],
        name=data['name'],
        device_type_id=data['device_type_id'],
        location=data.get('location'),
        manufacturer=data.get('manufacturer'),
        model=data.get('model'),
        serial_number=data.get('serial_number'),
        status=data.get('status', 'active'),
        health_score=data.get('health_score', 100),
        ip_address=data.get('ip_address'),
        port=data.get('port')
    )
    db.session.add(device)
    db.session.commit()
    return jsonify({'id': device.id, 'message': '创建设备成功'}), 201


@industrial_bp.route('/devices/<int:id>', methods=['PUT'])
@login_required
def update_device(id):
    """更新设备"""
    device = IndDevice.query.get_or_404(id)
    data = request.get_json()
    
    allowed_fields = ['name', 'location', 'status', 'health_score', 'ip_address', 'port']
    for field in allowed_fields:
        if field in data:
            setattr(device, field, data[field])
    
    db.session.commit()
    return jsonify({'message': '更新设备成功'})


@industrial_bp.route('/devices/<int:id>/components', methods=['GET'])
@login_required
def get_device_components(id):
    """获取设备组件列表"""
    components = IndDeviceComponent.query.filter_by(device_id=id).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'type': c.type,
        'model': c.model,
        'status': c.status,
        'health_score': c.health_score,
        'install_date': str(c.install_date) if c.install_date else None
    } for c in components])


@industrial_bp.route('/devices/<int:id>/components', methods=['POST'])
@login_required
def add_device_component(id):
    """添加设备组件"""
    data = request.get_json()
    component = IndDeviceComponent(
        device_id=id,
        name=data['name'],
        type=data.get('type'),
        model=data.get('model'),
        serial_number=data.get('serial_number'),
        status=data.get('status', 'normal'),
        health_score=data.get('health_score', 100)
    )
    db.session.add(component)
    db.session.commit()
    return jsonify({'id': component.id, 'message': '添加组件成功'}), 201


# ==================== 告警管理 ====================
@industrial_bp.route('/alerts', methods=['GET'])
@login_required
def get_alerts():
    """获取告警列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    level = request.args.get('level')

    query = IndAlert.query
    if status:
        query = query.filter_by(status=status)
    if level:
        query = query.filter_by(level=level)

    pagination = query.order_by(IndAlert.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'items': [{
            'id': a.id,
            'alert_code': a.alert_code,
            'level': a.level,
            'title': a.title,
            'device_name': a.device.name if a.device else None,
            'status': a.status,
            'created_at': str(a.created_at)
        } for a in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page
    })


@industrial_bp.route('/alerts/<int:id>', methods=['GET'])
@login_required
def get_alert_detail(id):
    """获取告警详情"""
    alert = IndAlert.query.get_or_404(id)
    return jsonify({
        'id': alert.id,
        'alert_code': alert.alert_code,
        'level': alert.level,
        'title': alert.title,
        'description': alert.description,
        'device_id': alert.device_id,
        'device_name': alert.device.name if alert.device else None,
        'source': alert.source,
        'parameter_code': alert.parameter_code,
        'parameter_value': alert.parameter_value,
        'threshold_value': alert.threshold_value,
        'status': alert.status,
        'acknowledged_at': str(alert.acknowledged_at) if alert.acknowledged_at else None,
        'resolved_at': str(alert.resolved_at) if alert.resolved_at else None,
        'created_at': str(alert.created_at)
    })


@industrial_bp.route('/alerts/<int:id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_alert(id):
    """确认告警"""
    alert = IndAlert.query.get_or_404(id)
    alert.status = 'acknowledged'
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': '告警已确认'})


@industrial_bp.route('/alerts/<int:id>/resolve', methods=['POST'])
@login_required
def resolve_alert(id):
    """处理告警"""
    alert = IndAlert.query.get_or_404(id)
    data = request.get_json()
    alert.status = 'resolved'
    alert.resolved_by = current_user.id
    alert.resolved_at = datetime.utcnow()
    alert.resolution = data.get('resolution')
    db.session.commit()
    return jsonify({'message': '告警已处理'})


# ==================== 维修工单管理 ====================
@industrial_bp.route('/work-orders', methods=['GET'])
@login_required
def get_work_orders():
    """获取工单列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')

    query = IndMaintenanceWorkOrder.query
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(IndMaintenanceWorkOrder.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'items': [{
            'id': w.id,
            'work_order_code': w.work_order_code,
            'title': w.title,
            'type': w.type,
            'priority': w.priority,
            'device_name': w.device.name if w.device else None,
            'status': w.status,
            'created_at': str(w.created_at)
        } for w in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page
    })


@industrial_bp.route('/work-orders/<int:id>', methods=['GET'])
@login_required
def get_work_order_detail(id):
    """获取工单详情"""
    work_order = IndMaintenanceWorkOrder.query.get_or_404(id)
    return jsonify({
        'id': work_order.id,
        'work_order_code': work_order.work_order_code,
        'title': work_order.title,
        'type': work_order.type,
        'priority': work_order.priority,
        'description': work_order.description,
        'device_id': work_order.device_id,
        'device_name': work_order.device.name if work_order.device else None,
        'status': work_order.status,
        'created_by': work_order.created_by,
        'assigned_to': work_order.assigned_to,
        'started_at': str(work_order.started_at) if work_order.started_at else None,
        'completed_at': str(work_order.completed_at) if work_order.completed_at else None,
        'result': work_order.result,
        'cost': work_order.cost,
        'created_at': str(work_order.created_at),
        'logs': [{
            'id': l.id,
            'action': l.action,
            'content': l.content,
            'operator_id': l.operator_id,
            'created_at': str(l.created_at)
        } for l in work_order.logs]
    })


@industrial_bp.route('/work-orders', methods=['POST'])
@login_required
def create_work_order():
    """创建工单"""
    data = request.get_json()
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    work_order = IndMaintenanceWorkOrder(
        work_order_code=f'WO-{timestamp}',
        device_id=data['device_id'],
        type=data.get('type', 'repair'),
        priority=data.get('priority', 'medium'),
        title=data['title'],
        description=data.get('description'),
        status='pending',
        created_by=current_user.id
    )
    db.session.add(work_order)
    db.session.commit()

    log = IndWorkOrderLog(
        work_order_id=work_order.id,
        operator_id=current_user.id,
        action='create',
        content=f'创建工单：{work_order.title}'
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'id': work_order.id, 'work_order_code': work_order.work_order_code, 'message': '创建工单成功'}), 201


@industrial_bp.route('/work-orders/<int:id>/assign', methods=['POST'])
@login_required
def assign_work_order(id):
    """派单"""
    work_order = IndMaintenanceWorkOrder.query.get_or_404(id)
    data = request.get_json()
    work_order.assigned_to = data['assigned_to']
    work_order.status = 'assigned'
    db.session.commit()

    log = IndWorkOrderLog(
        work_order_id=work_order.id,
        operator_id=current_user.id,
        action='assign',
        content=f'派单给用户ID: {data["assigned_to"]}'
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'message': '派单成功'})


@industrial_bp.route('/work-orders/<int:id>/start', methods=['POST'])
@login_required
def start_work_order(id):
    """开始处理"""
    work_order = IndMaintenanceWorkOrder.query.get_or_404(id)
    work_order.status = 'in_progress'
    work_order.started_at = datetime.utcnow()
    db.session.commit()

    log = IndWorkOrderLog(
        work_order_id=work_order.id,
        operator_id=current_user.id,
        action='start',
        content='开始处理工单'
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'message': '已开始处理'})


@industrial_bp.route('/work-orders/<int:id>/complete', methods=['POST'])
@login_required
def complete_work_order(id):
    """完成工单"""
    work_order = IndMaintenanceWorkOrder.query.get_or_404(id)
    data = request.get_json()
    work_order.status = 'completed'
    work_order.completed_at = datetime.utcnow()
    work_order.result = data.get('result')
    work_order.cost = data.get('cost')
    db.session.commit()

    log = IndWorkOrderLog(
        work_order_id=work_order.id,
        operator_id=current_user.id,
        action='complete',
        content=f'完成工单，结果：{data.get("result", "")}'
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'message': '工单已完成'})


# ==================== 知识库管理 ====================
@industrial_bp.route('/knowledge', methods=['GET'])
@login_required
def get_knowledge_list():
    """获取知识库列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category')

    query = IndKnowledgeBase.query.filter_by(is_active=True)
    if category:
        query = query.filter_by(category=category)

    pagination = query.order_by(IndKnowledgeBase.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'items': [{
            'id': k.id,
            'title': k.title,
            'category': k.category,
            'symptom': k.symptom,
            'view_count': k.view_count,
            'created_at': str(k.created_at)
        } for k in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page
    })


@industrial_bp.route('/knowledge/<int:id>', methods=['GET'])
@login_required
def get_knowledge_detail(id):
    """获取知识库详情"""
    knowledge = IndKnowledgeBase.query.get_or_404(id)
    knowledge.view_count += 1
    db.session.commit()

    return jsonify({
        'id': knowledge.id,
        'title': knowledge.title,
        'category': knowledge.category,
        'symptom': knowledge.symptom,
        'cause': knowledge.cause,
        'solution': knowledge.solution,
        'tags': knowledge.tags,
        'view_count': knowledge.view_count,
        'created_at': str(knowledge.created_at)
    })


@industrial_bp.route('/knowledge', methods=['POST'])
@login_required
def create_knowledge():
    """创建知识库条目"""
    data = request.get_json()
    knowledge = IndKnowledgeBase(
        title=data['title'],
        category=data.get('category'),
        symptom=data.get('symptom'),
        cause=data.get('cause'),
        solution=data.get('solution'),
        tags=data.get('tags'),
        created_by=current_user.id
    )
    db.session.add(knowledge)
    db.session.commit()
    return jsonify({'id': knowledge.id, 'message': '创建成功'}), 201


@industrial_bp.route('/knowledge/search', methods=['GET'])
@login_required
def search_knowledge():
    """搜索知识库"""
    keyword = request.args.get('keyword', '')
    query = IndKnowledgeBase.query.filter(
        db.or_(
            IndKnowledgeBase.title.contains(keyword),
            IndKnowledgeBase.symptom.contains(keyword),
            IndKnowledgeBase.solution.contains(keyword)
        )
    ).filter_by(is_active=True)

    items = query.limit(20).all()
    return jsonify([{
        'id': k.id,
        'title': k.title,
        'category': k.category,
        'symptom': k.symptom
    } for k in items])


# ==================== 备件管理 ====================
@industrial_bp.route('/spare-parts', methods=['GET'])
@login_required
def get_spare_parts():
    """获取备件列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = IndSparePart.query.order_by(IndSparePart.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'items': [{
            'id': s.id,
            'code': s.code,
            'name': s.name,
            'model': s.model,
            'manufacturer': s.manufacturer,
            'price': s.price,
            'inventories': [{
                'warehouse': inv.warehouse,
                'quantity': inv.quantity
            } for inv in s.inventories]
        } for s in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page
    })


@industrial_bp.route('/spare-parts', methods=['POST'])
@login_required
def create_spare_part():
    """创建备件"""
    data = request.get_json()
    spare_part = IndSparePart(
        code=data['code'],
        name=data['name'],
        model=data.get('model'),
        manufacturer=data.get('manufacturer'),
        description=data.get('description'),
        price=data.get('price')
    )
    db.session.add(spare_part)
    db.session.commit()

    inventory = IndSparePartInventory(
        spare_part_id=spare_part.id,
        warehouse=data.get('warehouse', '主仓库'),
        quantity=data.get('quantity', 0)
    )
    db.session.add(inventory)
    db.session.commit()

    return jsonify({'id': spare_part.id, 'message': '创建成功'}), 201


# ==================== 仪表板数据 ====================
@industrial_bp.route('/dashboard/overview', methods=['GET'])
@login_required
def get_dashboard_overview():
    """获取仪表板概览数据"""
    total_devices = IndDevice.query.count()
    active_devices = IndDevice.query.filter_by(status='active').count()
    maintenance_devices = IndDevice.query.filter_by(status='maintenance').count()

    active_alerts = IndAlert.query.filter_by(status='active').count()
    critical_alerts = IndAlert.query.filter_by(status='active', level='critical').count()

    pending_work_orders = IndMaintenanceWorkOrder.query.filter_by(status='pending').count()
    in_progress_work_orders = IndMaintenanceWorkOrder.query.filter_by(status='in_progress').count()

    recent_alerts = IndAlert.query.order_by(IndAlert.created_at.desc()).limit(10).all()

    return jsonify({
        'devices': {
            'total': total_devices,
            'active': active_devices,
            'maintenance': maintenance_devices
        },
        'alerts': {
            'active': active_alerts,
            'critical': critical_alerts
        },
        'work_orders': {
            'pending': pending_work_orders,
            'in_progress': in_progress_work_orders
        },
        'recent_alerts': [{
            'id': a.id,
            'level': a.level,
            'title': a.title,
            'device_name': a.device.name if a.device else None,
            'created_at': str(a.created_at)
        } for a in recent_alerts]
    })
