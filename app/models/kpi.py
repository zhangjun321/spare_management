"""
KPI管理模块 - 数据库模型
"""

from app.extensions import db
from datetime import datetime


class KPIConfig(db.Model):
    """KPI配置表"""
    __tablename__ = 'kpi_config'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='KPI名称')
    code = db.Column(db.String(50), nullable=False, unique=True, comment='KPI编码')
    description = db.Column(db.Text, comment='KPI描述')
    target_value = db.Column(db.Float, comment='目标值')
    warning_threshold = db.Column(db.Float, comment='预警阈值')
    critical_threshold = db.Column(db.Float, comment='严重阈值')
    unit = db.Column(db.String(20), comment='单位')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    check_frequency = db.Column(db.String(20), default='daily', comment='检查频率: daily/weekly/monthly')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    history = db.relationship('KPIHistory', backref='config', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'target_value': self.target_value,
            'warning_threshold': self.warning_threshold,
            'critical_threshold': self.critical_threshold,
            'unit': self.unit,
            'is_active': self.is_active,
            'check_frequency': self.check_frequency,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class KPIHistory(db.Model):
    """KPI历史记录表"""
    __tablename__ = 'kpi_history'

    id = db.Column(db.Integer, primary_key=True)
    kpi_id = db.Column(db.Integer, db.ForeignKey('kpi_config.id'), nullable=False, comment='KPI配置ID')
    period = db.Column(db.String(20), nullable=False, comment='周期: daily/weekly/monthly')
    period_start = db.Column(db.DateTime, comment='周期开始时间')
    period_end = db.Column(db.DateTime, comment='周期结束时间')
    actual_value = db.Column(db.Float, nullable=False, comment='实际值')
    target_value = db.Column(db.Float, comment='目标值')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    def to_dict(self):
        return {
            'id': self.id,
            'kpi_id': self.kpi_id,
            'period': self.period,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'actual_value': self.actual_value,
            'target_value': self.target_value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AIAnalysisHistory(db.Model):
    """AI分析历史表"""
    __tablename__ = 'ai_analysis_history'

    id = db.Column(db.Integer, primary_key=True)
    analysis_type = db.Column(db.String(50), nullable=False, comment='分析类型: health/anomaly/prediction')
    analysis_result = db.Column(db.Text, nullable=False, comment='分析结果JSON')
    confidence_score = db.Column(db.Float, comment='置信度')
    action_taken = db.Column(db.Boolean, default=False, comment='是否已采取行动')
    action_notes = db.Column(db.Text, comment='行动备注')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    def to_dict(self):
        return {
            'id': self.id,
            'analysis_type': self.analysis_type,
            'analysis_result': self.analysis_result,
            'confidence_score': self.confidence_score,
            'action_taken': self.action_taken,
            'action_notes': self.action_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
