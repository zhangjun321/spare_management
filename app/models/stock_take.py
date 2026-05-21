# -*- coding: utf-8 -*-
"""
盘点任务模型 — 可配置盘点任务、扫码盘点、差异处理与审批

任务状态: draft → in_progress → pending_review → completed | cancelled
差异调整单状态: draft → submitted → approved → applied | rejected
"""
from app.extensions import db
from datetime import datetime


class StockTakeTask(db.Model):
    """盘点任务"""
    __tablename__ = 'stock_take_task'

    id = db.Column(db.Integer, primary_key=True)
    task_code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='盘点编号(ST前缀)')
    title = db.Column(db.String(200), nullable=False, comment='任务标题')
    scope_type = db.Column(db.String(20), default='warehouse', comment='盘点范围: warehouse/area/category/manual')
    scope_value = db.Column(db.String(200), comment='范围值(仓库ID/库区/品类)')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), index=True, comment='仓库ID')
    status = db.Column(db.String(20), default='draft', comment='状态: draft/in_progress/pending_review/completed/cancelled')
    assignee_ids = db.Column(db.String(500), comment='盘点人员ID(逗号分隔)')
    assignee_names = db.Column(db.String(500), comment='盘点人员姓名')
    planner_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='计划人')
    deadline = db.Column(db.DateTime, comment='截止时间')
    total_items = db.Column(db.Integer, default=0, comment='盘点项总数')
    counted_items = db.Column(db.Integer, default=0, comment='已盘点项数')
    diff_items = db.Column(db.Integer, default=0, comment='差异项数')
    approval_required = db.Column(db.Boolean, default=True, comment='差异是否需要审批')
    remark = db.Column(db.Text, comment='备注')
    version = db.Column(db.Integer, default=1, comment='乐观锁版本号')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = db.Column(db.DateTime, comment='开始时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')

    # Relationships
    warehouse = db.relationship('Warehouse')
    planner = db.relationship('User', foreign_keys=[planner_id])
    items = db.relationship('StockTakeItem', back_populates='task', cascade='all, delete-orphan')

    TRANSITIONS = {
        'draft':          ['in_progress', 'cancelled'],
        'in_progress':    ['pending_review', 'cancelled'],
        'pending_review': ['completed'],
        'completed':      [],
        'cancelled':      [],
    }

    def can_transit(self, target):
        return target in self.TRANSITIONS.get(self.status, [])

    def transit(self, target, operator_id=None):
        if not self.can_transit(target):
            raise ValueError(f'不允许从 {self.status} 转为 {target}')
        self.status = target
        self.version += 1
        now = datetime.utcnow()
        if target == 'in_progress':
            self.started_at = now
        elif target == 'completed':
            self.completed_at = now

    def recalc_stats(self):
        items = self.items or []
        self.total_items = len(items)
        self.counted_items = sum(1 for i in items if i.system_qty is not None and i.counted_qty is not None)
        self.diff_items = sum(1 for i in items if i.has_diff())

    def to_dict(self):
        return {
            'id': self.id,
            'task_code': self.task_code,
            'title': self.title,
            'scope_type': self.scope_type,
            'scope_value': self.scope_value,
            'warehouse_id': self.warehouse_id,
            'warehouse_name': self.warehouse.name if self.warehouse else None,
            'status': self.status,
            'assignee_ids': self.assignee_ids,
            'assignee_names': self.assignee_names,
            'deadline': self.deadline.strftime('%Y-%m-%d %H:%M:%S') if self.deadline else None,
            'total_items': self.total_items,
            'counted_items': self.counted_items,
            'diff_items': self.diff_items,
            'approval_required': self.approval_required,
            'remark': self.remark,
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }


class StockTakeItem(db.Model):
    """盘点明细"""
    __tablename__ = 'stock_take_item'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('stock_take_task.id'), nullable=False, index=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True)
    batch_no = db.Column(db.String(100), comment='批次号(可选)')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), comment='库位ID')
    system_qty = db.Column(db.Numeric(10, 2), comment='系统数量')
    counted_qty = db.Column(db.Numeric(10, 2), comment='盘点数量')
    diff_qty = db.Column(db.Numeric(10, 2), comment='差异数量(=counted-system)')
    item_status = db.Column(db.String(20), default='pending', comment='状态: pending/counted/reconciled')
    counted_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='盘点人')
    counted_at = db.Column(db.DateTime, comment='盘点时间')
    scan_code = db.Column(db.String(200), comment='扫码编码')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task = db.relationship('StockTakeTask', back_populates='items')
    spare_part = db.relationship('SparePart')
    location = db.relationship('WarehouseLocation')

    def has_diff(self):
        s = float(self.system_qty or 0)
        c = float(self.counted_qty or 0)
        return abs(s - c) > 0.001

    def calc_diff(self):
        s = float(self.system_qty or 0)
        c = float(self.counted_qty or 0)
        self.diff_qty = c - s
        return self.diff_qty

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'spare_part_id': self.spare_part_id,
            'spare_part_code': self.spare_part.part_code if self.spare_part else None,
            'spare_part_name': self.spare_part.name if self.spare_part else None,
            'batch_no': self.batch_no,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'system_qty': float(self.system_qty) if self.system_qty else 0,
            'counted_qty': float(self.counted_qty) if self.counted_qty is not None else None,
            'diff_qty': float(self.diff_qty) if self.diff_qty else 0,
            'has_diff': self.has_diff(),
            'item_status': self.item_status,
            'counted_by': self.counted_by,
            'counted_at': self.counted_at.strftime('%Y-%m-%d %H:%M:%S') if self.counted_at else None,
            'remark': self.remark,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }


class AdjustmentOrder(db.Model):
    """差异调整单"""
    __tablename__ = 'adjustment_order'

    id = db.Column(db.Integer, primary_key=True)
    adjust_code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='调整编号(AD前缀)')
    task_id = db.Column(db.Integer, db.ForeignKey('stock_take_task.id'), nullable=False, index=True)
    stock_take_item_id = db.Column(db.Integer, db.ForeignKey('stock_take_item.id'), comment='盘点明细ID')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), index=True)
    adjust_type = db.Column(db.String(20), nullable=False, comment='调整类型: gain(盘盈)/loss(盘亏)/damage(破损)')
    adjust_qty = db.Column(db.Numeric(10, 2), nullable=False, comment='调整数量(正=盘盈,负=盘亏)')
    reason = db.Column(db.Text, comment='调整原因')
    status = db.Column(db.String(20), default='draft', comment='状态: draft/submitted/approved/applied/rejected')
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='提交人')
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='审批人')
    submitted_at = db.Column(db.DateTime, comment='提交时间')
    approved_at = db.Column(db.DateTime, comment='审批时间')
    applied_at = db.Column(db.DateTime, comment='执行时间')
    reject_reason = db.Column(db.Text, comment='驳回原因')
    version = db.Column(db.Integer, default=1, comment='乐观锁版本号')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task = db.relationship('StockTakeTask')
    spare_part = db.relationship('SparePart')
    warehouse = db.relationship('Warehouse')

    def to_dict(self):
        return {
            'id': self.id,
            'adjust_code': self.adjust_code,
            'task_id': self.task_id,
            'stock_take_item_id': self.stock_take_item_id,
            'spare_part_id': self.spare_part_id,
            'spare_part_name': self.spare_part.name if self.spare_part else None,
            'spare_part_code': self.spare_part.part_code if self.spare_part else None,
            'warehouse_id': self.warehouse_id,
            'warehouse_name': self.warehouse.name if self.warehouse else None,
            'adjust_type': self.adjust_type,
            'adjust_qty': float(self.adjust_qty) if self.adjust_qty else 0,
            'reason': self.reason,
            'status': self.status,
            'submitted_by': self.submitted_by,
            'approved_by': self.approved_by,
            'submitted_at': self.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if self.submitted_at else None,
            'approved_at': self.approved_at.strftime('%Y-%m-%d %H:%M:%S') if self.approved_at else None,
            'applied_at': self.applied_at.strftime('%Y-%m-%d %H:%M:%S') if self.applied_at else None,
            'reject_reason': self.reject_reason,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }
