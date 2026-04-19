"""
出库单管理 API
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from app.models.inbound_outbound import OutboundOrder
from app.models.warehouse import Warehouse
from app.extensions import db

outbound_api = Blueprint('outbound_api', __name__, url_prefix='/api/outbound')


@outbound_api.route('/list')
@login_required
def get_outbound_list():
    """
    获取出库单列表（支持搜索和分页）
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '').strip()
    
    # 构建查询
    query = OutboundOrder.query
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            db.or_(
                OutboundOrder.order_code.like(f'%{keyword}%'),
                OutboundOrder.batch_number.like(f'%{keyword}%'),
                OutboundOrder.remark.like(f'%{keyword}%')
            )
        )
    
    # 状态筛选
    if status:
        query = query.filter(OutboundOrder.status == status)
    
    # 分页
    pagination = query.order_by(OutboundOrder.id.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 格式化结果
    outbound_list = []
    for order in pagination.items:
        outbound_list.append({
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
            'recipient': order.recipient,
            'creator_name': order.creator.real_name if order.creator else None,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else None,
            'completed_at': order.completed_at.strftime('%Y-%m-%d %H:%M:%S') if order.completed_at else None
        })
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'list': outbound_list,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })


@outbound_api.route('/')
@login_required
def list_page():
    """
    出库单列表页面（带搜索）
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '').strip()
    
    # 构建查询
    query = OutboundOrder.query
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            db.or_(
                OutboundOrder.order_code.like(f'%{keyword}%'),
                OutboundOrder.batch_number.like(f'%{keyword}%'),
                OutboundOrder.remark.like(f'%{keyword}%')
            )
        )
    
    # 状态筛选
    if status:
        query = query.filter(OutboundOrder.status == status)
    
    # 分页
    pagination = query.order_by(OutboundOrder.id.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 获取所有仓库用于筛选
    warehouses = Warehouse.query.filter(Warehouse.is_active == True).all()
    
    # 统计
    stats = {
        'total': OutboundOrder.query.count(),
        'pending': OutboundOrder.query.filter(OutboundOrder.status == 'pending').count(),
        'completed': OutboundOrder.query.filter(OutboundOrder.status == 'completed').count(),
        'cancelled': OutboundOrder.query.filter(OutboundOrder.status == 'cancelled').count()
    }
    
    return render_template('warehouses/outbound_list_with_search.html', 
                         pagination=pagination, 
                         orders=pagination.items,
                         warehouses=warehouses,
                         stats=stats,
                         search_params={
                             'keyword': keyword,
                             'status': status
                         })
