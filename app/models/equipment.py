from app.extensions import db
from datetime import datetime


class Equipment(db.Model):
    __tablename__ = 'equipment'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_code = db.Column(db.String(50), unique=True, nullable=False, comment='设备代码')
    name = db.Column(db.String(200), nullable=False, comment='设备名称')
    model = db.Column(db.String(100), comment='型号')
    category = db.Column(db.String(50), comment='类别')
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), comment='使用部门 ID')
    location = db.Column(db.String(200), comment='安装位置')
    status = db.Column(db.String(20), default='running', comment='状态')
    purchase_date = db.Column(db.Date, comment='购买日期')
    warranty_expiry = db.Column(db.Date, comment='保修到期日期')
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), comment='供应商 ID')
    purchase_price = db.Column(db.Numeric(10, 2), comment='购买价格')
    remark = db.Column(db.Text, comment='备注')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    
    department = db.relationship('Department', foreign_keys=[department_id], backref='department_equipments')
    supplier = db.relationship('Supplier', foreign_keys=[supplier_id], backref='supplier_equipments')
    maintenance_orders = db.relationship('MaintenanceOrder', foreign_keys='MaintenanceOrder.equipment_id', backref='maintenance_equipment', lazy='dynamic')
    serial_numbers = db.relationship('SerialNumber', foreign_keys='SerialNumber.equipment_id', backref='serial_equipment', lazy='dynamic')
    
    def __repr__(self):
        return f'<Equipment {self.equipment_code}>'
