"""
质检标准管理 API
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from app.models.warehouse_v3.quality_check import QualityCheckStandard
from app.models.spare_part import SparePart
from app.extensions import db

quality_standard_api = Blueprint('quality_standard_api', __name__, url_prefix='/api/quality-standard')


@quality_standard_api.route('/list')
@login_required
def get_quality_standard_list():
    """
    获取质检标准列表（支持搜索和分页）
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    category = request.args.get('category', '').strip()
    is_active = request.args.get('is_active', '').strip()
    
    # 构建查询
    query = QualityCheckStandard.query
    
    # 关键词搜索
    if keyword:
        query = query.join(SparePart, QualityCheckStandard.spare_part_id == SparePart.id, isouter=True)\
                    .filter(
            db.or_(
                QualityCheckStandard.name.like(f'%{keyword}%'),
                QualityCheckStandard.code.like(f'%{keyword}%'),
                SparePart.name.like(f'%{keyword}%') if keyword else db.false()
            )
        )
    
    # 分类筛选
    if category:
        query = query.filter(QualityCheckStandard.category == category)
    
    # 状态筛选
    if is_active:
        query = query.filter(QualityCheckStandard.is_active == (is_active == 'true'))
    
    # 分页
    pagination = query.order_by(QualityStandard.id.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 格式化结果
    standard_list = []
    for std in pagination.items:
        standard_list.append({
            'id': std.id,
            'name': std.name,
            'code': std.code,
            'category': std.category,
            'spare_part_id': std.spare_part_id,
            'spare_part_name': std.spare_part.name if std.spare_part else None,
            'check_items': std.check_items,
            'standard_value': std.standard_value,
            'unit': std.unit,
            'tolerance': std.tolerance,
            'check_method': std.check_method,
            'is_active': std.is_active,
            'created_at': std.created_at.strftime('%Y-%m-%d %H:%M:%S') if std.created_at else None,
            'updated_at': std.updated_at.strftime('%Y-%m-%d %H:%M:%S') if std.updated_at else None
        })
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'list': standard_list,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })


@quality_standard_api.route('/')
@login_required
def list_page():
    """
    质检标准列表页面（带搜索）
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    category = request.args.get('category', '').strip()
    is_active = request.args.get('is_active', '').strip()
    
    # 构建查询
    query = QualityCheckStandard.query
    
    # 关键词搜索
    if keyword:
        query = query.join(SparePart, QualityCheckStandard.spare_part_id == SparePart.id, isouter=True)\
                    .filter(
            db.or_(
                QualityCheckStandard.name.like(f'%{keyword}%'),
                QualityCheckStandard.code.like(f'%{keyword}%'),
                SparePart.name.like(f'%{keyword}%') if keyword else db.false()
            )
        )
    
    # 分类筛选
    if category:
        query = query.filter(QualityCheckStandard.category == category)
    
    # 状态筛选
    if is_active:
        query = query.filter(QualityCheckStandard.is_active == (is_active == 'true'))
    
    # 分页
    pagination = query.order_by(QualityCheckStandard.id.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 统计
    stats = {
        'total': QualityCheckStandard.query.count(),
        'active': QualityCheckStandard.query.filter(QualityCheckStandard.is_active == True).count(),
        'inactive': QualityCheckStandard.query.filter(QualityCheckStandard.is_active == False).count()
    }
    
    return render_template('warehouse_new/quality_standard_list_with_search.html', 
                         pagination=pagination, 
                         standards=pagination.items,
                         stats=stats,
                         search_params={
                             'keyword': keyword,
                             'category': category,
                             'is_active': is_active
                         })
