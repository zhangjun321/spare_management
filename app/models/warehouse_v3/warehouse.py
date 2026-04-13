"""
仓库模型 V3
基于百度千帆 AI 的智能化仓库管理系统
"""

from datetime import datetime
from app.extensions import db


class WarehouseV3(db.Model):
    """仓库表 V3"""
    
    __tablename__ = 'warehouse_v3'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='仓库 ID')
    code = db.Column(db.String(50), unique=True, nullable=False, comment='仓库编码')
    name = db.Column(db.String(100), nullable=False, comment='仓库名称')
    type = db.Column(db.String(50), nullable=False, default='general', comment='仓库类型')
    level = db.Column(db.String(20), default='A', comment='仓库等级')
    status = db.Column(db.String(20), default='active', comment='仓库状态')
    
    # 位置信息
    address = db.Column(db.String(200), comment='仓库地址')
    latitude = db.Column(db.Numeric(10, 8), comment='纬度')
    longitude = db.Column(db.Numeric(11, 8), comment='经度')
    
    # 容量信息
    total_area = db.Column(db.Numeric(10, 2), comment='总面积 (平方米)')
    usable_area = db.Column(db.Numeric(10, 2), comment='可用面积 (平方米)')
    total_volume = db.Column(db.Numeric(12, 2), comment='总容积 (立方米)')
    total_capacity = db.Column(db.Integer, comment='总容量 (托盘数)')
    
    # 管理信息
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='仓库管理员 ID')
    phone = db.Column(db.String(20), comment='联系电话')
    email = db.Column(db.String(100), comment='联系邮箱')
    
    # 配置信息
    temperature_control = db.Column(db.Boolean, default=False, comment='温控')
    humidity_control = db.Column(db.Boolean, default=False, comment='湿控')
    security_level = db.Column(db.String(20), default='normal', comment='安防等级')
    
    # AI 相关
    ai_enabled = db.Column(db.Boolean, default=True, comment='启用 AI')
    ai_config = db.Column(db.JSON, comment='AI 配置')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人')
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='更新人')
    
    # 其他
    description = db.Column(db.Text, comment='描述')
    remarks = db.Column(db.Text, comment='备注')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    
    # 关系
    locations = db.relationship('WarehouseLocationV3', back_populates='warehouse', lazy='dynamic')
    inventories = db.relationship('InventoryV3', back_populates='warehouse', lazy='dynamic')
    inbound_orders = db.relationship('InboundOrderV3', back_populates='warehouse', lazy='dynamic')
    outbound_orders = db.relationship('OutboundOrderV3', back_populates='warehouse', lazy='dynamic')
    inventory_checks = db.relationship('InventoryCheck', lazy='dynamic')
    
    # 索引
    __table_args__ = (
        db.Index('idx_code', 'code'),
        db.Index('idx_type', 'type'),
        db.Index('idx_status', 'status'),
    )
    
    def __repr__(self):
        return f'<WarehouseV3 {self.name} ({self.code})>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'type': self.type,
            'level': self.level,
            'status': self.status,
            'total_area': float(self.total_area) if self.total_area else None,
            'total_capacity': self.total_capacity,
            'ai_enabled': self.ai_enabled,
            'is_active': self.is_active
        }
