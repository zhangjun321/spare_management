"""
出库单模型 V3
"""

from datetime import datetime
from app.extensions import db


class OutboundOrderV3(db.Model):
    """出库单表 V3"""
    
    __tablename__ = 'outbound_order_v3'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='出库单 ID')
    order_no = db.Column(db.String(50), unique=True, nullable=False, comment='出库单号')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), nullable=False, comment='仓库 ID')
    
    # 业务类型
    order_type = db.Column(db.String(50), nullable=False, comment='出库类型')
    destination_type = db.Column(db.String(50), comment='去向类型')
    destination_id = db.Column(db.Integer, comment='去向 ID')
    
    # 客户信息
    customer_id = db.Column(db.Integer, comment='客户 ID')
    customer_name = db.Column(db.String(100), comment='客户名称')
    
    # 状态信息
    status = db.Column(db.String(20), default='pending', comment='出库状态')
    priority = db.Column(db.String(20), default='normal', comment='优先级')
    
    # 计划信息
    planned_date = db.Column(db.Date, comment='计划出库日期')
    expected_date = db.Column(db.Date, comment='预计出库日期')
    actual_date = db.Column(db.Date, comment='实际出库日期')
    
    # 拣货信息
    picking_status = db.Column(db.String(20), default='pending', comment='拣货状态')
    picking_date = db.Column(db.DateTime, comment='拣货日期')
    picker_id = db.Column(db.Integer, comment='拣货员')
    
    # 汇总信息
    total_items = db.Column(db.Integer, default=0, comment='总项数')
    total_quantity = db.Column(db.Numeric(12, 4), default=0, comment='总数量')
    picked_quantity = db.Column(db.Numeric(12, 4), default=0, comment='已拣数量')
    
    # 复核信息
    review_status = db.Column(db.String(20), default='pending', comment='复核状态')
    review_date = db.Column(db.DateTime, comment='复核日期')
    reviewer_id = db.Column(db.Integer, comment='复核人')
    
    # AI 处理
    ai_picking_path = db.Column(db.JSON, comment='AI 拣货路径')
    ai_batch_recommendations = db.Column(db.JSON, comment='AI 批次推荐')
    ai_processing_status = db.Column(db.String(20), comment='AI 处理状态')
    
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
    warehouse = db.relationship('WarehouseV3', back_populates='outbound_orders')
    items = db.relationship('OutboundOrderItemV3', back_populates='order', lazy='dynamic')
    
    # 索引
    __table_args__ = (
        db.Index('idx_order_no', 'order_no'),
        db.Index('idx_warehouse', 'warehouse_id'),
        db.Index('idx_status', 'status'),
        db.Index('idx_order_type', 'order_type'),
    )
    
    def __repr__(self):
        return f'<OutboundOrderV3 {self.order_no}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_no': self.order_no,
            'warehouse_id': self.warehouse_id,
            'order_type': self.order_type,
            'status': self.status,
            'total_items': self.total_items,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class OutboundOrderItemV3(db.Model):
    """出库单明细表 V3"""
    
    __tablename__ = 'outbound_order_item_v3'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='出库单明细 ID')
    order_id = db.Column(db.Integer, db.ForeignKey('outbound_order_v3.id'), nullable=False, comment='出库单 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    
    # 数量信息
    requested_quantity = db.Column(db.Numeric(12, 4), nullable=False, comment='申请数量')
    picked_quantity = db.Column(db.Numeric(12, 4), default=0, comment='已拣数量')
    shipped_quantity = db.Column(db.Numeric(12, 4), default=0, comment='已发数量')
    unit = db.Column(db.String(20), nullable=False, comment='单位')
    
    # 批次推荐
    recommended_batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), comment='推荐批次 ID')
    actual_batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), comment='实际批次 ID')
    
    # 货位信息
    source_location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='源货位 ID')
    
    # 拣货信息
    picking_status = db.Column(db.String(20), default='pending', comment='拣货状态')
    picking_location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='拣货货位 ID')
    actual_picking_location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='实际拣货货位 ID')
    
    # AI 分析
    ai_recommendation_score = db.Column(db.Numeric(5, 2), comment='AI 推荐评分')
    ai_picking_sequence = db.Column(db.Integer, comment='AI 拣货顺序')
    ai_notes = db.Column(db.Text, comment='AI 备注')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 其他
    remarks = db.Column(db.Text)
    
    # 关系
    order = db.relationship('OutboundOrderV3', back_populates='items')
    part = db.relationship('SparePart')
    recommended_batch = db.relationship('Batch', foreign_keys=[recommended_batch_id])
    actual_batch = db.relationship('Batch', foreign_keys=[actual_batch_id])
    source_location = db.relationship('WarehouseLocationV3', foreign_keys=[source_location_id])
    
    # 索引
    __table_args__ = (
        db.Index('idx_order', 'order_id'),
        db.Index('idx_part', 'part_id'),
    )
    
    def __repr__(self):
        return f'<OutboundOrderItemV3 {self.order_id}-{self.part_id}>'
