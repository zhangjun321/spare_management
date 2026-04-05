
"""
三级库位管理模型 - 库区、货架、货位
"""

from app.extensions import db
from datetime import datetime


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
        return '<WarehouseZone {}>'.format(self.zone_code)


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
        return '<WarehouseRack {}>'.format(self.rack_code)

