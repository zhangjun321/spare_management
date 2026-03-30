#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库恢复脚本
功能：
1. 从备份文件恢复MySQL数据库
2. 支持从压缩文件恢复
3. 记录恢复日志
"""

import os
import sys
import subprocess
import logging
import zipfile
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
        logging.FileHandler(os.path.join(log_dir, 'restore.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')

# 数据库配置
DB_HOST = os.environ.get('MYSQL_HOST', 'localhost')
DB_PORT = os.environ.get('MYSQL_PORT', '3306')
DB_USER = os.environ.get('MYSQL_USER', 'root')
DB_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
DB_NAME = os.environ.get('MYSQL_DATABASE', 'spare_parts_db')


def extract_backup_file(backup_file):
    """提取备份文件"""
    if backup_file.endswith('.zip'):
        logger.info(f"正在提取压缩文件: {backup_file}")
        try:
            with zipfile.ZipFile(backup_file, 'r') as zip_ref:
                # 提取到临时目录
                temp_dir = os.path.join(os.path.dirname(backup_file), 'temp_restore')
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                zip_ref.extractall(temp_dir)
                
                # 查找SQL文件
                for file in os.listdir(temp_dir):
                    if file.endswith('.sql'):
                        return os.path.join(temp_dir, file)
            return None
        except Exception as e:
            logger.error(f"提取压缩文件失败: {str(e)}")
            return None
    else:
        return backup_file


def restore_database(backup_file):
    """恢复数据库"""
    logger.info(f"开始从备份文件恢复数据库: {backup_file}")
    
    try:
        # 提取备份文件
        sql_file = extract_backup_file(backup_file)
        if not sql_file:
            logger.error("无法找到SQL文件")
            return False
        
        # 构建mysql命令
        cmd = [
            'mysql',
            f'--host={DB_HOST}',
            f'--port={DB_PORT}',
            f'--user={DB_USER}',
            f'--password={DB_PASSWORD}',
            DB_NAME,
            f'< {sql_file}'
        ]
        
        # 执行恢复命令
        cmd_str = ' '.join(cmd)
        logger.info(f"执行恢复命令: {cmd_str}")
        
        result = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("数据库恢复成功")
            
            # 清理临时文件
            if sql_file != backup_file:
                os.remove(sql_file)
                os.rmdir(os.path.dirname(sql_file))
            
            return True
        else:
            logger.error(f"数据库恢复失败: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"恢复过程中发生错误: {str(e)}")
        return False


def list_backup_files():
    """列出所有备份文件"""
    if not os.path.exists(BACKUP_DIR):
        logger.error("备份目录不存在")
        return []
    
    backup_files = []
    for filename in os.listdir(BACKUP_DIR):
        if filename.endswith('.sql') or filename.endswith('.zip'):
            file_path = os.path.join(BACKUP_DIR, filename)
            file_size = os.path.getsize(file_path)
            file_mtime = os.path.getmtime(file_path)
            backup_files.append({
                'filename': filename,
                'path': file_path,
                'size': file_size,
                'mtime': file_mtime
            })
    
    # 按修改时间排序，最新的在前
    backup_files.sort(key=lambda x: x['mtime'], reverse=True)
    return backup_files


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("数据库恢复脚本执行开始")
    logger.info("=" * 80)
    
    # 列出所有备份文件
    backup_files = list_backup_files()
    
    if not backup_files:
        logger.error("没有找到备份文件")
        return
    
    logger.info("可用的备份文件:")
    for i, backup in enumerate(backup_files, 1):
        logger.info(f"{i}. {backup['filename']}")
    
    # 选择备份文件
    choice = input("请选择要恢复的备份文件编号: ")
    try:
        index = int(choice) - 1
        if 0 <= index < len(backup_files):
            backup_file = backup_files[index]['path']
            success = restore_database(backup_file)
            if success:
                logger.info("数据库恢复脚本执行成功")
            else:
                logger.error("数据库恢复脚本执行失败")
        else:
            logger.error("无效的选择")
    except ValueError:
        logger.error("请输入有效的数字")
    
    logger.info("=" * 80)
    logger.info("数据库恢复脚本执行结束")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
