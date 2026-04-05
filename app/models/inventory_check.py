
"""
库存盘点模型
支持循环盘点、全盘、差异处理
"""

from datetime import datetime
from app.extensions import db
from enum import Enum


class InventoryCheckStatus(Enum):
    """盘点状态枚举"""
    DRAFT = 'draft'  # 草稿
    IN_PROGRESS = 'in_progress'  # 进行中
    COMPLETED = 'completed'  # 已完成
    CANCELLED = 'cancelled'  # 已取消


class InventoryCheckType(Enum):
    """盘点类型枚举"""
    FULL = 'full'  # 全盘
    CYCLICAL = 'cyclical'  # 循环盘点
    ABC = 'abc'  # ABC分类盘点
    RANDOM = 'random'  # 随机抽盘


class InventoryCheck(db.Model):
    """库存盘点单表"""
    
    __tablename__ = 'inventory_check'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='盘点单 ID')
    check_code = db.Column(db.String(50), unique=True, nullable=False, comment='盘点单号')
    check_name = db.Column(db.String(100), nullable=False, comment='盘点名称')
    check_type = db.Column(db.String(20), nullable=False, default='full', comment='盘点类型')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, comment='仓库 ID')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), nullable=True, comment='库位 ID')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True, comment='分类 ID')
    
    # 盘点时间范围
    start_date = db.Column(db.DateTime, nullable=True, comment='开始日期')
    end_date = db.Column(db.DateTime, nullable=True, comment='结束日期')
    
    # ABC分类相关
    abc_class = db.Column(db.String(1), nullable=True, comment='ABC分类: A/B/C')
    
    # 状态
    status = db.Column(db.String(20), nullable=False, default='draft', comment='状态')
    
    # 统计信息
    total_items = db.Column(db.Integer, default=0, comment='总盘点项数')
    checked_items = db.Column(db.Integer, default=0, comment='已盘点项数')
    discrepancy_items = db.Column(db.Integer, default=0, comment='差异项数')
    discrepancy_value = db.Column(db.Numeric(15, 2), default=0, comment='差异金额')
    
    # 审核信息
    checked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, comment='盘点人 ID')
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, comment='审核人 ID')
    approved_at = db.Column(db.DateTime, nullable=True, comment='审核时间')
    
    remark = db.Column(db.Text, nullable=True, comment='备注')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='创建人 ID')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_id])
    location = db.relationship('WarehouseLocation', foreign_keys=[location_id])
    category = db.relationship('Category', foreign_keys=[category_id])
    creator = db.relationship('User', foreign_keys=[created_by])
    checker = db.relationship('User', foreign_keys=[checked_by])
    approver = db.relationship('User', foreign_keys=[approved_by])
    items = db.relationship('InventoryCheckItem', back_populates='inventory_check', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'&lt;InventoryCheck {self.check_code}&gt;'


class InventoryCheckItem(db.Model):
    """库存盘点明细表"""
    
    __tablename__ = 'inventory_check_item'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='明细 ID')
    inventory_check_id = db.Column(db.Integer, db.ForeignKey('inventory_check.id'), nullable=False, comment='盘点单 ID')
    
    # 库存信息
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), nullable=True, comment='批次 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, comment='仓库 ID')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), nullable=True, comment='库位 ID')
    
    # 账面数量
    system_quantity = db.Column(db.Integer, nullable=False, default=0, comment='系统数量')
    
    # 盘点数量
    check_quantity = db.Column(db.Integer, nullable=True, comment='盘点数量')
    second_check_quantity = db.Column(db.Integer, nullable=True, comment='复盘数量')
    
    # 差异
    difference_quantity = db.Column(db.Integer, nullable=True, comment='差异数量')
    difference_value = db.Column(db.Numeric(15, 2), nullable=True, comment='差异金额')
    
    # 状态
    status = db.Column(db.String(20), nullable=False, default='pending', comment='状态: pending/checked/difference/resolved')
    is_resolved = db.Column(db.Boolean, nullable=False, default=False, comment='是否已处理')
    
    # 盘点人信息
    checked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, comment='盘点人 ID')
    checked_at = db.Column(db.DateTime, nullable=True, comment='盘点时间')
    second_checked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, comment='复盘人 ID')
    second_checked_at = db.Column(db.DateTime, nullable=True, comment='复盘时间')
    
    remark = db.Column(db.Text, nullable=True, comment='备注')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    inventory_check = db.relationship('InventoryCheck', foreign_keys=[inventory_check_id])
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    batch = db.relationship('Batch', foreign_keys=[batch_id])
    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_id])
    location = db.relationship('WarehouseLocation', foreign_keys=[location_id])
    checker = db.relationship('User', foreign_keys=[checked_by])
    second_checker = db.relationship('User', foreign_keys=[second_checked_by])
    
    def __repr__(self):
        return f'&lt;InventoryCheckItem {self.id}&gt;'
    
    def calculate_difference(self):
        """计算差异"""
        if self.check_quantity is not None and self.system_quantity is not None:
            self.difference_quantity = self.check_quantity - self.system_quantity
            
            # 计算差异金额
            if self.spare_part and self.spare_part.unit_price:
                self.difference_value = self.difference_quantity * float(self.spare_part.unit_price)
            
            # 更新状态
            if self.difference_quantity == 0:
                self.status = 'checked'
            else:
                self.status = 'difference'
    
    def resolve_difference(self, user_id, remark=None):
        """处理差异"""
        self.is_resolved = True
        self.status = 'resolved'
        if remark:
            self.remark = remark


class StockAgeAnalysis(db.Model):
    """库龄分析表（用于存储分析结果）"""
    
    __tablename__ = 'stock_age_analysis'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='分析 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, comment='仓库 ID')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), nullable=True, comment='批次 ID')
    
    # 库龄信息
    stock_age_days = db.Column(db.Integer, nullable=False, comment='库龄天数')
    stock_age_level = db.Column(db.String(20), nullable=False, comment='库龄等级: normal/warning/danger/critical')
    
    # 库存信息
    quantity = db.Column(db.Integer, nullable=False, comment='库存数量')
    unit_price = db.Column(db.Numeric(15, 2), nullable=True, comment='单价')
    total_value = db.Column(db.Numeric(15, 2), nullable=True, comment='库存价值')
    
    # 呆滞库存标记
    is_slow_moving = db.Column(db.Boolean, nullable=False, default=False, comment='是否呆滞')
    is_obsolete = db.Column(db.Boolean, nullable=False, default=False, comment='是否过时')
    
    # 最后出库时间
    last_outbound_date = db.Column(db.DateTime, nullable=True, comment='最后出库时间')
    days_since_last_outbound = db.Column(db.Integer, nullable=True, comment='距最后出库天数')
    
    analysis_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='分析日期')
    
    # 关系
    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_id])
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    batch = db.relationship('Batch', foreign_keys=[batch_id])
    
    def __repr__(self):
        return f'&lt;StockAgeAnalysis {self.id}&gt;'

