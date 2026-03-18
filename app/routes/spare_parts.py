"""
备件管理模块路由
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.spare_part import SparePart
from app.models.category import Category
from app.models.supplier import Supplier
from app.forms.spare_parts import SparePartForm, SparePartSearchForm
from app.utils.decorators import permission_required
from app.utils.helpers import paginate_query

spare_parts_bp = Blueprint('spare_parts', __name__, template_folder='../templates/spare_parts')


@spare_parts_bp.route('/')
@login_required
def index():
    """备件列表页面"""
    form = SparePartSearchForm()
    
    query = SparePart.query
    
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
    
    pagination = paginate_query(query, per_page=20)
    
    return render_template('spare_parts/list.html', 
                         pagination=pagination, 
                         form=form,
                         categories=Category.query.filter_by(is_active=True).all(),
                         suppliers=Supplier.query.filter_by(is_active=True).all())


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
            current_stock=form.current_stock.data or 0,
            min_stock=form.min_stock.data or 0,
            max_stock=form.max_stock.data,
            unit=form.unit.data,
            unit_price=form.unit_price.data,
            location=form.location.data,
            image_url=form.image_url.data,
            remark=form.remark.data,
            is_active=form.is_active.data,
            created_by=current_user.id
        )
        
        spare_part.update_stock_status()
        
        db.session.add(spare_part)
        db.session.commit()
        
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
        spare_part.current_stock = form.current_stock.data or 0
        spare_part.min_stock = form.min_stock.data or 0
        spare_part.max_stock = form.max_stock.data
        spare_part.unit = form.unit.data
        spare_part.unit_price = form.unit_price.data
        spare_part.location = form.location.data
        spare_part.image_url = form.image_url.data
        spare_part.remark = form.remark.data
        spare_part.is_active = form.is_active.data
        
        spare_part.update_stock_status()
        
        db.session.commit()
        
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
