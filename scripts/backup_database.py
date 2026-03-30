#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库备份脚本
功能：
1. 备份MySQL数据库
2. 压缩备份文件
3. 管理备份文件保留策略
4. 记录备份日志
"""

import os
import sys
import time
import datetime
import subprocess
import shutil
import logging
from dotenv import load_dotenv

# 加载环境变量
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# 配置日志
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'backup.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# 数据库配置
DB_HOST = os.environ.get('MYSQL_HOST', 'localhost')
DB_PORT = os.environ.get('MYSQL_PORT', '3306')
DB_USER = os.environ.get('MYSQL_USER', 'root')
DB_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
DB_NAME = os.environ.get('MYSQL_DATABASE', 'spare_parts_db')

# 备份保留天数
RETENTION_DAYS = 7


def generate_backup_filename():
    """生成备份文件名"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{DB_NAME}_{timestamp}.sql"


def backup_database():
    """备份数据库"""
    logger.info("开始数据库备份...")
    
    try:
        # 生成备份文件名
        backup_file = os.path.join(BACKUP_DIR, generate_backup_filename())
        
        # 构建mysqldump命令
        cmd = [
            'mysqldump',
            f'--host={DB_HOST}',
            f'--port={DB_PORT}',
            f'--user={DB_USER}',
            f'--password={DB_PASSWORD}',
            '--single-transaction',
            '--quick',
            '--lock-tables=false',
            DB_NAME,
            f'> {backup_file}'
        ]
        
        # 执行备份命令
        cmd_str = ' '.join(cmd)
        logger.info(f"执行备份命令: {cmd_str}")
        
        result = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"数据库备份成功: {backup_file}")
            
            # 压缩备份文件
            zip_file = f"{backup_file}.zip"
            try:
                shutil.make_archive(backup_file, 'zip', BACKUP_DIR, os.path.basename(backup_file))
                os.remove(backup_file)  # 删除原始SQL文件
                logger.info(f"备份文件压缩成功: {zip_file}")
                backup_file = zip_file
            except Exception as e:
                logger.error(f"备份文件压缩失败: {str(e)}")
            
            # 清理过期备份
            clean_old_backups()
            
            return backup_file
        else:
            logger.error(f"数据库备份失败: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"备份过程中发生错误: {str(e)}")
        return None


def clean_old_backups():
    """清理过期备份"""
    logger.info("开始清理过期备份...")
    
    try:
        current_time = time.time()
        cutoff_time = current_time - (RETENTION_DAYS * 24 * 3600)
        
        for filename in os.listdir(BACKUP_DIR):
            file_path = os.path.join(BACKUP_DIR, filename)
            if os.path.isfile(file_path):
                file_mtime = os.path.getmtime(file_path)
                if file_mtime < cutoff_time:
                    os.remove(file_path)
                    logger.info(f"删除过期备份: {filename}")
        
        logger.info("过期备份清理完成")
        
    except Exception as e:
        logger.error(f"清理过期备份时发生错误: {str(e)}")


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("数据库备份脚本执行开始")
    logger.info("=" * 80)
    
    backup_file = backup_database()
    
    if backup_file:
        logger.info(f"备份文件: {backup_file}")
        logger.info("数据库备份脚本执行成功")
    else:
        logger.error("数据库备份脚本执行失败")
    
    logger.info("=" * 80)
    logger.info("数据库备份脚本执行结束")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
