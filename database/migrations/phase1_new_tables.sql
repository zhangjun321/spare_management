-- ============================================================
-- Phase 1 数据库迁移：调拨单 / 库存预留 / 盘点任务 / 批次策略
-- 执行环境: spare_parts_db (MySQL)
-- 兼容性: 纯新增表/字段，不影响现有数据和业务
-- 创建时间: 2026-05-21
-- ============================================================

START TRANSACTION;

-- ══════════════════════════════════════════
-- 1. 调拨单系统
-- ══════════════════════════════════════════

-- 1.1 调拨单主表
CREATE TABLE IF NOT EXISTS `transfer_order` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `order_code` VARCHAR(50) NOT NULL COMMENT '调拨单号(TO前缀)',
    `from_warehouse_id` INT NOT NULL COMMENT '调出仓库ID',
    `to_warehouse_id` INT NOT NULL COMMENT '调入仓库ID',
    `status` VARCHAR(20) DEFAULT 'draft' COMMENT 'draft/submitted/approved/in_transit/received/completed/cancelled',
    `requester_id` INT COMMENT '申请人ID',
    `approver_id` INT COMMENT '审批人ID',
    `shipper_id` INT COMMENT '发货人ID',
    `receiver_id` INT COMMENT '收货人ID',
    `remark` TEXT COMMENT '备注',
    `eta` DATETIME COMMENT '预计到达时间',
    `submitted_at` DATETIME COMMENT '提交时间',
    `approved_at` DATETIME COMMENT '审批时间',
    `shipped_at` DATETIME COMMENT '发货时间',
    `received_at` DATETIME COMMENT '收货时间',
    `completed_at` DATETIME COMMENT '完成时间',
    `cancelled_at` DATETIME COMMENT '取消时间',
    `cancel_reason` TEXT COMMENT '取消原因',
    `cancelled_by` INT COMMENT '取消人ID',
    `version` INT DEFAULT 1 COMMENT '乐观锁版本号',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_order_code` (`order_code`),
    KEY `idx_from_warehouse` (`from_warehouse_id`),
    KEY `idx_to_warehouse` (`to_warehouse_id`),
    KEY `idx_status` (`status`),
    KEY `idx_created_at` (`created_at`),
    CONSTRAINT `fk_to_from_wh` FOREIGN KEY (`from_warehouse_id`) REFERENCES `warehouse`(`id`),
    CONSTRAINT `fk_to_to_wh` FOREIGN KEY (`to_warehouse_id`) REFERENCES `warehouse`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='调拨单主表';

-- 1.2 调拨单明细
CREATE TABLE IF NOT EXISTS `transfer_order_item` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `transfer_id` INT NOT NULL COMMENT '调拨单ID',
    `spare_part_id` INT NOT NULL COMMENT '备件ID',
    `quantity` DECIMAL(10,2) NOT NULL COMMENT '调拨数量',
    `batch_no` VARCHAR(100) COMMENT '批次号',
    `item_status` VARCHAR(20) DEFAULT 'pending' COMMENT 'pending/shipped/received',
    `shipped_quantity` DECIMAL(10,2) DEFAULT 0 COMMENT '已发数量',
    `received_quantity` DECIMAL(10,2) DEFAULT 0 COMMENT '已收数量',
    `remark` TEXT COMMENT '备注',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_transfer_id` (`transfer_id`),
    KEY `idx_spare_part_id` (`spare_part_id`),
    CONSTRAINT `fk_toi_transfer` FOREIGN KEY (`transfer_id`) REFERENCES `transfer_order`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_toi_spare_part` FOREIGN KEY (`spare_part_id`) REFERENCES `spare_part`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='调拨单明细';


-- ══════════════════════════════════════════
-- 2. 库存预留系统
-- ══════════════════════════════════════════

CREATE TABLE IF NOT EXISTS `reservation` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `reservation_code` VARCHAR(50) NOT NULL COMMENT '预留编号(RS前缀)',
    `spare_part_id` INT NOT NULL COMMENT '备件ID',
    `warehouse_id` INT COMMENT '仓库ID(可选,为空则全局预留)',
    `quantity` DECIMAL(10,2) NOT NULL COMMENT '预留数量',
    `released_quantity` DECIMAL(10,2) DEFAULT 0 COMMENT '已释放数量',
    `project` VARCHAR(200) COMMENT '项目名称/编号',
    `order_ref` VARCHAR(100) COMMENT '关联订单号',
    `reason` TEXT COMMENT '预留原因',
    `priority` INT DEFAULT 5 COMMENT '优先级1-10',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT 'active/released/expired/consumed',
    `expire_at` DATETIME NOT NULL COMMENT '到期时间',
    `released_at` DATETIME COMMENT '释放时间',
    `released_by` INT COMMENT '释放人ID',
    `consumed_at` DATETIME COMMENT '消费时间',
    `version` INT DEFAULT 1 COMMENT '乐观锁版本号',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `created_by` INT COMMENT '创建人ID',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_reservation_code` (`reservation_code`),
    KEY `idx_spare_part_id` (`spare_part_id`),
    KEY `idx_warehouse_id` (`warehouse_id`),
    KEY `idx_status` (`status`),
    KEY `idx_expire_at` (`expire_at`),
    CONSTRAINT `fk_res_spare_part` FOREIGN KEY (`spare_part_id`) REFERENCES `spare_part`(`id`),
    CONSTRAINT `fk_res_warehouse` FOREIGN KEY (`warehouse_id`) REFERENCES `warehouse`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存预留';


-- ══════════════════════════════════════════
-- 3. 盘点任务系统
-- ══════════════════════════════════════════

-- 3.1 盘点任务
CREATE TABLE IF NOT EXISTS `stock_take_task` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `task_code` VARCHAR(50) NOT NULL COMMENT '盘点编号(ST前缀)',
    `title` VARCHAR(200) NOT NULL COMMENT '任务标题',
    `scope_type` VARCHAR(20) DEFAULT 'warehouse' COMMENT 'warehouse/area/category/manual',
    `scope_value` VARCHAR(200) COMMENT '范围值',
    `warehouse_id` INT COMMENT '仓库ID',
    `status` VARCHAR(20) DEFAULT 'draft' COMMENT 'draft/in_progress/pending_review/completed/cancelled',
    `assignee_ids` VARCHAR(500) COMMENT '盘点人员ID(逗号分隔)',
    `assignee_names` VARCHAR(500) COMMENT '盘点人员姓名',
    `planner_id` INT COMMENT '计划人ID',
    `deadline` DATETIME COMMENT '截止时间',
    `total_items` INT DEFAULT 0 COMMENT '盘点项总数',
    `counted_items` INT DEFAULT 0 COMMENT '已盘点项数',
    `diff_items` INT DEFAULT 0 COMMENT '差异项数',
    `approval_required` TINYINT(1) DEFAULT 1 COMMENT '差异是否需要审批',
    `remark` TEXT COMMENT '备注',
    `version` INT DEFAULT 1 COMMENT '乐观锁版本号',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `started_at` DATETIME COMMENT '开始时间',
    `completed_at` DATETIME COMMENT '完成时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_task_code` (`task_code`),
    KEY `idx_warehouse_id` (`warehouse_id`),
    KEY `idx_status` (`status`),
    KEY `idx_created_at` (`created_at`),
    CONSTRAINT `fk_stt_warehouse` FOREIGN KEY (`warehouse_id`) REFERENCES `warehouse`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='盘点任务';

-- 3.2 盘点明细
CREATE TABLE IF NOT EXISTS `stock_take_item` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `task_id` INT NOT NULL COMMENT '盘点任务ID',
    `spare_part_id` INT NOT NULL COMMENT '备件ID',
    `batch_no` VARCHAR(100) COMMENT '批次号',
    `location_id` INT COMMENT '库位ID',
    `system_qty` DECIMAL(10,2) COMMENT '系统数量',
    `counted_qty` DECIMAL(10,2) COMMENT '盘点数量',
    `diff_qty` DECIMAL(10,2) COMMENT '差异数量',
    `item_status` VARCHAR(20) DEFAULT 'pending' COMMENT 'pending/counted/reconciled',
    `counted_by` INT COMMENT '盘点人ID',
    `counted_at` DATETIME COMMENT '盘点时间',
    `scan_code` VARCHAR(200) COMMENT '扫码编码',
    `remark` TEXT COMMENT '备注',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_task_id` (`task_id`),
    KEY `idx_spare_part_id` (`spare_part_id`),
    KEY `idx_item_status` (`item_status`),
    CONSTRAINT `fk_sti_task` FOREIGN KEY (`task_id`) REFERENCES `stock_take_task`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_sti_spare_part` FOREIGN KEY (`spare_part_id`) REFERENCES `spare_part`(`id`),
    CONSTRAINT `fk_sti_location` FOREIGN KEY (`location_id`) REFERENCES `warehouse_location`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='盘点明细';

-- 3.3 差异调整单
CREATE TABLE IF NOT EXISTS `adjustment_order` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `adjust_code` VARCHAR(50) NOT NULL COMMENT '调整编号(AD前缀)',
    `task_id` INT NOT NULL COMMENT '盘点任务ID',
    `stock_take_item_id` INT COMMENT '盘点明细ID',
    `spare_part_id` INT NOT NULL COMMENT '备件ID',
    `warehouse_id` INT COMMENT '仓库ID',
    `adjust_type` VARCHAR(20) NOT NULL COMMENT 'gain(盘盈)/loss(盘亏)/damage(破损)',
    `adjust_qty` DECIMAL(10,2) NOT NULL COMMENT '调整数量',
    `reason` TEXT COMMENT '调整原因',
    `status` VARCHAR(20) DEFAULT 'draft' COMMENT 'draft/submitted/approved/applied/rejected',
    `submitted_by` INT COMMENT '提交人ID',
    `approved_by` INT COMMENT '审批人ID',
    `submitted_at` DATETIME COMMENT '提交时间',
    `approved_at` DATETIME COMMENT '审批时间',
    `applied_at` DATETIME COMMENT '执行时间',
    `reject_reason` TEXT COMMENT '驳回原因',
    `version` INT DEFAULT 1 COMMENT '乐观锁版本号',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_adjust_code` (`adjust_code`),
    KEY `idx_task_id` (`task_id`),
    KEY `idx_spare_part_id` (`spare_part_id`),
    KEY `idx_status` (`status`),
    CONSTRAINT `fk_ao_task` FOREIGN KEY (`task_id`) REFERENCES `stock_take_task`(`id`),
    CONSTRAINT `fk_ao_spare_part` FOREIGN KEY (`spare_part_id`) REFERENCES `spare_part`(`id`),
    CONSTRAINT `fk_ao_warehouse` FOREIGN KEY (`warehouse_id`) REFERENCES `warehouse`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='差异调整单';


-- ══════════════════════════════════════════
-- 4. 批次策略字段（扩展现有表）
-- ══════════════════════════════════════════

-- 仓库表增加拣货策略字段
ALTER TABLE `warehouse`
    ADD COLUMN IF NOT EXISTS `picking_strategy` VARCHAR(20) DEFAULT 'fifo'
    COMMENT '拣货策略: fifo(先进先出)/fefo(先到期先出)/manual(手动)';

-- 备件表增加有效期相关字段（如果不存在）
ALTER TABLE `spare_part`
    ADD COLUMN IF NOT EXISTS `expiry_days` INT DEFAULT NULL
    COMMENT '有效期天数(NULL=无有效期)';

ALTER TABLE `spare_part`
    ADD COLUMN IF NOT EXISTS `near_expiry_days` INT DEFAULT 30
    COMMENT '近效期预警天数';

COMMIT;

-- ============================================================
-- 验证查询（可选执行）
-- ============================================================
-- SHOW TABLES LIKE 'transfer_order%';
-- SHOW TABLES LIKE 'reservation%';
-- SHOW TABLES LIKE 'stock_take%';
-- SHOW TABLES LIKE 'adjustment_order%';
-- SHOW COLUMNS FROM warehouse LIKE 'picking_strategy';
-- SHOW COLUMNS FROM spare_part LIKE '%expiry%';
