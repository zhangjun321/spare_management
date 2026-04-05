"""
仓库与备件数据联动管理模型
包含：库存记录、入库单、出库单、操作日志等核心模型
"""

from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.mysql import JSON


# ==================== 库存记录模型 ====================

class InventoryRecord(db.Model):
    """
    库存记录表 - 核心联动表
    建立仓库与备件的多对多关联关系
    """
    __tablename__ = 'inventory_record'
    
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, index=True)
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), nullable=False, index=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True)
    
    # 批次信息
    batch_number = db.Column(db.String(100), index=True)  # 批次号
    
    # 数量信息
    quantity = db.Column(db.Integer, default=0, nullable=False)  # 当前数量
    initial_quantity = db.Column(db.Integer, default=0)  # 初始数量
    locked_quantity = db.Column(db.Integer, default=0)  # 锁定数量（已分配未出库）
    
    # 价值信息
    unit_price = db.Column(db.Float, default=0.0)  # 入库单价
    total_value = db.Column(db.Float, default=0.0)  # 总价值 = quantity * unit_price
    
    # 时间信息
    entry_date = db.Column(db.DateTime, default=datetime.utcnow)  # 入库日期
    expiry_date = db.Column(db.DateTime)  # 有效期
    last_check_date = db.Column(db.DateTime)  # 最后盘点日期
    
    # 库龄信息
    stock_age_days = db.Column(db.Integer, default=0)  # 库存天数
    
    # 状态
    status = db.Column(db.String(20), default='normal', index=True)  # normal/locked/damaged/expired
    
    # 操作信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # 关联关系
    warehouse = db.relationship('Warehouse', backref=db.backref('inventory_records', lazy='dynamic', cascade='all, delete-orphan'))
    location = db.relationship('WarehouseLocation', backref=db.backref('inventory_records', lazy='dynamic', cascade='all, delete-orphan'))
    spare_part = db.relationship('SparePart', backref=db.backref('inventory_records', lazy='dynamic', cascade='all, delete-orphan'))
    creator = db.relationship('User', foreign_keys=[created_by])
    
    # 索引
    __table_args__ = (
        db.Index('idx_warehouse_part_location', 'warehouse_id', 'spare_part_id', 'location_id'),
        db.Index('idx_batch', 'batch_number'),
        db.Index('idx_status', 'status'),
    )
    
    def __repr__(self):
        return f'<InventoryRecord {self.id} - Part:{self.spare_part_id} Warehouse:{self.warehouse_id}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'warehouse_id': self.warehouse_id,
            'location_id': self.location_id,
            'spare_part_id': self.spare_part_id,
            'batch_number': self.batch_number,
            'quantity': self.quantity,
            'initial_quantity': self.initial_quantity,
            'locked_quantity': self.locked_quantity,
            'unit_price': self.unit_price,
            'total_value': self.total_value,
            'entry_date': self.entry_date.strftime('%Y-%m-%d') if self.entry_date else None,
            'expiry_date': self.expiry_date.strftime('%Y-%m-%d') if self.expiry_date else None,
            'stock_age_days': self.stock_age_days,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }
    
    def is_available(self):
        """是否可用"""
        return self.status == 'normal' and self.quantity > self.locked_quantity
    
    def available_quantity(self):
        """可用数量"""
        return self.quantity - self.locked_quantity


# ==================== 入库单模型 ====================

class InboundOrder(db.Model):
    """入库单"""
    __tablename__ = 'inbound_order'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(100), unique=True, nullable=False, index=True)  # 入库单号
    
    # 类型
    type = db.Column(db.String(50), default='purchase')  # purchase/return/transfer/other
    status = db.Column(db.String(20), default='pending', index=True)  # pending/processing/completed/cancelled
    
    # 供应商信息
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    
    # 仓库信息
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'))
    
    # AI 推荐信息
    ai_recommended = db.Column(db.Boolean, default=False)
    ai_recommendation_data = db.Column(JSON)  # AI 推荐详情
    
    # 操作信息
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    completed_at = db.Column(db.DateTime)
    
    # 备注
    remark = db.Column(db.Text)
    
    # 关联关系
    supplier = db.relationship('Supplier', backref='inbound_orders')
    warehouse = db.relationship('Warehouse', backref='inbound_orders')
    creator = db.relationship('User', foreign_keys=[created_by])
    completer = db.relationship('User', foreign_keys=[completed_by])
    items = db.relationship('InboundOrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    # operations 关系移除，因为 OperationLog 使用通用关联
    
    def __repr__(self):
        return f'<InboundOrder {self.order_number}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'order_number': self.order_number,
            'type': self.type,
            'status': self.status,
            'warehouse_id': self.warehouse_id,
            'ai_recommended': self.ai_recommended,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None,
            'item_count': self.items.count(),
        }


class InboundOrderItem(db.Model):
    """入库单明细"""
    __tablename__ = 'inbound_order_item'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('inbound_order.id'), nullable=False, index=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False)
    
    # 数量信息
    planned_quantity = db.Column(db.Integer, nullable=False)  # 计划数量
    actual_quantity = db.Column(db.Integer)  # 实际数量
    received_quantity = db.Column(db.Integer, default=0)  # 已入库数量
    
    # 库位分配
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'))
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'))
    ai_recommended_location = db.Column(db.Boolean, default=False)
    
    # 批次信息
    batch_number = db.Column(db.String(100))
    production_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    
    # 价值信息
    unit_price = db.Column(db.Float, default=0.0)
    total_value = db.Column(db.Float, default=0.0)
    
    # 状态
    status = db.Column(db.String(20), default='pending')  # pending/received/completed
    
    # 关联关系
    spare_part = db.relationship('SparePart')
    warehouse = db.relationship('Warehouse')
    location = db.relationship('WarehouseLocation')
    
    __table_args__ = (
        db.Index('idx_order_part', 'order_id', 'spare_part_id'),
    )
    
    def __repr__(self):
        return f'<InboundOrderItem {self.id} - Order:{self.order_id}>'


# ==================== 出库单模型 ====================

class OutboundOrder(db.Model):
    """出库单"""
    __tablename__ = 'outbound_order'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(100), unique=True, nullable=False, index=True)  # 出库单号
    
    # 类型
    type = db.Column(db.String(50), default='requisition')  # requisition/sale/transfer/other
    status = db.Column(db.String(20), default='pending', index=True)  # pending/approved/processing/completed/cancelled
    
    # 出库策略
    strategy = db.Column(db.String(50), default='fifo')  # fifo/lifo/fefo/manual
    
    # 仓库信息
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'))
    
    # 领用信息
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    department = db.Column(db.String(100))
    purpose = db.Column(db.String(500))  # 用途
    
    # 审批信息
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)
    
    # 操作信息
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    completed_at = db.Column(db.DateTime)
    
    # 备注
    remark = db.Column(db.Text)
    
    # 关联关系
    warehouse = db.relationship('Warehouse', backref='outbound_orders')
    requester = db.relationship('User', foreign_keys=[requester_id])
    approver = db.relationship('User', foreign_keys=[approved_by])
    creator = db.relationship('User', foreign_keys=[created_by])
    completer = db.relationship('User', foreign_keys=[completed_by])
    items = db.relationship('OutboundOrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    # operations 关系移除，因为 OperationLog 使用通用关联
    
    def __repr__(self):
        return f'<OutboundOrder {self.order_number}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'order_number': self.order_number,
            'type': self.type,
            'status': self.status,
            'strategy': self.strategy,
            'warehouse_id': self.warehouse_id,
            'department': self.department,
            'purpose': self.purpose,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'approved_at': self.approved_at.strftime('%Y-%m-%d %H:%M:%S') if self.approved_at else None,
            'item_count': self.items.count(),
        }


class OutboundOrderItem(db.Model):
    """出库单明细"""
    __tablename__ = 'outbound_order_item'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('outbound_order.id'), nullable=False, index=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False)
    
    # 数量信息
    requested_quantity = db.Column(db.Integer, nullable=False)  # 申请数量
    approved_quantity = db.Column(db.Integer)  # 批准数量
    issued_quantity = db.Column(db.Integer, default=0)  # 已出库数量
    
    # 关联关系
    spare_part = db.relationship('SparePart')
    source_locations = db.relationship('OutboundSourceLocation', backref='order_item', lazy='dynamic', cascade='all, delete-orphan')
    
    # 状态
    status = db.Column(db.String(20), default='pending')  # pending/approved/issued
    
    __table_args__ = (
        db.Index('idx_order_part', 'order_id', 'spare_part_id'),
    )
    
    def __repr__(self):
        return f'<OutboundOrderItem {self.id} - Order:{self.order_id}>'


class OutboundSourceLocation(db.Model):
    """出库来源库位 - 支持从多个库位出库"""
    __tablename__ = 'outbound_source_location'
    
    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey('outbound_order_item.id'), nullable=False, index=True)
    inventory_record_id = db.Column(db.Integer, db.ForeignKey('inventory_record.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)  # 从该库位出库的数量
    
    # 关联关系
    inventory_record = db.relationship('InventoryRecord')
    location = db.relationship('WarehouseLocation')
    
    def __repr__(self):
        return f'<OutboundSourceLocation {self.id} - Item:{self.order_item_id}>'


# ==================== 操作日志模型 ====================

class OperationLog(db.Model):
    """操作日志 - 用于追溯和撤销"""
    __tablename__ = 'operation_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 关联单据
    order_type = db.Column(db.String(50), index=True)  # inbound/outbound/transfer/adjustment
    order_id = db.Column(db.Integer, index=True)
    
    # 操作类型
    action = db.Column(db.String(50), nullable=False, index=True)  # create/approve/execute/cancel/rollback
    
    # 操作详情
    details = db.Column(JSON)
    before_data = db.Column(JSON)  # 操作前数据快照
    after_data = db.Column(JSON)  # 操作后数据快照
    
    # 操作者信息
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    operator_name = db.Column(db.String(100))
    ip_address = db.Column(db.String(50))
    device_info = db.Column(db.String(200))
    
    # 时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 撤销相关
    can_rollback = db.Column(db.Boolean, default=True)
    rollback_executed = db.Column(db.Boolean, default=False)
    rollback_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    rollback_at = db.Column(db.DateTime)
    
    # 关联关系
    operator = db.relationship('User', foreign_keys=[operator_id])
    rollback_user = db.relationship('User', foreign_keys=[rollback_by])
    
    __table_args__ = (
        db.Index('idx_order', 'order_type', 'order_id'),
    )
    
    def __repr__(self):
        return f'<OperationLog {self.id} - {self.order_type}:{self.order_id} {self.action}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'order_type': self.order_type,
            'order_id': self.order_id,
            'action': self.action,
            'details': self.details,
            'operator_name': self.operator_name,
            'ip_address': self.ip_address,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'can_rollback': self.can_rollback,
            'rollback_executed': self.rollback_executed,
        }


# ==================== 数据联动事件监听器 ====================

from sqlalchemy import event

@event.listens_for(InventoryRecord, 'after_insert')
def on_inventory_insert(mapper, connection, target):
    """库存记录插入后的联动处理"""
    # 更新仓库统计信息
    # 更新备件库存总量
    pass


@event.listens_for(InventoryRecord, 'after_update')
def on_inventory_update(mapper, connection, target):
    """库存记录更新后的联动处理"""
    # 更新仓库统计信息
    # 更新备件库存总量
    # 触发 AI 分析（如需要）
    pass


@event.listens_for(InventoryRecord, 'after_delete')
def on_inventory_delete(mapper, connection, target):
    """库存记录删除后的联动处理"""
    # 更新仓库统计信息
    # 更新备件库存总量
    pass
