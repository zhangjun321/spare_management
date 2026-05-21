# -*- coding: utf-8 -*-
"""
Flask 应用配置
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

# 使用 PyMySQL 作为 MySQL 驱动
import pymysql
pymysql.install_as_MySQLdb()


class Config:
    """基础配置"""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'spare_management_secret_key_2024')
    DEBUG = False
    TESTING = False

    # ── S-05: Session 安全加固 ──
    SESSION_COOKIE_SECURE = False  # 子类按需覆盖；生产环境 True
    SESSION_COOKIE_HTTPONLY = True  # 禁止 JS 读取 Cookie，防 XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # 防 CSRF（Lax 允许 GET 跨站导航）
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # 8 小时过期
    
    # 数据库
    # 优先使用单独的 MySQL 配置项（避免密码中特殊字符问题）
    mysql_host = os.environ.get('MYSQL_HOST')
    mysql_port = os.environ.get('MYSQL_PORT', '3306')
    mysql_user = os.environ.get('MYSQL_USER')
    mysql_password = os.environ.get('MYSQL_PASSWORD')
    mysql_database = os.environ.get('MYSQL_DATABASE')
    
    if mysql_host and mysql_user and mysql_password and mysql_database:
        # 使用单独的配置项构建 MySQL URL
        import urllib.parse
        # 对密码进行 URL 编码
        encoded_password = urllib.parse.quote_plus(mysql_password)
        SQLALCHEMY_DATABASE_URI = f'mysql://{mysql_user}:{encoded_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4'
    else:
        # 回退到 DATABASE_URL 或 SQLite
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            SQLALCHEMY_DATABASE_URI = database_url
        else:
            # 使用默认的 SQLite
            db_path = './instance/spare_management.db'
            if not os.path.isabs(db_path):
                db_path = os.path.join(basedir, '..', db_path)
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # 日志
    LOG_LEVEL = 'INFO'
    LOG_PATH = os.path.join(basedir, '..', 'logs')
    
    # 上传
    UPLOAD_FOLDER = os.path.join(basedir, '..', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Redis (可选)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'ERROR'
    SESSION_COOKIE_SECURE = True  # 强制 HTTPS Only


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


# ============================================================
# S-01: 启动时安全配置检查
# ============================================================
def check_security_config(env_name: str = 'development') -> list:
    """检查安全相关配置，返回警告列表（启动时调用）"""
    import logging
    warnings = []
    logger = logging.getLogger(__name__)

    # 1) 检测弱 / 默认 SECRET_KEY
    _weak_keys = {
        'spare_management_secret_key_2024',
        'spare_management_dev_secret_key_20260515',
        'dev', 'secret', 'debug', '',
    }
    secret = os.environ.get('SECRET_KEY', 'spare_management_secret_key_2024')
    if secret in _weak_keys or len(secret) < 24:
        msg = '[SECURITY] 使用了弱/默认的 SECRET_KEY，生产环境请设置为至少 24 字符随机字符串！'
        warnings.append(msg)
        logger.warning(msg)

    # 2) 生产环境 DEBUG 检查
    if env_name == 'production' and ProductionConfig.DEBUG:
        msg = '[SECURITY] 生产环境 DEBUG=True，存在严重安全隐患！'
        warnings.append(msg)
        logger.error(msg)

    # 3) .env 文件权限提醒（Windows 仅记录）
    env_path = os.path.join(os.path.dirname(basedir), '.env')
    if os.path.exists(env_path):
        try:
            # Windows 上检查是否过于开放（仅记录提醒）
            import stat
            mode = os.stat(env_path).st_mode
            if hasattr(os, 'chmod'):
                logger.info('[SECURITY] 建议 .env 文件权限限制为 600 (仅所有者可读写)')
        except Exception:
            pass

    return warnings
