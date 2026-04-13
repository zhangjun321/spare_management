-- 添加缺失的 check_type 字段到 quality_check 表
ALTER TABLE `quality_check` 
ADD COLUMN `check_type` VARCHAR(20) NOT NULL DEFAULT 'inbound' COMMENT '质检类型' AFTER `inbound_order_id`;

-- 添加其他缺失的字段
ALTER TABLE `quality_check` 
ADD COLUMN `check_method` VARCHAR(20) DEFAULT 'sampling' COMMENT '质检方式' AFTER `inspection_type`;

ALTER TABLE `quality_check` 
ADD COLUMN `sample_ratio` DECIMAL(5,2) COMMENT '抽检比例' AFTER `check_method`;

ALTER TABLE `quality_check` 
ADD COLUMN `status` VARCHAR(20) DEFAULT 'pending' COMMENT '质检状态' AFTER `sample_size`;

ALTER TABLE `quality_check` 
ADD COLUMN `pass_rate` DECIMAL(5,2) COMMENT '合格率' AFTER `unqualified_count`;

ALTER TABLE `quality_check` 
ADD COLUMN `started_at` DATETIME COMMENT '开始时间' AFTER `inspector_id`;

ALTER TABLE `quality_check` 
ADD COLUMN `started_by` INT COMMENT '开始人' AFTER `started_at`;

ALTER TABLE `quality_check` 
ADD COLUMN `completed_at` DATETIME COMMENT '完成时间' AFTER `inspection_date`;

ALTER TABLE `quality_check` 
ADD COLUMN `completed_by` INT COMMENT '完成人' AFTER `completed_at`;

ALTER TABLE `quality_check` 
ADD COLUMN `cancelled_at` DATETIME COMMENT '取消时间' AFTER `completed_by`;

ALTER TABLE `quality_check` 
ADD COLUMN `cancelled_by` INT COMMENT '取消人' AFTER `cancelled_at`;

ALTER TABLE `quality_check` 
ADD COLUMN `remark` TEXT COMMENT '备注' AFTER `result`;

ALTER TABLE `quality_check` 
ADD COLUMN `check_remark` VARCHAR(255) COMMENT '质检备注' AFTER `remark`;
