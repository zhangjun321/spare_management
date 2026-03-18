from app.extensions import db
from datetime import datetime


class Batch(db.Model):
    __tablename__ = 'batch'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_number = db.Column(db.String(50), unique=True, nullable=False, comment='批次号')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, comment='仓库 ID')
    quantity = db.Column(db.Integer, nullable=False, default=0, comment='批次数量')
    production_date = db.Column(db.Date, comment='生产日期')
    expiry_date = db.Column(db.Date, comment='过期日期')
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), comment='供应商 ID')
    purchase_price = db.Column(db.Numeric(10, 2), comment='采购价格')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), comment='库位 ID')
    status = db.Column(db.String(20), default='active', comment='状态')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    
    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_id], backref='warehouse_batches')
    supplier = db.relationship('Supplier', foreign_keys=[supplier_id], backref='supplier_batches')
    location = db.relationship('WarehouseLocation', foreign_keys=[location_id], backref='location_batches')
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id], backref='batch_spare_part')
    serial_numbers = db.relationship('SerialNumber', foreign_keys='SerialNumber.batch_id', backref='serial_batch', lazy='dynamic')
    transactions = db.relationship('Transaction', foreign_keys='Transaction.batch_id', backref='transaction_batch', lazy='dynamic')
    
    def __repr__(self):
        return f'<Batch {self.batch_number}>'
