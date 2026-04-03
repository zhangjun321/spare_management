# -*- coding: utf-8 -*-
"""
API接口管理模型
"""

from datetime import datetime
from app.extensions import db


class ApiCategory(db.Model):
    """API接口分类表"""
    
    __tablename__ = 'api_category'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='分类ID')
    name = db.Column(db.String(100), nullable=False, comment='分类名称')
    code = db.Column(db.String(100), unique=True, nullable=False, index=True, comment='分类编码')
    description = db.Column(db.String(500), nullable=True, comment='分类描述')
    sort_order = db.Column(db.Integer, nullable=False, default=0, comment='排序')
    icon = db.Column(db.String(100), nullable=True, comment='图标')
    status = db.Column(db.Boolean, nullable=False, default=True, comment='状态：0-禁用，1-启用')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    endpoints = db.relationship('ApiEndpoint', foreign_keys='ApiEndpoint.category_id',
                                backref='category', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ApiCategory {self.name}>'


class ApiEndpoint(db.Model):
    """API接口端点表"""
    
    __tablename__ = 'api_endpoint'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='接口ID')
    category_id = db.Column(db.Integer, db.ForeignKey('api_category.id'), nullable=False, index=True, comment='分类ID')
    name = db.Column(db.String(200), nullable=False, comment='接口名称')
    path = db.Column(db.String(500), nullable=False, index=True, comment='接口路径')
    method = db.Column(db.String(20), nullable=False, index=True, comment='请求方法：GET,POST,PUT,DELETE,PATCH')
    description = db.Column(db.Text, nullable=True, comment='接口描述')
    request_example = db.Column(db.Text, nullable=True, comment='请求示例（JSON）')
    response_example = db.Column(db.Text, nullable=True, comment='响应示例（JSON）')
    parameters = db.Column(db.Text, nullable=True, comment='参数说明（JSON）')
    is_published = db.Column(db.Boolean, nullable=False, default=False, comment='是否发布')
    require_auth = db.Column(db.Boolean, nullable=False, default=True, comment='是否需要认证')
    rate_limit = db.Column(db.Integer, nullable=True, comment='限流次数（每分钟）')
    sort_order = db.Column(db.Integer, nullable=False, default=0, comment='排序')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<ApiEndpoint {self.method} {self.path}>'
    
    def get_parameters_list(self):
        """获取参数列表"""
        if self.parameters:
            import json
            try:
                return json.loads(self.parameters)
            except:
                pass
        return []


class ApiLog(db.Model):
    """API调用日志表"""
    
    __tablename__ = 'api_log'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='日志ID')
    endpoint_id = db.Column(db.Integer, db.ForeignKey('api_endpoint.id'), nullable=True, index=True, comment='接口ID')
    endpoint_path = db.Column(db.String(500), nullable=False, index=True, comment='接口路径')
    endpoint_method = db.Column(db.String(20), nullable=False, index=True, comment='请求方法')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True, comment='用户ID')
    ip_address = db.Column(db.String(50), nullable=True, index=True, comment='IP地址')
    user_agent = db.Column(db.String(500), nullable=True, comment='用户代理')
    request_headers = db.Column(db.Text, nullable=True, comment='请求头（JSON）')
    request_body = db.Column(db.Text, nullable=True, comment='请求体')
    response_status = db.Column(db.Integer, nullable=True, index=True, comment='响应状态码')
    response_body = db.Column(db.Text, nullable=True, comment='响应体')
    execution_time = db.Column(db.Float, nullable=True, comment='执行时间（毫秒）')
    is_success = db.Column(db.Boolean, nullable=True, index=True, comment='是否成功')
    error_message = db.Column(db.Text, nullable=True, comment='错误信息')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True, comment='创建时间')
    
    # 关系
    endpoint = db.relationship('ApiEndpoint', foreign_keys=[endpoint_id])
    user = db.relationship('User', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<ApiLog {self.endpoint_method} {self.endpoint_path}>'


def init_api_data():
    """初始化API接口数据"""
    # 检查是否已初始化
    if ApiCategory.query.count() > 0:
        return
    
    # 创建默认分类
    categories = [
        {
            'name': '系统接口',
            'code': 'system',
            'description': '系统基础接口',
            'icon': 'fa-cog',
            'sort_order': 1
        },
        {
            'name': '用户接口',
            'code': 'user',
            'description': '用户管理接口',
            'icon': 'fa-users',
            'sort_order': 2
        },
        {
            'name': '备件接口',
            'code': 'spare_parts',
            'description': '备件管理接口',
            'icon': 'fa-box',
            'sort_order': 3
        },
        {
            'name': '统计接口',
            'code': 'statistics',
            'description': '数据统计接口',
            'icon': 'fa-chart-bar',
            'sort_order': 4
        }
    ]
    
    category_objects = []
    for cat_data in categories:
        cat = ApiCategory(**cat_data)
        category_objects.append(cat)
        db.session.add(cat)
    
    db.session.flush()
    
    # 创建示例接口
    endpoints = [
        {
            'category_id': category_objects[0].id,
            'name': '获取系统信息',
            'path': '/api/system/info',
            'method': 'GET',
            'description': '获取系统基本信息，包括版本、运行时间等',
            'request_example': '{}',
            'response_example': '''{
  "status": "success",
  "data": {
    "version": "1.0.0",
    "uptime": "24h 35m",
    "status": "healthy"
  }
}''',
            'is_published': True,
            'require_auth': True,
            'sort_order': 1
        },
        {
            'category_id': category_objects[1].id,
            'name': '获取用户列表',
            'path': '/api/users',
            'method': 'GET',
            'description': '获取用户列表，支持分页和筛选',
            'parameters': '''[
  {"name": "page", "type": "integer", "required": false, "description": "页码"},
  {"name": "page_size", "type": "integer", "required": false, "description": "每页数量"}
]''',
            'is_published': True,
            'require_auth': True,
            'sort_order': 1
        },
        {
            'category_id': category_objects[1].id,
            'name': '创建用户',
            'path': '/api/users',
            'method': 'POST',
            'description': '创建新用户',
            'request_example': '''{
  "username": "testuser",
  "email": "test@example.com",
  "role_id": 2
}''',
            'is_published': True,
            'require_auth': True,
            'sort_order': 2
        },
        {
            'category_id': category_objects[2].id,
            'name': '获取备件列表',
            'path': '/api/spare-parts',
            'method': 'GET',
            'description': '获取备件列表，支持分类筛选和搜索',
            'is_published': True,
            'require_auth': True,
            'sort_order': 1
        },
        {
            'category_id': category_objects[3].id,
            'name': '获取仪表盘统计',
            'path': '/api/dashboard/stats',
            'method': 'GET',
            'description': '获取仪表盘关键指标统计数据',
            'is_published': True,
            'require_auth': True,
            'sort_order': 1
        }
    ]
    
    for ep_data in endpoints:
        ep = ApiEndpoint(**ep_data)
        db.session.add(ep)
    
    db.session.commit()
