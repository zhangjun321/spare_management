# -*- coding: utf-8 -*-
"""
仓库管理模块 REST API 路由
为 React 前端提供完整的 CRUD API 接口
"""

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models.warehouse import Warehouse
from app.models.inventory_record import InventoryRecord
from app.models.spare_part import SparePart
from app.models.warehouse_location import WarehouseLocation
from app.services.warehouse_service import WarehouseService
from app.utils.decorators import permission_required
from app.utils.helpers import paginate_query
from datetime import datetime

api_warehouses_bp = Blueprint('api_warehouses', __name__, url_prefix='/api/warehouses')

# CSRF 豁免配置
from app.extensions import csrf
csrf.exempt(api_warehouses_bp)


@api_warehouses_bp.route('/', methods=['GET'])
@login_required
@permission_required('warehouse', 'read')
def list_warehouses():
    """
    获取仓库列表（支持分页、筛选、排序）
    使用 Redis 缓存优化查询性能
    
    Query Parameters:
        page (int): 页码，默认 1
        per_page (int): 每页数量，默认 20
        keyword (str): 搜索关键词（仓库名称/编码）
        type (str): 仓库类型
        is_active (bool): 是否启用
        sort_by (str): 排序字段，默认 created_at
        order (str): 排序方向 asc/desc，默认 desc
    """
    # 获取参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '')
    warehouse_type = request.args.get('type', '')
    is_active = request.args.get('is_active')
    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc')
    
    try:
        # 生成缓存键
        from app.services.cache_service import cache_service
        cache_key = cache_service.generate_key(
            'warehouse_list',
            current_user.id,
            page=page,
            per_page=per_page,
            keyword=keyword,
            warehouse_type=warehouse_type,
            is_active=is_active,
            sort_by=sort_by,
            order=order
        )
        
        # 尝试从缓存获取（如果 Redis 可用）
        if cache_service.redis_client:
            cached_result = cache_service.get(cache_key)
            if cached_result:
                return jsonify(cached_result)
        
        # 构建查询：仅预加载非 dynamic 关系，避免 500
        query = Warehouse.query.options(joinedload(Warehouse.manager))
        
        # 关键词搜索
        if keyword:
            keyword = f'%{keyword}%'
            query = query.filter(
                db.or_(
                    Warehouse.name.like(keyword),
                    Warehouse.code.like(keyword),
                    Warehouse.address.like(keyword)
                )
            )
        
        # 类型筛选
        if warehouse_type:
            query = query.filter(Warehouse.type == warehouse_type)
        
        # 启用状态筛选
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter(Warehouse.is_active == is_active_bool)
        
        # 排序
        if hasattr(Warehouse, sort_by):
            sort_column = getattr(Warehouse, sort_by)
            if order.lower() == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        
        # 分页
        pagination = paginate_query(query, page=page, per_page=per_page)
        
        warehouses = []
        for warehouse in pagination.items:
            warehouse_data = warehouse.to_dict()
            warehouse_data['location_count'] = warehouse.locations.count()
            warehouse_data['inventory_count'] = warehouse.inventory_records.count()
            warehouse_data['manager_name'] = warehouse.manager.real_name if warehouse.manager else '未分配'
            warehouses.append(warehouse_data)
        
        result = {
            'success': True,
            'data': warehouses,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
        
        # 存入缓存（5 分钟）
        if cache_service.redis_client:
            cache_service.set(cache_key, result, timeout=300)
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.exception('list_warehouses failed')
        return jsonify({'success': False, 'error': f'加载仓库列表失败: {str(e)}'}), 500


@api_warehouses_bp.route('/<int:id>', methods=['GET'])
@login_required
@permission_required('warehouse', 'read')
def get_warehouse(id):
    """
    获取仓库详情
    
    Path Parameters:
        id (int): 仓库 ID
    """
    warehouse = Warehouse.query.options(
        joinedload(Warehouse.manager),
        joinedload(Warehouse.locations),
        joinedload(Warehouse.zones)
    ).get_or_404(id)
    
    warehouse_data = warehouse.to_dict()
    
    # 添加详细统计信息
    stats = WarehouseService.get_warehouse_detail_statistics(warehouse.id)
    warehouse_data['statistics'] = stats
    
    # 添加库位列表
    warehouse_data['locations'] = [loc.to_dict() for loc in warehouse.locations]
    
    # 添加区域列表
    warehouse_data['zones'] = [zone.to_dict() for zone in warehouse.zones]
    
    return jsonify({
        'success': True,
        'data': warehouse_data
    })


@api_warehouses_bp.route('/', methods=['POST'])
@login_required
@permission_required('warehouse', 'create')
def create_warehouse():
    """
    创建仓库
    
    Request Body:
        name (str): 仓库名称 [必填]
        code (str): 仓库编码 [必填]
        type (str): 仓库类型 [可选]
        address (str): 仓库地址 [可选]
        capacity (float): 仓库容量 [可选]
        area (float): 仓库面积 [可选]
        manager_id (int): 仓库管理员 ID [可选]
        phone (str): 联系电话 [可选]
        email (str): 邮箱 [可选]
        is_active (bool): 是否启用 [可选，默认 true]
        remark (str): 备注 [可选]
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': '请求数据为空'
        }), 400
    
    # 验证必填字段
    required_fields = ['name', 'code']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': f'缺少必填字段：{field}'
            }), 400
    
    # 检查编码是否已存在
    existing = Warehouse.query.filter_by(code=data['code']).first()
    if existing:
        return jsonify({
            'success': False,
            'error': f'仓库编码 {data["code"]} 已存在'
        }), 400
    
    try:
        # 创建仓库
        warehouse = Warehouse(
            name=data['name'],
            code=data['code'],
            type=data.get('type', 'general'),
            address=data.get('address'),
            capacity=data.get('capacity'),
            area=data.get('area'),
            manager_id=data.get('manager_id'),
            phone=data.get('phone'),
            email=data.get('email'),
            is_active=data.get('is_active', True),
            remark=data.get('remark'),
            created_by=current_user.id
        )
        
        db.session.add(warehouse)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': warehouse.to_dict(),
            'message': '仓库创建成功'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'创建失败：{str(e)}'
        }), 500


@api_warehouses_bp.route('/<int:id>', methods=['PUT'])
@login_required
@permission_required('warehouse', 'update')
def update_warehouse(id):
    """
    更新仓库（全量更新）
    
    Path Parameters:
        id (int): 仓库 ID
    
    Request Body:
        name (str): 仓库名称
        code (str): 仓库编码
        type (str): 仓库类型
        address (str): 仓库地址
        capacity (float): 仓库容量
        area (float): 仓库面积
        manager_id (int): 仓库管理员 ID
        phone (str): 联系电话
        email (str): 邮箱
        is_active (bool): 是否启用
        remark (str): 备注
    """
    warehouse = Warehouse.query.get_or_404(id)
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': '请求数据为空'
        }), 400
    
    try:
        # 检查编码是否已被其他仓库使用
        if 'code' in data and data['code'] != warehouse.code:
            existing = Warehouse.query.filter_by(code=data['code']).first()
            if existing and existing.id != id:
                return jsonify({
                    'success': False,
                    'error': f'仓库编码 {data["code"]} 已存在'
                }), 400
        
        # 更新字段
        updateable_fields = [
            'name', 'code', 'type', 'address', 'capacity', 'area',
            'manager_id', 'phone', 'email', 'is_active', 'remark'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(warehouse, field, data[field])
        
        warehouse.updated_at = datetime.utcnow()
        warehouse.updated_by = current_user.id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': warehouse.to_dict(),
            'message': '仓库更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'更新失败：{str(e)}'
        }), 500


@api_warehouses_bp.route('/<int:id>', methods=['PATCH'])
@login_required
@permission_required('warehouse', 'update')
def patch_warehouse(id):
    """
    部分更新仓库
    
    与 PUT 的区别：只更新提供的字段
    """
    warehouse = Warehouse.query.get_or_404(id)
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': '请求数据为空'
        }), 400
    
    try:
        # 只更新提供的字段
        for key, value in data.items():
            if hasattr(warehouse, key) and key not in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']:
                setattr(warehouse, key, value)
        
        warehouse.updated_at = datetime.utcnow()
        warehouse.updated_by = current_user.id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': warehouse.to_dict(),
            'message': '仓库更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'更新失败：{str(e)}'
        }), 500


@api_warehouses_bp.route('/<int:id>', methods=['DELETE'])
@login_required
@permission_required('warehouse', 'delete')
def delete_warehouse(id):
    """
    删除仓库
    
    删除前检查：
    1. 是否有库位
    2. 是否有库存记录
    3. 是否有入库单
    4. 是否有出库单
    """
    warehouse = Warehouse.query.get_or_404(id)
    
    try:
        # 检查是否有库位
        location_count = warehouse.locations.count()
        if location_count > 0:
            return jsonify({
                'success': False,
                'error': f'仓库下存在 {location_count} 个库位，无法删除',
                'code': 'HAS_LOCATIONS'
            }), 400
        
        # 检查是否有库存记录
        inventory_count = warehouse.inventory_records.count()
        if inventory_count > 0:
            return jsonify({
                'success': False,
                'error': f'仓库下存在 {inventory_count} 条库存记录，无法删除',
                'code': 'HAS_INVENTORY'
            }), 400
        
        # 检查是否有入库单
        inbound_count = warehouse.inbound_orders.count()
        if inbound_count > 0:
            return jsonify({
                'success': False,
                'error': f'仓库下存在 {inbound_count} 个入库单，无法删除',
                'code': 'HAS_INBOUND'
            }), 400
        
        # 检查是否有出库单
        outbound_count = warehouse.outbound_orders.count()
        if outbound_count > 0:
            return jsonify({
                'success': False,
                'error': f'仓库下存在 {outbound_count} 个出库单，无法删除',
                'code': 'HAS_OUTBOUND'
            }), 400
        
        # 执行删除
        db.session.delete(warehouse)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '仓库删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'删除失败：{str(e)}'
        }), 500


@api_warehouses_bp.route('/batch/delete', methods=['POST'])
@login_required
@permission_required('warehouse', 'delete')
def batch_delete_warehouses():
    """
    批量删除仓库
    
    Request Body:
        ids (list): 仓库 ID 列表
    """
    data = request.get_json()
    
    if not data or 'ids' not in data:
        return jsonify({
            'success': False,
            'error': '缺少仓库 ID 列表'
        }), 400
    
    ids = data['ids']
    if not isinstance(ids, list) or len(ids) == 0:
        return jsonify({
            'success': False,
            'error': '仓库 ID 列表格式错误'
        }), 400
    
    success_count = 0
    failed = []
    to_delete = []

    # 第一阶段：校验所有仓库（只读，不修改 session）
    for warehouse_id in ids:
        warehouse = Warehouse.query.get(warehouse_id)
        if not warehouse:
            failed.append({'id': warehouse_id, 'error': '仓库不存在'})
            continue
        if warehouse.locations.count() > 0:
            failed.append({'id': warehouse_id, 'error': '仓库下有库位'})
            continue
        if warehouse.inventory_records.count() > 0:
            failed.append({'id': warehouse_id, 'error': '仓库下有库存记录'})
            continue
        to_delete.append(warehouse)

    # 第二阶段：在同一事务中删除所有合法仓库
    try:
        for warehouse in to_delete:
            db.session.delete(warehouse)
        db.session.commit()
        success_count = len(to_delete)
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'批量删除事务失败：{str(e)}'
        }), 500

    return jsonify({
        'success': True,
        'data': {
            'success_count': success_count,
            'failed_count': len(failed),
            'failed': failed
        },
        'message': f'成功删除 {success_count} 个仓库，失败 {len(failed)} 个'
    })


@api_warehouses_bp.route('/batch/export', methods=['GET'])
@login_required
@permission_required('warehouse', 'read')
def batch_export_warehouses():
    """
    批量导出仓库数据（Excel 格式）
    
    Query Parameters:
        ids (str): 仓库 ID 列表，逗号分隔（可选，不传则导出所有）
    """
    import io
    import xlsxwriter
    
    # 获取要导出的 ID 列表
    ids_str = request.args.get('ids', '')
    
    # 查询仓库数据
    if ids_str:
        ids = [int(id.strip()) for id in ids_str.split(',') if id.strip()]
        warehouses = Warehouse.query.filter(Warehouse.id.in_(ids)).all()
    else:
        warehouses = Warehouse.query.filter_by(is_active=True).all()
    
    # 创建 Excel 文件
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('仓库列表')
    
    # 定义表头
    headers = [
        '仓库 ID', '仓库编码', '仓库名称', '仓库类型', '仓库地址',
        '容量', '面积', '管理员', '联系电话', '邮箱', '状态', '备注', '创建时间'
    ]
    
    # 写入表头
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    # 写入数据
    for row, warehouse in enumerate(warehouses, start=1):
        data = [
            warehouse.id,
            warehouse.code,
            warehouse.name,
            warehouse.type,
            warehouse.address or '',
            warehouse.capacity or '',
            warehouse.area or '',
            warehouse.manager.real_name if warehouse.manager else '',
            warehouse.phone or '',
            warehouse.email or '',
            '启用' if warehouse.is_active else '停用',
            warehouse.remark or '',
            warehouse.created_at.strftime('%Y-%m-%d %H:%M:%S') if warehouse.created_at else ''
        ]
        for col, value in enumerate(data):
            worksheet.write(row, col, value)
    
    # 设置列宽
    worksheet.set_column(0, 0, 10)  # ID
    worksheet.set_column(1, 2, 15)  # 编码、名称
    worksheet.set_column(3, 5, 20)  # 类型、地址、容量
    worksheet.set_column(6, 9, 15)  # 面积、管理员、电话、邮箱
    
    workbook.close()
    output.seek(0)
    
    # 返回文件
    from flask import send_file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'仓库列表_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )


@api_warehouses_bp.route('/batch/import', methods=['POST'])
@login_required
@permission_required('warehouse', 'create')
def batch_import_warehouses():
    """
    批量导入仓库数据（Excel 格式）
    
    Form Data:
        file: Excel 文件
    """
    import io
    import xlsxwriter
    import pandas as pd
    
    # 检查文件
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': '未上传文件'
        }), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': '文件名为空'
        }), 400
    
    if not file.filename.endswith('.xlsx'):
        return jsonify({
            'success': False,
            'error': '仅支持 Excel (.xlsx) 格式文件'
        }), 400
    
    try:
        # 读取 Excel 文件
        df = pd.read_excel(file)
        
        # 验证必填列
        required_columns = ['仓库编码', '仓库名称']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'success': False,
                'error': f'缺少必填列：{", ".join(missing_columns)}'
            }), 400
        
        # 导入数据
        success_count = 0
        failed = []
        
        for index, row in df.iterrows():
            try:
                # 检查编码是否已存在
                existing = Warehouse.query.filter_by(code=str(row['仓库编码'])).first()
                if existing:
                    failed.append({
                        'row': index + 2,
                        'error': f'编码 {row["仓库编码"]} 已存在'
                    })
                    continue
                
                # 创建仓库
                warehouse = Warehouse(
                    code=str(row['仓库编码']),
                    name=str(row.get('仓库名称', '')),
                    type=str(row.get('仓库类型', 'general')),
                    address=str(row.get('仓库地址', '')),
                    capacity=row.get('容量'),
                    area=row.get('面积'),
                    phone=str(row.get('联系电话', '')),
                    email=str(row.get('邮箱', '')),
                    remark=str(row.get('备注', '')),
                    is_active=row.get('状态', '启用') == '启用',
                    created_by=current_user.id
                )
                
                # 处理仓库管理员
                if pd.notna(row.get('管理员')):
                    manager = User.query.filter_by(real_name=str(row.get('管理员'))).first()
                    if manager:
                        warehouse.manager_id = manager.id
                
                db.session.add(warehouse)
                success_count += 1
                
            except Exception as e:
                failed.append({
                    'row': index + 2,
                    'error': str(e)
                })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'success_count': success_count,
                'failed_count': len(failed),
                'failed': failed
            },
            'message': f'成功导入 {success_count} 个仓库，失败 {len(failed)} 个'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'导入失败：{str(e)}'
        }), 500


@api_warehouses_bp.route('/batch/update', methods=['POST'])
@login_required
@permission_required('warehouse', 'update')
def batch_update_warehouses():
    """
    批量更新仓库状态
    
    Request Body:
        ids (list): 仓库 ID 列表
        field (str): 要更新的字段名
        value: 新的值
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': '请求数据为空'
        }), 400
    
    ids = data.get('ids', [])
    field = data.get('field', '')
    value = data.get('value')
    
    if not ids or not isinstance(ids, list):
        return jsonify({
            'success': False,
            'error': '仓库 ID 列表格式错误'
        }), 400
    
    if not field:
        return jsonify({
            'success': False,
            'error': '缺少字段名'
        }), 400
    
    # 允许批量更新的字段
    allowed_fields = ['is_active', 'type', 'manager_id']
    if field not in allowed_fields:
        return jsonify({
            'success': False,
            'error': f'不支持批量更新该字段，仅支持：{", ".join(allowed_fields)}'
        }), 400
    
    success_count = 0
    failed = []
    
    for warehouse_id in ids:
        warehouse = Warehouse.query.get(warehouse_id)
        if not warehouse:
            failed.append({'id': warehouse_id, 'error': '仓库不存在'})
            continue
        
        try:
            setattr(warehouse, field, value)
            warehouse.updated_at = datetime.utcnow()
            warehouse.updated_by = current_user.id
            success_count += 1
            
        except Exception as e:
            failed.append({'id': warehouse_id, 'error': str(e)})
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'success_count': success_count,
            'failed_count': len(failed),
            'failed': failed
        },
        'message': f'成功更新 {success_count} 个仓库，失败 {len(failed)} 个'
    })


@api_warehouses_bp.route('/<int:id>/statistics', methods=['GET'])
@login_required
@permission_required('warehouse', 'read')
def get_warehouse_statistics(id):
    """
    获取仓库统计信息
    
    Path Parameters:
        id (int): 仓库 ID
    """
    warehouse = Warehouse.query.get_or_404(id)
    
    stats = WarehouseService.get_warehouse_detail_statistics(warehouse.id)
    
    return jsonify({
        'success': True,
        'data': stats
    })


@api_warehouses_bp.route('/<int:id>/inventory', methods=['GET'])
@login_required
@permission_required('warehouse', 'read')
def get_warehouse_inventory(id):
    """
    获取仓库库存列表（库存联动展示）
    
    Path Parameters:
        id (int): 仓库 ID
    
    Query Parameters:
        page (int): 页码
        per_page (int): 每页数量
        keyword (str): 搜索关键词（备件名称/编码）
        category_id (int): 分类 ID
        stock_status (str): 库存状态
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '')
    category_id = request.args.get('category_id', type=int)
    stock_status = request.args.get('stock_status', '')
    
    # 查询该仓库的所有库存记录 - 使用 joinedload 预加载所有关联数据
    query = InventoryRecord.query.filter_by(warehouse_id=id).options(
        joinedload(InventoryRecord.spare_part).joinedload(SparePart.category),
        joinedload(InventoryRecord.warehouse_location).joinedload(WarehouseLocation.zone)
    )
    
    # 关键词搜索
    if keyword:
        keyword = f'%{keyword}%'
        query = query.join(SparePart).filter(
            db.or_(
                SparePart.name.like(keyword),
                SparePart.part_code.like(keyword)
            )
        )
    
    # 分类筛选
    if category_id:
        query = query.join(SparePart).filter(SparePart.category_id == category_id)
    
    # 库存状态筛选
    if stock_status:
        query = query.filter(InventoryRecord.stock_status == stock_status)
    
    # 分页
    pagination = paginate_query(query, page=page, per_page=per_page)
    
    # 转换为 JSON
    inventory_records = []
    for record in pagination.items:
        record_data = record.to_dict()
        
        # 添加备件信息
        if record.spare_part:
            record_data['spare_part'] = {
                'id': record.spare_part.id,
                'name': record.spare_part.name,
                'part_code': record.spare_part.part_code,
                'specification': record.spare_part.specification,
                'category': record.spare_part.category.name if record.spare_part.category else None
            }
        
        # 添加库位信息
        if record.warehouse_location:
            record_data['location'] = {
                'id': record.warehouse_location.id,
                'location_code': record.warehouse_location.location_code,
                'zone_name': record.warehouse_location.zone.name if record.warehouse_location.zone else None
            }
        
        inventory_records.append(record_data)
    
    return jsonify({
        'success': True,
        'data': inventory_records,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@api_warehouses_bp.route('/<int:id>/locations', methods=['GET'])
@login_required
@permission_required('warehouse', 'read')
def get_warehouse_locations(id):
    """
    获取仓库库位列表
    
    Path Parameters:
        id (int): 仓库 ID
    
    Query Parameters:
        page (int): 页码
        per_page (int): 每页数量
        keyword (str): 搜索关键词（库位编码）
        zone_id (int): 区域 ID
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '')
    zone_id = request.args.get('zone_id', type=int)
    
    # 构建查询 - 预加载区域信息，避免 N+1 查询
    query = WarehouseLocation.query.filter_by(warehouse_id=id).options(
        joinedload(WarehouseLocation.zone)
    )
    
    # 关键词搜索
    if keyword:
        keyword = f'%{keyword}%'
        query = query.filter(WarehouseLocation.location_code.like(keyword))
    
    # 区域筛选
    if zone_id:
        query = query.filter_by(zone_id=zone_id)
    
    # 分页
    pagination = paginate_query(query, page=page, per_page=per_page)
    
    locations = [loc.to_dict() for loc in pagination.items]
    
    return jsonify({
        'success': True,
        'data': locations,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@api_warehouses_bp.route('/all', methods=['GET'])
@login_required
def get_all_warehouses():
    """
    获取所有启用的仓库（用于下拉选择）
    只查询必要的字段，提高性能
    """
    # 只查询需要的字段，避免加载所有列
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    
    # 使用列表推导式高效构建结果
    warehouse_list = [
        {
            'id': warehouse.id,
            'name': warehouse.name,
            'code': warehouse.code
        }
        for warehouse in warehouses
    ]
    
    return jsonify({
        'success': True,
        'data': warehouse_list
    })


# ==================== 库存记录 API 蓝图 ====================

from app.extensions import csrf as _csrf

api_inventory_bp = Blueprint('api_inventory', __name__, url_prefix='/api/inventory')
_csrf.exempt(api_inventory_bp)


@api_inventory_bp.route('/records', methods=['GET'])
@login_required
def list_inventory_records():
    """
    获取全局库存记录列表（支持分页、筛选）

    Query Parameters:
        page (int): 页码，默认 1
        per_page (int): 每页数量，默认 20
        warehouse_id (int): 仓库 ID 筛选
        stock_status (str): 库存状态 (low/out/normal)
        has_stock (str): 是否有库存 ('1'=有库存, '0'=无库存)
        keyword (str): 备件名称/编码关键词
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 200)
    warehouse_id = request.args.get('warehouse_id', type=int)
    stock_status = request.args.get('stock_status', '')
    has_stock = request.args.get('has_stock', '')
    keyword = request.args.get('keyword', '')

    query = InventoryRecord.query.options(
        joinedload(InventoryRecord.spare_part),
        joinedload(InventoryRecord.warehouse)
    )

    if warehouse_id:
        query = query.filter(InventoryRecord.warehouse_id == warehouse_id)

    if stock_status:
        query = query.filter(InventoryRecord.stock_status == stock_status)

    if has_stock == '1':
        query = query.filter(InventoryRecord.quantity > 0)
    elif has_stock == '0':
        query = query.filter(InventoryRecord.quantity <= 0)

    if keyword:
        kw = f'%{keyword}%'
        query = query.join(SparePart).filter(
            db.or_(SparePart.name.like(kw), SparePart.part_code.like(kw))
        )

    pagination = paginate_query(query, page=page, per_page=per_page)

    items = []
    for record in pagination.items:
        data = record.to_dict()
        if record.spare_part:
            data['spare_part_name'] = record.spare_part.name
            data['spare_part_code'] = record.spare_part.part_code
        if record.warehouse:
            data['warehouse_name'] = record.warehouse.name
        items.append(data)

    return jsonify({
        'success': True,
        'data': {
            'items': items,
            'total': pagination.total
        },
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@api_inventory_bp.route('/warehouses', methods=['GET'])
@login_required
def get_inventory_warehouses():
    """库存页面专用仓库下拉接口（轻量稳定）"""
    try:
        warehouses = Warehouse.query.filter_by(is_active=True).order_by(Warehouse.id.asc()).all()
        return jsonify({
            'success': True,
            'data': [{'id': w.id, 'name': w.name} for w in warehouses]
        })
    except Exception as e:
        current_app.logger.exception('get_inventory_warehouses failed')
        return jsonify({'success': False, 'error': f'加载仓库下拉失败: {str(e)}'}), 500


@api_inventory_bp.route('/stats', methods=['GET'])
@login_required
def get_inventory_stats():
    """
    获取库存统计聚合数据（单次请求代替前端3次冗余查询）

    Returns:
        {
            total: 总条数,
            low_stock: 低库存数,
            out_of_stock: 缺货数,
            normal: 正常数
        }
    """
    from sqlalchemy import func, case
    from app.models.spare_part import SparePart

    warehouse_id = request.args.get('warehouse_id', type=int)

    try:
        base_q = db.session.query(
            func.count(InventoryRecord.id).label('total'),
            func.sum(
                case((InventoryRecord.stock_status == 'low', 1), else_=0)
            ).label('low_stock'),
            func.sum(
                case((InventoryRecord.stock_status == 'out', 1), else_=0)
            ).label('out_of_stock'),
            func.sum(
                case((InventoryRecord.stock_status == 'normal', 1), else_=0)
            ).label('normal')
        )

        if warehouse_id:
            base_q = base_q.filter(InventoryRecord.warehouse_id == warehouse_id)

        result = base_q.one()

        return jsonify({
            'success': True,
            'data': {
                'total': result.total or 0,
                'low_stock': int(result.low_stock or 0),
                'out_of_stock': int(result.out_of_stock or 0),
                'normal': int(result.normal or 0)
            }
        })
    except Exception:
        # 兼容历史库结构：InventoryRecord 字段缺失时，降级使用 SparePart 统计，避免前端 500
        current_app.logger.exception('get_inventory_stats failed on inventory_record, fallback to spare_part')

        sp_query = SparePart.query.filter(SparePart.is_active == True)
        if warehouse_id:
            sp_query = sp_query.filter(SparePart.warehouse_id == warehouse_id)

        total = sp_query.count()
        low_stock = sp_query.filter(
            SparePart.current_stock > 0,
            SparePart.current_stock <= SparePart.min_stock
        ).count()
        out_of_stock = sp_query.filter(SparePart.current_stock <= 0).count()
        normal = max(total - low_stock - out_of_stock, 0)

        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'low_stock': low_stock,
                'out_of_stock': out_of_stock,
                'normal': normal
            }
        })
