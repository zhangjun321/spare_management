from app.extensions import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ==================== 功能1：智能预测与补货模型 ====================

class SparePartDemandPrediction(db.Model):
    """备件需求预测记录"""
    __tablename__ = 'spare_part_demand_prediction'
    
    id = db.Column(db.Integer, primary_key=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件ID')
    prediction_date = db.Column(db.DateTime, nullable=False, comment='预测日期')
    start_date = db.Column(db.Date, nullable=False, comment='预测开始日期')
    end_date = db.Column(db.Date, nullable=False, comment='预测结束日期')
    predicted_quantity = db.Column(db.Numeric(10, 2), nullable=False, comment='预测数量')
    actual_quantity = db.Column(db.Numeric(10, 2), comment='实际数量')
    prediction_accuracy = db.Column(db.Numeric(5, 2), comment='预测准确率')
    prediction_method = db.Column(db.String(50), default='ai', comment='预测方法：ai(AI), moving_average(移动平均), exponential(指数平滑)')
    model_version = db.Column(db.String(50), comment='模型版本')
    confidence = db.Column(db.Numeric(5, 2), default=0.8, comment='置信度')
    status = db.Column(db.String(20), default='active', comment='状态：active, archived')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人ID')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'spare_part_id': self.spare_part_id,
            'spare_part_code': self.spare_part.part_code if self.spare_part else None,
            'spare_part_name': self.spare_part.name if self.spare_part else None,
            'prediction_date': self.prediction_date.strftime('%Y-%m-%d %H:%M:%S') if self.prediction_date else None,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'predicted_quantity': float(self.predicted_quantity) if self.predicted_quantity else None,
            'actual_quantity': float(self.actual_quantity) if self.actual_quantity else None,
            'prediction_accuracy': float(self.prediction_accuracy) if self.prediction_accuracy else None,
            'prediction_method': self.prediction_method,
            'confidence': float(self.confidence) if self.confidence else None,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartReplenishmentSuggestion(db.Model):
    """备件补货建议"""
    __tablename__ = 'spare_part_replenishment_suggestion'
    
    id = db.Column(db.Integer, primary_key=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件ID')
    suggestion_date = db.Column(db.DateTime, default=datetime.utcnow, comment='建议日期')
    suggested_quantity = db.Column(db.Numeric(10, 2), nullable=False, comment='建议补货数量')
    priority = db.Column(db.Integer, default=5, comment='优先级：1-10，越高越紧急')
    priority_level = db.Column(db.String(20), default='medium', comment='优先级等级：critical, high, medium, low')
    reason = db.Column(db.Text, comment='建议理由')
    reason_code = db.Column(db.String(50), comment='理由代码：low_stock, high_demand, maintenance, seasonality')
    eoq = db.Column(db.Numeric(10, 2), comment='经济订货量EOQ')
    safety_stock = db.Column(db.Numeric(10, 2), comment='安全库存')
    estimated_cost = db.Column(db.Numeric(12, 2), comment='预估成本')
    suggested_supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), comment='建议供应商')
    status = db.Column(db.String(20), default='pending', comment='状态：pending, approved, rejected, implemented')
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='审批人ID')
    approved_at = db.Column(db.DateTime, comment='审批时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人ID')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    suggested_supplier = db.relationship('Supplier', foreign_keys=[suggested_supplier_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'spare_part_id': self.spare_part_id,
            'spare_part_code': self.spare_part.part_code if self.spare_part else None,
            'spare_part_name': self.spare_part.name if self.spare_part else None,
            'suggestion_date': self.suggestion_date.strftime('%Y-%m-%d %H:%M:%S') if self.suggestion_date else None,
            'suggested_quantity': float(self.suggested_quantity) if self.suggested_quantity else None,
            'priority': self.priority,
            'priority_level': self.priority_level,
            'reason': self.reason,
            'reason_code': self.reason_code,
            'eoq': float(self.eoq) if self.eoq else None,
            'safety_stock': float(self.safety_stock) if self.safety_stock else None,
            'estimated_cost': float(self.estimated_cost) if self.estimated_cost else None,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartReplenishmentOrder(db.Model):
    """补货申请单"""
    __tablename__ = 'spare_part_replenishment_order'
    
    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='补货单号')
    suggestion_id = db.Column(db.Integer, db.ForeignKey('spare_part_replenishment_suggestion.id'), comment='关联建议ID')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件ID')
    quantity = db.Column(db.Numeric(10, 2), nullable=False, comment='补货数量')
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), comment='供应商ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), comment='入库仓库')
    expected_date = db.Column(db.Date, comment='期望到货日期')
    status = db.Column(db.String(20), default='draft', comment='状态：draft, submitted, approved, ordered, received, cancelled')
    priority = db.Column(db.Integer, default=5, comment='优先级')
    remark = db.Column(db.Text, comment='备注')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    supplier = db.relationship('Supplier', foreign_keys=[supplier_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_code': self.order_code,
            'spare_part_id': self.spare_part_id,
            'quantity': float(self.quantity) if self.quantity else None,
            'status': self.status,
            'priority': self.priority,
            'expected_date': self.expected_date.strftime('%Y-%m-%d') if self.expected_date else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


# ==================== 功能2：备件质量管理模型 ====================

class SparePartQualityInspection(db.Model):
    """备件质量检验记录"""
    __tablename__ = 'spare_part_quality_inspection'
    
    id = db.Column(db.Integer, primary_key=True)
    inspection_code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='检验单号')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件ID')
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), comment='批次ID')
    inspection_type = db.Column(db.String(20), default='incoming', comment='检验类型：incoming(入库), outgoing(出库), periodic(定期)')
    inspection_date = db.Column(db.DateTime, default=datetime.utcnow, comment='检验日期')
    inspector_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='检验人ID')
    sample_quantity = db.Column(db.Integer, comment='抽样数量')
    inspected_quantity = db.Column(db.Integer, comment='已检数量')
    passed_quantity = db.Column(db.Integer, comment='合格数量')
    failed_quantity = db.Column(db.Integer, comment='不合格数量')
    inspection_result = db.Column(db.String(20), default='pending', comment='检验结果：pending, passed, failed, conditional')
    quality_score = db.Column(db.Numeric(5, 2), comment='质量评分0-100')
    defect_count = db.Column(db.Integer, default=0, comment='缺陷数量')
    defect_details = db.Column(db.JSON, comment='缺陷详情')
    image_urls = db.Column(db.JSON, comment='检验图片URL')
    remark = db.Column(db.Text, comment='备注')
    ai_inspection = db.Column(db.Boolean, default=False, comment='是否AI辅助检验')
    ai_confidence = db.Column(db.Numeric(5, 2), comment='AI置信度')
    ai_analysis = db.Column(db.JSON, comment='AI分析结果')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'inspection_code': self.inspection_code,
            'spare_part_id': self.spare_part_id,
            'spare_part_code': self.spare_part.part_code if self.spare_part else None,
            'inspection_type': self.inspection_type,
            'inspection_date': self.inspection_date.strftime('%Y-%m-%d %H:%M:%S') if self.inspection_date else None,
            'inspection_result': self.inspection_result,
            'quality_score': float(self.quality_score) if self.quality_score else None,
            'passed_quantity': self.passed_quantity,
            'failed_quantity': self.failed_quantity,
            'ai_inspection': self.ai_inspection,
            'defect_count': self.defect_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartDefectRecord(db.Model):
    """缺陷记录"""
    __tablename__ = 'spare_part_defect_record'
    
    id = db.Column(db.Integer, primary_key=True)
    defect_code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='缺陷编号')
    inspection_id = db.Column(db.Integer, db.ForeignKey('spare_part_quality_inspection.id'), comment='关联检验ID')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), index=True, comment='备件ID')
    defect_type = db.Column(db.String(50), nullable=False, comment='缺陷类型')
    defect_category = db.Column(db.String(50), comment='缺陷分类')
    severity = db.Column(db.String(20), default='medium', comment='严重程度：low, medium, high, critical')
    description = db.Column(db.Text, comment='缺陷描述')
    image_url = db.Column(db.String(500), comment='缺陷图片URL')
    ai_detected = db.Column(db.Boolean, default=False, comment='是否AI检测')
    ai_confidence = db.Column(db.Numeric(5, 2), comment='AI置信度')
    position = db.Column(db.String(200), comment='缺陷位置')
    disposition = db.Column(db.String(20), comment='处理方式：repair, scrap, use_as_is, return')
    status = db.Column(db.String(20), default='open', comment='状态：open, in_progress, resolved, closed')
    resolved_at = db.Column(db.DateTime, comment='解决时间')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人ID')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'defect_code': self.defect_code,
            'spare_part_id': self.spare_part_id,
            'defect_type': self.defect_type,
            'severity': self.severity,
            'description': self.description,
            'ai_detected': self.ai_detected,
            'status': self.status,
            'disposition': self.disposition,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartQualityStandard(db.Model):
    """质量标准"""
    __tablename__ = 'spare_part_quality_standard'
    
    id = db.Column(db.Integer, primary_key=True)
    standard_code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='标准编号')
    name = db.Column(db.String(200), nullable=False, comment='标准名称')
    description = db.Column(db.Text, comment='标准描述')
    version = db.Column(db.String(20), default='1.0', comment='版本')
    criteria = db.Column(db.JSON, comment='检验标准')
    passing_score = db.Column(db.Numeric(5, 2), default=80.0, comment='合格分数')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    effective_date = db.Column(db.Date, comment='生效日期')
    expiry_date = db.Column(db.Date, comment='失效日期')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人ID')
    
    def to_dict(self):
        return {
            'id': self.id,
            'standard_code': self.standard_code,
            'name': self.name,
            'version': self.version,
            'passing_score': float(self.passing_score) if self.passing_score else None,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


# ==================== 功能3：故障诊断与维护模型 ====================

class SparePartFaultRecord(db.Model):
    """故障记录"""
    __tablename__ = 'spare_part_fault_record'
    
    id = db.Column(db.Integer, primary_key=True)
    fault_code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='故障编号')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件ID')
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), index=True, comment='设备ID')
    fault_type = db.Column(db.String(100), nullable=False, comment='故障类型')
    fault_category = db.Column(db.String(100), comment='故障分类')
    fault_description = db.Column(db.Text, comment='故障描述')
    fault_symptoms = db.Column(db.JSON, comment='故障症状')
    fault_time = db.Column(db.DateTime, default=datetime.utcnow, comment='故障发生时间')
    reported_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='报告人ID')
    severity = db.Column(db.String(20), default='medium', comment='严重程度：low, medium, high, critical')
    priority = db.Column(db.Integer, default=5, comment='优先级1-10')
    downtime_hours = db.Column(db.Numeric(8, 2), comment='停机时间(小时)')
    status = db.Column(db.String(20), default='open', comment='状态：open, in_progress, resolved, closed')
    ai_diagnosis = db.Column(db.Boolean, default=False, comment='是否AI诊断')
    ai_confidence = db.Column(db.Numeric(5, 2), comment='AI置信度')
    ai_analysis = db.Column(db.JSON, comment='AI分析结果')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    resolved_at = db.Column(db.DateTime, comment='解决时间')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    equipment = db.relationship('Equipment', foreign_keys=[equipment_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'fault_code': self.fault_code,
            'spare_part_id': self.spare_part_id,
            'spare_part_code': self.spare_part.part_code if self.spare_part else None,
            'spare_part_name': self.spare_part.name if self.spare_part else None,
            'equipment_id': self.equipment_id,
            'fault_type': self.fault_type,
            'severity': self.severity,
            'priority': self.priority,
            'status': self.status,
            'ai_diagnosis': self.ai_diagnosis,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartDiagnosis(db.Model):
    """诊断结果"""
    __tablename__ = 'spare_part_diagnosis'
    
    id = db.Column(db.Integer, primary_key=True)
    fault_id = db.Column(db.Integer, db.ForeignKey('spare_part_fault_record.id'), nullable=False, index=True, comment='故障记录ID')
    diagnosis_date = db.Column(db.DateTime, default=datetime.utcnow, comment='诊断日期')
    diagnostic_method = db.Column(db.String(20), default='manual', comment='诊断方式：manual, ai, hybrid')
    root_cause = db.Column(db.String(500), comment='根本原因')
    root_cause_code = db.Column(db.String(50), comment='根因代码')
    possible_causes = db.Column(db.JSON, comment='可能原因列表')
    confidence = db.Column(db.Numeric(5, 2), default=0.8, comment='置信度')
    diagnosis_result = db.Column(db.Text, comment='诊断结论')
    diagnostic_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='诊断人ID')
    ai_recommendation_id = db.Column(db.Integer, comment='AI推荐ID')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'fault_id': self.fault_id,
            'diagnosis_date': self.diagnosis_date.strftime('%Y-%m-%d %H:%M:%S') if self.diagnosis_date else None,
            'diagnostic_method': self.diagnostic_method,
            'root_cause': self.root_cause,
            'confidence': float(self.confidence) if self.confidence else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartMaintenanceSolution(db.Model):
    """维护方案"""
    __tablename__ = 'spare_part_maintenance_solution'
    
    id = db.Column(db.Integer, primary_key=True)
    solution_code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='方案编号')
    name = db.Column(db.String(200), nullable=False, comment='方案名称')
    description = db.Column(db.Text, comment='方案描述')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), index=True, comment='适用备件ID')
    fault_type = db.Column(db.String(100), comment='适用故障类型')
    solution_type = db.Column(db.String(20), default='repair', comment='方案类型：repair, replace, preventive')
    steps = db.Column(db.JSON, comment='操作步骤')
    required_tools = db.Column(db.JSON, comment='所需工具')
    estimated_time_hours = db.Column(db.Numeric(5, 2), comment='预估时间(小时)')
    estimated_cost = db.Column(db.Numeric(12, 2), comment='预估成本')
    success_rate = db.Column(db.Numeric(5, 2), comment='成功率')
    usage_count = db.Column(db.Integer, default=0, comment='使用次数')
    rating = db.Column(db.Numeric(3, 2), comment='评分')
    is_ai_recommended = db.Column(db.Boolean, default=False, comment='是否AI推荐')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人ID')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'solution_code': self.solution_code,
            'name': self.name,
            'solution_type': self.solution_type,
            'estimated_time_hours': float(self.estimated_time_hours) if self.estimated_time_hours else None,
            'estimated_cost': float(self.estimated_cost) if self.estimated_cost else None,
            'success_rate': float(self.success_rate) if self.success_rate else None,
            'is_ai_recommended': self.is_ai_recommended,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartFMEARecord(db.Model):
    """FMEA失效模式分析记录"""
    __tablename__ = 'spare_part_fmea_record'
    
    id = db.Column(db.Integer, primary_key=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件ID')
    failure_mode = db.Column(db.String(200), nullable=False, comment='失效模式')
    failure_effect = db.Column(db.Text, comment='失效影响')
    failure_cause = db.Column(db.Text, comment='失效原因')
    severity = db.Column(db.Integer, default=5, comment='严重度1-10')
    occurrence = db.Column(db.Integer, default=5, comment='发生频度1-10')
    detection = db.Column(db.Integer, default=5, comment='探测度1-10')
    rpn = db.Column(db.Integer, comment='风险优先级数(RPN=S×O×D)')
    recommended_actions = db.Column(db.Text, comment='建议措施')
    status = db.Column(db.String(20), default='open', comment='状态：open, in_progress, mitigated, closed')
    ai_analysis = db.Column(db.JSON, comment='AI分析')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'spare_part_id': self.spare_part_id,
            'failure_mode': self.failure_mode,
            'severity': self.severity,
            'occurrence': self.occurrence,
            'detection': self.detection,
            'rpn': self.rpn,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
    
    def calculate_rpn(self):
        """计算风险优先级数"""
        self.rpn = (self.severity or 5) * (self.occurrence or 5) * (self.detection or 5)


# ==================== 功能4：生命周期管理模型 ====================

class SparePartLifecycleStage(db.Model):
    """生命周期阶段定义"""
    __tablename__ = 'spare_part_lifecycle_stage'
    
    id = db.Column(db.Integer, primary_key=True)
    stage_code = db.Column(db.String(50), unique=True, nullable=False, comment='阶段代码')
    stage_name = db.Column(db.String(100), nullable=False, comment='阶段名称')
    description = db.Column(db.Text, comment='阶段描述')
    icon = db.Column(db.String(50), comment='图标类名')
    color = db.Column(db.String(50), comment='阶段颜色')
    sort_order = db.Column(db.Integer, default=0, comment='排序序号')
    auto_transition = db.Column(db.Boolean, default=False, comment='是否自动流转')
    transition_condition = db.Column(db.JSON, comment='流转条件配置')
    default_duration_days = db.Column(db.Integer, comment='默认持续天数')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'stage_code': self.stage_code,
            'stage_name': self.stage_name,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'sort_order': self.sort_order,
            'auto_transition': self.auto_transition,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartLifecycleTransition(db.Model):
    """生命周期阶段流转记录"""
    __tablename__ = 'spare_part_lifecycle_transition'
    
    id = db.Column(db.Integer, primary_key=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件ID')
    from_stage = db.Column(db.String(50), comment='起始阶段')
    to_stage = db.Column(db.String(50), nullable=False, comment='目标阶段')
    transition_date = db.Column(db.DateTime, default=datetime.utcnow, comment='流转时间')
    triggered_by = db.Column(db.String(20), default='manual', comment='触发方式：manual, auto, ai, rule')
    trigger_condition = db.Column(db.Text, comment='触发条件')
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='操作人ID')
    duration_days = db.Column(db.Integer, comment='上一阶段持续天数')
    remark = db.Column(db.Text, comment='流转说明')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'spare_part_id': self.spare_part_id,
            'from_stage': self.from_stage,
            'to_stage': self.to_stage,
            'transition_date': self.transition_date.strftime('%Y-%m-%d %H:%M:%S') if self.transition_date else None,
            'triggered_by': self.triggered_by,
            'duration_days': self.duration_days,
            'remark': self.remark,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartLifecycleLog(db.Model):
    """生命周期日志"""
    __tablename__ = 'spare_part_lifecycle_log'
    
    id = db.Column(db.Integer, primary_key=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件ID')
    log_type = db.Column(db.String(50), nullable=False, comment='日志类型：stage_change, status_change, maintenance, inspection, alert')
    action = db.Column(db.String(100), nullable=False, comment='操作动作')
    stage = db.Column(db.String(50), comment='当前阶段')
    status = db.Column(db.String(20), comment='当前状态')
    old_value = db.Column(db.Text, comment='旧值')
    new_value = db.Column(db.Text, comment='新值')
    detail = db.Column(db.JSON, comment='详细信息')
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='操作人ID')
    ip_address = db.Column(db.String(50), comment='IP地址')
    user_agent = db.Column(db.String(500), comment='用户代理')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'spare_part_id': self.spare_part_id,
            'log_type': self.log_type,
            'action': self.action,
            'stage': self.stage,
            'status': self.status,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'operator_id': self.operator_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartLifecycleRule(db.Model):
    """生命周期规则"""
    __tablename__ = 'spare_part_lifecycle_rule'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_code = db.Column(db.String(50), unique=True, nullable=False, comment='规则代码')
    rule_name = db.Column(db.String(200), nullable=False, comment='规则名称')
    rule_type = db.Column(db.String(50), default='stage_transition', comment='规则类型：stage_transition, alert, maintenance')
    description = db.Column(db.Text, comment='规则描述')
    condition = db.Column(db.JSON, comment='触发条件')
    action = db.Column(db.JSON, comment='执行动作')
    priority = db.Column(db.Integer, default=5, comment='优先级')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    is_auto_execute = db.Column(db.Boolean, default=False, comment='是否自动执行')
    trigger_count = db.Column(db.Integer, default=0, comment='触发次数')
    last_triggered = db.Column(db.DateTime, comment='最后触发时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='创建人ID')
    
    def to_dict(self):
        return {
            'id': self.id,
            'rule_code': self.rule_code,
            'rule_name': self.rule_name,
            'rule_type': self.rule_type,
            'description': self.description,
            'condition': self.condition,
            'action': self.action,
            'priority': self.priority,
            'is_active': self.is_active,
            'is_auto_execute': self.is_auto_execute,
            'trigger_count': self.trigger_count,
            'last_triggered': self.last_triggered.strftime('%Y-%m-%d %H:%M:%S') if self.last_triggered else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartLifecycleRecord(db.Model):
    """生命周期记录"""
    __tablename__ = 'spare_part_lifecycle_record'
    
    id = db.Column(db.Integer, primary_key=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件ID')
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), comment='批次ID')
    serial_number_id = db.Column(db.Integer, db.ForeignKey('serial_number.id'), comment='序列号ID')
    lifecycle_stage = db.Column(db.String(20), default='warehouse', comment='生命周期阶段：warehouse, in_use, maintenance, retired')
    stage_start_date = db.Column(db.DateTime, default=datetime.utcnow, comment='阶段开始时间')
    stage_end_date = db.Column(db.DateTime, comment='阶段结束时间')
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location.id'), comment='位置ID')
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), comment='安装设备ID')
    cost = db.Column(db.Numeric(12, 2), comment='阶段成本')
    usage_hours = db.Column(db.Numeric(10, 2), comment='使用小时数')
    cycle_count = db.Column(db.Integer, comment='循环次数')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'spare_part_id': self.spare_part_id,
            'lifecycle_stage': self.lifecycle_stage,
            'stage_start_date': self.stage_start_date.strftime('%Y-%m-%d %H:%M:%S') if self.stage_start_date else None,
            'stage_end_date': self.stage_end_date.strftime('%Y-%m-%d %H:%M:%S') if self.stage_end_date else None,
            'cost': float(self.cost) if self.cost else None,
            'usage_hours': float(self.usage_hours) if self.usage_hours else None,
            'cycle_count': self.cycle_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartUsageHistory(db.Model):
    """使用历史"""
    __tablename__ = 'spare_part_usage_history'
    
    id = db.Column(db.Integer, primary_key=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件ID')
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), comment='使用设备ID')
    usage_type = db.Column(db.String(20), default='replacement', comment='使用类型：replacement, backup, maintenance')
    install_date = db.Column(db.DateTime, comment='安装日期')
    remove_date = db.Column(db.DateTime, comment='移除日期')
    usage_hours = db.Column(db.Numeric(10, 2), comment='使用小时数')
    operating_conditions = db.Column(db.JSON, comment='运行条件')
    performance_data = db.Column(db.JSON, comment='性能数据')
    reason_for_removal = db.Column(db.Text, comment='移除原因')
    condition_at_removal = db.Column(db.String(50), comment='移除时状况')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'spare_part_id': self.spare_part_id,
            'usage_type': self.usage_type,
            'install_date': self.install_date.strftime('%Y-%m-%d %H:%M:%S') if self.install_date else None,
            'remove_date': self.remove_date.strftime('%Y-%m-%d %H:%M:%S') if self.remove_date else None,
            'usage_hours': float(self.usage_hours) if self.usage_hours else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartReplacementSchedule(db.Model):
    """更换计划"""
    __tablename__ = 'spare_part_replacement_schedule'
    
    id = db.Column(db.Integer, primary_key=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件ID')
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), comment='设备ID')
    planned_replacement_date = db.Column(db.Date, comment='计划更换日期')
    predicted_failure_date = db.Column(db.Date, comment='预测失效日期')
    urgency = db.Column(db.String(20), default='normal', comment='紧急程度：low, normal, high, urgent')
    reason = db.Column(db.Text, comment='更换原因')
    recommendation_source = db.Column(db.String(20), default='manual', comment='建议来源：manual, ai, preventive')
    ai_confidence = db.Column(db.Numeric(5, 2), comment='AI置信度')
    status = db.Column(db.String(20), default='planned', comment='状态：planned, in_progress, completed, cancelled')
    actual_replacement_date = db.Column(db.Date, comment='实际更换日期')
    remark = db.Column(db.Text, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'spare_part_id': self.spare_part_id,
            'planned_replacement_date': self.planned_replacement_date.strftime('%Y-%m-%d') if self.planned_replacement_date else None,
            'predicted_failure_date': self.predicted_failure_date.strftime('%Y-%m-%d') if self.predicted_failure_date else None,
            'urgency': self.urgency,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartLifecycleCost(db.Model):
    """生命周期成本"""
    __tablename__ = 'spare_part_lifecycle_cost'
    
    id = db.Column(db.Integer, primary_key=True)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False, index=True, comment='备件ID')
    cost_type = db.Column(db.String(20), nullable=False, comment='成本类型：purchase, maintenance, replacement, downtime, disposal')
    amount = db.Column(db.Numeric(12, 2), nullable=False, comment='金额')
    currency = db.Column(db.String(10), default='CNY', comment='币种')
    cost_date = db.Column(db.DateTime, default=datetime.utcnow, comment='成本日期')
    description = db.Column(db.Text, comment='成本描述')
    related_record_id = db.Column(db.Integer, comment='关联记录ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'spare_part_id': self.spare_part_id,
            'cost_type': self.cost_type,
            'amount': float(self.amount) if self.amount else None,
            'cost_date': self.cost_date.strftime('%Y-%m-%d %H:%M:%S') if self.cost_date else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


# ==================== 功能5：综合分析驾驶舱模型 ====================

class SparePartKPI(db.Model):
    """KPI记录"""
    __tablename__ = 'spare_part_kpi'
    
    id = db.Column(db.Integer, primary_key=True)
    kpi_code = db.Column(db.String(50), nullable=False, index=True, comment='KPI代码')
    kpi_name = db.Column(db.String(200), nullable=False, comment='KPI名称')
    period_type = db.Column(db.String(20), default='daily', comment='统计周期：daily, weekly, monthly, quarterly')
    period_start = db.Column(db.Date, nullable=False, comment='周期开始')
    period_end = db.Column(db.Date, nullable=False, comment='周期结束')
    value = db.Column(db.Numeric(12, 2), nullable=False, comment='KPI值')
    target_value = db.Column(db.Numeric(12, 2), comment='目标值')
    unit = db.Column(db.String(20), comment='单位')
    trend = db.Column(db.String(20), comment='趋势：up, down, stable')
    status = db.Column(db.String(20), default='normal', comment='状态：excellent, good, normal, warning, critical')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'kpi_code': self.kpi_code,
            'kpi_name': self.kpi_name,
            'period_type': self.period_type,
            'value': float(self.value) if self.value else None,
            'target_value': float(self.target_value) if self.target_value else None,
            'trend': self.trend,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartAnomalyRecord(db.Model):
    """异常记录"""
    __tablename__ = 'spare_part_anomaly_record'
    
    id = db.Column(db.Integer, primary_key=True)
    anomaly_code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='异常编号')
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), index=True, comment='备件ID')
    anomaly_type = db.Column(db.String(50), nullable=False, comment='异常类型')
    anomaly_description = db.Column(db.Text, comment='异常描述')
    detected_at = db.Column(db.DateTime, default=datetime.utcnow, comment='检测时间')
    detected_by = db.Column(db.String(20), default='system', comment='检测方式：system, ai, manual')
    ai_confidence = db.Column(db.Numeric(5, 2), comment='AI置信度')
    severity = db.Column(db.String(20), default='medium', comment='严重程度')
    status = db.Column(db.String(20), default='open', comment='状态：open, investigating, resolved, closed')
    resolved_at = db.Column(db.DateTime, comment='解决时间')
    resolution = db.Column(db.Text, comment='解决方案')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    spare_part = db.relationship('SparePart', foreign_keys=[spare_part_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'anomaly_code': self.anomaly_code,
            'anomaly_type': self.anomaly_type,
            'severity': self.severity,
            'status': self.status,
            'detected_at': self.detected_at.strftime('%Y-%m-%d %H:%M:%S') if self.detected_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SparePartReport(db.Model):
    """智能报告"""
    __tablename__ = 'spare_part_report'
    
    id = db.Column(db.Integer, primary_key=True)
    report_code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='报告编号')
    report_type = db.Column(db.String(20), nullable=False, comment='报告类型：daily, weekly, monthly, adhoc')
    title = db.Column(db.String(200), nullable=False, comment='报告标题')
    content = db.Column(db.Text, comment='报告内容')
    data_summary = db.Column(db.JSON, comment='数据摘要')
    recommendations = db.Column(db.JSON, comment='AI建议')
    generated_by = db.Column(db.String(20), default='system', comment='生成方式：system, ai, manual')
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, comment='生成时间')
    report_period_start = db.Column(db.Date, comment='报告周期开始')
    report_period_end = db.Column(db.Date, comment='报告周期结束')
    file_url = db.Column(db.String(500), comment='报告文件URL')
    is_ai_generated = db.Column(db.Boolean, default=True, comment='是否AI生成')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'report_code': self.report_code,
            'report_type': self.report_type,
            'title': self.title,
            'content': self.content,
            'generated_by': self.generated_by,
            'generated_at': self.generated_at.strftime('%Y-%m-%d %H:%M:%S') if self.generated_at else None,
            'is_ai_generated': self.is_ai_generated,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
