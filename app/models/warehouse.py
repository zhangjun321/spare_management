"""
仓库模型
"""

from datetime import datetime
from app.extensions import db


class Warehouse(db.Model):
    """仓库表"""
    
    __tablename__ = 'warehouse'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='仓库 ID')
    name = db.Column(db.String(100), nullable=False, comment='仓库名称')
    code = db.Column(db.String(50), unique=True, nullable=False, comment='仓库编码')
    type = db.Column(db.String(20), nullable=False, default='general', comment='仓库类型')
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, comment='仓库管理员 ID')
    address = db.Column(db.String(500), nullable=True, comment='仓库地址')
    area = db.Column(db.Numeric(10, 2), nullable=True, comment='仓库面积')
    capacity = db.Column(db.Integer, nullable=True, comment='仓库容量')
    phone = db.Column(db.String(20), nullable=True, comment='联系电话')
    description = db.Column(db.Text, nullable=True, comment='仓库描述')
    is_active = db.Column(db.Boolean, nullable=False, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    locations = db.relationship('WarehouseLocation', foreign_keys='WarehouseLocation.warehouse_id', lazy='dynamic')
    batches = db.relationship('Batch', foreign_keys='Batch.warehouse_id', lazy='dynamic')
    transactions = db.relationship('Transaction', foreign_keys='Transaction.warehouse_id', lazy='dynamic')
    
    def __repr__(self):
        return f'<Warehouse {self.name}>'
