# KeyDB 安装与使用指南

## 📖 简介

**KeyDB** 是 Redis 的高性能分支，完全兼容 Redis API，支持 Windows 原生运行。

**核心优势**:
- ✅ 100% Redis 兼容 - 无需修改任何代码
- ✅ 多线程架构 - 性能比 Redis 快 2-5 倍
- ✅ Windows 原生支持 - 无需 Docker/WSL
- ✅ 单文件运行 - 下载即用
- ✅ 内存效率更高 - 节省资源

---

## 一、下载 KeyDB

### 方法一：官网下载（推荐）

1. 访问：https://keydb.dev/downloads/
2. 选择 Windows 版本
3. 下载最新 Release

### 方法二：GitHub 下载

1. 访问：https://github.com/Snapchat/keydb/releases
2. 下载 Windows 预编译版本
3. 解压到本地

### 方法三：直接下载链接

```powershell
# 最新稳定版（示例链接，请替换为实际版本）
$url = "https://github.com/Snapchat/keydb/releases/download/v6.3.4/KeyDB-6.3.4-Windows.zip"
$output = "C:\keydb\keydb.zip"

# 创建目录
New-Item -ItemType Directory -Force -Path "C:\keydb"

# 下载
Invoke-WebRequest -Uri $url -OutFile $output

# 解压
Expand-Archive -Path $output -DestinationPath "C:\keydb" -Force
```

---

## 二、安装 KeyDB

### 2.1 解压文件

```powershell
# 假设下载到 C:\keydb
# 解压后目录结构:
# C:\keydb\
#   ├── keydb-server.exe
#   ├── keydb-cli.exe
#   ├── keydb-benchmark.exe
#   └── keydb.conf
```

### 2.2 配置 KeyDB

创建 `C:\keydb\keydb.conf` 配置文件：

```conf
# KeyDB 配置文件

# 网络配置
bind 127.0.0.1
port 6379

# 保护模式
protected-mode yes

# 密码（可选，生产环境建议设置）
# requirepass YourPassword123

# 日志
loglevel notice
logfile "C:\\keydb\\keydb.log"

# 持久化 - RDB
save 900 1
save 300 10
save 60 10000
dbfilename dump.rdb
dir C:\\keydb\\data

# 持久化 - AOF
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# 内存管理
maxmemory 256mb
maxmemory-policy allkeys-lru

# 多线程（KeyDB 特性）
threadpool-size 4

# 禁用危险命令（生产环境）
# rename-command FLUSHDB ""
# rename-command FLUSHALL ""
# rename-command DEBUG ""
```

### 2.3 创建数据目录

```powershell
# 创建数据目录
New-Item -ItemType Directory -Force -Path "C:\keydb\data"
```

---

## 三、启动 KeyDB

### 3.1 手动启动（开发环境）

```powershell
# 进入 KeyDB 目录
cd C:\keydb

# 启动服务器
.\keydb-server.exe keydb.conf

# 后台运行
Start-Process -FilePath ".\keydb-server.exe" -ArgumentList "keydb.conf" -WindowStyle Hidden
```

### 3.2 安装为 Windows 服务（生产环境）

```powershell
# 1. 以管理员身份运行 PowerShell

# 2. 安装服务
sc create KeyDB binPath= "C:\keydb\keydb-server.exe C:\keydb\keydb.conf" start= auto

# 3. 启动服务
net start KeyDB

# 4. 查看服务状态
sc query KeyDB

# 5. 停止服务
net stop KeyDB

# 6. 删除服务
sc delete KeyDB
```

### 3.3 使用启动脚本

创建 `C:\keydb\start_keydb.ps1`:

```powershell
# KeyDB 启动脚本
$KeyDBPath = "C:\keydb"
$ConfigFile = "$KeyDBPath\keydb.conf"
$LogFile = "$KeyDBPath\keydb.log"

Write-Host "正在启动 KeyDB..." -ForegroundColor Green

# 检查配置文件
if (!(Test-Path $ConfigFile)) {
    Write-Host "错误：配置文件不存在" -ForegroundColor Red
    exit 1
}

# 启动 KeyDB
Start-Process -FilePath "$KeyDBPath\keydb-server.exe" `
              -ArgumentList $ConfigFile `
              -WindowStyle Hidden

# 等待启动
Start-Sleep -Seconds 3

# 验证
$test = & "$KeyDBPath\keydb-cli.exe" ping
if ($test -eq "PONG") {
    Write-Host "KeyDB 启动成功！" -ForegroundColor Green
} else {
    Write-Host "KeyDB 启动失败" -ForegroundColor Red
}
```

---

## 四、验证安装

### 4.1 基础测试

```powershell
# 1. 使用 CLI 连接
cd C:\keydb
.\keydb-cli.exe

# 进入交互界面:
# 127.0.0.1:6379>

# 2. 测试基本命令
127.0.0.1:6379> PING
PONG

127.0.0.1:6379> SET test "hello keydb"
OK

127.0.0.1:6379> GET test
"hello keydb"

127.0.0.1:6379> INCR counter
(integer) 1

127.0.0.1:6379> INCR counter
(integer) 2

# 3. 退出
127.0.0.1:6379> EXIT
```

### 4.2 性能测试

```powershell
# 运行基准测试
.\keydb-benchmark.exe -q

# 预期输出:
# PING_INLINE: 100000 requests in 0.50 seconds
# PING_BULK: 100000 requests in 0.50 seconds
# SET: 100000 requests in 0.58 seconds
# GET: 100000 requests in 0.52 seconds
```

### 4.3 验证服务状态

```powershell
# 检查进程
Get-Process | Where-Object {$_.ProcessName -like "*keydb*"}

# 检查端口
netstat -ano | findstr :6379

# 查看日志
Get-Content "C:\keydb\keydb.log" -Tail 50
```

---

## 五、配置应用连接

### 5.1 修改项目配置

修改 `.env` 文件（项目根目录）：

```env
# Redis/KeyDB 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

### 5.2 重启应用

```powershell
# 停止应用（Ctrl+C）

# 重新启动
cd d:\Trae\spare_management
python run.py

# 查看日志，应该看到:
# [INFO] Redis 连接成功
```

---

## 六、常用命令

### 6.1 服务管理

```powershell
# 启动服务
net start KeyDB

# 停止服务
net stop KeyDB

# 重启服务
net stop KeyDB && net start KeyDB

# 查看状态
sc query KeyDB
```

### 6.2 数据管理

```powershell
# 备份数据
Copy-Item "C:\keydb\data\dump.rdb" "C:\backups\keydb-backup-$(Get-Date -Format 'yyyyMMdd').rdb"

# 恢复数据
Copy-Item "C:\backups\keydb-backup-20240101.rdb" "C:\keydb\data\dump.rdb" -Force

# 清空数据
.\keydb-cli.exe FLUSHALL
```

### 6.3 监控命令

```powershell
# 查看内存使用
.\keydb-cli.exe INFO memory

# 查看连接数
.\keydb-cli.exe CLIENT LIST

# 查看慢查询
.\keydb-cli.exe SLOWLOG GET 10

# 查看持久化状态
.\keydb-cli.exe INFO persistence

# 实时统计
.\keydb-cli.exe --stat
```

---

## 七、故障排查

### 问题 1: 无法启动

**症状**: 启动后立即退出

**解决**:
```powershell
# 1. 查看日志
Get-Content "C:\keydb\keydb.log"

# 2. 检查端口占用
netstat -ano | findstr :6379

# 3. 手动启动查看详细错误
.\keydb-server.exe keydb.conf
```

### 问题 2: 连接被拒绝

**症状**: `Could not connect to Redis at 127.0.0.1:6379`

**解决**:
```powershell
# 1. 检查服务是否运行
Get-Process | Where-Object {$_.ProcessName -like "*keydb*"}

# 2. 检查防火墙
netsh advfirewall firewall show rule name=all | findstr 6379

# 3. 允许端口
netsh advfirewall firewall add rule name="KeyDB" dir=in action=allow protocol=TCP localport=6379
```

### 问题 3: 密码认证失败

**症状**: `NOAUTH Authentication required`

**解决**:
```powershell
# 1. 检查配置文件中的密码
# keydb.conf:
# requirepass YourPassword

# 2. 使用密码连接
.\keydb-cli.exe -a YourPassword

# 3. 修改应用配置
# .env:
# REDIS_PASSWORD=YourPassword
```

### 问题 4: 内存不足

**症状**: `OOM command not allowed when used memory > 'maxmemory'`

**解决**:
```powershell
# 1. 修改配置文件
# keydb.conf:
# maxmemory 512mb

# 2. 或动态调整
.\keydb-cli.exe CONFIG SET maxmemory 512mb
```

---

## 八、性能优化

### 8.1 调整线程数

```conf
# keydb.conf
threadpool-size 8  # 根据 CPU 核心数调整
```

### 8.2 调整内存

```conf
# 根据系统内存调整
maxmemory 512mb
maxmemory-policy allkeys-lru
```

### 8.3 优化持久化

```conf
# AOF 配置
appendonly yes
appendfsync everysec  # everysec, always, no

# RDB 配置
save 900 1
save 300 10
save 60 10000
```

---

## 九、安全建议

### 9.1 设置密码

```conf
# keydb.conf
requirepass YourVeryStrongPassword123!
```

### 9.2 绑定本地地址

```conf
# keydb.conf
bind 127.0.0.1
protected-mode yes
```

### 9.3 禁用危险命令

```conf
# keydb.conf
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
rename-command DEBUG ""
```

### 9.4 防火墙配置

```powershell
# 仅允许本地访问
netsh advfirewall firewall add rule name="KeyDB Local" dir=in action=allow protocol=TCP localport=6379 remoteip=127.0.0.1
```

---

## 十、备份与恢复

### 10.1 自动备份脚本

创建 `C:\keydb\backup.ps1`:

```powershell
# KeyDB 自动备份脚本
$BackupDir = "C:\backups\keydb"
$Date = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "$BackupDir\keydb-backup-$Date.rdb"

# 创建备份目录
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Force -Path $BackupDir
}

# 触发 BGSAVE
& "C:\keydb\keydb-cli.exe" BGSAVE

# 等待保存完成
Start-Sleep -Seconds 5

# 复制 RDB 文件
Copy-Item "C:\keydb\data\dump.rdb" $BackupFile

# 清理 7 天前的备份
$DaysBack = -7
Get-ChildItem $BackupDir -Filter "keydb-backup-*.rdb" | `
    Where-Object {$_.CreationTime -lt (Get-Date).AddDays($DaysBack)} | `
    Remove-Item -Force

Write-Host "备份完成：$BackupFile" -ForegroundColor Green
```

### 10.2 设置定时任务

```powershell
# 创建计划任务（每天凌晨 2 点备份）
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
           -Argument "-File C:\keydb\backup.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName "KeyDB Backup" `
                       -Action $action `
                       -Trigger $trigger `
                       -User "System"
```

---

## 十一、监控与维护

### 11.1 日常监控

```powershell
# 创建监控脚本 C:\keydb\monitor.ps1
while ($true) {
    Clear-Host
    Write-Host "=== KeyDB 监控 ===" -ForegroundColor Cyan
    Write-Host "时间：$(Get-Date)" -ForegroundColor Yellow
    
    # 内存使用
    $info = & "C:\keydb\keydb-cli.exe" INFO memory
    $usedMemory = $info | Select-String "used_memory_human" | ForEach-Object { ($_ -split ':')[1].Trim() }
    Write-Host "内存使用：$usedMemory" -ForegroundColor Green
    
    # 连接数
    $clients = & "C:\keydb\keydb-cli.exe" CLIENT LIST | Measure-Object -Line
    Write-Host "连接数：$($clients.Lines)" -ForegroundColor Green
    
    # 运行时间
    $uptime = & "C:\keydb\keydb-cli.exe" INFO server | Select-String "uptime_in_seconds" | ForEach-Object { ($_ -split ':')[1].Trim() }
    Write-Host "运行时间：${uptime}秒" -ForegroundColor Green
    
    Start-Sleep -Seconds 5
}
```

### 11.2 定期维护

```powershell
# 每周清理慢查询
.\keydb-cli.exe SLOWLOG RESET

# 每月检查数据完整性
.\keydb-cli.exe BGSAVE

# 检查日志大小
$logSize = (Get-Item "C:\keydb\keydb.log").Length / 1MB
if ($logSize -gt 100) {
    Write-Host "日志文件过大，建议清理" -ForegroundColor Yellow
}
```

---

## 十二、快速参考

### 一键启动命令
```powershell
# 启动服务
net start KeyDB

# 或手动启动
C:\keydb\keydb-server.exe C:\keydb\keydb.conf
```

### 测试连接
```powershell
C:\keydb\keydb-cli.exe ping
# 返回：PONG
```

### 查看状态
```powershell
# 进程
Get-Process | Where-Object {$_.ProcessName -like "*keydb*"}

# 端口
netstat -ano | findstr :6379

# 服务
sc query KeyDB
```

---

## 十三、与 Redis 对比

| 特性       | Redis  | KeyDB  |
|------------|--------|--------|
| 性能       | ⭐⭐⭐   | ⭐⭐⭐⭐⭐ |
| 多线程     | ❌     | ✅     |
| Windows 支持 | ⚠️    | ✅     |
| 内存效率   | ⭐⭐⭐   | ⭐⭐⭐⭐  |
| 兼容性     | 100%   | 100%   |
| 社区规模   | ⭐⭐⭐⭐⭐ | ⭐⭐⭐   |
| 更新频率   | ⭐⭐⭐⭐⭐ | ⭐⭐⭐   |

---

## 十四、总结

### 为什么选择 KeyDB？

1. **零代码修改** - 完全兼容 Redis API
2. **性能提升** - 多线程架构，性能提升 2-5 倍
3. **Windows 原生** - 无需 Docker/WSL
4. **部署简单** - 单文件运行，5 分钟完成
5. **资源节省** - 内存效率更高

### 下一步

1. ✅ 下载 KeyDB
2. ✅ 安装配置
3. ✅ 启动服务
4. ✅ 验证连接
5. ✅ 重启应用

**祝您使用愉快！** 🎉

---

## 附录：资源链接

- 官网：https://keydb.dev/
- GitHub: https://github.com/Snapchat/keydb
- 文档：https://docs.keydb.dev/
- 下载：https://keydb.dev/downloads/
- 性能对比：https://keydb.dev/benchmark/
