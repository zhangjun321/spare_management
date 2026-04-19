"""
质检单管理 API
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from app.models.warehouse_v3.quality_check import QualityCheck
from app.models.spare_part import SparePart
from app.models.warehouse import Warehouse
from app.extensions import db

quality_check_api = Blueprint('quality_check_api', __name__, url_prefix='/api/quality-check')


@quality_check_api.route('/list')
@login_required
def get_quality_check_list():
    """
    获取质检单列表（支持搜索和分页）
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '').strip()
    result = request.args.get('result', '').strip()
    
    # 构建查询
    query = QualityCheck.query
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            db.or_(
                QualityCheck.check_code.like(f'%{keyword}%'),
                QualityCheck.batch_number.like(f'%{keyword}%'),
                QualityCheck.remark.like(f'%{keyword}%')
            )
        )
    
    # 状态筛选
    if status:
        query = query.filter(QualityCheck.status == status)
    
    # 结果筛选
    if result:
        query = query.filter(QualityCheck.result == result)
    
    # 分页
    pagination = query.order_by(QualityCheck.id.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 格式化结果
    check_list = []
    for check in pagination.items:
        check_list.append({
            'id': check.id,
            'check_code': check.check_code,
            'batch_number': check.batch_number,
            'spare_part_id': check.spare_part_id,
            'spare_part_name': check.spare_part.name if check.spare_part else None,
            'spare_part_code': check.spare_part.code if check.spare_part else None,
            'warehouse_id': check.warehouse_id,
            'warehouse_name': check.warehouse.name if check.warehouse else None,
            'quantity': check.quantity,
            'qualified_quantity': check.qualified_quantity,
            'unqualified_quantity': check.unqualified_quantity,
            'qualification_rate': float(check.qualification_rate) if check.qualification_rate else 0,
            'check_type': check.check_type,
            'check_method': check.check_method,
            'status': check.status,
            'result': check.result,
            'inspector_name': check.inspector.real_name if check.inspector else None,
            'created_at': check.created_at.strftime('%Y-%m-%d %H:%M:%S') if check.created_at else None,
            'completed_at': check.completed_at.strftime('%Y-%m-%d %H:%M:%S') if check.completed_at else None
        })
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'list': check_list,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })


@quality_check_api.route('/')
@login_required
def list_page():
    """
    质检单列表页面（带搜索）
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '').strip()
    result = request.args.get('result', '').strip()
    
    # 构建查询
    query = QualityCheck.query
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            db.or_(
                QualityCheck.check_code.like(f'%{keyword}%'),
                QualityCheck.batch_number.like(f'%{keyword}%'),
                QualityCheck.remark.like(f'%{keyword}%')
            )
        )
    
    # 状态筛选
    if status:
        query = query.filter(QualityCheck.status == status)
    
    # 结果筛选
    if result:
        query = query.filter(QualityCheck.result == result)
    
    # 分页
    pagination = query.order_by(QualityCheck.id.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 统计
    stats = {
        'total': QualityCheck.query.count(),
        'pending': QualityCheck.query.filter(QualityCheck.status == 'pending').count(),
        'completed': QualityCheck.query.filter(QualityCheck.status == 'completed').count(),
        'qualified': QualityCheck.query.filter(QualityCheck.result == 'qualified').count(),
        'unqualified': QualityCheck.query.filter(QualityCheck.result == 'unqualified').count()
    }
    
    return render_template('warehouse_new/quality_check_list_with_search.html', 
                         pagination=pagination, 
                         checks=pagination.items,
                         stats=stats,
                         search_params={
                             'keyword': keyword,
                             'status': status,
                             'result': result
                         })
