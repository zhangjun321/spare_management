"""
缓存服务 - 支持 Redis、SQLite 和内存缓存
提供统一的缓存管理接口
"""

from flask import current_app
from functools import wraps
import json
import hashlib
import sqlite3
import time
from datetime import datetime, timedelta
from threading import Lock

class SQLiteCacheService:
    """SQLite 缓存服务类（Redis 替代方案）"""
    
    def __init__(self, app=None):
        self.db_path = None
        self.default_timeout = 300  # 默认 5 分钟
        self.lock = Lock()
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化 SQLite 数据库"""
        self.db_path = app.config.get('CACHE_DB_PATH', 'cache.db')
        self._create_table(app)
        app.logger.info('SQLite 缓存初始化成功')
    
    def _create_table(self, app):
        """创建缓存表"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 创建缓存表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cache (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        expire_at INTEGER NOT NULL
                    )
                ''')
                
                # 创建过期时间索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_expire ON cache(expire_at)')
                
                conn.commit()
                conn.close()
                
                app.logger.info(f'SQLite 缓存表已创建：{self.db_path}')
        except Exception as e:
            app.logger.error(f'SQLite 表创建失败：{str(e)}')
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                current_time = int(time.time())
                cursor.execute('DELETE FROM cache WHERE expire_at < ?', (current_time,))
                conn.commit()
                conn.close()
        except Exception as e:
            current_app.logger.error(f'SQLite 清理过期缓存失败：{str(e)}')
    
    def get(self, key):
        """获取缓存"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                current_time = int(time.time())
                
                cursor.execute(
                    'SELECT value FROM cache WHERE key = ? AND expire_at > ?',
                    (key, current_time)
                )
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    return json.loads(result[0])
                return None
        except Exception as e:
            current_app.logger.error(f'SQLite GET 错误：{str(e)}')
            return None
    
    def set(self, key, value, expire=None, timeout=None):
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒）- 与 Redis 兼容的参数名
            timeout: 过期时间（秒）- 备用参数名
        """
        # 兼容 Redis 的 expire 参数
        if expire is not None:
            timeout = expire
            
        if timeout is None:
            timeout = self.default_timeout
        
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                current_time = int(time.time())
                expire_at = current_time + timeout
                
                serialized = json.dumps(value, ensure_ascii=False, default=str)
                
                # 使用 UPSERT 语法
                cursor.execute('''
                    INSERT INTO cache (key, value, expire_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        expire_at = excluded.expire_at
                ''', (key, serialized, expire_at))
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            current_app.logger.error(f'SQLite SET 错误：{str(e)}')
            return False
    
    def delete(self, key):
        """删除缓存"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM cache WHERE key = ?', (key,))
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            current_app.logger.error(f'SQLite DELETE 错误：{str(e)}')
            return False
    
    def exists(self, key):
        """检查缓存是否存在"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                current_time = int(time.time())
                cursor.execute(
                    'SELECT 1 FROM cache WHERE key = ? AND expire_at > ? LIMIT 1',
                    (key, current_time)
                )
                result = cursor.fetchone()
                conn.close()
                return result is not None
        except Exception as e:
            current_app.logger.error(f'SQLite EXISTS 错误：{str(e)}')
            return False
    
    def clear_pattern(self, pattern):
        """清除匹配模式的缓存"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                # 将 Redis 风格转换为 SQLite LIKE
                sql_pattern = pattern.replace('*', '%')
                cursor.execute('DELETE FROM cache WHERE key LIKE ?', (sql_pattern,))
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            current_app.logger.error(f'SQLite CLEAR PATTERN 错误：{str(e)}')
            return False
    
    def generate_key(self, prefix, *args, **kwargs):
        """生成缓存键"""
        args_str = ':'.join(str(arg) for arg in args)
        kwargs_str = ':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))
        
        key_parts = [prefix]
        if args_str:
            key_parts.append(args_str)
        if kwargs_str:
            key_parts.append(kwargs_str)
        
        key_string = ':'.join(key_parts)
        key_hash = hashlib.md5(key_string.encode('utf-8')).hexdigest()
        
        return f'{prefix}:{key_hash}'


class RedisCacheService:
    """Redis 缓存服务类"""
    
    def __init__(self, app=None):
        self.redis_client = None
        self.default_timeout = 300  # 默认 5 分钟
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化 Redis 连接"""
        self.redis_client = self._create_redis_client(app)
    
    def _create_redis_client(self, app):
        """创建 Redis 客户端"""
        try:
            import redis
            from redis import ConnectionPool
            
            # 从配置获取 Redis 配置
            redis_config = {
                'host': app.config.get('REDIS_HOST', 'localhost'),
                'port': app.config.get('REDIS_PORT', 6379),
                'db': app.config.get('REDIS_DB', 0),
                'password': app.config.get('REDIS_PASSWORD', None),
                'decode_responses': True,
                'socket_connect_timeout': 5,
                'socket_timeout': 5
            }
            
            pool = ConnectionPool(**redis_config)
            client = redis.Redis(connection_pool=pool)
            
            # 测试连接
            client.ping()
            app.logger.info('Redis 连接成功')
            return client
            
        except Exception as e:
            app.logger.warning(f'Redis 连接失败：{str(e)}')
            return None
    
    def get(self, key):
        """获取缓存"""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            current_app.logger.error(f'Redis GET 错误：{str(e)}')
            return None
    
    def set(self, key, value, timeout=None):
        """设置缓存"""
        if not self.redis_client:
            return False
        
        if timeout is None:
            timeout = self.default_timeout
        
        try:
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            self.redis_client.setex(key, timeout, serialized)
            return True
        except Exception as e:
            current_app.logger.error(f'Redis SET 错误：{str(e)}')
            return False
    
    def delete(self, key):
        """删除缓存"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            current_app.logger.error(f'Redis DELETE 错误：{str(e)}')
            return False
    
    def exists(self, key):
        """检查缓存是否存在"""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            current_app.logger.error(f'Redis EXISTS 错误：{str(e)}')
            return False
    
    def clear_pattern(self, pattern):
        """清除匹配模式的缓存"""
        if not self.redis_client:
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            current_app.logger.error(f'Redis CLEAR PATTERN 错误：{str(e)}')
            return False
    
    def generate_key(self, prefix, *args, **kwargs):
        """生成缓存键"""
        # 将参数转换为字符串
        args_str = ':'.join(str(arg) for arg in args)
        kwargs_str = ':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))
        
        # 组合所有参数
        key_parts = [prefix]
        if args_str:
            key_parts.append(args_str)
        if kwargs_str:
            key_parts.append(kwargs_str)
        
        # 使用 MD5 哈希确保键长度适中
        key_string = ':'.join(key_parts)
        key_hash = hashlib.md5(key_string.encode('utf-8')).hexdigest()
        
        return f'{prefix}:{key_hash}'


# 缓存装饰器
def cache(key=None, timeout=300, prefix='default', expire=None):
    """
    缓存装饰器
    
    用法:
    @cache(prefix='warehouse', timeout=300)
    def get_warehouse_list():
        ...
    
    @cache(key='warehouse:{id}', timeout=300)
    def get_warehouse_by_id(id):
        ...
    
    @cache('categories:active', expire=3600)  # 兼容 expire 参数
    def get_categories():
        ...
    """
    # 兼容 expire 参数
    if expire is not None:
        timeout = expire
        
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import current_app
            
            cache_service = current_app.extensions.get('cache')
            # 支持 Redis 和 SQLite 缓存
            cache_available = cache_service and (hasattr(cache_service, 'redis_client') or hasattr(cache_service, 'db_path'))
            if not cache_available:
                return func(*args, **kwargs)
            
            # 生成缓存键
            if key:
                # 使用自定义键（支持格式化）
                cache_key = key.format(*args, **kwargs)
            else:
                # 自动生成键
                cache_key = cache_service.generate_key(prefix, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数获取值
            result = func(*args, **kwargs)
            
            # 存入缓存（使用 expire 参数名以兼容两种实现）
            cache_service.set(cache_key, result, timeout=timeout)
            
            return result
        
        return wrapper
    return decorator


# 全局缓存服务实例
cache_service = RedisCacheService()


def init_cache(app):
    """初始化缓存服务"""
    cache_service.init_app(app)
    app.extensions['cache'] = cache_service
    return cache_service
