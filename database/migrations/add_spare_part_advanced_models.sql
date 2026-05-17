-- ========================================
-- 备件管理模块高级功能数据库迁移脚本
-- 基于ISO 14224、TPM、RCM标准
-- ========================================

-- ========================================
-- 功能1：智能预测与补货相关表
-- ========================================

CREATE TABLE IF NOT EXISTS spare_part_demand_prediction (
    id INT PRIMARY KEY AUTO_INCREMENT,
    spare_part_id INT NOT NULL COMMENT '备件ID',
    prediction_date DATETIME NOT NULL COMMENT '预测日期',
    start_date DATE NOT NULL COMMENT '预测开始日期',
    end_date DATE NOT NULL COMMENT '预测结束日期',
    predicted_quantity DECIMAL(10, 2) NOT NULL COMMENT '预测数量',
    actual_quantity DECIMAL(10, 2) COMMENT '实际数量',
    prediction_accuracy DECIMAL(5, 2) COMMENT '预测准确率',
    prediction_method VARCHAR(50) DEFAULT 'ai' COMMENT '预测方法',
    model_version VARCHAR(50) COMMENT '模型版本',
    confidence DECIMAL(5, 2) DEFAULT 0.8 COMMENT '置信度',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by INT COMMENT '创建人ID',
    INDEX idx_spare_part (spare_part_id),
    INDEX idx_prediction_date (prediction_date),
    INDEX idx_status (status),
    FOREIGN KEY (spare_part_id) REFERENCES spare_part(id),
    FOREIGN KEY (created_by) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='备件需求预测记录';

CREATE TABLE IF NOT EXISTS spare_part_replenishment_suggestion (
    id INT PRIMARY KEY AUTO_INCREMENT,
    spare_part_id INT NOT NULL COMMENT '备件ID',
    suggestion_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '建议日期',
    suggested_quantity DECIMAL(10, 2) NOT NULL COMMENT '建议补货数量',
    priority INT DEFAULT 5 COMMENT '优先级',
    priority_level VARCHAR(20) DEFAULT 'medium' COMMENT '优先级等级',
    reason TEXT COMMENT '建议理由',
    reason_code VARCHAR(50) COMMENT '理由代码',
    eoq DECIMAL(10, 2) COMMENT '经济订货量',
    safety_stock DECIMAL(10, 2) COMMENT '安全库存',
    estimated_cost DECIMAL(12, 2) COMMENT '预估成本',
    suggested_supplier_id INT COMMENT '建议供应商',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态',
    approved_by INT COMMENT '审批人ID',
    approved_at DATETIME COMMENT '审批时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    created_by INT COMMENT '创建人ID',
    INDEX idx_spare_part (spare_part_id),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    FOREIGN KEY (spare_part_id) REFERENCES spare_part(id),
    FOREIGN KEY (suggested_supplier_id) REFERENCES supplier(id),
    FOREIGN KEY (created_by) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='备件补货建议';

CREATE TABLE IF NOT EXISTS spare_part_replenishment_order (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_code VARCHAR(50) UNIQUE NOT NULL COMMENT '补货单号',
    suggestion_id INT COMMENT '关联建议ID',
    spare_part_id INT NOT NULL COMMENT '备件ID',
    quantity DECIMAL(10, 2) NOT NULL COMMENT '补货数量',
    supplier_id INT COMMENT '供应商ID',
    warehouse_id INT COMMENT '入库仓库',
    expected_date DATE COMMENT '期望到货日期',
    status VARCHAR(20) DEFAULT 'draft' COMMENT '状态',
    priority INT DEFAULT 5 COMMENT '优先级',
    remark TEXT COMMENT '备注',
    created_by INT COMMENT '创建人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_spare_part (spare_part_id),
    INDEX idx_order_code (order_code),
    INDEX idx_status (status),
    FOREIGN KEY (suggestion_id) REFERENCES spare_part_replenishment_suggestion(id),
    FOREIGN KEY (spare_part_id) REFERENCES spare_part(id),
    FOREIGN KEY (supplier_id) REFERENCES supplier(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouse(id),
    FOREIGN KEY (created_by) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='补货申请单';

-- ========================================
-- 功能2：备件质量管理相关表
-- ========================================

CREATE TABLE IF NOT EXISTS spare_part_quality_inspection (
    id INT PRIMARY KEY AUTO_INCREMENT,
    inspection_code VARCHAR(50) UNIQUE NOT NULL COMMENT '检验单号',
    spare_part_id INT NOT NULL COMMENT '备件ID',
    batch_id INT COMMENT '批次ID',
    inspection_type VARCHAR(20) DEFAULT 'incoming' COMMENT '检验类型',
    inspection_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '检验日期',
    inspector_id INT COMMENT '检验人ID',
    sample_quantity INT COMMENT '抽样数量',
    inspected_quantity INT COMMENT '已检数量',
    passed_quantity INT COMMENT '合格数量',
    failed_quantity INT COMMENT '不合格数量',
    inspection_result VARCHAR(20) DEFAULT 'pending' COMMENT '检验结果',
    quality_score DECIMAL(5, 2) COMMENT '质量评分',
    defect_count INT DEFAULT 0 COMMENT '缺陷数量',
    defect_details JSON COMMENT '缺陷详情',
    image_urls JSON COMMENT '检验图片URL',
    remark TEXT COMMENT '备注',
    ai_inspection BOOLEAN DEFAULT FALSE COMMENT '是否AI辅助检验',
    ai_confidence DECIMAL(5, 2) COMMENT 'AI置信度',
    ai_analysis JSON COMMENT 'AI分析结果',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_spare_part (spare_part_id),
    INDEX idx_inspection_date (inspection_date),
    INDEX idx_result (inspection_result),
    FOREIGN KEY (spare_part_id) REFERENCES spare_part(id),
    FOREIGN KEY (batch_id) REFERENCES batch(id),
    FOREIGN KEY (inspector_id) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='备件质量检验记录';

CREATE TABLE IF NOT EXISTS spare_part_defect_record (
    id INT PRIMARY KEY AUTO_INCREMENT,
    defect_code VARCHAR(50) UNIQUE NOT NULL COMMENT '缺陷编号',
    inspection_id INT COMMENT '关联检验ID',
    spare_part_id INT NOT NULL COMMENT '备件ID',
    defect_type VARCHAR(50) NOT NULL COMMENT '缺陷类型',
    defect_category VARCHAR(50) COMMENT '缺陷分类',
    severity VARCHAR(20) DEFAULT 'medium' COMMENT '严重程度',
    description TEXT COMMENT '缺陷描述',
    image_url VARCHAR(500) COMMENT '缺陷图片URL',
    ai_detected BOOLEAN DEFAULT FALSE COMMENT '是否AI检测',
    ai_confidence DECIMAL(5, 2) COMMENT 'AI置信度',
    position VARCHAR(200) COMMENT '缺陷位置',
    disposition VARCHAR(20) COMMENT '处理方式',
    status VARCHAR(20) DEFAULT 'open' COMMENT '状态',
    resolved_at DATETIME COMMENT '解决时间',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    created_by INT COMMENT '创建人ID',
    INDEX idx_spare_part (spare_part_id),
    INDEX idx_severity (severity),
    INDEX idx_status (status),
    FOREIGN KEY (inspection_id) REFERENCES spare_part_quality_inspection(id),
    FOREIGN KEY (spare_part_id) REFERENCES spare_part(id),
    FOREIGN KEY (created_by) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='缺陷记录';

CREATE TABLE IF NOT EXISTS spare_part_quality_standard (
    id INT PRIMARY KEY AUTO_INCREMENT,
    standard_code VARCHAR(50) UNIQUE NOT NULL COMMENT '标准编号',
    name VARCHAR(200) NOT NULL COMMENT '标准名称',
    description TEXT COMMENT '标准描述',
    version VARCHAR(20) DEFAULT '1.0' COMMENT '版本',
    criteria JSON COMMENT '检验标准',
    passing_score DECIMAL(5, 2) DEFAULT 80.0 COMMENT '合格分数',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    effective_date DATE COMMENT '生效日期',
    expiry_date DATE COMMENT '失效日期',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    created_by INT COMMENT '创建人ID',
    INDEX idx_standard_code (standard_code),
    INDEX idx_is_active (is_active),
    FOREIGN KEY (created_by) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='质量标准';

-- ========================================
-- 功能3：故障诊断与维护相关表
-- ========================================

CREATE TABLE IF NOT EXISTS spare_part_fault_record (
    id INT PRIMARY KEY AUTO_INCREMENT,
    fault_code VARCHAR(50) UNIQUE NOT NULL COMMENT '故障编号',
    spare_part_id INT NOT NULL COMMENT '备件ID',
    equipment_id INT COMMENT '设备ID',
    fault_type VARCHAR(100) NOT NULL COMMENT '故障类型',
    fault_category VARCHAR(100) COMMENT '故障分类',
    fault_description TEXT COMMENT '故障描述',
    fault_symptoms JSON COMMENT '故障症状',
    fault_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '故障发生时间',
    reported_by INT COMMENT '报告人ID',
    severity VARCHAR(20) DEFAULT 'medium' COMMENT '严重程度',
    priority INT DEFAULT 5 COMMENT '优先级',
    downtime_hours DECIMAL(8, 2) COMMENT '停机时间',
    status VARCHAR(20) DEFAULT 'open' COMMENT '状态',
    ai_diagnosis BOOLEAN DEFAULT FALSE COMMENT '是否AI诊断',
    ai_confidence DECIMAL(5, 2) COMMENT 'AI置信度',
    ai_analysis JSON COMMENT 'AI分析结果',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    resolved_at DATETIME COMMENT '解决时间',
    INDEX idx_spare_part (spare_part_id),
    INDEX idx_fault_time (fault_time),
    INDEX idx_severity (severity),
    INDEX idx_status (status),
    FOREIGN KEY (spare_part_id) REFERENCES spare_part(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (reported_by) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='故障记录';

CREATE TABLE IF NOT EXISTS spare_part_diagnosis (
    id INT PRIMARY KEY AUTO_INCREMENT,
    fault_id INT NOT NULL COMMENT '故障记录ID',
    diagnosis_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '诊断日期',
    diagnostic_method VARCHAR(20) DEFAULT 'manual' COMMENT '诊断方式',
    root_cause VARCHAR(500) COMMENT '根本原因',
    root_cause_code VARCHAR(50) COMMENT '根因代码',
    possible_causes JSON COMMENT '可能原因列表',
    confidence DECIMAL(5, 2) DEFAULT 0.8 COMMENT '置信度',
    diagnosis_result TEXT COMMENT '诊断结论',
    diagnostic_by INT COMMENT '诊断人ID',
    ai_recommendation_id INT COMMENT 'AI推荐ID',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_fault_id (fault_id),
    FOREIGN KEY (fault_id) REFERENCES spare_part_fault_record(id),
    FOREIGN KEY (diagnostic_by) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='诊断结果';

CREATE TABLE IF NOT EXISTS spare_part_maintenance_solution (
    id INT PRIMARY KEY AUTO_INCREMENT,
    solution_code VARCHAR(50) UNIQUE NOT NULL COMMENT '方案编号',
    name VARCHAR(200) NOT NULL COMMENT '方案名称',
    description TEXT COMMENT '方案描述',
    spare_part_id INT COMMENT '适用备件ID',
    fault_type VARCHAR(100) COMMENT '适用故障类型',
    solution_type VARCHAR(20) DEFAULT 'repair' COMMENT '方案类型',
    steps JSON COMMENT '操作步骤',
    required_tools JSON COMMENT '所需工具',
    estimated_time_hours DECIMAL(5, 2) COMMENT '预估时间',
    estimated_cost DECIMAL(12, 2) COMMENT '预估成本',
    success_rate DECIMAL(5, 2) COMMENT '成功率',
    usage_count INT DEFAULT 0 COMMENT '使用次数',
    rating DECIMAL(3, 2) COMMENT '评分',
    is_ai_recommended BOOLEAN DEFAULT FALSE COMMENT '是否AI推荐',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    created_by INT COMMENT '创建人ID',
    INDEX idx_spare_part (spare_part_id),
    INDEX idx_solution_type (solution_type),
    FOREIGN KEY (spare_part_id) REFERENCES spare_part(id),
    FOREIGN KEY (created_by) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='维护方案';

CREATE TABLE IF NOT EXISTS spare_part_fmea_record (
    id INT PRIMARY KEY AUTO_INCREMENT,
    spare_part_id INT NOT NULL COMMENT '备件ID',
    failure_mode VARCHAR(200) NOT NULL COMMENT '失效模式',
    failure_effect TEXT COMMENT '失效影响',
    failure_cause TEXT COMMENT '失效原因',
    severity INT DEFAULT 5 COMMENT '严重度',
    occurrence INT DEFAULT 5 COMMENT '发生频度',
    detection INT DEFAULT 5 COMMENT '探测度',
    rpn INT COMMENT '风险优先级数',
    recommended_actions TEXT COMMENT '建议措施',
    status VARCHAR(20) DEFAULT 'open' COMMENT '状态',
    ai_analysis JSON COMMENT 'AI分析',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_spare_part (spare_part_id),
    INDEX idx_rpn (rpn),
    INDEX idx_status (status),
    FOREIGN KEY (spare_part_id) REFERENCES spare_part(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='FMEA失效模式分析记录';

-- ========================================
-- 功能4：生命周期管理相关表
-- ========================================

CREATE TABLE IF NOT EXISTS spare_part_lifecycle_record (
    id INT PRIMARY KEY AUTO_INCREMENT,
    spare_part_id INT NOT NULL COMMENT '备件ID',
    batch_id INT COMMENT '批次ID',
    serial_number_id INT COMMENT '序列号ID',
    lifecycle_stage VARCHAR(20) DEFAULT 'warehouse' COMMENT '生命周期阶段',
    stage_start_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '阶段开始时间',
    stage_end_date DATETIME COMMENT '阶段结束时间',
    location_id INT COMMENT '位置ID',
    equipment_id INT COMMENT '安装设备ID',
    cost DECIMAL(12, 2) COMMENT '阶段成本',
    usage_hours DECIMAL(10, 2) COMMENT '使用小时数',
    cycle_count INT COMMENT '循环次数',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_spare_part (spare_part_id),
    INDEX idx_stage (lifecycle_stage),
    FOREIGN KEY (spare_part_id) REFERENCES spare_part(id),
    FOREIGN KEY (batch_id) REFERENCES batch(id),
    FOREIGN KEY (location_id) REFERENCES warehouse_location(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='生命周期记录';

CREATE TABLE IF NOT EXISTS spare_part_usage_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    spare_part_id INT NOT NULL COMMENT '备件ID',
    equipment_id INT COMMENT '使用设备ID',
    usage_type VARCHAR(20) DEFAULT 'replacement' COMMENT '使用类型',
    install_date DATETIME COMMENT '安装日期',
    remove_date DATETIME COMMENT '移除日期',
    usage_hours DECIMAL(10, 2) COMMENT '使用小时数',
    operating_conditions JSON COMMENT '运行条件',
    performance_data JSON COMMENT '性能数据',
    reason_for_removal TEXT COMMENT '移除原因',
    condition_at_removal VARCHAR(50) COMMENT '移除时状况',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_spare_part (spare_part_id),
    INDEX idx_equipment (equipment_id),
    FOREIGN KEY (spare_part_id) REFERENCES spare_part(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='使用历史';

CREATE TABLE IF NOT EXISTS spare_part_replacement_schedule (
    id INT PRIMARY KEY AUTO_INCREMENT,
    spare_part_id INT NOT NULL COMMENT '备件ID',
    equipment_id INT COMMENT '设备ID',
    planned_replacement_date DATE COMMENT '计划更换日期',
    predicted_failure_date DATE COMMENT '预测失效日期',
    urgency VARCHAR(20) DEFAULT 'normal' COMMENT '紧急程度',
    reason TEXT COMMENT '更换原因',
    recommendation_source VARCHAR(20) DEFAULT 'manual' COMMENT '建议来源',
    ai_confidence DECIMAL(5, 2) COMMENT 'AI置信度',
    status VARCHAR(20) DEFAULT 'planned' COMMENT '状态',
    actual_replacement_date DATE COMMENT '实际更换日期',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_spare_part (spare_part_id),
    INDEX idx_planned_date (planned_replacement_date),
    INDEX idx_status (status),
    FOREIGN KEY (spare_part_id) REFERENCES spare_part(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='更换计划';

CREATE TABLE IF NOT EXISTS spare_part_lifecycle_cost (
    id INT PRIMARY KEY AUTO_INCREMENT,
    spare_part_id INT NOT NULL COMMENT '备件ID',
    cost_type VARCHAR(20) NOT NULL COMMENT '成本类型',
    amount DECIMAL(12, 2) NOT NULL COMMENT '金额',
    currency VARCHAR(10) DEFAULT 'CNY' COMMENT '币种',
    cost_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '成本日期',
    description TEXT COMMENT '成本描述',
    related_record_id INT COMMENT '关联记录ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_spare_part (spare_part_id),
    INDEX idx_cost_type (cost_type),
    INDEX idx_cost_date (cost_date),
    FOREIGN KEY (spare_part_id) REFERENCES spare_part(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='生命周期成本';

-- ========================================
-- 功能5：综合分析驾驶舱相关表
-- ========================================

CREATE TABLE IF NOT EXISTS spare_part_kpi (
    id INT PRIMARY KEY AUTO_INCREMENT,
    kpi_code VARCHAR(50) NOT NULL COMMENT 'KPI代码',
    kpi_name VARCHAR(200) NOT NULL COMMENT 'KPI名称',
    period_type VARCHAR(20) DEFAULT 'daily' COMMENT '统计周期',
    period_start DATE NOT NULL COMMENT '周期开始',
    period_end DATE NOT NULL COMMENT '周期结束',
    value DECIMAL(12, 2) NOT NULL COMMENT 'KPI值',
    target_value DECIMAL(12, 2) COMMENT '目标值',
    unit VARCHAR(20) COMMENT '单位',
    trend VARCHAR(20) COMMENT '趋势',
    status VARCHAR(20) DEFAULT 'normal' COMMENT '状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_kpi_code (kpi_code),
    INDEX idx_period (period_type, period_start),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='KPI记录';

CREATE TABLE IF NOT EXISTS spare_part_anomaly_record (
    id INT PRIMARY KEY AUTO_INCREMENT,
    anomaly_code VARCHAR(50) UNIQUE NOT NULL COMMENT '异常编号',
    spare_part_id INT COMMENT '备件ID',
    anomaly_type VARCHAR(50) NOT NULL COMMENT '异常类型',
    anomaly_description TEXT COMMENT '异常描述',
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '检测时间',
    detected_by VARCHAR(20) DEFAULT 'system' COMMENT '检测方式',
    ai_confidence DECIMAL(5, 2) COMMENT 'AI置信度',
    severity VARCHAR(20) DEFAULT 'medium' COMMENT '严重程度',
    status VARCHAR(20) DEFAULT 'open' COMMENT '状态',
    resolved_at DATETIME COMMENT '解决时间',
    resolution TEXT COMMENT '解决方案',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_spare_part (spare_part_id),
    INDEX idx_anomaly_type (anomaly_type),
    INDEX idx_severity (severity),
    INDEX idx_status (status),
    FOREIGN KEY (spare_part_id) REFERENCES spare_part(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='异常记录';

CREATE TABLE IF NOT EXISTS spare_part_report (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_code VARCHAR(50) UNIQUE NOT NULL COMMENT '报告编号',
    report_type VARCHAR(20) NOT NULL COMMENT '报告类型',
    title VARCHAR(200) NOT NULL COMMENT '报告标题',
    content TEXT COMMENT '报告内容',
    data_summary JSON COMMENT '数据摘要',
    recommendations JSON COMMENT 'AI建议',
    generated_by VARCHAR(20) DEFAULT 'system' COMMENT '生成方式',
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
    report_period_start DATE COMMENT '报告周期开始',
    report_period_end DATE COMMENT '报告周期结束',
    file_url VARCHAR(500) COMMENT '报告文件URL',
    is_ai_generated BOOLEAN DEFAULT TRUE COMMENT '是否AI生成',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_report_code (report_code),
    INDEX idx_report_type (report_type),
    INDEX idx_generated_at (generated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能报告';

-- ========================================
-- 完成！
-- ========================================

SELECT '备件管理模块高级功能数据库迁移完成！' AS message;
