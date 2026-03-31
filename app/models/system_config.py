# -*- coding: utf-8 -*-
"""
系统配置模型
"""

from app.extensions import db
from datetime import datetime


class SystemConfig(db.Model):
    """系统配置表"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    config_group = db.Column(db.String(50), nullable=False, index=True, comment='配置分组')
    config_key = db.Column(db.String(100), nullable=False, unique=True, comment='配置键')
    config_value = db.Column(db.Text, nullable=False, comment='配置值')
    value_type = db.Column(db.String(20), default='string', comment='值类型：string/int/float/bool/json')
    description = db.Column(db.String(200), comment='描述')
    is_editable = db.Column(db.Boolean, default=True, comment='是否可编辑')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    version = db.Column(db.Integer, default=1, comment='版本号')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='更新人')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    def __repr__(self):
        return f'<SystemConfig {self.config_key}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'config_group': self.config_group,
            'config_key': self.config_key,
            'config_value': self.config_value,
            'value_type': self.value_type,
            'description': self.description,
            'is_editable': self.is_editable,
            'is_active': self.is_active,
            'version': self.version,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'updated_by': self.updated_by
        }
