# Redis 快速安装脚本（Windows PowerShell）
# 使用方法：以管理员身份运行 PowerShell，然后执行 .\install_redis.ps1

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Redis 快速安装脚本 (Windows)" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否已安装 Redis
Write-Host "正在检查 Redis 安装状态..." -ForegroundColor Yellow
try {
    $redisTest = redis-cli ping -ErrorAction SilentlyContinue
    if ($redisTest -eq "PONG") {
        Write-Host "✓ Redis 已安装并正在运行！" -ForegroundColor Green
        Write-Host ""
        Write-Host "Redis 信息:" -ForegroundColor Cyan
        redis-cli info server | Select-String "redis_version|tcp_port|uptime"
        exit 0
    }
} catch {
    Write-Host "Redis 未安装或未运行" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "请选择安装方式:" -ForegroundColor Cyan
Write-Host "1. 使用 Chocolatey 安装（推荐，需要已安装 Chocolatey）" -ForegroundColor White
Write-Host "2. 使用 Docker 安装（需要已安装 Docker Desktop）" -ForegroundColor White
Write-Host "3. 下载 MSI 安装包（手动安装）" -ForegroundColor White
Write-Host "4. 使用内存缓存（临时方案，无需安装 Redis）" -ForegroundColor White
Write-Host "5. 退出" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选项 (1-5)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "正在使用 Chocolatey 安装 Redis..." -ForegroundColor Yellow
        
        # 检查 Chocolatey
        if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
            Write-Host "✗ Chocolatey 未安装！" -ForegroundColor Red
            Write-Host "请先安装 Chocolatey: https://chocolatey.org/install" -ForegroundColor Yellow
            exit 1
        }
        
        # 安装 Redis
        Write-Host "正在安装 Redis-64..." -ForegroundColor Cyan
        choco install redis-64 -y
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Redis 安装成功！" -ForegroundColor Green
            Write-Host "正在启动 Redis 服务..." -ForegroundColor Yellow
            redis-server --service-start
            
            Write-Host "正在验证安装..." -ForegroundColor Yellow
            Start-Sleep -Seconds 2
            redis-cli ping
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Redis 已成功安装并启动！" -ForegroundColor Green
            } else {
                Write-Host "✗ Redis 启动失败，请手动启动：redis-server --service-start" -ForegroundColor Red
            }
        } else {
            Write-Host "✗ Redis 安装失败！" -ForegroundColor Red
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "正在使用 Docker 安装 Redis..." -ForegroundColor Yellow
        
        # 检查 Docker
        if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
            Write-Host "✗ Docker 未安装！" -ForegroundColor Red
            Write-Host "请先安装 Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
            exit 1
        }
        
        # 检查 Docker 是否运行
        try {
            docker ps | Out-Null
        } catch {
            Write-Host "✗ Docker 未运行！请启动 Docker Desktop" -ForegroundColor Red
            exit 1
        }
        
        # 检查是否已有 Redis 容器
        $existingRedis = docker ps -a --format "{{.Names}}" | Select-String "^redis$"
        if ($existingRedis) {
            Write-Host "发现已存在的 Redis 容器，正在删除..." -ForegroundColor Yellow
            docker rm -f redis
        }
        
        # 拉取镜像
        Write-Host "正在拉取 Redis 镜像..." -ForegroundColor Cyan
        docker pull redis:latest
        
        # 启动容器
        Write-Host "正在启动 Redis 容器..." -ForegroundColor Cyan
        docker run -d -p 6379:6379 --name redis redis:latest
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Redis 容器已成功启动！" -ForegroundColor Green
            Write-Host ""
            Write-Host "Redis 信息:" -ForegroundColor Cyan
            docker exec redis redis-cli info server | Select-String "redis_version|tcp_port"
            
            Write-Host ""
            Write-Host "验证连接..." -ForegroundColor Yellow
            docker exec redis redis-cli ping
            
            Write-Host ""
            Write-Host "常用命令:" -ForegroundColor Cyan
            Write-Host "  停止：docker stop redis" -ForegroundColor White
            Write-Host "  启动：docker start redis" -ForegroundColor White
            Write-Host "  重启：docker restart redis" -ForegroundColor White
            Write-Host "  删除：docker rm -f redis" -ForegroundColor White
            Write-Host "  查看日志：docker logs redis" -ForegroundColor White
        } else {
            Write-Host "✗ Redis 容器启动失败！" -ForegroundColor Red
        }
    }
    
    "3" {
        Write-Host ""
        Write-Host "MSI 安装包下载:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "选项 1: Microsoft Archive Redis (推荐)" -ForegroundColor White
        Write-Host "  下载地址：https://github.com/microsoftarchive/redis/releases" -ForegroundColor Yellow
        Write-Host "  文件：Redis-x64-3.0.504.msi" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "选项 2: tporadowski/redis (更新版本)" -ForegroundColor White
        Write-Host "  下载地址：https://github.com/tporadowski/redis/releases" -ForegroundColor Yellow
        Write-Host "  文件：Redis-x64-5.0.14.1.msi" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "安装步骤:" -ForegroundColor Cyan
        Write-Host "  1. 下载 MSI 安装包" -ForegroundColor White
        Write-Host "  2. 双击运行安装包" -ForegroundColor White
        Write-Host "  3. 按照安装向导完成安装" -ForegroundColor White
        Write-Host "  4. 安装完成后，Redis 会自动作为服务启动" -ForegroundColor White
        Write-Host ""
        Write-Host "验证安装:" -ForegroundColor Cyan
        Write-Host "  redis-cli ping" -ForegroundColor White
        Write-Host "  应该返回：PONG" -ForegroundColor Green
    }
    
    "4" {
        Write-Host ""
        Write-Host "配置内存缓存（临时方案）..." -ForegroundColor Yellow
        Write-Host ""
        
        # 检查 .env 文件
        $envFile = ".env"
        if (-not (Test-Path $envFile)) {
            Write-Host "未找到 .env 文件，正在创建..." -ForegroundColor Yellow
            Copy-Item ".env.example" -Destination ".env"
        }
        
        # 添加缓存配置
        Write-Host "正在修改 .env 文件..." -ForegroundColor Cyan
        $cacheConfig = @"

# ===========================================
# 缓存配置（内存缓存）
# ===========================================
CACHE_TYPE=SimpleCache
CACHE_DEFAULT_TIMEOUT=300
"@
        
        # 检查是否已存在缓存配置
        $envContent = Get-Content $envFile -Raw
        if ($envContent -match "CACHE_TYPE") {
            Write-Host "缓存配置已存在" -ForegroundColor Yellow
        } else {
            Add-Content -Path $envFile -Value $cacheConfig
            Write-Host "✓ 缓存配置已添加到 .env 文件" -ForegroundColor Green
        }
        
        Write-Host ""
        Write-Host "内存缓存特点:" -ForegroundColor Cyan
        Write-Host "  ✓ 无需安装 Redis" -ForegroundColor Green
        Write-Host "  ✓ 配置简单" -ForegroundColor Green
        Write-Host "  ✗ 应用重启后缓存丢失" -ForegroundColor Red
        Write-Host "  ✗ 仅支持单机，不支持集群" -ForegroundColor Red
        Write-Host ""
        Write-Host "提示：生产环境建议使用 Redis 或云 Redis 服务" -ForegroundColor Yellow
    }
    
    "5" {
        Write-Host "已退出安装程序" -ForegroundColor Yellow
        exit 0
    }
    
    default {
        Write-Host "无效的选项！" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  安装完成" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
