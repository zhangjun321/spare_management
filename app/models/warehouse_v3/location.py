"""
货位模型 V3
"""

from datetime import datetime
from app.extensions import db


class WarehouseLocationV3(db.Model):
    """货位表 V3"""
    
    __tablename__ = 'warehouse_location_v3'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='货位 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), nullable=False, comment='仓库 ID')
    code = db.Column(db.String(50), nullable=False, comment='货位编码')
    name = db.Column(db.String(100), comment='货位名称')
    
    # 位置信息
    zone_code = db.Column(db.String(50), comment='区域编码')
    aisle_code = db.Column(db.String(50), comment='通道编码')
    rack_code = db.Column(db.String(50), comment='货架编码')
    level_code = db.Column(db.String(10), comment='层编码')
    
    # 类型和规格
    type = db.Column(db.String(50), default='standard', comment='货位类型')
    size_type = db.Column(db.String(20), default='medium', comment='尺寸类型')
    length = db.Column(db.Numeric(8, 2), comment='长度 (cm)')
    width = db.Column(db.Numeric(8, 2), comment='宽度 (cm)')
    height = db.Column(db.Numeric(8, 2), comment='高度 (cm)')
    max_weight = db.Column(db.Numeric(10, 2), comment='最大承重 (kg)')
    max_volume = db.Column(db.Numeric(10, 2), comment='最大容积 (m³)')
    
    # 状态信息
    status = db.Column(db.String(20), default='available', comment='货位状态')
    occupied_volume = db.Column(db.Numeric(8, 2), default=0, comment='已占容积')
    occupied_weight = db.Column(db.Numeric(8, 2), default=0, comment='已占重量')
    
    # 存储策略
    storage_type = db.Column(db.String(50), default='mixed', comment='存储类型')
    temperature_range = db.Column(db.String(50), comment='温度范围')
    humidity_range = db.Column(db.String(50), comment='湿度范围')
    
    # AI 优化
    priority = db.Column(db.Integer, default=0, comment='优先级')
    ai_score = db.Column(db.Numeric(5, 2), comment='AI 评分')
    utilization_rate = db.Column(db.Numeric(5, 2), default=0, comment='利用率')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 其他
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # 关系
    warehouse = db.relationship('WarehouseV3', back_populates='locations')
    inventories = db.relationship('InventoryV3', back_populates='location', lazy='dynamic')
    
    # 索引
    __table_args__ = (
        db.UniqueConstraint('warehouse_id', 'code', name='uk_warehouse_code'),
        db.Index('idx_warehouse', 'warehouse_id'),
        db.Index('idx_status', 'status'),
        db.Index('idx_zone', 'zone_code'),
    )
    
    def __repr__(self):
        return f'<WarehouseLocationV3 {self.code}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'warehouse_id': self.warehouse_id,
            'type': self.type,
            'status': self.status,
            'ai_score': float(self.ai_score) if self.ai_score else None
        }
