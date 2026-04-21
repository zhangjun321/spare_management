#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业设备维护管理系统 - 数据模型

注意：所有模型类名已加上 Ind 前缀，以避免与现有系统冲突
表名使用 ind_ 前缀
"""
from datetime import datetime
from app.extensions import db


class IndDeviceType(db.Model):
    """设备类型表"""
    __tablename__ = 'ind_device_type'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    protocol = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    devices = db.relationship('IndDevice', back_populates='device_type')


class IndDevice(db.Model):
    """设备信息表"""
    __tablename__ = 'ind_device'

    id = db.Column(db.Integer, primary_key=True)
    device_code = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    device_type_id = db.Column(db.Integer, db.ForeignKey('ind_device_type.id'), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    manufacturer = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    serial_number = db.Column(db.String(100), nullable=True)
    purchase_date = db.Column(db.Date, nullable=True)
    warranty_period = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='active')
    health_score = db.Column(db.Float, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    port = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    device_type = db.relationship('IndDeviceType', back_populates='devices')
    components = db.relationship('IndDeviceComponent', back_populates='device')
    alerts = db.relationship('IndAlert', back_populates='device')
    work_orders = db.relationship('IndMaintenanceWorkOrder', back_populates='device')
    maintenance_plans = db.relationship('IndMaintenancePlan', back_populates='device')
    maintenance_records = db.relationship('IndMaintenanceRecord', back_populates='device')
    component_replacements = db.relationship('IndComponentReplacement', back_populates='device')


class IndDeviceComponent(db.Model):
    """设备组件表"""
    __tablename__ = 'ind_device_component'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('ind_device.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    serial_number = db.Column(db.String(100), nullable=True)
    install_date = db.Column(db.Date, nullable=True)
    life_span = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='normal')
    health_score = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    device = db.relationship('IndDevice', back_populates='components')


class IndAlert(db.Model):
    """告警记录表"""
    __tablename__ = 'ind_alert'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('ind_device.id'), nullable=False)
    alert_code = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(50), nullable=True)
    parameter_code = db.Column(db.String(100), nullable=True)
    parameter_value = db.Column(db.Float, nullable=True)
    threshold_value = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联
    device = db.relationship('IndDevice', back_populates='alerts')


class IndMaintenanceWorkOrder(db.Model):
    """维修工单表"""
    __tablename__ = 'ind_work_order'

    id = db.Column(db.Integer, primary_key=True)
    work_order_code = db.Column(db.String(100), unique=True, nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('ind_device.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False, default='repair')
    priority = db.Column(db.String(20), nullable=False, default='medium')
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    result = db.Column(db.Text, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    device = db.relationship('IndDevice', back_populates='work_orders')
    creator = db.relationship('User', foreign_keys=[created_by])
    assignee = db.relationship('User', foreign_keys=[assigned_to])
    logs = db.relationship('IndWorkOrderLog', back_populates='work_order')
    spare_part_uses = db.relationship('IndSparePartUse', back_populates='work_order')


class IndWorkOrderLog(db.Model):
    """工单日志表"""
    __tablename__ = 'ind_work_order_log'

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('ind_work_order.id'), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联
    work_order = db.relationship('IndMaintenanceWorkOrder', back_populates='logs')
    operator = db.relationship('User', foreign_keys=[operator_id])


class IndMaintenancePlan(db.Model):
    """维护计划表"""
    __tablename__ = 'ind_maintenance_plan'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('ind_device.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)
    interval_days = db.Column(db.Integer, nullable=False)
    last_executed = db.Column(db.Date, nullable=True)
    next_scheduled = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    device = db.relationship('IndDevice', back_populates='maintenance_plans')


class IndMaintenanceRecord(db.Model):
    """维护记录表"""
    __tablename__ = 'ind_maintenance_record'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('ind_device.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('ind_maintenance_plan.id'), nullable=True)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    executed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    executed_at = db.Column(db.DateTime, nullable=False)
    result = db.Column(db.Text, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联
    device = db.relationship('IndDevice', back_populates='maintenance_records')


class IndKnowledgeBase(db.Model):
    """故障知识库表"""
    __tablename__ = 'ind_knowledge_base'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    symptom = db.Column(db.Text, nullable=True)
    cause = db.Column(db.Text, nullable=True)
    solution = db.Column(db.Text, nullable=True)
    tags = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    view_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IndSparePart(db.Model):
    """备件信息表"""
    __tablename__ = 'ind_spare_part'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    model = db.Column(db.String(100), nullable=True)
    manufacturer = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    inventories = db.relationship('IndSparePartInventory', back_populates='spare_part')
    spare_part_uses = db.relationship('IndSparePartUse', back_populates='spare_part')


class IndSparePartInventory(db.Model):
    """备件库存表"""
    __tablename__ = 'ind_spare_part_inventory'

    id = db.Column(db.Integer, primary_key=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('ind_spare_part.id'), nullable=False)
    warehouse = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    min_stock = db.Column(db.Integer, nullable=True)
    safety_stock = db.Column(db.Integer, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    spare_part = db.relationship('IndSparePart', back_populates='inventories')


class IndSparePartUse(db.Model):
    """备件使用记录表"""
    __tablename__ = 'ind_spare_part_use'

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('ind_work_order.id'), nullable=False)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('ind_spare_part.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联
    work_order = db.relationship('IndMaintenanceWorkOrder', back_populates='spare_part_uses')
    spare_part = db.relationship('IndSparePart', back_populates='spare_part_uses')


class IndComponentReplacement(db.Model):
    """组件更换记录表"""
    __tablename__ = 'ind_component_replacement'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('ind_device.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('ind_device_component.id'), nullable=False)
    old_component_id = db.Column(db.Integer, db.ForeignKey('ind_device_component.id'), nullable=True)
    new_component_id = db.Column(db.Integer, db.ForeignKey('ind_device_component.id'), nullable=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('ind_work_order.id'), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    replaced_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 关联
    device = db.relationship('IndDevice', back_populates='component_replacements')
    component = db.relationship('IndDeviceComponent', foreign_keys=[component_id])
    old_component = db.relationship('IndDeviceComponent', foreign_keys=[old_component_id])
    new_component = db.relationship('IndDeviceComponent', foreign_keys=[new_component_id])
    work_order = db.relationship('IndMaintenanceWorkOrder', backref='ind_component_replacements')
    operator = db.relationship('User', foreign_keys=[operator_id])
