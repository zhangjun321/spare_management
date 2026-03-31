# -*- coding: utf-8 -*-
"""
数据库备份模型
"""

from app.extensions import db
from datetime import datetime


class DatabaseBackup(db.Model):
    """数据库备份表"""
    __tablename__ = 'database_backup'
    
    id = db.Column(db.Integer, primary_key=True)
    backup_name = db.Column(db.String(200), nullable=False, comment='备份名称')
    backup_file = db.Column(db.String(500), nullable=False, comment='备份文件路径')
    backup_size = db.Column(db.BigInteger, comment='备份文件大小 (字节)')
    backup_type = db.Column(db.String(20), default='manual', comment='备份类型：manual/scheduled')
    status = db.Column(db.String(20), default='pending', comment='状态：pending/running/success/failed')
    start_time = db.Column(db.DateTime, comment='开始时间')
    end_time = db.Column(db.DateTime, comment='结束时间')
    remark = db.Column(db.Text, comment='备注')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    def __repr__(self):
        return f'<DatabaseBackup {self.backup_name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'backup_name': self.backup_name,
            'backup_file': self.backup_file,
            'backup_size': self.backup_size,
            'backup_size_mb': round(self.backup_size / (1024 * 1024), 2) if self.backup_size else 0,
            'backup_type': self.backup_type,
            'status': self.status,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else None,
            'remark': self.remark,
            'created_by': self.created_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
