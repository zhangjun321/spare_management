# _deprecated — 废弃代码归档

这些文件在 Phase 0 代码清理 (F0-5) 中被移入此处，原因：**无任何代码引用、未被注册为蓝图、项目中无实际调用**。

如需恢复，移回原目录即可。这些文件不会影响应用运行。

## 废弃文件清单

### Models (2)
| 文件 | 原路径 | 说明 |
|------|--------|------|
| `inventory_check_simple.py` | `app/models/` | 旧版盘点模型（已由 warehouse_v3 替代） |
| `warehouse_zone_rack.py` | `app/models/` | 未使用的仓库分区/货架模型 |

### Routes (11)
| 文件 | 原路径 | 说明 |
|------|--------|------|
| `quality_check_enhanced.py` | `app/routes/` | 增强质检路由（未被注册） |
| `warehouses_ai_routes.py` | `app/routes/` | 旧版 AI 仓库路由 |
| `warehouse_new_routes.py` | `app/routes/` | 新版仓库路由（未被注册） |
| `warehouse_v3/ai_routes.py` | `app/routes/warehouse_v3/` | warehouse_v3 AI 路由（未在 `__init__.py` 注册） |
| `warehouse_v3/check_routes.py` | `app/routes/warehouse_v3/` | warehouse_v3 盘点路由（未注册） |
| `warehouse_v3/inbound_routes.py` | `app/routes/warehouse_v3/` | warehouse_v3 入库路由（未注册） |
| `warehouse_v3/location_routes.py` | `app/routes/warehouse_v3/` | warehouse_v3 货位路由（未注册） |
| `warehouse_v3/outbound_routes.py` | `app/routes/warehouse_v3/` | warehouse_v3 出库路由（未注册） |
| `warehouse_v3/quality_check_routes.py` | `app/routes/warehouse_v3/` | warehouse_v3 质检路由（未注册） |

### Services (6)
| 文件 | 原路径 | 说明 |
|------|--------|------|
| `ai_location_service.py` | `app/services/` | AI 货位推荐服务（未被调用） |
| `analytics_service.py` | `app/services/` | 数据分析服务（未被调用） |
| `audit_service.py` | `app/services/` | 审计服务（未被调用） |
| `optimized_inbound_service.py` | `app/services/` | 优化入库服务（未被调用） |
| `warehouse_advanced_service.py` | `app/services/` | 高级仓库服务 v1（未被调用） |
| `warehouse_advanced_service_v2.py` | `app/services/` | 高级仓库服务 v2（未被调用） |

---

归档日期: 2026-05-21 | Phase 0 (F0-5)
