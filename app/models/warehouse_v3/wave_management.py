from app import db
from datetime import datetime
from decimal import Decimal


class WavePlan(db.Model):
    """波次计划表 - 定义波次生成策略"""
    __tablename__ = 'wave_plan'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='计划代码')
    plan_name = db.Column(db.String(100), nullable=False, comment='计划名称')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), comment='仓库 ID')
    strategy_type = db.Column(db.String(20), nullable=False, comment='策略类型：TIME(定时)/QUANTITY(定量)/ROUTE(路线)/CARRIER(承运商)')
    priority = db.Column(db.Integer, default=1, comment='优先级')
    time_window = db.Column(db.Integer, comment='时间窗口（分钟）')
    max_orders = db.Column(db.Integer, comment='最大订单数')
    max_items = db.Column(db.Integer, comment='最大商品项数')
    route_filter = db.Column(db.String(200), comment='路线筛选条件')
    carrier_filter = db.Column(db.String(200), comment='承运商筛选条件')
    status = db.Column(db.String(20), default='active', comment='状态：active/inactive')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    remark = db.Column(db.Text, comment='备注')
    
    # 关系
    warehouse = db.relationship('WarehouseV3', backref='wave_plans')
    creator = db.relationship('User', backref='created_wave_plans')
    waves = db.relationship('WaveOrder', backref='plan', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'plan_code': self.plan_code,
            'plan_name': self.plan_name,
            'warehouse_id': self.warehouse_id,
            'strategy_type': self.strategy_type,
            'priority': self.priority,
            'time_window': self.time_window,
            'max_orders': self.max_orders,
            'max_items': self.max_items,
            'route_filter': self.route_filter,
            'carrier_filter': self.carrier_filter,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'created_by': self.created_by,
            'remark': self.remark
        }


class WaveOrder(db.Model):
    """波次订单表"""
    __tablename__ = 'wave_order'
    
    id = db.Column(db.Integer, primary_key=True)
    wave_no = db.Column(db.String(50), nullable=False, index=True, comment='波次号')
    plan_id = db.Column(db.Integer, db.ForeignKey('wave_plan.id'), comment='波次计划 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), nullable=False, comment='仓库 ID')
    status = db.Column(db.String(20), default='pending', comment='状态：pending/picking/partial/completed/cancelled')
    total_orders = db.Column(db.Integer, default=0, comment='订单总数')
    total_items = db.Column(db.Integer, default=0, comment='商品总项数')
    total_quantity = db.Column(db.Numeric(12, 4), default=0, comment='商品总数量')
    picked_orders = db.Column(db.Integer, default=0, comment='已拣货订单数')
    picked_items = db.Column(db.Integer, default=0, comment='已拣货项数')
    progress = db.Column(db.Numeric(5, 2), default=0, comment='进度百分比')
    started_at = db.Column(db.DateTime, comment='开始时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    remark = db.Column(db.Text, comment='备注')
    
    # 关系
    warehouse = db.relationship('WarehouseV3', backref='wave_orders')
    creator = db.relationship('User', backref='created_wave_orders')
    orders = db.relationship('WaveOrderItem', backref='wave', lazy='dynamic')
    tasks = db.relationship('WaveTask', backref='wave', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'wave_no': self.wave_no,
            'plan_id': self.plan_id,
            'warehouse_id': self.warehouse_id,
            'status': self.status,
            'total_orders': self.total_orders,
            'total_items': self.total_items,
            'total_quantity': float(self.total_quantity) if self.total_quantity else 0,
            'picked_orders': self.picked_orders,
            'picked_items': self.picked_items,
            'progress': float(self.progress) if self.progress else 0,
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'created_by': self.created_by,
            'remark': self.remark
        }


class WaveOrderItem(db.Model):
    """波次订单明细表"""
    __tablename__ = 'wave_order_item'
    
    id = db.Column(db.Integer, primary_key=True)
    wave_id = db.Column(db.Integer, db.ForeignKey('wave_order.id'), nullable=False, index=True, comment='波次 ID')
    outbound_order_id = db.Column(db.Integer, db.ForeignKey('outbound_order_v3.id'), nullable=False, comment='出库单 ID')
    outbound_order_no = db.Column(db.String(50), nullable=False, index=True, comment='出库单号')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件 ID')
    part_no = db.Column(db.String(50), comment='备件编号')
    part_name = db.Column(db.String(200), comment='备件名称')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), comment='仓库 ID')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='库位 ID')
    batch_no = db.Column(db.String(50), comment='批次号')
    required_quantity = db.Column(db.Numeric(12, 4), nullable=False, comment='需求数量')
    picked_quantity = db.Column(db.Numeric(12, 4), default=0, comment='已拣货数量')
    status = db.Column(db.String(20), default='pending', comment='状态：pending/picking/completed/shortage')
    priority = db.Column(db.Integer, default=1, comment='优先级')
    picked_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='拣货人 ID')
    picked_at = db.Column(db.DateTime, comment='拣货时间')
    remark = db.Column(db.Text, comment='备注')
    
    # 关系
    part = db.relationship('SparePart', backref='wave_order_items')
    warehouse = db.relationship('WarehouseV3', backref='wave_order_items')
    location = db.relationship('WarehouseLocationV3', backref='wave_order_items')
    picker = db.relationship('User', backref='picked_wave_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'wave_id': self.wave_id,
            'outbound_order_id': self.outbound_order_id,
            'outbound_order_no': self.outbound_order_no,
            'part_id': self.part_id,
            'part_no': self.part_no,
            'part_name': self.part_name,
            'warehouse_id': self.warehouse_id,
            'location_id': self.location_id,
            'batch_no': self.batch_no,
            'required_quantity': float(self.required_quantity) if self.required_quantity else 0,
            'picked_quantity': float(self.picked_quantity) if self.picked_quantity else 0,
            'status': self.status,
            'priority': self.priority,
            'picked_by': self.picked_by,
            'picked_at': self.picked_at.strftime('%Y-%m-%d %H:%M:%S') if self.picked_at else None,
            'remark': self.remark
        }


class WaveTask(db.Model):
    """波次拣货任务表"""
    __tablename__ = 'wave_task'
    
    id = db.Column(db.Integer, primary_key=True)
    task_no = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='任务号')
    wave_id = db.Column(db.Integer, db.ForeignKey('wave_order.id'), nullable=False, index=True, comment='波次 ID')
    task_type = db.Column(db.String(20), nullable=False, comment='任务类型：PICK(拣货)/MOVE(搬运)/PACK(打包)')
    status = db.Column(db.String(20), default='pending', comment='状态：pending/assigned/working/completed/cancelled')
    priority = db.Column(db.Integer, default=1, comment='优先级')
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), comment='分配给 ID')
    route_sequence = db.Column(db.Integer, comment='路线顺序')
    estimated_time = db.Column(db.Integer, comment='预计耗时（分钟）')
    actual_time = db.Column(db.Integer, comment='实际耗时（分钟）')
    started_at = db.Column(db.DateTime, comment='开始时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    remark = db.Column(db.Text, comment='备注')
    
    # 关系
    assignee = db.relationship('User', backref='wave_tasks')
    items = db.relationship('WaveTaskItem', backref='task', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_no': self.task_no,
            'wave_id': self.wave_id,
            'task_type': self.task_type,
            'status': self.status,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
            'route_sequence': self.route_sequence,
            'estimated_time': self.estimated_time,
            'actual_time': self.actual_time,
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'remark': self.remark
        }


class WaveTaskItem(db.Model):
    """波次拣货任务明细表"""
    __tablename__ = 'wave_task_item'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('wave_task.id'), nullable=False, index=True, comment='任务 ID')
    wave_item_id = db.Column(db.Integer, db.ForeignKey('wave_order_item.id'), nullable=False, comment='波次订单项 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件 ID')
    part_no = db.Column(db.String(50), comment='备件编号')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), nullable=False, comment='库位 ID')
    location_code = db.Column(db.String(50), comment='库位编码')
    batch_no = db.Column(db.String(50), comment='批次号')
    quantity = db.Column(db.Numeric(12, 4), nullable=False, comment='数量')
    picked_quantity = db.Column(db.Numeric(12, 4), default=0, comment='已拣货数量')
    status = db.Column(db.String(20), default='pending', comment='状态')
    sequence = db.Column(db.Integer, comment='拣货顺序')
    
    # 关系
    part = db.relationship('SparePart', backref='wave_task_items')
    location = db.relationship('WarehouseLocationV3', backref='wave_task_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'wave_item_id': self.wave_item_id,
            'part_id': self.part_id,
            'part_no': self.part_no,
            'location_id': self.location_id,
            'location_code': self.location_code,
            'batch_no': self.batch_no,
            'quantity': float(self.quantity) if self.quantity else 0,
            'picked_quantity': float(self.picked_quantity) if self.picked_quantity else 0,
            'status': self.status,
            'sequence': self.sequence
        }
