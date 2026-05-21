# -*- coding: utf-8 -*-
"""
库存预留模型 — 项目/订单维度库存预留

可用库存 = 物理库存 - 在途冻结 - 预留量
预留有过期时间和优先级，到期自动释放
"""
from app.extensions import db
from datetime import datetime


class Reservation(db.Model):
    """库存预留"""
    __tablename__ = 'reservation'

    id = db.Column(db.Integer, primary_key=True)
    reservation_code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='预留编号(RS前缀)')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), index=True, comment='仓库ID(可选,不填则全局预留)')
    quantity = db.Column(db.Numeric(10, 2), nullable=False, comment='预留数量')
    released_quantity = db.Column(db.Numeric(10, 2), default=0, comment='已释放数量')
    project = db.Column(db.String(200), comment='项目名称/编号')
    order_ref = db.Column(db.String(100), comment='关联订单号')
    reason = db.Column(db.Text, comment='预留原因')
    priority = db.Column(db.Integer, default=5, comment='优先级: 1-10, 越高越优先释放')
    status = db.Column(db.String(20), default='active', comment='状态: active/released/expired/consumed')
    expire_at = db.Column(db.DateTime, nullable=False, comment='到期时间')
    released_at = db.Column(db.DateTime, comment='释放时间')
    released_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='释放人')
    consumed_at = db.Column(db.DateTime, comment='消费时间(实际出库时转consumed)')
    version = db.Column(db.Integer, default=1, comment='乐观锁版本号')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人')

    # Relationships
    spare_part = db.relationship('SparePart')
    warehouse = db.relationship('Warehouse')

    def to_dict(self):
        return {
            'id': self.id,
            'reservation_code': self.reservation_code,
            'spare_part_id': self.spare_part_id,
            'spare_part_code': self.spare_part.part_code if self.spare_part else None,
            'spare_part_name': self.spare_part.name if self.spare_part else None,
            'warehouse_id': self.warehouse_id,
            'warehouse_name': self.warehouse.name if self.warehouse else None,
            'quantity': float(self.quantity) if self.quantity else 0,
            'released_quantity': float(self.released_quantity) if self.released_quantity else 0,
            'available_quantity': float(self.quantity or 0) - float(self.released_quantity or 0),
            'project': self.project,
            'order_ref': self.order_ref,
            'reason': self.reason,
            'priority': self.priority,
            'status': self.status,
            'expire_at': self.expire_at.strftime('%Y-%m-%d %H:%M:%S') if self.expire_at else None,
            'is_expired': self.expire_at < datetime.utcnow() if self.expire_at else False,
            'released_at': self.released_at.strftime('%Y-%m-%d %H:%M:%S') if self.released_at else None,
            'consumed_at': self.consumed_at.strftime('%Y-%m-%d %H:%M:%S') if self.consumed_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'created_by': self.created_by,
        }

    def is_expired(self):
        return self.expire_at < datetime.utcnow() if self.expire_at else False

    def release(self, operator_id=None, partial_qty=None):
        """释放预留(支持部分释放)"""
        qty = partial_qty or (float(self.quantity) - float(self.released_quantity or 0))
        if qty <= 0:
            raise ValueError('无可释放的预留数量')
        self.released_quantity = float(self.released_quantity or 0) + qty
