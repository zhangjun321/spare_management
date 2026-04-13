from datetime import datetime
from app import db


class AIAnalysisReport(db.Model):
    """AI 分析报告模型"""
    __tablename__ = 'ai_analysis_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(50), nullable=False, comment='报告类型：forecast/optimization/risk')
    report_title = db.Column(db.String(200), nullable=False, comment='报告标题')
    report_content = db.Column(db.Text, nullable=False, comment='报告内容')
    
    # 统计信息
    total_parts = db.Column(db.Integer, default=0, comment='备件总数')
    total_value = db.Column(db.Numeric(10, 2), default=0, comment='总价值')
    duration = db.Column(db.Numeric(10, 2), default=0, comment='分析耗时（秒）')
    
    # 用户信息
    user_id = db.Column(db.Integer, nullable=True, comment='用户 ID')
    user_name = db.Column(db.String(100), comment='用户名')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    # 索引
    __table_args__ = (
        db.Index('idx_report_type', 'report_type'),
        db.Index('idx_created_at', 'created_at'),
        db.Index('idx_user_id', 'user_id'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'report_type': self.report_type,
            'report_title': self.report_title,
            'report_content': self.report_content,
            'total_parts': self.total_parts,
            'total_value': float(self.total_value) if self.total_value else 0,
            'duration': float(self.duration) if self.duration else 0,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
