# 仓库管理系统功能分析与数据库设计

## 一、系统功能分析

### 1.1 核心业务流程分析

#### 1.1.1 备件入库流程
**当前实现：**
- ✅ 入库单创建（采购入库、退货入库、调拨入库、其他入库）
- ✅ 入库单明细管理（备件、数量、批次）
- ✅ 验收管理（验收状态、验收结果）
- ✅ 货位分配（AI 推荐、手动分配）
- ✅ 库存更新（自动增加库存）

**存在的问题：**
1. ❌ 缺少质检流程（QC 检验、不合格品处理）
2. ❌ 缺少上架确认环节（收货后未确认上架）
3. ❌ 缺少 ASN（预到货通知）功能
4. ❌ 缺少供应商预约入库功能
5. ❌ 缺少条码/RFID 扫描入库支持

**优化建议：**
```python
# 新增质检流程
class QualityCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inbound_order_id = db.Column(db.Integer, db.ForeignKey('inbound_order_v3.id'))
    inspector_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    inspection_type = db.Column(db.String(20))  # 抽检/全检
    sample_size = db.Column(db.Integer)  # 抽样数量
    qualified_count = db.Column(db.Integer)  # 合格数量
    unqualified_count = db.Column(db.Integer)  # 不合格数量
    defect_description = db.Column(db.Text)  # 缺陷描述
    inspection_report = db.Column(db.Text)  # 质检报告
    result = db.Column(db.String(20))  # 合格/不合格/让步接收
    inspection_date = db.Column(db.DateTime)
```

#### 1.1.2 备件出库流程
**当前实现：**
- ✅ 出库单创建（销售出库、调拨出库、报废出库、其他出库）
- ✅ 出库单明细管理
- ✅ 拣货管理（AI 路径优化）
- ✅ 批次推荐（FIFO/FEFO）
- ✅ 库存更新（自动减少库存）

**存在的问题：**
1. ❌ 缺少波次管理（多个订单合并拣货）
2. ❌ 缺少复核环节（拣货后未复核）
3. ❌ 缺少包装管理（打包、称重、贴标）
4. ❌ 缺少发货确认环节
5. ❌ 缺少物流跟踪集成

**优化建议：**
```python
# 新增波次管理
class PickingWave(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wave_no = db.Column(db.String(50), unique=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'))
    status = db.Column(db.String(20))  # 创建/拣货中/已完成
    picker_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    order_ids = db.Column(db.JSON)  # 关联的出库单 ID 列表
    total_items = db.Column(db.Integer)
    picked_items = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
```

#### 1.1.3 库存盘点流程
**当前实现：**
- ⚠️ 仅有基础库存模型
- ⚠️ 缺少盘点计划、盘点单、盘点差异处理

**缺失功能：**
1. ❌ 盘点计划（定期盘点、循环盘点、动态盘点）
2. ❌ 盘点单创建与执行
3. ❌ 盘点差异分析
4. ❌ 盘盈盘亏处理
5. ❌ 盘点报告生成

**建议实现：**
```python
# 盘点管理
class InventoryCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    check_no = db.Column(db.String(50), unique=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'))
    check_type = db.Column(db.String(20))  # 定期/循环/动态
    status = db.Column(db.String(20))  # 计划中/进行中/已完成
    planned_date = db.Column(db.Date)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    checker_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total_items = db.Column(db.Integer)
    checked_items = db.Column(db.Integer)
    difference_items = db.Column(db.Integer)
    notes = db.Column(db.Text)

class InventoryCheckItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    check_id = db.Column(db.Integer, db.ForeignKey('inventory_check.id'))
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory_v3.id'))
    part_id = db.Column(db.Integer, db.ForeignKey('spare_part.id'))
    location_id = db.Column(db.Integer, db.ForeignKey('warehouse_location_v3.id'))
    system_quantity = db.Column(db.Numeric(12, 4))  # 系统数量
    actual_quantity = db.Column(db.Numeric(12, 4))  # 实际数量
    difference = db.Column(db.Numeric(12, 4))  # 差异
    difference_reason = db.Column(db.String(200))  # 差异原因
    status = db.Column(db.String(20))  # 待盘点/已盘点/已处理
```

#### 1.1.4 库存预警流程
**当前实现：**
- ✅ 备件模型中有库存状态更新逻辑
- ✅ 支持最低/最高库存设置
- ⚠️ 预警功能不完善

**存在的问题：**
1. ❌ 缺少预警规则配置（多级预警、自定义阈值）
2. ❌ 缺少预警通知（邮件、短信、系统消息）
3. ❌ 缺少预警处理流程
4. ❌ 缺少预警统计分析
5. ❌ 缺少保质期预警

**优化建议：**
```python
# 预警规则配置
class WarningRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rule_name = db.Column(db.String(100))
    rule_type = db.Column(db.String(50))  # 低库存/高库存/保质期/呆滞
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_v3.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    threshold_type = db.Column(db.String(20))  # 百分比/固定值
    threshold_value = db.Column(db.Numeric(10, 2))
    warning_level = db.Column(db.String(20))  # 低/中/高/紧急
    enabled = db.Column(db.Boolean, default=True)
    
class WarningLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('warning_rule.id'))
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory_v3.id'))
    warning_content = db.Column(db.Text)
    warning_level = db.Column(db.String(20))
    status = db.Column(db.String(20))  # 未处理/已处理/已忽略
    notified_users = db.Column(db.JSON)  # 已通知用户
    notified_time = db.Column(db.DateTime)
    handled_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    handled_time = db.Column(db.DateTime)
    handled_notes = db.Column(db.Text)
```

### 1.2 数据处理分析

#### 1.2.1 并发控制问题
**当前问题：**
1. ❌ 缺少乐观锁/悲观锁机制
2. ❌ 库存扣减可能出现超卖
3. ❌ 多用户同时操作同一单据可能冲突

**解决方案：**
```python
# 乐观锁实现
class InventoryV3(db.Model):
    # ... 现有字段 ...
    version = db.Column(db.Integer, default=0, comment='版本号')
    
    def decrease_stock(self, quantity, user_id):
        """扣减库存（乐观锁）"""
        from sqlalchemy.orm import with_for_update
        
        # 方案 1: 悲观锁
        inventory = db.session.query(InventoryV3).with_for_update().get(self.id)
        
        # 方案 2: 乐观锁
        result = db.session.query(InventoryV3)\
            .filter(
                InventoryV3.id == self.id,
                InventoryV3.version == self.version,
                InventoryV3.quantity >= quantity
            )\
            .update({
                'quantity': InventoryV3.quantity - quantity,
                'version': InventoryV3.version + 1
            })
        
        if result == 0:
            raise Exception('库存不足或数据已被修改')
```

#### 1.2.2 事务处理
**当前问题：**
1. ⚠️ 部分操作缺少事务控制
2. ⚠️ 异常回滚不完整

**优化建议：**
```python
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

def create_inbound_order(data):
    """创建入库单（事务控制）"""
    try:
        # 开始事务
        db.session.begin_nested()
        
        # 创建入库单
        order = InboundOrderV3(**data)
        db.session.add(order)
        db.session.flush()
        
        # 创建入库明细
        for item_data in data['items']:
            item = InboundOrderItemV3(**item_data, order_id=order.id)
            db.session.add(item)
        
        # 提交事务
        db.session.commit()
        return order
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f'创建入库单失败：{str(e)}')
        raise
```

### 1.3 用户体验优化

#### 1.3.1 操作便捷性
**优化建议：**
1. ✅ 批量操作支持（批量入库、批量出库）
2. ✅ 快速搜索（条码扫描、模糊搜索）
3. ✅ 模板导入导出（Excel 导入、导出）
4. ✅ 最近操作记录（快速再次操作）
5. ✅ 快捷键支持

#### 1.3.2 可视化展示
**优化建议：**
1. ✅ 仓库平面图（可视化货位管理）
2. ✅ 库存热力图（高频备件展示）
3. ✅ 出入库趋势图（时间序列分析）
4. ✅ 库存周转率分析
5. ✅ ABC 分类可视化

## 二、数据库表结构设计

### 2.1 仓库管理核心表

#### 2.1.1 仓库表 (warehouse_v3)
```sql
CREATE TABLE warehouse_v3 (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '仓库 ID',
    code VARCHAR(50) UNIQUE NOT NULL COMMENT '仓库编码',
    name VARCHAR(100) NOT NULL COMMENT '仓库名称',
    type VARCHAR(50) NOT NULL DEFAULT 'general' COMMENT '仓库类型',
    level VARCHAR(20) DEFAULT 'A' COMMENT '仓库等级',
    status VARCHAR(20) DEFAULT 'active' COMMENT '仓库状态',
    
    -- 位置信息
    address VARCHAR(200) COMMENT '仓库地址',
    latitude DECIMAL(10, 8) COMMENT '纬度',
    longitude DECIMAL(11, 8) COMMENT '经度',
    
    -- 容量信息
    total_area DECIMAL(10, 2) COMMENT '总面积 (平方米)',
    usable_area DECIMAL(10, 2) COMMENT '可用面积 (平方米)',
    total_volume DECIMAL(12, 2) COMMENT '总容积 (立方米)',
    total_capacity INT COMMENT '总容量 (托盘数)',
    
    -- 管理信息
    manager_id INT COMMENT '仓库管理员 ID',
    phone VARCHAR(20) COMMENT '联系电话',
    email VARCHAR(100) COMMENT '联系邮箱',
    
    -- 配置信息
    temperature_control BOOLEAN DEFAULT FALSE COMMENT '温控',
    humidity_control BOOLEAN DEFAULT FALSE COMMENT '湿控',
    security_level VARCHAR(20) DEFAULT 'normal' COMMENT '安防等级',
    
    -- AI 相关
    ai_enabled BOOLEAN DEFAULT TRUE COMMENT '启用 AI',
    ai_config JSON COMMENT 'AI 配置',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by INT COMMENT '创建人',
    updated_by INT COMMENT '更新人',
    
    -- 其他
    description TEXT COMMENT '描述',
    remarks TEXT COMMENT '备注',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    
    -- 索引
    INDEX idx_code (code),
    INDEX idx_type (type),
    INDEX idx_status (status),
    
    -- 外键
    FOREIGN KEY (manager_id) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id),
    FOREIGN KEY (updated_by) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='仓库表 V3';
```

#### 2.1.2 仓库位置表 (warehouse_location_v3)
```sql
CREATE TABLE warehouse_location_v3 (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '货位 ID',
    warehouse_id INT NOT NULL COMMENT '仓库 ID',
    code VARCHAR(50) NOT NULL COMMENT '货位编码',
    name VARCHAR(100) COMMENT '货位名称',
    
    -- 位置信息
    zone VARCHAR(50) COMMENT '区域',
    aisle VARCHAR(50) COMMENT '通道',
    bay VARCHAR(50) COMMENT '排',
    level VARCHAR(50) COMMENT '层',
    position VARCHAR(50) COMMENT '位',
    
    -- 容量信息
    max_weight DECIMAL(10, 2) COMMENT '最大承重 (kg)',
    max_volume DECIMAL(10, 2) COMMENT '最大容积 (m³)',
    max_quantity INT COMMENT '最大数量',
    
    -- 状态信息
    status VARCHAR(20) DEFAULT 'available' COMMENT '货位状态',
    location_type VARCHAR(50) COMMENT '货位类型',
    
    -- 坐标信息（用于可视化）
    x_coordinate DECIMAL(8, 2) COMMENT 'X 坐标',
    y_coordinate DECIMAL(8, 2) COMMENT 'Y 坐标',
    z_coordinate DECIMAL(8, 2) COMMENT 'Z 坐标',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 其他
    remarks TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 索引
    UNIQUE KEY uk_warehouse_code (warehouse_id, code),
    INDEX idx_warehouse (warehouse_id),
    INDEX idx_status (status),
    INDEX idx_zone (zone),
    
    -- 外键
    FOREIGN KEY (warehouse_id) REFERENCES warehouse_v3(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='仓库位置表 V3';
```

#### 2.1.3 入库单表 (inbound_order_v3)
```sql
CREATE TABLE inbound_order_v3 (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '入库单 ID',
    order_no VARCHAR(50) UNIQUE NOT NULL COMMENT '入库单号',
    warehouse_id INT NOT NULL COMMENT '仓库 ID',
    
    -- 业务类型
    order_type VARCHAR(50) NOT NULL COMMENT '入库类型',
    source_type VARCHAR(50) COMMENT '来源类型',
    source_id INT COMMENT '来源 ID',
    
    -- 供应商信息
    supplier_id INT COMMENT '供应商 ID',
    supplier_name VARCHAR(100) COMMENT '供应商名称',
    
    -- 状态信息
    status VARCHAR(20) DEFAULT 'pending' COMMENT '入库状态',
    priority VARCHAR(20) DEFAULT 'normal' COMMENT '优先级',
    
    -- 计划信息
    planned_date DATE COMMENT '计划入库日期',
    expected_date DATE COMMENT '预计入库日期',
    actual_date DATE COMMENT '实际入库日期',
    
    -- 汇总信息
    total_items INT DEFAULT 0 COMMENT '总项数',
    total_quantity DECIMAL(12, 4) DEFAULT 0 COMMENT '总数量',
    received_quantity DECIMAL(12, 4) DEFAULT 0 COMMENT '已收数量',
    
    -- 验收信息
    inspection_status VARCHAR(20) DEFAULT 'pending' COMMENT '验收状态',
    inspection_date DATETIME COMMENT '验收日期',
    inspector_id INT COMMENT '验收人',
    inspection_result VARCHAR(20) COMMENT '验收结果',
    
    -- AI 处理
    ai_location_recommendations JSON COMMENT 'AI 货位推荐',
    ai_processing_status VARCHAR(20) COMMENT 'AI 处理状态',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT COMMENT '创建人',
    updated_by INT COMMENT '更新人',
    approved_at DATETIME COMMENT '审核时间',
    approved_by INT COMMENT '审核人',
    
    -- 其他
    description TEXT,
    remarks TEXT,
    
    -- 索引
    UNIQUE KEY uk_order_no (order_no),
    INDEX idx_warehouse (warehouse_id),
    INDEX idx_status (status),
    INDEX idx_order_type (order_type),
    INDEX idx_created_at (created_at),
    
    -- 外键
    FOREIGN KEY (warehouse_id) REFERENCES warehouse_v3(id),
    FOREIGN KEY (supplier_id) REFERENCES supplier(id),
    FOREIGN KEY (inspector_id) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id),
    FOREIGN KEY (updated_by) REFERENCES user(id),
    FOREIGN KEY (approved_by) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='入库单表 V3';
```

#### 2.1.4 入库单明细表 (inbound_order_item_v3)
```sql
CREATE TABLE inbound_order_item_v3 (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '入库单明细 ID',
    order_id INT NOT NULL COMMENT '入库单 ID',
    part_id INT NOT NULL COMMENT '备件 ID',
    location_id INT COMMENT '推荐货位 ID',
    
    -- 数量信息
    planned_quantity DECIMAL(12, 4) NOT NULL COMMENT '计划数量',
    received_quantity DECIMAL(12, 4) DEFAULT 0 COMMENT '实收数量',
    rejected_quantity DECIMAL(12, 4) DEFAULT 0 COMMENT '拒收数量',
    unit VARCHAR(20) NOT NULL COMMENT '单位',
    
    -- 批次信息
    batch_no VARCHAR(50) COMMENT '批次号',
    production_date DATE COMMENT '生产日期',
    expiry_date DATE COMMENT '有效期至',
    
    -- 货位分配
    assigned_location_id INT COMMENT '分配货位 ID',
    actual_location_id INT COMMENT '实际货位 ID',
    
    -- 验收信息
    inspection_status VARCHAR(20) DEFAULT 'pending' COMMENT '验收状态',
    inspection_result VARCHAR(20) COMMENT '验收结果',
    inspection_notes TEXT COMMENT '验收备注',
    
    -- AI 分析
    ai_recommendation_score DECIMAL(5, 2) COMMENT 'AI 推荐评分',
    ai_notes TEXT COMMENT 'AI 备注',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 其他
    remarks TEXT,
    
    -- 索引
    INDEX idx_order (order_id),
    INDEX idx_part (part_id),
    INDEX idx_location (location_id),
    INDEX idx_batch_no (batch_no),
    
    -- 外键
    FOREIGN KEY (order_id) REFERENCES inbound_order_v3(id),
    FOREIGN KEY (part_id) REFERENCES spare_part(id),
    FOREIGN KEY (location_id) REFERENCES warehouse_location_v3(id),
    FOREIGN KEY (assigned_location_id) REFERENCES warehouse_location_v3(id),
    FOREIGN KEY (actual_location_id) REFERENCES warehouse_location_v3(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='入库单明细表 V3';
```

#### 2.1.5 出库单表 (outbound_order_v3)
```sql
CREATE TABLE outbound_order_v3 (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '出库单 ID',
    order_no VARCHAR(50) UNIQUE NOT NULL COMMENT '出库单号',
    warehouse_id INT NOT NULL COMMENT '仓库 ID',
    
    -- 业务类型
    order_type VARCHAR(50) NOT NULL COMMENT '出库类型',
    destination_type VARCHAR(50) COMMENT '去向类型',
    destination_id INT COMMENT '去向 ID',
    
    -- 客户信息
    customer_id INT COMMENT '客户 ID',
    customer_name VARCHAR(100) COMMENT '客户名称',
    
    -- 状态信息
    status VARCHAR(20) DEFAULT 'pending' COMMENT '出库状态',
    priority VARCHAR(20) DEFAULT 'normal' COMMENT '优先级',
    
    -- 计划信息
    planned_date DATE COMMENT '计划出库日期',
    expected_date DATE COMMENT '预计出库日期',
    actual_date DATE COMMENT '实际出库日期',
    
    -- 拣货信息
    picking_status VARCHAR(20) DEFAULT 'pending' COMMENT '拣货状态',
    picking_date DATETIME COMMENT '拣货日期',
    picker_id INT COMMENT '拣货员',
    
    -- 汇总信息
    total_items INT DEFAULT 0 COMMENT '总项数',
    total_quantity DECIMAL(12, 4) DEFAULT 0 COMMENT '总数量',
    picked_quantity DECIMAL(12, 4) DEFAULT 0 COMMENT '已拣数量',
    
    -- 复核信息
    review_status VARCHAR(20) DEFAULT 'pending' COMMENT '复核状态',
    review_date DATETIME COMMENT '复核日期',
    reviewer_id INT COMMENT '复核人',
    
    -- AI 处理
    ai_picking_path JSON COMMENT 'AI 拣货路径',
    ai_batch_recommendations JSON COMMENT 'AI 批次推荐',
    ai_processing_status VARCHAR(20) COMMENT 'AI 处理状态',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT COMMENT '创建人',
    updated_by INT COMMENT '更新人',
    approved_at DATETIME COMMENT '审核时间',
    approved_by INT COMMENT '审核人',
    
    -- 其他
    description TEXT,
    remarks TEXT,
    
    -- 索引
    UNIQUE KEY uk_order_no (order_no),
    INDEX idx_warehouse (warehouse_id),
    INDEX idx_status (status),
    INDEX idx_order_type (order_type),
    INDEX idx_created_at (created_at),
    
    -- 外键
    FOREIGN KEY (warehouse_id) REFERENCES warehouse_v3(id),
    FOREIGN KEY (customer_id) REFERENCES customer(id),
    FOREIGN KEY (picker_id) REFERENCES user(id),
    FOREIGN KEY (reviewer_id) REFERENCES user(id),
    FOREIGN KEY (created_by) REFERENCES user(id),
    FOREIGN KEY (updated_by) REFERENCES user(id),
    FOREIGN KEY (approved_by) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='出库单表 V3';
```

#### 2.1.6 出库单明细表 (outbound_order_item_v3)
```sql
CREATE TABLE outbound_order_item_v3 (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '出库单明细 ID',
    order_id INT NOT NULL COMMENT '出库单 ID',
    part_id INT NOT NULL COMMENT '备件 ID',
    
    -- 数量信息
    requested_quantity DECIMAL(12, 4) NOT NULL COMMENT '申请数量',
    picked_quantity DECIMAL(12, 4) DEFAULT 0 COMMENT '已拣数量',
    shipped_quantity DECIMAL(12, 4) DEFAULT 0 COMMENT '已发数量',
    unit VARCHAR(20) NOT NULL COMMENT '单位',
    
    -- 批次推荐
    recommended_batch_id INT COMMENT '推荐批次 ID',
    actual_batch_id INT COMMENT '实际批次 ID',
    
    -- 货位信息
    source_location_id INT COMMENT '源货位 ID',
    
    -- 拣货信息
    picking_status VARCHAR(20) DEFAULT 'pending' COMMENT '拣货状态',
    picking_location_id INT COMMENT '拣货货位 ID',
    actual_picking_location_id INT COMMENT '实际拣货货位 ID',
    
    -- AI 分析
    ai_recommendation_score DECIMAL(5, 2) COMMENT 'AI 推荐评分',
    ai_picking_sequence INT COMMENT 'AI 拣货顺序',
    ai_notes TEXT COMMENT 'AI 备注',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 其他
    remarks TEXT,
    
    -- 索引
    INDEX idx_order (order_id),
    INDEX idx_part (part_id),
    INDEX idx_batch (recommended_batch_id),
    
    -- 外键
    FOREIGN KEY (order_id) REFERENCES outbound_order_v3(id),
    FOREIGN KEY (part_id) REFERENCES spare_part(id),
    FOREIGN KEY (recommended_batch_id) REFERENCES batch(id),
    FOREIGN KEY (actual_batch_id) REFERENCES batch(id),
    FOREIGN KEY (source_location_id) REFERENCES warehouse_location_v3(id),
    FOREIGN KEY (picking_location_id) REFERENCES warehouse_location_v3(id),
    FOREIGN KEY (actual_picking_location_id) REFERENCES warehouse_location_v3(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='出库单明细表 V3';
```

#### 2.1.7 库存表 (inventory_v3)
```sql
CREATE TABLE inventory_v3 (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '库存 ID',
    warehouse_id INT NOT NULL COMMENT '仓库 ID',
    location_id INT COMMENT '货位 ID',
    part_id INT NOT NULL COMMENT '备件 ID',
    batch_id INT COMMENT '批次 ID',
    
    -- 数量信息
    quantity DECIMAL(12, 4) NOT NULL DEFAULT 0 COMMENT '当前数量',
    locked_quantity DECIMAL(12, 4) DEFAULT 0 COMMENT '锁定数量',
    available_quantity DECIMAL(12, 4) DEFAULT 0 COMMENT '可用数量',
    unit VARCHAR(20) NOT NULL COMMENT '单位',
    
    -- 库存状态
    status VARCHAR(20) DEFAULT 'normal' COMMENT '库存状态',
    quality_status VARCHAR(20) DEFAULT '合格' COMMENT '质量状态',
    
    -- 入库信息
    inbound_date DATETIME COMMENT '入库日期',
    production_date DATE COMMENT '生产日期',
    expiry_date DATE COMMENT '有效期至',
    shelf_life INT COMMENT '保质期 (天)',
    
    -- 成本信息
    unit_cost DECIMAL(12, 2) COMMENT '单位成本',
    total_cost DECIMAL(14, 2) COMMENT '总成本',
    last_purchase_price DECIMAL(12, 2) COMMENT '最后采购价',
    
    -- 库存控制
    min_quantity DECIMAL(12, 4) COMMENT '最小库存',
    max_quantity DECIMAL(12, 4) COMMENT '最大库存',
    reorder_point DECIMAL(12, 4) COMMENT 'reorder 点',
    reorder_quantity DECIMAL(12, 4) COMMENT 'reorder 数量',
    
    -- ABC 分类
    abc_class VARCHAR(5) DEFAULT 'C' COMMENT 'ABC 分类',
    turnover_rate DECIMAL(8, 4) DEFAULT 0 COMMENT '周转率',
    last_movement_date DATETIME COMMENT '最后移动日期',
    
    -- AI 分析
    demand_forecast JSON COMMENT '需求预测',
    ai_recommendations JSON COMMENT 'AI 建议',
    risk_score DECIMAL(5, 2) COMMENT '风险评分',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 其他
    remarks TEXT,
    
    -- 索引
    UNIQUE KEY uk_warehouse_part_batch (warehouse_id, part_id, batch_id),
    INDEX idx_warehouse (warehouse_id),
    INDEX idx_part (part_id),
    INDEX idx_location (location_id),
    INDEX idx_status (status),
    INDEX idx_batch (batch_id),
    INDEX idx_expiry_date (expiry_date),
    
    -- 外键
    FOREIGN KEY (warehouse_id) REFERENCES warehouse_v3(id),
    FOREIGN KEY (location_id) REFERENCES warehouse_location_v3(id),
    FOREIGN KEY (part_id) REFERENCES spare_part(id),
    FOREIGN KEY (batch_id) REFERENCES batch(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存表 V3';
```

### 2.2 扩展功能表

#### 2.2.1 盘点管理表
```sql
CREATE TABLE inventory_check (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '盘点单 ID',
    check_no VARCHAR(50) UNIQUE NOT NULL COMMENT '盘点单号',
    warehouse_id INT NOT NULL COMMENT '仓库 ID',
    check_type VARCHAR(20) NOT NULL COMMENT '盘点类型',
    status VARCHAR(20) DEFAULT 'planned' COMMENT '盘点状态',
    planned_date DATE COMMENT '计划盘点日期',
    start_date DATETIME COMMENT '开始日期',
    end_date DATETIME COMMENT '结束日期',
    checker_id INT COMMENT '盘点人',
    total_items INT DEFAULT 0 COMMENT '总项数',
    checked_items INT DEFAULT 0 COMMENT '已盘点项数',
    difference_items INT DEFAULT 0 COMMENT '差异项数',
    notes TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_warehouse (warehouse_id),
    INDEX idx_status (status),
    FOREIGN KEY (warehouse_id) REFERENCES warehouse_v3(id),
    FOREIGN KEY (checker_id) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='盘点单表';

CREATE TABLE inventory_check_item (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '盘点明细 ID',
    check_id INT NOT NULL COMMENT '盘点单 ID',
    inventory_id INT COMMENT '库存 ID',
    part_id INT NOT NULL COMMENT '备件 ID',
    location_id INT COMMENT '货位 ID',
    system_quantity DECIMAL(12, 4) NOT NULL COMMENT '系统数量',
    actual_quantity DECIMAL(12, 4) NOT NULL COMMENT '实际数量',
    difference DECIMAL(12, 4) COMMENT '差异',
    difference_reason VARCHAR(200) COMMENT '差异原因',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态',
    checked_at DATETIME COMMENT '盘点时间',
    checked_by INT COMMENT '盘点人',
    
    INDEX idx_check (check_id),
    INDEX idx_part (part_id),
    FOREIGN KEY (check_id) REFERENCES inventory_check(id),
    FOREIGN KEY (inventory_id) REFERENCES inventory_v3(id),
    FOREIGN KEY (part_id) REFERENCES spare_part(id),
    FOREIGN KEY (location_id) REFERENCES warehouse_location_v3(id),
    FOREIGN KEY (checked_by) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='盘点明细表';
```

#### 2.2.2 预警管理表
```sql
CREATE TABLE warning_rule (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '预警规则 ID',
    rule_name VARCHAR(100) NOT NULL COMMENT '规则名称',
    rule_type VARCHAR(50) NOT NULL COMMENT '规则类型',
    warehouse_id INT COMMENT '仓库 ID',
    category_id INT COMMENT '分类 ID',
    threshold_type VARCHAR(20) COMMENT '阈值类型',
    threshold_value DECIMAL(10, 2) COMMENT '阈值',
    warning_level VARCHAR(20) DEFAULT 'medium' COMMENT '预警级别',
    enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_type (rule_type),
    INDEX idx_warehouse (warehouse_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouse_v3(id),
    FOREIGN KEY (category_id) REFERENCES category(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='预警规则表';

CREATE TABLE warning_log (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '预警日志 ID',
    rule_id INT NOT NULL COMMENT '预警规则 ID',
    inventory_id INT COMMENT '库存 ID',
    warning_content TEXT COMMENT '预警内容',
    warning_level VARCHAR(20) COMMENT '预警级别',
    status VARCHAR(20) DEFAULT 'unhandled' COMMENT '处理状态',
    notified_users JSON COMMENT '已通知用户',
    notified_time DATETIME COMMENT '通知时间',
    handled_user INT COMMENT '处理人',
    handled_time DATETIME COMMENT '处理时间',
    handled_notes TEXT COMMENT '处理备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_rule (rule_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (rule_id) REFERENCES warning_rule(id),
    FOREIGN KEY (inventory_id) REFERENCES inventory_v3(id),
    FOREIGN KEY (handled_user) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='预警日志表';
```

## 三、模拟测试数据

### 3.1 仓库数据
```sql
-- 仓库数据
INSERT INTO warehouse_v3 (code, name, type, level, status, address, total_area, total_capacity, manager_id, phone, email, temperature_control, humidity_control, security_level, ai_enabled, is_active) VALUES
('WH-MAIN-001', '主仓库', 'general', 'A', 'active', '北京市朝阳区工业园 1 号', 5000.00, 1000, 1, '13800138001', 'warehouse1@example.com', TRUE, TRUE, 'high', TRUE, TRUE),
('WH-COLD-001', '冷藏仓库', 'cold', 'A', 'active', '北京市朝阳区工业园 2 号', 2000.00, 500, 1, '13800138002', 'warehouse2@example.com', TRUE, TRUE, 'high', TRUE, TRUE),
('WH-HAZARD-001', '危险品仓库', 'hazardous', 'S', 'active', '北京市大兴区化工园 3 号', 1500.00, 300, 2, '13800138003', 'warehouse3@example.com', FALSE, TRUE, 'special', TRUE, TRUE),
('WH-VALUABLE-001', '贵重物品仓库', 'valuable', 'S', 'active', '北京市海淀区科技园 4 号', 800.00, 200, 3, '13800138004', 'warehouse4@example.com', TRUE, TRUE, 'special', TRUE, TRUE),
('WH-DIST-001', '备件分拣中心', 'distribution', 'A', 'active', '北京市通州区物流园 5 号', 10000.00, 2000, 1, '13800138005', 'warehouse5@example.com', FALSE, FALSE, 'normal', TRUE, TRUE);
```

### 3.2 仓库位置数据
```sql
-- 仓库位置数据（主仓库）
INSERT INTO warehouse_location_v3 (warehouse_id, code, name, zone, aisle, bay, level, position, max_weight, max_quantity, status, location_type, x_coordinate, y_coordinate, is_active) VALUES
(1, 'WH-MAIN-A01-01-01', 'A 区 -01 排 -01 层 -01 位', 'A', '01', '01', '01', '01', 500.00, 100, 'available', 'pallet', 10.5, 5.2, TRUE),
(1, 'WH-MAIN-A01-01-01-02', 'A 区 -01 排 -01 层 -02 位', 'A', '01', '01', '01', '02', 500.00, 100, 'available', 'pallet', 11.5, 5.2, TRUE),
(1, 'WH-MAIN-A01-01-02-01', 'A 区 -01 排 -02 层 -01 位', 'A', '01', '01', '02', '01', 500.00, 100, 'occupied', 'pallet', 10.5, 6.2, TRUE),
(1, 'WH-MAIN-A02-01-01-01', 'A 区 -02 排 -01 层 -01 位', 'A', '02', '01', '01', '01', 500.00, 100, 'available', 'pallet', 15.5, 5.2, TRUE),
(1, 'WH-MAIN-B01-01-01-01', 'B 区 -01 排 -01 层 -01 位', 'B', '01', '01', '01', '01', 300.00, 50, 'available', 'shelf', 20.5, 5.2, TRUE);
```

### 3.3 入库单数据
```sql
-- 入库单数据
INSERT INTO inbound_order_v3 (order_no, warehouse_id, order_type, supplier_id, supplier_name, status, priority, planned_date, total_items, total_quantity, received_quantity, created_by) VALUES
('INB-20240410-001', 1, 'purchase', 1, '北京供应商 A', 'completed', 'normal', '2024-04-10', 5, 500.0000, 500.0000, 1),
('INB-20240410-002', 1, 'purchase', 2, '上海供应商 B', 'processing', 'high', '2024-04-11', 3, 300.0000, 150.0000, 1),
('INB-20240410-003', 2, 'purchase', 3, '广州供应商 C', 'pending', 'normal', '2024-04-12', 10, 1000.0000, 0, 2),
('INB-20240410-004', 1, 'return', 1, '北京供应商 A', 'pending', 'low', '2024-04-13', 2, 50.0000, 0, 1),
('INB-20240410-005', 3, 'transfer', NULL, '内部调拨', 'completed', 'normal', '2024-04-10', 8, 800.0000, 800.0000, 3);
```

### 3.4 出库单数据
```sql
-- 出库单数据
INSERT INTO outbound_order_v3 (order_no, warehouse_id, order_type, customer_id, customer_name, status, priority, planned_date, total_items, total_quantity, picked_quantity, created_by) VALUES
('OUT-20240410-001', 1, 'sales', 1, '客户 A', 'completed', 'normal', '2024-04-10', 3, 300.0000, 300.0000, 1),
('OUT-20240410-002', 1, 'sales', 2, '客户 B', 'processing', 'high', '2024-04-11', 5, 500.0000, 250.0000, 1),
('OUT-20240410-003', 2, 'sales', 3, '客户 C', 'pending', 'normal', '2024-04-12', 2, 200.0000, 0, 2),
('OUT-20240410-004', 1, 'scrap', NULL, '报废处理', 'pending', 'low', '2024-04-13', 1, 50.0000, 0, 1),
('OUT-20240410-005', 3, 'transfer', NULL, '内部调拨', 'completed', 'normal', '2024-04-10', 4, 400.0000, 400.0000, 3);
```

### 3.5 库存数据
```sql
-- 库存数据
INSERT INTO inventory_v3 (warehouse_id, location_id, part_id, batch_id, quantity, locked_quantity, available_quantity, unit, status, quality_status, min_quantity, max_quantity, abc_class, turnover_rate) VALUES
(1, 1, 1, 1, 100.0000, 10.0000, 90.0000, '个', 'normal', '合格', 20.0000, 500.0000, 'A', 0.85),
(1, 2, 2, 2, 50.0000, 5.0000, 45.0000, '个', 'normal', '合格', 10.0000, 200.0000, 'B', 0.65),
(1, 3, 3, 3, 200.0000, 20.0000, 180.0000, '个', 'normal', '合格', 50.0000, 1000.0000, 'A', 0.92),
(1, 4, 4, 4, 30.0000, 0.0000, 30.0000, '个', 'low', '合格', 50.0000, 300.0000, 'C', 0.35),
(1, 5, 5, 5, 500.0000, 50.0000, 450.0000, '个', 'overstocked', '合格', 100.0000, 400.0000, 'B', 0.45),
(2, NULL, 6, 6, 80.0000, 8.0000, 72.0000, '个', 'normal', '合格', 15.0000, 150.0000, 'A', 0.78),
(2, NULL, 7, 7, 120.0000, 12.0000, 108.0000, '个', 'normal', '合格', 25.0000, 250.0000, 'B', 0.68),
(3, NULL, 8, 8, 45.0000, 5.0000, 40.0000, '个', 'normal', '合格', 10.0000, 100.0000, 'C', 0.42),
(4, NULL, 9, 9, 15.0000, 2.0000, 13.0000, '个', 'low', '合格', 20.0000, 80.0000, 'A', 0.88),
(5, NULL, 10, 10, 300.0000, 30.0000, 270.0000, '个', 'normal', '合格', 60.0000, 600.0000, 'B', 0.72);
```

### 3.6 边界和异常场景数据

```sql
-- 边界场景：零库存
INSERT INTO inventory_v3 (warehouse_id, location_id, part_id, quantity, locked_quantity, available_quantity, unit, status, quality_status) VALUES
(1, 1, 11, 0.0000, 0.0000, 0.0000, '个', 'out', '合格');

-- 边界场景：负库存（异常情况，用于测试）
-- 实际业务中应禁止，但可通过事务回滚测试
-- UPDATE inventory_v3 SET quantity = -10 WHERE id = 1;

-- 异常场景：超量锁定
INSERT INTO inventory_v3 (warehouse_id, location_id, part_id, quantity, locked_quantity, available_quantity, unit, status) VALUES
(1, 2, 12, 50.0000, 60.0000, -10.0000, '个', 'abnormal');

-- 边界场景：过期库存
INSERT INTO inventory_v3 (warehouse_id, location_id, part_id, quantity, unit, status, quality_status, expiry_date, shelf_life) VALUES
(1, 3, 13, 100.0000, '个', 'expired', '过期', DATE_SUB(CURDATE(), INTERVAL 30 DAY), 365);

-- 边界场景：接近保质期
INSERT INTO inventory_v3 (warehouse_id, location_id, part_id, quantity, unit, status, quality_status, expiry_date, shelf_life) VALUES
(1, 4, 14, 80.0000, '个', 'normal', '合格', DATE_ADD(CURDATE(), INTERVAL 7 DAY), 365);
```

## 四、测试用例设计

### 4.1 功能测试用例

#### 4.1.1 入库管理测试
```python
# 测试用例 1: 正常入库流程
def test_normal_inbound():
    """测试正常入库流程"""
    # 1. 创建入库单
    order = create_inbound_order({
        'warehouse_id': 1,
        'order_type': 'purchase',
        'supplier_id': 1,
        'items': [...]
    })
    
    # 2. 验收
    inspect_order(order.id, {'result': 'qualified'})
    
    # 3. 上架
    shelve_items(order.id, [{'item_id': 1, 'location_id': 1, 'quantity': 100}])
    
    # 4. 验证库存增加
    inventory = get_inventory(1, 1)
    assert inventory.quantity == 100

# 测试用例 2: 部分入库
def test_partial_inbound():
    """测试部分入库场景"""
    # 计划入库 100 个，实际入库 80 个
    pass

# 测试用例 3: 质检不合格
def test_quality_check_failed():
    """测试质检不合格处理"""
    pass
```

#### 4.1.2 出库管理测试
```python
# 测试用例 1: 正常出库流程
def test_normal_outbound():
    """测试正常出库流程"""
    pass

# 测试用例 2: 库存不足
def test_insufficient_stock():
    """测试库存不足场景"""
    pass

# 测试用例 3: FIFO 出库
def test_fifo_outbound():
    """测试先进先出出库"""
    pass
```

#### 4.1.3 并发测试
```python
# 测试用例 1: 并发入库
def test_concurrent_inbound():
    """测试并发入库操作"""
    pass

# 测试用例 2: 并发出库（超卖测试）
def test_concurrent_outbound():
    """测试并发出库防止超卖"""
    pass
```

### 4.2 性能测试用例

```python
# 性能测试：大批量入库
def test_bulk_inbound_performance():
    """测试 1000 个 SKU 同时入库的性能"""
    pass

# 性能测试：高并发查询
def test_high_concurrency_query():
    """测试 100 并发查询库存"""
    pass
```

## 五、总结与建议

### 5.1 当前系统优势
1. ✅ 数据库模型设计完善，字段覆盖全面
2. ✅ 支持多仓库、多货位管理
3. ✅ 集成 AI 功能（货位推荐、拣货路径优化）
4. ✅ 支持批次管理和保质期管理
5. ✅ 具备基础的库存状态管理

### 5.2 需要改进的方面
1. ❌ 缺少完整的质检流程
2. ❌ 缺少盘点管理功能
3. ❌ 缺少预警规则和通知机制
4. ❌ 缺少波次管理和复核流程
5. ❌ 并发控制需要加强
6. ❌ 缺少数据分析和报表功能

### 5.3 优先级建议

**高优先级（立即实施）：**
1. 完善入库质检流程
2. 实现库存盘点功能
3. 建立预警通知机制
4. 加强并发控制

**中优先级（近期实施）：**
1. 实现波次管理
2. 完善出库复核流程
3. 增加数据分析报表
4. 优化用户操作流程

**低优先级（远期规划）：**
1. 集成条码/RFID 系统
2. 对接物流跟踪系统
3. 实现供应商预约入库
4. 建设可视化仓库平面图
