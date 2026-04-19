"""
通用列表搜索 API
为所有列表提供统一的搜索接口
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.extensions import db

list_api = Blueprint('list_api', __name__, url_prefix='/api/list')


@list_api.route('/<model_name>')
@login_required
def get_list(model_name):
    """
    通用列表接口
    支持：warehouses, inbound, outbound, equipment, maintenance, purchase, transactions 等
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    
    # 映射模型名称到实际模型类
    from app.models.warehouse import Warehouse
    from app.models.inbound_outbound import InboundOrder, OutboundOrder
    from app.models.equipment import Equipment
    from app.models.maintenance import MaintenanceRecord
    from app.models.purchase import PurchaseOrder
    from app.models.transaction import Transaction
    
    model_map = {
        'warehouses': Warehouse,
        'inbound': InboundOrder,
        'outbound': OutboundOrder,
        'equipment': Equipment,
        'maintenance': MaintenanceRecord,
        'purchase': PurchaseOrder,
        'transactions': Transaction
    }
    
    if model_name not in model_map:
        return jsonify({
            'code': 400,
            'message': f'不支持的模型：{model_name}'
        }), 400
    
    model = model_map[model_name]
    
    # 构建查询
    query = model.query
    
    # 关键词搜索（动态字段）
    if keyword:
        # 获取模型的所有 String 和 Text 类型字段
        search_fields = []
        for column in model.__table__.columns:
            if isinstance(column.type, (db.String, db.Text)):
                search_fields.append(column)
        
        # 构建 OR 条件
        conditions = [field.like(f'%{keyword}%') for field in search_fields]
        if conditions:
            query = query.filter(db.or_(*conditions))
    
    # 分页
    pagination = query.order_by(model.id.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 格式化结果
    data_list = []
    for item in pagination.items:
        item_data = {
            'id': item.id
        }
        # 添加所有列
        for column in model.__table__.columns:
            value = getattr(item, column.name)
            if isinstance(value, (db.DateTime,)):
                item_data[column.name] = value.strftime('%Y-%m-%d %H:%M:%S') if value else None
            else:
                item_data[column.name] = value
        data_list.append(item_data)
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'list': data_list,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })
