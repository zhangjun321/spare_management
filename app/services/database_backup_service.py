# -*- coding: utf-8 -*-
"""
数据库备份服务
"""

import os
import subprocess
import gzip
import shutil
from datetime import datetime
from app.extensions import db
from app.models.database_backup import DatabaseBackup
from app.config import Config


class DatabaseBackupService:
    """数据库备份服务类"""
    
    # 备份目录
    BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
    
    @staticmethod
    def init_backup_dir():
        """初始化备份目录"""
        if not os.path.exists(DatabaseBackupService.BACKUP_DIR):
            os.makedirs(DatabaseBackupService.BACKUP_DIR)
            print(f"创建备份目录：{DatabaseBackupService.BACKUP_DIR}")
    
    @staticmethod
    def create_backup(backup_name=None, backup_type='manual', created_by=None):
        """创建数据库备份"""
        DatabaseBackupService.init_backup_dir()
        
        # 生成备份文件名
        if not backup_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'backup_{timestamp}'
        
        backup_file = os.path.join(DatabaseBackupService.BACKUP_DIR, f'{backup_name}.sql')
        compressed_file = f'{backup_file}.gz'
        
        # 创建备份记录
        backup_record = DatabaseBackup(
            backup_name=backup_name,
            backup_file=backup_file,
            backup_type=backup_type,
            status='pending',
            created_by=created_by
        )
        db.session.add(backup_record)
        db.session.commit()
        
        try:
            # 更新状态为运行中
            backup_record.status = 'running'
            backup_record.start_time = datetime.now()
            db.session.commit()
            
            # 获取数据库连接信息
            db_host = Config.SQLALCHEMY_DATABASE_URI.split('@')[1].split('/')[0].split(':')[0]
            db_port = Config.SQLALCHEMY_DATABASE_URI.split('@')[1].split('/')[0].split(':')[1] if ':' in Config.SQLALCHEMY_DATABASE_URI.split('@')[1].split('/')[0] else '3306'
            db_user = Config.SQLALCHEMY_DATABASE_URI.split('//')[1].split(':')[0]
            db_password = Config.SQLALCHEMY_DATABASE_URI.split('//')[1].split(':')[1].split('@')[0]
            db_name = Config.SQLALCHEMY_DATABASE_URI.split('/')[-1]
            
            # 执行 mysqldump
            cmd = [
                'mysqldump',
                '-h', db_host,
                '-P', db_port,
                '-u', db_user,
                f'-p{db_password}',
                '--single-transaction',
                '--routines',
                '--triggers',
                db_name
            ]
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)
            
            if result.returncode != 0:
                raise Exception(f'mysqldump 失败：{result.stderr.decode("utf-8")}')
            
            # 压缩备份文件
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 删除未压缩文件
            os.remove(backup_file)
            
            # 获取文件大小
            backup_size = os.path.getsize(compressed_file)
            
            # 更新备份记录
            backup_record.backup_file = compressed_file
            backup_record.backup_size = backup_size
            backup_record.status = 'success'
            backup_record.end_time = datetime.now()
            backup_record.remark = f'备份成功，文件大小：{round(backup_size / (1024 * 1024), 2)} MB'
            db.session.commit()
            
            return True, backup_record
            
        except Exception as e:
            # 更新备份记录为失败
            backup_record.status = 'failed'
            backup_record.end_time = datetime.now()
            backup_record.remark = f'备份失败：{str(e)}'
            db.session.commit()
            
            return False, str(e)
    
    @staticmethod
    def get_backup_list():
        """获取备份列表"""
        backups = DatabaseBackup.query.order_by(DatabaseBackup.created_at.desc()).all()
        return [backup.to_dict() for backup in backups]
    
    @staticmethod
    def delete_backup(backup_id):
        """删除备份"""
        backup = DatabaseBackup.query.get(backup_id)
        if not backup:
            return False, '备份记录不存在'
        
        try:
            # 删除备份文件
            if os.path.exists(backup.backup_file):
                os.remove(backup.backup_file)
            
            # 删除备份记录
            db.session.delete(backup)
            db.session.commit()
            
            return True, '删除成功'
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def restore_backup(backup_id):
        """恢复备份"""
        backup = DatabaseBackup.query.get(backup_id)
        if not backup:
            return False, '备份记录不存在'
        
        if not os.path.exists(backup.backup_file):
            return False, '备份文件不存在'
        
        try:
            # 获取数据库连接信息
            db_host = Config.SQLALCHEMY_DATABASE_URI.split('@')[1].split('/')[0].split(':')[0]
            db_port = Config.SQLALCHEMY_DATABASE_URI.split('@')[1].split('/')[0].split(':')[1] if ':' in Config.SQLALCHEMY_DATABASE_URI.split('@')[1].split('/')[0] else '3306'
            db_user = Config.SQLALCHEMY_DATABASE_URI.split('//')[1].split(':')[0]
            db_password = Config.SQLALCHEMY_DATABASE_URI.split('//')[1].split(':')[1].split('@')[0]
            db_name = Config.SQLALCHEMY_DATABASE_URI.split('/')[-1]
            
            # 解压并恢复
            if backup.backup_file.endswith('.gz'):
                cmd = f"gunzip -c \"{backup.backup_file}\" | mysql -h{db_host} -P{db_port} -u{db_user} -p{db_password} {db_name}"
            else:
                cmd = f"mysql -h{db_host} -P{db_port} -u{db_user} -p{db_password} {db_name} < \"{backup.backup_file}\""
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f'恢复失败：{result.stderr}')
            
            return True, '恢复成功'
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def cleanup_old_backups(days=30):
        """清理旧备份"""
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        old_backups = DatabaseBackup.query.filter(DatabaseBackup.created_at < cutoff_date).all()
        
        deleted_count = 0
        for backup in old_backups:
            success, _ = DatabaseBackupService.delete_backup(backup.id)
            if success:
                deleted_count += 1
        
        return deleted_count
