
"""
高级仓库管理模型
包含：库区、货架、库存盘点、库龄分析等
"""

from app.extensions import db
from datetime import datetime
from enum import Enum


class InventoryCheckStatus(Enum):
    """盘点状态枚举"""
    DRAFT = 'draft'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class InventoryCheckType(Enum):
    """盘点类型枚举"""
    FULL = 'full'
    CYCLICAL = 'cyclical'
    ABC = 'abc'
    RANDOM = 'random'


class WarehouseZone(db.Model):
    """库区表"""
    
    __tablename__ = 'warehouse_zone'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    zone_code = db.Column(db.String(20), nullable=False)
    zone_name = db.Column(db.String(100), nullable=False)
    zone_type = db.Column(db.String(20), nullable=False, default='general')
    
    temperature_min = db.Column(db.Numeric(5, 2), nullable=True)
    temperature_max = db.Column(db.Numeric(5, 2), nullable=True)
    humidity_min = db.Column(db.Numeric(5, 2), nullable=True)
    humidity_max = db.Column(db.Numeric(5, 2), nullable=True)
    
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_id])
    
    __table_args__ = (
        db.UniqueConstraint('warehouse_id', 'zone_code', name='uq_warehouse_zone'),
    )
    
    def __repr__(self):
        return f'<WarehouseZone {self.zone_code}>'


class WarehouseRack(db.Model):
    """货架表"""
    
    __tablename__ = 'warehouse_rack'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('warehouse_zone.id'), nullable=False)
    rack_code = db.Column(db.String(20), nullable=False)
    rack_name = db.Column(db.String(100), nullable=True)
    
    rack_type = db.Column(db.String(20), nullable=False, default='standard')
    levels_count = db.Column(db.Integer, default=5)
    max_weight_per_level = db.Column(db.Numeric(10, 2), nullable=True)
    
    position_x = db.Column(db.Integer, nullable=True)
    position_y = db.Column(db.Integer, nullable=True)
    
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    zone = db.relationship('WarehouseZone', foreign_keys=[zone_id])
    
    __table_args__ = (
        db.UniqueConstraint('zone_id', 'rack_code', name='uq_zone_rack'),
    )
    
    def __repr__(self):
        return f'<WarehouseRack {self.rack_code}>'


class InventoryCheck(db.Model):
    """库存盘点单表"""
    
    __tablename__ = 'inventory_check'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    check_code = db.Column(db.String(50), unique=True, nullable=False)
    check_name = db.Column(db.String(100), nullable=False)
    check_type = db.Column(db.String(20), nullable=False, default='full')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    
    abc_class = db.Column(db.String(1), nullable=True)
    
    status = db.Column(db.String(20), nullable=False, default='draft')
    
    total_items = db.Column(db.Integer, default=0)
    checked_items = db.Column(db.Integer, default=0)
    discrepancy_items = db.Column(db.Integer, default=0)
    discrepancy_value = db.Column(db.Numeric(15, 2), default=0)
    
    checked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    remark = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_id])
    
    def __repr__(self):
        return f'<InventoryCheck {self.check_code}>'


class InventoryCheckItem(db.Model):
    """库存盘点明细表"""
    
    __tablename__ = 'inventory_check_item'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inventory_check_id = db.Column(db.Integer, db.ForeignKey('inventory_check.id'), nullable=False)
    
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), nullable=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), nullable=True)
    
    system_quantity = db.Column(db.Integer, nullable=False, default=0)
    
    check_quantity = db.Column(db.Integer, nullable=True)
    second_check_quantity = db.Column(db.Integer, nullable=True)
    
    difference_quantity = db.Column(db.Integer, nullable=True)
    difference_value = db.Column(db.Numeric(15, 2), nullable=True)
    
    status = db.Column(db.String(20), nullable=False, default='pending')
    is_resolved = db.Column(db.Boolean, nullable=False, default=False)
    
    checked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    checked_at = db.Column(db.DateTime, nullable=True)
    second_checked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    second_checked_at = db.Column(db.DateTime, nullable=True)
    
    remark = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    inventory_check = db.relationship('InventoryCheck', foreign_keys=[inventory_check_id])
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    
    def __repr__(self):
        return f'<InventoryCheckItem {self.id}>'


class StockAgeAnalysis(db.Model):
    """库龄分析表"""
    
    __tablename__ = 'stock_age_analysis'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), nullable=True)
    
    stock_age_days = db.Column(db.Integer, nullable=False)
    stock_age_level = db.Column(db.String(20), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(15, 2), nullable=True)
    total_value = db.Column(db.Numeric(15, 2), nullable=True)
    
    is_slow_moving = db.Column(db.Boolean, nullable=False, default=False)
    is_obsolete = db.Column(db.Boolean, nullable=False, default=False)
    
    last_outbound_date = db.Column(db.DateTime, nullable=True)
    days_since_last_outbound = db.Column(db.Integer, nullable=True)
    
    analysis_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_id])
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    
    def __repr__(self):
        return f'<StockAgeAnalysis {self.id}>'

