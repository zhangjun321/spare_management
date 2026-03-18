@echo off
chcp 65001
echo ========================================
echo 备件管理系统 - 恢复脚本
echo ========================================
echo.

set BACKUP_FILE=%1
set RESTORE_DIR=D:\Trae\spare_management

if "%BACKUP_FILE%"=="" (
    echo 用法：restore.bat ^<备份文件路径^>
    echo.
    echo 示例：
    echo   restore.bat E:\Backup\spare_management\spare_management_backup_20260318.zip
    echo.
    pause
    exit /b
)

if not exist "%BACKUP_FILE%" (
    echo 错误：备份文件不存在！
    echo 文件路径：%BACKUP_FILE%
    pause
    exit /b
)

echo [1/3] 解压备份文件...
set TEMP_RESTORE_DIR=D:\Trae\temp_restore
if exist "%TEMP_RESTORE_DIR%" rmdir /s /q "%TEMP_RESTORE_DIR%"
mkdir "%TEMP_RESTORE_DIR%"

if exist "C:\Program Files\7-Zip\7z.exe" (
    "C:\Program Files\7-Zip\7z.exe" x "%BACKUP_FILE%" -o"%TEMP_RESTORE_DIR%" -y
) else (
    echo 错误：未安装 7-Zip，无法解压备份文件！
    echo 请先安装 7-Zip: https://www.7-zip.org/
    pause
    exit /b
)

echo [2/3] 恢复文件...
robocopy "%TEMP_RESTORE_DIR%" "%RESTORE_DIR%" /MIR /NFL /NDL

echo [3/3] 清理临时文件...
rmdir /s /q "%TEMP_RESTORE_DIR%"

echo.
echo ========================================
echo 恢复完成！
echo 恢复目录：%RESTORE_DIR%
echo ========================================
echo.
echo 提示：请手动执行以下操作
echo 1. 检查 .env 配置文件是否正确
echo 2. 检查数据库连接是否正常
echo 3. 运行 git status 检查 Git 状态
echo.
pause
