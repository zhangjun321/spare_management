from app.extensions import db
from datetime import datetime


class SupplierEvaluation(db.Model):
    __tablename__ = 'supplier_evaluation'
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False, comment='供应商 ID')
    evaluation_date = db.Column(db.Date, nullable=False, comment='评估日期')
    quality_score = db.Column(db.Integer, comment='质量评分')
    delivery_score = db.Column(db.Integer, comment='交货评分')
    service_score = db.Column(db.Integer, comment='服务评分')
    price_score = db.Column(db.Integer, comment='价格评分')
    total_score = db.Column(db.Integer, comment='总分')
    evaluation_result = db.Column(db.String(20), comment='评估结果')
    evaluated_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='评估人 ID')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    supplier = db.relationship('Supplier', foreign_keys=[supplier_id])
    
    def __repr__(self):
        return f'<SupplierEvaluation {self.id}>'
