# -*- coding: utf-8 -*-
"""
备件管理 REST API 蓝图（供 React 前端调用）
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app.extensions import db, csrf
from app.models.spare_part import SparePart
from app.models.category import Category
from app.models.supplier import Supplier
from app.models.warehouse import Warehouse

api_spare_parts_bp = Blueprint('api_spare_parts', __name__, url_prefix='/api/spare-parts')
csrf.exempt(api_spare_parts_bp)


def _serialize_part(part):
    """将 SparePart 对象序列化为 dict"""
    return {
        'id': part.id,
        'part_code': part.part_code,
        'name': part.name,
        'specification': part.specification,
        'category_id': part.category_id,
        'category_name': part.category.name if part.category else None,
        'supplier_id': part.supplier_id,
        'supplier_name': part.supplier.name if part.supplier else None,
        'warehouse_id': part.warehouse_id,
        'warehouse_name': part.warehouse.name if part.warehouse else None,
        'location_id': part.location_id,
        'location_code': part.warehouse_location.location_code if part.warehouse_location else None,
        'current_stock': part.current_stock,
        'stock_status': part.stock_status,
        'min_stock': part.min_stock,
        'max_stock': part.max_stock,
        'unit': part.unit,
        'unit_price': float(part.unit_price) if part.unit_price else None,
        'location': part.location,
        'brand': part.brand,
        'barcode': part.barcode,
        'safety_stock': part.safety_stock,
        'reorder_point': part.reorder_point,
        'last_purchase_price': float(part.last_purchase_price) if part.last_purchase_price else None,
        'currency': part.currency,
        'warranty_period': part.warranty_period,
        'last_purchase_date': part.last_purchase_date.strftime('%Y-%m-%d') if part.last_purchase_date else None,
        'datasheet_url': part.datasheet_url,
        'image_url': part.image_url,
        'thumbnail_url': part.thumbnail_url,
        'side_image_url': part.side_image_url,
        'detail_image_url': part.detail_image_url,
        'circuit_image_url': part.circuit_image_url,
        'perspective_image_url': part.perspective_image_url,
        'remark': part.remark,
        'is_active': part.is_active,
        'technical_params': part.technical_params,
        'created_at': part.created_at.strftime('%Y-%m-%d %H:%M:%S') if part.created_at else None,
        'updated_at': part.updated_at.strftime('%Y-%m-%d %H:%M:%S') if part.updated_at else None,
    }


# ──────────────────────────────────────────────
# 备件列表
# ──────────────────────────────────────────────
@api_spare_parts_bp.route('/', methods=['GET'])
@login_required
def list_parts():
    """备件列表，支持分页、搜索、筛选"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    if per_page not in [10, 20, 50]:
        per_page = 20

    keyword = request.args.get('keyword', '').strip()
    category_id = request.args.get('category_id', 0, type=int)
    supplier_id = request.args.get('supplier_id', 0, type=int)
    stock_status = request.args.get('stock_status', '')
    is_active = request.args.get('is_active', '')

    query = SparePart.query.options(
        joinedload(SparePart.category),
        joinedload(SparePart.supplier),
        joinedload(SparePart.warehouse),
    )

    if keyword:
        kw = f'%{keyword}%'
        query = query.filter(
            db.or_(
                SparePart.part_code.like(kw),
                SparePart.name.like(kw),
                SparePart.specification.like(kw),
            )
        )
    if category_id:
        query = query.filter(SparePart.category_id == category_id)
    if supplier_id:
        query = query.filter(SparePart.supplier_id == supplier_id)
    if stock_status:
        query = query.filter(SparePart.stock_status == stock_status)
    if is_active == '1':
        query = query.filter(SparePart.is_active == True)
    elif is_active == '0':
        query = query.filter(SparePart.is_active == False)

    pagination = query.order_by(SparePart.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'success': True,
        'data': [_serialize_part(p) for p in pagination.items],
        'pagination': {
            'page': pagination.page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
        }
    })


# ──────────────────────────────────────────────
# 筛选选项（分类/供应商/仓库下拉数据）
# ──────────────────────────────────────────────
@api_spare_parts_bp.route('/options', methods=['GET'])
@login_required
def get_options():
    """获取分类、供应商、仓库选项"""
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    warehouses = Warehouse.query.filter_by(is_active=True).order_by(Warehouse.name).all()

    return jsonify({
        'success': True,
        'categories': [{'id': c.id, 'name': c.name} for c in categories],
        'suppliers': [{'id': s.id, 'name': s.name} for s in suppliers],
        'warehouses': [{'id': w.id, 'name': w.name} for w in warehouses],
    })


# ──────────────────────────────────────────────
# 备件详情
# ──────────────────────────────────────────────
@api_spare_parts_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_part(id):
    part = SparePart.query.options(
        joinedload(SparePart.category),
        joinedload(SparePart.supplier),
        joinedload(SparePart.warehouse),
        joinedload(SparePart.warehouse_location),
    ).get_or_404(id)
    return jsonify({'success': True, 'data': _serialize_part(part)})


# ──────────────────────────────────────────────
# 新增备件
# ──────────────────────────────────────────────
@api_spare_parts_bp.route('/', methods=['POST'])
@login_required
def create_part():
    if not current_user.has_permission('spare_part', 'create'):
        return jsonify({'success': False, 'error': '无创建权限'}), 403

    data = request.get_json() or {}

    # 检查备件代码唯一
    if SparePart.query.filter_by(part_code=data.get('part_code')).first():
        return jsonify({'success': False, 'error': '备件代码已存在'}), 400

    part = SparePart(
        part_code=data.get('part_code'),
        name=data.get('name'),
        specification=data.get('specification'),
        category_id=data.get('category_id') or None,
        supplier_id=data.get('supplier_id') or None,
        warehouse_id=data.get('warehouse_id') or None,
        location_id=data.get('location_id') or None,
        current_stock=data.get('current_stock', 0),
        min_stock=data.get('min_stock', 0),
        max_stock=data.get('max_stock'),
        unit=data.get('unit'),
        unit_price=data.get('unit_price'),
        location=data.get('location'),
        brand=data.get('brand'),
        barcode=data.get('barcode') or None,
        safety_stock=data.get('safety_stock', 0),
        reorder_point=data.get('reorder_point'),
        last_purchase_price=data.get('last_purchase_price'),
        currency=data.get('currency', 'CNY'),
        warranty_period=data.get('warranty_period'),
        last_purchase_date=_parse_date(data.get('last_purchase_date')),
        datasheet_url=data.get('datasheet_url'),
        image_url=data.get('image_url'),
        thumbnail_url=data.get('thumbnail_url'),
        side_image_url=data.get('side_image_url'),
        detail_image_url=data.get('detail_image_url'),
        circuit_image_url=data.get('circuit_image_url'),
        perspective_image_url=data.get('perspective_image_url'),
        remark=data.get('remark'),
        is_active=data.get('is_active', True),
        created_by=current_user.id,
    )
    part.update_stock_status()
    db.session.add(part)
    db.session.commit()
    return jsonify({'success': True, 'data': _serialize_part(part)}), 201


# ──────────────────────────────────────────────
# 更新备件
# ──────────────────────────────────────────────
@api_spare_parts_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_part(id):
    if not current_user.has_permission('spare_part', 'update'):
        return jsonify({'success': False, 'error': '无编辑权限'}), 403

    part = SparePart.query.get_or_404(id)
    data = request.get_json() or {}

    # 检查备件代码唯一（排除自身）
    code = data.get('part_code')
    if code and code != part.part_code:
        if SparePart.query.filter(SparePart.part_code == code, SparePart.id != id).first():
            return jsonify({'success': False, 'error': '备件代码已存在'}), 400

    fields = [
        'part_code', 'name', 'specification', 'category_id', 'supplier_id',
        'warehouse_id', 'location_id', 'current_stock', 'min_stock', 'max_stock',
        'unit', 'unit_price', 'location', 'brand', 'safety_stock', 'reorder_point',
        'last_purchase_price', 'currency', 'warranty_period', 'datasheet_url',
        'image_url', 'thumbnail_url', 'side_image_url', 'detail_image_url',
        'circuit_image_url', 'perspective_image_url', 'remark', 'is_active',
        'technical_params',
    ]
    for f in fields:
        if f in data:
            setattr(part, f, data[f] or None if f in ('category_id', 'supplier_id', 'warehouse_id', 'location_id', 'barcode') else data[f])

    if 'barcode' in data:
        part.barcode = data['barcode'] or None
    if 'last_purchase_date' in data:
        part.last_purchase_date = _parse_date(data['last_purchase_date'])

    part.update_stock_status()
    db.session.commit()
    return jsonify({'success': True, 'data': _serialize_part(part)})


# ──────────────────────────────────────────────
# 删除备件
# ──────────────────────────────────────────────
@api_spare_parts_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_part(id):
    if not current_user.has_permission('spare_part', 'delete'):
        return jsonify({'success': False, 'error': '无删除权限'}), 403

    part = SparePart.query.get_or_404(id)
    db.session.delete(part)
    db.session.commit()
    return jsonify({'success': True, 'message': '删除成功'})


# ──────────────────────────────────────────────
# 切换启用状态
# ──────────────────────────────────────────────
@api_spare_parts_bp.route('/<int:id>/toggle-status', methods=['POST'])
@login_required
def toggle_status(id):
    if not current_user.has_permission('spare_part', 'update'):
        return jsonify({'success': False, 'error': '无编辑权限'}), 403

    part = SparePart.query.get_or_404(id)
    part.is_active = not part.is_active
    db.session.commit()
    return jsonify({'success': True, 'is_active': part.is_active})


# ──────────────────────────────────────────────
# 检查备件代码唯一
# ──────────────────────────────────────────────
@api_spare_parts_bp.route('/check-code', methods=['POST'])
@login_required
def check_code():
    data = request.get_json() or {}
    part_code = data.get('part_code', '')
    exclude_id = data.get('exclude_id')
    query = SparePart.query.filter_by(part_code=part_code)
    if exclude_id:
        query = query.filter(SparePart.id != exclude_id)
    return jsonify({'exists': query.first() is not None})


# ──────────────────────────────────────────────
# 条形码搜索
# ──────────────────────────────────────────────
@api_spare_parts_bp.route('/search-by-barcode', methods=['GET'])
@login_required
def search_by_barcode():
    barcode = request.args.get('barcode', '').strip()
    if not barcode:
        return jsonify({'success': False, 'message': '请提供条形码'}), 400

    part = SparePart.query.filter_by(barcode=barcode).first()
    if not part:
        part = SparePart.query.filter_by(part_code=barcode).first()

    if part:
        return jsonify({'success': True, 'spare_part': {'id': part.id, 'part_code': part.part_code, 'name': part.name}})
    return jsonify({'success': False, 'message': '未找到对应备件'}), 404


# ──────────────────────────────────────────────
# 导出（CSV/Excel）
# ──────────────────────────────────────────────
@api_spare_parts_bp.route('/export', methods=['GET'])
@login_required
def export_parts():
    from flask import Response
    import io
    import csv
    from datetime import datetime as dt

    fmt = request.args.get('format', 'csv')
    ids_str = request.args.get('ids', '')
    if ids_str:
        id_list = [int(i) for i in ids_str.split(',') if i.strip().isdigit()]
        parts = SparePart.query.filter(SparePart.id.in_(id_list)).all()
    else:
        # 带筛选条件导出
        keyword = request.args.get('keyword', '').strip()
        category_id = request.args.get('category_id', 0, type=int)
        supplier_id = request.args.get('supplier_id', 0, type=int)
        stock_status = request.args.get('stock_status', '')
        is_active = request.args.get('is_active', '')

        query = SparePart.query.options(joinedload(SparePart.category), joinedload(SparePart.supplier))
        if keyword:
            kw = f'%{keyword}%'
            query = query.filter(db.or_(SparePart.part_code.like(kw), SparePart.name.like(kw)))
        if category_id:
            query = query.filter(SparePart.category_id == category_id)
        if supplier_id:
            query = query.filter(SparePart.supplier_id == supplier_id)
        if stock_status:
            query = query.filter(SparePart.stock_status == stock_status)
        if is_active == '1':
            query = query.filter(SparePart.is_active == True)
        elif is_active == '0':
            query = query.filter(SparePart.is_active == False)
        parts = query.all()

    headers_row = ['备件代码', '名称', '规格型号', '分类', '供应商', '当前库存',
                   '库存状态', '最低库存', '最高库存', '单位', '单价', '存放位置',
                   '品牌', '条形码', '安全库存', '备注', '状态', '创建时间']
    status_map = {'low': '不足', 'overstocked': '过剩', 'normal': '正常', 'out': '缺货'}

    def row(p):
        return [
            p.part_code, p.name, p.specification or '',
            p.category.name if p.category else '',
            p.supplier.name if p.supplier else '',
            p.current_stock,
            status_map.get(p.stock_status, ''),
            p.min_stock, p.max_stock or '',
            p.unit or '', float(p.unit_price) if p.unit_price else '',
            p.location or '', p.brand or '', p.barcode or '',
            p.safety_stock or '', p.remark or '',
            '启用' if p.is_active else '停用',
            p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else '',
        ]

    timestamp = dt.now().strftime('%Y%m%d_%H%M%S')

    if fmt == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers_row)
        for p in parts:
            writer.writerow(row(p))
        output.seek(0)
        return Response(
            output.getvalue().encode('utf-8-sig'),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=spare_parts_{timestamp}.csv'}
        )

    # Excel
    try:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = '备件列表'
        ws.append(headers_row)
        for p in parts:
            ws.append(row(p))
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename=spare_parts_{timestamp}.xlsx'}
        )
    except ImportError:
        return jsonify({'success': False, 'error': '请先安装 openpyxl'}), 500


# ──────────────────────────────────────────────
# 图片管理接口（代理转发到原有 spare_parts 蓝图）
# ──────────────────────────────────────────────
@api_spare_parts_bp.route('/<int:id>/images', methods=['GET'])
@login_required
def get_images(id):
    part = SparePart.query.get_or_404(id)
    return jsonify({
        'success': True,
        'images': {
            'front': part.image_url,
            'thumbnail': part.thumbnail_url,
            'side': part.side_image_url,
            'detail': part.detail_image_url,
            'circuit': part.circuit_image_url,
            'perspective': part.perspective_image_url,
        }
    })


@api_spare_parts_bp.route('/<int:id>/generate-single-image', methods=['POST'])
@login_required
def generate_single_image(id):
    if not current_user.has_permission('spare_part', 'update'):
        return jsonify({'success': False, 'error': '无编辑权限'}), 403

    part = SparePart.query.get_or_404(id)
    data = request.get_json() or {}
    image_type = data.get('image_type')
    if not image_type:
        return jsonify({'success': False, 'message': '请指定图片类型'}), 400

    try:
        from app.services.image_generation_service import ImageGenerationService
        supplier_name = part.supplier.name if part.supplier else '未知供应商'
        svc = ImageGenerationService()
        result = svc.generate_single_image_by_type(
            part_code=part.part_code, part_name=part.name,
            supplier_name=supplier_name, image_type=image_type
        )
        if result['success']:
            field_map = {
                'front': 'image_url', 'thumbnail': 'thumbnail_url',
                'side': 'side_image_url', 'detail': 'detail_image_url',
                'circuit': 'circuit_image_url', 'perspective': 'perspective_image_url',
            }
            if image_type in field_map:
                setattr(part, field_map[image_type], result['image_url'])
                db.session.commit()
        return jsonify(result)
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@api_spare_parts_bp.route('/<int:id>/upload-image', methods=['POST'])
@login_required
def upload_image(id):
    if not current_user.has_permission('spare_part', 'update'):
        return jsonify({'success': False, 'error': '无编辑权限'}), 403

    from flask import current_app
    from werkzeug.utils import secure_filename
    import os

    part = SparePart.query.get_or_404(id)
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': '没有选择图片'}), 400

    file = request.files['image']
    image_type = request.form.get('image_type', 'front')

    allowed = {'png', 'jpg', 'jpeg', 'gif'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed:
        return jsonify({'success': False, 'message': '不支持的图片格式'}), 400

    try:
        base_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        part_dir = os.path.join(base_dir, 'images', part.part_code)
        os.makedirs(part_dir, exist_ok=True)
        filename = f'{image_type}.jpg'
        file.save(os.path.join(part_dir, filename))
        url = f'/uploads/images/{part.part_code}/{filename}'

        field_map = {
            'front': 'image_url', 'thumbnail': 'thumbnail_url',
            'side': 'side_image_url', 'detail': 'detail_image_url',
            'circuit': 'circuit_image_url', 'perspective': 'perspective_image_url',
        }
        if image_type in field_map:
            setattr(part, field_map[image_type], url)
            db.session.commit()

        return jsonify({'success': True, 'image_url': url})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@api_spare_parts_bp.route('/<int:id>/remove-image', methods=['POST'])
@login_required
def remove_image(id):
    if not current_user.has_permission('spare_part', 'update'):
        return jsonify({'success': False, 'error': '无编辑权限'}), 403

    from flask import current_app
    import os

    part = SparePart.query.get_or_404(id)
    data = request.get_json() or {}
    image_type = data.get('image_type')

    field_map = {
        'front': 'image_url', 'thumbnail': 'thumbnail_url',
        'side': 'side_image_url', 'detail': 'detail_image_url',
        'circuit': 'circuit_image_url', 'perspective': 'perspective_image_url',
    }
    if image_type not in field_map:
        return jsonify({'success': False, 'message': '无效的图片类型'}), 400

    try:
        base_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        fp = os.path.join(base_dir, 'images', part.part_code, f'{image_type}.jpg')
        if os.path.exists(fp):
            os.remove(fp)
        setattr(part, field_map[image_type], None)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ──────────────────────────────────────────────
# 条形码
# ──────────────────────────────────────────────
@api_spare_parts_bp.route('/<int:id>/barcode', methods=['GET'])
@login_required
def get_barcode(id):
    from flask import Response
    from app.services.barcode_service import generate_barcode_for_spare_part
    part = SparePart.query.get_or_404(id)
    try:
        _, barcode_bytes = generate_barcode_for_spare_part(part)
        if barcode_bytes:
            return Response(barcode_bytes, mimetype='image/png')
        return jsonify({'success': False, 'message': '生成失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_spare_parts_bp.route('/<int:id>/generate-barcode', methods=['POST'])
@login_required
def generate_barcode(id):
    if not current_user.has_permission('spare_part', 'update'):
        return jsonify({'success': False, 'error': '无编辑权限'}), 403

    from flask import current_app
    from app.services.barcode_service import generate_barcode_for_spare_part, save_barcode_to_file
    import os
    part = SparePart.query.get_or_404(id)
    try:
        barcode_data, barcode_bytes = generate_barcode_for_spare_part(part)
        if barcode_bytes:
            if not part.barcode:
                part.barcode = barcode_data
                db.session.commit()
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            barcode_folder = os.path.join(upload_folder, 'barcodes')
            filename = f'{part.part_code or part.id}.png'
            file_path = os.path.join(barcode_folder, filename)
            if save_barcode_to_file(barcode_data, file_path):
                return jsonify({
                    'success': True,
                    'barcode': barcode_data,
                    'barcode_url': f'/uploads/barcodes/{filename}'
                })
        return jsonify({'success': False, 'message': '生成失败'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ──────────────────────────────────────────────
# AI 智能填充
# ──────────────────────────────────────────────
@api_spare_parts_bp.route('/<int:id>/ai-fill', methods=['GET', 'POST'])
@login_required
def ai_fill(id):
    if not current_user.has_permission('spare_part', 'update'):
        return jsonify({'success': False, 'error': '无编辑权限'}), 403

    part = SparePart.query.get_or_404(id)
    try:
        from app.services.ai_info_fill_service import AIInfoFillService
        part_data = {
            'part_code': part.part_code, 'name': part.name,
            'specification': part.specification, 'brand': part.brand,
            'current_stock': part.current_stock, 'unit': part.unit,
            'unit_price': float(part.unit_price) if part.unit_price else None,
            'category_name': part.category.name if part.category else None,
            'supplier_name': part.supplier.name if part.supplier else None,
        }
        svc = AIInfoFillService()
        return jsonify(svc.fill_spare_part_info(part_data))
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@api_spare_parts_bp.route('/<int:id>/apply-ai-fill', methods=['POST'])
@login_required
def apply_ai_fill(id):
    if not current_user.has_permission('spare_part', 'update'):
        return jsonify({'success': False, 'error': '无编辑权限'}), 403

    part = SparePart.query.get_or_404(id)
    data = request.get_json() or {}
    filled = data.get('filled_data', {})
    try:
        for field in ('specification', 'safety_stock', 'min_stock', 'max_stock'):
            if field in filled and filled[field] is not None:
                setattr(part, field, filled[field])
        if 'description' in filled and filled['description']:
            part.remark = filled['description']
        if 'technical_params' in filled and filled['technical_params']:
            part.technical_params = filled['technical_params']
        db.session.commit()
        return jsonify({'success': True, 'message': 'AI填充信息已应用'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ──────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────
def _parse_date(value):
    if not value:
        return None
    from datetime import datetime
    for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y/%m/%d'):
        try:
            return datetime.strptime(value, fmt)
        except (ValueError, TypeError):
            continue
    return None
