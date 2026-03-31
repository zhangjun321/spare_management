# -*- coding: utf-8 -*-
"""
系统配置服务
"""

import json
from app.extensions import db
from app.models.system_config import SystemConfig
from datetime import datetime


class SystemConfigService:
    """系统配置服务类"""
    
    # 默认配置项
    DEFAULT_CONFIGS = {
        'inventory': {
            'min_stock_threshold': {'value': '10', 'type': 'int', 'description': '最低库存预警阈值'},
            'max_stock_threshold': {'value': '1000', 'type': 'int', 'description': '最高库存预警阈值'},
            'safety_stock_days': {'value': '30', 'type': 'int', 'description': '安全库存天数'},
            'auto_reorder_enabled': {'value': 'false', 'type': 'bool', 'description': '是否启用自动补货'},
        },
        'purchase': {
            'default_payment_terms': {'value': '30', 'type': 'int', 'description': '默认付款期限（天）'},
            'max_purchase_amount': {'value': '100000', 'type': 'float', 'description': '最大采购金额'},
            'require_approval': {'value': 'true', 'type': 'bool', 'description': '采购是否需要审批'},
        },
        'maintenance': {
            'default_maintenance_cycle': {'value': '90', 'type': 'int', 'description': '默认维护周期（天）'},
            'overdue_reminder_days': {'value': '7', 'type': 'int', 'description': '逾期提醒天数'},
        },
        'system': {
            'session_timeout': {'value': '3600', 'type': 'int', 'description': '会话超时时间（秒）'},
            'max_login_attempts': {'value': '5', 'type': 'int', 'description': '最大登录尝试次数'},
            'password_min_length': {'value': '6', 'type': 'int', 'description': '密码最小长度'},
            'enable_captcha': {'value': 'true', 'type': 'bool', 'description': '是否启用验证码'},
        }
    }
    
    @staticmethod
    def init_default_configs():
        """初始化默认配置"""
        for group, configs in SystemConfigService.DEFAULT_CONFIGS.items():
            for key, config in configs.items():
                existing = SystemConfig.query.filter_by(config_key=key).first()
                if not existing:
                    system_config = SystemConfig(
                        config_group=group,
                        config_key=key,
                        config_value=config['value'],
                        value_type=config['type'],
                        description=config['description'],
                        is_editable=True,
                        is_active=True
                    )
                    db.session.add(system_config)
        
        try:
            db.session.commit()
            print("默认配置初始化完成")
        except Exception as e:
            db.session.rollback()
            print(f"默认配置初始化失败：{e}")
    
    @staticmethod
    def get_config(key, default=None):
        """获取配置值"""
        config = SystemConfig.query.filter_by(config_key=key, is_active=True).first()
        if not config:
            return default
        
        return SystemConfigService._convert_value(config.config_value, config.value_type)
    
    @staticmethod
    def set_config(key, value, value_type='string', description=None, updated_by=None):
        """设置配置值"""
        config = SystemConfig.query.filter_by(config_key=key).first()
        
        if config:
            if not config.is_editable:
                return False, '该配置项不可编辑'
            
            config.config_value = str(value)
            config.value_type = value_type
            if description:
                config.description = description
            if updated_by:
                config.updated_by = updated_by
            config.version += 1
            config.updated_at = datetime.now()
        else:
            config = SystemConfig(
                config_group='custom',
                config_key=key,
                config_value=str(value),
                value_type=value_type,
                description=description or '',
                is_editable=True,
                is_active=True,
                updated_by=updated_by
            )
            db.session.add(config)
        
        try:
            db.session.commit()
            return True, '配置成功'
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def get_group_configs(group):
        """获取指定分组的所有配置"""
        configs = SystemConfig.query.filter_by(config_group=group, is_active=True).all()
        return [config.to_dict() for config in configs]
    
    @staticmethod
    def get_all_configs():
        """获取所有配置"""
        configs = SystemConfig.query.filter_by(is_active=True).order_by(
            SystemConfig.config_group, SystemConfig.config_key
        ).all()
        
        # 按分组组织
        result = {}
        for config in configs:
            if config.config_group not in result:
                result[config.config_group] = []
            result[config.config_group].append(config.to_dict())
        
        return result
    
    @staticmethod
    def _convert_value(value, value_type):
        """转换配置值类型"""
        if value_type == 'int':
            try:
                return int(value)
            except:
                return 0
        elif value_type == 'float':
            try:
                return float(value)
            except:
                return 0.0
        elif value_type == 'bool':
            return value.lower() in ('true', '1', 'yes', 'on')
        elif value_type == 'json':
            try:
                return json.loads(value)
            except:
                return {}
        else:
            return value
