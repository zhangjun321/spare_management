# -*- coding: utf-8 -*-
"""
Flask 应用工厂
创建和配置 Flask 应用
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify
from datetime import datetime
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

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
    
    # 添加uploads静态目录
    uploads_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    app.config['UPLOAD_FOLDER'] = uploads_path
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    init_extensions(app)
    
    # 初始化缓存服务（优先 Redis，其次 SQLite）
    try:
        from app.services.cache_service import init_cache, SQLiteCacheService
        
        # 检查是否启用 Redis
        use_redis = app.config.get('USE_REDIS', True)
        
        if use_redis:
            # 尝试初始化 Redis
            cache_service = init_cache(app)
            if cache_service and cache_service.redis_client:
                app.logger.info('使用 Redis 作为缓存后端')
            else:
                # Redis 失败，使用 SQLite
                raise Exception('Redis 连接失败')
        else:
            raise Exception('配置禁用 Redis')
            
    except Exception as e:
        # 使用 SQLite 缓存
        app.logger.warning(f'Redis 初始化失败 ({str(e)})，使用 SQLite 缓存替代')
        try:
            sqlite_cache = SQLiteCacheService()
            sqlite_cache.init_app(app)
            app.extensions['cache'] = sqlite_cache
            app.logger.info('SQLite 缓存初始化成功')
        except Exception as sqlite_error:
            app.logger.error(f'SQLite 缓存初始化失败：{str(sqlite_error)}')
    
    # 初始化定时任务调度器
    try:
        from app.scheduler import init_scheduler
        init_scheduler(app)
        app.logger.info('定时任务调度器初始化成功')
    except Exception as e:
        app.logger.error(f'定时任务调度器初始化失败：{str(e)}')
    
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
    
    # 请求日志中间件 - 记录所有请求（不打印敏感请求头，不记录静态文件）
    _SENSITIVE_HEADERS = {'authorization', 'cookie', 'x-api-key', 'x-auth-token'}
    _STATIC_EXTS = ('.js', '.css', '.png', '.jpg', '.ico', '.svg', '.woff', '.woff2', '.ttf', '.map')

    @app.before_request
    def log_request_info():
        # 静态文件请求不记录日志，避免噪音
        if request.path.startswith('/static/') or request.path.endswith(_STATIC_EXTS):
            return
        safe_headers = {
            k: v for k, v in request.headers
            if k.lower() not in _SENSITIVE_HEADERS
        }
        app.logger.debug(f"[{request.method}] {request.path} from {request.remote_addr} headers={safe_headers}")
        if request.data and app.debug:
            app.logger.debug(f"请求体：{request.data.decode('utf-8', errors='ignore')[:500]}")
        
        # 特殊处理备份 API 请求
        if '/backup/api/' in request.path:
            app.logger.warning(f"!!! 捕获到备份 API 请求 !!!")
    
    # 响应日志中间件
    @app.after_request
    def log_response_info(response):
        if not (request.path.startswith('/static/') or request.path.endswith(_STATIC_EXTS)):
            app.logger.debug(f"响应状态：{response.status_code} [{request.method}] {request.path}")
        return response
    
    # 添加响应头部中间件
    @app.after_request
    def add_security_headers(response):
        # 防止 MIME 类型嗅探
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # 防止点击劫持
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        # 内容安全策略 - 允许 CDN 资源和内联样式
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://unpkg.com https://cdn.staticfile.org; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://jsdelivr.net https://unpkg.com https://cdn.staticfile.org; img-src 'self' data: https: blob:; font-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://unpkg.com https://cdn.staticfile.org; connect-src 'self' http://localhost:* http://127.0.0.1:* https://* 'unsafe-inline'"
        # 静态资源（带哈希文件名）可长期缓存；其余接口禁止缓存
        if request.path.startswith('/static/') and (
            request.path.endswith(('.js', '.css', '.woff', '.woff2', '.ttf'))
        ):
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            response.headers.pop('Pragma', None)
            response.headers.pop('Expires', None)
        else:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

    # ── 健康检查端点（Docker healthcheck / LB 探针） ────────
    @app.route('/health')
    def health_check():
        """
        轻量健康检查：验证应用进程存活 + 数据库可达性
        返回 200 表示健康，503 表示不健康
        """
        status = {'status': 'ok', 'services': {}}
        http_status = 200

        # 检查数据库
        try:
            db.session.execute(db.text('SELECT 1'))
            status['services']['database'] = 'ok'
        except Exception as e:
            status['services']['database'] = f'error: {str(e)}'
            status['status'] = 'degraded'
            http_status = 503

        # 检查 Redis（可选，不影响主服务）
        try:
            cache = app.extensions.get('cache')
            if cache and hasattr(cache, 'redis_client') and cache.redis_client:
                cache.redis_client.ping()
                status['services']['redis'] = 'ok'
            else:
                status['services']['redis'] = 'unavailable (using sqlite cache)'
        except Exception:
            status['services']['redis'] = 'unavailable'

        return jsonify(status), http_status

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
    
    # 系统监控模块
    from app.routes.monitor import monitor_bp
    app.register_blueprint(monitor_bp, url_prefix='/monitor')
    
    # 日志审计模块
    from app.routes.logs import logs_bp
    app.register_blueprint(logs_bp, url_prefix='/logs')
    
    # 系统配置模块
    from app.routes.config import config_bp
    app.register_blueprint(config_bp, url_prefix='/config')
    
    # 角色权限管理模块
    from app.routes.roles import roles_bp
    app.register_blueprint(roles_bp, url_prefix='/roles')
    
    # 数据字典管理模块
    from app.routes.dictionary import dictionary_bp
    app.register_blueprint(dictionary_bp, url_prefix='/dictionary')
    
    # 帮助文档管理模块
    from app.routes.help import help_bp
    app.register_blueprint(help_bp, url_prefix='/help')
    
    # API 接口管理模块
    from app.routes.api_management import api_bp
    app.register_blueprint(api_bp, url_prefix='/api-docs')
    
    # 仓库管理 API 模块（为 React 前端提供完整 CRUD API）
    from app.routes.api_warehouses import api_warehouses_bp
    app.register_blueprint(api_warehouses_bp)
    
    # 数据备份模块
    from app.routes.backup import backup_bp
    app.register_blueprint(backup_bp, url_prefix='/backup')
    
    # 豁免备份 API 的 CSRF 保护
    from app.extensions import csrf
    csrf.exempt(backup_bp)
    
    # 通知模块
    from app.routes.notification import notification_bp
    app.register_blueprint(notification_bp, url_prefix='/notification')
    
    # 用户邮箱配置模块
    from app.routes.user_email import user_email_bp
    app.register_blueprint(user_email_bp, url_prefix='/user_email')
    
    # 告警管理模块
    from app.routes.alerts import alerts_bp
    app.register_blueprint(alerts_bp, url_prefix='/alerts')
    
    # ===========================================
    # 注意：旧的仓库管理模块已屏蔽，等待新模块开发完成
    # ===========================================
    # # 高级仓库管理模块
    # from app.routes.warehouses_advanced_routes import warehouses_advanced_bp
    # app.register_blueprint(warehouses_advanced_bp, url_prefix='/warehouses')
    
    # 智能仓库管理模块（百度千帆 AI）
    from app.routes.intelligent_warehouse_routes import intelligent_warehouse_bp
    app.register_blueprint(intelligent_warehouse_bp)
    
    # 库存管理模块（入库/出库/库存）
    from app.routes.inventory_routes import inventory_bp
    app.register_blueprint(inventory_bp)
    
    # 仓库可视化模块
    from app.routes.visualization_routes import visualization_bp
    app.register_blueprint(visualization_bp)
    
    # AI 图像生成模块
    from app.routes.ai_image_routes import ai_image_bp
    app.register_blueprint(ai_image_bp)
    from app.extensions import csrf
    csrf.exempt(ai_image_bp)
    
    # # 仓库管理 V3 模块（旧）- 已屏蔽
    # from app.routes.warehouse_v3 import warehouse_v3_bp
    # app.register_blueprint(warehouse_v3_bp)
    
    # # 仓库管理 V3 前端页面
    # from app.routes.warehouse_v3_pages import warehouse_v3_pages_bp
    # app.register_blueprint(warehouse_v3_pages_bp)
    # ===========================================
    
    # ===========================================
    # 注意：旧的仓库管理模块已屏蔽，使用 React 版本替代
    # ===========================================
    # # 旧的仓库管理模块前端页面 - 已屏蔽
    # from app.routes.warehouse_new_pages import warehouse_new_pages_bp
    # app.register_blueprint(warehouse_new_pages_bp)
    # ===========================================
    
    # 新的 React 仓库管理模块（完全独立）
    from app.routes.react_warehouse import react_warehouse_bp
    app.register_blueprint(react_warehouse_bp)

    # 备件管理 REST API（供 React 前端调用）
    from app.routes.api_spare_parts import api_spare_parts_bp
    app.register_blueprint(api_spare_parts_bp)

    # 交易管理 REST API（React 前端）
    from app.routes.api_transactions import api_transactions_bp
    app.register_blueprint(api_transactions_bp)
    csrf.exempt(api_transactions_bp)

    # React 备件管理前端页面入口
    from app.routes.react_spare_parts import react_spare_parts_bp
    app.register_blueprint(react_spare_parts_bp)
    
    # 库存盘点 API
    from app.routes.inventory_check import inventory_check_bp
    app.register_blueprint(inventory_check_bp)
    
    # 库存盘点页面
    from app.routes.inventory_check_pages import inventory_check_pages_bp
    app.register_blueprint(inventory_check_pages_bp)
    
    # 预警管理 API
    from app.routes.warning import warning_bp
    app.register_blueprint(warning_bp)
    
    # 预警管理页面
    from app.routes.warning_pages import warning_pages_bp
    app.register_blueprint(warning_pages_bp)
    
    # 质检管理 API
    from app.routes.quality_check import quality_check_bp
    app.register_blueprint(quality_check_bp)
    
    # 质检管理页面
    from app.routes.quality_check_pages import quality_check_pages_bp
    app.register_blueprint(quality_check_pages_bp)
    
    # 库存事务日志 API
    from app.routes.warehouse_v3.inventory_transaction_log_routes import inventory_transaction_log_bp
    app.register_blueprint(inventory_transaction_log_bp)
    
    # 效期预警 API
    from app.routes.warehouse_v3.expiry_warning_routes import expiry_warning_bp
    app.register_blueprint(expiry_warning_bp)
    
    # 拣货推荐 API
    from app.routes.warehouse_v3.picking_recommendation_routes import picking_recommendation_bp
    app.register_blueprint(picking_recommendation_bp)
    
    # 批次谱系 API
    from app.routes.warehouse_v3.batch_genealogy_routes import batch_genealogy_bp
    app.register_blueprint(batch_genealogy_bp)
    
    # 循环盘点 API
    from app.routes.warehouse_v3.cycle_count_routes import cycle_count_bp
    app.register_blueprint(cycle_count_bp)
    
    # 波次管理 API
    from app.routes.warehouse_v3.wave_management_routes import wave_management_bp
    app.register_blueprint(wave_management_bp)
    
    # 库位优化 API
    from app.routes.warehouse_v3.location_optimization_routes import location_optimization_bp
    app.register_blueprint(location_optimization_bp)
    
    # 任务调度 API
    from app.routes.warehouse_v3.task_scheduler_routes import task_scheduler_bp
    app.register_blueprint(task_scheduler_bp)
    
    # 路径优化 API
    from app.routes.warehouse_v3.path_optimization_routes import path_optimization_bp
    app.register_blueprint(path_optimization_bp)
    
    # AI 预测补货 API
    from app.routes.warehouse_v3.ai_forecast_routes import ai_forecast_bp
    app.register_blueprint(ai_forecast_bp)
    
    # AI 任务分配 API
    from app.routes.warehouse_v3.ai_task_assignment_routes import ai_task_assignment_bp
    app.register_blueprint(ai_task_assignment_bp)
    
    # 质检管理页面（已存在）
    # 质检管理 API 已在上面注册（app.routes.quality_check）
    
    # 库存并发控制 API
    from app.routes.warehouse_v3.inventory_concurrency_routes import inventory_concurrency_bp
    app.register_blueprint(inventory_concurrency_bp)
    
    # API 模块
    from app.routes.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 库存记录 API
    from app.routes.api_warehouses import api_inventory_bp
    app.register_blueprint(api_inventory_bp)
    
    # 入库单 / 出库单 API
    from app.routes.api_inbound_outbound import api_inbound_bp, api_outbound_bp
    app.register_blueprint(api_inbound_bp)
    app.register_blueprint(api_outbound_bp)
    
    # 处理 favicon 请求，避免浏览器控制台 404
    @app.route('/favicon.ico')
    def favicon():
        return ('', 204)

    # 提供uploads目录的静态文件访问
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # 注册一个测试路由，直接返回 JSON
    @app.route('/backup/test', methods=['GET', 'POST'])
    def backup_test():
        """测试备份路由"""
        app.logger.info(f"测试路由被调用：{request.method}")
        return jsonify({
            'status': 'success',
            'message': '测试成功',
            'method': request.method,
            'path': request.path,
            'headers': dict(request.headers)
        })


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
