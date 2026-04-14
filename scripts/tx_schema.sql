USE spare_parts_db;

-- Drop old tables (已备份，可安全重建)
DROP TABLE IF EXISTS inventory_snapshot;
DROP TABLE IF EXISTS inventory_ledger;
DROP TABLE IF EXISTS transaction_detail;
DROP TABLE IF EXISTS transaction;

-- 主表
CREATE TABLE `transaction` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `tx_code` VARCHAR(50) NOT NULL,
  `tx_type` VARCHAR(30) NOT NULL,
  `status` VARCHAR(20) DEFAULT 'draft',
  `source_warehouse_id` INT NULL,
  `target_warehouse_id` INT NULL,
  `operator_id` INT NOT NULL,
  `total_qty` DECIMAL(14,2) DEFAULT 0,
  `total_amount` DECIMAL(14,2) DEFAULT 0,
  `remark` TEXT,
  `submitted_at` DATETIME NULL,
  `approved_at` DATETIME NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ux_tx_code` (`tx_code`),
  KEY `idx_tx_type_status_created` (`tx_type`,`status`,`created_at`),
  KEY `idx_tx_source` (`source_warehouse_id`,`created_at`),
  KEY `idx_tx_target` (`target_warehouse_id`,`created_at`),
  CONSTRAINT `fk_tx_source_wh` FOREIGN KEY (`source_warehouse_id`) REFERENCES `warehouse` (`id`),
  CONSTRAINT `fk_tx_target_wh` FOREIGN KEY (`target_warehouse_id`) REFERENCES `warehouse` (`id`),
  CONSTRAINT `fk_tx_operator` FOREIGN KEY (`operator_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 明细表
CREATE TABLE `transaction_detail` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `transaction_id` INT NOT NULL,
  `spare_part_id` INT NOT NULL,
  `batch_id` INT NULL,
  `source_location_id` INT NULL,
  `target_location_id` INT NULL,
  `quantity` DECIMAL(14,2) NOT NULL,
  `unit_price` DECIMAL(14,2) NULL,
  `amount` DECIMAL(14,2) NULL,
  `status` VARCHAR(20) DEFAULT 'pending',
  `remark` TEXT,
  PRIMARY KEY (`id`),
  KEY `idx_tx_detail_tx` (`transaction_id`),
  KEY `idx_detail_part` (`spare_part_id`),
  CONSTRAINT `fk_detail_tx` FOREIGN KEY (`transaction_id`) REFERENCES `transaction` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_detail_part` FOREIGN KEY (`spare_part_id`) REFERENCES `spare_part` (`id`),
  CONSTRAINT `fk_detail_batch` FOREIGN KEY (`batch_id`) REFERENCES `batch` (`id`),
  CONSTRAINT `fk_detail_source_loc` FOREIGN KEY (`source_location_id`) REFERENCES `warehouse_location` (`id`),
  CONSTRAINT `fk_detail_target_loc` FOREIGN KEY (`target_location_id`) REFERENCES `warehouse_location` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 库存流水
CREATE TABLE `inventory_ledger` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `transaction_id` INT NOT NULL,
  `transaction_detail_id` INT NOT NULL,
  `spare_part_id` INT NOT NULL,
  `warehouse_id` INT NOT NULL,
  `location_id` INT NULL,
  `batch_id` INT NULL,
  `quantity_delta` DECIMAL(14,2) NOT NULL,
  `balance_after` DECIMAL(14,2) NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_ledger_part_wh` (`spare_part_id`,`warehouse_id`,`created_at`),
  CONSTRAINT `fk_ledger_tx` FOREIGN KEY (`transaction_id`) REFERENCES `transaction` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ledger_detail` FOREIGN KEY (`transaction_detail_id`) REFERENCES `transaction_detail` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ledger_part` FOREIGN KEY (`spare_part_id`) REFERENCES `spare_part` (`id`),
  CONSTRAINT `fk_ledger_wh` FOREIGN KEY (`warehouse_id`) REFERENCES `warehouse` (`id`),
  CONSTRAINT `fk_ledger_loc` FOREIGN KEY (`location_id`) REFERENCES `warehouse_location` (`id`),
  CONSTRAINT `fk_ledger_batch` FOREIGN KEY (`batch_id`) REFERENCES `batch` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 盘点快照
CREATE TABLE `inventory_snapshot` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `snapshot_code` VARCHAR(50) NOT NULL,
  `warehouse_id` INT NOT NULL,
  `location_id` INT NULL,
  `spare_part_id` INT NOT NULL,
  `batch_id` INT NULL,
  `quantity` DECIMAL(14,2) NOT NULL,
  `snapshot_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ux_snapshot_code` (`snapshot_code`),
  KEY `idx_snap_wh_loc_part` (`warehouse_id`,`location_id`,`spare_part_id`),
  CONSTRAINT `fk_snap_wh` FOREIGN KEY (`warehouse_id`) REFERENCES `warehouse` (`id`),
  CONSTRAINT `fk_snap_loc` FOREIGN KEY (`location_id`) REFERENCES `warehouse_location` (`id`),
  CONSTRAINT `fk_snap_part` FOREIGN KEY (`spare_part_id`) REFERENCES `spare_part` (`id`),
  CONSTRAINT `fk_snap_batch` FOREIGN KEY (`batch_id`) REFERENCES `batch` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
