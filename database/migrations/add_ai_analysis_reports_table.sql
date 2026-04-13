-- 创建 AI 分析报告表
CREATE TABLE IF NOT EXISTS `ai_analysis_reports` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `report_type` VARCHAR(50) NOT NULL COMMENT '报告类型：forecast/optimization/risk',
  `report_title` VARCHAR(200) NOT NULL COMMENT '报告标题',
  `report_content` TEXT NOT NULL COMMENT '报告内容',
  `total_parts` INT DEFAULT 0 COMMENT '备件总数',
  `total_value` DECIMAL(10, 2) DEFAULT 0 COMMENT '总价值',
  `duration` DECIMAL(10, 2) DEFAULT 0 COMMENT '分析耗时（秒）',
  `user_id` INT COMMENT '用户 ID',
  `user_name` VARCHAR(100) COMMENT '用户名',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  INDEX `idx_report_type` (`report_type`),
  INDEX `idx_created_at` (`created_at`),
  INDEX `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI 分析报告记录表';
