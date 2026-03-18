"""
用户模型
"""

from datetime import datetime
from app.extensions import db, login_manager
from flask_login import UserMixin


class User(db.Model, UserMixin):
    """用户表"""
    
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='用户 ID')
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    email = db.Column(db.String(100), unique=True, nullable=False, comment='邮箱')
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希')
    real_name = db.Column(db.String(50), nullable=False, comment='真实姓名')
    phone = db.Column(db.String(20), nullable=True, comment='联系电话')
    avatar_url = db.Column(db.String(500), nullable=True, comment='头像 URL')
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True, comment='部门 ID')
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=True, comment='角色 ID')
    is_active = db.Column(db.Boolean, nullable=False, default=True, comment='是否激活')
    is_admin = db.Column(db.Boolean, nullable=False, default=False, comment='是否管理员')
    last_login = db.Column(db.DateTime, nullable=True, comment='最后登录时间')
    last_login_ip = db.Column(db.String(50), nullable=True, comment='最后登录 IP')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    department = db.relationship('Department', foreign_keys=[department_id])
    role = db.relationship('Role', foreign_keys=[role_id], backref='role_users')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def get_id(self):
        """返回用户 ID (Flask-Login 要求)"""
        return str(self.id)
    
    def has_permission(self, module, action):
        """检查权限"""
        if self.is_admin:
            return True
        if self.role:
            return self.role.has_permission(module, action)
        return False


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login 用户加载器"""
    return User.query.get(int(user_id))
