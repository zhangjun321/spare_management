## 备件管理模块扩展开发与部署方案（10 大功能）

### 1. 目标与范围
- **目标**：在现有备件管理系统上扩展 10 个高价值功能，提升供应连续性、作业效率、风险预警与审计可控性。
- **范围**：后端 Flask + MySQL + APScheduler；前端 React + Zustand；不涉及数据库结构大规模重构，新增表/字段保持向后兼容。

### 2. 新功能清单与设计要点
1) **备件智能推荐与替代件**
- 业务：缺货时推荐替代件/兼容型号，支持手工维护与自动相似度（基于品牌/规格/接口）。
- 数据：新增表 `spare_part_substitute(id, part_id, substitute_id, score, created_at)`；在 `spare_part` 增加可选“相似度标签”字段（如 category/接口/功率）。
- 服务/API：
  - GET `/api/spare-parts/{id}/substitutes` 获取推荐/配置的替代件
  - POST `/api/spare-parts/{id}/substitutes` 维护替代关系
  - GET `/api/spare-parts/recommend?part_code=` 智能推荐（评分排序）
- 前端：出库/下单/低库存弹窗展示“可替代件”推荐卡片，支持一键替换。

2) **多仓/多库区调拨与在途库存**
- 业务：跨仓/库区调拨，状态机（draft→approved→in_transit→received）。
- 数据：新增 `transfer_order(id, code, from_wh, to_wh, status, requester, approver, created_at, updated_at, eta)`、`transfer_order_item(id, transfer_id, spare_part_id, quantity, batch_no, status)`；`inventory_record` 增加 `in_transit_quantity` 字段或通过聚合视图计算。
- 服务/API：
  - POST `/api/transfer-orders` 创建调拨单；POST `/api/transfer-orders/{id}/approve|ship|receive`
  - GET `/api/transfer-orders` 列表/筛选；GET `/api/transfer-orders/{id}` 详情+时间线
- 前端：新页面“调拨单列表/详情/执行”，在库存详情显示“在途量”。

3) **备件健康度与寿命预测**
- 业务：基于消耗频次、故障/替换记录（若有）、平均寿命，计算健康分与预计失效时间；高风险预警。
- 数据：新增表 `spare_part_health(part_id, health_score, predicted_eol_date, reason, updated_at)`；在现有日志/工单（如有）读取使用数据。
- 服务/API：
  - 定时任务每日计算（APScheduler）
  - GET `/api/spare-parts/{id}/health` 返回健康度与建议
- 前端：仪表盘“高风险件 TopN”，详情页展示趋势/更新时间。

4) **维修工单直连备件领用/归还**
- 业务：工单消耗闭环，出库需绑定工单；完工可归还或报废确认。
- 数据：新增 `work_order_part(id, work_order_id, spare_part_id, quantity, returned_qty, scrapped_qty, status)`。
- 服务/API：
  - 出库接口增加 `work_order_id` 参数；校验工单状态
  - POST `/api/work-orders/{id}/parts/return` 归还；`/scrap` 报废
- 前端：出库弹窗可搜索工单；工单详情显示备件耗用记录。

5) **低库存自动采购建议与审批**
- 业务：基于安全库存/再订货点/移动平均消耗生成采购建议；多级审批。
- 数据：新增 `purchase_suggestion(id, part_id, suggested_qty, reason, generated_at)`、`purchase_request(id, code, status, approver_id, total_amount)`、`purchase_request_item`。
- 服务/API：
  - 定时任务生成建议；一键转采购申请
  - 审批流：`/approve` `/reject`
- 前端：低库存页“生成采购建议”按钮；申请单列表与审批流界面。

6) **批次/效期管控（FIFO/FEFO 配置）**
- 业务：仓库或物料级策略（FIFO/FEFO）；拣货时按策略锁定批次；近效期/过期阻断。
- 数据：在 `warehouse` 或 `spare_part` 增加字段 `picking_strategy`(fifo|fefo|manual)。
- 服务/API：
  - 出库/拣货接口返回“建议批次”列表；校验策略
  - 近效期阈值参数化（默认 30 天）
- 前端：拣货弹窗显示策略与锁定批次；拒绝违规批次选择。

7) **条码/二维码一物一码 + 移动端扫码作业**
- 业务：批次或单件级码，入库/出库/盘点扫码校验；记录扫码日志。
- 数据：新增 `item_code(id, code, part_id, batch_no, status, bound_record_id, created_at)`；`scan_log`。
- 服务/API：
  - 生成/打印码接口；验证码接口；批量绑定
- 前端：H5/PWA 扫码组件，入库/出库/盘点界面支持扫码录入。

8) **库存占用/预留（项目/订单维度）**
- 业务：预留量从可用库存中扣减，非实际出库；有到期时间和优先级，到期自动释放。
- 数据：新增 `reservation(id, part_id, warehouse_id, quantity, project, expire_at, status, priority)`。
- 服务/API：
  - POST `/api/reservations` 创建；POST `/api/reservations/{id}/release|extend`
  - 可用量 = 物理库存 - 在途冻结 - 预留量
- 前端：库存列表展示“可用/预留/在途”；详情页可释放/延长。

9) **库存异常检测与审计追踪**
- 业务：检测异常模式（短时大量出库、频繁撤销、深夜操作等）；生成审计告警。
- 数据：扩展审计日志表或新增 `audit_alert(id, rule, object_type, object_id, level, status, created_at)`。
- 服务/API：
  - 定时任务执行规则；手动触发
  - GET `/api/audit-alerts` 列表，支持处置记录
- 前端：审计告警列表卡片，标注原因与处理按钮。

10) **可配置盘点任务与差异处理**
- 业务：创建盘点任务（范围：仓库/库区/品类），扫码盘点，多人并行；差异生成调整单，需审批。
- 数据：新增 `stock_take_task(id, code, scope, status, assignees, created_at, deadline)`、`stock_take_item(task_id, part_id, batch_no, system_qty, counted_qty, location_id)`、`adjustment_order`。
- 服务/API：
  - 任务 CRUD；提交盘点结果；生成差异调整单并审批
- 前端：盘点看板、任务详情、差异处理流，支持扫码。

### 3. 后端总体改造
- **框架/依赖**：沿用 Flask + SQLAlchemy + APScheduler；如需二维码生成可复用 `Pillow` 或新增 `qrcode` 包（建议加入 requirements）。
- **数据库原则**：新增表保持独立；对现有表仅新增少量字段（策略、在途量等），保证向后兼容。新增字段需提供默认值并在迁移脚本中设定。
- **服务层**：为每个功能新增独立 service 与路由模块，避免臃肿；事件/定时任务集中在 scheduler 注册。
- **事务与一致性**：调拨、预留、盘点、出库等操作需在单事务内写操作（创建单据 + 库存变更 + 日志）。
- **审计与日志**：所有状态流转写入操作日志，关键操作写入审计告警或安全日志。

### 4. 前端改造要点
- **路由/页面**：新增调拨、采购建议/申请、审计告警、盘点任务、扫码作业页面；在现有库存/备件详情中插入“可替代件”“预留/在途”信息块。
- **状态管理（Zustand）**：为调拨单、采购建议、审计告警、盘点任务等新增 store，带 TTL 缓存；复用现有列表 store 设计模式。
- **组件**：
  - 通用时间线/状态标签组件（复用在调拨、采购、盘点）。
  - 批次/策略选择器；扫码输入组件；审批流弹窗组件。
- **UX**：出库/拣货/预留流程要给出阻断式校验与明确错误提示；表格支持批量操作与导出。

### 5. API 与数据模型变更汇总（优先级顺序）
- P1：调拨单、预留、采购建议+申请、批次策略、盘点任务
- P2：替代件推荐、扫码一物一码、审计告警、健康度
- P3：可选的高级推荐（相似度模型迭代）

建议先落库表：`transfer_order*`、`reservation`、`purchase_suggestion/purchase_request*`、`stock_take_task/stock_take_item/adjustment_order`、`audit_alert`、`item_code/scan_log`、`spare_part_substitute`、`spare_part_health`。

### 6. 里程碑与迭代计划
- **里程碑 M1（1 周）**：数据表与迁移脚本；调拨/预留/采购建议接口雏形；前端列表框架与 store 雏形；基础部署流水线打通。
- **里程碑 M2（1-2 周）**：盘点任务闭环；批次策略拣货校验；审计规则最小集；扫码作业 MVP；前端页面可用。
- **里程碑 M3（1 周）**：替代件推荐/健康度评分；UX 打磨；报表与导出；性能与安全加固。

### 7. 测试与质量保障
- **单元/集成测试**：service 层事务、状态机、库存结算、批次校验；定时任务可使用 freeze_time 方案；二维码/扫码接口校验码值与绑定。
- **E2E**：调拨-在途-入库、预留-出库-释放、盘点-差异-调整、采购建议-申请-审批；移动端扫码流程。
- **数据校验**：关键字段非空/范围；批次/策略校验阻断；并发下的库存可用量一致性。

### 8. 部署与运维（建议）
- **后端**：保持 Flask + Gunicorn；如需长轮询/大并发可考虑 async worker；定时任务使用 APScheduler，确保单实例调度或使用分布式锁（如 Redis）。
- **前端**：Vite 构建后静态资源可部署到 CDN/静态站点，反向代理转发 API；生产开启 gzip/brotli。
- **配置**：新增功能相关的阈值（近效期天数、预留过期默认、审计规则开关）写入 `.env` 或配置表；敏感配置走环境变量。
- **迁移**：使用 Alembic 生成迁移脚本；逐环境执行；提供回滚脚本。
- **监控**：APScheduler 任务日志、失败重试；审计告警落库并推送；关键接口的 APM/错误率监控。

### 9. 开发优先级与落地顺序（推荐）
1) 落库表 + 迁移脚本（P1 集合）
2) 调拨、预留、采购建议接口与前端列表
3) 盘点任务 + 差异调整闭环
4) 批次策略与拣货校验
5) 扫码一物一码（最小化：入/出库扫码）
6) 审计告警基础规则
7) 替代件推荐 + 健康度

### 10. 环境与依赖补充
- 如需二维码生成：`qrcode[pil]==7.4.2`（可加入 requirements）。
- 如需缓存/分布式锁：启用 Redis，任务锁前缀 `scheduler:lock:*`。

### 11. 待办跟踪（落地用）
- DB 迁移脚本（P1 表集）
- 调拨/预留/采购建议 API 与单元测试
- 盘点任务闭环 + 前端页面
- 批次策略校验 + 出库/拣货 UI
- 扫码一物一码 MVP
- 审计规则与告警列表
- 替代件推荐/健康度

本文档用于指导后续迭代与分工，落地时请结合实际数据与权限模型微调。
