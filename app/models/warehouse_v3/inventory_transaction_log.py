"""
库存事务日志模型 - 用于审计和追溯
"""

from datetime import datetime
from app.extensions import db


class InventoryTransactionLog(db.Model):
    """库存交易日志表"""
    
    __tablename__ = 'inventory_transaction_log'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='交易日志 ID')
    transaction_no = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='交易编号')
    
    # 库存信息
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory_v3.id'), nullable=False, comment='库存 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), nullable=False, comment='仓库 ID')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='货位 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), comment='批次 ID')
    
    # 变动信息
    change_type = db.Column(db.String(20), nullable=False, comment='变动类型：IN/OUT/ADJUST/TRANSFER/LOCK/UNLOCK')
    old_quantity = db.Column(db.Numeric(12, 4), nullable=False, comment='变动前数量')
    new_quantity = db.Column(db.Numeric(12, 4), nullable=False, comment='变动后数量')
    change_quantity = db.Column(db.Numeric(12, 4), nullable=False, comment='变动数量')
    
    # 关联单据
    source_type = db.Column(db.String(20), comment='单据类型：INBOUND/OUTBOUND/INVENTORY_CHECK/TRANSFER/ADJUSTMENT')
    source_id = db.Column(db.Integer, comment='单据 ID')
    source_no = db.Column(db.String(50), comment='单据编号')
    
    # 操作信息
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='操作人 ID')
    operation_time = db.Column(db.DateTime, default=datetime.utcnow, comment='操作时间')
    remark = db.Column(db.Text, comment='备注')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    inventory = db.relationship('InventoryV3', backref='transaction_logs')
    warehouse = db.relationship('WarehouseV3')
    location = db.relationship('WarehouseLocationV3')
    part = db.relationship('SparePart')
    batch = db.relationship('Batch')
    operator = db.relationship('User')
    
    # 索引
    __table_args__ = (
        db.Index('idx_transaction_no', 'transaction_no'),
        db.Index('idx_inventory', 'inventory_id'),
        db.Index('idx_part', 'part_id'),
        db.Index('idx_warehouse', 'warehouse_id'),
        db.Index('idx_source', 'source_type', 'source_id'),
        db.Index('idx_operation_time', 'operation_time'),
    )
    
    def __repr__(self):
        return f'<InventoryTransactionLog {self.transaction_no}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_no': self.transaction_no,
            'inventory_id': self.inventory_id,
            'warehouse_id': self.warehouse_id,
            'location_id': self.location_id,
            'part_id': self.part_id,
            'batch_id': self.batch_id,
            'change_type': self.change_type,
            'old_quantity': float(self.old_quantity) if self.old_quantity else 0,
            'new_quantity': float(self.new_quantity) if self.new_quantity else 0,
            'change_quantity': float(self.change_quantity) if self.change_quantity else 0,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'source_no': self.source_no,
            'operator_id': self.operator_id,
            'operation_time': self.operation_time.strftime('%Y-%m-%d %H:%M:%S') if self.operation_time else None,
            'remark': self.remark,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
    
    @staticmethod
    def generate_transaction_no():
        """生成交易编号"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        import random
        random_suffix = str(random.randint(1000, 9999))
        return f'TRANS{timestamp}{random_suffix}'


class InventoryTransactionSummary(db.Model):
    """库存变动汇总表（按天）"""
    
    __tablename__ = 'inventory_transaction_summary'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), nullable=False, comment='仓库 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    transaction_date = db.Column(db.Date, nullable=False, comment='交易日期')
    
    # 入库汇总
    total_in_quantity = db.Column(db.Numeric(12, 4), default=0, comment='入库总量')
    inbound_count = db.Column(db.Integer, default=0, comment='入库次数')
    
    # 出库汇总
    total_out_quantity = db.Column(db.Numeric(12, 4), default=0, comment='出库总量')
    outbound_count = db.Column(db.Integer, default=0, comment='出库次数')
    
    # 调整汇总
    total_adjust_in = db.Column(db.Numeric(12, 4), default=0, comment='调增总量')
    total_adjust_out = db.Column(db.Numeric(12, 4), default=0, comment='调减总量')
    adjust_count = db.Column(db.Integer, default=0, comment='调整次数')
    
    # 期初期末
    opening_quantity = db.Column(db.Numeric(12, 4), comment='期初数量')
    closing_quantity = db.Column(db.Numeric(12, 4), comment='期末数量')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_summary_warehouse_part_date', 'warehouse_id', 'part_id', 'transaction_date', unique=True),
    )
    
    def __repr__(self):
        return f'<InventoryTransactionSummary {self.warehouse_id}-{self.part_id}-{self.transaction_date}>'
