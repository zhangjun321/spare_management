from app.extensions import db
from datetime import datetime


class WarehouseLocation(db.Model):
    """货位表 - 最小存储单元（扩展版）"""
    
    __tablename__ = 'warehouse_location'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='货位 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, index=True, comment='仓库 ID')
    zone_id = db.Column(db.Integer, db.ForeignKey('warehouse_zone.id'), nullable=True, index=True, comment='库区 ID')
    shelf_id = db.Column(db.Integer, db.ForeignKey('warehouse_rack.id'), nullable=True, index=True, comment='货架 ID')
    location_code = db.Column(db.String(50), nullable=False, unique=True, index=True, comment='货位编码')
    location_name = db.Column(db.String(100), comment='货位名称')
    level = db.Column(db.Integer, comment='层')
    column = db.Column(db.Integer, comment='列')
    position = db.Column(db.Integer, comment='位置')
    max_volume = db.Column(db.Numeric(10, 2), comment='最大体积 (m³)')
    max_weight = db.Column(db.Numeric(10, 2), comment='最大承重 (kg)')
    current_volume = db.Column(db.Numeric(10, 2), default=0, comment='当前体积 (m³)')
    current_weight = db.Column(db.Numeric(10, 2), default=0, comment='当前重量 (kg)')
    location_type = db.Column(db.String(20), default='standard', comment='货位类型')
    status = db.Column(db.String(20), default='available', comment='状态')
    priority = db.Column(db.Integer, default=50, comment='优先级 (1-100)')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    
    # 关系
    warehouse = db.relationship('Warehouse', back_populates='locations')
    zone = db.relationship('WarehouseZone', foreign_keys=[zone_id])
    shelf = db.relationship('WarehouseRack', foreign_keys=[shelf_id])
    batches = db.relationship('Batch', foreign_keys='Batch.location_id', back_populates='location', lazy='dynamic')
    spare_parts = db.relationship('SparePart', foreign_keys='SparePart.location_id', back_populates='warehouse_location', lazy='dynamic')
    inventory_records = db.relationship('InventoryRecord', foreign_keys='InventoryRecord.location_id', back_populates='warehouse_location', lazy='dynamic')
    
    __table_args__ = (
        db.UniqueConstraint('warehouse_id', 'location_code', name='uq_warehouse_location'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'warehouse_id': self.warehouse_id,
            'zone_id': self.zone_id,
            'shelf_id': self.shelf_id,
            'location_code': self.location_code,
            'location_name': self.location_name,
            'level': self.level,
            'column': self.column,
            'position': self.position,
            'max_volume': float(self.max_volume) if self.max_volume else None,
            'max_weight': float(self.max_weight) if self.max_weight else None,
            'current_volume': float(self.current_volume) if self.current_volume else 0,
            'current_weight': float(self.current_weight) if self.current_weight else 0,
            'location_type': self.location_type,
            'status': self.status,
            'priority': self.priority,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<WarehouseLocation {self.location_code}>'
