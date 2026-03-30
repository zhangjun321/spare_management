"""
角色模型
"""

from datetime import datetime
import json
from app.extensions import db


class Role(db.Model):
    """角色表"""
    
    __tablename__ = 'role'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='角色 ID')
    name = db.Column(db.String(50), unique=True, nullable=False, comment='角色名称')
    display_name = db.Column(db.String(100), nullable=False, comment='角色显示名称')
    description = db.Column(db.String(500), nullable=True, comment='角色描述')
    permissions = db.Column(db.Text, nullable=True, comment='权限配置 (JSON)')
    is_system = db.Column(db.Boolean, nullable=False, default=False, comment='是否系统内置角色')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    users = db.relationship('User', foreign_keys='User.role_id', lazy='dynamic')
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def get_permissions(self):
        """获取权限字典"""
        import json
        if self.permissions:
            try:
                return json.loads(self.permissions)
            except Exception:
                return {}
        return {}
    
    def has_permission(self, module, action):
        """检查是否有权限"""
        permissions = self.get_permissions()
        
        # 管理员拥有所有权限
        if self.name == 'admin':
            return True
        
        # 检查模块权限
        if module in permissions:
            module_perms = permissions[module]
            if action in module_perms or '*' in module_perms:
                return True
        
        # 检查全局权限
        if '*' in permissions:
            global_perms = permissions['*']
            if action in global_perms or '*' in global_perms:
                return True
        
        return False
    
    def add_permission(self, module, action):
        """添加权限"""
        permissions = self.get_permissions()
        if module not in permissions:
            permissions[module] = []
        if action not in permissions[module]:
            permissions[module].append(action)
        self.permissions = json.dumps(permissions)
    
    def remove_permission(self, module, action):
        """移除权限"""
        permissions = self.get_permissions()
        if module in permissions and action in permissions[module]:
            permissions[module].remove(action)
            if not permissions[module]:
                del permissions[module]
            self.permissions = json.dumps(permissions)
