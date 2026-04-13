# KeyDB 快速入门指南

## 🚀 5 分钟快速开始

### 步骤 1：运行安装脚本（1 分钟）

```powershell
# 1. 以管理员身份打开 PowerShell
# 2. 运行安装脚本
cd d:\Trae\spare_management
.\install_keydb.ps1
```

**安装脚本会自动**:
- ✅ 下载 KeyDB
- ✅ 解压到 C:\keydb
- ✅ 创建配置文件
- ✅ 创建启动脚本

### 步骤 2：启动 KeyDB（30 秒）

**方法 A：使用启动脚本（推荐）**
```powershell
# 双击运行或命令行执行
C:\keydb\start_keydb.ps1
```

**方法 B：手动启动**
```powershell
cd C:\keydb
.\keydb-server.exe keydb.conf
```

### 步骤 3：验证安装（30 秒）

```powershell
# 测试连接
C:\keydb\keydb-cli.exe ping

# 应该返回：PONG
```

### 步骤 4：重启应用（1 分钟）

```powershell
# 进入项目目录
cd d:\Trae\spare_management

# 重启 Flask 应用
python run.py

# 查看日志，应该看到:
# [INFO] Redis 连接成功
```

---

## 📝 完整文档

详细安装和使用指南请查看:
- [`KeyDB 安装与使用指南.md`](KeyDB 安装与使用指南.md)
- [`Redis 替代方案对比.md`](Redis 替代方案对比.md)

---

## 🔧 常用命令

### 启动/停止

```powershell
# 启动
C:\keydb\start_keydb.ps1

# 停止
C:\keydb\stop_keydb.ps1

# 或手动控制
C:\keydb\keydb-server.exe keydb.conf  # 启动
C:\keydb\keydb-cli.exe SHUTDOWN       # 停止
```

### 测试连接

```powershell
# CLI 连接
C:\keydb\keydb-cli.exe

# 测试命令
127.0.0.1:6379> PING
PONG

127.0.0.1:6379> SET test "hello"
OK

127.0.0.1:6379> GET test
"hello"
```

### 查看状态

```powershell
# 检查进程
Get-Process | Where-Object {$_.ProcessName -like "*keydb*"}

# 检查端口
netstat -ano | findstr :6379

# 查看日志
Get-Content C:\keydb\keydb.log -Tail 20
```

---

## ❓ 故障排查

### 问题 1：安装脚本下载失败

**解决**:
1. 手动访问：https://keydb.dev/downloads/
2. 下载 Windows 版本
3. 解压到 `C:\keydb`

### 问题 2：启动失败

**检查**:
```powershell
# 查看日志
Get-Content C:\keydb\keydb.log

# 检查端口占用
netstat -ano | findstr :6379
```

**解决**:
- 如果端口被占用，终止占用进程
- 或修改配置文件使用其他端口

### 问题 3：应用连接失败

**检查**:
1. KeyDB 是否运行：`C:\keydb\keydb-cli.exe ping`
2. 配置是否正确：`cat .env`
3. 防火墙是否阻止

**解决**:
```powershell
# 允许防火墙
netsh advfirewall firewall add rule name="KeyDB" dir=in action=allow protocol=TCP localport=6379
```

---

## 🎯 为什么选择 KeyDB？

| 特性 | Redis | KeyDB |
|------|-------|-------|
| Windows 支持 | ❌ | ✅ |
| 性能 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 多线程 | ❌ | ✅ |
| 代码修改 | 需要 | 不需要 |
| 部署难度 | 困难 | 简单 |

**KeyDB 优势**:
- ✅ 100% Redis 兼容 - 无需修改代码
- ✅ 性能提升 2-5 倍 - 多线程架构
- ✅ Windows 原生支持 - 无需 Docker
- ✅ 单文件运行 - 下载即用

---

## 📞 获取帮助

如果遇到问题:
1. 查看详细文档：[`KeyDB 安装与使用指南.md`](KeyDB 安装与使用指南.md)
2. 查看 KeyDB 日志：`C:\keydb\keydb.log`
3. 查看官方文档：https://docs.keydb.dev/

---

**祝您使用愉快！** 🎉
