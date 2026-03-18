from app.extensions import db
from datetime import datetime


class Transaction(db.Model):
    __tablename__ = 'transaction'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_number = db.Column(db.String(50), unique=True, nullable=False, comment='交易编号')
    transaction_type = db.Column(db.String(20), nullable=False, comment='交易类型')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), comment='批次 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, comment='仓库 ID')
    quantity = db.Column(db.Integer, nullable=False, comment='数量')
    unit_price = db.Column(db.Numeric(10, 2), comment='单价')
    total_amount = db.Column(db.Numeric(10, 2), comment='总金额')
    related_order_id = db.Column(db.Integer, comment='关联单据 ID')
    related_order_type = db.Column(db.String(20), comment='关联单据类型')
    transaction_date = db.Column(db.DateTime, default=datetime.now, comment='交易日期')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='创建人 ID')
    confirmed_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='确认人 ID')
    confirmed_at = db.Column(db.DateTime, comment='确认时间')
    status = db.Column(db.String(20), default='pending', comment='状态')
    
    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_id])
    batch = db.relationship('Batch', foreign_keys=[batch_id])
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    details = db.relationship('TransactionDetail', backref='transaction', lazy='dynamic')
    
    def __repr__(self):
        return f'<Transaction {self.transaction_number}>'


class TransactionDetail(db.Model):
    __tablename__ = 'transaction_detail'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False, comment='交易 ID')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), comment='批次 ID')
    quantity = db.Column(db.Integer, nullable=False, comment='数量')
    unit_price = db.Column(db.Numeric(10, 2), comment='单价')
    total_amount = db.Column(db.Numeric(10, 2), comment='总金额')
    remark = db.Column(db.Text, comment='备注')
    
    def __repr__(self):
        return f'<TransactionDetail {self.id}>'
