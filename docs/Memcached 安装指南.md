# Memcached Windows 安装指南

## 📖 简介

**Memcached** 是高性能分布式内存对象缓存系统，Windows 原生支持。

**核心优势**:
- ✅ Windows 原生支持 - 无需 Docker
- ✅ 成熟稳定 - 2003 年至今
- ✅ 单文件运行 - 简单易用
- ✅ 性能优秀 - 大规模应用验证
- ✅ 资源占用少 - 轻量级

**注意**: Memcached 仅支持简单 KV 缓存，需要修改部分代码适配。

---

## 一、下载 Memcached

### 官方下载

1. 访问：https://memcached.org/
2. 或 GitHub: https://github.com/memcached/memcached

### Windows 版本下载

**推荐下载源**:
- CodeHero: https://www.codehero.net/download-memcached-for-windows/
- GitHub Releases: https://github.com/memcached/memcached/releases

### 直接下载命令

```powershell
# 创建安装目录
New-Item -ItemType Directory -Force -Path "C:\memcached"

# 下载最新稳定版（示例，请替换为实际链接）
$url = "https://github.com/memcached/memcached/releases/download/1.6.17/memcached-1.6.17-windows-amd64.zip"
$output = "C:\memcached\memcached.zip"

# 下载
Invoke-WebRequest -Uri $url -OutFile $output

# 解压
Expand-Archive -Path $output -DestinationPath "C:\memcached" -Force
```

---

## 二、安装 Memcached

### 2.1 解压文件

```powershell
# 解压后目录结构:
# C:\memcached\
#   ├── memcached.exe
#   └── ...
```

### 2.2 安装为 Windows 服务

```powershell
# 1. 以管理员身份运行 PowerShell
# 2. 进入目录
cd C:\memcached

# 3. 安装服务
.\memcached.exe -d install

# 4. 启动服务
net start memcached

# 5. 查看服务状态
sc query memcached
```

### 2.3 手动启动（测试用）

```powershell
# 前台运行（测试用）
.\memcached.exe -m 64 -p 11211 -l 127.0.0.1

# 后台运行
.\memcached.exe -d run -m 64 -p 11211 -l 127.0.0.1
```

**参数说明**:
- `-m 64`: 使用 64MB 内存
- `-p 11211`: 监听端口 11211
- `-l 127.0.0.1`: 绑定本地地址
- `-d`: 以守护进程模式运行

---

## 三、验证安装

### 3.1 检查服务

```powershell
# 查看进程
Get-Process | Where-Object {$_.ProcessName -like "*memcached*"}

# 查看端口
netstat -ano | findstr :11211

# 查看服务
sc query memcached
```

### 3.2 测试连接

**方法 1：使用 Telnet**
```powershell
# 启用 Telnet 客户端（如果未启用）
# 控制面板 -> 程序和功能 -> 启用或关闭 Windows 功能 -> Telnet 客户端

# 连接
telnet localhost 11211

# 测试命令
stats
quit
```

**方法 2：使用 PowerShell**
```powershell
# 创建测试脚本
$test = @"
using System;
using System.Net.Sockets;
using System.Text;

class Test {
    static void Main() {
        TcpClient client = new TcpClient("localhost", 11211);
        NetworkStream stream = client.GetStream();
        
        // 发送 stats 命令
        byte[] data = Encoding.ASCII.GetBytes("stats\r\n");
        stream.Write(data, 0, data.Length);
        
        // 读取响应
        byte[] buffer = new byte[4096];
        int bytesRead = stream.Read(buffer, 0, buffer.Length);
        Console.WriteLine(Encoding.ASCII.GetString(buffer, 0, bytesRead));
        
        client.Close();
    }
}
"@

Add-Type -TypeDefinition $test
[Test]::Main()
```

**预期输出**: 应该看到 Memcached 统计信息

---

## 四、配置应用

### 4.1 安装 Python 客户端

```powershell
# 进入项目目录
cd d:\Trae\spare_management

# 安装 pymemcache
pip install pymemcache

# 或安装 python-binary-memcached
pip install bmemcached
```

### 4.2 修改项目配置

修改 `.env` 文件：

```env
# Memcached 配置
MEMCACHED_HOST=localhost
MEMCACHED_PORT=11211
```

### 4.3 修改缓存服务

修改 `app/services/cache_service.py`，添加 Memcached 支持：

```python
# 在文件开头添加
try:
    import pymemcache
    from pymemcache.client import base
    MEMCACHED_AVAILABLE = True
except ImportError:
    MEMCACHED_AVAILABLE = False

# 修改 RedisCacheService 类或创建 MemcachedCacheService 类
class MemcachedCacheService:
    """Memcached 缓存服务"""
    
    def __init__(self, app=None):
        self.client = None
        self.default_timeout = 300
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化 Memcached 连接"""
        if not MEMCACHED_AVAILABLE:
            app.logger.warning('pymemcache 未安装')
            return
        
        try:
            host = app.config.get('MEMCACHED_HOST', 'localhost')
            port = app.config.get('MEMCACHED_PORT', 11211)
            
            self.client = base.Client((host, port))
            app.logger.info('Memcached 连接成功')
        except Exception as e:
            app.logger.warning(f'Memcached 连接失败：{str(e)}')
            self.client = None
    
    def get(self, key):
        """获取缓存"""
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                import json
                return json.loads(value.decode('utf-8'))
            return None
        except Exception as e:
            current_app.logger.error(f'Memcached GET 错误：{str(e)}')
            return None
    
    def set(self, key, value, timeout=None):
        """设置缓存"""
        if not self.client:
            return False
        
        if timeout is None:
            timeout = self.default_timeout
        
        try:
            import json
            serialized = json.dumps(value, ensure_ascii=False, default=str).encode('utf-8')
            self.client.set(key, serialized, expire=timeout)
            return True
        except Exception as e:
            current_app.logger.error(f'Memcached SET 错误：{str(e)}')
            return False
    
    def delete(self, key):
        """删除缓存"""
        if not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            current_app.logger.error(f'Memcached DELETE 错误：{str(e)}')
            return False
```

### 4.4 修改应用初始化

修改 `app/__init__.py`：

```python
# 修改缓存服务初始化
def init_app(app):
    # ...现有代码...
    
    # 初始化缓存服务（优先 Redis，其次 Memcached）
    if app.config.get('USE_MEMCACHED', False):
        from app.services.cache_service import MemcachedCacheService
        cache_service = MemcachedCacheService()
        cache_service.init_app(app)
        app.extensions['cache'] = cache_service
        app.logger.info('使用 Memcached 作为缓存后端')
    else:
        from app.services.cache_service import init_cache
        init_cache(app)
        app.logger.info('使用 Redis 作为缓存后端')
```

---

## 五、常用命令

### 5.1 服务管理

```powershell
# 启动服务
net start memcached

# 停止服务
net stop memcached

# 重启服务
net stop memcached && net start memcached

# 查看状态
sc query memcached

# 删除服务
sc delete memcached
```

### 5.2 监控命令

```powershell
# 查看进程
Get-Process memcached

# 查看端口
netstat -ano | findstr :11211

# 查看内存使用
Get-Process memcached | Select-Object WorkingSet, VirtualMemorySize
```

### 5.3 性能调优

```powershell
# 停止服务
net stop memcached

# 修改启动参数（通过注册表）
# 128MB 内存，端口 11211，绑定本地
.\memcached.exe -m 128 -p 11211 -l 127.0.0.1 -d run

# 或使用服务配置
sc config memcached binPath= "C:\memcached\memcached.exe -m 128 -p 11211 -l 127.0.0.1"
```

---

## 六、故障排查

### 问题 1：服务无法启动

**症状**: `net start memcached` 失败

**解决**:
```powershell
# 1. 查看事件日志
Get-EventLog -LogName Application -Source memcached -Newest 10

# 2. 手动运行查看详细错误
.\memcached.exe -vv

# 3. 检查端口占用
netstat -ano | findstr :11211
```

### 问题 2：连接被拒绝

**症状**: `Connection refused`

**解决**:
```powershell
# 1. 检查服务是否运行
Get-Process | Where-Object {$_.ProcessName -like "*memcached*"}

# 2. 检查防火墙
netsh advfirewall firewall show rule name=all | findstr 11211

# 3. 允许端口
netsh advfirewall firewall add rule name="Memcached" dir=in action=allow protocol=TCP localport=11211
```

### 问题 3：内存不足

**症状**: `Out of memory`

**解决**:
```powershell
# 1. 停止服务
net stop memcached

# 2. 增加内存限制
.\memcached.exe -m 256 -d run

# 3. 或修改服务配置
sc config memcached binPath= "C:\memcached\memcached.exe -m 256"
```

---

## 七、性能优化

### 7.1 调整内存

```powershell
# 根据系统内存调整
# -m 512: 512MB
# -m 1024: 1GB
sc config memcached binPath= "C:\memcached\memcached.exe -m 512"
```

### 7.2 调整连接数

```powershell
# -c 1024: 最大 1024 个并发连接
sc config memcached binPath= "C:\memcached\memcached.exe -c 1024"
```

### 7.3 调整线程数

```powershell
# -t 4: 使用 4 个线程
sc config memcached binPath= "C:\memcached\memcached.exe -t 4"
```

---

## 八、安全建议

### 8.1 绑定本地地址

```powershell
# 仅允许本地访问
sc config memcached binPath= "C:\memcached\memcached.exe -l 127.0.0.1"
```

### 8.2 防火墙配置

```powershell
# 限制本地访问
netsh advfirewall firewall add rule name="Memcached Local" dir=in action=allow protocol=TCP localport=11211 remoteip=127.0.0.1
```

### 8.3 禁用 UDP

```powershell
# -U 0: 禁用 UDP
sc config memcached binPath= "C:\memcached\memcached.exe -U 0"
```

---

## 九、快速参考

### 一键安装命令
```powershell
# 1. 创建目录
New-Item -ItemType Directory -Force -Path "C:\memcached"

# 2. 下载（替换为实际链接）
$url = "https://github.com/memcached/memcached/releases/download/1.6.17/memcached-1.6.17-windows-amd64.zip"
Invoke-WebRequest -Uri $url -OutFile "C:\memcached\memcached.zip"

# 3. 解压
Expand-Archive -Path "C:\memcached\memcached.zip" -DestinationPath "C:\memcached" -Force

# 4. 安装服务
cd C:\memcached
.\memcached.exe -d install

# 5. 启动
net start memcached
```

### 测试连接
```powershell
# Telnet
telnet localhost 11211

# PowerShell
Test-NetConnection -ComputerName localhost -Port 11211
```

### 查看状态
```powershell
# 进程
Get-Process memcached

# 端口
netstat -ano | findstr :11211

# 服务
sc query memcached
```

---

## 十、与 Redis 对比

| 特性 | Redis | Memcached |
|------|-------|-----------|
| 数据结构 | 丰富（Hash、List 等） | 简单 KV |
| 持久化 | ✅ | ❌ |
| 多线程 | ❌ | ✅ |
| Windows 支持 | ⚠️ | ✅ |
| 性能 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 内存效率 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 复杂度 | 中等 | 简单 |

---

## 十一、总结

### 为什么选择 Memcached？

**优点**:
- ✅ Windows 原生支持
- ✅ 部署简单
- ✅ 性能优秀
- ✅ 成熟稳定

**缺点**:
- ❌ 仅支持简单 KV
- ❌ 不支持持久化
- ❌ 需要修改代码适配

### 适用场景

**推荐使用**:
- 简单缓存场景
- 不需要持久化
- 追求极简部署

**不推荐**:
- 需要复杂数据结构
- 需要数据持久化
- 需要发布订阅功能

---

## 附录：资源链接

- 官网：https://memcached.org/
- GitHub: https://github.com/memcached/memcached
- 文档：https://github.com/memcached/memcached/wiki
- Windows 下载：https://www.codehero.net/download-memcached-for-windows/
