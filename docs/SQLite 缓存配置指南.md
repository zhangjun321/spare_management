# SQLite 缓存配置指南

## 📖 简介

**SQLite 缓存**是 Redis 的零依赖替代方案，无需安装任何外部服务。

**核心优势**:
- ✅ 零依赖 - 仅需 Python 标准库
- ✅ 数据持久化 - 自动保存到磁盘
- ✅ 支持过期时间 - 自动清理过期缓存
- ✅ 线程安全 - 使用锁机制保证并发安全
- ✅ 完全兼容 - 与 Redis 缓存接口一致

**适用场景**:
- Windows 老版本系统
- 开发/测试环境
- 小规模生产环境
- 无外部依赖要求

---

## 一、自动配置

### 1.1 系统自动选择

系统现在会自动检测并选择缓存后端：

```
优先级:
1. Redis (如果可用)
2. SQLite (Redis 不可用时自动降级)
```

### 1.2 配置选项

修改 `.env` 文件：

```env
# 缓存配置
USE_REDIS=false  # 设置为 false 强制使用 SQLite
CACHE_DB_PATH=cache.db  # SQLite 数据库文件路径
```

---

## 二、手动配置

### 2.1 修改应用配置

修改 `app/config.py`：

```python
class Config:
    # ...现有配置...
    
    # SQLite 缓存配置
    CACHE_TYPE = 'sqlite'
    CACHE_DB_PATH = os.path.join(BASE_DIR, 'cache.db')
    CACHE_DEFAULT_TIMEOUT = 300  # 5 分钟
```

### 2.2 缓存服务初始化

修改 `app/__init__.py`（已自动完成）：

```python
from app.services.cache_service import SQLiteCacheService

# 初始化 SQLite 缓存
sqlite_cache = SQLiteCacheService()
sqlite_cache.init_app(app)
app.extensions['cache'] = sqlite_cache
```

---

## 三、使用示例

### 3.1 基础使用

```python
from app.services.cache_service import cache_service

# 设置缓存
cache_service.set('my_key', {'data': 'value'}, timeout=300)

# 获取缓存
data = cache_service.get('my_key')

# 删除缓存
cache_service.delete('my_key')

# 检查是否存在
exists = cache_service.exists('my_key')
```

### 3.2 使用装饰器

```python
from app.services.cache_service import cache

# 自动缓存函数结果
@cache(prefix='warehouse', timeout=300)
def get_warehouse_list(warehouse_id):
    # 函数逻辑
    return data

# 使用自定义键
@cache(key='warehouse:{id}', timeout=300)
def get_warehouse_by_id(warehouse_id):
    # 函数逻辑
    return data
```

### 3.3 API 路由示例

```python
from flask import Blueprint, jsonify
from app.services.cache_service import cache_service

@api_warehouses_bp.route('/list', methods=['GET'])
def list_warehouses():
    cache_key = 'warehouse_list'
    
    # 尝试从缓存获取
    cached_data = cache_service.get(cache_key)
    if cached_data:
        return jsonify(cached_data)
    
    # 从数据库查询
    warehouses = Warehouse.query.all()
    data = [w.to_dict() for w in warehouses]
    
    # 存入缓存
    cache_service.set(cache_key, data, timeout=300)
    
    return jsonify(data)
```

---

## 四、数据库结构

### 4.1 缓存表结构

SQLite 缓存数据库包含一个表：

```sql
CREATE TABLE cache (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    expire_at INTEGER NOT NULL
);

CREATE INDEX idx_expire ON cache(expire_at);
```

**字段说明**:
- `key`: 缓存键（主键）
- `value`: 缓存值（JSON 格式）
- `expire_at`: 过期时间（Unix 时间戳）

### 4.2 查看缓存数据

```python
import sqlite3

# 连接数据库
conn = sqlite3.connect('cache.db')
cursor = conn.cursor()

# 查询所有缓存
cursor.execute('SELECT key, value, datetime(expire_at, "unixepoch") as expire_time FROM cache')
for row in cursor.fetchall():
    print(f"Key: {row[0]}")
    print(f"Value: {row[1]}")
    print(f"Expire: {row[2]}")
    print("---")

# 查询缓存数量
cursor.execute('SELECT COUNT(*) FROM cache')
count = cursor.fetchone()[0]
print(f"总缓存数：{count}")

conn.close()
```

### 4.3 清理过期缓存

```python
import sqlite3
import time

conn = sqlite3.connect('cache.db')
cursor = conn.cursor()

# 删除过期缓存
current_time = int(time.time())
cursor.execute('DELETE FROM cache WHERE expire_at < ?', (current_time,))
deleted_count = cursor.rowcount
conn.commit()
conn.close()

print(f"已清理 {deleted_count} 条过期缓存")
```

---

## 五、性能优化

### 5.1 调整缓存超时

根据数据类型设置不同的超时时间：

```python
# 频繁变化的数据 - 短超时
cache_service.set('inventory_count', count, timeout=60)  # 1 分钟

# 相对稳定的数据 - 中超时
cache_service.set('warehouse_list', warehouses, timeout=300)  # 5 分钟

# 几乎不变的数据 - 长超时
cache_service.set('config_data', config, timeout=3600)  # 1 小时
```

### 5.2 定期清理

创建定时任务清理过期缓存：

```python
# app/services/cache_cleanup.py
from app.services.cache_service import cache_service
import logging

def cleanup_expired_cache():
    """清理过期缓存"""
    try:
        # SQLite 会自动在查询时清理
        # 但可以手动执行一次完整清理
        cache_service._cleanup_expired()
        logging.info('过期缓存清理完成')
    except Exception as e:
        logging.error(f'缓存清理失败：{str(e)}')
```

### 5.3 使用连接池（可选）

对于高并发场景，可以使用连接池：

```python
from sqlite3 import connect
from queue import Queue

class SQLiteConnectionPool:
    def __init__(self, db_path, max_connections=10):
        self.db_path = db_path
        self.pool = Queue(max_connections)
        
        # 初始化连接池
        for _ in range(max_connections):
            conn = connect(db_path)
            self.pool.put(conn)
    
    def get_connection(self):
        return self.pool.get()
    
    def return_connection(self, conn):
        self.pool.put(conn)
```

---

## 六、监控与维护

### 6.1 查看缓存统计

```python
import sqlite3

def get_cache_stats():
    """获取缓存统计信息"""
    conn = sqlite3.connect('cache.db')
    cursor = conn.cursor()
    
    # 总缓存数
    cursor.execute('SELECT COUNT(*) FROM cache')
    total = cursor.fetchone()[0]
    
    # 即将过期的缓存（5 分钟内）
    import time
    soon_expire = int(time.time()) + 300
    cursor.execute('SELECT COUNT(*) FROM cache WHERE expire_at BETWEEN ? AND ?', 
                   (int(time.time()), soon_expire))
    expiring_soon = cursor.fetchone()[0]
    
    # 缓存大小
    cursor.execute('SELECT SUM(length(value)) FROM cache')
    total_size = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'total_keys': total,
        'expiring_soon': expiring_soon,
        'total_size_bytes': total_size,
        'total_size_mb': round(total_size / 1024 / 1024, 2)
    }

# 使用示例
stats = get_cache_stats()
print(f"总缓存数：{stats['total_keys']}")
print(f"即将过期：{stats['expiring_soon']}")
print(f"总大小：{stats['total_size_mb']} MB")
```

### 6.2 备份缓存数据库

```python
import shutil
from datetime import datetime

def backup_cache_db():
    """备份缓存数据库"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backups/cache_backup_{timestamp}.db'
    
    # 创建备份目录
    import os
    os.makedirs('backups', exist_ok=True)
    
    # 复制数据库文件
    shutil.copy2('cache.db', backup_file)
    
    print(f"缓存数据库已备份：{backup_file}")
    return backup_file
```

### 6.3 日志记录

在 `app/services/cache_service.py` 中添加详细日志：

```python
def set(self, key, value, timeout=None):
    """设置缓存（增强日志）"""
    # ...现有代码...
    
    current_app.logger.debug(f'缓存 SET: key={key}, timeout={timeout}')
    
    # ...现有代码...
```

---

## 七、故障排查

### 问题 1：缓存文件过大

**症状**: `cache.db` 文件超过 100MB

**解决**:
```python
# 1. 清理所有缓存
cache_service.clear_pattern('*')

# 2. 压缩数据库
import sqlite3
conn = sqlite3.connect('cache.db')
conn.execute('VACUUM')
conn.close()

# 3. 调整超时配置
# .env:
CACHE_DEFAULT_TIMEOUT=60  # 减少默认超时时间
```

### 问题 2：并发写入冲突

**症状**: `database is locked` 错误

**解决**:
```python
# 1. 增加超时时间
# cache_service.py 中修改:
conn = sqlite3.connect(self.db_path, timeout=30)

# 2. 使用 WAL 模式
conn.execute('PRAGMA journal_mode=WAL')

# 3. 减少并发写入
# 使用队列批量写入
```

### 问题 3：缓存命中率低

**症状**: 缓存很少被命中

**解决**:
```python
# 1. 检查超时设置是否太短
# 增加超时时间
cache_service.set(key, value, timeout=600)  # 10 分钟

# 2. 检查键生成逻辑
# 确保相同参数生成相同的键

# 3. 添加缓存统计
# 记录命中/未命中次数
```

---

## 八、与 Redis 对比

| 特性 | Redis | SQLite 缓存 |
|------|-------|------------|
| 安装依赖 | ❌ 需要 | ✅ 无需 |
| 性能 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 并发能力 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 持久化 | ✅ | ✅ |
| 过期时间 | ✅ | ✅ |
| 数据结构 | 丰富 | 仅 KV |
| 内存占用 | 中等 | 低 |
| 适用场景 | 生产环境 | 开发/小规模 |

---

## 九、最佳实践

### 9.1 缓存策略

```python
# 1. 热点数据优先缓存
hot_data = get_hot_data()
cache_service.set('hot_data', hot_data, timeout=60)

# 2. 冷数据不缓存
cold_data = get_cold_data()  # 直接查询数据库

# 3. 写操作清除相关缓存
def update_warehouse(warehouse_id, data):
    # 更新数据
    warehouse.update(data)
    
    # 清除相关缓存
    cache_service.delete(f'warehouse:{warehouse_id}')
    cache_service.clear_pattern('warehouse_list:*')
```

### 9.2 缓存键命名规范

```python
# 格式：{模块}:{类型}:{ID}
cache_key = f'warehouse:detail:{warehouse_id}'
cache_key = f'user:permissions:{user_id}'
cache_key = f'config:system:global'
```

### 9.3 超时时间建议

```python
# 配置数据 - 1 小时
CACHE_CONFIG_TIMEOUT = 3600

# 列表数据 - 5 分钟
CACHE_LIST_TIMEOUT = 300

# 详情数据 - 10 分钟
CACHE_DETAIL_TIMEOUT = 600

# 统计数据 - 15 分钟
CACHE_STATS_TIMEOUT = 900
```

---

## 十、总结

### SQLite 缓存优势

**推荐使用场景**:
- ✅ Windows 老版本系统
- ✅ 开发/测试环境
- ✅ 无外部依赖要求
- ✅ 小规模生产环境

**不推荐场景**:
- ❌ 高并发场景（>1000 QPS）
- ❌ 需要复杂数据结构
- ❌ 需要分布式缓存

### 性能建议

1. **合理设置超时** - 避免过短或过长
2. **定期清理** - 删除过期和无效缓存
3. **监控统计** - 了解缓存命中率
4. **备份数据库** - 防止数据丢失

### 下一步

1. ✅ 系统已自动集成 SQLite 缓存
2. ✅ 无需额外配置即可使用
3. ✅ 如需优化，参考本文档调整参数

---

**SQLite 缓存已就绪，系统可正常运行！** 🎉
