
"""
库存盘点模型
支持循环盘点、全盘、差异处理
"""

from app.extensions import db
from datetime import datetime


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
        return '<InventoryCheck {}>'.format(self.check_code)


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
        return '<InventoryCheckItem {}>'.format(self.id)


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
        return '<StockAgeAnalysis {}>'.format(self.id)

