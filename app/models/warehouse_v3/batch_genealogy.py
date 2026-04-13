from app import db
from datetime import datetime


class BatchGenealogy(db.Model):
    """批次谱系表 - 记录批次之间的父子关系"""
    __tablename__ = 'batch_genealogy'
    
    id = db.Column(db.Integer, primary_key=True)
    child_batch_id = db.Column(db.Integer, db.ForeignKey('inventory_v3.id'), nullable=False, index=True, comment='子批次 ID')
    parent_batch_id = db.Column(db.Integer, db.ForeignKey('inventory_v3.id'), nullable=False, index=True, comment='父批次 ID')
    relationship_type = db.Column(db.String(20), nullable=False, comment='关系类型：SPLIT(拆分)/MERGE(合并)/TRANSFER(转移)')
    quantity = db.Column(db.Numeric(12, 4), nullable=False, comment='数量')
    operation_type = db.Column(db.String(50), comment='操作类型')
    operation_id = db.Column(db.Integer, comment='操作单据 ID')
    operation_time = db.Column(db.DateTime, default=datetime.utcnow, comment='操作时间')
    remark = db.Column(db.Text, comment='备注')
    
    # 关系
    child_inventory = db.relationship('InventoryV3', foreign_keys=[child_batch_id], backref='child_genealogy_records')
    parent_inventory = db.relationship('InventoryV3', foreign_keys=[parent_batch_id], backref='parent_genealogy_records')
    
    def to_dict(self):
        return {
            'id': self.id,
            'child_batch_id': self.child_batch_id,
            'parent_batch_id': self.parent_batch_id,
            'relationship_type': self.relationship_type,
            'quantity': float(self.quantity) if self.quantity else 0,
            'operation_type': self.operation_type,
            'operation_id': self.operation_id,
            'operation_time': self.operation_time.strftime('%Y-%m-%d %H:%M:%S') if self.operation_time else None,
            'remark': self.remark
        }
    
    @staticmethod
    def create_genealogy(child_batch_id, parent_batch_id, relationship_type, quantity, 
                        operation_type=None, operation_id=None, remark=None):
        """创建批次谱系关系"""
        genealogy = BatchGenealogy(
            child_batch_id=child_batch_id,
            parent_batch_id=parent_batch_id,
            relationship_type=relationship_type,
            quantity=quantity,
            operation_type=operation_type,
            operation_id=operation_id,
            remark=remark
        )
        db.session.add(genealogy)
        return genealogy


class BatchTrace(db.Model):
    """批次追溯表 - 记录批次的全链路流转"""
    __tablename__ = 'batch_trace'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_no = db.Column(db.String(50), nullable=False, index=True, comment='批次号')
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory_v3.id'), nullable=False, comment='库存 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件 ID')
    trace_type = db.Column(db.String(20), nullable=False, comment='追溯类型：INBOUND(入库)/STORAGE(存储)/OUTBOUND(出库)/TRANSFER(调拨)/ADJUST(调整)')
    source_type = db.Column(db.String(50), comment='单据类型')
    source_id = db.Column(db.Integer, comment='单据 ID')
    quantity = db.Column(db.Numeric(12, 4), nullable=False, comment='数量')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), comment='仓库 ID')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='库位 ID')
    operation_time = db.Column(db.DateTime, default=datetime.utcnow, comment='操作时间')
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='操作人 ID')
    remark = db.Column(db.Text, comment='备注')
    
    # 关系
    inventory = db.relationship('InventoryV3', backref='trace_records')
    part = db.relationship('SparePart', backref='batch_traces')
    warehouse = db.relationship('WarehouseV3', backref='batch_traces')
    location = db.relationship('WarehouseLocationV3', backref='batch_traces')
    operator = db.relationship('User', backref='batch_trace_operations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'batch_no': self.batch_no,
            'inventory_id': self.inventory_id,
            'part_id': self.part_id,
            'trace_type': self.trace_type,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'quantity': float(self.quantity) if self.quantity else 0,
            'warehouse_id': self.warehouse_id,
            'location_id': self.location_id,
            'operation_time': self.operation_time.strftime('%Y-%m-%d %H:%M:%S') if self.operation_time else None,
            'operator_id': self.operator_id,
            'remark': self.remark
        }
    
    @staticmethod
    def create_trace(batch_no, inventory_id, part_id, trace_type, quantity,
                    source_type=None, source_id=None, warehouse_id=None, 
                    location_id=None, operator_id=None, remark=None):
        """创建批次追溯记录"""
        trace = BatchTrace(
            batch_no=batch_no,
            inventory_id=inventory_id,
            part_id=part_id,
            trace_type=trace_type,
            quantity=quantity,
            source_type=source_type,
            source_id=source_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            operator_id=operator_id,
            remark=remark
        )
        db.session.add(trace)
        return trace
