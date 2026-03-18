"""
工具函数模块
"""

from datetime import datetime


def datetime_format(value, format='%Y-%m-%d %H:%M'):
    """格式化日期时间"""
    if value:
        return value.strftime(format)
    return ''


def currency_format(value):
    """格式化货币"""
    if value is not None:
        return f'¥{value:,.2f}'
    return '¥0.00'


def generate_order_number(prefix):
    """生成订单编号"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f'{prefix}{timestamp}'


def paginate_query(query, page=None, per_page=20):
    """分页查询"""
    from flask import request
    if page is None:
        try:
            page = int(request.args.get('page', 1))
        except (TypeError, ValueError):
            page = 1
    
    if page < 1:
        page = 1
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return pagination


def get_client_ip(request):
    """获取客户端 IP"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr
