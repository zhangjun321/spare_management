# -*- coding: utf-8 -*-
"""
备件管理模块路由
"""


from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response, current_app
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
from app.services.image_generation_service import ImageGenerationService
import io
import os
import csv
from datetime import datetime

spare_parts_bp = Blueprint('spare_parts', __name__, template_folder='../templates/spare_parts')

# CSRF 豁免配置
from app.extensions import csrf
csrf.exempt(spare_parts_bp)


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
        spare_part.thumbnail_url = form.thumbnail_url.data
        spare_part.side_image_url = form.side_image_url.data
        spare_part.detail_image_url = form.detail_image_url.data
        spare_part.circuit_image_url = form.circuit_image_url.data
        spare_part.perspective_image_url = form.perspective_image_url.data
        spare_part.remark = form.remark.data
        spare_part.is_active = form.is_active.data
        
        spare_part.update_stock_status()
        
        db.session.commit()
        
        # 清除相关缓存
        clear_cache('categories:*')
        clear_cache('suppliers:*')
        
        flash('备件更新成功！', 'success')
        return redirect(url_for('spare_parts.detail', id=spare_part.id))
    
    return render_template('spare_parts/form.html', form=form, title='编辑备件', spare_part=spare_part)


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


@spare_parts_bp.route('/<int:id>/generate-images', methods=['POST'])
@login_required
@permission_required('spare_part', 'update')
def generate_images(id):
    """生成备件图片"""
    from app.extensions import db, csrf
    
    spare_part = SparePart.query.get_or_404(id)
    
    try:
        # 获取供应商名称
        supplier_name = spare_part.supplier.name if spare_part.supplier else "未知供应商"
        
        # 初始化图片生成服务
        image_service = ImageGenerationService()
        
        # 生成图片
        results = image_service.generate_spare_part_images(
            part_code=spare_part.part_code,
            part_name=spare_part.name,
            supplier_name=supplier_name
        )
        
        # 更新备件的缩略图
        if results.get('thumbnail_url'):
            spare_part.thumbnail_url = results['thumbnail_url']
        
        # 更新图片URL（使用正面图）
        if results.get('images', {}).get('front'):
            spare_part.image_url = results['images']['front']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '图片生成成功',
            'data': results
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'图片生成失败: {str(e)}'
        }), 500

@spare_parts_bp.route('/<int:id>/image-types', methods=['GET'])
@login_required
@permission_required('spare_part', 'view')
def get_image_types(id):
    """获取图片类型列表"""
    image_service = ImageGenerationService()
    types = image_service.get_image_types()
    return jsonify({
        'success': True,
        'data': [{'type': t[0], 'name': t[1]} for t in types]
    })


@spare_parts_bp.route('/<int:id>/generate-single-image', methods=['POST'])
@login_required
@permission_required('spare_part', 'update')
def generate_single_image(id):
    """生成单张图片"""
    from app.extensions import db, csrf
    
    spare_part = SparePart.query.get_or_404(id)
    data = request.get_json()
    image_type = data.get('image_type')
    
    if not image_type:
        return jsonify({'success': False, 'message': '请指定图片类型'}), 400
    
    try:
        supplier_name = spare_part.supplier.name if spare_part.supplier else "未知供应商"
        image_service = ImageGenerationService()
        
        result = image_service.generate_single_image_by_type(
            part_code=spare_part.part_code,
            part_name=spare_part.name,
            supplier_name=supplier_name,
            image_type=image_type
        )
        
        if result['success']:
            if image_type == 'thumbnail':
                spare_part.thumbnail_url = result['image_url']
            elif image_type == 'front':
                spare_part.image_url = result['image_url']
            
            db.session.commit()
        
        return jsonify(result)
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'图片生成失败: {str(e)}'
        }), 500


# 豁免此端点的 CSRF 保护
from app.extensions import csrf
csrf.exempt(generate_images)
csrf.exempt(generate_single_image)


@spare_parts_bp.route('/<int:id>/images', methods=['GET'])
@login_required
@permission_required('spare_part', 'view')
def get_images(id):
    """获取备件的所有图片"""
    spare_part = SparePart.query.get_or_404(id)
    
    images = {
        'front': spare_part.image_url,
        'thumbnail': spare_part.thumbnail_url,
        'side': spare_part.side_image_url,
        'detail': spare_part.detail_image_url,
        'circuit': spare_part.circuit_image_url,
        'perspective': spare_part.perspective_image_url
    }
    
    return jsonify({
        'success': True,
        'images': images
    })


@spare_parts_bp.route('/<int:id>/upload-image', methods=['POST'])
@login_required
@permission_required('spare_part', 'update')
def upload_image(id):
    """上传图片"""
    from werkzeug.utils import secure_filename
    
    spare_part = SparePart.query.get_or_404(id)
    
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': '没有选择图片'}), 400
    
    file = request.files['image']
    image_type = request.form.get('image_type', 'front')
    
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择图片'}), 400
    
    # 允许的文件扩展名
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'success': False, 'message': '不支持的图片格式'}), 400
    
    try:
        # 保存图片
        part_code = spare_part.part_code
        base_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads/images')
        part_dir = os.path.join(base_dir, part_code)
        
        if not os.path.exists(part_dir):
            os.makedirs(part_dir, exist_ok=True)
        
        # 保存文件
        filename = f'{image_type}.jpg'
        filepath = os.path.join(part_dir, filename)
        file.save(filepath)
        
        # 更新数据库
        if image_type == 'front':
            spare_part.image_url = f'/uploads/images/{part_code}/{filename}'
        elif image_type == 'thumbnail':
            spare_part.thumbnail_url = f'/uploads/images/{part_code}/{filename}'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'image_url': f'/uploads/images/{part_code}/{filename}'
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'上传失败：{str(e)}'
        }), 500


@spare_parts_bp.route('/<int:id>/remove-image', methods=['POST'])
@login_required
@permission_required('spare_part', 'update')
def remove_image(id):
    """删除图片"""
    spare_part = SparePart.query.get_or_404(id)
    data = request.get_json()
    image_type = data.get('image_type')
    
    if not image_type:
        return jsonify({'success': False, 'message': '请指定图片类型'}), 400
    
    try:
        part_code = spare_part.part_code
        base_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads/images')
        part_dir = os.path.join(base_dir, part_code)
        filepath = os.path.join(part_dir, f'{image_type}.jpg')
        
        # 删除文件
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # 更新数据库
        field_map = {
            'front': 'image_url',
            'thumbnail': 'thumbnail_url',
            'side': 'side_image_url',
            'detail': 'detail_image_url',
            'circuit': 'circuit_image_url',
            'perspective': 'perspective_image_url'
        }
        
        field_name = field_map.get(image_type)
        if field_name:
            setattr(spare_part, field_name, None)
        
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'删除失败：{str(e)}'
        }), 500


@spare_parts_bp.route('/<int:id>/check-ai-images', methods=['GET'])
@login_required
@permission_required('spare_part', 'view')
def check_ai_images(id):
    """检查 AI 生成的图片"""
    spare_part = SparePart.query.get_or_404(id)
    part_code = spare_part.part_code
    
    try:
        base_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads/images')
        part_dir = os.path.join(base_dir, part_code)
        
        # 检查目录是否存在
        if not os.path.exists(part_dir):
            return jsonify({
                'success': True,
                'hasImages': False,
                'message': '还没有 AI 生成的图片，请先生成 AI 图片！',
                'images': []
            })
        
        # 检查有哪些图片
        image_types = ['front', 'side', 'detail', 'circuit', 'perspective', 'thumbnail']
        available_images = []
        
        for img_type in image_types:
            img_path = os.path.join(part_dir, f'{img_type}.jpg')
            if os.path.exists(img_path):
                available_images.append(img_type)
        
        if len(available_images) == 0:
            return jsonify({
                'success': True,
                'hasImages': False,
                'message': '还没有 AI 生成的图片，请先生成 AI 图片！',
                'images': []
            })
        
        return jsonify({
            'success': True,
            'hasImages': True,
            'images': available_images
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'检查失败：{str(e)}'
        }), 500


@spare_parts_bp.route('/<int:id>/auto-upload-image', methods=['POST'])
@login_required
@permission_required('spare_part', 'update')
def auto_upload_image(id):
    """自动上传图片（从 AI 生成目录）"""
    spare_part = SparePart.query.get_or_404(id)
    data = request.get_json()
    image_type = data.get('image_type')
    
    if not image_type:
        return jsonify({'success': False, 'message': '请指定图片类型'}), 400
    
    try:
        part_code = spare_part.part_code
        base_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads/images')
        part_dir = os.path.join(base_dir, part_code)
        
        # 源文件路径
        source_path = os.path.join(part_dir, f'{image_type}.jpg')
        
        # 检查源文件是否存在
        if not os.path.exists(source_path):
            return jsonify({
                'success': False,
                'message': f'{image_type} 图片不存在'
            })
        
        # 检查是否已经有图片
        current_url = None
        if image_type == 'front':
            current_url = spare_part.image_url
        elif image_type == 'thumbnail':
            current_url = spare_part.thumbnail_url
        
        action = 'uploaded'
        
        # 如果已有图片，检查是否需要替换（简单比较 URL）
        if current_url:
            # 如果 URL 相同，说明已经是这张图，不需要更新
            expected_url = f'/uploads/images/{part_code}/{image_type}.jpg'
            if current_url == expected_url:
                action = 'skipped'
            else:
                action = 'updated'
        
        # 更新数据库
        if action != 'skipped':
            if image_type == 'front':
                spare_part.image_url = f'/uploads/images/{part_code}/{image_type}.jpg'
            elif image_type == 'thumbnail':
                spare_part.thumbnail_url = f'/uploads/images/{part_code}/{image_type}.jpg'
            elif image_type == 'side':
                spare_part.side_image_url = f'/uploads/images/{part_code}/{image_type}.jpg'
            elif image_type == 'detail':
                spare_part.detail_image_url = f'/uploads/images/{part_code}/{image_type}.jpg'
            elif image_type == 'circuit':
                spare_part.circuit_image_url = f'/uploads/images/{part_code}/{image_type}.jpg'
            elif image_type == 'perspective':
                spare_part.perspective_image_url = f'/uploads/images/{part_code}/{image_type}.jpg'
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'image_url': f'/uploads/images/{part_code}/{image_type}.jpg',
            'action': action
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'上传失败：{str(e)}'
        }), 500


@spare_parts_bp.route('/code/<part_code>/check-ai-images', methods=['GET'])
@login_required
@permission_required('spare_part', 'view')
def check_ai_images_by_code(part_code):
    """通过备件代码检查 AI 生成的图片"""
    from flask import current_app
    
    try:
        # 获取 UPLOAD_FOLDER 配置（应该是 uploads 目录）
        base_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        
        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(base_dir):
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), base_dir)
        
        # 图片子目录
        part_dir = os.path.join(base_dir, 'images', part_code)
        
        # 检查目录是否存在
        if not os.path.exists(part_dir):
            return jsonify({
                'success': True,
                'hasImages': False,
                'message': '还没有 AI 生成的图片，请先生成 AI 图片！',
                'images': []
            })
        
        # 检查有哪些图片
        image_types = ['front', 'side', 'detail', 'circuit', 'perspective', 'thumbnail']
        available_images = []
        
        for img_type in image_types:
            img_path = os.path.join(part_dir, f'{img_type}.jpg')
            if os.path.exists(img_path):
                available_images.append(img_type)
        
        if len(available_images) == 0:
            return jsonify({
                'success': True,
                'hasImages': False,
                'message': '还没有 AI 生成的图片，请先生成 AI 图片！',
                'images': []
            })
        
        return jsonify({
            'success': True,
            'hasImages': True,
            'images': available_images
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'检查失败：{str(e)}'
        }), 500


@spare_parts_bp.route('/code/<part_code>/auto-upload-image', methods=['POST'])
@login_required
@permission_required('spare_part', 'update')
def auto_upload_image_by_code(part_code):
    """通过备件代码自动上传图片（从 AI 生成目录）"""
    from flask import current_app
    
    data = request.get_json()
    image_type = data.get('image_type')
    
    if not image_type:
        return jsonify({'success': False, 'message': '请指定图片类型'}), 400
    
    try:
        # 通过 part_code 查找备件
        spare_part = SparePart.query.filter_by(part_code=part_code).first()
        
        if not spare_part:
            return jsonify({
                'success': False,
                'message': '备件不存在，请先保存备件信息'
            })
        
        # 获取 UPLOAD_FOLDER 配置（应该是 uploads 目录）
        base_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        
        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(base_dir):
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), base_dir)
        
        # 图片子目录
        part_dir = os.path.join(base_dir, 'images', part_code)
        
        # 源文件路径
        source_path = os.path.join(part_dir, f'{image_type}.jpg')
        
        # 检查源文件是否存在
        if not os.path.exists(source_path):
            return jsonify({
                'success': False,
                'message': f'{image_type} 图片不存在'
            })
        
        # 检查是否已经有图片
        current_url = None
        if image_type == 'front':
            current_url = spare_part.image_url
        elif image_type == 'thumbnail':
            current_url = spare_part.thumbnail_url
        
        action = 'uploaded'
        
        # 如果已有图片，检查是否需要替换（简单比较 URL）
        if current_url:
            # 如果 URL 相同，说明已经是这张图，不需要更新
            expected_url = f'/uploads/images/{part_code}/{image_type}.jpg'
            if current_url == expected_url:
                action = 'skipped'
            else:
                action = 'updated'
        
        # 更新数据库
        if action != 'skipped':
            if image_type == 'front':
                spare_part.image_url = f'/uploads/images/{part_code}/{image_type}.jpg'
            elif image_type == 'thumbnail':
                spare_part.thumbnail_url = f'/uploads/images/{part_code}/{image_type}.jpg'
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'image_url': f'/uploads/images/{part_code}/{image_type}.jpg',
            'action': action
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'上传失败：{str(e)}'
        }), 500


# �����Զ��ϴ� API �� CSRF ����
csrf.exempt(auto_upload_image_by_code)
