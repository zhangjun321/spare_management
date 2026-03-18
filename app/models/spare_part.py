from app.extensions import db
from datetime import datetime


class SparePart(db.Model):
    __tablename__ = 'spare_part'
    
    id = db.Column(db.Integer, primary_key=True)
    part_code = db.Column(db.String(50), unique=True, nullable=False, comment='备件代码')
    name = db.Column(db.String(200), nullable=False, comment='备件名称')
    specification = db.Column(db.String(200), comment='规格型号')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), comment='分类 ID')
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), comment='供应商 ID')
    current_stock = db.Column(db.Integer, nullable=False, default=0, comment='当前库存')
    stock_status = db.Column(db.String(20), nullable=False, default='normal', comment='库存状态')
    min_stock = db.Column(db.Integer, default=0, comment='最低库存')
    max_stock = db.Column(db.Integer, comment='最高库存')
    unit = db.Column(db.String(20), comment='单位')
    unit_price = db.Column(db.Numeric(10, 2), comment='单价')
    location = db.Column(db.String(200), comment='存放位置')
    image_url = db.Column(db.String(500), comment='图片 URL')
    remark = db.Column(db.Text, comment='备注')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    
    category = db.relationship('Category', foreign_keys=[category_id], backref='category_spare_parts')
    supplier = db.relationship('Supplier', foreign_keys=[supplier_id], backref='supplier_spare_parts')
    batches = db.relationship('Batch', foreign_keys='Batch.spare_part_id', backref='batch_spare_part', lazy='dynamic')
    transactions = db.relationship('Transaction', foreign_keys='Transaction.spare_part_id', lazy='dynamic')
    serial_numbers = db.relationship('SerialNumber', foreign_keys='SerialNumber.spare_part_id', lazy='dynamic')
    
    def update_stock_status(self):
        if self.current_stock <= self.min_stock:
            self.stock_status = 'low'
        elif self.max_stock and self.current_stock >= self.max_stock:
            self.stock_status = 'overstocked'
        else:
            self.stock_status = 'normal'
    
    def __repr__(self):
        return f'<SparePart {self.part_code}>'
