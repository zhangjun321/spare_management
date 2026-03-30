@echo off
chcp 65001
echo ========================================
echo 备件管理系统 - 数据库备份任务
echo ========================================
echo.
echo 开始执行数据库备份...
echo.

REM 切换到脚本目录
cd /d %~dp0

REM 执行备份脚本
python backup_database.py

echo.
echo 备份任务执行完成！
echo ========================================
echo.
pause
