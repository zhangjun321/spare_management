# Redis 配置检查脚本
# 用于诊断 Redis 连接问题

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Redis 配置检查工具" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Redis 是否安装
Write-Host "1. 检查 Redis 安装状态" -ForegroundColor Yellow
try {
    $redisCli = Get-Command redis-cli -ErrorAction SilentlyContinue
    if ($redisCli) {
        Write-Host "   ✓ Redis CLI 已安装" -ForegroundColor Green
        Write-Host "     路径：$($redisCli.Source)" -ForegroundColor Gray
        
        # 测试连接
        Write-Host "   正在测试连接..." -ForegroundColor Gray
        try {
            $pingResult = redis-cli ping 2>&1
            if ($pingResult -eq "PONG") {
                Write-Host "   ✓ Redis 连接成功！" -ForegroundColor Green
                
                # 获取 Redis 信息
                Write-Host "   Redis 信息:" -ForegroundColor Cyan
                $info = redis-cli info server 2>&1
                $info | Select-String "redis_version|tcp_port|uptime|os" | ForEach-Object {
                    Write-Host "     $_" -ForegroundColor Gray
                }
            } else {
                Write-Host "   ✗ Redis 连接失败：$pingResult" -ForegroundColor Red
            }
        } catch {
            Write-Host "   ✗ Redis 未运行或无法连接" -ForegroundColor Red
        }
    } else {
        Write-Host "   ✗ Redis CLI 未安装" -ForegroundColor Red
    }
} catch {
    Write-Host "   ✗ 检查失败：$_" -ForegroundColor Red
}

Write-Host ""

# 2. 检查 Docker Redis
Write-Host "2. 检查 Docker Redis 容器" -ForegroundColor Yellow
try {
    $dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerInstalled) {
        Write-Host "   ✓ Docker 已安装" -ForegroundColor Green
        
        # 检查 Docker 是否运行
        try {
            docker ps | Out-Null
            Write-Host "   ✓ Docker 正在运行" -ForegroundColor Green
            
            # 检查 Redis 容器
            $redisContainer = docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String "redis"
            if ($redisContainer) {
                Write-Host "   ✓ 发现 Redis 容器:" -ForegroundColor Green
                $redisContainer | ForEach-Object {
                    Write-Host "     $_" -ForegroundColor Gray
                }
                
                # 检查是否运行
                if ($redisContainer -match "Up") {
                    Write-Host "   ✓ Redis 容器正在运行" -ForegroundColor Green
                    
                    # 测试连接
                    Write-Host "   测试容器内 Redis 连接..." -ForegroundColor Gray
                    $pingResult = docker exec redis redis-cli ping 2>&1
                    if ($pingResult -eq "PONG") {
                        Write-Host "   ✓ 容器内 Redis 连接成功！" -ForegroundColor Green
                    } else {
                        Write-Host "   ✗ 容器内 Redis 连接失败" -ForegroundColor Red
                    }
                } else {
                    Write-Host "   ⚠ Redis 容器未运行" -ForegroundColor Yellow
                    Write-Host "     启动命令：docker start redis" -ForegroundColor Cyan
                }
            } else {
                Write-Host "   ✗ 未发现 Redis 容器" -ForegroundColor Red
            }
        } catch {
            Write-Host "   ✗ Docker 未运行" -ForegroundColor Red
        }
    } else {
        Write-Host "   ✗ Docker 未安装" -ForegroundColor Red
    }
} catch {
    Write-Host "   ✗ 检查失败：$_" -ForegroundColor Red
}

Write-Host ""

# 3. 检查 Redis 服务
Write-Host "3. 检查 Windows Redis 服务" -ForegroundColor Yellow
try {
    $redisService = Get-Service -Name "Redis" -ErrorAction SilentlyContinue
    if ($redisService) {
        Write-Host "   ✓ Redis 服务已安装" -ForegroundColor Green
        Write-Host "     状态：$($redisService.Status)" -ForegroundColor Gray
        
        if ($redisService.Status -eq "Running") {
            Write-Host "   ✓ Redis 服务正在运行" -ForegroundColor Green
        } else {
            Write-Host "   ⚠ Redis 服务未运行" -ForegroundColor Yellow
            Write-Host "     启动命令：net start Redis" -ForegroundColor Cyan
        }
    } else {
        Write-Host "   ✗ Redis 服务未安装" -ForegroundColor Red
    }
} catch {
    Write-Host "   ✗ 服务检查失败：$_" -ForegroundColor Red
}

Write-Host ""

# 4. 检查端口占用
Write-Host "4. 检查 6379 端口" -ForegroundColor Yellow
try {
    $port = Get-NetTCPConnection -LocalPort 6379 -ErrorAction SilentlyContinue
    if ($port) {
        Write-Host "   ✓ 端口 6379 正在监听" -ForegroundColor Green
        Write-Host "     进程 ID: $($port.OwningProcess)" -ForegroundColor Gray
        
        # 获取进程信息
        try {
            $process = Get-Process -Id $port.OwningProcess -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "     进程名称：$($process.ProcessName)" -ForegroundColor Gray
            }
        } catch {}
    } else {
        Write-Host "   ⚠ 端口 6379 未被占用" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠ 无法检查端口（可能需要管理员权限）" -ForegroundColor Yellow
}

Write-Host ""

# 5. 检查防火墙规则
Write-Host "5. 检查防火墙规则" -ForegroundColor Yellow
try {
    $firewallRules = Get-NetFirewallRule -DisplayName "*Redis*" -ErrorAction SilentlyContinue
    if ($firewallRules) {
        Write-Host "   ✓ 发现 Redis 防火墙规则:" -ForegroundColor Green
        $firewallRules | ForEach-Object {
            $status = if ($_.Enabled) { "已启用" } else { "已禁用" }
            Write-Host "     $($_.DisplayName): $status" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⚠ 未发现 Redis 防火墙规则" -ForegroundColor Yellow
        Write-Host "     如果需要远程访问，请添加防火墙规则:" -ForegroundColor Cyan
        Write-Host "     netsh advfirewall firewall add rule name=`"Redis`" dir=in action=allow protocol=TCP localport=6379" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠ 无法检查防火墙规则（可能需要管理员权限）" -ForegroundColor Yellow
}

Write-Host ""

# 6. 检查应用配置
Write-Host "6. 检查应用配置" -ForegroundColor Yellow
$envFile = ".env"
if (Test-Path $envFile) {
    Write-Host "   ✓ .env 文件存在" -ForegroundColor Green
    
    # 读取 Redis 配置
    $envContent = Get-Content $envFile
    $redisConfigs = $envContent | Select-String "^REDIS_"
    
    if ($redisConfigs) {
        Write-Host "   Redis 配置:" -ForegroundColor Cyan
        $redisConfigs | ForEach-Object {
            Write-Host "     $_" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⚠ 未发现 Redis 配置" -ForegroundColor Yellow
        Write-Host "     默认配置：localhost:6379, db=0" -ForegroundColor Cyan
    }
} else {
    Write-Host "   ✗ .env 文件不存在" -ForegroundColor Red
    Write-Host "     提示：复制 .env.example 为 .env" -ForegroundColor Cyan
}

Write-Host ""

# 7. 检查 Python redis 包
Write-Host "7. 检查 Python redis 包" -ForegroundColor Yellow
try {
    $redisPackage = pip show redis 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Python redis 包已安装" -ForegroundColor Green
        $redisPackage | Select-String "Version" | ForEach-Object {
            Write-Host "     $_" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ✗ Python redis 包未安装" -ForegroundColor Red
        Write-Host "     安装命令：pip install redis" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   ✗ 检查失败：$_" -ForegroundColor Red
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  检查完成" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 总结和建议
Write-Host "诊断建议:" -ForegroundColor Cyan
Write-Host ""

$hasRedis = (redis-cli ping 2>&1 -eq "PONG") -or (docker exec redis redis-cli ping 2>&1 -eq "PONG")

if ($hasRedis) {
    Write-Host "✓ Redis 可以正常连接，如果应用仍然报错，请检查:" -ForegroundColor Green
    Write-Host "  1. 应用的 Redis 配置是否正确" -ForegroundColor White
    Write-Host "  2. Redis 密码是否正确（如果设置了密码）" -ForegroundColor White
    Write-Host "  3. 应用是否有权限访问 Redis" -ForegroundColor White
} else {
    Write-Host "✗ Redis 未安装或未运行，建议:" -ForegroundColor Red
    Write-Host ""
    Write-Host "  方案 1 (推荐): 使用 Docker 安装 Redis" -ForegroundColor Cyan
    Write-Host "    docker run -d -p 6379:6379 --name redis redis:latest" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  方案 2: 使用 PowerShell 脚本安装" -ForegroundColor Cyan
    Write-Host "    .\install_redis.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  方案 3: 临时使用内存缓存" -ForegroundColor Cyan
    Write-Host "    在 .env 文件中添加:" -ForegroundColor Gray
    Write-Host "    CACHE_TYPE=SimpleCache" -ForegroundColor White
    Write-Host ""
    Write-Host "  详细安装指南请查看：docs\Redis 安装与配置指南.md" -ForegroundColor Cyan
}

Write-Host ""
