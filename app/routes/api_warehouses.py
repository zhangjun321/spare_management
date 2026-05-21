# -*- coding: utf-8 -*-
"""
仓库管理模块 REST API 路由
为 React 前端提供完整的 CRUD API 接口
F0-2 已迁移：全部 jsonify → ok() / error() / paginated_data()
F0-3 已迁移：业务校验 → raise BusinessError 子类
"""

from flask import Blueprint, request, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app.extensions import db, csrf
from app.models.warehouse import Warehouse
from app.models.inventory_record import InventoryRecord
from app.models.spare_part import SparePart
from app.models.warehouse_location import WarehouseLocation
from app.services.warehouse_service import WarehouseService
from app.utils.decorators import permission_required
from app.utils.helpers import paginate_query
from app.utils.response import ok, error, paginated_data, ResponseCode
from app.utils.exceptions import (
    ParamError, ForbiddenError,
    NotFoundError, ConflictError, BusinessError,
)
from datetime import datetime

api_warehouses_bp = Blueprint('api_warehouses', __name__, url_prefix='/api/warehouses')
csrf.exempt(api_warehouses_bp)


@api_warehouses_bp.route('/', methods=['GET'])
@login_required
@permission_required('warehouse', 'read')
def list_warehouses():
    """获取仓库列表（支持分页、筛选、排序）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '')
    warehouse_type = request.args.get('type', '')
    is_active = request.args.get('is_active')
    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc')

    try:
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

        # 尝试从缓存获取
        if cache_service.redis_client:
            cached_result = cache_service.get(cache_key)
            if cached_result:
                return ok(data=cached_result)

        query = Warehouse.query.options(joinedload(Warehouse.manager))

        if keyword:
            keyword = f'%{keyword}%'
            query = query.filter(
                db.or_(
                    Warehouse.name.like(keyword),
                    Warehouse.code.like(keyword),
                    Warehouse.address.like(keyword)
                )
            )
        if warehouse_type:
            query = query.filter(Warehouse.type == warehouse_type)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter(Warehouse.is_active == is_active_bool)
        if hasattr(Warehouse, sort_by):
            sort_column = getattr(Warehouse, sort_by)
            if order.lower() == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        pagination = paginate_query(query, page=page, per_page=per_page)

        warehouses = []
        for warehouse in pagination.items:
            warehouse_data = warehouse.to_dict()
            warehouse_data['location_count'] = warehouse.locations.count()
            warehouse_data['inventory_count'] = warehouse.inventory_records.count()
            warehouse_data['manager_name'] = warehouse.manager.real_name if warehouse.manager else '未分配'
            warehouses.append(warehouse_data)

        result_data = {
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

        if cache_service.redis_client:
            cache_service.set(cache_key, result_data, timeout=300)

        return paginated_data(items=warehouses, pagination=pagination)
    except BusinessError:
        raise
    except Exception as e:
        current_app.logger.exception('list_warehouses failed')
        raise BusinessError(f'加载仓库列表失败: {e}')


@api_warehouses_bp.route('/<int:id>', methods=['GET'])
@login_required
@permission_required('warehouse', 'read')
def get_warehouse(id):
    """获取仓库详情"""
    warehouse = Warehouse.query.options(
        joinedload(Warehouse.manager),
        joinedload(Warehouse.locations),
        joinedload(Warehouse.zones)
    ).get(id)
    if not warehouse:
        raise NotFoundError(f'仓库不存在 (ID: {id})')

    warehouse_data = warehouse.to_dict()
    stats = WarehouseService.get_warehouse_detail_statistics(warehouse.id)
    warehouse_data['statistics'] = stats
    warehouse_data['locations'] = [loc.to_dict() for loc in warehouse.locations]
    warehouse_data['zones'] = [zone.to_dict() for zone in warehouse.zones]

    return ok(data=warehouse_data)


@api_warehouses_bp.route('/', methods=['POST'])
@login_required
@permission_required('warehouse', 'create')
def create_warehouse():
    """创建仓库"""
    data = request.get_json()

    if not data:
        raise ParamError('请求数据为空')

    required_fields = ['name', 'code']
    for field in required_fields:
        if field not in data:
            raise ParamError(f'缺少必填字段：{field}')

    existing = Warehouse.query.filter_by(code=data['code']).first()
    if existing:
        raise ConflictError(f'仓库编码 {data["code"]} 已存在')

    try:
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
        return ok(data=warehouse.to_dict(), message='仓库创建成功', status_code=201)
    except BusinessError:
        raise
    except Exception as e:
        db.session.rollback()
        raise BusinessError(f'创建失败: {e}')


@api_warehouses_bp.route('/<int:id>', methods=['PUT'])
@login_required
@permission_required('warehouse', 'update')
def update_warehouse(id):
    """更新仓库（全量更新）"""
    warehouse = Warehouse.query.get(id)
    if not warehouse:
        raise NotFoundError(f'仓库不存在 (ID: {id})')

    data = request.get_json()
    if not data:
        raise ParamError('请求数据为空')

    try:
        if 'code' in data and data['code'] != warehouse.code:
            existing = Warehouse.query.filter_by(code=data['code']).first()
            if existing and existing.id != id:
                raise ConflictError(f'仓库编码 {data["code"]} 已存在')

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
        return ok(data=warehouse.to_dict(), message='仓库更新成功')
    except BusinessError:
        raise
    except Exception as e:
        db.session.rollback()
        raise BusinessError(f'更新失败: {e}')


@api_warehouses_bp.route('/<int:id>', methods=['PATCH'])
@login_required
@permission_required('warehouse', 'update')
def patch_warehouse(id):
    """部分更新仓库"""
    warehouse = Warehouse.query.get(id)
    if not warehouse:
        raise NotFoundError(f'仓库不存在 (ID: {id})')

    data = request.get_json()
    if not data:
        raise ParamError('请求数据为空')

    try:
        for key, value in data.items():
            if hasattr(warehouse, key) and key not in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']:
                setattr(warehouse, key, value)

        warehouse.updated_at = datetime.utcnow()
        warehouse.updated_by = current_user.id
        db.session.commit()
        return ok(data=warehouse.to_dict(), message='仓库更新成功')
    except BusinessError:
        raise
    except Exception as e:
        db.session.rollback()
        raise BusinessError(f'更新失败: {e}')


@api_warehouses_bp.route('/<int:id>', methods=['DELETE'])
@login_required
@permission_required('warehouse', 'delete')
def delete_warehouse(id):
    """删除仓库（带前置检查）"""
    warehouse = Warehouse.query.get(id)
    if not warehouse:
        raise NotFoundError(f'仓库不存在 (ID: {id})')

    try:
        location_count = warehouse.locations.count()
        if location_count > 0:
            raise ConflictError(f'仓库下存在 {location_count} 个库位，无法删除')

        inventory_count = warehouse.inventory_records.count()
        if inventory_count > 0:
            raise ConflictError(f'仓库下存在 {inventory_count} 条库存记录，无法删除')

        inbound_count = warehouse.inbound_orders.count()
        if inbound_count > 0:
            raise ConflictError(f'仓库下存在 {inbound_count} 个入库单，无法删除')

        outbound_count = warehouse.outbound_orders.count()
        if outbound_count > 0:
            raise ConflictError(f'仓库下存在 {outbound_count} 个出库单，无法删除')

        db.session.delete(warehouse)
        db.session.commit()
        return ok(message='仓库删除成功')
    except BusinessError:
        raise
    except Exception as e:
        db.session.rollback()
        raise BusinessError(f'删除失败: {e}')


@api_warehouses_bp.route('/batch/delete', methods=['POST'])
@login_required
@permission_required('warehouse', 'delete')
def batch_delete_warehouses():
    """批量删除仓库"""
    data = request.get_json()

    if not data or 'ids' not in data:
        raise ParamError('缺少仓库 ID 列表')

    ids = data['ids']
    if not isinstance(ids, list) or len(ids) == 0:
        raise ParamError('仓库 ID 列表格式错误')

    success_count = 0
    failed = []
    to_delete = []

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

    try:
        for warehouse in to_delete:
            db.session.delete(warehouse)
        db.session.commit()
        success_count = len(to_delete)
    except Exception as e:
        db.session.rollback()
        raise BusinessError(f'批量删除事务失败: {e}')

    return ok(data={
        'success_count': success_count,
        'failed_count': len(failed),
        'failed': failed
    }, message=f'成功删除 {success_count} 个仓库，失败 {len(failed)} 个')


@api_warehouses_bp.route('/batch/export', methods=['GET'])
@login_required
@permission_required('warehouse', 'read')
def batch_export_warehouses():
    """批量导出仓库数据（Excel 格式）"""
    import io
    import xlsxwriter

    ids_str = request.args.get('ids', '')

    if ids_str:
        ids = [int(id.strip()) for id in ids_str.split(',') if id.strip()]
        warehouses = Warehouse.query.filter(Warehouse.id.in_(ids)).all()
    else:
        warehouses = Warehouse.query.filter_by(is_active=True).all()

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('仓库列表')

    headers = [
        '仓库 ID', '仓库编码', '仓库名称', '仓库类型', '仓库地址',
        '容量', '面积', '管理员', '联系电话', '邮箱', '状态', '备注', '创建时间'
    ]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)

    for row, warehouse in enumerate(warehouses, start=1):
        data = [
            warehouse.id, warehouse.code, warehouse.name, warehouse.type,
            warehouse.address or '', warehouse.capacity or '', warehouse.area or '',
            warehouse.manager.real_name if warehouse.manager else '',
            warehouse.phone or '', warehouse.email or '',
            '启用' if warehouse.is_active else '停用',
            warehouse.remark or '',
            warehouse.created_at.strftime('%Y-%m-%d %H:%M:%S') if warehouse.created_at else ''
        ]
        for col, value in enumerate(data):
            worksheet.write(row, col, value)

    worksheet.set_column(0, 0, 10)
    worksheet.set_column(1, 2, 15)
    worksheet.set_column(3, 5, 20)
    worksheet.set_column(6, 9, 15)

    workbook.close()
    output.seek(0)

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
    """批量导入仓库数据（Excel 格式）"""
    import io
    import pandas as pd

    if 'file' not in request.files:
        raise ParamError('未上传文件')

    file = request.files['file']
    if file.filename == '':
        raise ParamError('文件名为空')

    if not file.filename.endswith('.xlsx'):
        raise ParamError('仅支持 Excel (.xlsx) 格式文件')

    try:
        df = pd.read_excel(file)

        required_columns = ['仓库编码', '仓库名称']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ParamError(f'缺少必填列：{", ".join(missing_columns)}')

        success_count = 0
        failed = []

        for index, row in df.iterrows():
            try:
                existing = Warehouse.query.filter_by(code=str(row['仓库编码'])).first()
                if existing:
                    failed.append({'row': index + 2, 'error': f'编码 {row["仓库编码"]} 已存在'})
                    continue

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

                if pd.notna(row.get('管理员')):
                    from app.models.user import User
                    manager = User.query.filter_by(real_name=str(row.get('管理员'))).first()
                    if manager:
                        warehouse.manager_id = manager.id

                db.session.add(warehouse)
                success_count += 1
            except Exception as e:
                failed.append({'row': index + 2, 'error': str(e)})

        db.session.commit()
        return ok(data={
            'success_count': success_count,
            'failed_count': len(failed),
            'failed': failed
        }, message=f'成功导入 {success_count} 个仓库，失败 {len(failed)} 个')
    except BusinessError:
        raise
    except Exception as e:
        db.session.rollback()
        raise BusinessError(f'导入失败: {e}')


@api_warehouses_bp.route('/batch/update', methods=['POST'])
@login_required
@permission_required('warehouse', 'update')
def batch_update_warehouses():
    """批量更新仓库状态"""
    data = request.get_json()

    if not data:
        raise ParamError('请求数据为空')

    ids = data.get('ids', [])
    field = data.get('field', '')
    value = data.get('value')

    if not ids or not isinstance(ids, list):
        raise ParamError('仓库 ID 列表格式错误')

    if not field:
        raise ParamError('缺少字段名')

    allowed_fields = ['is_active', 'type', 'manager_id']
    if field not in allowed_fields:
        raise ParamError(f'不支持批量更新该字段，仅支持：{", ".join(allowed_fields)}')

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
    return ok(data={
        'success_count': success_count,
        'failed_count': len(failed),
        'failed': failed
    }, message=f'成功更新 {success_count} 个仓库，失败 {len(failed)} 个')


@api_warehouses_bp.route('/<int:id>/statistics', methods=['GET'])
@login_required
@permission_required('warehouse', 'read')
def get_warehouse_statistics(id):
    """获取仓库统计信息"""
    warehouse = Warehouse.query.get(id)
    if not warehouse:
        raise NotFoundError(f'仓库不存在 (ID: {id})')
    stats = WarehouseService.get_warehouse_detail_statistics(warehouse.id)
    return ok(data=stats)


@api_warehouses_bp.route('/<int:id>/inventory', methods=['GET'])
@login_required
@permission_required('warehouse', 'read')
def get_warehouse_inventory(id):
    """获取仓库库存列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '')
    category_id = request.args.get('category_id', type=int)
    stock_status = request.args.get('stock_status', '')

    query = InventoryRecord.query.filter_by(warehouse_id=id).options(
        joinedload(InventoryRecord.spare_part).joinedload(SparePart.category),
        joinedload(InventoryRecord.warehouse_location).joinedload(WarehouseLocation.zone)
    )

    if keyword:
        keyword = f'%{keyword}%'
        query = query.join(SparePart).filter(
            db.or_(SparePart.name.like(keyword), SparePart.part_code.like(keyword))
        )
    if category_id:
        query = query.join(SparePart).filter(SparePart.category_id == category_id)
    if stock_status:
        query = query.filter(InventoryRecord.stock_status == stock_status)

    pagination = paginate_query(query, page=page, per_page=per_page)

    inventory_records = []
    for record in pagination.items:
        record_data = record.to_dict()
        if record.spare_part:
            record_data['spare_part'] = {
                'id': record.spare_part.id,
                'name': record.spare_part.name,
                'part_code': record.spare_part.part_code,
                'specification': record.spare_part.specification,
                'category': record.spare_part.category.name if record.spare_part.category else None
            }
        if record.warehouse_location:
            record_data['location'] = {
                'id': record.warehouse_location.id,
                'location_code': record.warehouse_location.location_code,
                'zone_name': record.warehouse_location.zone.name if record.warehouse_location.zone else None
            }
        inventory_records.append(record_data)

    return paginated_data(items=inventory_records, pagination=pagination)


@api_warehouses_bp.route('/<int:id>/locations', methods=['GET'])
@login_required
@permission_required('warehouse', 'read')
def get_warehouse_locations(id):
    """获取仓库库位列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    keyword = request.args.get('keyword', '')
    zone_id = request.args.get('zone_id', type=int)

    query = WarehouseLocation.query.filter_by(warehouse_id=id).options(
        joinedload(WarehouseLocation.zone)
    )
    if keyword:
        keyword = f'%{keyword}%'
        query = query.filter(WarehouseLocation.location_code.like(keyword))
    if zone_id:
        query = query.filter_by(zone_id=zone_id)

    pagination = paginate_query(query, page=page, per_page=per_page)
    locations = [loc.to_dict() for loc in pagination.items]
    return paginated_data(items=locations, pagination=pagination)


@api_warehouses_bp.route('/all', methods=['GET'])
@login_required
def get_all_warehouses():
    """获取所有启用的仓库（用于下拉选择）"""
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    warehouse_list = [
        {'id': w.id, 'name': w.name, 'code': w.code}
        for w in warehouses
    ]
    return ok(data=warehouse_list)


# ==================== 库存记录 API 蓝图 ====================

api_inventory_bp = Blueprint('api_inventory', __name__, url_prefix='/api/inventory')
csrf.exempt(api_inventory_bp)


@api_inventory_bp.route('/records', methods=['GET'])
@login_required
def list_inventory_records():
    """获取全局库存记录列表（支持分页、筛选）"""
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

    return paginated_data(items=items, pagination=pagination)


@api_inventory_bp.route('/warehouses', methods=['GET'])
@login_required
def get_inventory_warehouses():
    """库存页面专用仓库下拉接口"""
    try:
        warehouses = Warehouse.query.filter_by(is_active=True).order_by(Warehouse.id.asc()).all()
        return ok(data=[{'id': w.id, 'name': w.name} for w in warehouses])
    except Exception as e:
        current_app.logger.exception('get_inventory_warehouses failed')
        raise BusinessError(f'加载仓库下拉失败: {e}')


@api_inventory_bp.route('/stats', methods=['GET'])
@login_required
def get_inventory_stats():
    """获取库存统计聚合数据"""
    from sqlalchemy import func, case

    warehouse_id = request.args.get('warehouse_id', type=int)

    try:
        base_q = db.session.query(
            func.count(InventoryRecord.id).label('total'),
            func.sum(case((InventoryRecord.stock_status == 'low', 1), else_=0)).label('low_stock'),
            func.sum(case((InventoryRecord.stock_status == 'out', 1), else_=0)).label('out_of_stock'),
            func.sum(case((InventoryRecord.stock_status == 'normal', 1), else_=0)).label('normal')
        )
        if warehouse_id:
            base_q = base_q.filter(InventoryRecord.warehouse_id == warehouse_id)
        result = base_q.one()
        return ok(data={
            'total': result.total or 0,
            'low_stock': int(result.low_stock or 0),
            'out_of_stock': int(result.out_of_stock or 0),
            'normal': int(result.normal or 0)
        })
    except Exception:
        # 兼容历史库结构降级
        current_app.logger.exception('get_inventory_stats fallback to spare_part')
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
        return ok(data={
            'total': total,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'normal': normal
        })
