"""
并发控制工具模块
提供乐观锁、事务控制等并发控制功能
"""

from functools import wraps
from flask import current_app
from app.extensions import db
from datetime import datetime
import threading


class OptimisticLock:
    """乐观锁工具类"""
    
    @staticmethod
    def check_version(model_instance, expected_version):
        """
        检查版本号是否匹配
        
        Args:
            model_instance: 模型实例
            expected_version: 期望的版本号
            
        Returns:
            bool: 版本号是否匹配
        """
        if not hasattr(model_instance, 'version'):
            return True
        
        return model_instance.version == expected_version
    
    @staticmethod
    def increment_version(model_instance):
        """
        增加版本号
        
        Args:
            model_instance: 模型实例
            
        Returns:
            int: 新版本号
        """
        if hasattr(model_instance, 'version'):
            model_instance.version += 1
            model_instance.updated_at = datetime.utcnow()
            return model_instance.version
        return None


class TransactionManager:
    """事务管理器"""
    
    @staticmethod
    def execute_with_transaction(func, *args, **kwargs):
        """
        在事务中执行函数
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 关键字参数
            
        Returns:
            函数执行结果
        """
        try:
            result = func(*args, **kwargs)
            db.session.commit()
            return result
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"事务执行失败：{str(e)}")
            raise
    
    @staticmethod
    def execute_with_retry(func, max_retries=3, delay=0.1):
        """
        带重试执行函数
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            delay: 重试延迟（秒）
            
        Returns:
            函数执行结果
        """
        import time
        
        last_error = None
        for attempt in range(max_retries):
            try:
                return TransactionManager.execute_with_transaction(func)
            except Exception as e:
                last_error = e
                current_app.logger.warning(f"执行失败，第 {attempt + 1} 次重试：{str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
        
        raise last_error


class LockManager:
    """锁管理器 - 基于数据库的分布式锁"""
    
    _locks = {}
    _lock = threading.Lock()
    
    @classmethod
    def acquire(cls, lock_name, timeout=30):
        """
        获取锁
        
        Args:
            lock_name: 锁名称
            timeout: 超时时间（秒）
            
        Returns:
            bool: 是否成功获取锁
        """
        import time
        
        start_time = time.time()
        
        with cls._lock:
            while True:
                if lock_name not in cls._locks:
                    cls._locks[lock_name] = {
                        'acquired_at': datetime.utcnow(),
                        'timeout': timeout
                    }
                    return True
                
                lock_info = cls._locks[lock_name]
                elapsed = (datetime.utcnow() - lock_info['acquired_at']).total_seconds()
                
                if elapsed > timeout:
                    # 锁已超时，强制释放
                    del cls._locks[lock_name]
                    cls._locks[lock_name] = {
                        'acquired_at': datetime.utcnow(),
                        'timeout': timeout
                    }
                    return True
                
                if time.time() - start_time > timeout:
                    return False
                
                time.sleep(0.1)
    
    @classmethod
    def release(cls, lock_name):
        """
        释放锁
        
        Args:
            lock_name: 锁名称
        """
        with cls._lock:
            if lock_name in cls._locks:
                del cls._locks[lock_name]
    
    @classmethod
    def is_locked(cls, lock_name):
        """
        检查是否已锁定
        
        Args:
            lock_name: 锁名称
            
        Returns:
            bool: 是否已锁定
        """
        if lock_name not in cls._locks:
            return False
        
        lock_info = cls._locks[lock_name]
        elapsed = (datetime.utcnow() - lock_info['acquired_at']).total_seconds()
        
        if elapsed > lock_info['timeout']:
            # 锁已超时
            with cls._lock:
                if lock_name in cls._locks:
                    del cls._locks[lock_name]
            return False
        
        return True


def optimistic_lock(model_class, version_field='version'):
    """
    乐观锁装饰器
    
    Args:
        model_class: 模型类
        version_field: 版本字段名
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取模型实例和期望版本号
            model_instance = kwargs.get('instance') or args[0] if args else None
            expected_version = kwargs.get('expected_version')
            
            if model_instance and expected_version is not None:
                # 检查版本号
                current_version = getattr(model_instance, version_field, None)
                if current_version != expected_version:
                    raise Exception(f'数据已被修改，当前版本号：{current_version}, 期望版本号：{expected_version}')
                
                # 增加版本号
                setattr(model_instance, version_field, current_version + 1)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def with_transaction(func):
    """
    事务装饰器
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            db.session.commit()
            return result
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"事务执行失败：{str(e)}")
            raise
    return wrapper


def with_retry(max_retries=3, delay=0.1):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
    """
    import time
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    current_app.logger.warning(f"执行失败，第 {attempt + 1} 次重试：{str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(delay)
            
            raise last_error
        return wrapper
    return decorator


def distributed_lock(lock_name, timeout=30):
    """
    分布式锁装饰器
    
    Args:
        lock_name: 锁名称
        timeout: 超时时间（秒）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not LockManager.acquire(lock_name, timeout):
                raise Exception(f'获取锁失败：{lock_name}')
            
            try:
                return func(*args, **kwargs)
            finally:
                LockManager.release(lock_name)
        return wrapper
    return decorator


def check_inventory_conflict(warehouse_id, part_id, exclude_batch_id=None):
    """
    检查库存冲突
    
    Args:
        warehouse_id: 仓库 ID
        part_id: 备件 ID
        exclude_batch_id: 排除的批次 ID
        
    Returns:
        bool: 是否存在冲突
    """
    from app.models.warehouse_v3 import InventoryV3
    
    query = InventoryV3.query.filter_by(
        warehouse_id=warehouse_id,
        part_id=part_id
    )
    
    if exclude_batch_id:
        query = query.filter(InventoryV3.batch_id != exclude_batch_id)
    
    count = query.count()
    return count > 0


def safe_update_inventory(inventory_id, quantity_change, operation_type='in', max_retries=3):
    """
    安全更新库存（带乐观锁和重试）
    
    Args:
        inventory_id: 库存 ID
        quantity_change: 数量变化
        operation_type: 操作类型（in/out）
        max_retries: 最大重试次数
        
    Returns:
        bool: 是否成功
    """
    from app.models.warehouse_v3 import InventoryV3
    
    for attempt in range(max_retries):
        try:
            # 获取库存记录
            inventory = InventoryV3.query.get(inventory_id)
            if not inventory:
                raise Exception('库存记录不存在')
            
            # 检查可用数量
            if operation_type == 'out':
                if inventory.available_quantity < quantity_change:
                    raise Exception('可用库存不足')
                inventory.quantity -= quantity_change
                inventory.available_quantity -= quantity_change
            else:
                inventory.quantity += quantity_change
                inventory.available_quantity += quantity_change
            
            inventory.updated_at = datetime.utcnow()
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            if attempt >= max_retries - 1:
                raise
            current_app.logger.warning(f"更新库存失败，第 {attempt + 1} 次重试：{str(e)}")
    
    return False
