# -*- coding: utf-8 -*-
"""
系统监控服务
"""

import psutil
import platform
from datetime import datetime, timedelta
from app.extensions import db
from app.models.system_monitor import SystemMonitor
from app.models.system import EmailConfig


class SystemMonitorService:
    """系统监控服务类"""
    
    @staticmethod
    def get_server_status():
        """获取服务器状态"""
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # 系统运行时间
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            return {
                'status': 'success',
                'data': {
                    'cpu': {
                        'usage': cpu_percent,
                        'status': SystemMonitorService._get_status(cpu_percent, 70, 90)
                    },
                    'memory': {
                        'usage': memory_percent,
                        'total': memory.total / (1024**3),  # GB
                        'used': memory.used / (1024**3),
                        'status': SystemMonitorService._get_status(memory_percent, 70, 90)
                    },
                    'disk': {
                        'usage': disk_percent,
                        'total': disk.total / (1024**3),  # GB
                        'used': disk.used / (1024**3),
                        'status': SystemMonitorService._get_status(disk_percent, 80, 95)
                    },
                    'uptime': {
                        'days': uptime.days,
                        'hours': uptime.seconds // 3600,
                        'minutes': (uptime.seconds % 3600) // 60
                    },
                    'system': {
                        'platform': platform.system(),
                        'version': platform.version(),
                        'python_version': platform.python_version()
                    }
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    def get_database_status():
        """获取数据库状态"""
        try:
            # 执行简单查询测试数据库连接
            from app.models.spare_part import SparePart
            count = SparePart.query.count()
            
            # 获取数据库大小（MySQL 特定）
            result = db.session.execute(db.text("""
                SELECT 
                    table_schema as database_name,
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                GROUP BY table_schema
            """)).fetchone()
            
            db_size = result[1] if result else 0
            
            # 获取表数量
            table_count = db.session.execute(db.text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
            """)).fetchone()[0]
            
            return {
                'status': 'success',
                'data': {
                    'connection': 'connected',
                    'status': 'normal',
                    'size_mb': db_size,
                    'table_count': table_count,
                    'record_count': count
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    def get_redis_status():
        """获取 Redis 状态"""
        try:
            from app.services.cache_service import get_redis, redis_available
            
            if not redis_available:
                return {
                    'status': 'success',
                    'data': {
                        'connection': 'disconnected',
                        'status': 'unavailable',
                        'message': 'Redis 未启用'
                    }
                }
            
            r = get_redis()
            info = r.info()
            
            # 获取键数量
            db_size = r.dbsize()
            
            # 获取内存使用
            used_memory = info.get('used_memory', 0) / (1024 * 1024)  # MB
            
            return {
                'status': 'success',
                'data': {
                    'connection': 'connected',
                    'status': 'normal',
                    'version': info.get('redis_version', 'unknown'),
                    'uptime_days': info.get('uptime_in_days', 0),
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_mb': round(used_memory, 2),
                    'db_size': db_size
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    def get_service_status():
        """获取服务状态"""
        try:
            # 检查邮件服务配置
            email_config = EmailConfig.query.filter_by(is_active=True).first()
            email_status = 'configured' if email_config else 'not_configured'
            
            return {
                'status': 'success',
                'data': {
                    'email_service': {
                        'status': email_status,
                        'message': '邮件服务已配置' if email_config else '邮件服务未配置'
                    },
                    'cache_service': {
                        'status': 'enabled',
                        'message': '缓存服务已启用'
                    },
                    'log_service': {
                        'status': 'enabled',
                        'message': '日志服务已启用'
                    }
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    
    @staticmethod
    def _get_status(value, warning_threshold, critical_threshold):
        """根据阈值判断状态"""
        if value >= critical_threshold:
            return 'critical'
        elif value >= warning_threshold:
            return 'warning'
        else:
            return 'normal'
    
    @staticmethod
    def save_monitor_data(monitor_type, metric_name, metric_value, 
                         threshold_warning=None, threshold_critical=None, unit=None):
        """保存监控数据"""
        status = SystemMonitorService._get_status(
            metric_value, 
            threshold_warning or 0, 
            threshold_critical or 0
        )
        
        monitor = SystemMonitor(
            monitor_type=monitor_type,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical,
            status=status,
            unit=unit
        )
        
        db.session.add(monitor)
        db.session.commit()
        
        return monitor
