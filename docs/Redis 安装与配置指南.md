# Redis 安装与配置指南

## 📋 问题诊断

**当前状态**: Redis 未安装或未启动
**错误信息**: `Redis 连接失败：Error 10061 connecting to localhost:6379. 由于目标计算机积极拒绝，无法连接。`

**原因分析**:
1. ✅ Redis 未安装在 Windows 系统上
2. ✅ Redis 服务未启动
3. ✅ Redis 端口被防火墙阻止（如果已安装）

---

## 🔧 解决方案

### 方案一：安装 Redis（推荐用于生产环境）

#### Windows 安装步骤

**1. 下载 Redis**

Redis 官方不支持 Windows，但可以使用社区维护的版本：

- **选项 A**: [Microsoft Archive Redis](https://github.com/microsoftarchive/redis/releases)
  - 下载：`Redis-x64-3.0.504.msi`
  - 适合：Windows 7/8/10/Server 2012+

- **选项 B**: [Memurai](https://www.memurai.com/) (Redis 兼容)
  - 下载：Memurai Developer
  - 适合：需要最新 Redis 特性

- **选项 C**: [Chocolatey 包管理器](https://chocolatey.org/)
  ```powershell
  choco install redis-64
  ```

**2. 安装 Redis (使用 MSI 安装包)**

```powershell
# 1. 运行下载的 MSI 安装包
Redis-x64-3.0.504.msi

# 2. 按照安装向导完成安装
# 3. 默认安装路径：C:\Program Files\Redis
# 4. 默认端口：6379
```

**3. 启动 Redis 服务**

```powershell
# 方法 1: 使用服务管理器
# 按 Win+R，输入 services.msc
# 找到 Redis 服务，右键启动

# 方法 2: 使用命令行（管理员权限）
net start Redis

# 方法 3: 手动启动
cd "C:\Program Files\Redis"
redis-server.exe redis.windows.conf
```

**4. 验证安装**

```powershell
# 测试连接
redis-cli ping
# 应该返回：PONG

# 查看 Redis 信息
redis-cli info

# 测试设置和获取值
redis-cli set test "hello"
redis-cli get test
# 应该返回："hello"
```

---

#### 使用 Docker 安装 Redis（最简单）

**前提条件**: 已安装 Docker Desktop

```powershell
# 1. 拉取 Redis 镜像
docker pull redis:latest

# 2. 启动 Redis 容器
docker run -d -p 6379:6379 --name redis redis:latest

# 3. 验证运行
docker ps | findstr redis

# 4. 测试连接
docker exec redis redis-cli ping
# 应该返回：PONG

# 5. 持久化数据（可选）
docker run -d -p 6379:6379 -v redis_data:/data --name redis redis:latest
```

---

#### 使用 WSL (Windows Subsystem for Linux)

**前提条件**: 已启用 WSL

```bash
# 1. 更新包列表
sudo apt update

# 2. 安装 Redis
sudo apt install redis-server

# 3. 启动 Redis
sudo service redis-server start

# 4. 验证
redis-cli ping
# 应该返回：PONG

# 5. 设置开机自启
sudo systemctl enable redis-server
```

---

### 方案二：使用内存缓存（临时方案，无需安装）

如果暂时不需要 Redis，可以使用 Flask-Caching 的内存缓存：

**1. 修改配置文件**

在 `.env` 文件中添加：
```env
CACHE_TYPE=SimpleCache
CACHE_DEFAULT_TIMEOUT=300
```

**2. 修改缓存服务**

修改 `app/services/cache_service.py`，添加内存缓存支持：

```python
from flask_caching import Cache

# 创建缓存实例
cache = Cache(config={
    'CACHE_TYPE': 'SimpleCache',  # 使用内存缓存
    'CACHE_DEFAULT_TIMEOUT': 300
})

def init_cache(app):
    """初始化缓存服务"""
    try:
        # 尝试使用 Redis
        cache.init_app(app, config={
            'CACHE_TYPE': 'redis',
            'CACHE_REDIS_URL': app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        })
        app.logger.info('Redis 缓存已连接')
    except:
        # 降级到内存缓存
        cache.init_app(app, config={
            'CACHE_TYPE': 'SimpleCache',
            'CACHE_DEFAULT_TIMEOUT': 300
        })
        app.logger.info('使用内存缓存（Redis 不可用）')
    
    app.extensions['cache'] = cache
    return cache
```

**3. 安装 Flask-Caching**

```powershell
pip install Flask-Caching
```

---

### 方案三：使用云 Redis 服务（生产环境推荐）

#### 阿里云 Redis

1. 登录阿里云控制台
2. 创建 Redis 实例
3. 获取连接信息：
   - 主机地址：`redis-xxxx.cn-hangzhou.rds.aliyuncs.com`
   - 端口：`6379`
   - 密码：`your_password`

4. 修改 `.env`:
```env
REDIS_HOST=redis-xxxx.cn-hangzhou.rds.aliyuncs.com
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DB=0
```

#### 腾讯云 Redis

1. 登录腾讯云控制台
2. 创建 Redis 实例
3. 获取连接信息

4. 修改 `.env`:
```env
REDIS_HOST=xxxxx.redis.tencentcloud.com
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DB=0
```

---

## 🔍 故障排查

### 问题 1: Redis 服务未启动

**症状**: `redis-cli ping` 返回连接错误

**解决**:
```powershell
# Windows
net start Redis

# 或者手动启动
cd "C:\Program Files\Redis"
redis-server.exe redis.windows.conf
```

### 问题 2: 端口被占用

**症状**: Redis 启动失败，提示端口已占用

**解决**:
```powershell
# 查找占用 6379 端口的进程
netstat -ano | findstr :6379

# 终止进程（假设 PID 为 12345）
taskkill /PID 12345 /F

# 重新启动 Redis
net start Redis
```

### 问题 3: 防火墙阻止

**症状**: 远程无法连接 Redis

**解决**:
```powershell
# Windows 防火墙添加入站规则
netsh advfirewall firewall add rule name="Redis" dir=in action=allow protocol=TCP localport=6379
```

### 问题 4: 密码认证失败

**症状**: `AUTH failed`

**解决**:
1. 修改 `redis.windows.conf`:
```conf
requirepass your_password
```

2. 重启 Redis 服务

3. 使用密码连接:
```powershell
redis-cli -a your_password ping
```

---

## 📊 Redis 配置优化

### 基础配置 (`redis.windows.conf`)

```conf
# 绑定地址（允许远程连接）
bind 0.0.0.0

# 端口
port 6379

# 密码保护
requirepass your_strong_password

# 最大内存限制（根据服务器内存调整）
maxmemory 256mb

# 内存淘汰策略
maxmemory-policy allkeys-lru

# 持久化（RDB）
save 900 1
save 300 10
save 60 10000
dbfilename dump.rdb
dir "C:/Program Files/Redis/data"

# 持久化（AOF）
appendonly yes
appendfilename "appendonly.aof"

# 日志
loglevel notice
logfile "C:/Program Files/Redis/redis.log"
```

### 性能优化

```conf
# TCP 连接 backlog
tcp-backlog 511

# 客户端超时（0 表示禁用）
timeout 0

# TCP keepalive
tcp-keepalive 300

# 最大连接数
maxclients 10000
```

---

## 🎯 应用配置

### 开发环境 (.env)

```env
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

### 生产环境 (.env.production)

```env
# Redis 配置（使用云 Redis）
REDIS_HOST=redis-instance.xxx.redis.com
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_strong_password

# 缓存超时（秒）
CACHE_DEFAULT_TIMEOUT=300
CACHE_TIMEOUT_SHORT=60
CACHE_TIMEOUT_LONG=3600
```

---

## ✅ 验证 Redis 工作

### 1. 测试连接

```powershell
redis-cli ping
# 返回：PONG
```

### 2. 测试缓存功能

```python
# 在 Python 中测试
from app.services.cache_service import cache_service

# 设置缓存
cache_service.set('test_key', 'test_value', timeout=60)

# 获取缓存
value = cache_service.get('test_key')
print(value)  # 应该输出：test_value

# 删除缓存
cache_service.delete('test_key')
```

### 3. 检查应用日志

启动应用后，检查日志：
```
[INFO] Redis 连接成功
```

如果看到：
```
[WARNING] Redis 连接失败
```
说明 Redis 仍未正确连接，请检查上述配置。

---

## 🚀 快速开始（推荐方案）

**最简单的方法 - 使用 Docker**:

```powershell
# 1. 安装 Docker Desktop (如果未安装)
# 下载：https://www.docker.com/products/docker-desktop

# 2. 启动 Redis
docker run -d -p 6379:6379 --name redis redis:latest

# 3. 验证
docker exec redis redis-cli ping

# 4. 重启应用
cd d:\Trae\spare_management
python run.py

# 5. 检查日志
# 应该看到：[INFO] Redis 连接成功
```

---

## 📝 总结

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **Windows 安装** | 原生支持，性能好 | 安装稍复杂 | 开发/生产环境 |
| **Docker** | 简单快速，易管理 | 需要 Docker | 开发环境 ⭐ |
| **WSL** | Linux 原生体验 | 需要 WSL | 开发环境 |
| **云 Redis** | 免运维，高可用 | 需要付费 | 生产环境 ⭐ |
| **内存缓存** | 无需安装 | 重启丢失，单机 | 临时方案 |

**推荐**: 
- 开发环境：Docker（最简单）
- 生产环境：云 Redis 服务（最可靠）

---

## 🔗 相关资源

- [Redis 官方文档](https://redis.io/documentation)
- [Redis Windows 版本](https://github.com/tporadowski/redis)
- [Docker Hub Redis](https://hub.docker.com/_/redis)
- [阿里云 Redis](https://www.aliyun.com/product/kvstore)
- [腾讯云 Redis](https://cloud.tencent.com/product/crs)
