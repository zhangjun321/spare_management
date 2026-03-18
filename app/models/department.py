"""
部门模型
"""

from datetime import datetime
from app.extensions import db


class Department(db.Model):
    """部门表"""
    
    __tablename__ = 'department'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='部门 ID')
    name = db.Column(db.String(100), nullable=False, comment='部门名称')
    code = db.Column(db.String(50), unique=True, nullable=True, comment='部门编码')
    parent_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True, comment='父部门 ID')
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, comment='部门负责人 ID')
    description = db.Column(db.String(500), nullable=True, comment='部门描述')
    sort_order = db.Column(db.Integer, nullable=False, default=0, comment='排序顺序')
    is_active = db.Column(db.Boolean, nullable=False, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    parent = db.relationship('Department', remote_side=[id], backref='children')
    users = db.relationship('User', foreign_keys='User.department_id', backref='user_department', lazy='dynamic')
    manager = db.relationship('User', foreign_keys=[manager_id], backref='managed_departments')
    equipments = db.relationship('Equipment', foreign_keys='Equipment.department_id', lazy='dynamic')
    
    def __repr__(self):
        return f'<Department {self.name}>'
