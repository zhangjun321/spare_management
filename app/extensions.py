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
