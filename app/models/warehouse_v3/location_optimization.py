from app import db
from datetime import datetime
from decimal import Decimal


class LocationOptimization(db.Model):
    """库位优化配置表"""
    __tablename__ = 'location_optimization'
    
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), nullable=False, comment='仓库 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件 ID')
    current_location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='当前库位 ID')
    recommended_location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='推荐库位 ID')
    turnover_rate = db.Column(db.Numeric(10, 6), comment='周转率')
    pick_frequency = db.Column(db.Integer, default=0, comment='拣货频次')
    demand_stability = db.Column(db.String(20), comment='需求稳定性：HIGH/MEDIUM/LOW')
    weight = db.Column(db.Numeric(10, 2), comment='重量（kg）')
    volume = db.Column(db.Numeric(10, 2), comment='体积（m³）')
    storage_type = db.Column(db.String(20), comment='存储类型：BULK/RACK/SHELF')
    optimization_score = db.Column(db.Numeric(5, 2), comment='优化评分')
    last_optimized_at = db.Column(db.DateTime, comment='最后优化时间')
    status = db.Column(db.String(20), default='pending', comment='状态：pending/recommended/applied')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    remark = db.Column(db.Text, comment='备注')
    
    # 关系
    warehouse = db.relationship('WarehouseV3', backref='location_optimizations')
    part = db.relationship('SparePart', backref='location_optimizations')
    current_location = db.relationship('WarehouseLocationV3', foreign_keys=[current_location_id], backref='current_optimizations')
    recommended_location = db.relationship('WarehouseLocationV3', foreign_keys=[recommended_location_id], backref='recommended_optimizations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'warehouse_id': self.warehouse_id,
            'part_id': self.part_id,
            'current_location_id': self.current_location_id,
            'recommended_location_id': self.recommended_location_id,
            'turnover_rate': float(self.turnover_rate) if self.turnover_rate else 0,
            'pick_frequency': self.pick_frequency,
            'demand_stability': self.demand_stability,
            'weight': float(self.weight) if self.weight else 0,
            'volume': float(self.volume) if self.volume else 0,
            'storage_type': self.storage_type,
            'optimization_score': float(self.optimization_score) if self.optimization_score else 0,
            'last_optimized_at': self.last_optimized_at.strftime('%Y-%m-%d %H:%M:%S') if self.last_optimized_at else None,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'remark': self.remark
        }


class LocationHeatmap(db.Model):
    """库位热度表 - 记录库位的拣货活动"""
    __tablename__ = 'location_heatmap'
    
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), nullable=False, comment='仓库 ID')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), nullable=False, index=True, comment='库位 ID')
    date = db.Column(db.Date, nullable=False, comment='日期')
    pick_count = db.Column(db.Integer, default=0, comment='拣货次数')
    put_count = db.Column(db.Integer, default=0, comment='上架次数')
    move_count = db.Column(db.Integer, default=0, comment='移动次数')
    total_operations = db.Column(db.Integer, default=0, comment='总操作次数')
    heat_level = db.Column(db.String(20), comment='热度等级：HOT/WARM/COLD')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    warehouse = db.relationship('WarehouseV3', backref='location_heatmaps')
    location = db.relationship('WarehouseLocationV3', backref='heatmaps')
    
    def to_dict(self):
        return {
            'id': self.id,
            'warehouse_id': self.warehouse_id,
            'location_id': self.location_id,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'pick_count': self.pick_count,
            'put_count': self.put_count,
            'move_count': self.move_count,
            'total_operations': self.total_operations,
            'heat_level': self.heat_level,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class LocationSuggestion(db.Model):
    """库位推荐表 - 存储智能推荐结果"""
    __tablename__ = 'location_suggestion'
    
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), nullable=False, comment='仓库 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件 ID')
    part_no = db.Column(db.String(50), comment='备件编号')
    part_name = db.Column(db.String(200), comment='备件名称')
    suggested_location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'), comment='推荐库位 ID')
    suggestion_reason = db.Column(db.String(200), comment='推荐原因')
    priority = db.Column(db.Integer, default=1, comment='优先级')
    expected_efficiency_gain = db.Column(db.Numeric(5, 2), comment='预期效率提升（%）')
    status = db.Column(db.String(20), default='pending', comment='状态：pending/accepted/rejected')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    applied_at = db.Column(db.DateTime, comment='应用时间')
    applied_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='应用人 ID')
    
    # 关系
    warehouse = db.relationship('WarehouseV3', backref='location_suggestions')
    part = db.relationship('SparePart', backref='location_suggestions')
    suggested_location = db.relationship('WarehouseLocationV3', backref='suggestions')
    applier = db.relationship('User', backref='applied_suggestions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'warehouse_id': self.warehouse_id,
            'part_id': self.part_id,
            'part_no': self.part_no,
            'part_name': self.part_name,
            'suggested_location_id': self.suggested_location_id,
            'suggestion_reason': self.suggestion_reason,
            'priority': self.priority,
            'expected_efficiency_gain': float(self.expected_efficiency_gain) if self.expected_efficiency_gain else 0,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'applied_at': self.applied_at.strftime('%Y-%m-%d %H:%M:%S') if self.applied_at else None,
            'applied_by': self.applied_by
        }
