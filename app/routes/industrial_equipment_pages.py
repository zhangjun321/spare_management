
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业设备维护管理系统 - 前端页面路由
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
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

industrial_pages_bp = Blueprint('industrial_pages', __name__, url_prefix='/industrial')


@industrial_pages_bp.route('/dashboard')
@login_required
def dashboard():
    """工业设备仪表盘页面"""
    # 统计数据
    total_devices = IndDevice.query.count()
    active_devices = IndDevice.query.filter_by(status='active').count()
    maintenance_devices = IndDevice.query.filter_by(status='maintenance').count()
    
    active_alerts = IndAlert.query.filter_by(status='active').count()
    critical_alerts = IndAlert.query.filter_by(status='active', level='critical').count()
    
    pending_work_orders = IndMaintenanceWorkOrder.query.filter_by(status='pending').count()
    in_progress_work_orders = IndMaintenanceWorkOrder.query.filter_by(status='in_progress').count()
    
    # 最近的告警
    recent_alerts = IndAlert.query.order_by(IndAlert.created_at.desc()).limit(10).all()
    
    # 最近的工单
    recent_work_orders = IndMaintenanceWorkOrder.query.order_by(
        IndMaintenanceWorkOrder.created_at.desc()
    ).limit(10).all()
    
    return render_template('industrial/dashboard.html',
        total_devices=total_devices,
        active_devices=active_devices,
        maintenance_devices=maintenance_devices,
        active_alerts=active_alerts,
        critical_alerts=critical_alerts,
        pending_work_orders=pending_work_orders,
        in_progress_work_orders=in_progress_work_orders,
        recent_alerts=recent_alerts,
        recent_work_orders=recent_work_orders
    )


@industrial_pages_bp.route('/devices')
@login_required
def devices():
    """设备列表页面"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    device_type_id = request.args.get('device_type_id', type=int)
    
    query = IndDevice.query
    
    if status:
        query = query.filter_by(status=status)
    if device_type_id:
        query = query.filter_by(device_type_id=device_type_id)
    
    pagination = query.order_by(IndDevice.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    device_types = IndDeviceType.query.all()
    
    return render_template('industrial/devices.html',
        pagination=pagination,
        device_types=device_types,
        current_status=status,
        current_device_type=device_type_id
    )


@industrial_pages_bp.route('/devices/&lt;int:id&gt;')
@login_required
def device_detail(id):
    """设备详情页面"""
    device = IndDevice.query.get_or_404(id)
    
    # 获取该设备的告警
    alerts = IndAlert.query.filter_by(device_id=id).order_by(IndAlert.created_at.desc()).all()
    
    # 获取该设备的工单
    work_orders = IndMaintenanceWorkOrder.query.filter_by(device_id=id).order_by(
        IndMaintenanceWorkOrder.created_at.desc()
    ).all()
    
    # 获取该设备的组件
    components = IndDeviceComponent.query.filter_by(device_id=id).all()
    
    # 获取该设备的维护计划
    maintenance_plans = IndMaintenancePlan.query.filter_by(device_id=id).all()
    
    return render_template('industrial/device_detail.html',
        device=device,
        alerts=alerts,
        work_orders=work_orders,
        components=components,
        maintenance_plans=maintenance_plans
    )


@industrial_pages_bp.route('/alerts')
@login_required
def alerts():
    """告警管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    level = request.args.get('level')
    
    query = IndAlert.query
    
    if status:
        query = query.filter_by(status=status)
    if level:
        query = query.filter_by(level=level)
    
    pagination = query.order_by(IndAlert.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('industrial/alerts.html',
        pagination=pagination,
        current_status=status,
        current_level=level
    )


@industrial_pages_bp.route('/work-orders')
@login_required
def work_orders():
    """维修工单页面"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    priority = request.args.get('priority')
    
    query = IndMaintenanceWorkOrder.query
    
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    
    pagination = query.order_by(IndMaintenanceWorkOrder.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('industrial/work_orders.html',
        pagination=pagination,
        current_status=status,
        current_priority=priority
    )


@industrial_pages_bp.route('/work-orders/&lt;int:id&gt;')
@login_required
def work_order_detail(id):
    """工单详情页面"""
    work_order = IndMaintenanceWorkOrder.query.get_or_404(id)
    
    # 获取工单日志
    logs = IndWorkOrderLog.query.filter_by(work_order_id=id).order_by(IndWorkOrderLog.created_at.desc()).all()
    
    return render_template('industrial/work_order_detail.html',
        work_order=work_order,
        logs=logs
    )


@industrial_pages_bp.route('/work-orders/create')
@login_required
def create_work_order():
    """创建工单页面"""
    devices = IndDevice.query.all()
    return render_template('industrial/create_work_order.html', devices=devices)


@industrial_pages_bp.route('/knowledge-base')
@login_required
def knowledge_base():
    """知识库页面"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category')
    
    query = IndKnowledgeBase.query.filter_by(is_active=True)
    
    if category:
        query = query.filter_by(category=category)
    
    pagination = query.order_by(IndKnowledgeBase.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('industrial/knowledge_base.html',
        pagination=pagination,
        current_category=category
    )


@industrial_pages_bp.route('/knowledge-base/&lt;int:id&gt;')
@login_required
def knowledge_detail(id):
    """知识库详情页面"""
    knowledge = IndKnowledgeBase.query.get_or_404(id)
    
    # 增加浏览次数
    knowledge.view_count += 1
    db.session.commit()
    
    return render_template('industrial/knowledge_detail.html', knowledge=knowledge)


@industrial_pages_bp.route('/spare-parts')
@login_required
def spare_parts():
    """备件管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = IndSparePart.query.order_by(IndSparePart.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('industrial/spare_parts.html', pagination=pagination)


@industrial_pages_bp.route('/spare-parts/&lt;int:id&gt;')
@login_required
def spare_part_detail(id):
    """备件详情页面"""
    spare_part = IndSparePart.query.get_or_404(id)
    
    # 获取库存信息
    inventory = IndSparePartInventory.query.filter_by(spare_part_id=id).all()
    
    return render_template('industrial/spare_part_detail.html',
        spare_part=spare_part,
        inventory=inventory
    )


@industrial_pages_bp.route('/maintenance-plans')
@login_required
def maintenance_plans():
    """维护计划页面"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = IndMaintenancePlan.query.order_by(IndMaintenancePlan.next_scheduled).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('industrial/maintenance_plans.html', pagination=pagination)


@industrial_pages_bp.route('/components')
@login_required
def components():
    """设备组件管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = IndDeviceComponent.query
    
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(IndDeviceComponent.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('industrial/components.html',
        pagination=pagination,
        current_status=status
    )

