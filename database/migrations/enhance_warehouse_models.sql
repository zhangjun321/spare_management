-- ========================================
-- 仓库管理模块增强 - 数据库迁移脚本
-- 执行时间：2026-04-10
-- 说明：质检管理模块增强、盘点管理增强准备
-- ========================================

-- 开始事务
START TRANSACTION;

-- ========================================
-- 1. 质检管理模块增强
-- ========================================

-- 1.1 为 quality_check 表添加新字段
ALTER TABLE quality_check 
ADD COLUMN check_type VARCHAR(20) DEFAULT 'inbound' COMMENT '质检类型' AFTER inbound_order_id,
ADD COLUMN check_method VARCHAR(20) DEFAULT 'sampling' COMMENT '质检方式' AFTER inspection_type,
ADD COLUMN sample_ratio DECIMAL(5,2) COMMENT '抽检比例' AFTER check_method,
ADD COLUMN status VARCHAR(20) DEFAULT 'pending' COMMENT '质检状态' AFTER sample_size,
ADD COLUMN pass_rate DECIMAL(5,2) COMMENT '合格率' AFTER unqualified_count,
ADD COLUMN started_at DATETIME COMMENT '开始时间' AFTER inspection_date,
ADD COLUMN started_by INT COMMENT '开始人' AFTER started_at,
ADD COLUMN completed_at DATETIME COMMENT '完成时间' AFTER completed_by,
ADD COLUMN completed_by INT COMMENT '完成人' AFTER completed_at,
ADD COLUMN cancelled_at DATETIME COMMENT '取消时间' AFTER cancelled_by,
ADD COLUMN cancelled_by INT COMMENT '取消人' AFTER cancelled_at,
ADD COLUMN remark TEXT COMMENT '备注' AFTER updated_at;

-- 1.2 为 quality_check_item 表添加新字段
ALTER TABLE quality_check_item
ADD COLUMN expected_quantity DECIMAL(12,4) COMMENT '应检数量' AFTER part_id,
ADD COLUMN unit VARCHAR(20) COMMENT '单位' AFTER unqualified_quantity,
ADD COLUMN status VARCHAR(20) DEFAULT 'pending' COMMENT '状态' AFTER inspected_at,
ADD COLUMN remark TEXT COMMENT '备注' AFTER status;

-- 1.3 创建 quality_check_standard 表（质检标准）
CREATE TABLE IF NOT EXISTS quality_check_standard (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '质检标准 ID',
    part_id INT NOT NULL COMMENT '备件 ID',
    part_code VARCHAR(50) NOT NULL COMMENT '备件编码',
    check_item VARCHAR(100) NOT NULL COMMENT '检验项目',
    check_method VARCHAR(50) COMMENT '检验方法',
    standard_value VARCHAR(100) COMMENT '标准值',
    min_value DECIMAL(12,4) COMMENT '最小值',
    max_value DECIMAL(12,4) COMMENT '最大值',
    unit VARCHAR(20) COMMENT '单位',
    severity_level VARCHAR(20) DEFAULT 'normal' COMMENT '严重程度',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_part_code (part_code),
    INDEX idx_part_id (part_id),
    INDEX idx_check_item (check_item),
    INDEX idx_is_active (is_active),
    
    FOREIGN KEY (part_id) REFERENCES spare_part(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='质检标准表';

-- ========================================
-- 2. 盘点管理模块增强准备
-- ========================================

-- 2.1 为 inventory_check 表添加新字段
ALTER TABLE inventory_check
ADD COLUMN planned_by INT COMMENT '计划人' AFTER checker_id,
ADD COLUMN approved_by INT COMMENT '审批人' AFTER planned_by,
ADD COLUMN approved_at DATETIME COMMENT '审批时间' AFTER approved_by,
ADD COLUMN lock_inventory BOOLEAN DEFAULT TRUE COMMENT '是否锁定库存' AFTER approved_at,
ADD COLUMN report_generated BOOLEAN DEFAULT FALSE COMMENT '是否生成报告' AFTER lock_inventory;

-- 2.2 创建 inventory_check_plan 表（盘点计划）
CREATE TABLE IF NOT EXISTS inventory_check_plan (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '盘点计划 ID',
    plan_no VARCHAR(50) UNIQUE NOT NULL COMMENT '计划编号',
    plan_name VARCHAR(100) NOT NULL COMMENT '计划名称',
    warehouse_id INT NOT NULL COMMENT '仓库 ID',
    check_type VARCHAR(20) NOT NULL COMMENT '盘点类型',
    planned_date DATE NOT NULL COMMENT '计划日期',
    start_date DATE COMMENT '开始日期',
    end_date DATE COMMENT '结束日期',
    scope_type VARCHAR(20) COMMENT '盘点范围类型',
    scope_ids JSON COMMENT '盘点范围 ID 列表',
    status VARCHAR(20) DEFAULT 'draft' COMMENT '计划状态',
    created_by INT COMMENT '创建人',
    approved_by INT COMMENT '审批人',
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_warehouse (warehouse_id),
    INDEX idx_status (status),
    INDEX idx_planned_date (planned_date),
    
    FOREIGN KEY (warehouse_id) REFERENCES warehouse_v3(id),
    FOREIGN KEY (created_by) REFERENCES user(id),
    FOREIGN KEY (approved_by) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='盘点计划表';

-- 2.3 创建 inventory_check_analysis 表（盘点差异分析）
CREATE TABLE IF NOT EXISTS inventory_check_analysis (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '分析 ID',
    check_id INT NOT NULL COMMENT '盘点单 ID',
    part_id INT NOT NULL COMMENT '备件 ID',
    system_quantity DECIMAL(12,4) NOT NULL COMMENT '系统数量',
    actual_quantity DECIMAL(12,4) NOT NULL COMMENT '实际数量',
    difference DECIMAL(12,4) NOT NULL COMMENT '差异数量',
    difference_value DECIMAL(14,2) COMMENT '差异金额',
    difference_rate DECIMAL(8,4) COMMENT '差异率',
    reason_category VARCHAR(50) COMMENT '原因分类',
    reason_description TEXT COMMENT '原因说明',
    responsibility VARCHAR(50) COMMENT '责任部门',
    handling_suggestion TEXT COMMENT '处理建议',
    analyzed_by INT COMMENT '分析人',
    analyzed_at DATETIME COMMENT '分析时间',
    
    INDEX idx_check (check_id),
    INDEX idx_part (part_id),
    INDEX idx_reason_category (reason_category),
    
    FOREIGN KEY (check_id) REFERENCES inventory_check(id),
    FOREIGN KEY (part_id) REFERENCES spare_part(id),
    FOREIGN KEY (analyzed_by) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='盘点差异分析表';

-- ========================================
-- 3. 预警管理模块增强准备
-- ========================================

-- 3.1 为 warning_rule 表添加新字段
ALTER TABLE warning_rule
ADD COLUMN condition_field VARCHAR(50) COMMENT '条件字段' AFTER threshold_value,
ADD COLUMN condition_operator VARCHAR(10) COMMENT '条件运算符' AFTER condition_field,
ADD COLUMN notification_method JSON COMMENT '通知方式' AFTER warning_level;

-- 3.2 为 warning_log 表添加新字段
ALTER TABLE warning_log
ADD COLUMN current_value VARCHAR(50) COMMENT '当前值' AFTER warning_content,
ADD COLUMN threshold_value VARCHAR(50) COMMENT '阈值' AFTER current_value,
ADD COLUMN notification_sent BOOLEAN DEFAULT FALSE COMMENT '是否已通知' AFTER notified_time,
ADD COLUMN is_read BOOLEAN DEFAULT FALSE COMMENT '是否已读' AFTER notification_sent,
ADD COLUMN read_time DATETIME COMMENT '阅读时间' AFTER is_read;

-- 3.3 创建 warning_notification 表（预警通知记录）
CREATE TABLE IF NOT EXISTS warning_notification (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '通知 ID',
    warning_log_id INT NOT NULL COMMENT '预警日志 ID',
    notification_type VARCHAR(20) NOT NULL COMMENT '通知类型',
    recipient VARCHAR(100) COMMENT '接收者',
    content TEXT COMMENT '通知内容',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '通知状态',
    sent_at DATETIME COMMENT '发送时间',
    read_at DATETIME COMMENT '阅读时间',
    
    INDEX idx_warning_log (warning_log_id),
    INDEX idx_status (status),
    INDEX idx_sent_at (sent_at),
    
    FOREIGN KEY (warning_log_id) REFERENCES warning_log(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='预警通知表';

-- ========================================
-- 4. 波次管理模块（新增）
-- ========================================

-- 4.1 创建 picking_wave 表（波次）
CREATE TABLE IF NOT EXISTS picking_wave (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '波次 ID',
    wave_no VARCHAR(50) UNIQUE NOT NULL COMMENT '波次号',
    warehouse_id INT NOT NULL COMMENT '仓库 ID',
    wave_type VARCHAR(20) NOT NULL COMMENT '波次类型',
    status VARCHAR(20) DEFAULT 'created' COMMENT '波次状态',
    priority VARCHAR(20) DEFAULT 'normal' COMMENT '优先级',
    
    -- 关联订单
    order_count INT DEFAULT 0 COMMENT '订单数量',
    order_ids JSON COMMENT '订单 ID 列表',
    
    -- 汇总信息
    total_items INT DEFAULT 0 COMMENT '总品项数',
    total_quantity DECIMAL(12,4) DEFAULT 0 COMMENT '总数量',
    picked_quantity DECIMAL(12,4) DEFAULT 0 COMMENT '已拣数量',
    
    -- 人员信息
    picker_id INT COMMENT '拣货员',
    assigned_at DATETIME COMMENT '分配时间',
    
    -- 时间信息
    started_at DATETIME COMMENT '开始时间',
    completed_at DATETIME COMMENT '完成时间',
    
    -- 路径信息
    picking_path JSON COMMENT '拣货路径',
    
    created_by INT COMMENT '创建人',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_warehouse (warehouse_id),
    INDEX idx_status (status),
    INDEX idx_picker (picker_id),
    INDEX idx_wave_no (wave_no),
    
    FOREIGN KEY (warehouse_id) REFERENCES warehouse_v3(id),
    FOREIGN KEY (picker_id) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='波次表';

-- 4.2 创建 wave_strategy 表（波次策略）
CREATE TABLE IF NOT EXISTS wave_strategy (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '策略 ID',
    strategy_name VARCHAR(100) NOT NULL COMMENT '策略名称',
    warehouse_id INT COMMENT '仓库 ID',
    
    -- 策略规则
    order_type_filter JSON COMMENT '订单类型过滤',
    time_window INT COMMENT '时间窗口（分钟）',
    max_orders INT COMMENT '最大订单数',
    max_items INT COMMENT '最大品项数',
    priority_rule VARCHAR(50) COMMENT '优先级规则',
    
    -- 拣货规则
    picking_strategy VARCHAR(50) COMMENT '拣货策略',
    route_optimization BOOLEAN DEFAULT TRUE COMMENT '路径优化',
    
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (warehouse_id) REFERENCES warehouse_v3(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='波次策略表';

-- ========================================
-- 5. 初始化数据
-- ========================================

-- 5.1 初始化质检标准示例数据
INSERT INTO quality_check_standard (part_id, part_code, check_item, check_method, standard_value, min_value, max_value, unit, severity_level) VALUES
(1, 'SP-001', '外观检查', 'visual', '无划痕、无变形', NULL, NULL, '', 'normal'),
(1, 'SP-001', '尺寸检测', 'measurement', '符合图纸要求', NULL, NULL, 'mm', 'critical'),
(2, 'SP-002', '材质检验', 'material', '304 不锈钢', NULL, NULL, '', 'critical'),
(2, 'SP-002', '硬度测试', 'hardness', 'HRC 30-35', 30, 35, 'HRC', 'major')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 5.2 初始化波次策略示例数据
INSERT INTO wave_strategy (strategy_name, warehouse_id, order_type_filter, time_window, max_orders, max_items, priority_rule, picking_strategy, route_optimization) VALUES
('标准波次策略', 1, '["sales"]', 30, 10, 50, 'first_come_first_served', 'batch_picking', TRUE),
('紧急订单波次', 1, '["sales_urgent"]', 15, 5, 20, 'priority_first', 'single_order', TRUE)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- ========================================
-- 6. 索引优化
-- ========================================

-- 为现有表添加缺失的索引
CREATE INDEX IF NOT EXISTS idx_quality_check_status ON quality_check(status);
CREATE INDEX IF NOT EXISTS idx_quality_check_inbound_order ON quality_check(inbound_order_id);
CREATE INDEX IF NOT EXISTS idx_quality_check_item_check ON quality_check_item(check_id);
CREATE INDEX IF NOT EXISTS idx_inventory_check_warehouse ON inventory_check(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warning_rule_type ON warning_rule(rule_type);
CREATE INDEX IF NOT EXISTS idx_warning_log_created ON warning_log(created_at);

-- 提交事务
COMMIT;

-- ========================================
-- 迁移完成验证
-- ========================================

-- 验证表结构
SELECT 'quality_check_standard' AS table_name, COUNT(*) AS row_count FROM quality_check_standard;
SELECT 'picking_wave' AS table_name, COUNT(*) AS row_count FROM picking_wave;
SELECT 'wave_strategy' AS table_name, COUNT(*) AS row_count FROM wave_strategy;
SELECT 'inventory_check_plan' AS table_name, COUNT(*) AS row_count FROM inventory_check_plan;
SELECT 'inventory_check_analysis' AS table_name, COUNT(*) AS row_count FROM inventory_check_analysis;
SELECT 'warning_notification' AS table_name, COUNT(*) AS row_count FROM warning_notification;

-- 显示迁移结果
SELECT '数据库迁移完成！' AS message;
