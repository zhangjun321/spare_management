from app.extensions import db
from datetime import datetime


class SerialNumber(db.Model):
    __tablename__ = 'serial_number'
    
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(100), unique=True, nullable=False, comment='序列号')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), comment='批次 ID')
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), comment='设备 ID')
    status = db.Column(db.String(20), default='in_stock', comment='状态')
    purchase_date = db.Column(db.Date, comment='购买日期')
    warranty_expiry = db.Column(db.Date, comment='保修到期日期')
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), comment='供应商 ID')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id], back_populates='serial_numbers')
    batch = db.relationship('Batch', foreign_keys=[batch_id], back_populates='serial_numbers')
    equipment = db.relationship('Equipment', foreign_keys=[equipment_id], back_populates='serial_numbers')
    supplier = db.relationship('Supplier', foreign_keys=[supplier_id], back_populates='serial_numbers')
    
    def __repr__(self):
        return f'<SerialNumber {self.serial_number}>'
