"""
设备管理模块路由
支持同方威视车辆扫描设备的全生命周期管理
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.equipment import Equipment, EquipmentSpecs
from app.models.equipment_extensions import EquipmentStatusHistory
from app.models.maintenance import MaintenanceOrder
from app.models.department import Department
from app.models.supplier import Supplier
from app.extensions import db
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_, func

equipment_bp = Blueprint('equipment', __name__, url_prefix='/equipment')


@equipment_bp.route('/')
@login_required
def index():
    """设备列表页面"""
    # 获取筛选条件
    keyword = request.args.get('keyword', '').strip()
    series = request.args.get('series', '').strip()
    status = request.args.get('status', '').strip()
    department_id = request.args.get('department_id', type=int)
    
    # 构建查询
    query = Equipment.query
    
    if keyword:
        query = query.filter(
            or_(
                Equipment.equipment_code.like(f'%{keyword}%'),
                Equipment.name.like(f'%{keyword}%'),
                Equipment.model.like(f'%{keyword}%'),
                Equipment.serial_number.like(f'%{keyword}%')
            )
        )
    
    if series:
        query = query.filter(Equipment.series == series)
    
    if status:
        query = query.filter(Equipment.status == status)
    
    if department_id:
        query = query.filter(Equipment.department_id == department_id)
    
    # 分页
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = query.order_by(Equipment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取统计信息
    stats = {
        'total': Equipment.query.count(),
        'running': Equipment.query.filter_by(status='running').count(),
        'stopped': Equipment.query.filter_by(status='stopped').count(),
        'maintenance': Equipment.query.filter_by(status='maintenance').count(),
        'scrapped': Equipment.query.filter_by(status='scrapped').count()
    }
    
    # 获取部门和供应商列表（用于筛选）
    departments = Department.query.filter_by(is_active=True).all()
    suppliers = Supplier.query.filter_by(is_active=True).all()
    
    # 设备系列选项
    series_options = [
        {'value': 'FS', 'label': 'FS 系列 - 固定式/快速通道'},
        {'value': 'MT', 'label': 'MT 系列 - 车载移动式'},
        {'value': 'CS', 'label': 'CS 系列 - 小型车辆检查'},
        {'value': 'MB', 'label': 'MB 系列 - 组合移动式'},
        {'value': 'FG', 'label': 'FG 系列 - 固定式集装箱'},
        {'value': 'PB', 'label': 'PB 系列 - 多用途移动式'},
        {'value': 'RF', 'label': 'RF 系列 - 铁路检查'}
    ]
    
    # 状态选项
    status_options = [
        {'value': 'running', 'label': '运行中'},
        {'value': 'stopped', 'label': '停机'},
        {'value': 'maintenance', 'label': '维修中'},
        {'value': 'scrapped', 'label': '已报废'}
    ]
    
    return render_template('equipment/index.html',
                         pagination=pagination,
                         stats=stats,
                         departments=departments,
                         suppliers=suppliers,
                         series_options=series_options,
                         status_options=status_options,
                         current_filters={
                             'keyword': keyword,
                             'series': series,
                             'status': status,
                             'department_id': department_id
                         })


@equipment_bp.route('/create')
@login_required
def create():
    """创建设备页面"""
    departments = Department.query.filter_by(is_active=True).all()
    suppliers = Supplier.query.filter_by(is_active=True).all()
    
    series_options = [
        {'value': 'FS', 'label': 'FS 系列'},
        {'value': 'MT', 'label': 'MT 系列'},
        {'value': 'CS', 'label': 'CS 系列'},
        {'value': 'MB', 'label': 'MB 系列'},
        {'value': 'FG', 'label': 'FG 系列'},
        {'value': 'PB', 'label': 'PB 系列'},
        {'value': 'RF', 'label': 'RF 系列'}
    ]
    
    # 预定义型号数据
    model_data = {
        'FS': [
            {'model': 'FS6000', 'name': '固定式快速检查系统'},
            {'model': 'FS6000MF', 'name': '多视角固定式检查系统'},
            {'model': 'FS0200BX', 'name': '背散射检查系统'}
        ],
        'MT': [
            {'model': 'MT1213LT', 'name': '车载移动式检查系统 (低能)'},
            {'model': 'MT1213LH', 'name': '车载移动式检查系统 (高能)'},
            {'model': 'MT1213LC', 'name': '车载移动式检查系统 (紧凑型)'},
            {'model': 'MT1213DE', 'name': '车载移动式检查系统 (出口型)'}
        ],
        'CS': [
            {'model': 'CS0300T', 'name': '小型车辆检查系统'},
            {'model': 'CS1000T', 'name': '小型车辆检查系统 (增强型)'},
            {'model': 'CS0200T', 'name': '小型车辆检查系统 (紧凑型)'},
            {'model': 'CS0300TS', 'name': '小型车辆检查系统 (高分辨率)'}
        ],
        'MB': [
            {'model': 'MB1215CV', 'name': '组合移动式集装箱检查系统'}
        ],
        'FG': [
            {'model': 'FG9000DE', 'name': '固定式集装箱检查系统'}
        ]
    }
    
    return render_template('equipment/create.html',
                         departments=departments,
                         suppliers=suppliers,
                         series_options=series_options,
                         model_data=model_data)


@equipment_bp.route('/save', methods=['POST'])
@login_required
def save():
    """保存设备"""
    try:
        # 创建设备
        equipment = Equipment()
        equipment.equipment_code = request.form.get('equipment_code')
        equipment.name = request.form.get('name')
        equipment.model = request.form.get('model')
        equipment.series = request.form.get('series')
        equipment.category = request.form.get('category')
        equipment.manufacturer = request.form.get('manufacturer', '同方威视')
        equipment.serial_number = request.form.get('serial_number')
        equipment.department_id = request.form.get('department_id', type=int)
        equipment.location = request.form.get('location')
        equipment.install_date = datetime.strptime(request.form.get('install_date'), '%Y-%m-%d') if request.form.get('install_date') else None
        equipment.status = request.form.get('status', 'running')
        equipment.purchase_date = datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d') if request.form.get('purchase_date') else None
        equipment.warranty_expiry = datetime.strptime(request.form.get('warranty_expiry'), '%Y-%m-%d') if request.form.get('warranty_expiry') else None
        equipment.supplier_id = request.form.get('supplier_id', type=int)
        equipment.purchase_price = request.form.get('purchase_price', type=float)
        equipment.responsible_person = request.form.get('responsible_person')
        equipment.remark = request.form.get('remark')
        equipment.is_active = request.form.get('is_active') == 'on'
        equipment.created_by = current_user.id
        
        db.session.add(equipment)
        db.session.flush()
        
        # 创建技术参数
        if request.form.get('radiation_source'):
            specs = EquipmentSpecs()
            specs.equipment_id = equipment.id
            specs.radiation_source = request.form.get('radiation_source')
            specs.energy = request.form.get('energy')
            specs.penetration = request.form.get('penetration')
            specs.resolution = request.form.get('resolution')
            specs.check_speed = request.form.get('check_speed')
            specs.channel_size = request.form.get('channel_size')
            specs.imaging_mode = request.form.get('imaging_mode')
            specs.shielding_mode = request.form.get('shielding_mode')
            db.session.add(specs)
        
        db.session.commit()
        flash('设备创建成功！', 'success')
        return redirect(url_for('equipment.index'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'创建设备失败：{str(e)}', 'danger')
        return redirect(url_for('equipment.create'))


@equipment_bp.route('/<int:id>')
@login_required
def view(id):
    """设备详情页面"""
    equipment = Equipment.query.get_or_404(id)
    
    # 获取维修记录统计
    maintenance_stats = {
        'total': MaintenanceOrder.query.filter_by(equipment_id=id).count(),
        'pending': MaintenanceOrder.query.filter_by(equipment_id=id, status='pending').count(),
        'in_progress': MaintenanceOrder.query.filter_by(equipment_id=id, status='in_progress').count(),
        'completed': MaintenanceOrder.query.filter_by(equipment_id=id, status='completed').count()
    }
    
    # 获取最近的维修记录
    recent_maintenance = MaintenanceOrder.query.filter_by(
        equipment_id=id
    ).order_by(MaintenanceOrder.created_at.desc()).limit(5).all()
    
    return render_template('equipment/view.html',
                         equipment=equipment,
                         maintenance_stats=maintenance_stats,
                         recent_maintenance=recent_maintenance)


@equipment_bp.route('/<int:id>/edit')
@login_required
def edit(id):
    """编辑设备页面"""
    equipment = Equipment.query.get_or_404(id)
    departments = Department.query.filter_by(is_active=True).all()
    suppliers = Supplier.query.filter_by(is_active=True).all()
    
    series_options = [
        {'value': 'FS', 'label': 'FS 系列'},
        {'value': 'MT', 'label': 'MT 系列'},
        {'value': 'CS', 'label': 'CS 系列'},
        {'value': 'MB', 'label': 'MB 系列'},
        {'value': 'FG', 'label': 'FG 系列'},
        {'value': 'PB', 'label': 'PB 系列'},
        {'value': 'RF', 'label': 'RF 系列'}
    ]
    
    return render_template('equipment/edit.html',
                         equipment=equipment,
                         departments=departments,
                         suppliers=suppliers,
                         series_options=series_options)


@equipment_bp.route('/<int:id>/update', methods=['POST'])
@login_required
def update(id):
    """更新设备"""
    try:
        equipment = Equipment.query.get_or_404(id)
        
        equipment.equipment_code = request.form.get('equipment_code')
        equipment.name = request.form.get('name')
        equipment.model = request.form.get('model')
        equipment.series = request.form.get('series')
        equipment.category = request.form.get('category')
        equipment.manufacturer = request.form.get('manufacturer')
        equipment.serial_number = request.form.get('serial_number')
        equipment.department_id = request.form.get('department_id', type=int)
        equipment.location = request.form.get('location')
        equipment.install_date = datetime.strptime(request.form.get('install_date'), '%Y-%m-%d') if request.form.get('install_date') else None
        equipment.status = request.form.get('status')
        equipment.purchase_date = datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d') if request.form.get('purchase_date') else None
        equipment.warranty_expiry = datetime.strptime(request.form.get('warranty_expiry'), '%Y-%m-%d') if request.form.get('warranty_expiry') else None
        equipment.supplier_id = request.form.get('supplier_id', type=int)
        equipment.purchase_price = request.form.get('purchase_price', type=float)
        equipment.responsible_person = request.form.get('responsible_person')
        equipment.remark = request.form.get('remark')
        equipment.is_active = request.form.get('is_active') == 'on'
        equipment.updated_by = current_user.id
        
        # 更新技术参数
        specs = EquipmentSpecs.query.filter_by(equipment_id=id).first()
        if not specs:
            specs = EquipmentSpecs()
            specs.equipment_id = id
            db.session.add(specs)
        
        specs.radiation_source = request.form.get('radiation_source')
        specs.energy = request.form.get('energy')
        specs.penetration = request.form.get('penetration')
        specs.resolution = request.form.get('resolution')
        specs.check_speed = request.form.get('check_speed')
        specs.channel_size = request.form.get('channel_size')
        specs.imaging_mode = request.form.get('imaging_mode')
        specs.shielding_mode = request.form.get('shielding_mode')
        
        db.session.commit()
        flash('设备更新成功！', 'success')
        return redirect(url_for('equipment.view', id=id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'更新设备失败：{str(e)}', 'danger')
        return redirect(url_for('equipment.edit', id=id))


@equipment_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """删除设备"""
    try:
        equipment = Equipment.query.get_or_404(id)
        
        # 检查是否有关联的维修记录
        if equipment.maintenance_orders.count() > 0:
            flash('无法删除设备，存在关联的维修记录', 'danger')
            return redirect(url_for('equipment.view', id=id))
        
        # 删除技术参数
        if equipment.specs:
            db.session.delete(equipment.specs)
        
        db.session.delete(equipment)
        db.session.commit()
        flash('设备删除成功！', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'删除设备失败：{str(e)}', 'danger')
    
    return redirect(url_for('equipment.index'))


@equipment_bp.route('/api/list')
@login_required
def api_list():
    """设备列表 API"""
    keyword = request.args.get('keyword', '').strip()
    series = request.args.get('series', '').strip()
    status = request.args.get('status', '').strip()
    
    query = Equipment.query
    
    if keyword:
        query = query.filter(
            or_(
                Equipment.equipment_code.like(f'%{keyword}%'),
                Equipment.name.like(f'%{keyword}%'),
                Equipment.model.like(f'%{keyword}%')
            )
        )
    
    if series:
        query = query.filter(Equipment.series == series)
    
    if status:
        query = query.filter(Equipment.status == status)
    
    equipments = query.order_by(Equipment.created_at.desc()).all()
    
    result = []
    for eq in equipments:
        item = {
            'id': eq.id,
            'equipment_code': eq.equipment_code,
            'name': eq.name,
            'model': eq.model,
            'series': eq.series,
            'status': eq.status,
            'department': eq.department.name if eq.department else None,
            'responsible_person': eq.responsible_person,
            'location': eq.location,
            'created_at': eq.created_at.strftime('%Y-%m-%d %H:%M:%S') if eq.created_at else None
        }
        result.append(item)
    
    return jsonify(result)


@equipment_bp.route('/api/stats')
@login_required
def api_stats():
    """设备统计 API"""
    stats = {
        'total': Equipment.query.count(),
        'running': Equipment.query.filter_by(status='running').count(),
        'stopped': Equipment.query.filter_by(status='stopped').count(),
        'maintenance': Equipment.query.filter_by(status='maintenance').count(),
        'scrapped': Equipment.query.filter_by(status='scrapped').count()
    }
    
    # 按系列统计
    series_stats = db.session.query(
        Equipment.series,
        db.func.count(Equipment.id)
    ).group_by(Equipment.series).all()
    
    stats['by_series'] = {series: count for series, count in series_stats}
    
    return jsonify(stats)


@equipment_bp.route('/dashboard')
@login_required
def dashboard():
    """设备仪表盘 - 高德地图（独立版本）"""
    # 获取统计信息
    stats = {
        'total': Equipment.query.count(),
        'running': Equipment.query.filter_by(status='running').count(),
        'stopped': Equipment.query.filter_by(status='stopped').count(),
        'maintenance': Equipment.query.filter_by(status='maintenance').count(),
        'scrapped': Equipment.query.filter_by(status='scrapped').count()
    }
    
    # 按系列统计
    series_stats = db.session.query(
        Equipment.series,
        db.func.count(Equipment.id)
    ).group_by(Equipment.series).all()
    
    stats['by_series'] = {series: count for series, count in series_stats}
    
    return render_template('equipment/dashboard.html', stats=stats)


@equipment_bp.route('/test-map')
def test_map():
    """测试 Leaflet 地图是否正常加载"""
    return render_template('equipment/test_leaflet.html')


@equipment_bp.route('/test-amap')
def test_amap():
    """测试高德地图是否正常加载"""
    return render_template('equipment/test_amap.html')


@equipment_bp.route('/test-simple-amap')
def test_simple_amap():
    """简单的高德地图测试页面"""
    return render_template('equipment/test_simple_amap.html')


@equipment_bp.route('/<int:id>/change-status', methods=['POST'])
@login_required
def change_status(id):
    """变更设备状态"""
    try:
        equipment = Equipment.query.get_or_404(id)
        new_status = request.form.get('new_status')
        change_reason = request.form.get('change_reason', '')
        
        if new_status not in ['running', 'stopped', 'maintenance', 'scrapped']:
            flash('无效的状态', 'danger')
            return redirect(url_for('equipment.view', id=id))
        
        # 记录状态变更历史
        old_status = equipment.status
        if old_status != new_status:
            history = EquipmentStatusHistory()
            history.equipment_id = id
            history.old_status = old_status
            history.new_status = new_status
            history.change_reason = change_reason
            history.changed_by = current_user.id
            db.session.add(history)
        
        # 更新设备状态
        equipment.status = new_status
        equipment.updated_at = datetime.now()
        db.session.commit()
        
        flash('设备状态变更成功！', 'success')
        return redirect(url_for('equipment.view', id=id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'状态变更失败：{str(e)}', 'danger')
        return redirect(url_for('equipment.view', id=id))


@equipment_bp.route('/<int:id>/status-history')
@login_required
def status_history(id):
    """获取设备状态变更历史"""
    equipment = Equipment.query.get_or_404(id)
    histories = EquipmentStatusHistory.query.filter_by(
        equipment_id=id
    ).order_by(EquipmentStatusHistory.created_at.desc()).all()
    
    result = []
    for h in histories:
        status_labels = {
            'running': '运行中',
            'stopped': '停机',
            'maintenance': '维修中',
            'scrapped': '已报废'
        }
        result.append({
            'id': h.id,
            'old_status': status_labels.get(h.old_status, h.old_status),
            'new_status': status_labels.get(h.new_status, h.new_status),
            'change_reason': h.change_reason,
            'changed_by': h.changed_by,
            'created_at': h.created_at.strftime('%Y-%m-%d %H:%M:%S') if h.created_at else None
        })
    
    return jsonify(result)


@equipment_bp.route('/api/overview-stats')
@login_required
def overview_stats():
    """获取设备概览统计数据"""
    from sqlalchemy import func
    
    today = date.today()
    
    # 基础统计
    total = Equipment.query.count()
    running = Equipment.query.filter_by(status='running').count()
    stopped = Equipment.query.filter_by(status='stopped').count()
    maintenance = Equipment.query.filter_by(status='maintenance').count()
    scrapped = Equipment.query.filter_by(status='scrapped').count()
    
    # 保修到期预警（30天内到期）
    thirty_days_later = today + timedelta(days=30)
    warranty_soon = Equipment.query.filter(
        Equipment.warranty_expiry.isnot(None),
        Equipment.warranty_expiry <= thirty_days_later,
        Equipment.warranty_expiry >= today
    ).count()
    
    # 已过保
    warranty_expired = Equipment.query.filter(
        Equipment.warranty_expiry.isnot(None),
        Equipment.warranty_expiry < today
    ).count()
    
    # 按部门统计
    dept_stats = db.session.query(
        Department.name,
        func.count(Equipment.id)
    ).join(
        Department, Equipment.department_id == Department.id
    ).group_by(
        Department.name
    ).all()
    
    # 按系列统计
    series_stats = db.session.query(
        Equipment.series,
        func.count(Equipment.id)
    ).filter(
        Equipment.series.isnot(None)
    ).group_by(
        Equipment.series
    ).all()
    
    return jsonify({
        'total': total,
        'running': running,
        'stopped': stopped,
        'maintenance': maintenance,
        'scrapped': scrapped,
        'warranty_soon': warranty_soon,
        'warranty_expired': warranty_expired,
        'by_department': {name: count for name, count in dept_stats},
        'by_series': {series: count for series, count in series_stats}
    })


@equipment_bp.route('/direct-amap-test')
def direct_amap_test():
    """直接的高德地图测试页面"""
    return render_template('equipment/direct_amap_test.html')


@equipment_bp.route('/api/locations')
@login_required
def api_locations():
    """获取所有设备的地理位置信息（用于地图展示）"""
    # 获取筛选参数
    filter_site_name = request.args.get('site_name', '')
    filter_series = request.args.get('series', '')
    filter_category = request.args.get('category', '')
    filter_province = request.args.get('province', '')
    filter_city = request.args.get('city', '')
    
    # 构建查询
    query = Equipment.query.filter(
        Equipment.latitude.isnot(None),
        Equipment.longitude.isnot(None)
    )
    
    # 按站点名称筛选（包含）
    if filter_site_name:
        query = query.filter(Equipment.site_name.contains(filter_site_name))
    
    # 按设备系列筛选
    if filter_series:
        query = query.filter(Equipment.series == filter_series)
    
    # 按设备类别筛选
    if filter_category:
        query = query.filter(Equipment.category == filter_category)
    
    # 按省份/城市筛选（从地址中解析）
    if filter_province or filter_city:
        addr_filter = (Equipment.map_address.isnot(None) | Equipment.location.isnot(None))
        query = query.filter(addr_filter)
        
        if filter_province:
            query = query.filter(
                (Equipment.map_address.contains(filter_province)) |
                (Equipment.location.contains(filter_province))
            )
        
        if filter_city:
            query = query.filter(
                (Equipment.map_address.contains(filter_city)) |
                (Equipment.location.contains(filter_city))
            )
    
    equipments = query.all()
    
    # 统计各状态数量
    total_count = Equipment.query.count()
    running_count = Equipment.query.filter_by(status='running').count()
    stopped_count = Equipment.query.filter_by(status='stopped').count()
    maintenance_count = Equipment.query.filter_by(status='maintenance').count()
    scrapped_count = Equipment.query.filter_by(status='scrapped').count()
    
    # 获取所有筛选选项
    all_site_names = db.session.query(Equipment.site_name).filter(
        Equipment.site_name.isnot(None)
    ).distinct().all()
    all_series = db.session.query(Equipment.series).filter(
        Equipment.series.isnot(None)
    ).distinct().all()
    all_categories = db.session.query(Equipment.category).filter(
        Equipment.category.isnot(None)
    ).distinct().all()
    
    # 获取地址中的省份和城市
    all_locations = db.session.query(Equipment.map_address, Equipment.location).filter(
        (Equipment.map_address.isnot(None)) | (Equipment.location.isnot(None))
    ).all()
    
    # 解析省份和城市（简单实现）
    provinces = set()
    cities = set()
    for loc in all_locations:
        addr = loc[0] or loc[1] or ''
        # 简单识别省份和城市
        province_keywords = ['省', '北京', '上海', '天津', '重庆']
        city_keywords = ['市', '州', '盟', '地区']
        
        for keyword in province_keywords:
            if keyword in addr:
                # 简单提取
                for province in ['北京', '上海', '天津', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江', 
                                '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南',
                                '广东', '广西', '海南', '四川', '贵州', '云南', '陕西', '甘肃', '青海',
                                '内蒙古', '新疆', '西藏', '宁夏', '台湾', '香港', '澳门']:
                    if province in addr:
                        provinces.add(province)
                        break
        
        if '市' in addr:
            idx = addr.find('市')
            if idx > 0:
                city = addr[max(0, idx-3):idx+1]
                if city and len(city) <= 6:
                    cities.add(city)
    
    result = []
    for eq in equipments:
        # 根据状态设置不同的标记配置
        if eq.status == 'running':
            color = '#52c41a'
            icon = 'check-circle'
            status_label = '运行中'
        elif eq.status == 'stopped':
            color = '#86909c'
            icon = 'pause-circle'
            status_label = '停机'
        elif eq.status == 'maintenance':
            color = '#faad14'
            icon = 'tool'
            status_label = '维修中'
        else:
            color = '#ff4d4f'
            icon = 'close-circle'
            status_label = '已报废'
        
        # 解析地址获取城市信息
        full_address = eq.map_address or eq.location or ''
        city = ''
        if '市' in full_address:
            idx = full_address.find('市')
            if idx > 0:
                city = full_address[max(0, idx-3):idx+1]
        
        item = {
            'id': eq.id,
            'equipment_code': eq.equipment_code,
            'name': eq.name,
            'model': eq.model,
            'series': eq.series,
            'category': eq.category,
            'status': eq.status,
            'status_label': status_label,
            'latitude': float(eq.latitude),
            'longitude': float(eq.longitude),
            'map_address': full_address,
            'city': city,
            'site_name': eq.site_name,
            'color': color,
            'icon': icon,
            'department': eq.department.name if eq.department else None,
            'responsible_person': eq.responsible_person,
            'contact_person': eq.responsible_person,
            'contact_phone': getattr(eq, 'contact_phone', None)
        }
        result.append(item)
    
    return jsonify({
        'total_count': total_count,
        'running_count': running_count,
        'stopped_count': stopped_count,
        'maintenance_count': maintenance_count,
        'scrapped_count': scrapped_count,
        'locations': result,
        'site_names': [s[0] for s in all_site_names if s[0]],
        'series_options': [s[0] for s in all_series if s[0]],
        'category_options': [c[0] for c in all_categories if c[0]],
        'province_options': sorted(list(provinces)),
        'city_options': sorted(list(cities))
    })
