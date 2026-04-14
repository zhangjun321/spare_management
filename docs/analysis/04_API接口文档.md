# 备件管理系统 API 接口文档

**版本**：v1.0  
**日期**：2026-04-14  
**Base URL**：`/api`  
**认证方式**：Session Cookie（Flask-Login）+ CSRF Token（X-CSRFToken Header）  
**响应格式**：`application/json`

---

## 通用规范

### 请求头

```
Content-Type: application/json
X-CSRFToken: <csrf_token>        # POST/PUT/DELETE 请求必须携带
```

### 统一响应格式

**成功响应：**

```json
{
    "success": true,
    "data": { ... },
    "message": "操作成功",
    "meta": {
        "total": 100,
        "page": 1,
        "per_page": 20,
        "pages": 5
    }
}
```

**错误响应：**

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "备件代码已存在",
        "details": {
            "field": "part_code",
            "value": "SP-001"
        }
    }
}
```

### HTTP 状态码约定

| 状态码 | 含义 |
|--------|------|
| 200 | 成功（查询/更新） |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未登录 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如重复编号） |
| 422 | 业务逻辑校验失败 |
| 500 | 服务器内部错误 |

### 分页参数（GET 请求通用）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| per_page | int | 20 | 每页数量（最大100） |
| sort_by | string | created_at | 排序字段 |
| sort_order | string | desc | asc / desc |

---

## 一、备件管理 API

> **Blueprint 前缀**：`/api/spare-parts`  
> **文件**：`app/routes/api_spare_parts.py`

### 1.1 获取备件列表

```
GET /api/spare-parts/
```

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| q | string | 搜索关键词（名称/代码/条形码） |
| category_id | int | 分类ID筛选 |
| warehouse_id | int | 仓库ID筛选 |
| stock_status | string | 库存状态：out/low/normal/overstocked |
| is_active | bool | 是否启用 |
| abc_class | string | ABC分类：A/B/C |
| is_critical | bool | 是否关键备件 |

**响应示例：**

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "part_code": "SP-2024-001",
            "name": "轴承 6205-2RS",
            "specification": "25×52×15",
            "category": {"id": 3, "name": "轴承"},
            "warehouse": {"id": 1, "name": "主仓库"},
            "current_stock": 50,
            "stock_status": "normal",
            "min_stock": 10,
            "max_stock": 100,
            "unit_price": "12.50",
            "unit": "个",
            "brand": "SKF",
            "abc_class": "A",
            "is_critical": true,
            "thumbnail_url": "/uploads/thumbnails/SP-2024-001.jpg",
            "is_active": true,
            "updated_at": "2026-04-14T08:00:00"
        }
    ],
    "meta": {"total": 256, "page": 1, "per_page": 20, "pages": 13}
}
```

---

### 1.2 获取备件详情

```
GET /api/spare-parts/{id}
```

**响应示例：**

```json
{
    "success": true,
    "data": {
        "id": 1,
        "part_code": "SP-2024-001",
        "name": "轴承 6205-2RS",
        "specification": "25×52×15",
        "category_id": 3,
        "category": {"id": 3, "name": "轴承", "code": "BEAR"},
        "supplier_id": 2,
        "supplier": {"id": 2, "name": "SKF中国"},
        "warehouse_id": 1,
        "location_id": 5,
        "current_stock": 50,
        "stock_status": "normal",
        "min_stock": 10,
        "max_stock": 100,
        "safety_stock": 15,
        "reorder_point": 20,
        "unit": "个",
        "unit_price": "12.50",
        "last_purchase_price": "11.80",
        "currency": "CNY",
        "brand": "SKF",
        "barcode": "6901234567890",
        "warranty_period": 24,
        "lead_time_days": 7,
        "abc_class": "A",
        "is_critical": true,
        "criticality_level": "critical",
        "annual_usage_qty": 200,
        "annual_usage_value": "2500.00",
        "turnover_rate": "4.00",
        "technical_params": {
            "inner_diameter": "25mm",
            "outer_diameter": "52mm",
            "width": "15mm",
            "material": "铬钢"
        },
        "image_url": "/uploads/SP-2024-001.jpg",
        "thumbnail_url": "/uploads/thumbnails/SP-2024-001.jpg",
        "datasheet_url": "/uploads/datasheets/SP-2024-001.pdf",
        "remark": "高频消耗备件，保持充足库存",
        "is_active": true,
        "created_at": "2024-01-10T09:00:00",
        "updated_at": "2026-04-14T08:00:00"
    }
}
```

---

### 1.3 创建备件

```
POST /api/spare-parts/
```

**请求体：**

```json
{
    "part_code": "SP-2024-099",
    "name": "轴承 6210-2Z",
    "specification": "50×90×20",
    "category_id": 3,
    "supplier_id": 2,
    "warehouse_id": 1,
    "min_stock": 5,
    "max_stock": 50,
    "safety_stock": 8,
    "reorder_point": 10,
    "unit": "个",
    "unit_price": 28.50,
    "brand": "NSK",
    "lead_time_days": 14,
    "is_critical": false,
    "technical_params": {"inner_diameter": "50mm"},
    "remark": ""
}
```

**必填字段**：`part_code`、`name`

**响应：** `201 Created`

```json
{
    "success": true,
    "data": {"id": 99, "part_code": "SP-2024-099"},
    "message": "备件创建成功"
}
```

---

### 1.4 更新备件

```
PUT /api/spare-parts/{id}
```

请求体同创建，字段均为可选（PATCH 语义）。

**响应：** `200 OK`

---

### 1.5 删除备件

```
DELETE /api/spare-parts/{id}
```

> 软删除：将 `is_active` 置为 `false`，保留历史记录。  
> 若存在库存（`current_stock > 0`），拒绝删除（422）。

**响应：**

```json
{"success": true, "message": "备件已停用"}
```

---

### 1.6 条形码查询

```
GET /api/spare-parts/barcode/{barcode}
```

**响应：** 返回单个备件详情对象（同 1.2）。  
未找到时返回 `404`。

---

### 1.7 批量导入

```
POST /api/spare-parts/import
Content-Type: multipart/form-data
```

**表单参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | Excel/CSV 文件，最大 10MB |
| update_existing | bool | 否 | 是否更新已存在的备件（默认 false） |

**响应：** `202 Accepted`

```json
{
    "success": true,
    "data": {
        "task_id": 5,
        "task_no": "IMP-20260414-0001",
        "status": "processing",
        "message": "导入任务已提交，正在后台处理"
    }
}
```

---

### 1.8 查询导入任务状态

```
GET /api/spare-parts/import/{task_id}
```

**响应：**

```json
{
    "success": true,
    "data": {
        "task_id": 5,
        "task_no": "IMP-20260414-0001",
        "status": "completed",
        "total_rows": 100,
        "success_rows": 95,
        "failed_rows": 3,
        "skipped_rows": 2,
        "result_file_url": "/api/spare-parts/import/5/download",
        "completed_at": "2026-04-14T08:05:30"
    }
}
```

---

### 1.9 导出备件列表

```
GET /api/spare-parts/export
```

**查询参数**：同列表接口，另加：

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| format | string | xlsx | 导出格式：xlsx / csv |
| fields | string | all | 导出字段（逗号分隔），all 表示全部 |

**响应**：`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` 文件流。

---

## 二、调拨管理 API

> **Blueprint 前缀**：`/api/transfer`  
> **文件**：`app/routes/api_transfer.py`（新建）

### 2.1 获取调拨单列表

```
GET /api/transfer/orders
```

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | draft/pending/approved/in_transit/completed/cancelled |
| from_warehouse_id | int | 调出仓库 |
| to_warehouse_id | int | 调入仓库 |
| date_from | date | 创建日期起始（YYYY-MM-DD） |
| date_to | date | 创建日期结束 |

**响应示例：**

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "order_no": "DB-20260414-0001",
            "from_warehouse": {"id": 1, "name": "主仓库"},
            "to_warehouse": {"id": 2, "name": "车间仓库"},
            "transfer_type": "normal",
            "status": "approved",
            "priority": 2,
            "item_count": 3,
            "total_quantity": 50,
            "estimated_arrival": "2026-04-16",
            "created_by_name": "张三",
            "approved_by_name": "李四",
            "created_at": "2026-04-14T08:00:00"
        }
    ],
    "meta": {"total": 28, "page": 1, "per_page": 20, "pages": 2}
}
```

---

### 2.2 创建调拨单

```
POST /api/transfer/orders
```

**请求体：**

```json
{
    "from_warehouse_id": 1,
    "to_warehouse_id": 2,
    "from_location_id": null,
    "to_location_id": null,
    "transfer_type": "normal",
    "priority": 2,
    "reason": "车间备件库存不足，从主仓库补充",
    "estimated_arrival": "2026-04-16",
    "items": [
        {
            "spare_part_id": 1,
            "planned_quantity": 20,
            "batch_number": "BATCH-2025-001",
            "from_location_id": 5
        },
        {
            "spare_part_id": 3,
            "planned_quantity": 10
        }
    ]
}
```

**业务校验：**
- `from_warehouse_id != to_warehouse_id`
- 调出仓库对应备件可用库存 ≥ `planned_quantity`
- `items` 不能为空

**响应：** `201 Created`

```json
{
    "success": true,
    "data": {
        "id": 1,
        "order_no": "DB-20260414-0001",
        "status": "draft"
    },
    "message": "调拨单创建成功"
}
```

---

### 2.3 获取调拨单详情

```
GET /api/transfer/orders/{id}
```

**响应：** 返回完整调拨单信息，包含明细列表。

---

### 2.4 提交审批

```
POST /api/transfer/orders/{id}/submit
```

状态变更：`draft → pending`

```json
{"remark": "请尽快审批"}
```

---

### 2.5 审批调拨单

```
POST /api/transfer/orders/{id}/approve
```

**权限要求**：仓库管理员或管理员角色

```json
{
    "action": "approve",
    "comment": "同意调拨，请安排发货"
}
```

`action` 取值：`approve`（批准）/ `reject`（驳回）

状态变更：
- 批准：`pending → approved`
- 驳回：`pending → draft`（退回修改）

---

### 2.6 确认发货（调出仓库操作）

```
POST /api/transfer/orders/{id}/ship
```

```json
{
    "carrier": "顺丰速运",
    "tracking_no": "SF1234567890",
    "items": [
        {"item_id": 1, "actual_quantity": 20},
        {"item_id": 2, "actual_quantity": 10}
    ]
}
```

**触发动作**：
1. 生成出库单（`outbound_order`），类型 `transfer`
2. 扣减调出仓库库存
3. 状态变更：`approved → in_transit`

---

### 2.7 确认收货（调入仓库操作）

```
POST /api/transfer/orders/{id}/receive
```

```json
{
    "items": [
        {"item_id": 1, "received_quantity": 20, "to_location_id": 8},
        {"item_id": 2, "received_quantity": 10, "to_location_id": 9}
    ],
    "remark": "货物完好"
}
```

**触发动作**：
1. 生成入库单（`inbound_order`），类型 `transfer`
2. 增加调入仓库库存
3. 状态变更：`in_transit → completed`

---

### 2.8 取消调拨单

```
POST /api/transfer/orders/{id}/cancel
```

```json
{"reason": "需求变更，不再需要调拨"}
```

> 仅 `draft`、`pending` 状态可取消；`in_transit` 及以后不可取消。

---

## 三、报表中心 API

> **Blueprint 前缀**：`/api/reports`  
> **文件**：`app/routes/api_reports.py`（新建）

### 3.1 获取报表模板列表

```
GET /api/reports/templates
```

**响应：**

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "name": "库存汇总报表",
            "code": "inventory_summary",
            "type": "table",
            "category": "inventory",
            "is_builtin": true
        }
    ]
}
```

---

### 3.2 执行报表查询

```
POST /api/reports/query
```

**请求体：**

```json
{
    "template_code": "inventory_summary",
    "filters": {
        "warehouse_id": 1,
        "category_id": null,
        "date_from": "2026-01-01",
        "date_to": "2026-04-14",
        "stock_status": ["low", "out"]
    },
    "group_by": "category",
    "page": 1,
    "per_page": 50
}
```

**内置报表 `template_code` 列表：**

| code | 报表名称 |
|------|---------|
| `inventory_summary` | 库存汇总报表 |
| `low_stock_alert` | 低库存预警报表 |
| `turnover_analysis` | 库存周转率分析 |
| `purchase_execution` | 采购执行情况报表 |
| `supplier_performance` | 供应商绩效报表 |
| `transfer_execution` | 调拨执行报表 |
| `abc_analysis` | ABC分类分析 |
| `stock_age_analysis` | 库龄分析报表 |

**响应示例（库存汇总）：**

```json
{
    "success": true,
    "data": {
        "columns": [
            {"key": "category_name", "label": "分类", "type": "string"},
            {"key": "part_count",    "label": "备件种数", "type": "number"},
            {"key": "total_stock",   "label": "总库存", "type": "number"},
            {"key": "total_value",   "label": "库存金额", "type": "currency"},
            {"key": "low_stock_count","label": "低库存数", "type": "number"}
        ],
        "rows": [
            {
                "category_name": "轴承",
                "part_count": 25,
                "total_stock": 1250,
                "total_value": "15625.00",
                "low_stock_count": 3
            }
        ],
        "summary": {
            "total_parts": 256,
            "total_stock": 8960,
            "total_value": "125680.00"
        }
    },
    "meta": {"total": 12, "page": 1, "per_page": 50, "pages": 1}
}
```

---

### 3.3 导出报表

```
POST /api/reports/export
```

**请求体：**

```json
{
    "template_code": "inventory_summary",
    "filters": { ... },
    "format": "xlsx",
    "title": "2026年Q1库存汇总"
}
```

**响应**：Excel/CSV 文件流（Content-Disposition: attachment）。

---

### 3.4 获取仪表盘数据

```
GET /api/reports/dashboard
```

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| warehouse_id | int | 可选，不传则全局统计 |
| period | string | week/month/quarter/year，默认 month |

**响应：**

```json
{
    "success": true,
    "data": {
        "kpi": {
            "total_parts": 256,
            "total_stock_value": "125680.00",
            "low_stock_count": 12,
            "out_of_stock_count": 3,
            "pending_purchase_count": 5,
            "pending_transfer_count": 2,
            "expiry_warning_count": 8,
            "stock_age_warning_count": 15
        },
        "stock_status_chart": {
            "labels": ["正常", "低库存", "缺货", "超储"],
            "values": [210, 32, 8, 6]
        },
        "category_distribution": [
            {"name": "轴承", "value": 25, "stock_value": "15625.00"},
            {"name": "密封件", "value": 38, "stock_value": "9860.00"}
        ],
        "monthly_trend": {
            "labels": ["2026-01", "2026-02", "2026-03", "2026-04"],
            "inbound": [120, 85, 200, 95],
            "outbound": [98, 110, 145, 60]
        },
        "recent_warnings": [
            {
                "type": "low_stock",
                "part_code": "SP-2024-001",
                "part_name": "轴承 6205-2RS",
                "current_stock": 5,
                "min_stock": 10,
                "created_at": "2026-04-14T06:00:00"
            }
        ]
    }
}
```

---

### 3.5 ABC 分析接口

```
POST /api/reports/abc-analysis
```

**请求体：**

```json
{
    "date_from": "2025-04-14",
    "date_to": "2026-04-14",
    "warehouse_id": null,
    "a_threshold": 70,
    "b_threshold": 90
}
```

> `a_threshold`：前 70% 金额归为 A 类；`b_threshold`：70%~90% 归为 B 类；其余为 C 类。

**触发动作**：计算完成后将 `abc_class` 写入 `spare_part` 表。

**响应：**

```json
{
    "success": true,
    "data": {
        "summary": {
            "A": {"count": 30, "value_pct": 70.2, "qty_pct": 11.7},
            "B": {"count": 68, "value_pct": 20.1, "qty_pct": 26.6},
            "C": {"count": 158, "value_pct": 9.7, "qty_pct": 61.7}
        },
        "updated_count": 256,
        "analysis_date": "2026-04-14"
    }
}
```

---

## 四、批量导入 API

> **Blueprint 前缀**：`/api/import`

### 4.1 下载导入模板

```
GET /api/import/template/{type}
```

`type` 取值：`spare_part` / `inventory` / `supplier`

**响应**：Excel 模板文件下载。

---

### 4.2 提交导入任务

```
POST /api/import/tasks
Content-Type: multipart/form-data
```

**表单参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | xlsx / csv，最大 10MB |
| import_type | string | 是 | spare_part / inventory / supplier |
| update_existing | bool | 否 | 是否覆盖已有数据（默认 false） |
| warehouse_id | int | 否 | 导入库存时指定默认仓库 |

---

### 4.3 查询导入任务列表

```
GET /api/import/tasks
```

---

### 4.4 下载导入结果（含错误明细）

```
GET /api/import/tasks/{task_id}/download
```

**响应**：包含错误详情的 Excel 文件。

---

## 五、采购管理 API

> **Blueprint 前缀**：`/api/purchase`  
> **注意**：采购模型已存在（`app/models/purchase.py`），此处仅补充缺失的 API 端点。

### 5.1 获取采购申请列表

```
GET /api/purchase/requests
```

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | pending/approved/rejected/completed |
| spare_part_id | int | 备件ID |
| date_from | date | 申请日期起始 |

---

### 5.2 创建采购申请

```
POST /api/purchase/requests
```

**请求体：**

```json
{
    "spare_part_id": 1,
    "quantity": 50,
    "estimated_price": 12.50,
    "reason": "库存低于安全库存，需补货",
    "plan_id": null
}
```

---

### 5.3 审批采购申请

```
POST /api/purchase/requests/{id}/approve
```

```json
{
    "action": "approve",
    "comment": "批准采购"
}
```

---

### 5.4 获取采购订单列表

```
GET /api/purchase/orders
```

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | pending/confirmed/delivered/completed/cancelled |
| supplier_id | int | 供应商 |
| delivery_status | string | pending/partial/completed |
| payment_status | string | unpaid/partial/paid |

---

### 5.5 创建采购订单

```
POST /api/purchase/orders
```

**请求体：**

```json
{
    "supplier_id": 2,
    "title": "SKF轴承采购",
    "contract_no": "HT-2026-001",
    "expected_delivery_date": "2026-04-30",
    "payment_terms": "月结30天",
    "items": [
        {
            "spare_part_id": 1,
            "request_id": 5,
            "quantity": 50,
            "unit_price": 11.80
        }
    ],
    "remark": ""
}
```

---

### 5.6 确认收货

```
POST /api/purchase/orders/{id}/receive
```

**请求体：**

```json
{
    "items": [
        {
            "order_item_id": 1,
            "received_quantity": 48,
            "warehouse_id": 1,
            "location_id": 5,
            "batch_number": "BATCH-2026-SKF-001",
            "production_date": "2026-01-15",
            "expiry_date": "2030-01-15",
            "quality_check": true,
            "quality_status": "passed"
        }
    ],
    "invoice_no": "FP-2026-SKF-001",
    "remark": "2个外包装轻微破损，零件完好"
}
```

**触发动作**：
1. 生成入库单（类型 `purchase`）
2. 更新库存记录
3. 更新采购订单 `delivery_status`
4. 更新备件 `last_purchase_price` 和 `last_purchase_date`

---

## 六、仓库管理 API

> **Blueprint 前缀**：`/api/warehouse`（现有，补充新端点）

### 6.1 获取仓库统计概览

```
GET /api/warehouse/{id}/statistics
```

**响应：**

```json
{
    "success": true,
    "data": {
        "warehouse_id": 1,
        "warehouse_name": "主仓库",
        "total_inventory": 8960,
        "total_spare_parts": 156,
        "utilization_rate": 73.5,
        "total_value": "98650.00",
        "location_count": 200,
        "occupied_locations": 147,
        "stock_status_breakdown": {
            "normal": 130,
            "low": 18,
            "out": 5,
            "overstocked": 3
        },
        "recent_inbound_7d": 320,
        "recent_outbound_7d": 280,
        "last_inventory_date": "2026-03-31"
    }
}
```

---

## 七、批次追溯 API

> **Blueprint 前缀**：`/api/batch`

### 7.1 获取备件批次列表

```
GET /api/batch/spare-parts/{spare_part_id}
```

**响应：**

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "batch_number": "BATCH-2025-001",
            "warehouse": {"id": 1, "name": "主仓库"},
            "quantity": 30,
            "original_quantity": 50,
            "unit_cost": "11.80",
            "production_date": "2025-06-01",
            "expiry_date": "2029-06-01",
            "fifo_sequence": 1,
            "fefo_flag": false,
            "is_consumed": false,
            "supplier_batch_no": "SKF-2025-BATCH-A",
            "inbound_order_no": "IN-20250610-001",
            "created_at": "2025-06-10T09:30:00"
        }
    ]
}
```

---

### 7.2 批次谱系追溯

```
GET /api/batch/{batch_number}/genealogy
```

返回该批次的完整流转历史（入库→出库→调拨链路）。

---

## 八、系统配置 API

> **Blueprint 前缀**：`/api/system`（现有，补充）

### 8.1 获取/更新仪表盘配置

```
GET  /api/system/dashboard-config
PUT  /api/system/dashboard-config
```

**请求体（PUT）：**

```json
{
    "layout": "grid",
    "widgets": [
        {"id": "kpi_cards",      "enabled": true,  "order": 1},
        {"id": "stock_chart",    "enabled": true,  "order": 2},
        {"id": "warning_list",   "enabled": true,  "order": 3},
        {"id": "abc_chart",      "enabled": false, "order": 4}
    ],
    "default_warehouse_id": 1,
    "refresh_interval": 300
}
```

---

## 九、移动端 API

> **Blueprint 前缀**：`/api/mobile`

### 9.1 扫码查询备件

```
GET /api/mobile/scan/{barcode}
```

**响应：** 返回备件基本信息 + 当前库存 + 所在货位。

---

### 9.2 扫码快速出库

```
POST /api/mobile/quick-outbound
```

**请求体：**

```json
{
    "barcode": "6901234567890",
    "quantity": 1,
    "warehouse_id": 1,
    "reason": "设备维修"
}
```

**响应：** 生成出库单，返回出库单号。

---

### 9.3 扫码快速入库（扫采购单/入库单二维码）

```
POST /api/mobile/quick-inbound
```

```json
{
    "inbound_order_no": "IN-20260414-001",
    "barcode": "6901234567890",
    "received_quantity": 10,
    "location_id": 5
}
```

---

## 十、错误码参考

| 错误码 | HTTP状态 | 说明 |
|--------|---------|------|
| `INVALID_PARAMS` | 400 | 请求参数格式错误 |
| `REQUIRED_FIELD_MISSING` | 400 | 必填字段缺失 |
| `UNAUTHORIZED` | 401 | 未登录或Session过期 |
| `FORBIDDEN` | 403 | 无操作权限 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `DUPLICATE_CODE` | 409 | 编号重复（备件代码/单号等） |
| `INSUFFICIENT_STOCK` | 422 | 库存不足 |
| `INVALID_STATUS_TRANSITION` | 422 | 状态流转不合法 |
| `STOCK_EXISTS` | 422 | 存在库存，不能删除 |
| `SAME_WAREHOUSE` | 422 | 调出调入仓库相同 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

---

*本文档基于现有代码结构（Flask Blueprint + SQLAlchemy）设计，新增 API 路由需在 `app/__init__.py` 的 `register_blueprints()` 函数中注册对应蓝图。*
