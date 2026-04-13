from app import db
from datetime import datetime
from decimal import Decimal


class TaskQueue(db.Model):
    """任务队列表"""
    __tablename__ = 'task_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    queue_name = db.Column(db.String(50), nullable=False, index=True, comment='队列名称')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), comment='仓库 ID')
    queue_type = db.Column(db.String(20), nullable=False, comment='队列类型：PICK/PUT/MOVE/COUNT/TRANSFER')
    priority = db.Column(db.Integer, default=5, comment='优先级 1-10，1 最高')
    max_capacity = db.Column(db.Integer, default=1000, comment='最大容量')
    current_size = db.Column(db.Integer, default=0, comment='当前大小')
    status = db.Column(db.String(20), default='active', comment='状态：active/paused/closed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    warehouse = db.relationship('WarehouseV3', backref='task_queues')
    tasks = db.relationship('WarehouseTask', backref='queue', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'queue_name': self.queue_name,
            'warehouse_id': self.warehouse_id,
            'queue_type': self.queue_type,
            'priority': self.priority,
            'max_capacity': self.max_capacity,
            'current_size': self.current_size,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class WarehouseTask(db.Model):
    """仓库作业任务表"""
    __tablename__ = 'warehouse_task'
    
    id = db.Column(db.Integer, primary_key=True)
    task_no = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='任务号')
    queue_id = db.Column(db.Integer, db.ForeignKey('task_queue.id'), index=True, comment='队列 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), nullable=False, comment='仓库 ID')
    task_type = db.Column(db.String(20), nullable=False, comment='任务类型：PICK/PUT/MOVE/COUNT/TRANSFER/ADJUST')
    task_subtype = db.Column(db.String(50), comment='任务子类型')
    priority = db.Column(db.Integer, default=5, comment='优先级 1-10')
    status = db.Column(db.String(20), default='pending', comment='状态：pending/ready/assigned/working/paused/completed/cancelled/failed')
    
    # 任务内容
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), index=True, comment='备件 ID')
    part_no = db.Column(db.String(50), comment='备件编号')
    part_name = db.Column(db.String(200), comment='备件名称')
    from_location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='源库位 ID')
    to_location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='目标库位 ID')
    quantity = db.Column(db.Numeric(12, 4), nullable=False, comment='数量')
    unit = db.Column(db.String(20), comment='单位')
    batch_no = db.Column(db.String(50), comment='批次号')
    
    # 关联单据
    source_type = db.Column(db.String(50), comment='单据类型：OUTBOUND/INBOUND/TRANSFER/COUNT')
    source_id = db.Column(db.Integer, comment='单据 ID')
    source_no = db.Column(db.String(50), comment='单据号')
    
    # 分配与执行
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), comment='分配给 ID')
    assigned_at = db.Column(db.DateTime, comment='分配时间')
    started_at = db.Column(db.DateTime, comment='开始时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    estimated_time = db.Column(db.Integer, comment='预计耗时（分钟）')
    actual_time = db.Column(db.Integer, comment='实际耗时（分钟）')
    
    # 调度信息
    route_sequence = db.Column(db.Integer, comment='路线顺序')
    route_distance = db.Column(db.Numeric(10, 2), comment='路线距离（米）')
    optimal_route = db.Column(db.Text, comment='最优路径 JSON')
    
    # 其他
    error_message = db.Column(db.Text, comment='错误信息')
    retry_count = db.Column(db.Integer, default=0, comment='重试次数')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    part = db.relationship('SparePart', backref='warehouse_tasks')
    from_location = db.relationship('WarehouseLocationV3', foreign_keys=[from_location_id], backref='from_tasks')
    to_location = db.relationship('WarehouseLocationV3', foreign_keys=[to_location_id], backref='to_tasks')
    assignee = db.relationship('User', backref='assigned_tasks')
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_no': self.task_no,
            'queue_id': self.queue_id,
            'warehouse_id': self.warehouse_id,
            'task_type': self.task_type,
            'task_subtype': self.task_subtype,
            'priority': self.priority,
            'status': self.status,
            'part_id': self.part_id,
            'part_no': self.part_no,
            'part_name': self.part_name,
            'from_location_id': self.from_location_id,
            'to_location_id': self.to_location_id,
            'quantity': float(self.quantity) if self.quantity else 0,
            'unit': self.unit,
            'batch_no': self.batch_no,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'source_no': self.source_no,
            'assigned_to': self.assigned_to,
            'assigned_at': self.assigned_at.strftime('%Y-%m-%d %H:%M:%S') if self.assigned_at else None,
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None,
            'estimated_time': self.estimated_time,
            'actual_time': self.actual_time,
            'route_sequence': self.route_sequence,
            'route_distance': float(self.route_distance) if self.route_distance else 0,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'remark': self.remark
        }


class TaskScheduler(db.Model):
    """任务调度器配置表"""
    __tablename__ = 'task_scheduler'
    
    id = db.Column(db.Integer, primary_key=True)
    scheduler_name = db.Column(db.String(100), nullable=False, comment='调度器名称')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), comment='仓库 ID')
    scheduler_type = db.Column(db.String(20), nullable=False, comment='调度器类型：ROUND_ROBIN/PRIORITY/FIRST_IN_FIRST_OUT/SKILL_BASED')
    is_active = db.Column(db.Boolean, default=True, comment='是否激活')
    config = db.Column(db.Text, comment='配置 JSON')
    last_run_at = db.Column(db.DateTime, comment='最后运行时间')
    next_run_at = db.Column(db.DateTime, comment='下次运行时间')
    run_count = db.Column(db.Integer, default=0, comment='运行次数')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    warehouse = db.relationship('WarehouseV3', backref='task_schedulers')
    
    def to_dict(self):
        return {
            'id': self.id,
            'scheduler_name': self.scheduler_name,
            'warehouse_id': self.warehouse_id,
            'scheduler_type': self.scheduler_type,
            'is_active': self.is_active,
            'config': self.config,
            'last_run_at': self.last_run_at.strftime('%Y-%m-%d %H:%M:%S') if self.last_run_at else None,
            'next_run_at': self.next_run_at.strftime('%Y-%m-%d %H:%M:%S') if self.next_run_at else None,
            'run_count': self.run_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Worker(db.Model):
    """作业人员表"""
    __tablename__ = 'worker'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False, comment='用户 ID')
    employee_no = db.Column(db.String(50), unique=True, comment='工号')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), comment='仓库 ID')
    status = db.Column(db.String(20), default='available', comment='状态：available/busy/offline/on_leave')
    current_task_id = db.Column(db.Integer, db.ForeignKey('warehouse_task.id'), comment='当前任务 ID')
    skill_level = db.Column(db.Integer, default=1, comment='技能等级 1-5')
    efficiency_score = db.Column(db.Numeric(5, 2), default=100, comment='效率评分')
    total_tasks = db.Column(db.Integer, default=0, comment='总任务数')
    completed_tasks = db.Column(db.Integer, default=0, comment='完成任务数')
    last_active_at = db.Column(db.DateTime, comment='最后活跃时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    user = db.relationship('User', backref='worker_profile')
    warehouse = db.relationship('WarehouseV3', backref='workers')
    current_task = db.relationship('WarehouseTask', backref='assigned_worker')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'employee_no': self.employee_no,
            'warehouse_id': self.warehouse_id,
            'status': self.status,
            'current_task_id': self.current_task_id,
            'skill_level': self.skill_level,
            'efficiency_score': float(self.efficiency_score) if self.efficiency_score else 0,
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'last_active_at': self.last_active_at.strftime('%Y-%m-%d %H:%M:%S') if self.last_active_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
