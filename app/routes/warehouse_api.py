"""
仓库管理 API
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from app.models.warehouse import Warehouse
from app.extensions import db
from sqlalchemy import func

warehouse_api = Blueprint('warehouse_api', __name__, url_prefix='/api/warehouses')


@warehouse_api.route('/list')
@login_required
def get_warehouse_list():
    """
    获取仓库列表（支持搜索和分页）
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    warehouse_type = request.args.get('type', '').strip()
    is_active = request.args.get('is_active', '').strip()
    
    # 构建查询
    query = Warehouse.query
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            db.or_(
                Warehouse.name.like(f'%{keyword}%'),
                Warehouse.code.like(f'%{keyword}%'),
                Warehouse.address.like(f'%{keyword}%'),
                Warehouse.description.like(f'%{keyword}%')
            )
        )
    
    # 类型筛选
    if warehouse_type:
        query = query.filter(Warehouse.type == warehouse_type)
    
    # 状态筛选
    if is_active:
        query = query.filter(Warehouse.is_active == (is_active == 'true'))
    
    # 分页
    pagination = query.order_by(Warehouse.id.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 格式化结果
    warehouses_list = []
    for wh in pagination.items:
        warehouses_list.append({
            'id': wh.id,
            'name': wh.name,
            'code': wh.code,
            'type': wh.type,
            'address': wh.address,
            'manager_name': wh.manager.real_name if wh.manager else None,
            'area': float(wh.area) if wh.area else 0,
            'capacity': wh.capacity,
            'utilization_rate': float(wh.utilization_rate) if wh.utilization_rate else 0,
            'is_active': wh.is_active,
            'created_at': wh.created_at.strftime('%Y-%m-%d %H:%M:%S') if wh.created_at else None
        })
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'list': warehouses_list,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })


@warehouse_api.route('/')
@login_required
def list_page():
    """
    仓库列表页面（带搜索）
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    warehouse_type = request.args.get('type', '')
    is_active = request.args.get('is_active', '')
    
    # 构建查询
    query = Warehouse.query
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            db.or_(
                Warehouse.name.like(f'%{keyword}%'),
                Warehouse.code.like(f'%{keyword}%'),
                Warehouse.address.like(f'%{keyword}%')
            )
        )
    
    # 类型筛选
    if warehouse_type:
        query = query.filter(Warehouse.type == warehouse_type)
    
    # 状态筛选
    if is_active:
        query = query.filter(Warehouse.is_active == (is_active == 'true'))
    
    # 分页
    pagination = query.order_by(Warehouse.id.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 统计
    stats = {
        'total': Warehouse.query.count(),
        'active': Warehouse.query.filter(Warehouse.is_active == True).count(),
        'inactive': Warehouse.query.filter(Warehouse.is_active == False).count()
    }
    
    return render_template('warehouses/list_with_search.html', 
                         pagination=pagination, 
                         warehouses=pagination.items,
                         stats=stats,
                         search_params={
                             'keyword': keyword,
                             'type': warehouse_type,
                             'is_active': is_active
                         })
