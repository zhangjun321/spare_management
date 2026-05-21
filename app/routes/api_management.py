# -*- coding: utf-8 -*-
"""
API接口管理路由
F0-2 已迁移：全部 jsonify → ok() / error() / paginated_data()
F0-3 已迁移：业务校验 → raise BusinessError 子类
"""

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.api import ApiCategory, ApiEndpoint, ApiLog, init_api_data
from app.utils.decorators import permission_required
from app.utils.response import ok, error, ResponseCode
from app.utils.exceptions import ParamError, BusinessError

api_bp = Blueprint('api_management', __name__, template_folder='../templates/api')


@api_bp.route('/')
@login_required
def api_index():
    """API文档首页"""
    try:
        init_api_data()
    except Exception:
        pass

    categories = ApiCategory.query.filter_by(status=True).order_by(
        ApiCategory.sort_order, ApiCategory.created_at
    ).all()

    return render_template('api/index.html', categories=categories)


@api_bp.route('/doc/<int:endpoint_id>')
@login_required
def api_doc(endpoint_id):
    """API文档详情页"""
    endpoint = ApiEndpoint.query.get_or_404(endpoint_id)
    categories = ApiCategory.query.filter_by(status=True).order_by(
        ApiCategory.sort_order, ApiCategory.created_at
    ).all()
    return render_template('api/doc.html', endpoint=endpoint, categories=categories)


@api_bp.route('/manage')
@login_required
@permission_required('system', 'read')
def api_manage():
    """API管理首页"""
    return render_template('api/manage.html')


@api_bp.route('/logs')
@login_required
@permission_required('system', 'read')
def api_logs():
    """API调用日志"""
    return render_template('api/logs.html')


@api_bp.route('/api/categories')
@login_required
def get_categories():
    """获取分类列表"""
    try:
        categories = ApiCategory.query.order_by(
            ApiCategory.sort_order, ApiCategory.created_at.desc()
        ).all()

        data = []
        for cat in categories:
            ep_count = cat.endpoints.count() if cat.endpoints else 0
            data.append({
                'id': cat.id,
                'name': cat.name,
                'code': cat.code,
                'description': cat.description,
                'icon': cat.icon,
                'status': cat.status,
                'sort_order': cat.sort_order,
                'endpoint_count': ep_count,
                'created_at': cat.created_at.strftime('%Y-%m-%d %H:%M:%S') if cat.created_at else None
            })
        return ok(data=data)
    except Exception as e:
        raise BusinessError(f'获取分类列表失败: {e}')


@api_bp.route('/api/endpoints')
@login_required
def get_endpoints():
    """获取接口列表"""
    try:
        category_id = request.args.get('category_id', type=int)
        query = ApiEndpoint.query
        if category_id:
            query = query.filter_by(category_id=category_id)
        endpoints = query.order_by(ApiEndpoint.sort_order, ApiEndpoint.created_at.desc()).all()

        data = []
        for ep in endpoints:
            data.append({
                'id': ep.id,
                'category_id': ep.category_id,
                'category_name': ep.category.name if ep.category else '',
                'name': ep.name,
                'path': ep.path,
                'method': ep.method,
                'description': ep.description,
                'is_published': ep.is_published,
                'require_auth': ep.require_auth,
                'rate_limit': ep.rate_limit,
                'sort_order': ep.sort_order,
                'created_at': ep.created_at.strftime('%Y-%m-%d %H:%M:%S') if ep.created_at else None
            })
        return ok(data=data)
    except Exception as e:
        raise BusinessError(f'获取接口列表失败: {e}')


@api_bp.route('/api/endpoints/<int:endpoint_id>')
@login_required
def get_endpoint(endpoint_id):
    """获取单个接口详情"""
    try:
        endpoint = ApiEndpoint.query.get_or_404(endpoint_id)
        return ok(data={
            'id': endpoint.id,
            'category_id': endpoint.category_id,
            'name': endpoint.name,
            'path': endpoint.path,
            'method': endpoint.method,
            'description': endpoint.description,
            'request_example': endpoint.request_example,
            'response_example': endpoint.response_example,
            'parameters': endpoint.parameters,
            'is_published': endpoint.is_published,
            'require_auth': endpoint.require_auth,
            'rate_limit': endpoint.rate_limit,
            'sort_order': endpoint.sort_order
        })
    except BusinessError:
        raise
    except Exception as e:
        raise BusinessError(f'获取接口详情失败: {e}')


@api_bp.route('/api/endpoints/create', methods=['POST'])
@login_required
@permission_required('system', 'write')
def create_endpoint():
    """创建接口"""
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'path' not in data or 'method' not in data:
            raise ParamError('缺少必要参数 (name, path, method)')

        endpoint = ApiEndpoint(
            category_id=data.get('category_id'),
            name=data['name'],
            path=data['path'],
            method=data['method'].upper(),
            description=data.get('description', ''),
            request_example=data.get('request_example', ''),
            response_example=data.get('response_example', ''),
            parameters=data.get('parameters', ''),
            is_published=data.get('is_published', False),
            require_auth=data.get('require_auth', True),
            rate_limit=data.get('rate_limit'),
            sort_order=data.get('sort_order', 0)
        )
        db.session.add(endpoint)
        db.session.commit()
        return ok(data={'id': endpoint.id}, message='接口创建成功')
    except BusinessError:
        raise
    except Exception as e:
        db.session.rollback()
        raise BusinessError(f'创建接口失败: {e}')


@api_bp.route('/api/endpoints/<int:endpoint_id>/update', methods=['PUT'])
@login_required
@permission_required('system', 'write')
def update_endpoint(endpoint_id):
    """更新接口"""
    try:
        endpoint = ApiEndpoint.query.get_or_404(endpoint_id)
        data = request.get_json()

        field_map = {
            'category_id': 'category_id', 'name': 'name', 'path': 'path',
            'method': 'method', 'description': 'description',
            'request_example': 'request_example', 'response_example': 'response_example',
            'parameters': 'parameters', 'is_published': 'is_published',
            'require_auth': 'require_auth', 'rate_limit': 'rate_limit',
            'sort_order': 'sort_order',
        }
        for key in field_map:
            if key in data:
                val = data[key]
                if key == 'method':
                    val = val.upper()
                setattr(endpoint, field_map[key], val)

        db.session.commit()
        return ok(message='接口更新成功')
    except BusinessError:
        raise
    except Exception as e:
        db.session.rollback()
        raise BusinessError(f'更新接口失败: {e}')


@api_bp.route('/api/endpoints/<int:endpoint_id>/delete', methods=['DELETE'])
@login_required
@permission_required('system', 'write')
def delete_endpoint(endpoint_id):
    """删除接口"""
    try:
        endpoint = ApiEndpoint.query.get_or_404(endpoint_id)
        db.session.delete(endpoint)
        db.session.commit()
        return ok(message='接口删除成功')
    except BusinessError:
        raise
    except Exception as e:
        db.session.rollback()
        raise BusinessError(f'删除接口失败: {e}')


@api_bp.route('/api/logs')
@login_required
@permission_required('system', 'read')
def get_logs():
    """获取API调用日志"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        endpoint_id = request.args.get('endpoint_id', type=int)
        status = request.args.get('status')

        query = ApiLog.query
        if endpoint_id:
            query = query.filter_by(endpoint_id=endpoint_id)
        if status == 'success':
            query = query.filter_by(is_success=True)
        elif status == 'error':
            query = query.filter_by(is_success=False)

        pagination = query.order_by(ApiLog.created_at.desc()).paginate(
            page=page, per_page=page_size, error_out=False
        )

        data = []
        for log in pagination.items:
            data.append({
                'id': log.id,
                'endpoint_path': log.endpoint_path,
                'endpoint_method': log.endpoint_method,
                'user_id': log.user_id,
                'ip_address': log.ip_address,
                'response_status': log.response_status,
                'execution_time': log.execution_time,
                'is_success': log.is_success,
                'error_message': log.error_message,
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else None
            })

        return ok(data={
            'items': data,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
    except Exception as e:
        raise BusinessError(f'获取日志失败: {e}')
