"""
分类模型
"""

from datetime import datetime
from app.extensions import db


class Category(db.Model):
    """分类表"""
    
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='分类 ID')
    name = db.Column(db.String(100), nullable=False, comment='分类名称')
    code = db.Column(db.String(50), unique=True, nullable=True, comment='分类编码')
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True, comment='父分类 ID')
    level = db.Column(db.Integer, nullable=False, default=1, comment='分类层级')
    description = db.Column(db.Text, nullable=True, comment='分类描述')
    sort_order = db.Column(db.Integer, nullable=False, default=0, comment='排序顺序')
    is_active = db.Column(db.Boolean, nullable=False, default=True, comment='是否启用')
    status = db.Column(db.String(20), nullable=False, default='active', comment='状态')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    parent = db.relationship('Category', remote_side=[id], backref='children')
    spare_parts = db.relationship('SparePart', foreign_keys='SparePart.category_id', back_populates='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'
