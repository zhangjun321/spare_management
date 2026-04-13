"""
仓库与备件数据联动管理模型
包含：库存记录、入库单、出库单、操作日志等核心模型
"""

from datetime import datetime
from app.extensions import db
from sqlalchemy.dialects.mysql import JSON

# 从 inventory_record.py 导入 InventoryRecord，避免重复定义
from app.models.inventory_record import InventoryRecord

# 从 inbound_outbound.py 导入 InboundOrder 和 OutboundOrder，避免重复定义
from app.models.inbound_outbound import InboundOrder, OutboundOrder


# ==================== 入库单明细模型 ====================

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


# ==================== 出库单明细模型 ====================

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

from sqlalchemy import event, text


def _sync_spare_part_stock(connection, spare_part_id):
    """
    用原生 SQL 重新计算并更新 spare_part.current_stock
    使用 SUM(quantity) over all inventory_record rows for this spare_part
    """
    connection.execute(text("""
        UPDATE spare_part
        SET current_stock = COALESCE(
            (SELECT SUM(ir.quantity)
             FROM inventory_record ir
             WHERE ir.spare_part_id = :part_id),
            0
        )
        WHERE id = :part_id
    """), {"part_id": spare_part_id})


def _sync_warehouse_statistics(connection, warehouse_id):
    """
    用原生 SQL 重新计算并更新 warehouse 统计字段
    (total_inventory, total_spare_parts, utilization_rate)
    """
    connection.execute(text("""
        UPDATE warehouse w
        SET
            w.total_inventory = COALESCE(
                (SELECT SUM(ir.quantity)
                 FROM inventory_record ir
                 WHERE ir.warehouse_id = :wh_id),
                0
            ),
            w.total_spare_parts = COALESCE(
                (SELECT COUNT(DISTINCT ir.spare_part_id)
                 FROM inventory_record ir
                 WHERE ir.warehouse_id = :wh_id),
                0
            ),
            w.utilization_rate = CASE
                WHEN w.capacity IS NULL OR w.capacity = 0 THEN 0
                ELSE LEAST(100, ROUND(
                    COALESCE(
                        (SELECT SUM(ir.quantity)
                         FROM inventory_record ir
                         WHERE ir.warehouse_id = :wh_id),
                        0
                    ) * 100.0 / w.capacity, 2
                ))
            END
        WHERE w.id = :wh_id
    """), {"wh_id": warehouse_id})


@event.listens_for(InventoryRecord, 'after_insert')
def on_inventory_insert(mapper, connection, target):
    """库存记录插入后：同步备件库存总量和仓库统计"""
    _sync_spare_part_stock(connection, target.spare_part_id)
    _sync_warehouse_statistics(connection, target.warehouse_id)


@event.listens_for(InventoryRecord, 'after_update')
def on_inventory_update(mapper, connection, target):
    """库存记录更新后：同步备件库存总量和仓库统计"""
    _sync_spare_part_stock(connection, target.spare_part_id)
    _sync_warehouse_statistics(connection, target.warehouse_id)


@event.listens_for(InventoryRecord, 'after_delete')
def on_inventory_delete(mapper, connection, target):
    """库存记录删除后：同步备件库存总量和仓库统计"""
    _sync_spare_part_stock(connection, target.spare_part_id)
    _sync_warehouse_statistics(connection, target.warehouse_id)
