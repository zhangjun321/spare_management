"""
入库单模型 V3
"""

from datetime import datetime
from app.extensions import db


class InboundOrderV3(db.Model):
    """入库单表 V3"""
    
    __tablename__ = 'inbound_order_v3'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='入库单 ID')
    order_no = db.Column(db.String(50), unique=True, nullable=False, comment='入库单号')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), nullable=False, comment='仓库 ID')
    
    # 业务类型
    order_type = db.Column(db.String(50), nullable=False, comment='入库类型')
    source_type = db.Column(db.String(50), comment='来源类型')
    source_id = db.Column(db.Integer, comment='来源 ID')
    
    # 供应商信息
    supplier_id = db.Column(db.Integer, comment='供应商 ID')
    supplier_name = db.Column(db.String(100), comment='供应商名称')
    
    # 状态信息
    status = db.Column(db.String(20), default='pending', comment='入库状态')
    priority = db.Column(db.String(20), default='normal', comment='优先级')
    
    # 计划信息
    planned_date = db.Column(db.Date, comment='计划入库日期')
    expected_date = db.Column(db.Date, comment='预计入库日期')
    actual_date = db.Column(db.Date, comment='实际入库日期')
    
    # 汇总信息
    total_items = db.Column(db.Integer, default=0, comment='总项数')
    total_quantity = db.Column(db.Numeric(12, 4), default=0, comment='总数量')
    received_quantity = db.Column(db.Numeric(12, 4), default=0, comment='已收数量')
    
    # 验收信息
    inspection_status = db.Column(db.String(20), default='pending', comment='验收状态')
    inspection_date = db.Column(db.DateTime, comment='验收日期')
    inspector_id = db.Column(db.Integer, comment='验收人')
    inspection_result = db.Column(db.String(20), comment='验收结果')
    
    # AI 处理
    ai_location_recommendations = db.Column(db.JSON, comment='AI 货位推荐')
    ai_processing_status = db.Column(db.String(20), comment='AI 处理状态')
    
    # 质检控制（新增）
    quality_check_required = db.Column(db.Boolean, default=True, comment='是否要求质检')
    quality_check_status = db.Column(db.String(20), default='pending', comment='质检状态：pending/passed/failed')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人')
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='更新人')
    approved_at = db.Column(db.DateTime, comment='审核时间')
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='审核人')
    
    # 其他
    description = db.Column(db.Text)
    remarks = db.Column(db.Text)
    
    # 关系
    warehouse = db.relationship('WarehouseV3', back_populates='inbound_orders')
    items = db.relationship('InboundOrderItemV3', back_populates='order', lazy='dynamic')
    
    # 索引
    __table_args__ = (
        db.Index('idx_order_no', 'order_no'),
        db.Index('idx_warehouse', 'warehouse_id'),
        db.Index('idx_status', 'status'),
        db.Index('idx_order_type', 'order_type'),
    )
    
    def __repr__(self):
        return f'<InboundOrderV3 {self.order_no}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_no': self.order_no,
            'warehouse_id': self.warehouse_id,
            'order_type': self.order_type,
            'status': self.status,
            'quality_check_required': self.quality_check_required,
            'quality_check_status': self.quality_check_status,
            'total_items': self.total_items,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
    
    def can_complete(self):
        """检查是否可以完成入库"""
        if self.quality_check_required and self.quality_check_status != 'passed':
            return False, '质检未完成，不能入库'
        return True, '可以入库'
    
    def update_quality_check_status(self):
        """根据质检单状态更新入库单质检状态"""
        from .quality_check import QualityCheck
        
        # 查询关联的质检单
        checks = QualityCheck.query.filter_by(inbound_order_id=self.id).all()
        
        if not checks:
            # 没有质检单，不需要质检
            self.quality_check_status = 'not_required'
            return
        
        # 检查所有质检单是否都合格
        all_passed = all(check.status == 'completed' and check.result == 'passed' for check in checks)
        any_failed = any(check.result == 'failed' for check in checks)
        
        if any_failed:
            self.quality_check_status = 'failed'
        elif all_passed:
            self.quality_check_status = 'passed'
        else:
            self.quality_check_status = 'pending'


class InboundOrderItemV3(db.Model):
    """入库单明细表 V3"""
    
    __tablename__ = 'inbound_order_item_v3'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='入库单明细 ID')
    order_id = db.Column(db.Integer, db.ForeignKey('inbound_order_v3.id'), nullable=False, comment='入库单 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='推荐货位 ID')
    
    # 数量信息
    planned_quantity = db.Column(db.Numeric(12, 4), nullable=False, comment='计划数量')
    received_quantity = db.Column(db.Numeric(12, 4), default=0, comment='实收数量')
    rejected_quantity = db.Column(db.Numeric(12, 4), default=0, comment='拒收数量')
    unit = db.Column(db.String(20), nullable=False, comment='单位')
    
    # 批次信息
    batch_no = db.Column(db.String(50), comment='批次号')
    production_date = db.Column(db.Date, comment='生产日期')
    expiry_date = db.Column(db.Date, comment='有效期至')
    
    # 货位分配
    assigned_location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='分配货位 ID')
    actual_location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='实际货位 ID')
    
    # 验收信息
    inspection_status = db.Column(db.String(20), default='pending', comment='验收状态')
    inspection_result = db.Column(db.String(20), comment='验收结果')
    inspection_notes = db.Column(db.Text, comment='验收备注')
    
    # AI 分析
    ai_recommendation_score = db.Column(db.Numeric(5, 2), comment='AI 推荐评分')
    ai_notes = db.Column(db.Text, comment='AI 备注')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 其他
    remarks = db.Column(db.Text)
    
    # 关系
    order = db.relationship('InboundOrderV3', back_populates='items')
    part = db.relationship('SparePart')
    location = db.relationship('WarehouseLocationV3', foreign_keys=[location_id])
    assigned_location = db.relationship('WarehouseLocationV3', foreign_keys=[assigned_location_id])
    actual_location = db.relationship('WarehouseLocationV3', foreign_keys=[actual_location_id])
    
    # 索引
    __table_args__ = (
        db.Index('idx_order', 'order_id'),
        db.Index('idx_part', 'part_id'),
    )
    
    def __repr__(self):
        return f'<InboundOrderItemV3 {self.order_id}-{self.part_id}>'
