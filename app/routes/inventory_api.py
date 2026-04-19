"""
库存管理 API
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from app.models.warehouse_v3.inventory import InventoryV3 as Inventory
from app.models.warehouse import Warehouse
from app.models.spare_part import SparePart
from app.extensions import db

inventory_api = Blueprint('inventory_api', __name__, url_prefix='/api/inventory')


@inventory_api.route('/list')
@login_required
def get_inventory_list():
    """
    获取库存列表（支持搜索和分页）
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    warehouse_id = request.args.get('warehouse_id', '').strip()
    low_stock = request.args.get('low_stock', '').strip()
    
    # 构建查询
    query = Inventory.query
    
    # 关键词搜索
    if keyword:
        # 关联查询备件和仓库
        query = query.join(SparePart, Inventory.spare_part_id == SparePart.id)\
                    .join(Warehouse, Inventory.warehouse_id == Warehouse.id)\
                    .filter(
            db.or_(
                SparePart.name.like(f'%{keyword}%'),
                SparePart.code.like(f'%{keyword}%'),
                Warehouse.name.like(f'%{keyword}%'),
                Warehouse.code.like(f'%{keyword}%')
            )
        )
    
    # 仓库筛选
    if warehouse_id:
        query = query.filter(Inventory.warehouse_id == warehouse_id)
    
    # 低库存筛选
    if low_stock == 'true':
        query = query.filter(Inventory.quantity <= Inventory.min_quantity)
    
    # 分页
    pagination = query.order_by(Inventory.id.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 格式化结果
    inventory_list = []
    for inv in pagination.items:
        inventory_list.append({
            'id': inv.id,
            'warehouse_id': inv.warehouse_id,
            'warehouse_name': inv.warehouse.name if inv.warehouse else None,
            'warehouse_code': inv.warehouse.code if inv.warehouse else None,
            'spare_part_id': inv.spare_part_id,
            'spare_part_name': inv.spare_part.name if inv.spare_part else None,
            'spare_part_code': inv.spare_part.code if inv.spare_part else None,
            'spare_part_model': inv.spare_part.model if inv.spare_part else None,
            'quantity': inv.quantity,
            'min_quantity': inv.min_quantity,
            'max_quantity': inv.max_quantity,
            'unit': inv.spare_part.unit if inv.spare_part else None,
            'unit_price': float(inv.unit_price) if inv.unit_price else 0,
            'total_value': float(inv.quantity * inv.unit_price) if inv.unit_price else 0,
            'stock_status': 'low' if inv.quantity <= inv.min_quantity else ('sufficient' if inv.quantity >= inv.max_quantity else 'normal'),
            'location': inv.location,
            'updated_at': inv.updated_at.strftime('%Y-%m-%d %H:%M:%S') if inv.updated_at else None
        })
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'list': inventory_list,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })


@inventory_api.route('/')
@login_required
def list_page():
    """
    库存列表页面（带搜索）
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    warehouse_id = request.args.get('warehouse_id', '').strip()
    low_stock = request.args.get('low_stock', '').strip()
    
    # 构建查询
    query = Inventory.query
    
    # 关键词搜索
    if keyword:
        query = query.join(SparePart, Inventory.spare_part_id == SparePart.id)\
                    .join(Warehouse, Inventory.warehouse_id == Warehouse.id)\
                    .filter(
            db.or_(
                SparePart.name.like(f'%{keyword}%'),
                SparePart.code.like(f'%{keyword}%'),
                Warehouse.name.like(f'%{keyword}%')
            )
        )
    
    # 仓库筛选
    if warehouse_id:
        query = query.filter(Inventory.warehouse_id == warehouse_id)
    
    # 低库存筛选
    if low_stock == 'true':
        query = query.filter(Inventory.quantity <= Inventory.min_quantity)
    
    # 分页
    pagination = query.order_by(Inventory.id.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 获取所有仓库用于筛选
    warehouses = Warehouse.query.filter(Warehouse.is_active == True).all()
    
    # 统计
    total_inventory = Inventory.query.count()
    low_stock_count = Inventory.query.filter(Inventory.quantity <= Inventory.min_quantity).count()
    sufficient_stock_count = Inventory.query.filter(Inventory.quantity >= Inventory.max_quantity).count()
    normal_stock_count = total_inventory - low_stock_count - sufficient_stock_count
    
    stats = {
        'total': total_inventory,
        'low_stock': low_stock_count,
        'sufficient': sufficient_stock_count,
        'normal': normal_stock_count
    }
    
    return render_template('warehouses/inventory_list_with_search.html', 
                         pagination=pagination, 
                         inventory_list=pagination.items,
                         warehouses=warehouses,
                         stats=stats,
                         search_params={
                             'keyword': keyword,
                             'warehouse_id': warehouse_id,
                             'low_stock': low_stock
                         })
