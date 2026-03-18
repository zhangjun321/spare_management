@echo off
chcp 65001
echo ========================================
echo 备件管理系统 - 自动备份脚本
echo ========================================
echo.

set BACKUP_DATE=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%
set BACKUP_DIR=E:\Backup\spare_management\%BACKUP_DATE%
set SOURCE_DIR=D:\Trae\spare_management

echo [1/4] 创建备份目录...
if not exist "E:\Backup\spare_management" mkdir "E:\Backup\spare_management"
mkdir "%BACKUP_DIR%"

echo [2/4] 排除临时文件...
robocopy "%SOURCE_DIR%" "%BACKUP_DIR%" /MIR /XD __pycache__ venv .git .vscode .idea /XF *.pyc *.db .env *.log /NFL /NDL

echo [3/4] 压缩备份文件...
cd "%BACKUP_DIR%\.."
if exist "C:\Program Files\7-Zip\7z.exe" (
    "C:\Program Files\7-Zip\7z.exe" a -tzip "spare_management_backup_%BACKUP_DATE%.zip" "%BACKUP_DATE%" -mx9
) else (
    echo 7-Zip 未安装，跳过压缩步骤...
    echo 备份文件位置：%BACKUP_DIR%
)

echo [4/4] 清理临时备份目录...
if exist "C:\Program Files\7-Zip\7z.exe" (
    rmdir /s /q "%BACKUP_DIR%"
)

echo.
echo ========================================
echo 备份完成！
if exist "C:\Program Files\7-Zip\7z.exe" (
    echo 备份文件：E:\Backup\spare_management\spare_management_backup_%BACKUP_DATE%.zip
) else (
    echo 备份目录：%BACKUP_DIR%
)
echo ========================================
pause
