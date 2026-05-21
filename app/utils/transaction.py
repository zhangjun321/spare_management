# -*- coding: utf-8 -*-
"""
数据库事务管理工具

提供统一的事务管理上下文管理器，确保：
1. commit/rollback 成对出现，避免事务泄漏
2. 数据库异常（IntegrityError, OperationalError）被正确捕获并转换
3. 业务异常（BusinessError 子类）正常透传

用法：
    from app.utils.transaction import transactional

    # 方式 1：上下文管理器（推荐用于路由函数）
    @api_xxx_bp.route('/<int:id>', methods=['PUT'])
    @login_required
    def update_xxx(id):
        with transactional():
            obj = Model.query.get(id)
            obj.name = 'new name'
            db.session.add(obj)
            # 不需要手动 commit/rollback，退出 with 块时自动处理
        return ok(data=obj.to_dict())

    # 方式 2：装饰器
    @transactional()
    def my_service_function():
        ...
"""

from contextlib import contextmanager
from app.extensions import db
from app.utils.exceptions import BusinessError
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError


@contextmanager
def transactional():
    """
    事务上下文管理器。

    - 正常退出时自动 commit
    - BusinessError 子类 → rollback 后重新抛出
    - SQLAlchemy 错误（IntegrityError / OperationalError）→ rollback → 转为 BusinessError
    - 其他 Exception → rollback 后重新抛出
    """
    try:
        yield
        db.session.commit()
    except BusinessError:
        db.session.rollback()
        raise
    except (IntegrityError, OperationalError) as e:
        db.session.rollback()
        _error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        # 检测常见约束冲突类型
        if 'UNIQUE' in str(e).upper() or 'duplicate' in _error_msg.lower():
            from app.utils.exceptions import ConflictError
            raise ConflictError(f'数据冲突: {_error_msg}')
        elif 'FOREIGN' in str(e).upper():
            from app.utils.exceptions import ParamError
            raise ParamError(f'关联数据不存在: {_error_msg}')
        else:
            raise BusinessError(f'数据库操作失败: {_error_msg}')
    except SQLAlchemyError as e:
        db.session.rollback()
        raise BusinessError(f'数据库错误: {str(e)}')
    except Exception:
        db.session.rollback()
        raise
