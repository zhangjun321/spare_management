# -*- coding: utf-8 -*-
"""
调拨单模型 — 跨仓库/库区调拨与在途库存管理

状态机: draft → submitted → approved → in_transit → received → completed
         ↓ any state → cancelled
"""
from app.extensions import db
from datetime import datetime


class TransferOrder(db.Model):
    """调拨单主表"""
    __tablename__ = 'transfer_order'

    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='调拨单号(TO前缀)')
    from_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, comment='调出仓库')
    to_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, comment='调入仓库')
    status = db.Column(db.String(20), default='draft', comment='状态: draft/submitted/approved/in_transit/received/completed/cancelled')
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='申请人')
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='审批人')
    shipper_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='发货人')
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='收货人')
    remark = db.Column(db.Text, comment='备注')
    eta = db.Column(db.DateTime, comment='预计到达时间')
    submitted_at = db.Column(db.DateTime, comment='提交时间')
    approved_at = db.Column(db.DateTime, comment='审批时间')
    shipped_at = db.Column(db.DateTime, comment='发货时间')
    received_at = db.Column(db.DateTime, comment='收货时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    cancelled_at = db.Column(db.DateTime, comment='取消时间')
    cancel_reason = db.Column(db.Text, comment='取消原因')
    cancelled_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='取消人')
    version = db.Column(db.Integer, default=1, comment='乐观锁版本号')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    from_warehouse = db.relationship('Warehouse', foreign_keys=[from_warehouse_id])
    to_warehouse = db.relationship('Warehouse', foreign_keys=[to_warehouse_id])
    requester = db.relationship('User', foreign_keys=[requester_id])
    approver = db.relationship('User', foreign_keys=[approver_id])
    shipper = db.relationship('User', foreign_keys=[shipper_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])
    items = db.relationship('TransferOrderItem', back_populates='transfer_order', cascade='all, delete-orphan')

    # Valid status transitions
    TRANSITIONS = {
        'draft':      ['submitted', 'cancelled'],
        'submitted':  ['approved', 'cancelled', 'draft'],
        'approved':   ['in_transit', 'cancelled'],
        'in_transit': ['received', 'cancelled'],
        'received':   ['completed'],
        'completed':  [],
        'cancelled':  [],
    }

    def can_transit(self, target):
        return target in self.TRANSITIONS.get(self.status, [])

    def transit(self, target, operator_id=None):
        if not self.can_transit(target):
            raise ValueError(f'不允许从 {self.status} 转为 {target}')
        old = self.status
        self.status = target
        self.version += 1
        now = datetime.utcnow()
        if target == 'submitted':
            self.submitted_at = now
        elif target == 'approved':
            self.approved_at = now
            self.approver_id = operator_id
        elif target == 'in_transit':
            self.shipped_at = now
            self.shipper_id = operator_id
        elif target == 'received':
            self.received_at = now
            self.receiver_id = operator_id
        elif target == 'completed':
            self.completed_at = now
        elif target == 'cancelled':
            self.cancelled_at = now
            self.cancelled_by = operator_id

    def to_dict(self):
        return {
            'id': self.id,
            'order_code': self.order_code,
            'from_warehouse_id': self.from_warehouse_id,
            'from_warehouse_name': self.from_warehouse.name if self.from_warehouse else None,
            'to_warehouse_id': self.to_warehouse_id,
            'to_warehouse_name': self.to_warehouse.name if self.to_warehouse else None,
            'status': self.status,
            'requester_id': self.requester_id,
            'requester_name': self.requester.username if self.requester else None,
            'approver_id': self.approver_id,
            'approver_name': self.approver.username if self.approver else None,
            'remark': self.remark,
            'eta': self.eta.strftime('%Y-%m-%d %H:%M:%S') if self.eta else None,
            'submitted_at': self.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if self.submitted_at else None,
            'approved_at': self.approved_at.strftime('%Y-%m-%d %H:%M:%S') if self.approved_at else None,
            'shipped_at': self.shipped_at.strftime('%Y-%m-%d %H:%M:%S') if self.shipped_at else None,
            'received_at': self.received_at.strftime('%Y-%m-%d %H:%M:%S') if self.received_at else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None,
            'items': [item.to_dict() for item in self.items] if self.items else [],
            'item_count': len(self.items) if self.items else 0,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }


class TransferOrderItem(db.Model):
    """调拨单明细"""
    __tablename__ = 'transfer_order_item'

    id = db.Column(db.Integer, primary_key=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey('transfer_order.id'), nullable=False, index=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True)
    quantity = db.Column(db.Numeric(10, 2), nullable=False, comment='调拨数量')
    batch_no = db.Column(db.String(100), comment='批次号')
    item_status = db.Column(db.String(20), default='pending', comment='明细状态: pending/shipped/received')
    shipped_quantity = db.Column(db.Numeric(10, 2), default=0, comment='已发数量')
    received_quantity = db.Column(db.Numeric(10, 2), default=0, comment='已收数量')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transfer_order = db.relationship('TransferOrder', back_populates='items')
    spare_part = db.relationship('SparePart')

    def to_dict(self):
        return {
            'id': self.id,
            'transfer_id': self.transfer_id,
            'spare_part_id': self.spare_part_id,
            'spare_part_code': self.spare_part.part_code if self.spare_part else None,
            'spare_part_name': self.spare_part.name if self.spare_part else None,
            'quantity': float(self.quantity) if self.quantity else 0,
            'batch_no': self.batch_no,
            'item_status': self.item_status,
            'shipped_quantity': float(self.shipped_quantity) if self.shipped_quantity else 0,
            'received_quantity': float(self.received_quantity) if self.received_quantity else 0,
            'remark': self.remark,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }
