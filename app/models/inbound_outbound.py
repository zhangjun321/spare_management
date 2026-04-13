"""
入库单和出库单模型
实现完整的出入库业务流程
"""

from datetime import datetime
from app.extensions import db


class InboundOrder(db.Model):
    """
    入库单表
    
    支持多种入库类型：采购入库、退货入库、调拨入库、其他入库
    """
    
    __tablename__ = 'inbound_order'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='入库单 ID')
    order_no = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='入库单号')
    
    # 入库类型
    inbound_type = db.Column(db.String(20), nullable=False, index=True, comment='入库类型')
    # purchase-采购入库，return-退货入库，transfer-调拨入库，other-其他入库
    
    # 关联信息
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, index=True, comment='仓库 ID')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), nullable=True, index=True, comment='货位 ID')
    inventory_record_id = db.Column(db.Integer, db.ForeignKey('inventory_record.id'), index=True, comment='库存记录 ID')
    
    # 关联单据
    purchase_order_id = db.Column(db.Integer, comment='关联采购单 ID')
    transfer_order_id = db.Column(db.Integer, comment='关联调拨单 ID')
    
    # 入库数量
    quantity = db.Column(db.Integer, nullable=False, comment='入库数量')
    received_quantity = db.Column(db.Integer, default=0, comment='实收数量')
    
    # 批次信息
    batch_number = db.Column(db.String(50), comment='批次号')
    production_date = db.Column(db.Date, comment='生产日期')
    expiry_date = db.Column(db.Date, comment='有效期至')
    
    # 金额信息
    unit_price = db.Column(db.Numeric(12, 2), comment='单价')
    total_amount = db.Column(db.Numeric(12, 2), comment='总金额')
    currency = db.Column(db.String(10), default='CNY', comment='币种')
    
    # 供应商信息
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), index=True, comment='供应商 ID')
    
    # 入库状态
    status = db.Column(db.String(20), nullable=False, default='pending', index=True, comment='入库状态')
    # pending-待入库，partial-部分入库，completed-已完成，cancelled-已取消
    
    # 质检信息
    quality_check = db.Column(db.Boolean, default=False, comment='是否质检')
    quality_status = db.Column(db.String(20), comment='质检状态')
    # passed-合格，rejected-不合格，pending-待质检
    quality_remark = db.Column(db.Text, comment='质检备注')
    
    # 物流信息
    carrier = db.Column(db.String(100), comment='物流公司')
    tracking_number = db.Column(db.String(100), comment='物流单号')
    
    # 备注信息
    remark = db.Column(db.Text, comment='备注')
    extra_data = db.Column(db.JSON, comment='扩展数据')
    
    # 审计字段
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    confirmed_at = db.Column(db.DateTime, comment='确认时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    cancelled_at = db.Column(db.DateTime, comment='取消时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    confirmed_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='确认人 ID')
    completed_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='完成人 ID')
    
    # 关系
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id], backref='inbound_orders')
    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_id], backref='inbound_orders')
    warehouse_location = db.relationship('WarehouseLocation', foreign_keys=[location_id], backref='inbound_orders')
    inventory_record = db.relationship('InventoryRecord', foreign_keys=[inventory_record_id], back_populates='inbound_orders')
    supplier = db.relationship('Supplier', foreign_keys=[supplier_id], backref='inbound_orders')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_inbound_orders')
    confirmer = db.relationship('User', foreign_keys=[confirmed_by], backref='confirmed_inbound_orders')
    completer = db.relationship('User', foreign_keys=[completed_by], backref='completed_inbound_orders')
    
    def __repr__(self):
        return f'<InboundOrder {self.order_no}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'order_no': self.order_no,
            'inbound_type': self.inbound_type,
            'spare_part_id': self.spare_part_id,
            'warehouse_id': self.warehouse_id,
            'location_id': self.location_id,
            'quantity': self.quantity,
            'received_quantity': self.received_quantity,
            'batch_number': self.batch_number,
            'production_date': self.production_date.isoformat() if self.production_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'unit_price': float(self.unit_price) if self.unit_price else None,
            'total_amount': float(self.total_amount) if self.total_amount else None,
            'status': self.status,
            'quality_check': self.quality_check,
            'quality_status': self.quality_status,
            'carrier': self.carrier,
            'tracking_number': self.tracking_number,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class OutboundOrder(db.Model):
    """
    出库单表
    
    支持多种出库类型：领用出库、销售出库、退货出库、调拨出库、其他出库
    """
    
    __tablename__ = 'outbound_order'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='出库单 ID')
    order_no = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='出库单号')
    
    # 出库类型
    outbound_type = db.Column(db.String(20), nullable=False, index=True, comment='出库类型')
    # requisition-领用出库，sale-销售出库，return-退货出库，transfer-调拨出库，other-其他出库
    
    # 关联信息
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, index=True, comment='仓库 ID')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), nullable=True, index=True, comment='货位 ID')
    inventory_record_id = db.Column(db.Integer, db.ForeignKey('inventory_record.id'), index=True, comment='库存记录 ID')
    
    # 关联单据
    transfer_order_id = db.Column(db.Integer, comment='关联调拨单 ID')
    requisition_id = db.Column(db.Integer, comment='关联领用申请 ID')
    
    # 出库数量
    quantity = db.Column(db.Integer, nullable=False, comment='出库数量')
    shipped_quantity = db.Column(db.Integer, default=0, comment='实发数量')
    
    # 领用部门/人员
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), index=True, comment='领用部门 ID')
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True, comment='领用人 ID')
    
    # 金额信息
    unit_cost = db.Column(db.Numeric(12, 2), comment='单位成本')
    total_amount = db.Column(db.Numeric(12, 2), comment='总金额')
    
    # 出库状态
    status = db.Column(db.String(20), nullable=False, default='pending', index=True, comment='出库状态')
    # pending-待出库，partial-部分出库，completed-已完成，cancelled-已取消
    
    # 审批信息
    approval_required = db.Column(db.Boolean, default=False, comment='是否需要审批')
    approval_status = db.Column(db.String(20), comment='审批状态')
    # pending-待审批，approved-已批准，rejected-已拒绝
    approval_remark = db.Column(db.Text, comment='审批备注')
    
    # 物流信息
    carrier = db.Column(db.String(100), comment='物流公司')
    tracking_number = db.Column(db.String(100), comment='物流单号')
    recipient_name = db.Column(db.String(100), comment='收货人姓名')
    recipient_phone = db.Column(db.String(20), comment='收货人电话')
    recipient_address = db.Column(db.String(500), comment='收货地址')
    
    # 备注信息
    remark = db.Column(db.Text, comment='备注')
    extra_data = db.Column(db.JSON, comment='扩展数据')
    
    # 审计字段
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    approved_at = db.Column(db.DateTime, comment='审批时间')
    confirmed_at = db.Column(db.DateTime, comment='确认时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    cancelled_at = db.Column(db.DateTime, comment='取消时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='审批人 ID')
    confirmed_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='确认人 ID')
    completed_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='完成人 ID')
    
    # 关系
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id], backref='outbound_orders')
    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_id], backref='outbound_orders')
    warehouse_location = db.relationship('WarehouseLocation', foreign_keys=[location_id], backref='outbound_orders')
    inventory_record = db.relationship('InventoryRecord', foreign_keys=[inventory_record_id], back_populates='outbound_orders')
    department = db.relationship('Department', foreign_keys=[department_id], backref='outbound_orders')
    requester = db.relationship('User', foreign_keys=[requester_id], backref='requested_outbound_orders')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_outbound_orders')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_outbound_orders')
    confirmer = db.relationship('User', foreign_keys=[confirmed_by], backref='confirmed_outbound_orders')
    completer = db.relationship('User', foreign_keys=[completed_by], backref='completed_outbound_orders')
    
    def __repr__(self):
        return f'<OutboundOrder {self.order_no}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'order_no': self.order_no,
            'outbound_type': self.outbound_type,
            'spare_part_id': self.spare_part_id,
            'warehouse_id': self.warehouse_id,
            'location_id': self.location_id,
            'quantity': self.quantity,
            'shipped_quantity': self.shipped_quantity,
            'department_id': self.department_id,
            'requester_id': self.requester_id,
            'status': self.status,
            'approval_required': self.approval_required,
            'approval_status': self.approval_status,
            'carrier': self.carrier,
            'tracking_number': self.tracking_number,
            'recipient_name': self.recipient_name,
            'recipient_phone': self.recipient_phone,
            'recipient_address': self.recipient_address,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
