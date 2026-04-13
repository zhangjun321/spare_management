from app import db
from datetime import datetime
from decimal import Decimal


class CycleCountPlan(db.Model):
    """循环盘点计划表"""
    __tablename__ = 'cycle_count_plan'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_no = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='盘点计划号')
    plan_name = db.Column(db.String(100), nullable=False, comment='盘点计划名称')
    plan_type = db.Column(db.String(20), nullable=False, comment='计划类型：ABC(ABC 分类)/PERIODIC(定期)/SPECIAL(特殊)')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), comment='仓库 ID')
    abc_class = db.Column(db.String(10), comment='ABC 分类：A/B/C')
    start_date = db.Column(db.Date, comment='开始日期')
    end_date = db.Column(db.Date, comment='结束日期')
    frequency = db.Column(db.Integer, comment='盘点频率（天）')
    status = db.Column(db.String(20), default='draft', comment='状态：draft/active/completed/cancelled')
    total_items = db.Column(db.Integer, default=0, comment='总物品数')
    counted_items = db.Column(db.Integer, default=0, comment='已盘点物品数')
    variance_items = db.Column(db.Integer, default=0, comment='差异物品数')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人 ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='审批人 ID')
    approved_at = db.Column(db.DateTime, comment='审批时间')
    remark = db.Column(db.Text, comment='备注')
    
    # 关系
    warehouse = db.relationship('WarehouseV3', backref='cycle_count_plans')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_cycle_count_plans')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_cycle_count_plans')
    items = db.relationship('CycleCountItem', backref='plan', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'plan_no': self.plan_no,
            'plan_name': self.plan_name,
            'plan_type': self.plan_type,
            'warehouse_id': self.warehouse_id,
            'abc_class': self.abc_class,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'frequency': self.frequency,
            'status': self.status,
            'total_items': self.total_items,
            'counted_items': self.counted_items,
            'variance_items': self.variance_items,
            'created_by': self.created_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.strftime('%Y-%m-%d %H:%M:%S') if self.approved_at else None,
            'remark': self.remark
        }
    
    def get_progress(self):
        """获取盘点进度"""
        if self.total_items == 0:
            return 0
        return round((self.counted_items / self.total_items) * 100, 2)
    
    @staticmethod
    def generate_plan_no():
        """生成盘点计划号"""
        from datetime import datetime
        prefix = 'CCP'
        date_str = datetime.now().strftime('%Y%m%d')
        # 获取当天最后一个计划号
        last_plan = CycleCountPlan.query.filter(
            CycleCountPlan.plan_no.like(f'{prefix}{date_str}%')
        ).order_by(CycleCountPlan.plan_no.desc()).first()
        
        if last_plan:
            # 提取序号并 +1
            last_no = int(last_plan.plan_no[-3:])
            new_no = last_no + 1
        else:
            new_no = 1
        
        return f'{prefix}{date_str}{new_no:03d}'


class CycleCountItem(db.Model):
    """循环盘点项目表"""
    __tablename__ = 'cycle_count_item'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('cycle_count_plan.id'), nullable=False, index=True, comment='盘点计划 ID')
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory_v3.id'), nullable=False, comment='库存 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件 ID')
    part_no = db.Column(db.String(50), comment='备件编号')
    part_name = db.Column(db.String(200), comment='备件名称')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), comment='仓库 ID')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='库位 ID')
    batch_no = db.Column(db.String(50), comment='批次号')
    book_quantity = db.Column(db.Numeric(12, 4), nullable=False, default=0, comment='账面数量')
    actual_quantity = db.Column(db.Numeric(12, 4), comment='实际数量')
    variance_quantity = db.Column(db.Numeric(12, 4), comment='差异数量')
    variance_rate = db.Column(db.Numeric(5, 4), comment='差异率')
    unit = db.Column(db.String(20), comment='单位')
    status = db.Column(db.String(20), default='pending', comment='状态：pending/counted/reviewed/adjusted')
    counted_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='盘点人 ID')
    counted_at = db.Column(db.DateTime, comment='盘点时间')
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='复核人 ID')
    reviewed_at = db.Column(db.DateTime, comment='复核时间')
    variance_reason = db.Column(db.String(500), comment='差异原因')
    remark = db.Column(db.Text, comment='备注')
    
    # 关系
    inventory = db.relationship('InventoryV3', backref='cycle_count_items')
    part = db.relationship('SparePart', backref='cycle_count_items')
    warehouse = db.relationship('WarehouseV3', backref='cycle_count_items')
    location = db.relationship('WarehouseLocationV3', backref='cycle_count_items')
    counter = db.relationship('User', foreign_keys=[counted_by], backref='counted_items')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'inventory_id': self.inventory_id,
            'part_id': self.part_id,
            'part_no': self.part_no,
            'part_name': self.part_name,
            'warehouse_id': self.warehouse_id,
            'location_id': self.location_id,
            'batch_no': self.batch_no,
            'book_quantity': float(self.book_quantity) if self.book_quantity else 0,
            'actual_quantity': float(self.actual_quantity) if self.actual_quantity else None,
            'variance_quantity': float(self.variance_quantity) if self.variance_quantity else None,
            'variance_rate': float(self.variance_rate) if self.variance_rate else None,
            'unit': self.unit,
            'status': self.status,
            'counted_by': self.counted_by,
            'counted_at': self.counted_at.strftime('%Y-%m-%d %H:%M:%S') if self.counted_at else None,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if self.reviewed_at else None,
            'variance_reason': self.variance_reason,
            'remark': self.remark
        }
    
    def calculate_variance(self):
        """计算差异"""
        if self.actual_quantity is not None:
            self.variance_quantity = self.actual_quantity - self.book_quantity
            if self.book_quantity and self.book_quantity > 0:
                self.variance_rate = abs(self.variance_quantity) / self.book_quantity
            else:
                self.variance_rate = None


class ABCClassification(db.Model):
    """ABC 分类表"""
    __tablename__ = 'abc_classification'
    
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, unique=True, index=True, comment='备件 ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), comment='仓库 ID')
    annual_consumption = db.Column(db.Numeric(12, 2), default=0, comment='年消耗金额')
    consumption_percentage = db.Column(db.Numeric(5, 4), comment='消耗占比')
    abc_class = db.Column(db.String(10), nullable=False, comment='ABC 分类：A/B/C')
    last_count_date = db.Column(db.Date, comment='最后盘点日期')
    next_count_date = db.Column(db.Date, comment='下次盘点日期')
    count_frequency = db.Column(db.Integer, default=30, comment='盘点频率（天）')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    part = db.relationship('SparePart', backref='abc_classifications')
    warehouse = db.relationship('WarehouseV3', backref='abc_classifications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'part_id': self.part_id,
            'warehouse_id': self.warehouse_id,
            'annual_consumption': float(self.annual_consumption) if self.annual_consumption else 0,
            'consumption_percentage': float(self.consumption_percentage) if self.consumption_percentage else 0,
            'abc_class': self.abc_class,
            'last_count_date': self.last_count_date.strftime('%Y-%m-%d') if self.last_count_date else None,
            'next_count_date': self.next_count_date.strftime('%Y-%m-%d') if self.next_count_date else None,
            'count_frequency': self.count_frequency,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
    
    @staticmethod
    def get_count_frequency(abc_class):
        """获取 ABC 分类对应的盘点频率"""
        frequencies = {
            'A': 7,    # A 类物品每周盘点
            'B': 30,   # B 类物品每月盘点
            'C': 90    # C 类物品每季度盘点
        }
        return frequencies.get(abc_class, 30)
