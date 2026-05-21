"""
操作审计服务
记录所有重要操作的详细日志，支持审计和追溯
"""

from flask import request, g
from flask_login import current_user
from datetime import datetime
from app.extensions import db
import json


class OperationLog(db.Model):
    """操作日志模型"""
    __tablename__ = 'operation_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 操作信息
    operation_type = db.Column(db.String(50), nullable=False, index=True)  # 操作类型
    resource_type = db.Column(db.String(50), nullable=False, index=True)   # 资源类型
    resource_id = db.Column(db.Integer)                                     # 资源 ID
    
    # 用户信息
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_name = db.Column(db.String(100))                                   # 用户名（冗余存储）
    
    # 操作详情
    action = db.Column(db.String(50), nullable=False)                       # 具体操作 (create/update/delete/query)
    description = db.Column(db.Text)                                        # 操作描述
    
    # 变更内容
    old_value = db.Column(db.JSON)                                          # 原值
    new_value = db.Column(db.JSON)                                          # 新值
    changes = db.Column(db.JSON)                                            # 变更字段
    
    # 请求信息
    ip_address = db.Column(db.String(50))                                   # IP 地址
    user_agent = db.Column(db.String(500))                                  # User-Agent
    request_method = db.Column(db.String(10))                               # 请求方法
    request_path = db.Column(db.String(200))                                # 请求路径
    
    # 执行结果
    status = db.Column(db.String(20), default='success')                    # 状态 (success/error)
    error_message = db.Column(db.Text)                                      # 错误信息
    execution_time = db.Column(db.Integer)                                  # 执行时间 (ms)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # 索引
    __table_args__ = (
        db.Index('idx_resource', 'resource_type', 'resource_id'),
        db.Index('idx_user', 'user_id', 'created_at'),
        db.Index('idx_action', 'action'),
    )
    
    def __repr__(self):
        return f'<OperationLog {self.id} - {self.user_name} {self.action} {self.resource_type}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'operation_type': self.operation_type,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'action': self.action,
            'description': self.description,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'changes': self.changes,
            'ip_address': self.ip_address,
            'request_method': self.request_method,
            'request_path': self.request_path,
            'status': self.status,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class AuditService:
    """审计服务类"""
    
    @staticmethod
    def log_operation(
        action,
        resource_type,
        resource_id=None,
        operation_type=None,
        description=None,
        old_value=None,
        new_value=None,
        changes=None,
        status='success',
        error_message=None,
        execution_time=None
    ):
        """
        记录操作日志
        
        Args:
            action: 操作类型 (create/update/delete/query)
            resource_type: 资源类型 (warehouse/spare_part/inventory 等)
            resource_id: 资源 ID
            operation_type: 操作类型（业务分类）
            description: 操作描述
            old_value: 原值（字典）
            new_value: 新值（字典）
            changes: 变更字段（字典）
            status: 状态 (success/error)
            error_message: 错误信息
            execution_time: 执行时间 (ms)
        """
        try:
            log = OperationLog(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                operation_type=operation_type or action,
                description=description,
                old_value=old_value,
                new_value=new_value,
                changes=changes,
                status=status,
                error_message=error_message,
                execution_time=execution_time,
                # 用户信息
                user_id=current_user.id if current_user.is_authenticated else None,
                user_name=current_user.real_name if current_user.is_authenticated else 'Anonymous',
                # 请求信息
                ip_address=request.remote_addr if request else None,
                user_agent=request.user_agent.string[:500] if request else None,
                request_method=request.method if request else None,
                request_path=request.path if request else None
            )
            
            db.session.add(log)
            db.session.commit()
            
            return log.id
            
        except Exception as e:
            # 日志记录失败不应该影响主流程
            db.session.rollback()
            print(f'记录操作日志失败：{str(e)}')
            return None
    
    @staticmethod
    def get_user_operations(user_id, page=1, per_page=20):
        """获取用户的操作日志"""
        from app.utils.helpers import paginate_query
        
        query = OperationLog.query.filter_by(user_id=user_id).order_by(
            OperationLog.created_at.desc()
        )
        
        return paginate_query(query, page=page, per_page=per_page)
    
    @staticmethod
    def get_resource_operations(resource_type, resource_id):
        """获取资源的操作历史"""
        return OperationLog.query.filter_by(
            resource_type=resource_type,
            resource_id=resource_id
        ).order_by(OperationLog.created_at.desc()).all()
    
    @staticmethod
    def get_recent_operations(limit=100):
        """获取最近的操作日志"""
        return OperationLog.query.order_by(
            OperationLog.created_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def search_operations(
        keyword=None,
        action=None,
        resource_type=None,
        user_id=None,
        start_date=None,
        end_date=None,
        page=1,
        per_page=20
    ):
        """搜索操作日志"""
        from app.utils.helpers import paginate_query
        
        query = OperationLog.query
        
        # 关键词搜索
        if keyword:
            keyword = f'%{keyword}%'
            query = query.filter(
                db.or_(
                    OperationLog.description.like(keyword),
                    OperationLog.user_name.like(keyword)
                )
            )
        
        # 筛选条件
        if action:
            query = query.filter(OperationLog.action == action)
        if resource_type:
            query = query.filter(OperationLog.resource_type == resource_type)
        if user_id:
            query = query.filter(OperationLog.user_id == user_id)
        if start_date:
            query = query.filter(OperationLog.created_at >= start_date)
        if end_date:
            query = query.filter(OperationLog.created_at <= end_date)
        
        query = query.order_by(OperationLog.created_at.desc())
        
        return paginate_query(query, page=page, per_page=per_page)
    
    @staticmethod
    def cleanup_old_logs(days=90):
        """清理旧日志"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = OperationLog.query.filter(
            OperationLog.created_at < cutoff_date
        ).delete()
        
        db.session.commit()
        
        return deleted


# 装饰器：自动记录操作日志
def audit_log(action, resource_type, get_resource_id=None):
    """
    审计日志装饰器
    
    用法:
    @audit_log('create', 'warehouse')
    def create_warehouse(data):
        ...
    
    @audit_log('update', 'warehouse', get_resource_id=lambda data: data.get('id'))
    def update_warehouse(data):
        ...
    """
    from functools import wraps
    import time
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # 执行原函数
            try:
                result = func(*args, **kwargs)
                
                # 记录成功日志
                execution_time = int((time.time() - start_time) * 1000)
                
                # 获取资源 ID
                resource_id = None
                if get_resource_id:
                    resource_id = get_resource_id(kwargs.get('data', {}))
                elif result and isinstance(result, dict):
                    resource_id = result.get('id')
                
                # 获取变更内容
                old_value = None
                new_value = None
                changes = None
                
                if action in ['update', 'delete']:
                    old_value = kwargs.get('old_value')
                
                if action in ['create', 'update']:
                    new_value = kwargs.get('data')
                
                if old_value and new_value and action == 'update':
                    changes = {}
                    for key in set(old_value.keys()) | set(new_value.keys()):
                        if old_value.get(key) != new_value.get(key):
                            changes[key] = {
                                'old': old_value.get(key),
                                'new': new_value.get(key)
                            }
                
                AuditService.log_operation(
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    old_value=old_value,
                    new_value=new_value,
                    changes=changes,
                    execution_time=execution_time
                )
                
                return result
                
            except Exception as e:
                # 记录错误日志
                execution_time = int((time.time() - start_time) * 1000)
                
                AuditService.log_operation(
                    action=action,
                    resource_type=resource_type,
                    status='error',
                    error_message=str(e),
                    execution_time=execution_time
                )
                
                raise
        
        return wrapper
    return decorator
