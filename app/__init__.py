"""
Flask 应用工厂
创建和配置 Flask 应用
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from datetime import datetime

from app.config import config
from app.extensions import init_extensions, db, login_manager


def create_app(config_name=None):
    """
    应用工厂函数
    
    Args:
        config_name: 配置名称 (development/production/testing)
    
    Returns:
        Flask 应用实例
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    init_extensions(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 配置日志
    configure_logging(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册模板过滤器
    register_template_filters(app)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        
        # 创建管理员账户 (如果不存在)
        from app.models.user import User
        from app.models.role import Role
        
        # 创建系统角色
        # create_system_roles()
        
        # 创建默认管理员
        # create_default_admin()
    
    # 注册 Shell 上下文处理器
    @app.shell_context_processor
    def make_shell_context():
        return {'db': db, 'app': app}
    
    return app


def register_blueprints(app):
    """注册所有蓝图"""
    
    # 用户认证模块
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/')
    
    # 仪表盘模块
    from app.routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/')
    
    # 备件管理模块
    from app.routes.spare_parts import spare_parts_bp
    app.register_blueprint(spare_parts_bp, url_prefix='/spare_parts')
    
    # 批次管理模块
    from app.routes.batches import batches_bp
    app.register_blueprint(batches_bp, url_prefix='/batches')
    
    # 仓库管理模块
    from app.routes.warehouses import warehouses_bp
    app.register_blueprint(warehouses_bp, url_prefix='/warehouses')
    
    # 交易管理模块
    from app.routes.transactions import transactions_bp
    app.register_blueprint(transactions_bp, url_prefix='/transactions')
    
    # 设备管理模块
    from app.routes.equipment import equipment_bp
    app.register_blueprint(equipment_bp, url_prefix='/equipment')
    
    # 维修管理模块
    from app.routes.maintenance import maintenance_bp
    app.register_blueprint(maintenance_bp, url_prefix='/maintenance')
    
    # 采购管理模块
    from app.routes.purchases import purchases_bp
    app.register_blueprint(purchases_bp, url_prefix='/purchase')
    
    # 报表统计模块
    from app.routes.reports import reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    # 系统管理模块
    from app.routes.system import system_bp
    app.register_blueprint(system_bp, url_prefix='/system')
    
    # 告警管理模块
    from app.routes.alerts import alerts_bp
    app.register_blueprint(alerts_bp, url_prefix='/alerts')
    
    # 通知模块
    from app.routes.notification import notification_bp
    app.register_blueprint(notification_bp, url_prefix='/notification')
    
    # API 模块
    from app.routes.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')


def configure_logging(app):
    """配置日志"""
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
    app.logger.addHandler(console_handler)
    
    # 文件日志 (轮转)
    file_handler = RotatingFileHandler(
        os.path.join(app.config['LOG_PATH'], f'app_{datetime.now().strftime("%Y%m%d")}.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    # 错误日志
    error_handler = RotatingFileHandler(
        os.path.join(app.config['LOG_PATH'], f'errors_{datetime.now().strftime("%Y%m%d")}.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=10
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    app.logger.addHandler(error_handler)
    
    # 设置日志级别
    app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
    app.logger.info(f'应用启动 - 环境：{app.config["DEBUG"] and "开发" or "生产"}')


def register_error_handlers(app):
    """注册错误处理器"""
    
    from app.errors.handlers import errors_bp
    app.register_blueprint(errors_bp)


def register_template_filters(app):
    """注册模板过滤器"""
    
    @app.template_filter('datetime_format')
    def datetime_format_filter(value, format='%Y-%m-%d %H:%M'):
        if value:
            return value.strftime(format)
        return ''
    
    @app.template_filter('currency')
    def currency_filter(value):
        if value is not None:
            return f'¥{value:,.2f}'
        return '¥0.00'
    
    @app.template_filter('stock_status')
    def stock_status_filter(status):
        status_map = {
            'normal': ('正常', 'success'),
            'low': ('低库存', 'warning'),
            'out': ('缺货', 'danger'),
            'overstock': ('超储', 'info')
        }
        return status_map.get(status, ('未知', 'secondary'))


def create_system_roles():
    """创建系统角色"""
    from app.models.role import Role
    
    roles = [
        {
            'name': 'admin',
            'display_name': '系统管理员',
            'description': '拥有所有权限',
            'permissions': {'*': ['create', 'read', 'update', 'delete']},
            'is_system': True
        },
        {
            'name': 'warehouse_manager',
            'display_name': '仓库管理员',
            'description': '负责仓库管理',
            'permissions': {
                'spare_parts': ['create', 'read', 'update'],
                'batches': ['create', 'read', 'update'],
                'warehouses': ['read'],
                'transactions': ['create', 'read'],
                'reports': ['read']
            },
            'is_system': True
        },
        {
            'name': 'purchaser',
            'display_name': '采购员',
            'description': '负责采购管理',
            'permissions': {
                'spare_parts': ['read'],
                'suppliers': ['create', 'read', 'update'],
                'purchase': ['create', 'read', 'update'],
                'reports': ['read']
            },
            'is_system': True
        },
        {
            'name': 'maintenance_manager',
            'display_name': '维修管理员',
            'description': '负责维修管理',
            'permissions': {
                'equipment': ['create', 'read', 'update'],
                'maintenance': ['create', 'read', 'update', 'delete'],
                'spare_parts': ['read'],
                'reports': ['read']
            },
            'is_system': True
        },
        {
            'name': 'accountant',
            'display_name': '财务人员',
            'description': '负责财务管理',
            'permissions': {
                'spare_parts': ['read'],
                'maintenance': ['read'],
                'purchase': ['read'],
                'reports': ['read', 'export']
            },
            'is_system': True
        },
        {
            'name': 'normal_user',
            'display_name': '普通用户',
            'description': '普通用户',
            'permissions': {
                'spare_parts': ['read'],
                'inventory': ['read']
            },
            'is_system': True
        }
    ]
    
    for role_data in roles:
        existing_role = Role.query.filter_by(name=role_data['name']).first()
        if not existing_role:
            role = Role(**role_data)
            db.session.add(role)
            db.session.commit()
            logging.info(f"创建系统角色：{role_data['display_name']}")


def create_default_admin():
    """创建默认管理员账户"""
    from app.models.user import User
    from app.models.role import Role
    from app.extensions import generate_password_hash
    
    admin_role = Role.query.filter_by(name='admin').first()
    
    if not admin_role:
        return
    
    # 检查是否已有管理员
    existing_admin = User.query.filter_by(username='admin').first()
    
    if not existing_admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            real_name='系统管理员',
            role_id=admin_role.id,
            is_admin=True,
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        logging.info("创建默认管理员账户：admin / admin123")
