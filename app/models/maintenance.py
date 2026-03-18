from app.extensions import db
from datetime import datetime


class MaintenanceOrder(db.Model):
    __tablename__ = 'maintenance_order'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, comment='工单编号')
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False, comment='设备 ID')
    title = db.Column(db.String(200), nullable=False, comment='工单标题')
    description = db.Column(db.Text, comment='工单描述')
    priority = db.Column(db.String(20), default='medium', comment='优先级')
    type = db.Column(db.String(20), comment='工单类型')
    status = db.Column(db.String(20), default='pending', comment='状态')
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='报修人 ID')
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), comment='指派给')
    scheduled_date = db.Column(db.DateTime, comment='计划日期')
    completed_date = db.Column(db.DateTime, comment='完成日期')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    requester = db.relationship('User', foreign_keys=[requester_id], backref='user_requested_orders')
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='user_assigned_orders')
    equipment = db.relationship('Equipment', foreign_keys=[equipment_id])
    tasks = db.relationship('MaintenanceTask', foreign_keys='MaintenanceTask.order_id', backref='task_order', lazy='dynamic')
    records = db.relationship('MaintenanceRecord', foreign_keys='MaintenanceRecord.order_id', backref='record_order', lazy='dynamic')
    costs = db.relationship('MaintenanceCost', foreign_keys='MaintenanceCost.order_id', backref='cost_order', lazy='dynamic')
    
    def __repr__(self):
        return f'<MaintenanceOrder {self.order_number}>'


class MaintenanceTask(db.Model):
    __tablename__ = 'maintenance_task'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('maintenance_order.id'), nullable=False, comment='工单 ID')
    task_name = db.Column(db.String(200), nullable=False, comment='任务名称')
    description = db.Column(db.Text, comment='任务描述')
    status = db.Column(db.String(20), default='pending', comment='状态')
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), comment='指派给')
    started_at = db.Column(db.DateTime, comment='开始时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    assignee = db.relationship('User', foreign_keys=[assigned_to])
    
    def __repr__(self):
        return f'<MaintenanceTask {self.id}>'


class MaintenanceRecord(db.Model):
    __tablename__ = 'maintenance_record'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('maintenance_order.id'), nullable=False, comment='工单 ID')
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False, comment='设备 ID')
    maintenance_type = db.Column(db.String(20), comment='维修类型')
    description = db.Column(db.Text, comment='维修描述')
    spare_parts_used = db.Column(db.Text, comment='使用的备件')
    maintenance_result = db.Column(db.Text, comment='维修结果')
    maintenance_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='维修人 ID')
    started_at = db.Column(db.DateTime, comment='开始时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    def __repr__(self):
        return f'<MaintenanceRecord {self.id}>'


class MaintenanceCost(db.Model):
    __tablename__ = 'maintenance_cost'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('maintenance_order.id'), nullable=False, comment='工单 ID')
    cost_type = db.Column(db.String(20), comment='费用类型')
    description = db.Column(db.String(200), comment='费用描述')
    amount = db.Column(db.Numeric(10, 2), nullable=False, comment='金额')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    
    order = db.relationship('MaintenanceOrder', foreign_keys=[order_id])
    
    def __repr__(self):
        return f'<MaintenanceCost {self.id}>'
