from datetime import datetime

from app.extensions import db


class Transaction(db.Model):
    """交易主表"""

    __tablename__ = 'transaction'

    id = db.Column(db.Integer, primary_key=True)
    tx_code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='交易编号')
    tx_type = db.Column(db.String(30), nullable=False, index=True, comment='交易类型：inbound/outbound/transfer/inventory_adjust')
    status = db.Column(db.String(20), default='draft', index=True, comment='draft/submitted/approved/rejected/closed')

    source_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), comment='来源仓库ID')
    target_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), comment='目标仓库ID')
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='操作人')

    total_qty = db.Column(db.Numeric(14, 2), default=0, comment='总数量')
    total_amount = db.Column(db.Numeric(14, 2), default=0, comment='总金额')

    remark = db.Column(db.Text, comment='备注')

    submitted_at = db.Column(db.DateTime, comment='提交时间')
    approved_at = db.Column(db.DateTime, comment='审批时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source_warehouse = db.relationship('Warehouse', foreign_keys=[source_warehouse_id], back_populates='transactions_from')
    target_warehouse = db.relationship('Warehouse', foreign_keys=[target_warehouse_id], back_populates='transactions_to')
    operator = db.relationship('User', foreign_keys=[operator_id])
    details = db.relationship('TransactionDetail', backref='transaction', lazy='dynamic', cascade='all, delete-orphan')
    ledgers = db.relationship('InventoryLedger', backref='transaction', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_tx_type_status_created', 'tx_type', 'status', 'created_at'),
        db.Index('idx_tx_source', 'source_warehouse_id', 'created_at'),
        db.Index('idx_tx_target', 'target_warehouse_id', 'created_at'),
    )

    def __repr__(self):
        return f'<Transaction {self.tx_code}>'


class TransactionDetail(db.Model):
    """交易明细"""

    __tablename__ = 'transaction_detail'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False, comment='交易 ID')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), comment='批次 ID')
    source_location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), comment='来源库位')
    target_location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), comment='目标库位')
    quantity = db.Column(db.Numeric(14, 2), nullable=False, comment='数量')
    unit_price = db.Column(db.Numeric(14, 2), comment='单价')
    amount = db.Column(db.Numeric(14, 2), comment='金额')
    status = db.Column(db.String(20), default='pending', comment='明细状态')
    remark = db.Column(db.Text, comment='备注')

    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    batch = db.relationship('Batch', foreign_keys=[batch_id])
    source_location = db.relationship('WarehouseLocation', foreign_keys=[source_location_id])
    target_location = db.relationship('WarehouseLocation', foreign_keys=[target_location_id])

    __table_args__ = (
        db.Index('idx_tx_detail_tx', 'transaction_id'),
        db.Index('idx_detail_part', 'spare_part_id'),
    )

    def __repr__(self):
        return f'<TransactionDetail {self.id}>'


class InventoryLedger(db.Model):
    """库存流水"""

    __tablename__ = 'inventory_ledger'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False, comment='交易 ID')
    transaction_detail_id = db.Column(db.Integer, db.ForeignKey('transaction_detail.id'), nullable=False, comment='交易明细 ID')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, comment='备件 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, comment='仓库 ID')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), comment='库位 ID')
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), comment='批次 ID')

    quantity_delta = db.Column(db.Numeric(14, 2), nullable=False, comment='数量变化，入库正，出库负')
    balance_after = db.Column(db.Numeric(14, 2), comment='变化后的余额（可选）')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_id])
    location = db.relationship('WarehouseLocation', foreign_keys=[location_id])
    batch = db.relationship('Batch', foreign_keys=[batch_id])
    detail = db.relationship('TransactionDetail', foreign_keys=[transaction_detail_id])

    __table_args__ = (
        db.Index('idx_ledger_part_wh', 'spare_part_id', 'warehouse_id', 'created_at'),
    )


class InventorySnapshot(db.Model):
    """库存盘点快照"""

    __tablename__ = 'inventory_snapshot'

    id = db.Column(db.Integer, primary_key=True)
    snapshot_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'))
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'))
    quantity = db.Column(db.Numeric(14, 2), nullable=False)
    snapshot_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_snap_wh_loc_part', 'warehouse_id', 'location_id', 'spare_part_id'),
    )

    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_id])
    location = db.relationship('WarehouseLocation', foreign_keys=[location_id])
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    batch = db.relationship('Batch', foreign_keys=[batch_id])
