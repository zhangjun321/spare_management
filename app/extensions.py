"""
Flask 应用扩展配置
初始化所有 Flask 扩展
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt

# 数据库 ORM
db = SQLAlchemy()

# 用户认证
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录以访问此页面'
login_manager.login_message_category = 'warning'

# 数据库迁移
migrate = Migrate()

# CSRF 保护
csrf = CSRFProtect()


def init_extensions(app):
    """初始化所有扩展"""
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # 对 /api/ 前缀的请求，未登录时返回 JSON 401 而非 302 重定向 HTML
    # 避免 React axios 收到 HTML 页面导致数据静默失败
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request, jsonify, redirect, url_for
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': '未登录或登录已过期，请重新登录',
                'code': 401,
                'redirect': '/login'
            }), 401
        # 非 API 请求保持原有重定向行为
        return redirect(url_for('auth.login'))
