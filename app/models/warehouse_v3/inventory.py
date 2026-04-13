"""
库存模型 V3
"""

from datetime import datetime
from app.extensions import db


class InventoryV3(db.Model):
    """库存表 V3"""
    
    __tablename__ = 'inventory_v3'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='库存 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), nullable=False, comment='仓库 ID')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='货位 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), comment='批次 ID')
    
    # 数量信息
    quantity = db.Column(db.Numeric(12, 4), nullable=False, default=0, comment='当前数量')
    locked_quantity = db.Column(db.Numeric(12, 4), default=0, comment='锁定数量')
    available_quantity = db.Column(db.Numeric(12, 4), default=0, comment='可用数量')
    unit = db.Column(db.String(20), nullable=False, comment='单位')
    
    # 库存状态
    status = db.Column(db.String(20), default='normal', comment='库存状态')
    quality_status = db.Column(db.String(20), default='合格', comment='质量状态')
    
    # 入库信息
    inbound_date = db.Column(db.DateTime, comment='入库日期')
    production_date = db.Column(db.Date, comment='生产日期')
    expiry_date = db.Column(db.Date, comment='有效期至')
    shelf_life = db.Column(db.Integer, comment='保质期 (天)')
    
    # 成本信息
    unit_cost = db.Column(db.Numeric(12, 2), comment='单位成本')
    total_cost = db.Column(db.Numeric(14, 2), comment='总成本')
    last_purchase_price = db.Column(db.Numeric(12, 2), comment='最后采购价')
    
    # 库存控制
    min_quantity = db.Column(db.Numeric(12, 4), comment='最小库存')
    max_quantity = db.Column(db.Numeric(12, 4), comment='最大库存')
    reorder_point = db.Column(db.Numeric(12, 4), comment='reorder 点')
    reorder_quantity = db.Column(db.Numeric(12, 4), comment='reorder 数量')
    
    # ABC 分类
    abc_class = db.Column(db.String(5), default='C', comment='ABC 分类')
    turnover_rate = db.Column(db.Numeric(8, 4), default=0, comment='周转率')
    last_movement_date = db.Column(db.DateTime, comment='最后移动日期')
    
    # AI 分析
    demand_forecast = db.Column(db.JSON, comment='需求预测')
    ai_recommendations = db.Column(db.JSON, comment='AI 建议')
    risk_score = db.Column(db.Numeric(5, 2), comment='风险评分')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 乐观锁版本号
    version = db.Column(db.Integer, default=0, nullable=False, comment='版本号')
    
    # 其他
    remarks = db.Column(db.Text)
    
    # 关系
    warehouse = db.relationship('WarehouseV3', back_populates='inventories')
    location = db.relationship('WarehouseLocationV3', back_populates='inventories')
    part = db.relationship('SparePart')
    batch = db.relationship('Batch')
    
    # 索引
    __table_args__ = (
        db.UniqueConstraint('warehouse_id', 'part_id', 'batch_id', name='uk_warehouse_part_batch'),
        db.Index('idx_warehouse', 'warehouse_id'),
        db.Index('idx_part', 'part_id'),
        db.Index('idx_location', 'location_id'),
        db.Index('idx_status', 'status'),
    )
    
    def __repr__(self):
        return f'<InventoryV3 {self.part_id}@{self.warehouse_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'warehouse_id': self.warehouse_id,
            'part_id': self.part_id,
            'quantity': float(self.quantity) if self.quantity else 0,
            'available_quantity': float(self.available_quantity) if self.available_quantity else 0,
            'status': self.status,
            'abc_class': self.abc_class
        }
    
    def get_expiry_days(self):
        """获取距离过期的天数"""
        from datetime import datetime
        
        if not self.expiry_date:
            return None
        
        today = datetime.now().date()
        delta = self.expiry_date - today
        return delta.days
    
    def is_near_expiry(self, days_threshold=30):
        """检查是否接近过期"""
        days = self.get_expiry_days()
        if days is None:
            return False
        return 0 <= days <= days_threshold
    
    def is_expired(self):
        """检查是否已过期"""
        from datetime import datetime
        
        if not self.expiry_date:
            return False
        
        return datetime.now().date() > self.expiry_date
