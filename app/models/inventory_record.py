"""
库存记录模型 - 核心联动表
连接备件、仓库、货位，实现备件与仓库的深度联动
"""

from datetime import datetime
from app.extensions import db


class InventoryRecord(db.Model):
    """
    库存记录表 - 核心联动表
    
    每个备件在每个仓库的每个货位都有一条记录
    通过数据库触发器自动同步备件表和仓库表的库存数据
    """
    
    __tablename__ = 'inventory_record'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='库存记录 ID')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, index=True, comment='仓库 ID')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), nullable=True, index=True, comment='货位 ID')
    
    # 库存数量
    quantity = db.Column(db.Integer, nullable=False, default=0, comment='库存数量')
    locked_quantity = db.Column(db.Integer, nullable=False, default=0, comment='锁定数量（已分配未出库）')
    available_quantity = db.Column(db.Integer, nullable=False, default=0, comment='可用数量')
    
    # 库存状态
    stock_status = db.Column(db.String(20), nullable=False, default='normal', index=True, comment='库存状态')
    # normal-正常，low-低库存，out-缺货，overstocked-超储，locked-锁定
    
    # 批次信息
    batch_number = db.Column(db.String(50), index=True, comment='批次号')
    production_date = db.Column(db.Date, comment='生产日期')
    expiry_date = db.Column(db.Date, comment='有效期至')
    
    # 库存金额
    unit_cost = db.Column(db.Numeric(12, 2), comment='单位成本')
    total_amount = db.Column(db.Numeric(12, 2), comment='总金额')
    
    # 库存预警
    min_stock = db.Column(db.Integer, default=0, comment='最低库存')
    max_stock = db.Column(db.Integer, comment='最高库存')
    safety_stock = db.Column(db.Integer, default=0, comment='安全库存')
    
    # 最后操作信息
    last_inbound_time = db.Column(db.DateTime, comment='最后入库时间')
    last_outbound_time = db.Column(db.DateTime, comment='最后出库时间')
    last_check_time = db.Column(db.DateTime, comment='最后盘点时间')
    
    # 备注和扩展字段
    remark = db.Column(db.Text, comment='备注')
    extra_data = db.Column(db.JSON, comment='扩展数据')
    
    # 审计字段
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='更新人 ID')
    
    # 关系
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id], back_populates='inventory_records')
    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_id], back_populates='inventory_records')
    warehouse_location = db.relationship('WarehouseLocation', foreign_keys=[location_id], back_populates='inventory_records')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_inventory_records')
    updater = db.relationship('User', foreign_keys=[updated_by], backref='updated_inventory_records')
    
    # 入库单和出库单关系
    inbound_orders = db.relationship('InboundOrder', foreign_keys='InboundOrder.inventory_record_id', back_populates='inventory_record', lazy='dynamic')
    outbound_orders = db.relationship('OutboundOrder', foreign_keys='OutboundOrder.inventory_record_id', back_populates='inventory_record', lazy='dynamic')
    
    def __repr__(self):
        return f'<InventoryRecord SP:{self.spare_part_id} WH:{self.warehouse_id} LOC:{self.location_id} QTY:{self.quantity}>'
    
    def update_stock_status(self):
        """更新库存状态"""
        old_status = self.stock_status
        
        # 更新库存状态
        if self.quantity == 0:
            self.stock_status = 'out'  # 缺货
        elif self.quantity <= self.min_stock:
            self.stock_status = 'low'  # 低库存
        elif self.max_stock and self.quantity >= self.max_stock:
            self.stock_status = 'overstocked'  # 超储
        elif self.locked_quantity > 0 and self.locked_quantity >= self.quantity:
            self.stock_status = 'locked'  # 锁定
        else:
            self.stock_status = 'normal'  # 正常
        
        return old_status != self.stock_status
    
    def update_available_quantity(self):
        """更新可用数量"""
        self.available_quantity = self.quantity - self.locked_quantity
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'spare_part_id': self.spare_part_id,
            'warehouse_id': self.warehouse_id,
            'location_id': self.location_id,
            'quantity': self.quantity,
            'locked_quantity': self.locked_quantity,
            'available_quantity': self.available_quantity,
            'stock_status': self.stock_status,
            'batch_number': self.batch_number,
            'production_date': self.production_date.isoformat() if self.production_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'unit_cost': float(self.unit_cost) if self.unit_cost else None,
            'total_amount': float(self.total_amount) if self.total_amount else None,
            'min_stock': self.min_stock,
            'max_stock': self.max_stock,
            'safety_stock': self.safety_stock,
            'last_inbound_time': self.last_inbound_time.isoformat() if self.last_inbound_time else None,
            'last_outbound_time': self.last_outbound_time.isoformat() if self.last_outbound_time else None,
            'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
