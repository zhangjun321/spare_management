"""
库存盘点模型
"""

from datetime import datetime
from app.extensions import db


class InventoryCheck(db.Model):
    """库存盘点单"""
    
    __tablename__ = 'inventory_check'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='盘点单 ID')
    check_no = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='盘点单号')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), nullable=False, comment='仓库 ID')
    check_type = db.Column(db.String(20), nullable=False, comment='盘点类型：定期/循环/动态')
    status = db.Column(db.String(20), default='planned', comment='盘点状态')
    
    # 计划信息
    planned_date = db.Column(db.Date, comment='计划盘点日期')
    start_date = db.Column(db.DateTime, comment='开始日期')
    end_date = db.Column(db.DateTime, comment='结束日期')
    
    # 人员信息
    checker_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='盘点人')
    
    # 汇总信息
    total_items = db.Column(db.Integer, default=0, comment='总项数')
    checked_items = db.Column(db.Integer, default=0, comment='已盘点项数')
    difference_items = db.Column(db.Integer, default=0, comment='差异项数')
    
    # 备注
    notes = db.Column(db.Text, comment='备注')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    warehouse = db.relationship('WarehouseV3')
    checker = db.relationship('User', foreign_keys=[checker_id])
    items = db.relationship('InventoryCheckItem', back_populates='check', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<InventoryCheck {self.check_no}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'check_no': self.check_no,
            'warehouse_id': self.warehouse_id,
            'warehouse_name': self.warehouse.name if self.warehouse else None,
            'check_type': self.check_type,
            'status': self.status,
            'planned_date': self.planned_date.strftime('%Y-%m-%d') if self.planned_date else None,
            'start_date': self.start_date.strftime('%Y-%m-%d %H:%M:%S') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d %H:%M:%S') if self.end_date else None,
            'checker_id': self.checker_id,
            'checker_name': self.checker.name if self.checker else None,
            'total_items': self.total_items,
            'checked_items': self.checked_items,
            'difference_items': self.difference_items,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
    
    @staticmethod
    def generate_check_no():
        """生成盘点单号"""
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d')
        # 获取当天的最大单号
        last_check = InventoryCheck.query.filter(
            InventoryCheck.check_no.like(f'CHK-{date_str}-%')
        ).order_by(InventoryCheck.check_no.desc()).first()
        
        if last_check:
            last_no = int(last_check.check_no.split('-')[-1])
            new_no = last_no + 1
        else:
            new_no = 1
        
        return f'CHK-{date_str}-{new_no:04d}'


class InventoryCheckItem(db.Model):
    """库存盘点明细"""
    
    __tablename__ = 'inventory_check_item'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='盘点明细 ID')
    check_id = db.Column(db.Integer, db.ForeignKey('inventory_check.id'), nullable=False, index=True, comment='盘点单 ID')
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory_v3.id'), comment='库存 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件 ID')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='货位 ID')
    
    # 数量信息
    system_quantity = db.Column(db.Numeric(12, 4), nullable=False, comment='系统数量')
    actual_quantity = db.Column(db.Numeric(12, 4), nullable=False, comment='实际数量')
    difference = db.Column(db.Numeric(12, 4), comment='差异')
    difference_reason = db.Column(db.String(200), comment='差异原因')
    
    # 状态
    status = db.Column(db.String(20), default='pending', comment='状态')
    
    # 盘点信息
    checked_at = db.Column(db.DateTime, comment='盘点时间')
    checked_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='盘点人')
    
    # 关系
    check = db.relationship('InventoryCheck', back_populates='items')
    inventory = db.relationship('InventoryV3')
    part = db.relationship('SparePart')
    location = db.relationship('WarehouseLocationV3')
    checker = db.relationship('User', foreign_keys=[checked_by])
    
    def __repr__(self):
        return f'<InventoryCheckItem {self.id}@{self.check_id}>'
    
    def calculate_difference(self):
        """计算差异"""
        self.difference = self.actual_quantity - self.system_quantity
        
        # 自动判断状态
        if abs(float(self.difference)) < 0.001:
            self.status = 'confirmed'  # 无差异
        else:
            self.status = 'difference'  # 有差异
    
    def to_dict(self):
        return {
            'id': self.id,
            'check_id': self.check_id,
            'inventory_id': self.inventory_id,
            'part_id': self.part_id,
            'part_name': self.part.name if self.part else None,
            'part_code': self.part.part_code if self.part else None,
            'location_id': self.location_id,
            'location_name': self.location.name if self.location else None,
            'system_quantity': float(self.system_quantity) if self.system_quantity else 0,
            'actual_quantity': float(self.actual_quantity) if self.actual_quantity else 0,
            'difference': float(self.difference) if self.difference else 0,
            'difference_reason': self.difference_reason,
            'status': self.status,
            'checked_at': self.checked_at.strftime('%Y-%m-%d %H:%M:%S') if self.checked_at else None,
            'checked_by': self.checked_by,
            'checker_name': self.checker.name if self.checker else None
        }
