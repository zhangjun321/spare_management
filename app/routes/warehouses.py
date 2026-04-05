"""
仓库管理模块路由
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.forms.warehouse import WarehouseForm, WarehouseLocationForm, InventoryAdjustForm, InventoryTransferForm
from app.services.warehouse_service import WarehouseService
from app.services.location_service import LocationService
from app.services.inventory_service import InventoryService
from app.services.operation_service import OperationService
from app.services.report_service import ReportService
from app.models.user import User
from app.models.spare_part import SparePart
from app.models import Warehouse
from app.extensions import db
from app.utils.decorators import permission_required

warehouses_bp = Blueprint('warehouses', __name__, template_folder='../templates/warehouses')

# 仓库管理路由
@warehouses_bp.route('/')
@login_required
@permission_required('warehouse', 'read')
def index():
    """仓库列表 - 整合智能仓库功能"""
    # 获取筛选条件
    filters = {
        'name': request.args.get('name'),
        'code': request.args.get('code'),
        'type': request.args.get('type'),
        'is_active': request.args.get('is_active') == 'true'
    }
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 获取仓库列表
    pagination = WarehouseService.get_warehouses(filters, page, per_page)
    
    # 获取统计信息
    statistics = WarehouseService.get_warehouse_statistics()
    
    # 获取所有启用的仓库（用于智能管理）
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    
    return render_template('warehouses/index.html', 
                         pagination=pagination,
                         filters=filters,
                         statistics=statistics,
                         warehouses=warehouses or [])


@warehouses_bp.route('/dashboard')
@login_required
@permission_required('warehouse', 'read')
def dashboard():
    """仓库看板"""
    from app.services.warehouse_advanced_service_v2 import WarehouseAdvancedService
    
    warehouse_id = request.args.get('warehouse_id', type=int)
    period_days = request.args.get('period_days', 30, type=int)
    
    kpis = WarehouseAdvancedService.calculate_kpis(warehouse_id, period_days)
    
    from app.models.warehouse import Warehouse
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    
    return render_template('warehouses/dashboard.html', 
                         kpis=kpis,
                         warehouses=warehouses,
                         selected_warehouse_id=warehouse_id,
                         period_days=period_days)

@warehouses_bp.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('warehouse', 'create')
def create():
    """创建仓库"""
    form = WarehouseForm()
    
    # 填充仓库管理员选项
    form.manager_id.choices = [(0, '请选择')] + [(user.id, user.real_name) for user in User.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        data = form.data
        data.pop('submit')
        data.pop('csrf_token')
        
        # 处理仓库管理员
        if data['manager_id'] == 0:
            data['manager_id'] = None
        
        warehouse = WarehouseService.create_warehouse(data)
        flash('仓库创建成功！', 'success')
        return redirect(url_for('warehouses.index'))
    
    return render_template('warehouses/form.html', form=form, title='创建仓库')

@warehouses_bp.route('/<int:id>')
@login_required
@permission_required('warehouse', 'read')
def detail(id):
    """仓库详情"""
    warehouse = WarehouseService.get_warehouse(id)
    if not warehouse:
        flash('仓库不存在', 'danger')
        return redirect(url_for('warehouses.index'))
    
    # 获取仓库统计信息
    total_inventory = WarehouseService.get_total_inventory(id)
    utilization_rate = WarehouseService.get_utilization_rate(id)
    operations_count = WarehouseService.get_operations_count(id)
    
    # 获取仓库的库位
    locations = LocationService.get_location_by_warehouse(id)
    
    return render_template('warehouses/detail.html', 
                         warehouse=warehouse,
                         total_inventory=total_inventory,
                         utilization_rate=utilization_rate,
                         operations_count=operations_count,
                         locations=locations)

@warehouses_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('warehouse', 'update')
def edit(id):
    """编辑仓库"""
    warehouse = WarehouseService.get_warehouse(id)
    if not warehouse:
        flash('仓库不存在', 'danger')
        return redirect(url_for('warehouses.index'))
    
    form = WarehouseForm(obj=warehouse)
    
    # 填充仓库管理员选项
    form.manager_id.choices = [(0, '请选择')] + [(user.id, user.real_name) for user in User.query.filter_by(is_active=True).all()]
    if warehouse.manager_id:
        form.manager_id.data = warehouse.manager_id
    else:
        form.manager_id.data = 0
    
    if form.validate_on_submit():
        data = form.data
        data.pop('submit')
        data.pop('csrf_token')
        
        # 处理仓库管理员
        if data['manager_id'] == 0:
            data['manager_id'] = None
        
        warehouse = WarehouseService.update_warehouse(id, data)
        flash('仓库更新成功！', 'success')
        return redirect(url_for('warehouses.detail', id=id))
    
    return render_template('warehouses/form.html', form=form, title='编辑仓库', warehouse=warehouse)

@warehouses_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('warehouse', 'delete')
def delete(id):
    """删除仓库"""
    success = WarehouseService.delete_warehouse(id)
    if success:
        flash('仓库删除成功！', 'success')
    else:
        flash('仓库删除失败，可能存在关联的库位', 'danger')
    return redirect(url_for('warehouses.index'))

@warehouses_bp.route('/<int:id>/locations')
@login_required
@permission_required('warehouse', 'read')
def warehouse_locations(id):
    """仓库库位列表"""
    warehouse = WarehouseService.get_warehouse(id)
    if not warehouse:
        flash('仓库不存在', 'danger')
        return redirect(url_for('warehouses.index'))
    
    locations = LocationService.get_location_by_warehouse(id)
    return render_template('warehouses/locations.html', 
                         warehouse=warehouse,
                         locations=locations)

# 库位管理路由
@warehouses_bp.route('/locations/')
@login_required
@permission_required('location', 'read')
def location_list():
    """库位列表"""
    # 获取筛选条件
    filters = {
        'warehouse_id': request.args.get('warehouse_id', type=int),
        'location_code': request.args.get('location_code'),
        'location_name': request.args.get('location_name'),
        'location_type': request.args.get('location_type'),
        'status': request.args.get('status')
    }
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 获取库位列表
    pagination = LocationService.get_locations(filters, page, per_page)
    
    return render_template('warehouses/location_list.html', 
                         pagination=pagination,
                         filters=filters)

@warehouses_bp.route('/locations/create', methods=['GET', 'POST'])
@login_required
@permission_required('location', 'create')
def location_create():
    """创建库位"""
    form = WarehouseLocationForm()
    
    # 填充仓库选项
    from app.models.warehouse import Warehouse
    form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        data = form.data
        data.pop('submit')
        data.pop('csrf_token')
        data['created_by'] = current_user.id
        
        location = LocationService.create_location(data)
        flash('库位创建成功！', 'success')
        return redirect(url_for('warehouses.location_list'))
    
    return render_template('warehouses/location_form.html', form=form, title='创建库位')

@warehouses_bp.route('/locations/<int:id>')
@login_required
@permission_required('location', 'read')
def location_detail(id):
    """库位详情"""
    location = LocationService.get_location(id)
    if not location:
        flash('库位不存在', 'danger')
        return redirect(url_for('warehouses.location_list'))
    
    # 获取库位库存
    inventory = LocationService.get_inventory(id)
    utilization_rate = LocationService.get_utilization_rate(id)
    available_space = LocationService.get_available_space(id)
    
    # 获取库位中的批次
    batches = location.batches.all()
    
    return render_template('warehouses/location_detail.html', 
                         location=location,
                         inventory=inventory,
                         utilization_rate=utilization_rate,
                         available_space=available_space,
                         batches=batches)

@warehouses_bp.route('/locations/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('location', 'update')
def location_edit(id):
    """编辑库位"""
    location = LocationService.get_location(id)
    if not location:
        flash('库位不存在', 'danger')
        return redirect(url_for('warehouses.location_list'))
    
    form = WarehouseLocationForm(obj=location)
    
    # 填充仓库选项
    from app.models.warehouse import Warehouse
    form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        data = form.data
        data.pop('submit')
        data.pop('csrf_token')
        
        location = LocationService.update_location(id, data)
        flash('库位更新成功！', 'success')
        return redirect(url_for('warehouses.location_detail', id=id))
    
    return render_template('warehouses/location_form.html', form=form, title='编辑库位', location=location)

@warehouses_bp.route('/locations/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('location', 'delete')
def location_delete(id):
    """删除库位"""
    success = LocationService.delete_location(id)
    if success:
        flash('库位删除成功！', 'success')
    else:
        flash('库位删除失败，可能存在关联的批次', 'danger')
    return redirect(url_for('warehouses.location_list'))

# 库存管理路由
@warehouses_bp.route('/inventory/')
@login_required
@permission_required('inventory', 'read')
def inventory_overview():
    """库存概览"""
    # 获取所有仓库的库存统计
    from app.models.warehouse import Warehouse
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    
    inventory_stats = []
    for warehouse in warehouses:
        stats = InventoryService.get_inventory_statistics(warehouse.id)
        stats['warehouse'] = warehouse
        inventory_stats.append(stats)
    
    # 获取总统计
    total_stats = InventoryService.get_inventory_statistics()
    
    return render_template('warehouses/inventory_overview.html', 
                         inventory_stats=inventory_stats,
                         total_stats=total_stats)

@warehouses_bp.route('/inventory/warehouse/<int:id>')
@login_required
@permission_required('inventory', 'read')
def inventory_warehouse(id):
    """仓库库存"""
    warehouse = WarehouseService.get_warehouse(id)
    if not warehouse:
        flash('仓库不存在', 'danger')
        return redirect(url_for('warehouses.inventory_overview'))
    
    inventory = InventoryService.get_inventory_by_warehouse(id)
    stats = InventoryService.get_inventory_statistics(id)
    
    return render_template('warehouses/inventory_warehouse.html', 
                         warehouse=warehouse,
                         inventory=inventory,
                         stats=stats)

@warehouses_bp.route('/inventory/location/<int:id>')
@login_required
@permission_required('inventory', 'read')
def inventory_location(id):
    """库位库存"""
    location = LocationService.get_location(id)
    if not location:
        flash('库位不存在', 'danger')
        return redirect(url_for('warehouses.inventory_overview'))
    
    inventory = InventoryService.get_inventory_by_location(id)
    
    return render_template('warehouses/inventory_location.html', 
                         location=location,
                         inventory=inventory)

@warehouses_bp.route('/inventory/adjust', methods=['GET', 'POST'])
@login_required
@permission_required('inventory', 'update')
def inventory_adjust():
    """库存调整"""
    form = InventoryAdjustForm()
    
    # 填充仓库选项
    from app.models.warehouse import Warehouse
    form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).all()]
    
    # 填充库位选项（根据仓库动态加载）
    if request.method == 'GET':
        form.location_id.choices = [(0, '请选择仓库')]
        form.spare_part_id.choices = [(0, '请选择库位')]
    elif request.method == 'POST' and 'warehouse_id' in request.form:
        warehouse_id = int(request.form['warehouse_id'])
        locations = LocationService.get_location_by_warehouse(warehouse_id)
        form.location_id.choices = [(l.id, l.location_code) for l in locations]
        form.spare_part_id.choices = [(0, '请选择库位')]
    
    if form.validate_on_submit():
        try:
            InventoryService.adjust_inventory(
                form.warehouse_id.data,
                form.location_id.data,
                form.spare_part_id.data,
                form.quantity.data,
                current_user.id,
                form.remark.data
            )
            flash('库存调整成功！', 'success')
            return redirect(url_for('warehouses.inventory_overview'))
        except Exception as e:
            flash(f'库存调整失败：{str(e)}', 'danger')
    
    return render_template('warehouses/inventory_adjust.html', form=form)

@warehouses_bp.route('/inventory/transfer', methods=['GET', 'POST'])
@login_required
@permission_required('inventory', 'update')
def inventory_transfer():
    """库存调拨"""
    form = InventoryTransferForm()
    
    # 填充仓库选项
    from app.models.warehouse import Warehouse
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    warehouse_choices = [(w.id, w.name) for w in warehouses]
    form.from_warehouse_id.choices = warehouse_choices
    form.to_warehouse_id.choices = warehouse_choices
    
    # 填充库位选项（根据仓库动态加载）
    if request.method == 'GET':
        form.from_location_id.choices = [(0, '请选择源仓库')]
        form.to_location_id.choices = [(0, '请选择目标仓库')]
        form.spare_part_id.choices = [(0, '请选择源库位')]
    
    if form.validate_on_submit():
        try:
            InventoryService.transfer_inventory(
                form.from_warehouse_id.data,
                form.from_location_id.data,
                form.to_warehouse_id.data,
                form.to_location_id.data,
                form.spare_part_id.data,
                form.quantity.data,
                current_user.id,
                form.remark.data
            )
            flash('库存调拨成功！', 'success')
            return redirect(url_for('warehouses.inventory_overview'))
        except Exception as e:
            flash(f'库存调拨失败：{str(e)}', 'danger')
    
    return render_template('warehouses/inventory_transfer.html', form=form)

# 操作记录路由
@warehouses_bp.route('/operations/')
@login_required
@permission_required('operation', 'read')
def operations_list():
    """操作记录列表"""
    # 获取筛选条件
    filters = {
        'warehouse_id': request.args.get('warehouse_id', type=int),
        'operation_type': request.args.get('operation_type'),
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'user_id': request.args.get('user_id', type=int)
    }
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 获取操作记录
    pagination = OperationService.get_operations(filters, page, per_page)
    
    return render_template('warehouses/operations_list.html', 
                         pagination=pagination,
                         filters=filters)

@warehouses_bp.route('/operations/<int:id>')
@login_required
@permission_required('operation', 'read')
def operation_detail(id):
    """操作详情"""
    operation = OperationService.get_operation(id)
    if not operation:
        flash('操作记录不存在', 'danger')
        return redirect(url_for('warehouses.operations_list'))
    
    return render_template('warehouses/operation_detail.html', operation=operation)

# 报表分析路由
@warehouses_bp.route('/reports/warehouse-utilization')
@login_required
@permission_required('report', 'read')
def report_warehouse_utilization():
    """仓库利用率报表"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    
    report_data = ReportService.generate_warehouse_utilization_report(warehouse_id)
    
    return render_template('warehouses/report_warehouse_utilization.html', 
                         report_data=report_data,
                         warehouse_id=warehouse_id)

@warehouses_bp.route('/reports/inventory-flow')
@login_required
@permission_required('report', 'read')
def report_inventory_flow():
    """库存流动报表"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    report_data = ReportService.generate_inventory_flow_report(warehouse_id, start_date, end_date)
    
    return render_template('warehouses/report_inventory_flow.html', 
                         report_data=report_data,
                         warehouse_id=warehouse_id,
                         start_date=start_date,
                         end_date=end_date)

@warehouses_bp.route('/reports/inventory-value')
@login_required
@permission_required('report', 'read')
def report_inventory_value():
    """库存价值报表"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    
    report_data = ReportService.generate_inventory_value_report(warehouse_id)
    
    return render_template('warehouses/report_inventory_value.html', 
                         report_data=report_data,
                         warehouse_id=warehouse_id)

@warehouses_bp.route('/reports/inventory-turnover')
@login_required
@permission_required('report', 'read')
def report_inventory_turnover():
    """库存周转率报表"""
    warehouse_id = request.args.get('warehouse_id', type=int)
    period_days = request.args.get('period_days', 30, type=int)
    
    report_data = ReportService.generate_inventory_turnover_report(warehouse_id, period_days)
    
    return render_template('warehouses/report_inventory_turnover.html', 
                         report_data=report_data,
                         warehouse_id=warehouse_id,
                         period_days=period_days)

# API 接口
@warehouses_bp.route('/api/warehouses')
@login_required
def api_warehouses():
    """获取仓库列表 API"""
    warehouses = WarehouseService.get_warehouses()
    return jsonify([{
        'id': w.id,
        'name': w.name,
        'code': w.code
    } for w in warehouses.items])

@warehouses_bp.route('/api/locations/<int:warehouse_id>')
@login_required
def api_locations(warehouse_id):
    """获取仓库的库位 API"""
    locations = LocationService.get_location_by_warehouse(warehouse_id)
    return jsonify([{
        'id': l.id,
        'location_code': l.location_code,
        'location_name': l.location_name
    } for l in locations])

@warehouses_bp.route('/api/spare-parts/<int:location_id>')
@login_required
def api_spare_parts(location_id):
    """获取库位的备件 API"""
    inventory = InventoryService.get_inventory_by_location(location_id)
    spare_parts = []
    for batch in inventory:
        if batch.spare_part not in spare_parts:
            spare_parts.append(batch.spare_part)
    return jsonify([{
        'id': sp.id,
        'part_code': sp.part_code,
        'name': sp.name
    } for sp in spare_parts])


@warehouses_bp.route('/quick-create-warehouses/')
@login_required
def quick_create_warehouses():
    """快速创建6个示例仓库"""
    
    # 先删除已有的不完整仓库
    Warehouse.query.delete()
    db.session.commit()
    
    # 获取当前用户作为管理员
    manager_id = current_user.id
    
    # 要创建的6个仓库数据
    warehouses_data = [
        {
            'name': '主仓库',
            'code': 'WH-MAIN',
            'type': 'general',
            'manager_id': manager_id,
            'address': '上海市浦东新区张江高科技园区科苑路88号',
            'area': 1000.0,
            'capacity': 5000,
            'phone': '021-55550001',
            'description': '主要仓储中心，存放常用备件',
            'is_active': True
        },
        {
            'name': '冷藏仓库',
            'code': 'WH-COLD',
            'type': 'cold',
            'manager_id': manager_id,
            'address': '上海市浦东新区张江高科技园区科苑路88号B区',
            'area': 500.0,
            'capacity': 1000,
            'phone': '021-55550002',
            'description': '冷藏仓库，存放需低温保存的备件',
            'is_active': True
        },
        {
            'name': '危险品仓库',
            'code': 'WH-HAZARD',
            'type': 'hazardous',
            'manager_id': manager_id,
            'address': '上海市浦东新区化工园区危险物品管理区',
            'area': 300.0,
            'capacity': 500,
            'phone': '021-55550003',
            'description': '危险品专用仓库',
            'is_active': True
        },
        {
            'name': '贵重物品仓库',
            'code': 'WH-VALUABLE',
            'type': 'valuable',
            'manager_id': manager_id,
            'address': '上海市浦东新区陆家嘴金融区保险库',
            'area': 200.0,
            'capacity': 200,
            'phone': '021-55550004',
            'description': '贵重物品专用仓库，安保级别高',
            'is_active': True
        },
        {
            'name': '备件分拨中心',
            'code': 'WH-DISTRIBUTION',
            'type': 'general',
            'manager_id': manager_id,
            'address': '上海市青浦区物流园区',
            'area': 2000.0,
            'capacity': 10000,
            'phone': '021-55550005',
            'description': '区域分拨中心，负责周边地区备件配送',
            'is_active': True
        },
        {
            'name': '备用仓库',
            'code': 'WH-BACKUP',
            'type': 'general',
            'manager_id': manager_id,
            'address': '江苏省苏州市工业园区',
            'area': 800.0,
            'capacity': 3000,
            'phone': '0512-55550001',
            'description': '备用仓库，应急使用',
            'is_active': True
        }
    ]
    
    # 创建仓库
    created_count = 0
    for data in warehouses_data:
        WarehouseService.create_warehouse(data)
        created_count += 1
    
    flash('成功创建 ' + str(created_count) + ' 个仓库！', 'success')
    return redirect(url_for('warehouses.index'))
