# -*- coding: utf-8 -*-
"""
缓存服务模块
"""


import redis
import json
from functools import wraps
from app.config import Config

# Redis 连接池
redis_client = None
redis_available = False

def init_redis():
    """初始化 Redis 连接"""
    global redis_client, redis_available
    try:
        redis_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            password=Config.REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=1,  # 连接超时 1 秒
            socket_timeout=1  # 操作超时 1 秒
        )
        # 测试连接
        redis_client.ping()
        print("Redis 连接成功")
        redis_available = True
        return True
    except Exception as e:
        print(f"Redis 连接失败：{e}")
        redis_available = False
        return False

def get_redis():
    """获取 Redis 客户端"""
    global redis_client
    if redis_client is None and redis_available:
        init_redis()
    return redis_client if redis_available else None

def cache(key_pattern, expire=3600):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 如果 Redis 不可用，直接执行函数
            if not redis_available:
                return func(*args, **kwargs)
            
            # 生成缓存键
            key = key_pattern
            for i, arg in enumerate(args):
                key = key.replace(f"{{{i}}}", str(arg))
            for k, v in kwargs.items():
                key = key.replace(f"{{{k}}}", str(v))
            
            # 尝试从缓存获取
            r = get_redis()
            if r:
                try:
                    cached = r.get(key)
                    if cached:
                        return json.loads(cached)
                except Exception as e:
                    print(f"缓存读取错误：{e}")
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            if r:
                try:
                    r.setex(key, expire, json.dumps(result, default=str))
                except Exception as e:
                    print(f"缓存写入错误：{e}")
            
            return result
        return wrapper
    return decorator

def clear_cache(pattern):
    """清除匹配模式的缓存"""
    r = get_redis()
    if r:
        try:
            keys = r.keys(pattern)
            if keys:
                r.delete(*keys)
                print(f"清除缓存: {len(keys)} 个键")
        except Exception as e:
            print(f"清除缓存错误: {e}")

def get_cached_or_query(key, query_func, expire=3600):
    """获取缓存或执行查询"""
    # 如果 Redis 不可用，直接执行查询
    if not redis_available:
        return query_func()
    
    r = get_redis()
    if r:
        try:
            cached = r.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            print(f"缓存读取错误：{e}")
    
    result = query_func()
    
    if r:
        try:
            r.setex(key, expire, json.dumps(result, default=str))
        except Exception as e:
            print(f"缓存写入错误：{e}")
    
    return result
