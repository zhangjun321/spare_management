"""
库存预警模型
"""

from datetime import datetime
from app.extensions import db


class WarningRule(db.Model):
    """预警规则"""
    
    __tablename__ = 'warning_rule'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='预警规则 ID')
    rule_name = db.Column(db.String(100), nullable=False, comment='规则名称')
    rule_type = db.Column(db.String(50), nullable=False, index=True, comment='规则类型')
    
    # 适用范围
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), comment='仓库 ID')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), comment='分类 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), comment='备件 ID')
    
    # 阈值配置
    threshold_type = db.Column(db.String(20), comment='阈值类型')
    threshold_value = db.Column(db.Numeric(10, 2), comment='阈值')
    warning_level = db.Column(db.String(20), default='medium', comment='预警级别')
    
    # 通知配置
    notify_users = db.Column(db.JSON, comment='通知用户列表')
    notify_methods = db.Column(db.JSON, comment='通知方式')
    
    # 状态
    enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人')
    
    # 关系
    warehouse = db.relationship('WarehouseV3')
    category = db.relationship('Category')
    part = db.relationship('SparePart')
    creator = db.relationship('User', foreign_keys=[created_by])
    logs = db.relationship('WarningLog', back_populates='rule', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<WarningRule {self.rule_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'rule_name': self.rule_name,
            'rule_type': self.rule_type,
            'warehouse_id': self.warehouse_id,
            'warehouse_name': self.warehouse.name if self.warehouse else None,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'part_id': self.part_id,
            'part_name': self.part.name if self.part else None,
            'threshold_type': self.threshold_type,
            'threshold_value': float(self.threshold_value) if self.threshold_value else 0,
            'warning_level': self.warning_level,
            'notify_users': self.notify_users,
            'notify_methods': self.notify_methods,
            'enabled': self.enabled,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.name if self.creator else None
        }


class WarningLog(db.Model):
    """预警日志"""
    
    __tablename__ = 'warning_log'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='预警日志 ID')
    rule_id = db.Column(db.Integer, db.ForeignKey('warning_rule.id'), nullable=False, index=True, comment='预警规则 ID')
    
    # 关联对象
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory_v3.id'), comment='库存 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), comment='仓库 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), comment='备件 ID')
    
    # 预警内容
    warning_content = db.Column(db.Text, comment='预警内容')
    warning_level = db.Column(db.String(20), comment='预警级别')
    
    # 当前值
    current_value = db.Column(db.Numeric(12, 4), comment='当前值')
    threshold_value = db.Column(db.Numeric(10, 2), comment='阈值')
    
    # 处理状态
    status = db.Column(db.String(20), default='unhandled', comment='处理状态')
    
    # 通知信息
    notified_users = db.Column(db.JSON, comment='已通知用户')
    notified_time = db.Column(db.DateTime, comment='通知时间')
    
    # 处理信息
    handled_user = db.Column(db.Integer, db.ForeignKey('user.id'), comment='处理人')
    handled_time = db.Column(db.DateTime, comment='处理时间')
    handled_notes = db.Column(db.Text, comment='处理备注')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True, comment='创建时间')
    
    # 关系
    rule = db.relationship('WarningRule', back_populates='logs')
    inventory = db.relationship('InventoryV3')
    warehouse = db.relationship('WarehouseV3')
    part = db.relationship('SparePart')
    handler = db.relationship('User', foreign_keys=[handled_user])
    
    def __repr__(self):
        return f'<WarningLog {self.id}@{self.rule_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'rule_name': self.rule.rule_name if self.rule else None,
            'inventory_id': self.inventory_id,
            'warehouse_id': self.warehouse_id,
            'warehouse_name': self.warehouse.name if self.warehouse else None,
            'part_id': self.part_id,
            'part_name': self.part.name if self.part else None,
            'warning_content': self.warning_content,
            'warning_level': self.warning_level,
            'current_value': float(self.current_value) if self.current_value else 0,
            'threshold_value': float(self.threshold_value) if self.threshold_value else 0,
            'status': self.status,
            'notified_users': self.notified_users,
            'notified_time': self.notified_time.strftime('%Y-%m-%d %H:%M:%S') if self.notified_time else None,
            'handled_user': self.handled_user,
            'handler_name': self.handler.name if self.handler else None,
            'handled_time': self.handled_time.strftime('%Y-%m-%d %H:%M:%S') if self.handled_time else None,
            'handled_notes': self.handled_notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
    
    @staticmethod
    def create_warning(rule, inventory, current_value, threshold_value, warning_content, warning_level):
        """创建预警记录"""
        log = WarningLog(
            rule_id=rule.id,
            inventory_id=inventory.id,
            warehouse_id=inventory.warehouse_id,
            part_id=inventory.part_id,
            current_value=current_value,
            threshold_value=threshold_value,
            warning_content=warning_content,
            warning_level=warning_level,
            status='unhandled'
        )
        return log
