
"""
仓库AI管理路由
智能仓库初始化、库位分配等
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Warehouse
from app.services.warehouse_ai_service import WarehouseAIService

warehouses_ai_bp = Blueprint('warehouses_ai', __name__, url_prefix='/warehouses/ai')
ai_service = WarehouseAIService()


@warehouses_ai_bp.route('/quick-create-warehouses/', methods=['GET'])
@login_required
def quick_create_warehouses():
    """快速创建6个示例仓库"""
    
    # 检查是否已有仓库
    existing_count = Warehouse.query.count()
    if existing_count &gt; 0:
        flash('已存在 ' + str(existing_count) + ' 个仓库，跳过创建', 'info')
        return redirect(url_for('warehouses.index'))
    
    # 要创建的6个仓库数据
    warehouses_data = [
        {
            'name': '主仓库',
            'code': 'WH-MAIN',
            'type': 'general',
            'address': '上海市浦东新区张江高科技园区科苑路88号',
            'area': 1000.0,
            'capacity': 5000,
            'phone': '021-55550001',
            'description': '主要仓储中心，存放常用备件'
        },
        {
            'name': '冷藏仓库',
            'code': 'WH-COLD',
            'type': 'cold',
            'address': '上海市浦东新区张江高科技园区科苑路88号B区',
            'area': 500.0,
            'capacity': 1000,
            'phone': '021-55550002',
            'description': '冷藏仓库，存放需低温保存的备件'
        },
        {
            'name': '危险品仓库',
            'code': 'WH-HAZARD',
            'type': 'hazardous',
            'address': '上海市浦东新区化工园区危险物品管理区',
            'area': 300.0,
            'capacity': 500,
            'phone': '021-55550003',
            'description': '危险品专用仓库'
        },
        {
            'name': '贵重物品仓库',
            'code': 'WH-VALUABLE',
            'type': 'valuable',
            'address': '上海市浦东新区陆家嘴金融区保险库',
            'area': 200.0,
            'capacity': 200,
            'phone': '021-55550004',
            'description': '贵重物品专用仓库，安保级别高'
        },
        {
            'name': '备件分拨中心',
            'code': 'WH-DISTRIBUTION',
            'type': 'general',
            'address': '上海市青浦区物流园区',
            'area': 2000.0,
            'capacity': 10000,
            'phone': '021-55550005',
            'description': '区域分拨中心，负责周边地区备件配送'
        },
        {
            'name': '备用仓库',
            'code': 'WH-BACKUP',
            'type': 'general',
            'address': '江苏省苏州市工业园区',
            'area': 800.0,
            'capacity': 3000,
            'phone': '0512-55550001',
            'description': '备用仓库，应急使用'
        }
    ]
    
    # 创建仓库
    created_count = 0
    for data in warehouses_data:
        warehouse = Warehouse(
            name=data['name'],
            code=data['code'],
            type=data['type'],
            address=data['address'],
            area=data['area'],
            capacity=data['capacity'],
            phone=data['phone'],
            description=data['description'],
            is_active=True
        )
        db.session.add(warehouse)
        created_count += 1
    
    db.session.commit()
    flash('成功创建 ' + str(created_count) + ' 个仓库！', 'success')
    return redirect(url_for('warehouses.index'))


@warehouses_ai_bp.route('/init/&lt;int:warehouse_id&gt;/', methods=['GET', 'POST'])
@login_required
def init_warehouse(warehouse_id):
    """
    智能初始化仓库页面
    """
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    
    if request.method == 'POST':
        # 执行初始化
        result = ai_service.init_warehouse(warehouse_id, current_user.id)
        
        if result['success']:
            flash('仓库智能初始化成功！', 'success')
            return render_template('warehouses/init_result.html', 
                                  warehouse=warehouse, 
                                  result=result)
        else:
            flash('初始化失败：' + result.get('error', '未知错误'), 'danger')
    
    # GET请求 - 显示预览页面
    analysis_result = ai_service.analyze_spare_parts(warehouse_id)
    zone_plan = ai_service.generate_zone_plan(analysis_result, warehouse_id)
    
    return render_template('warehouses/init_preview.html',
                          warehouse=warehouse,
                          analysis_result=analysis_result,
                          zone_plan=zone_plan)


@warehouses_ai_bp.route('/api/analyze/&lt;int:warehouse_id&gt;/', methods=['GET'])
@login_required
def api_analyze(warehouse_id):
    """
    API: 分析备件数据
    """
    try:
        result = ai_service.analyze_spare_parts(warehouse_id)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@warehouses_ai_bp.route('/api/init/&lt;int:warehouse_id&gt;/', methods=['POST'])
@login_required
def api_init_warehouse(warehouse_id):
    """
    API: 执行智能初始化
    """
    try:
        result = ai_service.init_warehouse(warehouse_id, current_user.id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

