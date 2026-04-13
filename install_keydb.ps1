# KeyDB 快速安装脚本（Windows）
# 适用于 Windows 7/8/10/11

$ErrorActionPreference = "Stop"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  KeyDB 自动安装脚本" -ForegroundColor Cyan
Write-Host "  Windows 版本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 配置参数
$KeyDBVersion = "6.3.4"
$InstallDir = "C:\keydb"
$DownloadUrl = "https://github.com/Snapchat/keydb/releases/download/v$KeyDBVersion/KeyDB-$KeyDBVersion-Windows.zip"
$OutputFile = "$InstallDir\keydb.zip"

Write-Host "[1/6] 创建安装目录..." -ForegroundColor Yellow
if (!(Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    Write-Host "  ✓ 目录已创建：$InstallDir" -ForegroundColor Green
} else {
    Write-Host "  ✓ 目录已存在：$InstallDir" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/6] 下载 KeyDB..." -ForegroundColor Yellow
Write-Host "  下载地址：$DownloadUrl" -ForegroundColor Gray

try {
    # 检查网络连接
    Test-Connection -ComputerName github.com -Count 1 -Quiet -ErrorAction Stop | Out-Null
    
    # 下载文件
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $OutputFile -UseBasicParsing
    
    Write-Host "  ✓ 下载完成" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 下载失败：$($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "请手动下载 KeyDB:" -ForegroundColor Yellow
    Write-Host "1. 访问：https://keydb.dev/downloads/" -ForegroundColor Cyan
    Write-Host "2. 下载 Windows 版本" -ForegroundColor Cyan
    Write-Host "3. 解压到：$InstallDir" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "按任意键退出..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host ""
Write-Host "[3/6] 解压文件..." -ForegroundColor Yellow

try {
    Expand-Archive -Path $OutputFile -DestinationPath $InstallDir -Force
    Write-Host "  ✓ 解压完成" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 解压失败：$($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[4/6] 创建配置文件..." -ForegroundColor Yellow

# 创建配置文件
$ConfigContent = @"
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
logfile "$InstallDir\keydb.log"

# 持久化 - RDB
save 900 1
save 300 10
save 60 10000
dbfilename dump.rdb
dir $InstallDir\data

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
"@

$ConfigContent | Out-File -FilePath "$InstallDir\keydb.conf" -Encoding UTF8
Write-Host "  ✓ 配置文件已创建" -ForegroundColor Green

Write-Host ""
Write-Host "[5/6] 创建数据目录..." -ForegroundColor Yellow

if (!(Test-Path "$InstallDir\data")) {
    New-Item -ItemType Directory -Force -Path "$InstallDir\data" | Out-Null
    Write-Host "  ✓ 数据目录已创建" -ForegroundColor Green
} else {
    Write-Host "  ✓ 数据目录已存在" -ForegroundColor Green
}

Write-Host ""
Write-Host "[6/6] 创建启动脚本..." -ForegroundColor Yellow

# 创建启动脚本
$StartupScript = @"
# KeyDB 启动脚本
`$KeyDBPath = "$InstallDir"
`$ConfigFile = "`$KeyDBPath\keydb.conf"

Write-Host "正在启动 KeyDB..." -ForegroundColor Green

# 启动 KeyDB
Start-Process -FilePath "`$KeyDBPath\keydb-server.exe" `
              -ArgumentList `$ConfigFile `
              -WindowStyle Hidden

# 等待启动
Start-Sleep -Seconds 3

# 验证
`$test = & "`$KeyDBPath\keydb-cli.exe" ping
if (`$test -eq "PONG") {
    Write-Host "KeyDB 启动成功！" -ForegroundColor Green
    Write-Host "连接地址：localhost:6379" -ForegroundColor Cyan
} else {
    Write-Host "KeyDB 启动失败" -ForegroundColor Red
    Write-Host "请查看日志：`$KeyDBPath\keydb.log" -ForegroundColor Yellow
}
"@

$StartupScript | Out-File -FilePath "$InstallDir\start_keydb.ps1" -Encoding UTF8
Write-Host "  ✓ 启动脚本已创建" -ForegroundColor Green

# 创建停止脚本
$StopScript = @"
# KeyDB 停止脚本
`$KeyDBPath = "$InstallDir"

Write-Host "正在停止 KeyDB..." -ForegroundColor Yellow
& "`$KeyDBPath\keydb-cli.exe" SHUTDOWN
Write-Host "KeyDB 已停止" -ForegroundColor Green
"@

$StopScript | Out-File -FilePath "$InstallDir\stop_keydb.ps1" -Encoding UTF8
Write-Host "  ✓ 停止脚本已创建" -ForegroundColor Green

# 清理下载文件
Remove-Item $OutputFile -Force

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  KeyDB 安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "安装位置：$InstallDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "快速启动:" -ForegroundColor Yellow
Write-Host "  1. 双击运行：$InstallDir\start_keydb.ps1" -ForegroundColor White
Write-Host "  2. 或手动启动：cd $InstallDir && .\keydb-server.exe keydb.conf" -ForegroundColor White
Write-Host ""
Write-Host "测试连接:" -ForegroundColor Yellow
Write-Host "  cd $InstallDir" -ForegroundColor White
Write-Host "  .\keydb-cli.exe ping" -ForegroundColor White
Write-Host "  应该返回：PONG" -ForegroundColor Green
Write-Host ""
Write-Host "配置应用连接:" -ForegroundColor Yellow
Write-Host "  修改 .env 文件:" -ForegroundColor White
Write-Host "  REDIS_HOST=localhost" -ForegroundColor Cyan
Write-Host "  REDIS_PORT=6379" -ForegroundColor Cyan
Write-Host ""
Write-Host "按任意键继续..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
