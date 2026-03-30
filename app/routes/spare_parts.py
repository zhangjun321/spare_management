# -*- coding: utf-8 -*-
"""
备件管理模块路由
"""


from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models.spare_part import SparePart
from app.models.category import Category
from app.models.supplier import Supplier
from app.forms.spare_parts import SparePartForm, SparePartSearchForm
from app.utils.decorators import permission_required
from app.utils.helpers import paginate_query
from app.services.cache_service import cache, clear_cache
import io
import csv
from datetime import datetime

spare_parts_bp = Blueprint('spare_parts', __name__, template_folder='../templates/spare_parts')


@spare_parts_bp.route('/')
@login_required
def index():
    """备件列表页面"""
    form = SparePartSearchForm()
    
    # 使用 joinedload 预加载关联数据，避免 N+1 查询
    query = SparePart.query.options(
        joinedload(SparePart.category),
        joinedload(SparePart.supplier)
    )
    
    if form.keyword.data:
        keyword = f'%{form.keyword.data}%'
        query = query.filter(
            db.or_(
                SparePart.part_code.like(keyword),
                SparePart.name.like(keyword),
                SparePart.specification.like(keyword)
            )
        )
    
    if form.category_id.data and form.category_id.data != 0:
        query = query.filter(SparePart.category_id == form.category_id.data)
    
    if form.supplier_id.data and form.supplier_id.data != 0:
        query = query.filter(SparePart.supplier_id == form.supplier_id.data)
    
    if form.stock_status.data:
        query = query.filter(SparePart.stock_status == form.stock_status.data)
    
    if form.is_active.data == '1':
        query = query.filter(SparePart.is_active == True)
    elif form.is_active.data == '0':
        query = query.filter(SparePart.is_active == False)
    
    # 获取每页显示数量，默认 20
    try:
        per_page = int(request.args.get('per_page', 20))
        if per_page not in [10, 20, 50]:
            per_page = 20
    except (TypeError, ValueError):
        per_page = 20
    
    # 使用 distinct 避免重复记录
    query = query.distinct()
    
    pagination = paginate_query(query, per_page=per_page)
    
    @cache('categories:active', expire=3600)
    def get_active_categories():
        return Category.query.filter_by(is_active=True).all()
    
    @cache('suppliers:active', expire=3600)
    def get_active_suppliers():
        return Supplier.query.filter_by(is_active=True).all()
    
    return render_template('spare_parts/list.html', 
                         pagination=pagination, 
                         form=form,
                         per_page=per_page,
                         categories=get_active_categories(),
                         suppliers=get_active_suppliers())


@spare_parts_bp.route('/new', methods=['GET', 'POST'])
@login_required
@permission_required('spare_part', 'create')
def new():
    """新增备件"""
    form = SparePartForm()
    
    if form.validate_on_submit():
        spare_part = SparePart(
            part_code=form.part_code.data,
            name=form.name.data,
            specification=form.specification.data,
            category_id=form.category_id.data if form.category_id.data != 0 else None,
            supplier_id=form.supplier_id.data if form.supplier_id.data != 0 else None,
            warehouse_id=form.warehouse_id.data if form.warehouse_id.data != 0 else None,
            location_id=form.location_id.data if form.location_id.data != 0 else None,
            current_stock=form.current_stock.data or 0,
            min_stock=form.min_stock.data or 0,
            max_stock=form.max_stock.data,
            unit=form.unit.data,
            unit_price=form.unit_price.data,
            location=form.location.data,
            brand=form.brand.data,
            barcode=form.barcode.data,
            safety_stock=form.safety_stock.data or 0,
            reorder_point=form.reorder_point.data,
            last_purchase_price=form.last_purchase_price.data,
            currency=form.currency.data,
            warranty_period=form.warranty_period.data,
            last_purchase_date=form.last_purchase_date.data,
            datasheet_url=form.datasheet_url.data,
            image_url=form.image_url.data,
            remark=form.remark.data,
            is_active=form.is_active.data,
            created_by=current_user.id
        )
        
        spare_part.update_stock_status()
        
        db.session.add(spare_part)
        db.session.commit()
        
        # 清除相关缓存
        clear_cache('categories:*')
        clear_cache('suppliers:*')
        
        flash('备件创建成功！', 'success')
        return redirect(url_for('spare_parts.index'))
    
    return render_template('spare_parts/form.html', form=form, title='新增备件')


@spare_parts_bp.route('/<int:id>')
@login_required
def detail(id):
    """备件详情"""
    spare_part = SparePart.query.get_or_404(id)
    return render_template('spare_parts/detail.html', spare_part=spare_part)


@spare_parts_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('spare_part', 'update')
def edit(id):
    """编辑备件"""
    spare_part = SparePart.query.get_or_404(id)
    form = SparePartForm(obj=spare_part)
    form.id = spare_part.id
    
    if form.validate_on_submit():
        spare_part.part_code = form.part_code.data
        spare_part.name = form.name.data
        spare_part.specification = form.specification.data
        spare_part.category_id = form.category_id.data if form.category_id.data != 0 else None
        spare_part.supplier_id = form.supplier_id.data if form.supplier_id.data != 0 else None
        spare_part.warehouse_id = form.warehouse_id.data if form.warehouse_id.data != 0 else None
        spare_part.location_id = form.location_id.data if form.location_id.data != 0 else None
        spare_part.current_stock = form.current_stock.data or 0
        spare_part.min_stock = form.min_stock.data or 0
        spare_part.max_stock = form.max_stock.data
        spare_part.unit = form.unit.data
        spare_part.unit_price = form.unit_price.data
        spare_part.location = form.location.data
        spare_part.brand = form.brand.data
        spare_part.barcode = form.barcode.data
        spare_part.safety_stock = form.safety_stock.data or 0
        spare_part.reorder_point = form.reorder_point.data
        spare_part.last_purchase_price = form.last_purchase_price.data
        spare_part.currency = form.currency.data
        spare_part.warranty_period = form.warranty_period.data
        spare_part.last_purchase_date = form.last_purchase_date.data
        spare_part.datasheet_url = form.datasheet_url.data
        spare_part.image_url = form.image_url.data
        spare_part.remark = form.remark.data
        spare_part.is_active = form.is_active.data
        
        spare_part.update_stock_status()
        
        db.session.commit()
        
        # 清除相关缓存
        clear_cache('categories:*')
        clear_cache('suppliers:*')
        
        flash('备件更新成功！', 'success')
        return redirect(url_for('spare_parts.detail', id=spare_part.id))
    
    return render_template('spare_parts/form.html', form=form, title='编辑备件')


@spare_parts_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('spare_part', 'delete')
def delete(id):
    """删除备件"""
    spare_part = SparePart.query.get_or_404(id)
    
    db.session.delete(spare_part)
    db.session.commit()
    
    flash('备件删除成功！', 'success')
    return redirect(url_for('spare_parts.index'))


@spare_parts_bp.route('/<int:id>/toggle-status', methods=['POST'])
@login_required
@permission_required('spare_part', 'update')
def toggle_status(id):
    """切换备件状态"""
    spare_part = SparePart.query.get_or_404(id)
    spare_part.is_active = not spare_part.is_active
    
    db.session.commit()
    
    flash('备件状态已更新！', 'success')
    return redirect(url_for('spare_parts.detail', id=spare_part.id))


@spare_parts_bp.route('/api/check-code', methods=['POST'])
@login_required
def check_code():
    """检查备件代码是否存在"""
    data = request.get_json()
    part_code = data.get('part_code')
    exclude_id = data.get('exclude_id')
    
    query = SparePart.query.filter_by(part_code=part_code)
    if exclude_id:
        query = query.filter(SparePart.id != exclude_id)
    
    exists = query.first() is not None
    
    return jsonify({'exists': exists})


@spare_parts_bp.route('/export')
@login_required
@permission_required('spare_part', 'read')
def export():
    """导出备件数据"""
    format_type = request.args.get('format', 'excel')
    ids = request.args.get('ids', '')
    
    # 查询数据
    if ids:
        id_list = [int(id) for id in ids.split(',')]
        query = SparePart.query.filter(SparePart.id.in_(id_list))
    else:
        query = SparePart.query
    
    parts = query.all()
    
    if format_type == 'csv':
        # 导出 CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            '备件代码', '名称', '规格型号', '分类', '供应商', '当前库存',
            '库存状态', '最低库存', '最高库存', '单位', '单价', '存放位置',
            '品牌', '条形码', '安全库存', '备注', '状态', '创建时间'
        ])
        
        # 写入数据
        for part in parts:
            writer.writerow([
                part.part_code,
                part.name,
                part.specification or '',
                part.category.name if part.category else '',
                part.supplier.name if part.supplier else '',
                part.current_stock,
                {'low': '不足', 'overstocked': '过剩', 'normal': '正常'}.get(part.stock_status, ''),
                part.min_stock,
                part.max_stock or '',
                part.unit or '',
                float(part.unit_price) if part.unit_price else '',
                part.location or '',
                part.brand or '',
                part.barcode or '',
                part.safety_stock or '',
                part.remark or '',
                '启用' if part.is_active else '停用',
                part.created_at.strftime('%Y-%m-%d %H:%M:%S') if part.created_at else ''
            ])
        
        output.seek(0)
        return Response(
            output.getvalue().encode('utf-8-sig'),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=spare_parts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
    
    # 默认导出 Excel（需要 openpyxl 库）
    try:
        from openpyxl import Workbook
        
        wb = Workbook()
        ws = wb.active
        ws.title = '备件列表'
        
        # 表头
        headers = [
            '备件代码', '名称', '规格型号', '分类', '供应商', '当前库存',
            '库存状态', '最低库存', '最高库存', '单位', '单价', '存放位置',
            '品牌', '条形码', '安全库存', '备注', '状态', '创建时间'
        ]
        ws.append(headers)
        
        # 数据
        for part in parts:
            ws.append([
                part.part_code,
                part.name,
                part.specification or '',
                part.category.name if part.category else '',
                part.supplier.name if part.supplier else '',
                part.current_stock,
                {'low': '不足', 'overstocked': '过剩', 'normal': '正常'}.get(part.stock_status, ''),
                part.min_stock,
                part.max_stock or '',
                part.unit or '',
                float(part.unit_price) if part.unit_price else 0,
                part.location or '',
                part.brand or '',
                part.barcode or '',
                part.safety_stock or 0,
                part.remark or '',
                '启用' if part.is_active else '停用',
                part.created_at.strftime('%Y-%m-%d %H:%M:%S') if part.created_at else ''
            ])
        
        # 调整列宽
        for column in ws.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2) if max_length < 50 else 50
            ws.column_dimensions[column[0].column_letter].width = adjusted_width
        
        # 保存到字节流
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': f'attachment; filename=spare_parts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            }
        )
    except ImportError:
        flash('请先安装 openpyxl 库：pip install openpyxl', 'warning')
        return redirect(url_for('spare_parts.index'))
