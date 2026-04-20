"""
用户模型
"""

from datetime import datetime
from app.extensions import db, login_manager
from flask_login import UserMixin
import bcrypt


class User(db.Model, UserMixin):
    """用户表"""
    
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='用户 ID')
    username = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='用户名')
    email = db.Column(db.String(100), unique=True, nullable=False, index=True, comment='邮箱')
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希')
    real_name = db.Column(db.String(50), nullable=False, index=True, comment='真实姓名')
    phone = db.Column(db.String(20), nullable=True, comment='联系电话')
    avatar_url = db.Column(db.String(500), nullable=True, comment='头像 URL')
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True, index=True, comment='部门 ID')
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=True, index=True, comment='角色 ID')
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True, comment='是否激活')
    is_admin = db.Column(db.Boolean, nullable=False, default=False, index=True, comment='是否管理员')
    last_login = db.Column(db.DateTime, nullable=True, index=True, comment='最后登录时间')
    last_login_ip = db.Column(db.String(50), nullable=True, comment='最后登录 IP')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, index=True, comment='更新时间')
    
    # 关系
    department = db.relationship('Department', foreign_keys=[department_id])
    role = db.relationship('Role', foreign_keys=[role_id], backref='role_users')
    managed_warehouses = db.relationship('Warehouse', foreign_keys='Warehouse.manager_id', back_populates='manager')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def get_id(self):
        """返回用户 ID (Flask-Login 要求)"""
        return str(self.id)
    
    def set_password(self, password: str) -> None:
        """设置密码（bcrypt 哈希）"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """验证密码是否正确"""
        try:
            password_bytes = password.encode('utf-8')
            hash_bytes = self.password_hash.encode('utf-8')
            
            # 判断密码哈希格式
            if hash_bytes.startswith(b'$2b$') or hash_bytes.startswith(b'$2a$') or hash_bytes.startswith(b'$2y$'):
                # bcrypt 格式
                return bcrypt.checkpw(password_bytes, hash_bytes)
            else:
                # werkzeug (pbkdf2) 格式
                from werkzeug.security import check_password_hash
                return check_password_hash(self.password_hash, password)
        except Exception:
            return False
    
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
