"""
备件管理 API - 搜索功能
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models.spare_part import SparePart
from app.extensions import db

spare_parts_api = Blueprint('spare_parts_api', __name__, url_prefix='/api/spare-parts')


@spare_parts_api.route('/list')
@login_required
def get_spare_parts_list():
    """
    获取备件列表（支持搜索和分页）
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    
    # 构建查询
    query = SparePart.query
    
    # 关键词搜索（支持多个字段）
    if keyword:
        query = query.filter(
            db.or_(
                SparePart.name.like(f'%{keyword}%'),
                SparePart.code.like(f'%{keyword}%'),
                SparePart.model.like(f'%{keyword}%'),
                SparePart.spec.like(f'%{keyword}%'),
                SparePart.material.like(f'%{keyword}%')
            )
        )
    
    # 分页
    pagination = query.order_by(SparePart.id.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 格式化结果
    parts_list = []
    for part in pagination.items:
        parts_list.append({
            'id': part.id,
            'name': part.name,
            'code': part.code,
            'model': part.model,
            'spec': part.spec,
            'category': part.category.name if part.category else None,
            'supplier': part.supplier.name if part.supplier else None,
            'stock_quantity': part.stock_quantity,
            'unit': part.unit,
            'price': float(part.price) if part.price else 0,
            'status': part.status,
            'is_active': part.is_active
        })
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'list': parts_list,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })
