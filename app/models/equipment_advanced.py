"""
设备管理高级功能模型
包含IoT数据采集、预测性维护、设备健康指数等现代工业4.0标准功能
"""
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import JSON, Index


class EquipmentHealthIndex(db.Model):
    """设备健康指数模型 - 工业4.0核心功能"""
    __tablename__ = 'equipment_health_index'
    __table_args__ = (
        Index('idx_eq_health_equipment_date', 'equipment_id', 'record_date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)

    # 综合健康评分（0-100）
    health_score = db.Column(db.Numeric(5, 2), nullable=False, comment='综合健康评分')
    reliability_score = db.Column(db.Numeric(5, 2), comment='可靠性评分')
    performance_score = db.Column(db.Numeric(5, 2), comment='性能评分')
    maintenance_score = db.Column(db.Numeric(5, 2), comment='维护状况评分')

    # 健康等级
    health_level = db.Column(db.String(20), comment='健康等级: excellent/good/normal/warning/critical')

    # 风险评估
    risk_level = db.Column(db.String(20), comment='风险等级: low/medium/high/critical')
    risk_score = db.Column(db.Numeric(5, 2), comment='风险评分')

    # 预测性指标
    mtbf_prediction = db.Column(db.Integer, comment='预测MTBF（小时）')
    rul_prediction = db.Column(db.Integer, comment='剩余使用寿命（天）')
    failure_risk = db.Column(db.Numeric(5, 2), comment='故障风险概率')

    # 记录时间
    record_date = db.Column(db.Date, nullable=False, default=datetime.now().date)
    record_time = db.Column(db.DateTime, default=datetime.now)

    # 备注
    remarks = db.Column(db.Text, comment='健康分析备注')

    # 关系
    equipment = db.relationship('Equipment', backref='health_records')

    def __repr__(self):
        return f'<EquipmentHealth {self.equipment_id} {self.health_score}>'

    @staticmethod
    def calculate_health_score(equipment):
        """基于历史数据计算设备健康评分"""
        from app.models.maintenance import MaintenanceOrder
        import math

        # 获取设备相关数据
        total_maintenances = MaintenanceOrder.query.filter_by(equipment_id=equipment.id).count()
        completed_maintenances = MaintenanceOrder.query.filter_by(
            equipment_id=equipment.id,
            status='completed'
        ).count()

        # 基础计算
        base_score = 80.0
        maintenance_rate = (completed_maintenances / max(total_maintenances, 1)) * 100

        # 根据状态调整
        status_adjustments = {
            'running': 0,
            'stopped': -10,
            'maintenance': -20,
            'scrapped': -50
        }

        base_score += status_adjustments.get(equipment.status, 0)
        base_score = max(0, min(100, base_score))

        # 返回评分
        return round(base_score, 2)


class EquipmentIotData(db.Model):
    """设备IoT数据采集模型 - 实时监控"""
    __tablename__ = 'equipment_iot_data'
    __table_args__ = (
        Index('idx_iot_equipment_timestamp', 'equipment_id', 'timestamp'),
    )

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)

    # 设备运行状态
    is_running = db.Column(db.Boolean, default=False, comment='是否正在运行')
    uptime_hours = db.Column(db.Numeric(10, 2), comment='运行时长（小时）')

    # 性能指标
    voltage = db.Column(db.Numeric(10, 2), comment='电压（V）')
    current = db.Column(db.Numeric(10, 2), comment='电流（A）')
    temperature = db.Column(db.Numeric(10, 2), comment='温度（°C）')
    pressure = db.Column(db.Numeric(10, 2), comment='压力（MPa）')
    vibration = db.Column(db.Numeric(10, 2), comment='振动值（mm/s）')

    # 射线源指标
    radiation_power = db.Column(db.Numeric(10, 2), comment='射线源功率（kW）')
    radiation_on_time = db.Column(db.Numeric(10, 2), comment='射线照射时间（秒）')

    # 检测量统计
    today_scans = db.Column(db.Integer, default=0, comment='今日检测次数')
    today_images = db.Column(db.Integer, default=0, comment='今日成像数')
    total_scans = db.Column(db.BigInteger, default=0, comment='累计检测次数')

    # 告警状态
    has_alarms = db.Column(db.Boolean, default=False, comment='是否有告警')
    alarm_count = db.Column(db.Integer, default=0, comment='告警数量')

    # 数据质量
    data_quality = db.Column(db.String(20), default='good', comment='数据质量: good/warning/bad')

    # 时间戳
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 原始JSON数据
    raw_data = db.Column(db.JSON, comment='原始IoT数据')

    # 关系
    equipment = db.relationship('Equipment', backref='iot_data')

    def __repr__(self):
        return f'<EquipmentIotData {self.equipment_id} {self.timestamp}>'


class EquipmentPredictiveMaintenance(db.Model):
    """预测性维护模型 - 工业4.0预测分析"""
    __tablename__ = 'equipment_predictive_maintenance'
    __table_args__ = (
        Index('idx_pred_eq_date', 'equipment_id', 'prediction_date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)

    # 预测类型
    prediction_type = db.Column(db.String(50), nullable=False, comment='预测类型: failure/performance/maintenance')

    # 预测内容
    predicted_failure_date = db.Column(db.Date, comment='预测故障日期')
    predicted_maintenance_date = db.Column(db.Date, comment='预测维护日期')

    # 预测指标
    confidence_level = db.Column(db.Numeric(5, 2), comment='置信度（0-100）')
    priority = db.Column(db.String(20), comment='优先级: low/medium/high/critical')

    # 分析详情
    failure_probability = db.Column(db.Numeric(5, 2), comment='故障概率')
    predicted_component = db.Column(db.String(200), comment='预测故障部件')
    failure_symptoms = db.Column(db.Text, comment='故障症状')
    recommendations = db.Column(db.Text, comment='维护建议')

    # AI模型信息
    model_version = db.Column(db.String(50), comment='预测模型版本')
    model_type = db.Column(db.String(50), comment='模型类型: ml/rule-based/hybrid')

    # 时间
    prediction_date = db.Column(db.Date, nullable=False, default=datetime.now().date)
    created_at = db.Column(db.DateTime, default=datetime.now)
    acknowledged = db.Column(db.Boolean, default=False, comment='是否已确认')
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    acknowledged_at = db.Column(db.DateTime)

    # 关系
    equipment = db.relationship('Equipment', backref='predictive_maintenances')

    def __repr__(self):
        return f'<EquipmentPredictive {self.id} {self.prediction_type}>'


class EquipmentPerformanceMetric(db.Model):
    """设备性能指标模型 - OEE等KPI"""
    __tablename__ = 'equipment_performance_metric'
    __table_args__ = (
        Index('idx_perf_eq_date_type', 'equipment_id', 'period_date', 'metric_type'),
    )

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)

    # 指标类型
    metric_type = db.Column(db.String(50), nullable=False, comment='指标类型: daily/weekly/monthly')
    period_date = db.Column(db.Date, nullable=False)

    # OEE指标
    oee_score = db.Column(db.Numeric(5, 2), comment='整体设备效率OEE')
    availability_rate = db.Column(db.Numeric(5, 2), comment='可用率')
    performance_rate = db.Column(db.Numeric(5, 2), comment='性能率')
    quality_rate = db.Column(db.Numeric(5, 2), comment='合格率')

    # 运行统计
    planned_uptime = db.Column(db.Numeric(10, 2), comment='计划运行时间（小时）')
    actual_uptime = db.Column(db.Numeric(10, 2), comment='实际运行时间（小时）')
    downtime = db.Column(db.Numeric(10, 2), comment='停机时间（小时）')
    maintenance_time = db.Column(db.Numeric(10, 2), comment='维护时间（小时）')

    # 检测统计
    total_scans = db.Column(db.Integer, default=0, comment='总检测次数')
    successful_scans = db.Column(db.Integer, default=0, comment='成功检测次数')
    rejected_scans = db.Column(db.Integer, default=0, comment='拒检次数')

    # 质量指标
    defect_rate = db.Column(db.Numeric(5, 2), comment='缺陷率')
    false_alarm_rate = db.Column(db.Numeric(5, 2), comment='误报率')

    # 能效指标
    energy_consumption = db.Column(db.Numeric(10, 2), comment='能耗（kWh）')
    energy_efficiency = db.Column(db.Numeric(5, 2), comment='能效评分')

    # 成本
    maintenance_cost = db.Column(db.Numeric(15, 2), comment='维护成本')
    operating_cost = db.Column(db.Numeric(15, 2), comment='运营成本')
    total_cost = db.Column(db.Numeric(15, 2), comment='总成本')

    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关系
    equipment = db.relationship('Equipment', backref='performance_metrics')

    def __repr__(self):
        return f'<EquipmentPerformance {self.equipment_id} {self.metric_type}>'

    @staticmethod
    def calculate_oee(availability, performance, quality):
        """计算OEE: OEE = Availability × Performance × Quality"""
        if availability is None or performance is None or quality is None:
            return None
        return round((availability / 100) * (performance / 100) * (quality / 100) * 100, 2)


class EquipmentComponent(db.Model):
    """设备组件/备件关联模型"""
    __tablename__ = 'equipment_component'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    spare_part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'), nullable=False)

    # 组件信息
    component_name = db.Column(db.String(200), comment='组件名称')
    component_type = db.Column(db.String(50), comment='组件类型: critical/important/standard')
    installation_position = db.Column(db.String(200), comment='安装位置')

    # 生命周期管理
    installation_date = db.Column(db.Date, comment='安装日期')
    replacement_cycle = db.Column(db.Integer, comment='更换周期（天）')
    expected_lifetime = db.Column(db.Integer, comment='预期寿命（小时）')
    usage_hours = db.Column(db.Numeric(10, 2), default=0, comment='已使用小时数')

    # 状态
    status = db.Column(db.String(20), default='normal', comment='状态: normal/warning/needs_replacement')
    last_maintenance_date = db.Column(db.Date, comment='上次维护日期')
    next_replacement_date = db.Column(db.Date, comment='下次更换日期')

    # 关联数量
    quantity_required = db.Column(db.Integer, default=1, comment='所需数量')
    quantity_installed = db.Column(db.Integer, default=1, comment='已安装数量')

    # 备注
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    equipment = db.relationship('Equipment', backref='components')
    spare_part = db.relationship('SparePart', backref='equipment_components')

    def __repr__(self):
        return f'<EquipmentComponent {self.equipment_id} {self.component_name}>'


class EquipmentMaintenanceTask(db.Model):
    """设备维护任务 - 工单系统增强"""
    __tablename__ = 'equipment_maintenance_task'
    __table_args__ = (
        Index('idx_task_eq_status_date', 'equipment_id', 'status', 'scheduled_date'),
    )

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    maintenance_order_id = db.Column(db.Integer, db.ForeignKey('maintenance_order.id'))

    # 任务基本信息
    task_name = db.Column(db.String(200), nullable=False)
    task_code = db.Column(db.String(50), unique=True, comment='任务编号')
    task_type = db.Column(db.String(50), nullable=False, comment='任务类型: preventive/corrective/inspection/calibration/upgrade')
    priority = db.Column(db.String(20), default='medium', comment='优先级: low/medium/high/critical')

    # 时间安排
    scheduled_date = db.Column(db.Date, comment='计划日期')
    scheduled_time = db.Column(db.Time, comment='计划时间')
    estimated_duration = db.Column(db.Numeric(5, 1), comment='预估时长（小时）')
    actual_start_date = db.Column(db.DateTime, comment='实际开始时间')
    actual_end_date = db.Column(db.DateTime, comment='实际结束时间')

    # 状态管理
    status = db.Column(db.String(20), default='pending', comment='状态: pending/in_progress/completed/cancelled/overdue')
    progress = db.Column(db.Integer, default=0, comment='进度（0-100）')

    # 负责人员
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), comment='分配给用户')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    # 任务内容
    description = db.Column(db.Text, comment='任务描述')
    check_list = db.Column(db.JSON, comment='检查清单')
    required_tools = db.Column(db.JSON, comment='所需工具')
    required_parts = db.Column(db.JSON, comment='所需备件')

    # 结果记录
    result = db.Column(db.Text, comment='执行结果')
    findings = db.Column(db.Text, comment='发现的问题')
    recommendations = db.Column(db.Text, comment='后续建议')

    # 成本
    material_cost = db.Column(db.Numeric(15, 2), comment='材料成本')
    labor_cost = db.Column(db.Numeric(15, 2), comment='人工成本')
    total_cost = db.Column(db.Numeric(15, 2), comment='总成本')

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    equipment = db.relationship('Equipment', backref='equipment_tasks')
    maintenance_order = db.relationship('MaintenanceOrder', backref='equipment_task_list')

    def __repr__(self):
        return f'<EquipmentMaintenanceTask {self.task_code}>'


class EquipmentDocument(db.Model):
    """设备文档/知识库管理"""
    __tablename__ = 'equipment_document'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)

    # 文档信息
    document_type = db.Column(db.String(50), nullable=False, comment='文档类型: manual/drawing/spec/procedure/maintenance_record')
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    version = db.Column(db.String(50), default='1.0', comment='文档版本')

    # 文件信息
    file_name = db.Column(db.String(500))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.BigInteger)
    file_type = db.Column(db.String(50))
    file_url = db.Column(db.String(500), comment='文件访问URL')

    # 分类标签
    category = db.Column(db.String(100), comment='文档分类')
    tags = db.Column(db.JSON, comment='标签数组')

    # 状态
    is_active = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=False, comment='是否公开')

    # 审核流程
    review_status = db.Column(db.String(20), default='draft', comment='审核状态: draft/reviewed/approved')
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    approved_at = db.Column(db.DateTime)

    # 元数据
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    download_count = db.Column(db.Integer, default=0, comment='下载次数')

    # 关系
    equipment = db.relationship('Equipment', backref='documents')

    def __repr__(self):
        return f'<EquipmentDocument {self.id} {self.title}>'
