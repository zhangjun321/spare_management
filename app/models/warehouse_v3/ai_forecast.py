from app import db
from datetime import datetime
from decimal import Decimal


class DemandForecast(db.Model):
    """需求预测表"""
    __tablename__ = 'demand_forecast'
    
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), nullable=False, index=True, comment='仓库 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件 ID')
    part_no = db.Column(db.String(50), comment='备件编号')
    part_name = db.Column(db.String(200), comment='备件名称')
    forecast_date = db.Column(db.Date, nullable=False, index=True, comment='预测日期')
    forecast_period = db.Column(db.Integer, nullable=False, comment='预测周期（天）')
    predicted_demand = db.Column(db.Numeric(12, 4), nullable=False, comment='预测需求量')
    confidence_level = db.Column(db.Numeric(5, 2), comment='置信度（%）')
    demand_trend = db.Column(db.String(20), comment='需求趋势：INCREASING/DECREASING/STABLE/SEASONAL')
    seasonality_index = db.Column(db.Numeric(5, 2), comment='季节性指数')
    model_type = db.Column(db.String(50), comment='预测模型：ARIMA/PROPHET/LSTM/ENSEMBLE')
    actual_demand = db.Column(db.Numeric(12, 4), comment='实际需求')
    forecast_error = db.Column(db.Numeric(12, 4), comment='预测误差')
    accuracy = db.Column(db.Numeric(5, 2), comment='准确率（%）')
    status = db.Column(db.String(20), default='active', comment='状态：active/verified/archived')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    remark = db.Column(db.Text, comment='备注')
    
    # 关系
    warehouse = db.relationship('WarehouseV3', backref='demand_forecasts')
    part = db.relationship('SparePart', backref='demand_forecasts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'warehouse_id': self.warehouse_id,
            'part_id': self.part_id,
            'part_no': self.part_no,
            'part_name': self.part_name,
            'forecast_date': self.forecast_date.strftime('%Y-%m-%d') if self.forecast_date else None,
            'forecast_period': self.forecast_period,
            'predicted_demand': float(self.predicted_demand) if self.predicted_demand else 0,
            'confidence_level': float(self.confidence_level) if self.confidence_level else 0,
            'demand_trend': self.demand_trend,
            'seasonality_index': float(self.seasonality_index) if self.seasonality_index else 0,
            'model_type': self.model_type,
            'actual_demand': float(self.actual_demand) if self.actual_demand else None,
            'forecast_error': float(self.forecast_error) if self.forecast_error else None,
            'accuracy': float(self.accuracy) if self.accuracy else 0,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'remark': self.remark
        }


class ReorderRecommendation(db.Model):
    """补货建议表"""
    __tablename__ = 'reorder_recommendation'
    
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), nullable=False, comment='仓库 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件 ID')
    part_no = db.Column(db.String(50), comment='备件编号')
    part_name = db.Column(db.String(200), comment='备件名称')
    current_stock = db.Column(db.Numeric(12, 4), nullable=False, comment='当前库存')
    safety_stock = db.Column(db.Numeric(12, 4), comment='安全库存')
    reorder_point = db.Column(db.Numeric(12, 4), comment=' reorder 点')
    recommended_quantity = db.Column(db.Numeric(12, 4), nullable=False, comment='建议补货量')
    priority = db.Column(db.Integer, default=3, comment='优先级 1-5，1 最高')
    urgency_level = db.Column(db.String(20), comment='紧急程度：URGENT/HIGH/MEDIUM/LOW')
    lead_time_days = db.Column(db.Integer, comment='采购提前期（天）')
    estimated_cost = db.Column(db.Numeric(12, 2), comment='预估成本')
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), comment='供应商 ID')
    forecast_demand = db.Column(db.Numeric(12, 4), comment='预测需求')
    stockout_risk = db.Column(db.Numeric(5, 2), comment='缺货风险（%）')
    status = db.Column(db.String(20), default='pending', comment='状态：pending/approved/ordered/cancelled')
    generated_by = db.Column(db.String(50), default='AI', comment='生成方式：AI/MANUAL')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    approved_at = db.Column(db.DateTime, comment='审批时间')
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='审批人 ID')
    ordered_at = db.Column(db.DateTime, comment='下单时间')
    remark = db.Column(db.Text, comment='备注')
    
    # 关系
    warehouse = db.relationship('WarehouseV3', backref='reorder_recommendations')
    part = db.relationship('SparePart', backref='reorder_recommendations')
    supplier = db.relationship('Supplier', backref='reorder_recommendations')
    approver = db.relationship('User', backref='approved_reorders')
    
    def to_dict(self):
        return {
            'id': self.id,
            'warehouse_id': self.warehouse_id,
            'part_id': self.part_id,
            'part_no': self.part_no,
            'part_name': self.part_name,
            'current_stock': float(self.current_stock) if self.current_stock else 0,
            'safety_stock': float(self.safety_stock) if self.safety_stock else None,
            'reorder_point': float(self.reorder_point) if self.reorder_point else None,
            'recommended_quantity': float(self.recommended_quantity) if self.recommended_quantity else 0,
            'priority': self.priority,
            'urgency_level': self.urgency_level,
            'lead_time_days': self.lead_time_days,
            'estimated_cost': float(self.estimated_cost) if self.estimated_cost else None,
            'supplier_id': self.supplier_id,
            'forecast_demand': float(self.forecast_demand) if self.forecast_demand else None,
            'stockout_risk': float(self.stockout_risk) if self.stockout_risk else 0,
            'status': self.status,
            'generated_by': self.generated_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'approved_at': self.approved_at.strftime('%Y-%m-%d %H:%M:%S') if self.approved_at else None,
            'approved_by': self.approved_by,
            'ordered_at': self.ordered_at.strftime('%Y-%m-%d %H:%M:%S') if self.ordered_at else None,
            'remark': self.remark
        }


class InventoryOptimization(db.Model):
    """库存优化配置表"""
    __tablename__ = 'inventory_optimization'
    
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'), nullable=False, comment='仓库 ID')
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, unique=True, index=True, comment='备件 ID')
    target_service_level = db.Column(db.Numeric(5, 2), default=95.00, comment='目标服务水平（%）')
    holding_cost_rate = db.Column(db.Numeric(10, 4), comment='持有成本率')
    ordering_cost = db.Column(db.Numeric(10, 2), comment='订货成本')
    eoq = db.Column(db.Numeric(12, 4), comment='经济订货批量 EOQ')
    safety_stock = db.Column(db.Numeric(12, 4), comment='安全库存')
    reorder_point = db.Column(db.Numeric(12, 4), comment=' reorder 点')
    max_stock = db.Column(db.Numeric(12, 4), comment='最大库存')
    demand_variability = db.Column(db.Numeric(5, 2), comment='需求波动率')
    lead_time_variability = db.Column(db.Numeric(5, 2), comment='提前期波动率')
    last_calculated_at = db.Column(db.DateTime, comment='最后计算时间')
    status = db.Column(db.String(20), default='active', comment='状态：active/inactive')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    warehouse = db.relationship('WarehouseV3', backref='inventory_optimizations')
    part = db.relationship('SparePart', backref='inventory_optimizations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'warehouse_id': self.warehouse_id,
            'part_id': self.part_id,
            'target_service_level': float(self.target_service_level) if self.target_service_level else 0,
            'holding_cost_rate': float(self.holding_cost_rate) if self.holding_cost_rate else None,
            'ordering_cost': float(self.ordering_cost) if self.ordering_cost else None,
            'eoq': float(self.eoq) if self.eoq else None,
            'safety_stock': float(self.safety_stock) if self.safety_stock else None,
            'reorder_point': float(self.reorder_point) if self.reorder_point else None,
            'max_stock': float(self.max_stock) if self.max_stock else None,
            'demand_variability': float(self.demand_variability) if self.demand_variability else None,
            'lead_time_variability': float(self.lead_time_variability) if self.lead_time_variability else None,
            'last_calculated_at': self.last_calculated_at.strftime('%Y-%m-%d %H:%M:%S') if self.last_calculated_at else None,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
