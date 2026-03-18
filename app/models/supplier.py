"""
供应商模型
"""

from datetime import datetime
from app.extensions import db


class Supplier(db.Model):
    """供应商表"""
    
    __tablename__ = 'supplier'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='供应商 ID')
    name = db.Column(db.String(200), nullable=False, comment='供应商名称')
    code = db.Column(db.String(50), unique=True, nullable=False, comment='供应商编码')
    type = db.Column(db.String(50), nullable=True, comment='供应商类型')
    contact_person = db.Column(db.String(50), nullable=True, comment='联系人')
    phone = db.Column(db.String(20), nullable=True, comment='联系电话')
    mobile = db.Column(db.String(20), nullable=True, comment='手机')
    email = db.Column(db.String(100), nullable=True, comment='邮箱')
    fax = db.Column(db.String(20), nullable=True, comment='传真')
    website = db.Column(db.String(200), nullable=True, comment='网站')
    address = db.Column(db.String(500), nullable=True, comment='地址')
    city = db.Column(db.String(50), nullable=True, comment='城市')
    province = db.Column(db.String(50), nullable=True, comment='省份')
    country = db.Column(db.String(50), nullable=True, default='中国', comment='国家')
    postal_code = db.Column(db.String(20), nullable=True, comment='邮编')
    tax_number = db.Column(db.String(50), nullable=True, comment='税号')
    bank_name = db.Column(db.String(100), nullable=True, comment='开户行')
    bank_account = db.Column(db.String(100), nullable=True, comment='银行账号')
    rating = db.Column(db.Numeric(3, 2), nullable=False, default=0.00, comment='评级')
    status = db.Column(db.String(20), nullable=False, default='active', comment='状态')
    is_active = db.Column(db.Boolean, nullable=False, default=True, comment='是否启用')
    business_scope = db.Column(db.Text, nullable=True, comment='经营范围')
    notes = db.Column(db.Text, nullable=True, comment='备注')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    spare_parts = db.relationship('SparePart', foreign_keys='SparePart.supplier_id', lazy='dynamic')
    evaluations = db.relationship('SupplierEvaluation', foreign_keys='SupplierEvaluation.supplier_id', lazy='dynamic')
    batches = db.relationship('Batch', foreign_keys='Batch.supplier_id', lazy='dynamic')
    serial_numbers = db.relationship('SerialNumber', foreign_keys='SerialNumber.supplier_id', lazy='dynamic')
    
    def __repr__(self):
        return f'<Supplier {self.name}>'
