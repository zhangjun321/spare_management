"""
入库单管理 API
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from app.models.inbound_outbound import InboundOrder
from app.models.warehouse import Warehouse
from app.models.spare_part import SparePart
from app.extensions import db

inbound_api = Blueprint('inbound_api', __name__, url_prefix='/api/inbound')


@inbound_api.route('/list')
@login_required
def get_inbound_list():
    """
    获取入库单列表（支持搜索和分页）
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '').strip()
    warehouse_id = request.args.get('warehouse_id', '').strip()
    
    # 构建查询
    query = InboundOrder.query
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            db.or_(
                InboundOrder.order_code.like(f'%{keyword}%'),
                InboundOrder.batch_number.like(f'%{keyword}%'),
                InboundOrder.remark.like(f'%{keyword}%')
            )
        )
    
    # 状态筛选
    if status:
        query = query.filter(InboundOrder.status == status)
    
    # 仓库筛选
    if warehouse_id:
        query = query.filter(InboundOrder.warehouse_id == warehouse_id)
    
    # 分页
    pagination = query.order_by(InboundOrder.id.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 格式化结果
    inbound_list = []
    for order in pagination.items:
        inbound_list.append({
            'id': order.id,
            'order_code': order.order_code,
            'batch_number': order.batch_number,
            'warehouse_id': order.warehouse_id,
            'warehouse_name': order.warehouse.name if order.warehouse else None,
            'spare_part_id': order.spare_part_id,
            'spare_part_name': order.spare_part.name if order.spare_part else None,
            'quantity': order.quantity,
            'actual_quantity': order.actual_quantity,
            'unit_price': float(order.unit_price) if order.unit_price else 0,
            'total_amount': float(order.total_amount) if order.total_amount else 0,
            'status': order.status,
            'supplier': order.supplier,
            'creator_name': order.creator.real_name if order.creator else None,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else None,
            'completed_at': order.completed_at.strftime('%Y-%m-%d %H:%M:%S') if order.completed_at else None
        })
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'list': inbound_list,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })


@inbound_api.route('/')
@login_required
def list_page():
    """
    入库单列表页面（带搜索）
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '').strip()
    
    # 构建查询
    query = InboundOrder.query
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            db.or_(
                InboundOrder.order_code.like(f'%{keyword}%'),
                InboundOrder.batch_number.like(f'%{keyword}%'),
                InboundOrder.remark.like(f'%{keyword}%')
            )
        )
    
    # 状态筛选
    if status:
        query = query.filter(InboundOrder.status == status)
    
    # 分页
    pagination = query.order_by(InboundOrder.id.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 获取所有仓库用于筛选
    warehouses = Warehouse.query.filter(Warehouse.is_active == True).all()
    
    # 统计
    stats = {
        'total': InboundOrder.query.count(),
        'pending': InboundOrder.query.filter(InboundOrder.status == 'pending').count(),
        'completed': InboundOrder.query.filter(InboundOrder.status == 'completed').count(),
        'cancelled': InboundOrder.query.filter(InboundOrder.status == 'cancelled').count()
    }
    
    return render_template('warehouses/inbound_list_with_search.html', 
                         pagination=pagination, 
                         orders=pagination.items,
                         warehouses=warehouses,
                         stats=stats,
                         search_params={
                             'keyword': keyword,
                             'status': status
                         })
