-- ============================================
-- 备件管理系统 - 数据库表创建脚本
-- 数据库：spare_parts_db
-- 创建时间：2026-03-18
-- ============================================

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 角色表
-- ============================================
DROP TABLE IF EXISTS `role`;
CREATE TABLE `role` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '角色 ID',
  `name` VARCHAR(50) UNIQUE NOT NULL COMMENT '角色名称',
  `display_name` VARCHAR(100) NOT NULL COMMENT '角色显示名称',
  `description` VARCHAR(500) COMMENT '角色描述',
  `permissions` TEXT COMMENT '权限配置 (JSON)',
  `is_system` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否系统内置角色',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

-- ============================================
-- 2. 部门表
-- ============================================
DROP TABLE IF EXISTS `department`;
CREATE TABLE `department` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '部门 ID',
  `name` VARCHAR(100) NOT NULL COMMENT '部门名称',
  `code` VARCHAR(50) UNIQUE COMMENT '部门编码',
  `parent_id` INT COMMENT '父部门 ID',
  `manager_id` INT COMMENT '部门负责人 ID',
  `description` VARCHAR(500) COMMENT '部门描述',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序顺序',
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`parent_id`) REFERENCES `department`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部门表';

-- ============================================
-- 3. 用户表
-- ============================================
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户 ID',
  `username` VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
  `email` VARCHAR(100) UNIQUE NOT NULL COMMENT '邮箱',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
  `real_name` VARCHAR(50) NOT NULL COMMENT '真实姓名',
  `phone` VARCHAR(20) COMMENT '联系电话',
  `avatar_url` VARCHAR(500) COMMENT '头像 URL',
  `department_id` INT COMMENT '部门 ID',
  `role_id` INT COMMENT '角色 ID',
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否激活',
  `is_admin` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否管理员',
  `last_login` DATETIME COMMENT '最后登录时间',
  `last_login_ip` VARCHAR(50) COMMENT '最后登录 IP',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`department_id`) REFERENCES `department`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`role_id`) REFERENCES `role`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 添加部门外键
ALTER TABLE `department` ADD CONSTRAINT `fk_department_manager` FOREIGN KEY (`manager_id`) REFERENCES `user`(`id`) ON DELETE SET NULL;

-- ============================================
-- 4. 分类表
-- ============================================
DROP TABLE IF EXISTS `category`;
CREATE TABLE `category` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '分类 ID',
  `name` VARCHAR(100) NOT NULL COMMENT '分类名称',
  `code` VARCHAR(50) UNIQUE COMMENT '分类编码',
  `parent_id` INT COMMENT '父分类 ID',
  `level` INT NOT NULL DEFAULT 1 COMMENT '分类层级',
  `description` TEXT COMMENT '分类描述',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序顺序',
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`parent_id`) REFERENCES `category`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='分类表';

-- ============================================
-- 5. 供应商表
-- ============================================
DROP TABLE IF EXISTS `supplier`;
CREATE TABLE `supplier` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '供应商 ID',
  `name` VARCHAR(200) NOT NULL COMMENT '供应商名称',
  `code` VARCHAR(50) UNIQUE NOT NULL COMMENT '供应商编码',
  `type` VARCHAR(50) COMMENT '供应商类型',
  `contact_person` VARCHAR(50) COMMENT '联系人',
  `phone` VARCHAR(20) COMMENT '联系电话',
  `mobile` VARCHAR(20) COMMENT '手机',
  `email` VARCHAR(100) COMMENT '邮箱',
  `fax` VARCHAR(20) COMMENT '传真',
  `website` VARCHAR(200) COMMENT '网站',
  `address` VARCHAR(500) COMMENT '地址',
  `city` VARCHAR(50) COMMENT '城市',
  `province` VARCHAR(50) COMMENT '省份',
  `country` VARCHAR(50) DEFAULT '中国' COMMENT '国家',
  `postal_code` VARCHAR(20) COMMENT '邮编',
  `tax_number` VARCHAR(50) COMMENT '税号',
  `bank_name` VARCHAR(100) COMMENT '开户行',
  `bank_account` VARCHAR(100) COMMENT '银行账号',
  `rating` DECIMAL(3,2) NOT NULL DEFAULT 0.00 COMMENT '评级',
  `status` VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态',
  `business_scope` TEXT COMMENT '经营范围',
  `notes` TEXT COMMENT '备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='供应商表';

-- ============================================
-- 6. 仓库表
-- ============================================
DROP TABLE IF EXISTS `warehouse`;
CREATE TABLE `warehouse` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '仓库 ID',
  `name` VARCHAR(100) NOT NULL COMMENT '仓库名称',
  `code` VARCHAR(50) UNIQUE NOT NULL COMMENT '仓库编码',
  `type` VARCHAR(20) NOT NULL DEFAULT 'general' COMMENT '仓库类型',
  `manager_id` INT COMMENT '仓库管理员 ID',
  `address` VARCHAR(500) COMMENT '仓库地址',
  `area` DECIMAL(10,2) COMMENT '仓库面积',
  `capacity` INT COMMENT '仓库容量',
  `phone` VARCHAR(20) COMMENT '联系电话',
  `description` TEXT COMMENT '仓库描述',
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`manager_id`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='仓库表';

-- ============================================
-- 7. 库位表
-- ============================================
DROP TABLE IF EXISTS `warehouse_location`;
CREATE TABLE `warehouse_location` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '库位 ID',
  `warehouse_id` INT NOT NULL COMMENT '仓库 ID',
  `location_code` VARCHAR(50) NOT NULL COMMENT '库位编码',
  `location_name` VARCHAR(100) COMMENT '库位名称',
  `zone` VARCHAR(50) COMMENT '区域',
  `aisle` VARCHAR(50) COMMENT '通道',
  `rack` VARCHAR(50) COMMENT '货架',
  `shelf` VARCHAR(50) COMMENT '层',
  `max_capacity` INT COMMENT '最大容量',
  `current_capacity` INT NOT NULL DEFAULT 0 COMMENT '当前容量',
  `status` VARCHAR(20) NOT NULL DEFAULT 'available' COMMENT '状态',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`warehouse_id`) REFERENCES `warehouse`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `idx_warehouse_location` (`warehouse_id`, `location_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='库位表';

-- ============================================
-- 8. 备件表
-- ============================================
DROP TABLE IF EXISTS `spare_part`;
CREATE TABLE `spare_part` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '备件 ID',
  `part_code` VARCHAR(50) UNIQUE NOT NULL COMMENT '备件代码',
  `name` VARCHAR(200) NOT NULL COMMENT '备件名称',
  `specification` VARCHAR(200) COMMENT '规格型号',
  `category_id` INT COMMENT '分类 ID',
  `supplier_id` INT COMMENT '供应商 ID',
  `unit` VARCHAR(20) NOT NULL DEFAULT '个' COMMENT '单位',
  `unit_price` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '单价',
  `min_stock` INT NOT NULL DEFAULT 0 COMMENT '最低库存',
  `max_stock` INT COMMENT '最高库存',
  `safety_stock` INT NOT NULL DEFAULT 0 COMMENT '安全库存',
  `current_stock` INT NOT NULL DEFAULT 0 COMMENT '当前库存',
  `stock_status` VARCHAR(20) NOT NULL DEFAULT 'normal' COMMENT '库存状态',
  `location` VARCHAR(100) COMMENT '库位',
  `barcode` VARCHAR(100) UNIQUE COMMENT '条形码',
  `image_url` VARCHAR(500) COMMENT '图片 URL',
  `description` TEXT COMMENT '详细描述',
  `technical_params` TEXT COMMENT '技术参数 (JSON)',
  `status` VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态',
  `created_by` INT COMMENT '创建人 ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`category_id`) REFERENCES `category`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`supplier_id`) REFERENCES `supplier`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`created_by`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='备件表';

-- ============================================
-- 9. 批次表
-- ============================================
DROP TABLE IF EXISTS `batch`;
CREATE TABLE `batch` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '批次 ID',
  `batch_number` VARCHAR(50) UNIQUE NOT NULL COMMENT '批次编号',
  `spare_part_id` INT NOT NULL COMMENT '备件 ID',
  `quantity` INT NOT NULL DEFAULT 0 COMMENT '批次数量',
  `remaining_quantity` INT NOT NULL DEFAULT 0 COMMENT '剩余数量',
  `production_date` DATE COMMENT '生产日期',
  `expiry_date` DATE COMMENT '有效期',
  `warehouse_id` INT COMMENT '仓库 ID',
  `location_id` INT COMMENT '库位 ID',
  `unit_price` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '入库单价',
  `supplier_id` INT COMMENT '供应商 ID',
  `status` VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态',
  `notes` TEXT COMMENT '备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`spare_part_id`) REFERENCES `spare_part`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`warehouse_id`) REFERENCES `warehouse`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`location_id`) REFERENCES `warehouse_location`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`supplier_id`) REFERENCES `supplier`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='批次表';

-- ============================================
-- 10. 序列号表
-- ============================================
DROP TABLE IF EXISTS `serial_number`;
CREATE TABLE `serial_number` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '序列号 ID',
  `serial_number` VARCHAR(100) UNIQUE NOT NULL COMMENT '序列号',
  `spare_part_id` INT NOT NULL COMMENT '备件 ID',
  `batch_id` INT COMMENT '批次 ID',
  `warehouse_id` INT COMMENT '仓库 ID',
  `location_id` INT COMMENT '库位 ID',
  `status` VARCHAR(20) NOT NULL DEFAULT 'in_stock' COMMENT '状态',
  `equipment_id` INT COMMENT '安装设备 ID',
  `install_date` DATE COMMENT '安装日期',
  `notes` TEXT COMMENT '备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`spare_part_id`) REFERENCES `spare_part`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`batch_id`) REFERENCES `batch`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`warehouse_id`) REFERENCES `warehouse`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`location_id`) REFERENCES `warehouse_location`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='序列号表';

-- ============================================
-- 11. 交易表
-- ============================================
DROP TABLE IF EXISTS `transaction`;
CREATE TABLE `transaction` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '交易 ID',
  `transaction_number` VARCHAR(50) UNIQUE NOT NULL COMMENT '交易编号',
  `transaction_type` VARCHAR(20) NOT NULL COMMENT '交易类型',
  `spare_part_id` INT NOT NULL COMMENT '备件 ID',
  `batch_id` INT COMMENT '批次 ID',
  `quantity` INT NOT NULL COMMENT '数量',
  `unit_price` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '单价',
  `amount` DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '金额',
  `warehouse_id` INT NOT NULL COMMENT '仓库 ID',
  `location_id` INT COMMENT '库位 ID',
  `reference_type` VARCHAR(50) COMMENT '关联类型',
  `reference_id` INT COMMENT '关联 ID',
  `notes` TEXT COMMENT '备注',
  `created_by` INT NOT NULL COMMENT '创建人 ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`spare_part_id`) REFERENCES `spare_part`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`batch_id`) REFERENCES `batch`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`warehouse_id`) REFERENCES `warehouse`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`location_id`) REFERENCES `warehouse_location`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`created_by`) REFERENCES `user`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交易表';

-- ============================================
-- 12. 交易明细表
-- ============================================
DROP TABLE IF EXISTS `transaction_detail`;
CREATE TABLE `transaction_detail` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '明细 ID',
  `transaction_id` INT NOT NULL COMMENT '交易 ID',
  `spare_part_id` INT NOT NULL COMMENT '备件 ID',
  `batch_id` INT COMMENT '批次 ID',
  `quantity` INT NOT NULL COMMENT '数量',
  `unit_price` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '单价',
  `amount` DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '金额',
  `notes` TEXT COMMENT '备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`transaction_id`) REFERENCES `transaction`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`spare_part_id`) REFERENCES `spare_part`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`batch_id`) REFERENCES `batch`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交易明细表';

-- ============================================
-- 13. 设备表
-- ============================================
DROP TABLE IF EXISTS `equipment`;
CREATE TABLE `equipment` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '设备 ID',
  `equipment_code` VARCHAR(50) UNIQUE NOT NULL COMMENT '设备编码',
  `name` VARCHAR(200) NOT NULL COMMENT '设备名称',
  `model` VARCHAR(100) COMMENT '型号',
  `specification` VARCHAR(200) COMMENT '规格',
  `category` VARCHAR(100) COMMENT '设备类别',
  `department_id` INT COMMENT '使用部门 ID',
  `location` VARCHAR(200) COMMENT '安装位置',
  `manufacturer` VARCHAR(200) COMMENT '制造商',
  `purchase_date` DATE COMMENT '购买日期',
  `install_date` DATE COMMENT '安装日期',
  `warranty_period` INT COMMENT '保修期 (月)',
  `warranty_expiry` DATE COMMENT '保修到期日期',
  `status` VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态',
  `last_maintenance_date` DATE COMMENT '最后维修日期',
  `next_maintenance_date` DATE COMMENT '下次维修计划日期',
  `maintenance_cycle` INT COMMENT '维修周期 (天)',
  `total_maintenance_count` INT NOT NULL DEFAULT 0 COMMENT '累计维修次数',
  `total_maintenance_cost` DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '累计维修成本',
  `description` TEXT COMMENT '设备描述',
  `technical_params` TEXT COMMENT '技术参数 (JSON)',
  `image_url` VARCHAR(500) COMMENT '图片 URL',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`department_id`) REFERENCES `department`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备表';

-- ============================================
-- 14. 维修工单表
-- ============================================
DROP TABLE IF EXISTS `maintenance_order`;
CREATE TABLE `maintenance_order` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '工单 ID',
  `order_number` VARCHAR(50) UNIQUE NOT NULL COMMENT '工单编号',
  `equipment_id` INT NOT NULL COMMENT '设备 ID',
  `request_type` VARCHAR(50) NOT NULL COMMENT '维修类型',
  `priority` VARCHAR(20) NOT NULL DEFAULT 'medium' COMMENT '优先级',
  `status` VARCHAR(20) NOT NULL DEFAULT 'created' COMMENT '状态',
  `description` TEXT NOT NULL COMMENT '维修描述',
  `reported_by` INT COMMENT '报告人 ID',
  `assigned_to` INT COMMENT '指派人 ID',
  `estimated_hours` FLOAT COMMENT '预计工时',
  `actual_hours` FLOAT COMMENT '实际工时',
  `estimated_cost` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '预计成本',
  `actual_cost` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '实际成本',
  `scheduled_start` DATETIME COMMENT '计划开始时间',
  `actual_start` DATETIME COMMENT '实际开始时间',
  `scheduled_completion` DATETIME COMMENT '计划完成时间',
  `actual_completion` DATETIME COMMENT '实际完成时间',
  `resolution` TEXT COMMENT '解决方案',
  `notes` TEXT COMMENT '备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`equipment_id`) REFERENCES `equipment`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`reported_by`) REFERENCES `user`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`assigned_to`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='维修工单表';

-- ============================================
-- 15. 维修任务表
-- ============================================
DROP TABLE IF EXISTS `maintenance_task`;
CREATE TABLE `maintenance_task` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '任务 ID',
  `task_number` VARCHAR(50) UNIQUE NOT NULL COMMENT '任务编号',
  `maintenance_order_id` INT NOT NULL COMMENT '工单 ID',
  `task_name` VARCHAR(200) NOT NULL COMMENT '任务名称',
  `task_type` VARCHAR(50) NOT NULL COMMENT '任务类型',
  `description` TEXT COMMENT '任务描述',
  `spare_parts_required` TEXT COMMENT '所需备件 (JSON)',
  `assigned_to` INT COMMENT '指派人 ID',
  `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态',
  `estimated_hours` FLOAT COMMENT '预计工时',
  `actual_hours` FLOAT COMMENT '实际工时',
  `completed_at` DATETIME COMMENT '完成时间',
  `notes` TEXT COMMENT '备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`maintenance_order_id`) REFERENCES `maintenance_order`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`assigned_to`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='维修任务表';

-- ============================================
-- 16. 维修记录表
-- ============================================
DROP TABLE IF EXISTS `maintenance_record`;
CREATE TABLE `maintenance_record` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录 ID',
  `record_number` VARCHAR(50) UNIQUE NOT NULL COMMENT '记录编号',
  `maintenance_order_id` INT NOT NULL COMMENT '工单 ID',
  `equipment_id` INT NOT NULL COMMENT '设备 ID',
  `maintenance_type` VARCHAR(50) NOT NULL COMMENT '维修类型',
  `maintenance_date` DATETIME NOT NULL COMMENT '维修日期',
  `description` TEXT NOT NULL COMMENT '维修描述',
  `spare_parts_used` TEXT COMMENT '使用的备件 (JSON)',
  `labor_hours` FLOAT NOT NULL DEFAULT 0 COMMENT '工时',
  `labor_cost` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '人工成本',
  `parts_cost` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '备件成本',
  `total_cost` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '总成本',
  `performed_by` INT COMMENT '维修人 ID',
  `notes` TEXT COMMENT '备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`maintenance_order_id`) REFERENCES `maintenance_order`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`equipment_id`) REFERENCES `equipment`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`performed_by`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='维修记录表';

-- ============================================
-- 17. 维修成本表
-- ============================================
DROP TABLE IF EXISTS `maintenance_cost`;
CREATE TABLE `maintenance_cost` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '成本 ID',
  `maintenance_order_id` INT NOT NULL COMMENT '工单 ID',
  `cost_type` VARCHAR(50) NOT NULL COMMENT '成本类型',
  `description` VARCHAR(500) NOT NULL COMMENT '成本描述',
  `quantity` INT NOT NULL DEFAULT 1 COMMENT '数量',
  `unit_price` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '单价',
  `amount` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '金额',
  `spare_part_id` INT COMMENT '备件 ID',
  `notes` TEXT COMMENT '备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`maintenance_order_id`) REFERENCES `maintenance_order`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`spare_part_id`) REFERENCES `spare_part`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='维修成本表';

-- ============================================
-- 18. 采购计划表
-- ============================================
DROP TABLE IF EXISTS `purchase_plan`;
CREATE TABLE `purchase_plan` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '计划 ID',
  `plan_number` VARCHAR(50) UNIQUE NOT NULL COMMENT '计划编号',
  `plan_name` VARCHAR(200) NOT NULL COMMENT '计划名称',
  `plan_type` VARCHAR(50) NOT NULL COMMENT '计划类型',
  `year` INT NOT NULL COMMENT '年份',
  `quarter` INT COMMENT '季度',
  `month` INT COMMENT '月份',
  `department_id` INT COMMENT '申请部门 ID',
  `total_budget` DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '总预算',
  `status` VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT '状态',
  `description` TEXT COMMENT '计划描述',
  `created_by` INT NOT NULL COMMENT '创建人 ID',
  `approved_by` INT COMMENT '审批人 ID',
  `approved_at` DATETIME COMMENT '审批时间',
  `notes` TEXT COMMENT '备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`department_id`) REFERENCES `department`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`created_by`) REFERENCES `user`(`id`) ON DELETE RESTRICT,
  FOREIGN KEY (`approved_by`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='采购计划表';

-- ============================================
-- 19. 采购申请表
-- ============================================
DROP TABLE IF EXISTS `purchase_request`;
CREATE TABLE `purchase_request` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '申请 ID',
  `request_number` VARCHAR(50) UNIQUE NOT NULL COMMENT '申请编号',
  `purchase_plan_id` INT COMMENT '采购计划 ID',
  `requester_id` INT NOT NULL COMMENT '申请人 ID',
  `department` VARCHAR(100) NOT NULL COMMENT '申请部门',
  `priority` VARCHAR(20) NOT NULL DEFAULT 'normal' COMMENT '优先级',
  `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态',
  `total_amount` DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '预估总金额',
  `reason` TEXT NOT NULL COMMENT '申请原因',
  `expected_delivery` DATE COMMENT '期望交货日期',
  `approved_by` INT COMMENT '审批人 ID',
  `approved_at` DATETIME COMMENT '审批时间',
  `rejection_reason` TEXT COMMENT '拒绝原因',
  `notes` TEXT COMMENT '备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`purchase_plan_id`) REFERENCES `purchase_plan`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`requester_id`) REFERENCES `user`(`id`) ON DELETE RESTRICT,
  FOREIGN KEY (`approved_by`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='采购申请表';

-- ============================================
-- 20. 采购订单表
-- ============================================
DROP TABLE IF EXISTS `purchase_order`;
CREATE TABLE `purchase_order` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '订单 ID',
  `order_number` VARCHAR(50) UNIQUE NOT NULL COMMENT '订单编号',
  `purchase_request_id` INT COMMENT '采购申请 ID',
  `supplier_id` INT NOT NULL COMMENT '供应商 ID',
  `buyer_id` INT NOT NULL COMMENT '采购员 ID',
  `order_date` DATE NOT NULL COMMENT '订单日期',
  `total_amount` DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '订单总金额',
  `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态',
  `expected_delivery` DATE COMMENT '预计交货日期',
  `actual_delivery` DATE COMMENT '实际交货日期',
  `contract_number` VARCHAR(50) COMMENT '合同编号',
  `payment_terms` VARCHAR(200) COMMENT '付款条款',
  `shipping_address` VARCHAR(500) COMMENT '送货地址',
  `contact_person` VARCHAR(50) COMMENT '联系人',
  `contact_phone` VARCHAR(20) COMMENT '联系电话',
  `notes` TEXT COMMENT '备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`purchase_request_id`) REFERENCES `purchase_request`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`supplier_id`) REFERENCES `supplier`(`id`) ON DELETE RESTRICT,
  FOREIGN KEY (`buyer_id`) REFERENCES `user`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='采购订单表';

-- ============================================
-- 21. 报价表
-- ============================================
DROP TABLE IF EXISTS `purchase_quote`;
CREATE TABLE `purchase_quote` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '报价 ID',
  `quote_number` VARCHAR(50) UNIQUE NOT NULL COMMENT '报价编号',
  `purchase_request_id` INT COMMENT '采购申请 ID',
  `supplier_id` INT NOT NULL COMMENT '供应商 ID',
  `spare_part_id` INT NOT NULL COMMENT '备件 ID',
  `quantity` INT NOT NULL COMMENT '数量',
  `unit_price` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '单价',
  `total_amount` DECIMAL(12,2) NOT NULL DEFAULT 0.00 COMMENT '总金额',
  `currency` VARCHAR(10) NOT NULL DEFAULT 'CNY' COMMENT '币种',
  `valid_until` DATE COMMENT '报价有效期至',
  `delivery_time` INT COMMENT '交货周期 (天)',
  `payment_terms` VARCHAR(200) COMMENT '付款条款',
  `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态',
  `notes` TEXT COMMENT '备注',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`purchase_request_id`) REFERENCES `purchase_request`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`supplier_id`) REFERENCES `supplier`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`spare_part_id`) REFERENCES `spare_part`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报价表';

-- ============================================
-- 22. 供应商评估表
-- ============================================
DROP TABLE IF EXISTS `supplier_evaluation`;
CREATE TABLE `supplier_evaluation` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '评估 ID',
  `supplier_id` INT NOT NULL COMMENT '供应商 ID',
  `evaluation_date` DATE NOT NULL COMMENT '评估日期',
  `evaluation_period` VARCHAR(50) NOT NULL COMMENT '评估周期',
  `quality_score` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '质量评分',
  `delivery_score` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '交货评分',
  `price_score` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '价格评分',
  `service_score` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '服务评分',
  `total_score` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '总分',
  `rating` VARCHAR(10) NOT NULL DEFAULT 'C' COMMENT '评级',
  `evaluator_id` INT NOT NULL COMMENT '评估人 ID',
  `comments` TEXT COMMENT '评估意见',
  `improvement_plan` TEXT COMMENT '改进建议',
  `status` VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT '状态',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`supplier_id`) REFERENCES `supplier`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`evaluator_id`) REFERENCES `user`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='供应商评估表';

-- ============================================
-- 23. 标签表
-- ============================================
DROP TABLE IF EXISTS `tag`;
CREATE TABLE `tag` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '标签 ID',
  `name` VARCHAR(50) UNIQUE NOT NULL COMMENT '标签名称',
  `color` VARCHAR(20) NOT NULL DEFAULT '#007bff' COMMENT '标签颜色',
  `description` VARCHAR(200) COMMENT '标签描述',
  `usage_count` INT NOT NULL DEFAULT 0 COMMENT '使用次数',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签表';

-- ============================================
-- 24. 告警表
-- ============================================
DROP TABLE IF EXISTS `alert`;
CREATE TABLE `alert` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '告警 ID',
  `alert_type` VARCHAR(50) NOT NULL COMMENT '告警类型',
  `title` VARCHAR(200) NOT NULL COMMENT '告警标题',
  `message` TEXT NOT NULL COMMENT '告警内容',
  `level` VARCHAR(20) NOT NULL DEFAULT 'info' COMMENT '告警级别',
  `status` VARCHAR(20) NOT NULL DEFAULT 'unread' COMMENT '状态',
  `related_type` VARCHAR(50) COMMENT '关联类型',
  `related_id` INT COMMENT '关联 ID',
  `triggered_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '触发时间',
  `read_at` DATETIME COMMENT '阅读时间',
  `read_by` INT COMMENT '阅读人 ID',
  `processed_at` DATETIME COMMENT '处理时间',
  `processed_by` INT COMMENT '处理人 ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`read_by`) REFERENCES `user`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`processed_by`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='告警表';

-- ============================================
-- 25. 告警规则表
-- ============================================
DROP TABLE IF EXISTS `alert_rule`;
CREATE TABLE `alert_rule` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '规则 ID',
  `rule_name` VARCHAR(100) NOT NULL COMMENT '规则名称',
  `rule_type` VARCHAR(50) NOT NULL COMMENT '规则类型',
  `alert_type` VARCHAR(50) NOT NULL COMMENT '告警类型',
  `condition_type` VARCHAR(50) NOT NULL COMMENT '条件类型',
  `threshold_value` VARCHAR(100) COMMENT '阈值',
  `enabled` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
  `notification_methods` VARCHAR(100) COMMENT '通知方式 (JSON)',
  `recipients` TEXT COMMENT '接收人列表 (JSON)',
  `description` TEXT COMMENT '规则描述',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='告警规则表';

-- ============================================
-- 26. 通知表
-- ============================================
DROP TABLE IF EXISTS `notification`;
CREATE TABLE `notification` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '通知 ID',
  `notification_type` VARCHAR(50) NOT NULL COMMENT '通知类型',
  `title` VARCHAR(200) NOT NULL COMMENT '通知标题',
  `message` TEXT NOT NULL COMMENT '通知内容',
  `level` VARCHAR(20) NOT NULL DEFAULT 'info' COMMENT '通知级别',
  `recipient_type` VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '接收者类型',
  `recipient_id` INT COMMENT '接收者 ID',
  `is_read` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否已读',
  `read_at` DATETIME COMMENT '阅读时间',
  `link_type` VARCHAR(50) COMMENT '链接类型',
  `link_url` VARCHAR(500) COMMENT '链接 URL',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知表';

-- ============================================
-- 27. 邮件配置表
-- ============================================
DROP TABLE IF EXISTS `email_config`;
CREATE TABLE `email_config` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '配置 ID',
  `config_name` VARCHAR(100) NOT NULL COMMENT '配置名称',
  `smtp_server` VARCHAR(200) NOT NULL COMMENT 'SMTP 服务器',
  `smtp_port` INT NOT NULL DEFAULT 25 COMMENT 'SMTP 端口',
  `use_tls` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否使用 TLS',
  `username` VARCHAR(100) NOT NULL COMMENT '用户名',
  `password` VARCHAR(255) NOT NULL COMMENT '密码',
  `sender_email` VARCHAR(100) NOT NULL COMMENT '发件人邮箱',
  `sender_name` VARCHAR(100) COMMENT '发件人名称',
  `is_default` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否默认配置',
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
  `last_test_at` DATETIME COMMENT '最后测试时间',
  `last_test_result` BOOLEAN COMMENT '最后测试结果',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='邮件配置表';

-- ============================================
-- 28. 删除日志表
-- ============================================
DROP TABLE IF EXISTS `deletion_log`;
CREATE TABLE `deletion_log` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志 ID',
  `table_name` VARCHAR(50) NOT NULL COMMENT '表名',
  `record_id` INT NOT NULL COMMENT '记录 ID',
  `record_data` TEXT COMMENT '删除前的数据 (JSON)',
  `deleted_by` INT NOT NULL COMMENT '删除人 ID',
  `deleted_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '删除时间',
  `reason` VARCHAR(500) COMMENT '删除原因',
  `ip_address` VARCHAR(50) COMMENT 'IP 地址',
  FOREIGN KEY (`deleted_by`) REFERENCES `user`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='删除日志表';

-- ============================================
-- 29. 系统日志表
-- ============================================
DROP TABLE IF EXISTS `system_log`;
CREATE TABLE `system_log` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志 ID',
  `log_level` VARCHAR(20) NOT NULL DEFAULT 'info' COMMENT '日志级别',
  `module` VARCHAR(50) COMMENT '模块名称',
  `action` VARCHAR(100) NOT NULL COMMENT '操作动作',
  `user_id` INT COMMENT '用户 ID',
  `user_agent` VARCHAR(500) COMMENT '用户代理',
  `ip_address` VARCHAR(50) COMMENT 'IP 地址',
  `request_method` VARCHAR(10) COMMENT '请求方法',
  `request_url` VARCHAR(500) COMMENT '请求 URL',
  `request_data` TEXT COMMENT '请求数据 (JSON)',
  `response_status` INT COMMENT '响应状态码',
  `response_data` TEXT COMMENT '响应数据 (JSON)',
  `error_message` TEXT COMMENT '错误信息',
  `execution_time` FLOAT COMMENT '执行时间 (秒)',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统日志表';

-- 启用外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- 初始化基础数据
-- ============================================

-- 插入系统角色
INSERT INTO `role` (`name`, `display_name`, `description`, `permissions`, `is_system`) VALUES
('admin', '系统管理员', '拥有所有权限', '{"*": ["create", "read", "update", "delete"]}', TRUE),
('warehouse_manager', '仓库管理员', '负责仓库管理', '{"spare_parts": ["create", "read", "update"], "batches": ["create", "read", "update"], "warehouses": ["read"], "transactions": ["create", "read"], "reports": ["read"]}', TRUE),
('purchaser', '采购员', '负责采购管理', '{"spare_parts": ["read"], "suppliers": ["create", "read", "update"], "purchase": ["create", "read", "update"], "reports": ["read"]}', TRUE),
('maintenance_manager', '维修管理员', '负责维修管理', '{"equipment": ["create", "read", "update"], "maintenance": ["create", "read", "update", "delete"], "spare_parts": ["read"], "reports": ["read"]}', TRUE),
('accountant', '财务人员', '负责财务管理', '{"spare_parts": ["read"], "maintenance": ["read"], "purchase": ["read"], "reports": ["read", "export"]}', TRUE),
('normal_user', '普通用户', '普通用户', '{"spare_parts": ["read"], "inventory": ["read"]}', TRUE);

-- ============================================
-- 脚本完成
-- ============================================
