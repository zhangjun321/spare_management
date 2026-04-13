# Docker 安装 Redis 完整操作指南

## 📋 目录

1. [Docker 安装](#一 docker 安装)
2. [Redis 安装](#二 redis 安装)
3. [验证测试](#三验证测试)
4. [常用命令](#四常用命令)
5. [故障排查](#五故障排查)
6. [应用集成](#六应用集成)

---

## 一、Docker 安装

### 1.1 下载 Docker Desktop

**官方网站**: https://www.docker.com/products/docker-desktop/

**系统要求**:
- Windows 10/11 64 位
- Hyper-V 支持
- 至少 4GB 内存
- 虚拟化支持（BIOS 中开启）

**下载步骤**:
1. 访问官网下载页面
2. 点击 "Download for Windows"
3. 选择适合的安装包：
   - Intel 芯片：`Docker Desktop Installer.exe`
   - AMD 芯片：`Docker Desktop Installer.exe`
   - ARM 芯片：`Docker Desktop for ARM`

### 1.2 安装 Docker Desktop

**安装步骤**:

```powershell
# 1. 双击运行下载的安装包
Docker Desktop Installer.exe

# 2. 按照安装向导操作
#    - 接受许可协议
#    - 选择安装路径（默认 C:\Program Files\Docker\Docker）
#    - 勾选 "Use WSL 2 instead of Hyper-V"（推荐）

# 3. 等待安装完成（约 5-10 分钟）

# 4. 安装完成后重启计算机
```

**配置 WSL 2**（如果未自动配置）:

```powershell
# 1. 以管理员身份运行 PowerShell
# 2. 启用 WSL 功能
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# 3. 启用虚拟机平台
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 4. 重启计算机

# 5. 下载并安装 WSL 2 Linux 内核
# 下载地址：https://aka.ms/wsl2kernel

# 6. 设置 WSL 2 为默认版本
wsl --set-default-version 2
```

### 1.3 启动 Docker Desktop

```powershell
# 1. 从开始菜单启动 Docker Desktop
# 或双击桌面快捷方式

# 2. 首次启动会提示：
#    - 接受服务条款
#    - 选择是否发送使用数据

# 3. 等待 Docker 引擎启动（状态栏显示 "Docker Desktop is running"）

# 4. 验证安装
docker --version
docker compose version
```

**预期输出**:
```
Docker version 25.0.3, build 4debf41
Docker Compose version v2.24.6
```

---

## 二、Redis 安装

### 2.1 拉取 Redis 镜像

```powershell
# 1. 从 Docker Hub 拉取最新稳定版 Redis
docker pull redis:latest

# 2. 验证镜像已下载
docker images redis

# 预期输出:
# REPOSITORY   TAG       IMAGE ID       CREATED         SIZE
# redis        latest    xxxxxxxxxxxx   2 weeks ago     45MB
```

**可选：拉取特定版本**
```powershell
# 拉取 Redis 7.0
docker pull redis:7.0

# 拉取 Redis 6.2
docker pull redis:6.2

# 拉取 Alpine 版本（更小）
docker pull redis:alpine
```

### 2.2 启动 Redis 容器

**基础启动（推荐开发环境）**:

```powershell
# 启动 Redis 容器
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:latest

# 参数说明:
# -d: 后台运行（detached mode）
# --name redis: 容器名称为 redis
# -p 6379:6379: 映射容器 6379 端口到主机 6379 端口
```

**生产环境配置（带数据持久化）**:

```powershell
# 创建数据卷
docker volume create redis_data

# 启动带持久化的 Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v redis_data:/data \
  --restart unless-stopped \
  redis:latest \
  redis-server --appendonly yes

# 参数说明:
# -v redis_data:/data: 挂载数据卷到容器/data 目录
# --restart unless-stopped: 容器退出时自动重启
# --appendonly yes: 启用 AOF 持久化
```

**完整配置（带密码和内存限制）**:

```powershell
# 创建配置文件目录
mkdir C:\docker\redis

# 创建 redis.conf 配置文件
# 内容如下:
```

创建 `C:\docker\redis\redis.conf`:
```conf
# Redis 配置文件

# 绑定所有网络接口
bind 0.0.0.0

# 端口
port 6379

# 密码保护（生产环境必须设置！）
requirepass YourStrongPassword123!

# 最大内存限制
maxmemory 256mb

# 内存淘汰策略
maxmemory-policy allkeys-lru

# AOF 持久化
appendonly yes
appendfsync everysec

# RDB 持久化
save 900 1
save 300 10
save 60 10000

# 日志
loglevel notice
logfile ""

# 禁用危险命令（生产环境）
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
```

启动容器:
```powershell
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v C:\docker\redis\redis.conf:/usr/local/etc/redis/redis.conf \
  -v redis_data:/data \
  --restart unless-stopped \
  redis:latest \
  redis-server /usr/local/etc/redis/redis.conf
```

### 2.3 验证容器运行

```powershell
# 1. 查看运行中的容器
docker ps

# 预期输出:
# CONTAINER ID   IMAGE          COMMAND                  CREATED          STATUS          PORTS                    NAMES
# abc123def456   redis:latest   "docker-entrypoint.s…"   10 seconds ago   Up 9 seconds    0.0.0.0:6379->6379/tcp   redis

# 2. 查看容器日志
docker logs redis

# 预期看到:
# Ready to accept connections

# 3. 测试连接
docker exec redis redis-cli ping

# 预期输出:
# PONG
```

---

## 三、验证测试

### 3.1 基础功能测试

```powershell
# 1. 连接 Redis
docker exec -it redis redis-cli

# 进入 Redis 交互界面:
# 127.0.0.1:6379>

# 2. 测试基本命令
127.0.0.1:6379> SET test "hello redis"
OK

127.0.0.1:6379> GET test
"hello redis"

127.0.0.1:6379> INCR counter
(integer) 1

127.0.0.1:6379> INCR counter
(integer) 2

127.0.0.1:6379> GET counter
"2"

# 3. 测试 Hash 结构
127.0.0.1:6379> HSET user:1 name "张三" age 25 email "zhangsan@example.com"
(integer) 3

127.0.0.1:6379> HGETALL user:1
1) "name"
2) "张三"
3) "age"
4) "25"
5) "email"
6) "zhangsan@example.com"

# 4. 测试 List 结构
127.0.0.1:6379> LPUSH tasks "task1" "task2" "task3"
(integer) 3

127.0.0.1:6379> LRANGE tasks 0 -1
1) "task3"
2) "task2"
3) "task1"

# 5. 退出
127.0.0.1:6379> EXIT
```

### 3.2 性能测试

```powershell
# 运行 Redis 基准测试
docker exec redis redis-benchmark -q

# 预期输出:
# PING_INLINE: 100000 requests in 0.85 seconds
# PING_BULK: 100000 requests in 0.85 seconds
# SET: 100000 requests in 0.92 seconds
# GET: 100000 requests in 0.88 seconds
# INCR: 100000 requests in 0.86 seconds
```

### 3.3 持久化测试

```powershell
# 1. 设置数据
docker exec -it redis redis-cli SET persistence_test "data_will_survive_restart"

# 2. 重启容器
docker restart redis

# 3. 验证数据还在
docker exec -it redis redis-cli GET persistence_test

# 应该返回:
# "data_will_survive_restart"
```

---

## 四、常用命令

### 4.1 容器管理

```powershell
# 启动容器
docker start redis

# 停止容器
docker stop redis

# 重启容器
docker restart redis

# 查看容器状态
docker ps -a | findstr redis

# 查看容器详情
docker inspect redis

# 查看容器资源使用
docker stats redis

# 进入容器交互
docker exec -it redis bash

# 查看容器日志
docker logs redis

# 实时查看日志
docker logs -f redis

# 删除容器（先停止）
docker stop redis
docker rm redis
```

### 4.2 镜像管理

```powershell
# 查看本地镜像
docker images redis

# 查看镜像详情
docker inspect redis:latest

# 删除镜像（先删除容器）
docker rm redis
docker rmi redis:latest

# 更新镜像
docker pull redis:latest

# 导出镜像
docker save redis:latest > redis-latest.tar

# 导入镜像
docker load < redis-latest.tar
```

### 4.3 数据管理

```powershell
# 备份数据卷
docker run --rm -v redis_data:/data -v ${PWD}:/backup alpine tar czf /backup/redis-backup.tar.gz /data

# 恢复数据卷
docker run --rm -v redis_data:/data -v ${PWD}:/backup alpine tar xzf /backup/redis-backup.tar.gz -C /

# 导出数据
docker exec redis redis-cli --rdb /backup/dump.rdb

# 导入数据
cat /backup/dump.rdb | docker exec -i redis redis-cli --pipe
```

### 4.4 网络管理

```powershell
# 查看容器 IP
docker inspect redis | findstr IPAddress

# 创建自定义网络
docker network create redis-network

# 将容器连接到自定义网络
docker network connect redis-network redis

# 查看网络连接
docker network inspect redis-network
```

---

## 五、故障排查

### 5.1 常见问题

**问题 1: 容器无法启动**

```powershell
# 症状: docker run 报错
# 错误信息: port is already allocated

# 原因：6379 端口已被占用

# 解决:
# 1. 查找占用端口的进程
netstat -ano | findstr :6379

# 2. 终止进程（假设 PID 为 12345）
taskkill /PID 12345 /F

# 3. 或者使用不同端口
docker run -d -p 6380:6379 --name redis redis:latest
```

**问题 2: 容器启动后立即退出**

```powershell
# 查看日志
docker logs redis

# 可能原因:
# 1. 配置文件错误
# 2. 权限问题
# 3. 内存不足

# 解决:
# 1. 检查配置文件语法
# 2. 使用默认配置启动测试
docker run -d --name redis-test redis:latest
```

**问题 3: 无法连接 Redis**

```powershell
# 检查容器是否运行
docker ps | findstr redis

# 检查端口映射
docker port redis

# 测试本地连接
docker exec redis redis-cli ping

# 测试主机连接
redis-cli -h localhost -p 6379 ping

# 检查防火墙
netsh advfirewall firewall show rule name=all | findstr 6379
```

**问题 4: 数据丢失**

```powershell
# 原因：未使用数据卷持久化

# 解决:
# 1. 停止并删除旧容器
docker stop redis
docker rm redis

# 2. 创建数据卷
docker volume create redis_data

# 3. 使用数据卷启动
docker run -d -p 6379:6379 -v redis_data:/data --name redis redis:latest
```

### 5.2 性能优化

**调整内存限制**:
```powershell
docker run -d -p 6379:6379 \
  --memory 512m \
  --memory-swap 512m \
  --name redis \
  redis:latest
```

**调整 CPU 限制**:
```powershell
docker run -d -p 6379:6379 \
  --cpus="1.5" \
  --name redis \
  redis:latest
```

**优化 I/O 性能**:
```powershell
# 使用本地卷而非 bind mount
docker volume create redis_data
docker run -d -p 6379:6379 -v redis_data:/data redis:latest
```

---

## 六、应用集成

### 6.1 配置应用连接 Redis

**修改 `.env` 文件**:
```env
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

**如果使用密码**:
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=YourStrongPassword123!
```

### 6.2 测试应用连接

```powershell
# 1. 重启应用
cd d:\Trae\spare_management
python run.py

# 2. 检查日志
# 应该看到:
# [INFO] Redis 连接成功

# 3. 如果看到:
# [WARNING] Redis 连接失败
# 请检查:
# - Redis 容器是否运行：docker ps
# - 端口是否映射：docker port redis
# - 配置是否正确：cat .env
```

### 6.3 使用 Docker Compose（可选）

创建 `docker-compose.yml`:
```yaml
version: '3.8'

services:
  redis:
    image: redis:latest
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis
    volumes:
      - .:/app

volumes:
  redis_data:
```

启动服务:
```powershell
# 启动所有服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

---

## 七、安全建议

### 7.1 生产环境配置

**1. 设置强密码**
```conf
# redis.conf
requirepass YourVeryStrongAndComplexPassword123!
```

**2. 修改默认端口**
```conf
# redis.conf
port 6380
```

**3. 绑定特定 IP**
```conf
# redis.conf
bind 127.0.0.1
```

**4. 禁用危险命令**
```conf
# redis.conf
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
rename-command CONFIG ""
```

**5. 启用 SSL/TLS**（Redis 6.0+）
```conf
# redis.conf
tls-port 6379
port 0
tls-cert-file /etc/redis/tls/redis.crt
tls-key-file /etc/redis/tls/redis.key
tls-ca-cert-file /etc/redis/tls/ca.crt
```

### 7.2 网络安全

**使用 Docker 网络隔离**:
```powershell
# 创建专用网络
docker network create --driver bridge --subnet 172.20.0.0/16 redis-network

# 启动 Redis（仅内网访问）
docker run -d --network redis-network --name redis redis:latest

# 启动应用（同一网络）
docker run -d --network redis-network --name web myapp:latest
```

**防火墙配置**:
```powershell
# Windows 防火墙允许 Redis 端口
netsh advfirewall firewall add rule name="Redis" dir=in action=allow protocol=TCP localport=6379

# 或限制特定 IP
netsh advfirewall firewall add rule name="Redis" dir=in action=allow protocol=TCP localport=6379 remoteip=192.168.1.0/24
```

---

## 八、监控与维护

### 8.1 监控命令

```powershell
# 查看 Redis 信息
docker exec redis redis-cli INFO

# 查看内存使用
docker exec redis redis-cli INFO memory

# 查看连接数
docker exec redis redis-cli CLIENT LIST

# 查看慢查询
docker exec redis redis-cli SLOWLOG GET 10

# 实时监控系统资源
docker stats redis
```

### 8.2 定期维护

**清理过期键**:
```powershell
docker exec redis redis-cli MEMORY DOCTOR
```

**优化 RDB 文件**:
```powershell
docker exec redis redis-cli BGSAVE
```

**检查持久化状态**:
```powershell
docker exec redis redis-cli INFO persistence
```

### 8.3 备份策略

**每日备份脚本**:
```powershell
# backup_redis.ps1
$backupDir = "C:\backups\redis"
$date = Get-Date -Format "yyyyMMdd"
$backupFile = "$backupDir\redis-backup-$date.rdb"

# 创建备份目录
if (!(Test-Path $backupDir)) {
    New-Item -ItemType Directory -Force -Path $backupDir
}

# 触发 BGSAVE
docker exec redis redis-cli BGSAVE

# 等待保存完成
Start-Sleep -Seconds 5

# 复制 RDB 文件
docker cp redis:/data/dump.rdb $backupFile

Write-Host "备份完成：$backupFile"
```

**设置定时任务**:
```powershell
# 创建计划任务
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\scripts\backup_redis.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName "Redis Backup" -Action $action -Trigger $trigger -User "System"
```

---

## 九、快速参考卡片

### 一键启动命令
```powershell
# 最简单方式
docker run -d -p 6379:6379 --name redis redis:latest

# 生产环境方式
docker run -d -p 6379:6379 -v redis_data:/data --restart unless-stopped --name redis redis:latest redis-server --appendonly yes
```

### 常用组合命令
```powershell
# 查看运行状态
docker ps | findstr redis && docker exec redis redis-cli ping

# 重启并查看日志
docker restart redis && docker logs --tail 50 redis

# 完全清理
docker stop redis && docker rm redis && docker volume rm redis_data
```

---

## 十、总结

### 优点
- ✅ 安装简单快速（5 分钟内完成）
- ✅ 环境隔离，不污染主机
- ✅ 易于备份和迁移
- ✅ 版本管理方便
- ✅ 资源占用少

### 缺点
- ⚠️ 需要学习 Docker 基础
- ⚠️ 数据持久化需要配置卷
- ⚠️ 网络配置稍复杂

### 最佳实践
1. 使用数据卷持久化数据
2. 生产环境设置密码
3. 配置自动重启策略
4. 定期备份数据
5. 监控资源使用
6. 使用自定义网络隔离

---

## 📞 获取帮助

如果遇到问题：
1. 查看容器日志：`docker logs redis`
2. 查看 Redis 文档：https://redis.io/documentation
3. 查看 Docker 文档：https://docs.docker.com/
4. 检查本文档的故障排查章节

**祝您使用愉快！** 🎉
