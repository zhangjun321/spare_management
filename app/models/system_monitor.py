# -*- coding: utf-8 -*-
"""
系统监控模型
"""

from app.extensions import db
from datetime import datetime


class SystemMonitor(db.Model):
    """系统监控数据表"""
    __tablename__ = 'system_monitor'
    
    id = db.Column(db.Integer, primary_key=True)
    monitor_type = db.Column(db.String(50), nullable=False, comment='监控类型：server/database/redis/service')
    metric_name = db.Column(db.String(100), nullable=False, comment='指标名称')
    metric_value = db.Column(db.Float, nullable=False, comment='指标值')
    threshold_warning = db.Column(db.Float, comment='警告阈值')
    threshold_critical = db.Column(db.Float, comment='严重阈值')
    status = db.Column(db.String(20), default='normal', comment='状态：normal/warning/critical')
    unit = db.Column(db.String(20), comment='单位')
    recorded_at = db.Column(db.DateTime, default=datetime.now, comment='记录时间')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    def __repr__(self):
        return f'<SystemMonitor {self.metric_name} - {self.status}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'monitor_type': self.monitor_type,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'threshold_warning': self.threshold_warning,
            'threshold_critical': self.threshold_critical,
            'status': self.status,
            'unit': self.unit,
            'recorded_at': self.recorded_at.strftime('%Y-%m-%d %H:%M:%S') if self.recorded_at else None
        }
