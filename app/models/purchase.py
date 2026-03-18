from app.extensions import db
from datetime import datetime


class PurchasePlan(db.Model):
    __tablename__ = 'purchase_plan'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_number = db.Column(db.String(50), unique=True, nullable=False, comment='计划编号')
    title = db.Column(db.String(200), nullable=False, comment='计划标题')
    description = db.Column(db.Text, comment='计划描述')
    status = db.Column(db.String(20), default='draft', comment='状态')
    total_amount = db.Column(db.Numeric(10, 2), comment='总金额')
    planned_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='计划人 ID')
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='批准人 ID')
    planned_date = db.Column(db.Date, comment='计划日期')
    approved_date = db.Column(db.DateTime, comment='批准日期')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    requests = db.relationship('PurchaseRequest', foreign_keys='PurchaseRequest.plan_id', backref='request_plan', lazy='dynamic')
    
    def __repr__(self):
        return f'<PurchasePlan {self.plan_number}>'


class PurchaseRequest(db.Model):
    __tablename__ = 'purchase_request'
    
    id = db.Column(db.Integer, primary_key=True)
    request_number = db.Column(db.String(50), unique=True, nullable=False, comment='申请编号')
    plan_id = db.Column(db.Integer, db.ForeignKey('purchase_plan.id'), comment='计划 ID')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    quantity = db.Column(db.Integer, nullable=False, comment='申请数量')
    unit = db.Column(db.String(20), comment='单位')
    estimated_price = db.Column(db.Numeric(10, 2), comment='预估单价')
    estimated_total = db.Column(db.Numeric(10, 2), comment='预估总价')
    reason = db.Column(db.Text, comment='申请原因')
    status = db.Column(db.String(20), default='pending', comment='状态')
    requested_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='申请人 ID')
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='批准人 ID')
    requested_date = db.Column(db.DateTime, default=datetime.now, comment='申请日期')
    approved_date = db.Column(db.DateTime, comment='批准日期')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id], backref='part_purchase_requests')
    quotes = db.relationship('PurchaseQuote', foreign_keys='PurchaseQuote.request_id', backref='quote_request', lazy='dynamic')
    order_items = db.relationship('PurchaseOrderItem', foreign_keys='PurchaseOrderItem.request_id', backref='item_request', lazy='dynamic')
    
    def __repr__(self):
        return f'<PurchaseRequest {self.request_number}>'


class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_order'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, comment='订单编号')
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False, comment='供应商 ID')
    title = db.Column(db.String(200), nullable=False, comment='订单标题')
    status = db.Column(db.String(20), default='pending', comment='状态')
    total_amount = db.Column(db.Numeric(10, 2), comment='总金额')
    order_date = db.Column(db.DateTime, default=datetime.now, comment='订单日期')
    expected_delivery_date = db.Column(db.Date, comment='预计交货日期')
    actual_delivery_date = db.Column(db.Date, comment='实际交货日期')
    received_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='收货人 ID')
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='批准人 ID')
    approved_date = db.Column(db.DateTime, comment='批准日期')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    
    supplier = db.relationship('Supplier', foreign_keys=[supplier_id], backref='supplier_orders')
    receiver = db.relationship('User', foreign_keys=[received_by], backref='user_received_orders')
    items = db.relationship('PurchaseOrderItem', foreign_keys='PurchaseOrderItem.order_id', backref='item_order', lazy='dynamic')
    
    def __repr__(self):
        return f'<PurchaseOrder {self.order_number}>'


class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_item'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=False, comment='订单 ID')
    request_id = db.Column(db.Integer, db.ForeignKey('purchase_request.id'), comment='申请 ID')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    quantity = db.Column(db.Integer, nullable=False, comment='数量')
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, comment='单价')
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, comment='总金额')
    received_quantity = db.Column(db.Integer, default=0, comment='已收货数量')
    remark = db.Column(db.Text, comment='备注')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id], backref='part_order_items')
    
    def __repr__(self):
        return f'<PurchaseOrderItem {self.id}>'


class PurchaseQuote(db.Model):
    __tablename__ = 'purchase_quote'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('purchase_request.id'), nullable=False, comment='申请 ID')
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False, comment='供应商 ID')
    quotation_number = db.Column(db.String(50), comment='报价单号')
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, comment='单价')
    total_amount = db.Column(db.Numeric(10, 2), comment='总价')
    delivery_days = db.Column(db.Integer, comment='交货天数')
    valid_until = db.Column(db.Date, comment='有效期至')
    is_selected = db.Column(db.Boolean, default=False, comment='是否选中')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    
    supplier = db.relationship('Supplier', foreign_keys=[supplier_id], backref='supplier_quotes')
    
    def __repr__(self):
        return f'<PurchaseQuote {self.id}>'
