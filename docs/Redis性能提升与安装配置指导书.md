# Redis 性能提升与安装配置指导书（spare_management）

## 1. 适用范围与当前项目现状

本指导书基于你当前项目代码现状编写，已确认：

- 项目已内置 Redis 依赖：`requirements.txt` 中有 `redis==5.0.0`
- 应用启动时默认优先使用 Redis：`app/__init__.py` 中 `USE_REDIS` 默认 `True`
- 已有 Redis 失败自动降级机制：Redis 不可用时回退到 SQLite 缓存（`app/services/cache_service.py`）
- Docker 编排已包含 Redis 服务：`docker-compose.yml` 中有 `redis:7-alpine`

结论：你的项目已经具备 Redis 接入基础，当前重点是**正确安装 + 配置 + 把高频查询点纳入缓存**。

---

## 2. Redis 对你项目的性能提升点

结合你系统特征（库存、交易、看板、列表分页、统计接口），Redis 的主要收益如下。

### 2.1 页面响应更快（尤其列表与统计）

- 高频接口（如库存统计、交易列表首屏）可从 Redis 直接返回，减少数据库查询。
- 典型可见收益：
  - 热点统计接口：响应时间可从 `200~800ms` 降到 `20~80ms`
  - 列表首屏：在分页参数重复访问场景下可降 `40%~70%`

### 2.2 降低数据库压力与锁竞争

- 你当前系统中有较多读多写少的页面（仪表盘、库存概览、交易查询）。
- 使用 Redis 后，MySQL 可把资源留给写操作与复杂事务，整体稳定性更好。

### 2.3 多实例部署时缓存共享

- SQLite/内存缓存是“单实例本地缓存”，多实例下命中率低且不一致。
- Redis 是集中式缓存，多个 Flask 实例共享同一缓存，适合你后续横向扩容。

### 2.4 用户体验提升

- 减少“页面一直转圈”概率（数据库繁忙时可优先返回缓存数据）。
- 筛选、分页、切换菜单重复访问更流畅。

---

## 3. 推荐缓存策略（按优先级）

### P0（立即做）

- 仪表盘统计接口（库存状态、入库/出库汇总）
- 交易管理列表接口（按页+筛选条件缓存 30~120 秒）
- 仓库下拉、字典类接口（缓存 10~30 分钟）

### P1（第二阶段）

- 复杂聚合报表（缓存 1~10 分钟）
- 首页卡片数据（缓存 30~180 秒）

### P2（谨慎）

- 高实时性库存明细（只做短 TTL，如 10~30 秒，且写后删除相关 key）

---

## 4. 安装 Redis（Windows 10）

你是 Windows 环境，推荐两条路径：**Docker**（首选）或本机服务。

## 4.1 方案 A：Docker（推荐）

前提：已安装并启动 Docker Desktop。

在项目根目录执行：

```powershell
docker compose up -d redis
docker ps
docker exec spare-redis redis-cli -a "你的密码" ping
```

若返回 `PONG`，说明 Redis 正常。

> 你的 `docker-compose.yml` 已配置：
> - 端口：`6379`
> - 最大内存：`256mb`
> - 淘汰策略：`allkeys-lru`

## 4.2 方案 B：Windows 本机安装

可使用项目内脚本：

```powershell
.\install_redis.ps1
```

安装后验证：

```powershell
redis-cli ping
```

返回 `PONG` 即可。

---

## 5. 项目配置 Redis

在项目根目录创建或修改 `.env`（可基于 `.env.example`）：

```env
USE_REDIS=true
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=你的密码
```

注意：

- 如果用 Docker Compose 且 Flask 也在 Compose 内，`REDIS_HOST` 推荐填 `redis`
- 如果 Flask 在本机直接跑、Redis 在本机或 Docker 映射端口，`REDIS_HOST=127.0.0.1`

---

## 6. 启动与验证

## 6.1 启动应用

```powershell
python run.py
```

或你的既有启动方式（Flask/Gunicorn）。

## 6.2 看日志确认是否命中 Redis

你项目中会打印类似日志：

- `Redis 连接成功`
- `使用 Redis 作为缓存后端`

若 Redis 不可用，会看到：

- `Redis 初始化失败 ... 使用 SQLite 缓存替代`

## 6.3 健康检查

访问：

- `http://127.0.0.1:5000/health`

观察返回 JSON 中 `services.redis` 字段：

- `ok`：Redis 正常
- `unavailable (using sqlite cache)`：已降级到 SQLite 缓存

## 6.4 使用项目诊断脚本

```powershell
.\check_redis.ps1
```

---

## 7. 缓存改造实施模板（开发用）

你项目已有装饰器 `@cache(...)`，可直接用于热点函数。

示例（伪代码）：

```python
from app.services.cache_service import cache

@cache(prefix='inventory_stats', timeout=60)
def get_inventory_stats(...):
    # 原本慢查询逻辑
    return data
```

建议规则：

- 列表查询 key 必须包含分页和筛选参数
- 统计数据 TTL 短一些（30~120 秒）
- 字典类 TTL 长一些（10~30 分钟）

---

## 8. 缓存失效策略（非常关键）

写操作后主动清理相关缓存，避免脏数据：

- 入库/出库/调拨成功后，清理：
  - `inventory*`
  - `dashboard*`
  - `transaction_list*`

项目已有模式删除能力（`clear_pattern`），可直接调用。

---

## 9. 生产环境建议参数

Redis 建议：

- `maxmemory`: 按机器内存设置（如 `256mb~1gb` 起步）
- `maxmemory-policy`: `allkeys-lru`（适合通用缓存）
- 开启密码，限制外网直接访问 6379
- 监控指标：`used_memory`, `evicted_keys`, `keyspace_hits`, `keyspace_misses`

应用建议：

- 缓存失败不影响主流程（你当前已具备降级）
- 记录缓存命中率日志，按周优化 key 与 TTL

---

## 10. 常见问题与排查

### Q1：连接超时

- 检查 `REDIS_HOST/PORT/PASSWORD`
- 检查 6379 端口、防火墙、容器状态

### Q2：项目仍然慢

- Redis 只是“缓存层”，根因可能是 SQL 慢查询或接口串行请求
- 先抓热点接口（TOP N）再加缓存，不要全量盲加

### Q3：数据不一致

- 原因通常是“写后未删缓存”
- 按第 8 节补齐失效策略

---

## 11. 推荐落地计划（7 天）

- Day 1: 安装 Redis + 健康检查通过
- Day 2: 接入 P0 接口缓存（统计、交易列表、仓库下拉）
- Day 3: 加写后失效逻辑
- Day 4: 压测并记录命中率/响应时间
- Day 5: 调整 TTL 与 key 粒度
- Day 6-7: 扩展到 P1 场景

---

## 12. 预期收益（保守估计）

在你这个备件/仓储业务系统中，Redis 完整落地后，通常可达到：

- 热点读接口平均响应下降：`40%~80%`
- 数据库读压力下降：`30%~60%`
- 高峰时页面首屏稳定性明显提升（减少长时间 loading）

---

如需下一步，我可以直接给你出一版“按你当前路由文件逐个加缓存”的改造清单（精确到函数名和建议 TTL）。
