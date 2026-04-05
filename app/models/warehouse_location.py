from app.extensions import db
from datetime import datetime


class WarehouseLocation(db.Model):
    __tablename__ = 'warehouse_location'
    
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, comment='仓库 ID')
    location_code = db.Column(db.String(50), nullable=False, comment='库位代码')
    location_name = db.Column(db.String(100), comment='库位名称')
    location_type = db.Column(db.String(20), comment='库位类型')
    max_capacity = db.Column(db.Integer, comment='最大容量')
    current_capacity = db.Column(db.Integer, default=0, comment='当前容量')
    status = db.Column(db.String(20), default='available', comment='状态')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    
    warehouse = db.relationship('Warehouse', foreign_keys=[warehouse_id], back_populates='locations')
    batches = db.relationship('Batch', foreign_keys='Batch.location_id', back_populates='location', lazy='dynamic')
    spare_parts = db.relationship('SparePart', foreign_keys='SparePart.location_id', back_populates='warehouse_location', lazy='dynamic')
    
    __table_args__ = (
        db.UniqueConstraint('warehouse_id', 'location_code', name='uq_warehouse_location'),
    )
    
    def __repr__(self):
        return '<WarehouseLocation {}>'.format(self.location_code)
