"""
仓库模型 - 扩展版
"""

from datetime import datetime
from app.extensions import db


class Warehouse(db.Model):
    """仓库表 - 扩展版"""
    
    __tablename__ = 'warehouse'
    
    # === 基础字段（13 个） ===
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='仓库 ID')
    name = db.Column(db.String(100), nullable=False, comment='仓库名称')
    code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='仓库编码')
    type = db.Column(db.String(20), nullable=False, default='general', comment='仓库类型')
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, comment='仓库管理员 ID')
    address = db.Column(db.String(500), nullable=True, comment='仓库地址')
    area = db.Column(db.Numeric(10, 2), nullable=True, comment='仓库面积 (㎡)')
    capacity = db.Column(db.Integer, nullable=True, comment='仓库容量 (件)')
    phone = db.Column(db.String(20), nullable=True, comment='联系电话')
    description = db.Column(db.Text, nullable=True, comment='仓库描述')
    is_active = db.Column(db.Boolean, nullable=False, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # === 图片字段（7 个） ===
    image_url = db.Column(db.String(500), comment='仓库主图 URL')
    thumbnail_url = db.Column(db.String(500), comment='仓库缩略图 URL')
    interior_image_url = db.Column(db.String(500), comment='仓库内部图 URL')
    exterior_image_url = db.Column(db.String(500), comment='仓库外观图 URL')
    location_map_url = db.Column(db.String(500), comment='仓库位置地图 URL')
    layout_image_url = db.Column(db.String(500), comment='仓库布局图 URL')
    thumbnail_map_url = db.Column(db.String(500), comment='缩略地图 URL')
    
    # === 统计字段（5 个，冗余存储） ===
    total_inventory = db.Column(db.Integer, default=0, comment='总库存数量')
    total_spare_parts = db.Column(db.Integer, default=0, comment='总备件种类数')
    utilization_rate = db.Column(db.Numeric(5, 2), default=0, comment='仓库利用率 (%)')
    last_inventory_date = db.Column(db.DateTime, comment='最后盘点日期')
    last_inbound_date = db.Column(db.DateTime, comment='最后入库日期')
    last_outbound_date = db.Column(db.DateTime, comment='最后出库日期')
    
    # === 预警配置（3 个） ===
    capacity_warning_threshold = db.Column(db.Integer, default=90, comment='容量预警阈值 (%)')
    utilization_warning_threshold = db.Column(db.Integer, default=85, comment='利用率预警阈值 (%)')
    enable_auto_alert = db.Column(db.Boolean, default=True, comment='是否启用自动预警')
    
    # === 关系 ===
    manager = db.relationship('User', foreign_keys=[manager_id], back_populates='managed_warehouses')
    zones = db.relationship('WarehouseZone', back_populates='warehouse', lazy='dynamic', cascade='all, delete-orphan')
    locations = db.relationship('WarehouseLocation', back_populates='warehouse', lazy='dynamic')
    batches = db.relationship('Batch', back_populates='warehouse', lazy='dynamic')
    transactions = db.relationship('Transaction', back_populates='warehouse', lazy='dynamic')
    spare_parts = db.relationship('SparePart', back_populates='warehouse', lazy='dynamic')
    inventory_records = db.relationship('InventoryRecord', back_populates='warehouse', lazy='dynamic')
    
    def to_dict(self, include_details=False):
        """转换为字典（用于 API 返回）"""
        data = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'type': self.type,
            'manager_id': self.manager_id,
            'address': self.address,
            'area': float(self.area) if self.area else None,
            'capacity': self.capacity,
            'phone': self.phone,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            
            # 图片字段
            'image_url': self.image_url,
            'thumbnail_url': self.thumbnail_url,
            'interior_image_url': self.interior_image_url,
            'exterior_image_url': self.exterior_image_url,
            'location_map_url': self.location_map_url,
            'layout_image_url': self.layout_image_url,
            'thumbnail_map_url': self.thumbnail_map_url,
            
            # 统计字段
            'total_inventory': self.total_inventory,
            'total_spare_parts': self.total_spare_parts,
            'utilization_rate': float(self.utilization_rate) if self.utilization_rate else 0,
            'last_inventory_date': self.last_inventory_date.isoformat() if self.last_inventory_date else None,
            'last_inbound_date': self.last_inbound_date.isoformat() if self.last_inbound_date else None,
            'last_outbound_date': self.last_outbound_date.isoformat() if self.last_outbound_date else None,
            
            # 预警配置
            'capacity_warning_threshold': self.capacity_warning_threshold,
            'utilization_warning_threshold': self.utilization_warning_threshold,
            'enable_auto_alert': self.enable_auto_alert,
        }
        
        # 包含管理员信息
        if self.manager:
            data['manager'] = {
                'id': self.manager.id,
                'username': self.manager.username,
                'email': self.manager.email,
                'phone': self.manager.phone
            }
        
        # 包含库区/货位统计
        if include_details:
            data['zones_count'] = self.zones.count()
            data['locations_count'] = self.locations.count()
            data['available_locations_count'] = self.locations.filter(
                WarehouseLocation.status == 'available'
            ).count() if hasattr(self, 'locations') else 0
        
        return data
    
    def update_statistics(self):
        """更新仓库统计数据"""
        from app.models.inventory import InventoryRecord
        
        # 统计总库存
        total_inventory = db.session.query(
            db.func.sum(InventoryRecord.quantity)
        ).filter(
            InventoryRecord.warehouse_id == self.id
        ).scalar() or 0
        
        # 统计备件种类数
        total_spare_parts = db.session.query(
            db.func.count(db.distinct(InventoryRecord.spare_part_id))
        ).filter(
            InventoryRecord.warehouse_id == self.id
        ).scalar() or 0
        
        # 计算利用率
        utilization_rate = 0
        if self.capacity:
            utilization_rate = min(100, (total_inventory / self.capacity) * 100)
        
        # 更新字段
        self.total_inventory = total_inventory
        self.total_spare_parts = total_spare_parts
        self.utilization_rate = utilization_rate
        
        db.session.commit()
    
    def __repr__(self):
        return f'<Warehouse {self.name}>'
